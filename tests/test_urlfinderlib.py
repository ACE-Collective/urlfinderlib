import os

import urlfinderlib
from urlfinderlib.urlfinderlib import (
    _has_u_escaped_lowercase_bytes,
    _has_u_escaped_uppercase_bytes,
    _has_x_escaped_lowercase_bytes,
    _has_x_escaped_uppercase_bytes,
    _is_maybe_csv,
    _unescape_ascii,
)

this_dir = os.path.dirname(os.path.realpath(__file__))
files_dir = os.path.realpath(f"{this_dir}/files")


def test_find_urls_base_url_malformed():
    with open(f"{files_dir}/base_url_malformed.html", "rb") as f:
        blob = f.read()

    expected_urls = {
        "https://t.co",
        "https://t.co/asdf1234?amp=1",
        "https://t.co/images/stickman.gif",
        "https://www.w3schools.com/images/stickman.gif",
    }

    assert urlfinderlib.find_urls(blob) == expected_urls


def test_find_urls_binary():
    with open(f"{files_dir}/hello.bin", "rb") as f:
        blob = f.read()

    expected_urls = {"http://domain.com"}

    assert urlfinderlib.find_urls(blob) == expected_urls


def test_find_urls_csv():
    with open(f"{files_dir}/test.csv", "rb") as f:
        blob = f.read()

    expected_urls = {"http://domain.com", "http://domain2.com", "http://domain3.com"}

    assert urlfinderlib.find_urls(blob) == expected_urls


def test_find_urls_csv_lookalike():
    with open(f"{files_dir}/csv_lookalike.txt", "rb") as f:
        blob = f.read()

    expected_urls = {"https://example.com"}

    assert urlfinderlib.find_urls(blob) == expected_urls


def test_find_urls_html():
    with open(f"{files_dir}/test.html", "rb") as f:
        blob = f.read()

    expected_urls = {
        "http://domain.com",
        "http://domain.com/action",
        "http://domain.com/background",
        "http://domain.com/css",
        "http://domain.com/href",
        "http://domain.com/meta",
        "http://domain.com/src",
        "http://domain.com/xmlns",
        "http://domain3.com",
        "http://faß.de/re.php",
        "http://domain2.com/image-small.png",
        "http://domain2.com/image-medium.png",
        "http://domain2.com/image-large.png",
        "http://domain4.com/index.php#thing=http://domain5.com",
        "http://domain5.com",
        "https://domain6.com",
        "https://domain.com/?a=1234",
    }

    assert urlfinderlib.find_urls(blob) == expected_urls


def test_find_urls_html_no_base_url():
    with open(f"{files_dir}/test_no_base_url.html", "rb") as f:
        blob = f.read()

    expected_urls = {
        "http://domain.com/action",
        "http://domain.com/background",
        "http://domain.com/css",
        "http://domain.com/href",
        "http://domain.com/meta",
        "http://domain.com/src",
        "http://domain.com/xmlns",
        "http://domain3.com",
        "http://faß.de/re.php",
        "http://domain2.com/image-small.png",
        "http://domain2.com/image-medium.png",
        "http://domain2.com/image-large.png",
        "http://domain4.com/index.php#thing=http://domain5.com",
        "http://domain5.com",
        "https://domain6.com",
        "https://domain.com/?a=1234",
    }

    assert urlfinderlib.find_urls(blob) == expected_urls


def test_find_urls_ical():
    with open(f"{files_dir}/test.ical", "rb") as f:
        blob = f.read()

        expected_urls = {
            "https://thisisjustatest.com",
            "https://thisisjustatest2.com",
            "https://thisisjustatest3.com",
            "https://thisisjustatest4.com",
        }

        result = urlfinderlib.find_urls(blob)

        assert result == expected_urls


def test_find_urls_in_text_like_html():
    blob = b"""<meta http-equiv="refresh" content="0; URL=https://blah.com/one/two">"""
    assert urlfinderlib.find_urls(blob) == {"https://blah.com/one/two"}


def test_find_urls_ooxml():
    with open(f"{files_dir}/test.ooxml", "rb") as f:
        blob = f.read()

    assert urlfinderlib.find_urls(blob) == set()


def test_find_urls_pdf():
    with open(f"{files_dir}/test.pdfparser", "rb") as f:
        blob = f.read()

    expected_urls = {"http://en.wikipedia.org/wiki/MIT_License", "http://domain.com", "http://domain.com/(test/123"}

    assert urlfinderlib.find_urls(blob) == expected_urls


