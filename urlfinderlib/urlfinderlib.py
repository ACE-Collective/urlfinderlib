import codecs
import re
import string
from typing import Set, Union

import magic

import urlfinderlib.finders as finders
import urlfinderlib.helpers as helpers
from urlfinderlib.url import URL, URLList


def _remove_utf16_chars(blob: bytes) -> bytes:
    blob = blob.lstrip(codecs.BOM_UTF16)
    return blob.replace(b"\x00", b"")


def get_url_permutations(url: str) -> Set[str]:
    return URL(url).permutations


def find_urls(blob: Union[bytes, str], base_url: str = "", mimetype: str = "", domain_as_url: bool = False) -> Set[str]:
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
        return set()
    elif "html" in mimetype:
        blob = _unescape_ascii(blob)
        urls += finders.HtmlUrlFinder(blob, base_url=base_url).find_urls()
    elif "vcalendar" in mimetype or "icalendar" in mimetype:
        urls += finders.IcalUrlFinder(blob).find_urls()
    elif "xml" in mimetype:
        urls += finders.XmlUrlFinder(blob).find_urls()
    elif b"%PDF-" in blob[:1024]:
        urls += finders.PdfUrlFinder(blob).find_urls()
    elif "text" in mimetype:
        if b"xmlns" in blob and b"</" in blob:
            urls += finders.XmlUrlFinder(blob).find_urls()
        elif _is_maybe_csv(blob):
            urls += finders.CsvUrlFinder(blob).find_urls()
        elif helpers.might_be_html(blob):
            urls += finders.HtmlUrlFinder(blob).find_urls()
            urls += finders.TextUrlFinder(blob).find_urls(strict=True, domain_as_url=domain_as_url)
        else:
            urls += finders.TextUrlFinder(blob).find_urls(strict=True, domain_as_url=domain_as_url)
    else:
        urls += finders.DataUrlFinder(blob).find_urls()

    return URLList([URL(u) for u in urls]).get_all_urls()


def _has_u_escaped_lowercase_bytes(blob: bytes) -> bool:
    return bool(re.search(r"\\u00[a-f0-9]{2}", blob.decode("utf-8", errors="ignore")))


def _has_u_escaped_uppercase_bytes(blob: bytes) -> bool:
    return bool(re.search(r"\\u00[A-F0-9]{2}", blob.decode("utf-8", errors="ignore")))


def _has_x_escaped_lowercase_bytes(blob: bytes) -> bool:
    return bool(re.search(r"\\x[a-f0-9]{2}", blob.decode("utf-8", errors="ignore")))


def _has_x_escaped_uppercase_bytes(blob: bytes) -> bool:
    return bool(re.search(r"\\x[A-F0-9]{2}", blob.decode("utf-8", errors="ignore")))


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


def _unescape_ascii(blob: bytes) -> bytes:
    ascii_chars = string.ascii_letters + string.digits + string.punctuation

    if _has_u_escaped_lowercase_bytes(blob):
        for char in ascii_chars:
            escaped = f"\\u00{format(ord(char), 'x')}".encode("utf-8")
            blob = blob.replace(escaped, escaped.decode("unicode_escape").encode("utf-8"))

    if _has_u_escaped_uppercase_bytes(blob):
        for char in ascii_chars:
            escaped = f"\\u00{format(ord(char), 'X')}".encode("utf-8")
            blob = blob.replace(escaped, escaped.decode("unicode_escape").encode("utf-8"))

    if _has_x_escaped_lowercase_bytes(blob):
        for char in ascii_chars:
            escaped = f"\\x{format(ord(char), 'x')}".encode("utf-8")
            blob = blob.replace(escaped, escaped.decode("unicode_escape").encode("utf-8"))

    if _has_x_escaped_uppercase_bytes(blob):
        for char in ascii_chars:
            escaped = f"\\x{format(ord(char), 'X')}".encode("utf-8")
            blob = blob.replace(escaped, escaped.decode("unicode_escape").encode("utf-8"))

    return blob
