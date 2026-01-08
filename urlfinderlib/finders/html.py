import html
import re
import warnings
from io import StringIO
from itertools import chain
from typing import Set, Union
from urllib.parse import unquote, urljoin

from lxml import etree

import urlfinderlib.helpers as helpers
import urlfinderlib.tokenizer as tokenizer
from urlfinderlib import is_url
from urlfinderlib.url import URLList

from .text import TextUrlFinder

warnings.filterwarnings("ignore", category=UserWarning, module="bs4")


def _build_tree(string: str) -> etree.Element:
    parser = etree.HTMLParser(encoding="utf-8", default_doctype=False)

    tree = etree.parse(StringIO(string), parser=parser)
    if tree.getroot() is None:
        tree = etree.parse(StringIO("<html></html>"), parser=parser)

    return tree


def _remove_element_from_tree(element: etree.Element) -> None:
    parent = element.getparent()

    if element.tail and element.tail.strip():
        prev = element.getprevious()
        if prev is not None:
            prev.tail = (prev.tail or "") + element.tail
        else:
            parent.text = (parent.text or "") + element.tail

    parent.remove(element)


def _remove_obfuscating_font_tags_from_tree(tree: etree.Element) -> None:
    for tag in tree.iterfind(".//font[@id]"):
        if len(tag.items()) == 1:
            _remove_element_from_tree(tag)


class HtmlUrlFinder:
    def __init__(self, blob: Union[bytes, str], base_url: str = ""):
        if isinstance(blob, str):
            blob = blob.encode("utf-8", errors="ignore")

        self._base_url = base_url

        utf8_string = helpers.remove_null_characters(blob.decode("utf-8", errors="ignore"))
        decoded_utf8_string = html.unescape(unquote(utf8_string))

        self._strings = [utf8_string]
        if decoded_utf8_string != utf8_string:
            self._strings.append(decoded_utf8_string)

    def find_urls(self) -> Set[str]:
        urls = URLList()
        for string in self._strings:
            urls += HtmlTreeUrlFinder(string, base_url=self._base_url).find_urls()

        return set(urls)


