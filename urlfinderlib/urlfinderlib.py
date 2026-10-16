import codecs
import json
import re
from typing import Iterable, List, Optional, Set, Union

import magic

import urlfinderlib.finders as finders
import urlfinderlib.helpers as helpers
from urlfinderlib.url import URL, URLList

# A whole URL stored base64-encoded: a run of base64-alphabet characters (standard or URL-safe) that opens
# with the encoding of "http" or "ftp". Phishing kits park the redirect target this way in an attribute
# (`<a href="aHR0cHM6Ly9...">`) or a string literal and decode it with atob() at runtime, so the URL never
# appears in the file as text. The lookbehind anchors the run at a non-base64 character, which keeps the
# match aligned on a 4-character group boundary: a match that starts mid-run would decode to garbage.
base64_encoded_url_pattern = re.compile(r"(?<![A-Za-z0-9+/_-])(?:aHR0c|ZnRw)[A-Za-z0-9+/_-]+={0,2}")

# What servers put in front of a JSON response so that a page loading it as a script cannot read it.
_JSON_HIJACKING_PREFIXES = (")]}'", "while(1);", "for(;;);")

# A JSON document stored in a JSON string is decoded again, this many levels deep at most.
_MAX_JSON_DEPTH = 3


def _find_base64_encoded_urls(blob: bytes) -> Set[str]:
    urls = set()
    for match in base64_encoded_url_pattern.finditer(blob.decode("utf-8", errors="ignore")):
        decoded = helpers.decode_base64_ascii(match.group(0))
        if decoded:
            urls |= finders.TextUrlFinder(decoded).find_urls(strict=True)

    return urls


def _json_strings(blob: bytes) -> Optional[List[str]]:
    """Returns every string in a JSON document, keys included, or None when the blob is not one.

    The parser decodes the escapes in each string exactly. Read as text, an escape that follows a URL
    becomes part of it: "see https://domain.com/a\\nNext" reads as https://domain.com/a/nNext.
    Text cannot decode \\n the same way, because a backslash-obfuscated URL such as
    https:\\\\domain.com\\next is spelled with the same characters.
    """
    text = blob.decode("utf-8", errors="ignore").strip()
    for prefix in _JSON_HIJACKING_PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix) :].lstrip()
            break

    # only an object or an array is worth parsing; other text fails at its first character anyway
    if text[:1] not in ("{", "["):
        return None

    try:
        document = json.loads(text)
    except (ValueError, RecursionError):
        return None

    strings = []
    stack = [document]
    while stack:
        value = stack.pop()
        if isinstance(value, str):
            strings.append(value)
        elif isinstance(value, dict):
            strings.extend(value)
            stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)

    return strings


def _remove_utf16_chars(blob: bytes) -> bytes:
    blob = blob.lstrip(codecs.BOM_UTF16)
    return blob.replace(b"\x00", b"")


def _distinct_urls(urls: Iterable[str], domain_as_url: bool = False) -> Set[str]:
    """One spelling of each URL the finders found, and of each URL found inside those.

    Each finder keeps one spelling of a URL, but two finders can keep different ones (the HTML finder
    reads an href with its entities decoded, the text finder reads it as written), and a URL found
    inside another (a query value, a decoded redirect) can be a spelling of one already found.
    """
    found = URLList([URL(u) for u in urls]).distinct_values()
    expanded = URLList([URL(u) for u in found]).get_all_urls(domain_as_url=domain_as_url)
    return URLList([URL(u) for u in expanded]).distinct_values()


def get_url_permutations(url: str) -> Set[str]:
    return URL(url).permutations


def find_urls(blob: Union[bytes, str], base_url: str = "", mimetype: str = "", domain_as_url: bool = False) -> Set[str]:
    urls = _find_candidate_urls(blob, base_url, mimetype, domain_as_url, json_depth=_MAX_JSON_DEPTH)
    return _distinct_urls(urls, domain_as_url=domain_as_url)


