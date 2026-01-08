import base64
import binascii
import html
import ipaddress
import json
import re
import string
from collections import UserList
from typing import AnyStr, Dict, List, Set, Union
from urllib.parse import ParseResult, SplitResult, parse_qs, quote, unquote, urlparse, urlsplit

import idna
import tld
import validators

import urlfinderlib.helpers as helpers

# The base64 strings we want are usually preceeded by a character in the URL such as: ", ', #, or /
# If these were not at the beginning of the regex statement, we would find additional URLs, but they
# are often malformed when decoded, as they are buried inside of a larger URL encoding scheme.
base64_pattern = re.compile(r"[\"\'\#\/](((aHR0c)|(ZnRw))[a-zA-Z0-9]+)")


# TODO: Change this to inherit from a set
class URLList(UserList):
    def __eq__(self, other: Union[list, "URLList"]) -> bool:
        if isinstance(other, list):
            return sorted(self.data) == sorted(other)
        elif isinstance(other, URLList):
            return sorted(self.data) == sorted(other.data)
        else:
            return False

    def append(self, value: Union[str, "URL"]) -> None:
        if isinstance(value, str):
            value = URL(value)

        if isinstance(value, URL):
            if value.is_url:
                self.data.append(value)
            elif value.is_url_ascii:
                self.data.append(URL(helpers.get_ascii_url(value.value)))

    def get_all_urls(self) -> Set[str]:
        if self.data:
            all_urls = []
            stack = self.data[:]
            while stack:
                url = stack.pop()
                all_urls.append(url.value)
                for child_url in url.child_urls:
                    stack.append(child_url)

            return set(all_urls)

        return set()

    def remove_partial_urls(self) -> "URLList":
        return URLList(
            {
                url.value
                for url in self.data
                if not any(u.value.startswith(url.value) and u != url.value for u in self.data)
                or not url.split_value.path
            }
        )