class HtmlTreeUrlFinder:
    def __init__(self, string: str, base_url: str = ""):
        self._base_url = None
        self._given_base_url = base_url
        self._string = string
        self._tree = _build_tree(string)

    @property
    def base_url(self):
        if self._base_url is None:
            self._base_url = self._pick_base_url(self._given_base_url)

        return self._base_url

    @property
    def tree_string(self):
        return unquote(etree.tostring(self._tree, encoding="unicode", method="html"))

    def find_urls(self) -> Set[str]:
        valid_urls = URLList()

        for document_write_url in self._find_document_write_urls():
            valid_urls.append(document_write_url)

        for window_location_url in self._get_window_location_href():
            valid_urls.append(helpers.fix_possible_url(window_location_url))

        for visible_url in self._find_visible_urls():
            valid_urls.append(visible_url)

        for meta_refresh_value in self._get_meta_refresh_values():
            valid_urls.append(meta_refresh_value)

        possible_urls = set()
        possible_urls |= {urljoin(self.base_url, u) for u in self._get_base_url_eligible_values()}

        srcset_values = self._get_srcset_values()
        possible_urls = {u for u in possible_urls if not any(srcset_value in u for srcset_value in srcset_values)}
        possible_urls |= {urljoin(self._base_url, u) for u in srcset_values}

        possible_urls |= self._get_tag_attribute_values()

        for possible_url in possible_urls:
            valid_urls.append(helpers.fix_possible_url(possible_url))

        tok = tokenizer.UTF8Tokenizer(self.tree_string)

        # TODO: itertools.product(*zip(string.lower(), string.upper()))
        token_iter = chain(
            tok.get_tokens_between_open_and_close_sequence('"http', '"', strict=True),
            tok.get_tokens_between_open_and_close_sequence('"ftp', '"', strict=True),
            tok.get_tokens_between_open_and_close_sequence("'http", "'", strict=True),
            tok.get_tokens_between_open_and_close_sequence("'ftp", "'", strict=True),
            tok.get_tokens_between_open_and_close_sequence('"HTTP', '"', strict=True),
            tok.get_tokens_between_open_and_close_sequence('"FTP', '"', strict=True),
            tok.get_tokens_between_open_and_close_sequence("'HTTP", "'", strict=True),
            tok.get_tokens_between_open_and_close_sequence("'FTP", "'", strict=True),
        )

        for token in token_iter:
            valid_urls.append(token)

        return set(valid_urls)

    def _find_document_write_urls(self) -> Set[str]:
        urls = URLList()

        document_writes_contents = self._get_document_write_contents()
        for content in document_writes_contents:
            new_parser = HtmlUrlFinder(content, base_url=self.base_url)
            urls += new_parser.find_urls()

        return set(urls)

    def _find_visible_urls(self) -> Set[str]:
        visible_text = self._get_visible_text()
        possible_urls = {line for line in visible_text.splitlines() if "." in line and "/" in line}

        urls = URLList()
        for possible_url in possible_urls:
            urls += TextUrlFinder(possible_url).find_urls(strict=True)

        return set(urls)

    def _get_action_values(self) -> Set[str]:
        values = set()
        for tag in self._tree.iterfind(".//*[@action]"):
            if self.base_url:
                values.add(helpers.fix_possible_value(tag.attrib["action"]))
            else:
                values.add(helpers.fix_possible_url(tag.attrib["action"]))
            tag.attrib["action"] = ""
        return values

    def _get_background_values(self) -> Set[str]:
        values = set()
        for tag in self._tree.iterfind(".//*[@background]"):
            if self.base_url:
                values.add(helpers.fix_possible_value(tag.attrib["background"]))
            else:
                values.add(helpers.fix_possible_url(tag.attrib["background"]))
            tag.attrib["background"] = ""
        return values

    def _get_base_url_from_html(self) -> str:
        tag = self._tree.find(".//base[@href]")
        if tag is not None:
            base_url = helpers.fix_possible_url(tag.attrib["href"])
            return base_url if is_url(base_url) else ""

        return ""

    def _get_base_url_eligible_values(self) -> Set[str]:
        values = set()
        values |= self._get_action_values()
        values |= self._get_background_values()
        values |= self._get_css_url_values()
        values |= self._get_href_values()
        values |= self._get_src_values()
        values |= self._get_xmlns_values()

        return values

    def _get_css_url_values(self) -> Set[str]:
        return {
            match for match in re.findall(r"url\s*\(\s*[\'\"]?(.*?)[\'\"]?\s*\)", self._string, flags=re.IGNORECASE)
        }

    def _get_document_writes(self) -> Set[str]:
        return {match for match in re.findall(r"document\.write\s*\(.*?\)\s*;", self._string, flags=re.IGNORECASE)}

    def _get_document_write_contents(self) -> Set[str]:
        document_writes = self._get_document_writes()
        document_writes_contents = set()

        for document_write in document_writes:
            write_begin_index = document_write.rfind("(")
            write_end_index = document_write.find(")")
            write_content = document_write[write_begin_index + 1 : write_end_index]
            document_writes_contents.add(helpers.fix_possible_value(write_content))

        return {contents for contents in document_writes_contents if contents}

    def _get_href_values(self) -> Set[str]:
        values = set()
        for tag in self._tree.iterfind(".//*[@href]"):
            if self.base_url:
                values.add(helpers.fix_possible_value(tag.attrib["href"]))
            else:
                values.add(helpers.fix_possible_url(tag.attrib["href"]))
            tag.attrib["href"] = ""
        return values

    def _get_meta_refresh_values(self) -> Set[str]:
        values = set()

        for tag in self._tree.iterfind(".//meta[@http-equiv][@content]"):
            value = tag.attrib["content"]
            if "url=" in value.lower():
                value = value.partition("=")[2].strip()
                value = helpers.fix_possible_value(value)
                values.add(value)

        return values

    def _get_src_values(self) -> Set[str]:
        values = set()
        for tag in self._tree.iterfind(".//*[@src]"):
            if self.base_url:
                values.add(helpers.fix_possible_value(tag.attrib["src"]))
            else:
                values.add(helpers.fix_possible_url(tag.attrib["src"]))
            tag.attrib["src"] = ""
        return values

    def _get_srcset_values(self) -> Set[str]:
        values = set()
        for tag in self._tree.iterfind(".//*[@srcset]"):
            value = helpers.fix_possible_url(tag.attrib["srcset"])
            splits = value.split(",")
            values |= {s.strip().split(" ")[0] for s in splits}

            tag.attrib["srcset"] = ""

        return values

    def _get_tag_attribute_values(self) -> Set[str]:
        values = set()

        for element in self._tree.iter():
            values |= {v for v in element.attrib.values()}

            for attrib in element.attrib:
                # Ignore the "onclick" attribute since that contains JavaScript. By not replacing this value, it lets
                # the TextUrlFinder attempt to extract URLs from it instead since it is not parsed by lxml.
                if attrib.lower() == "onclick":
                    continue

                element.attrib[attrib] = ""

        return values

    def _get_visible_text(self) -> str:
        new_tree = _build_tree(self._string)
        _remove_obfuscating_font_tags_from_tree(new_tree)

        for tag in new_tree.iterfind(".//script"):
            _remove_element_from_tree(tag)

        for tag in new_tree.iterfind(".//style"):
            _remove_element_from_tree(tag)

        return etree.tostring(new_tree, encoding="utf-8", method="text").decode("utf-8", errors="ignore").strip()

    def _get_window_location_href(self) -> Set[str]:
        return {
            match
            for match in re.findall(
                r"window\.location\.href\s*?=\s*?['\"](.*?)['\"]", self._string, flags=re.IGNORECASE
            )
        }

    def _get_xmlns_values(self) -> Set[str]:
        values = {helpers.fix_possible_url(tag.attrib["xmlns"]) for tag in self._tree.iterfind(".[@xmlns]")}
        values |= {helpers.fix_possible_url(tag.attrib["xmlns"]) for tag in self._tree.iterfind(".//*[@xmlns]")}
        return values

    def _pick_base_url(self, given_base_url: str) -> str:
        found_base_url = self._get_base_url_from_html()
        return found_base_url if found_base_url else given_base_url