def _find_candidate_urls(
    blob: Union[bytes, str],
    base_url: str,
    mimetype: str,
    domain_as_url: bool,
    json_depth: int,
    json_string: bool = False,
) -> List[str]:
    if isinstance(blob, str):
        blob = blob.encode("utf-8", errors="ignore")

    if not mimetype:
        mimetype = magic.from_buffer(blob)
    mimetype = mimetype.lower()

    if "utf-16" in mimetype:
        blob = _remove_utf16_chars(blob)
        mimetype = magic.from_buffer(blob)
    mimetype = mimetype.lower()

    urls = []

    if "rfc 822" in mimetype or "mail" in mimetype:
        return []
    elif "html" in mimetype:
        blob = helpers.unescape_ascii(blob)
        urls += finders.HtmlUrlFinder(blob, base_url=base_url).find_urls()
    elif "vcalendar" in mimetype or "icalendar" in mimetype or b"BEGIN:VCALENDAR" in blob[:256]:
        urls += finders.IcalUrlFinder(blob).find_urls()
    elif "xml" in mimetype:
        urls += finders.XmlUrlFinder(blob).find_urls()
    elif b"%PDF-" in blob[:1024]:
        urls += finders.PdfUrlFinder(blob).find_urls()
    elif "text" in mimetype:
        json_strings = _json_strings(blob) if json_depth else None

        if json_strings is not None:
            # Each string is a document of its own, so one that holds markup reaches the HTML finder. A
            # string with no dot in it holds no URL as text, but a base64-encoded one has no dot either.
            for string in json_strings:
                if "." in string:
                    urls += _find_candidate_urls(
                        string, base_url, "text/plain", domain_as_url, json_depth - 1, json_string=True
                    )

            urls += _find_base64_encoded_urls("\n".join(json_strings).encode("utf-8", errors="ignore"))
        elif b"xmlns" in blob and b"</" in blob:
            urls += finders.XmlUrlFinder(blob).find_urls()
        # a JSON string is one value, so a comma in it does not separate columns: read as CSV, the font
        # URL https://fonts.googleapis.com/css?family=A:300,400 is cut at its first comma
        elif not json_string and _is_maybe_csv(blob):
            urls += finders.CsvUrlFinder(blob).find_urls()
        elif helpers.might_be_html(blob):
            urls += finders.HtmlUrlFinder(blob).find_urls()
            urls += finders.TextUrlFinder(blob).find_urls(strict=True, domain_as_url=domain_as_url)
        else:
            urls += finders.TextUrlFinder(blob).find_urls(strict=True, domain_as_url=domain_as_url)
    else:
        urls += finders.DataUrlFinder(blob).find_urls()

    urls += _find_base64_encoded_urls(blob)

    return urls


def find_urls_in_text(blob: Union[bytes, str], domain_as_url: bool = False) -> Set[str]:
    """Find URLs in a blob the caller knows to be plain text.

    find_urls() selects a finder by sniffing the body, and its might_be_html() test is satisfied by
    any blob containing the characters < > = : / anywhere in it. That is true of a great deal of
    plain text -- OCR transcriptions, source code, log lines -- and routes the blob through the HTML
    finder as well as the text finder. Use this when the content type is already known so that no
    sniffing is done.
    """
    if isinstance(blob, str):
        blob = blob.encode("utf-8", errors="ignore")

    urls = finders.TextUrlFinder(blob).find_urls(strict=True, domain_as_url=domain_as_url)
    urls |= _find_base64_encoded_urls(blob)
    return _distinct_urls(urls, domain_as_url=domain_as_url)


def _is_maybe_csv(blob: bytes) -> bool:
    lines = blob.decode("utf-8", errors="ignore").splitlines()

    if not lines:
        return False

    # Each line must have at least one comma
    if not all("," in l for l in lines):
        return False

    # Each line must have the same number of commas
    first_line_commas = lines[0].count(",")
    return all(l.count(",") == first_line_commas for l in lines)
