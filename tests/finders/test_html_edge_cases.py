from lxml import etree

import urlfinderlib.finders


def test_backslashes():
    html = b'<html><body><a href="http:/\\domain.com"></a></body></html>'
    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"http://domain.com"}

    html = b'<html><body><a href="http:\\/domain.com"></a></body></html>'
    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"http://domain.com"}

    html = b'<html><body><a href="http:\\\\domain.com"></a></body></html>'
    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"http://domain.com"}


def test_base_url_with_backslashes():
    html = '<html><head><base href="http:\\/domain.com"></head><body><a href="index.php"></a></body></html>'
    finder = urlfinderlib.finders.HtmlTreeUrlFinder(html)

    assert finder._get_base_url_from_html() == "http://domain.com"
    assert finder.find_urls() == {"http://domain.com", "http://domain.com/index.php"}


def test_conditional_html():
    html = b"""<html><head></head><body>
<!--[if mso]>
<v:roundrect href="http://domain.com"></v:roundrect>
<![endif]-->
</body></html>
"""

    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"http://domain.com"}


def test_double_opening_characters():
    html = b"<html><body><p>(http://domain.com/(123)</p></body></html>"
    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"http://domain.com/(123", "http://domain.com"}


def test_email_embedded_image_url():
    html = b'<html><body><img src="cid:asdf1234"></body></html>'
    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == set()


def test_encoded_space_before_url():
    html = b'<html><body><a href="%20http://domain.com"></a></body></html>'
    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"http://domain.com"}


def test_ftp_url():
    html = b'<html><body><a href="ftp://user:pass@domain.com"></a></body></html>'
    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"ftp://user:pass@domain.com"}


def test_javascript_encoded_html():
    html = b"""
<script language='javascript'>
document.write(
    unescape('%3Chtml%3E%3Cbody%3E%3Ca%20href%3D%22http%3A//domain.com%22%3E%3C/a%3E%3C/body%3E%3C/html%3E')
);
</script>
"""

    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"http://domain.com"}


def test_mailto():
    html = b'<html><body><a href="mailto:user@domain.com"</a><a href="mailto:http://domain.com"></a></body></html>'
    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"http://domain.com"}


def test_meta_refresh_new_line():
    html = b'<html><head><meta http-equiv="refresh" content="0;\nurl=http://domain.com">'
    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"http://domain.com"}


def test_missing_closing_html_tag():
    html = b'<html><body><a href="http://domain.com"></a></body>'
    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"http://domain.com"}


def test_missing_scheme_slash():
    html = b"<html><body>http:/domain.com/index.html</body></html>"
    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"http://domain.com/index.html"}


def test_missing_scheme_with_backslash():
    html = b'<html><body><a href="/\\domain.com/index.html"></a></body>'
    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"https://domain.com/index.html"}


def test_missing_scheme_with_colon():
    html = b"<html><body>://domain.com/index.html</body></html>"
    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"https://domain.com/index.html"}


def test_missing_scheme_without_colon():
    html = b"<html><body>//domain.com/index.html</body></html>"
    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"https://domain.com/index.html"}


def test_new_line_in_anchor_tag():
    html = b'<html><body><a href="\nhttp://domain.com"></a></body></html>'
    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"http://domain.com"}


def test_no_quotes_in_anchor_tag():
    html = b"<html><body><a href=http://domain.com></a></body></html>"
    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"http://domain.com"}


def test_non_utf8_characters():
    html = b'<html><body><a href="http://domain\x8a.com"></a></body></html>'
    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"http://domain.com"}


def test_null_characters():
    html = b"<html><body>http://\x00domain.com</body></html>"
    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"http://domain.com"}


def test_two_urls_in_anchor_tag():
    html = b'<html><body><a href="http://domain.com">http://domain2.com</a></body></html>'
    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"http://domain.com", "http://domain2.com"}


def test_unicode():
    html = """
<html>
<body>
<a href="http://উদাহরণ.বাংলা/😉"></a>
<a href="http://√.com"></a>
</body>
</html>
""".encode("utf-8", errors="ignore")

    expected_urls = {"http://উদাহরণ.বাংলা/😉", "http://√.com"}

    finder = urlfinderlib.finders.HtmlUrlFinder(html)

    assert finder.find_urls() == expected_urls


def test_url_in_paragraph():
    html = b"<html><body>This is http://domain.com a test</body></html>"
    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"http://domain.com"}


def test_url_in_query_value():
    html = '<html><body><a href="https://www.domain.com/redirect?url=http://√.com"></a></body></html>'
    finder = urlfinderlib.finders.HtmlUrlFinder(html.encode("utf-8"))
    assert finder.find_urls() == {"https://www.domain.com/redirect?url=http://√.com"}


def test_window_location_redirect():
    html = b"""
<script type="text/javascript">
    function redirect() {
        window.location = "http://domain.com";
    }
    redirect();
</script>"""

    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    assert finder.find_urls() == {"http://domain.com"}