def test_find_urls_rfc822():
    with open(f"{files_dir}/email.rfc822", "rb") as f:
        blob = f.read()

    assert urlfinderlib.find_urls(blob) == set()


def test_find_urls_text():
    assert urlfinderlib.find_urls("test") == set()


def test_find_urls_text_xml():
    with open(f"{files_dir}/text.xml", "rb") as f:
        blob = f.read()

    expected_urls = {
        "http://schemas.microsoft.com/office/drawing/2010/main",
        "http://schemas.openxmlformats.org/drawingml/2006/chart",
        "http://schemas.openxmlformats.org/drawingml/2006/chartDrawing",
        "http://schemas.openxmlformats.org/drawingml/2006/main",
        "http://schemas.openxmlformats.org/markup-compatibility/2006",
    }

    assert urlfinderlib.find_urls(blob) == expected_urls


def test_find_urls_looks_like_html():
    with open(f"{files_dir}/looks_like_html.xml", "rb") as f:
        blob = f.read()

    expected_urls = {"https://example.com"}

    assert urlfinderlib.find_urls(blob) == expected_urls


def test_find_urls_xml():
    with open(f"{files_dir}/sharedStrings.xml", "rb") as f:
        blob = f.read()

    expected_urls = {
        "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "https://domain.com/test",
        "http://domain2.com",
        "http://www.w3.org/XML/1998/namespace",
    }

    assert urlfinderlib.find_urls(blob) == expected_urls


def test_find_urls_domain_as_url():
    with open(f"{files_dir}/domain_as_url.txt", "rb") as f:
        blob = f.read()

    expected_urls = {"https://somefakesite.com", "https://somefakesite.com/index.html", "https://somefakesite2.com"}

    assert urlfinderlib.find_urls(blob, domain_as_url=True) == expected_urls


def test_get_url_permutations():
    url = "http://faß.de/index.php?test<123/😉"

    expected_permutations = {
        "http://faß.de/index.php%3Ftest%3C123/%F0%9F%98%89",
        "http://faß.de/index.php?test&lt;123/😉",
        "http://faß.de/index.php?test<123/😉",
        "http://xn--fa-hia.de/index.php%3Ftest%3C123/%F0%9F%98%89",
        "http://xn--fa-hia.de/index.php?test&lt;123/😉",
        "http://xn--fa-hia.de/index.php?test<123/😉",
    }

    assert urlfinderlib.get_url_permutations(url) == expected_permutations


def test_has_u_escaped_lowercase_bytes():
    assert _has_u_escaped_lowercase_bytes(b"This is a test") is False
    assert _has_u_escaped_lowercase_bytes(b"This is \\u002A a test") is False
    assert _has_u_escaped_lowercase_bytes(b"This is \\u002a a test") is True


def test_has_u_escaped_uppercase_bytes():
    assert _has_u_escaped_uppercase_bytes(b"This is a test") is False
    assert _has_u_escaped_uppercase_bytes(b"This is \\u002A a test") is True
    assert _has_u_escaped_uppercase_bytes(b"This is \\u002a a test") is False


def test_has_x_escaped_lowercase_bytes():
    assert _has_x_escaped_lowercase_bytes(b"This is a test") is False
    assert _has_x_escaped_lowercase_bytes(b"This is \\x2A a test") is False
    assert _has_x_escaped_lowercase_bytes(b"This is \\x2a a test") is True


def test_has_x_escaped_uppercase_bytes():
    assert _has_x_escaped_uppercase_bytes(b"This is a test") is False
    assert _has_x_escaped_uppercase_bytes(b"This is \\x2A a test") is True
    assert _has_x_escaped_uppercase_bytes(b"This is \\x2a a test") is False


def test_is_maybe_csv():
    assert _is_maybe_csv(b"") is False
    assert (
        _is_maybe_csv(b"This is probably, most likely, not a valid CSV file.\nIt looks more like a paragraph.") is False
    )
    assert _is_maybe_csv(b"test,test,test\ntest2,test2,test2") is True


def test_unescape_ascii():
    assert _unescape_ascii(b"\\x4d") == b"M"
    assert _unescape_ascii(b"\\x4D") == b"M"
    assert _unescape_ascii(b"\\u004d") == b"M"
    assert _unescape_ascii(b"\\u004D") == b"M"
