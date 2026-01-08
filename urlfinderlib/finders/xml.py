from typing import Set, Union
from xml.etree import cElementTree

from urlfinderlib.url import URLList

from .text import TextUrlFinder


class XmlUrlFinder:
    def __init__(self, string: Union[bytes, str]):
        if isinstance(string, bytes):
            string = string.decode("utf-8", errors="ignore")

        try:
            self._root = cElementTree.fromstring(string)
        except cElementTree.ParseError:
            self._root = cElementTree.fromstring('<?xml version="1.0" encoding="UTF-8"?><empty></empty>')

    def find_urls(self) -> Set[str]:
        possible_urls = {str(self._root)}
        possible_urls |= {v for v in self._get_all_attribute_values() if v and "." in v and "/" in v}
        possible_urls |= {t for t in self._get_all_text() if t and "." in t and "/" in t}

        urls = URLList()
        for possible_url in possible_urls:
            urls += TextUrlFinder(possible_url).find_urls(strict=True)

        return set(urls)

    def _get_all_attribute_values(self) -> Set[str]:
        values = set()

        for element in self._root.iter():
            values.add(element.tag)
            values |= {item for sublist in element.items() for item in sublist}

        return values

    def _get_all_text(self) -> Set[str]:
        return {element.text for element in self._root.iter()}