class URL:
    def __init__(self, value: Union[bytes, str]):
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="ignore")

        if isinstance(value, URL):
            value = value.value

        self.value = value.rstrip("/") if value else ""
        self.value = self.value.rstrip("\\") if self.value else ""

        self._child_urls = None
        self._fragment_dict = None
        self._is_mandrillapp = None
        self._is_netloc_ipv4 = None
        self._is_netloc_localhost = None
        self._is_netloc_valid_tld = None
        self._is_proofpoint_v2 = None
        self._is_proofpoint_v3 = None
        self._is_url = None
        self._is_url_ascii = None
        self._is_valid_format = None
        self._netloc_idna = None
        self._netloc_original = None
        self._netloc_unicode = None
        self._netlocs = None
        self._original_url = None
        self._parse_value = None
        self._path_all_decoded = None
        self._path_html_decoded = None
        self._path_html_encoded = None
        self._path_original = None
        self._path_percent_decoded = None
        self._path_percent_encoded = None
        self._paths = None
        self._permutations = None
        self._query_dict = None
        self._split_value = None
        self._value_lower = None

    def __eq__(self, other: Union[bytes, str, "URL"]) -> bool:
        if isinstance(other, str):
            other = URL(other)
        elif isinstance(other, bytes):
            other = URL(other.decode("utf-8", errors="ignore"))
        elif not isinstance(other, URL):
            return False

        return self.value == other.value or any(
            other_permutation in self.permutations for other_permutation in other.permutations
        )

    def __hash__(self) -> int:
        return hash(html.unescape(unquote(self.value)))

    def __lt__(self, other: "URL") -> bool:
        if isinstance(other, URL):
            return self.value < other.value

        return False

    def __repr__(self) -> str:
        return f"URL: {self.value}"

    def __str__(self) -> str:
        return self.value

    @property
    def child_urls(self) -> "URLList":
        if self._child_urls is None:
            self._child_urls = self.get_child_urls()

        return self._child_urls

    @property
    def fragment_dict(self) -> Dict[AnyStr, List[AnyStr]]:
        if self._fragment_dict is None:
            self._fragment_dict = parse_qs(self.parse_value.fragment)

        return self._fragment_dict

    @property
    def idna_percent_encoded(self) -> str:
        """Returns the URL with the IDNA version of the domain and the percent encoded path"""

        return f"{self.split_value.scheme}://{self.netloc_idna}{self.path_percent_encoded}"

    @property
    def is_mandrillapp(self) -> bool:
        if self._is_mandrillapp is None and self.split_value.hostname:
            self._is_mandrillapp = "mandrillapp.com" in self.split_value.hostname and "p" in self.query_dict

        return self._is_mandrillapp

    @property
    def is_netloc_ipv4(self) -> bool:
        if self._is_netloc_ipv4 is None:
            if not self.split_value.hostname:
                self._is_netloc_ipv4 = False
            else:
                try:
                    ipaddress.ip_address(self.split_value.hostname)
                    self._is_netloc_ipv4 = True
                    return self._is_netloc_ipv4
                except ValueError:
                    self._is_netloc_ipv4 = False
                    return self._is_netloc_ipv4

        return self._is_netloc_ipv4

    @property
    def is_netloc_localhost(self) -> bool:
        if self._is_netloc_localhost is None:
            if not self.split_value.hostname:
                self._is_netloc_localhost = False
            else:
                self._is_netloc_localhost = (
                    self.split_value.hostname.lower() == "localhost"
                    or self.split_value.hostname.lower() == "localhost.localdomain"
                )

        return self._is_netloc_localhost

    @property
    def is_netloc_valid_tld(self) -> bool:
        if self._is_netloc_valid_tld is None:
            self._is_netloc_valid_tld = bool(tld.get_tld(self.value, fail_silently=True))

        return self._is_netloc_valid_tld

    @property
    def is_proofpoint_v2(self) -> bool:
        if self._is_proofpoint_v2 is None and self.split_value.hostname:
            self._is_proofpoint_v2 = (
                "urldefense" in self.split_value.hostname
                and ("urldefense.proofpoint.com/v2" in self.value_lower or "urldefense.com/v2" in self.value_lower)
                and "u" in self.query_dict
            )

        return self._is_proofpoint_v2

    @property
    def is_proofpoint_v3(self) -> bool:
        if self._is_proofpoint_v3 is None and self.split_value.hostname:
            self._is_proofpoint_v3 = "urldefense" in self.split_value.hostname and (
                "urldefense.proofpoint.com/v3" in self.value_lower or "urldefense.com/v3" in self.value_lower
            )

        return self._is_proofpoint_v3

    @property
    def is_url(self) -> bool:
        if self._is_url is None:
            if "." not in self.value or ":" not in self.value or "/" not in self.value:
                self._is_url = False
            else:
                self._is_url = (
                    self.is_netloc_valid_tld or self.is_netloc_ipv4 or self.is_netloc_localhost
                ) and self.is_valid_format

        return self._is_url

    @property
    def is_url_ascii(self) -> bool:
        if self._is_url_ascii is None:
            url = self.value.encode("ascii", errors="ignore").decode()
            self._is_url_ascii = URL(url).is_url

        return self._is_url_ascii

    @property
    def is_valid_format(self) -> bool:
        if self._is_valid_format is None:
            if not re.match(r"^[a-zA-Z0-9\-\.\:\@]{1,255}$", self.netloc_idna):
                return False

            encoded_url = helpers.build_url(self.split_value.scheme, self.netloc_idna, self.path_percent_encoded)
            self._is_valid_format = bool(validators.url(encoded_url, simple_host=True))

        return self._is_valid_format

    @property
    def netloc_idna(self) -> str:
        if self._netloc_idna is None:
            netloc = self.split_value.netloc

            # Decode percent-encoded sequences in netloc
            if "%" in netloc:
                netloc = unquote(netloc)

            if all(ord(char) < 128 for char in netloc):
                self._netloc_idna = netloc.lower()
                return self._netloc_idna

            try:
                hostname = urlsplit(f"http://{netloc}").hostname or netloc
                idna_hostname = idna.encode(hostname).decode("utf-8").lower()
                self._netloc_idna = netloc.lower().replace(hostname.lower(), idna_hostname)
                return self._netloc_idna
            except idna.core.IDNAError:
                try:
                    hostname = urlsplit(f"http://{netloc}").hostname or netloc
                    idna_hostname = hostname.encode("idna").decode("utf-8", errors="ignore").lower()
                    self._netloc_idna = netloc.lower().replace(hostname.lower(), idna_hostname)
                    return self._netloc_idna
                except UnicodeError:
                    self._netloc_idna = ""

            self._netloc_idna = ""

        return self._netloc_idna

    @property
    def netloc_original(self) -> str:
        if self._netloc_original is None:
            self._netloc_original = self.split_value.netloc.lower()

        return self._netloc_original

    @property
    def netloc_unicode(self) -> str:
        if self._netloc_unicode is None:
            netloc = self.split_value.netloc

            # Decode percent-encoded sequences in netloc
            if "%" in netloc:
                netloc = unquote(netloc)

            if any(ord(char) >= 128 for char in netloc):
                self._netloc_unicode = netloc.lower()
                return self._netloc_unicode

            try:
                self._netloc_unicode = idna.decode(netloc).lower()
                return self._netloc_unicode
            except idna.core.IDNAError:
                self._netloc_unicode = netloc.encode("utf-8", errors="ignore").decode("idna").lower()
                return self._netloc_unicode

        return self._netloc_unicode

    @property
    def netlocs(self) -> Dict[AnyStr, AnyStr]:
        if self._netlocs is None:
            self._netlocs = {"idna": self.netloc_idna, "original": self.netloc_original, "unicode": self.netloc_unicode}

        return self._netlocs

    @property
    def original_url(self) -> str:
        if self._original_url is None:
            self._original_url = helpers.build_url(self.split_value.scheme, self.netloc_original, self.path_original)

        return self._original_url

    @property
    def parse_value(self) -> ParseResult:
        if self._parse_value is None:
            self._parse_value = urlparse(self.value)

        return self._parse_value

    @property
    def path_all_decoded(self) -> str:
        if self._path_all_decoded is None:
            self._path_all_decoded = html.unescape(unquote(self.path_original))

        return self._path_all_decoded

    @property
    def path_html_decoded(self) -> str:
        if self._path_html_decoded is None:
            self._path_html_decoded = html.unescape(self.path_original)

        return self._path_html_decoded

    @property
    def path_html_encoded(self) -> str:
        if self._path_html_encoded is None:
            self._path_html_encoded = html.escape(self.path_all_decoded)

        return self._path_html_encoded

    @property
    def path_original(self) -> str:
        if self._path_original is None:
            path = self.split_value.path
            query = self.split_value.query
            fragment = self.split_value.fragment

            if (path or query or fragment) and not path.startswith("/"):
                path = f"/{path}"

            if query:
                path = f"{path}?{query}"

            if fragment:
                path = f"{path}#{fragment}"

            self._path_original = path

        return self._path_original

    @property
    def path_percent_decoded(self) -> str:
        if self._path_percent_decoded is None:
            self._path_percent_decoded = unquote(self.path_original)

        return self._path_percent_decoded

    @property
    def path_percent_encoded(self) -> str:
        if self._path_percent_encoded is None:
            """
            Line breaks are included in safe_chars because they should not exist in a valid URL.
            The tokenizer will sometimes create tokens that would be considered valid URLs if
            these characters get %-encoded.
            """
            safe_chars = "/\n\r"
            self._path_percent_encoded = quote(self.path_all_decoded, safe=safe_chars)

        return self._path_percent_encoded

    @property
    def paths(self) -> Dict[AnyStr, AnyStr]:
        if self._paths is None:
            self._paths = {
                "all_decoded": self.path_all_decoded,
                "original": self.path_original,
                "html_decoded": self.path_html_decoded,
                "html_encoded": self.path_html_encoded,
                "percent_decoded": self.path_percent_decoded,
                "percent_encoded": self.path_percent_encoded,
            }

        return self._paths

    @property
    def permutations(self) -> Set[str]:
        if self._permutations is None:
            self._permutations = self.get_permutations()

        return self._permutations

    @property
    def query_dict(self) -> Dict[AnyStr, List[AnyStr]]:
        if self._query_dict is None:
            self._query_dict = parse_qs(self.parse_value.query)

        return self._query_dict

    @property
    def split_value(self) -> SplitResult:
        if self._split_value is None:
            try:
                self._split_value = urlsplit(self.value)
            except ValueError:
                self._split_value = urlsplit("")

        return self._split_value

    @property
    def value_lower(self) -> str:
        if self._value_lower is None:
            self._value_lower = self.value.lower()

        return self._value_lower

    def decode_mandrillapp(self) -> str:
        base64_string = self.query_dict["p"][0].replace("_", "/")
        decoded = base64.b64decode(f"{base64_string}===")

        try:
            outer_json = json.loads(decoded)
            inner_json = json.loads(outer_json["p"])
            possible_url = helpers.fix_possible_url(inner_json["url"])
            return possible_url if URL(possible_url).is_url else ""
        except json.JSONDecodeError:
            return ""
        except UnicodeDecodeError:
            return ""

    def decode_proofpoint_v2(self) -> str:
        maketrans = str.maketrans
        trans = maketrans("-_", "%/")
        try:
            query_url = self.query_dict["u"][0]
            url_encoded_url = query_url.translate(trans)
            html_encoded_url = unquote(url_encoded_url)
            url = html.unescape(html_encoded_url)

            possible_url = helpers.fix_possible_url(url)
            return possible_url if URL(possible_url).is_url else ""
        except KeyError:
            return ""

    # Official decoder code from Proofpoint
    # https://help.proofpoint.com/@api/deki/files/2775/urldecoder.py?revision=1
    def decode_proofpoint_v3(self) -> str:
        v3_single_slash = re.compile(r"^([a-z0-9+.-]+:/)([^/].+)", re.IGNORECASE)
        v3_run_mapping = {}
        run_values = string.ascii_uppercase + string.ascii_lowercase + string.digits + "-" + "_"
        run_length = 2
        for value in run_values:
            v3_run_mapping[value] = run_length
            run_length += 1

        def replace_token(token):
            nonlocal current_marker
            nonlocal decoded_characters
            nonlocal v3_run_mapping
            if token == "*":
                character = decoded_characters[current_marker]
                current_marker += 1
                return character
            if token.startswith("**"):
                run_length = v3_run_mapping[token[-1]]
                run = decoded_characters[current_marker : current_marker + run_length]
                current_marker += run_length
                return run

        def substitute_tokens(text, start_pos=0):
            v3_token_pattern = re.compile(r"\*(\*.)?")
            match = v3_token_pattern.search(text, start_pos)
            if match:
                start = text[start_pos : match.start()]
                built_string = start
                token = text[match.start() : match.end()]
                built_string += replace_token(token)
                built_string += substitute_tokens(text, match.end())
                return built_string
            else:
                return text[start_pos : len(text)]

        try:
            match = re.search(r"v3/__(.+?)__;(.*?)!", self.value, re.IGNORECASE)
            embedded_url = match.group(1)
            base64_characters = match.group(2)

            single_slash = v3_single_slash.findall(embedded_url)
            if single_slash and len(single_slash[0]) == 2:
                embedded_url = single_slash[0][0] + "/" + single_slash[0][1]
            embedded_url = unquote(embedded_url)

            base64_characters += "=="
            decoded_characters = base64.urlsafe_b64decode(base64_characters).decode("utf-8")
            current_marker = 0

            decoded_url = substitute_tokens(embedded_url)
            decoded_url = helpers.fix_possible_url(decoded_url)
            return decoded_url if URL(decoded_url).is_url else ""
        except AttributeError:
            return ""

    def get_base64_urls(self) -> Set[str]:
        fixed_base64_values = {helpers.fix_possible_value(v) for v in self.get_base64_values()}
        return {u for u in fixed_base64_values if URL(u).is_url}

    def get_base64_values(self) -> Set[str]:
        values = set()

        for match in base64_pattern.findall(self.path_original):
            if helpers.is_base64_ascii(match[0]):
                values.add(base64.b64decode(f"{match[0]}===").decode("ascii"))

        return values

    def get_child_urls(self) -> "URLList":
        child_urls = []

        child_urls += self.get_query_urls()
        child_urls += self.get_fragment_urls()
        child_urls += self.get_base64_urls()

        if self.is_mandrillapp:
            decoded_url = self.decode_mandrillapp()
            if decoded_url:
                child_urls.append(decoded_url)

        if self.is_proofpoint_v2:
            child_urls.append(self.decode_proofpoint_v2())

        if self.is_proofpoint_v3:
            child_urls.append(self.decode_proofpoint_v3())

        return URLList([URL(u) for u in child_urls])

    def get_fragment_urls(self) -> Set[str]:
        return {v for v in self.get_fragment_values() if URL(v).is_url}

    def get_fragment_values(self) -> Set[str]:
        values = set()

        for url in self.permutations:
            values |= {item for sublist in URL(url).fragment_dict.values() for item in sublist}

        return values

    def get_permutations(self) -> Set[str]:
        return {
            helpers.build_url(self.split_value.scheme, netloc, path)
            for netloc in self.netlocs.values()
            for path in self.paths.values()
        }

    def get_query_urls(self) -> Set[str]:
        return {v for v in self.get_query_values() if URL(v).is_url}

    def get_query_values(self) -> Set[str]:
        values = set()

        for url in self.permutations:
            values |= {item for sublist in URL(url).query_dict.values() for item in sublist}

        return values
