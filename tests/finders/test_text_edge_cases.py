import urlfinderlib.finders


def test_backslashes():
    text = b"http:/\\domain.com"
    finder = urlfinderlib.finders.TextUrlFinder(text)
    assert finder.find_urls() == {"http://domain.com"}


def test_double_opening_characters():
    text = b"<http://domain.com/<123>"
    finder = urlfinderlib.finders.TextUrlFinder(text)
    assert finder.find_urls() == {"http://domain.com/<123", "http://domain.com"}


def test_mailto():
    text = b"<mailto:user@domain.com> <mailto:http://domain.com>"
    finder = urlfinderlib.finders.TextUrlFinder(text)
    assert finder.find_urls() == {"http://domain.com"}


def test_missing_scheme_slash():
    text = b"http:/domain.com"
    finder = urlfinderlib.finders.TextUrlFinder(text)
    assert finder.find_urls() == {"http://domain.com"}


def test_null_characters():
    text = b"http://\x00domain.com"
    finder = urlfinderlib.finders.TextUrlFinder(text)
    assert finder.find_urls() == {"http://domain.com"}


def test_unicode():
    text = """
http://উদাহরণ.বাংলা/😉
http://√.com
""".encode("utf-8", errors="ignore")

    expected_urls = {"http://উদাহরণ.বাংলা/😉", "http://√.com"}

    finder = urlfinderlib.finders.TextUrlFinder(text)

    assert finder.find_urls() == expected_urls


def test_url_in_query_value():
    text = '<html><body><a href="https://www.domain.com/redirect?url=http://√.com"></a></body></html>'
    finder = urlfinderlib.finders.TextUrlFinder(text.encode("utf-8"))
    assert finder.find_urls() == {"https://www.domain.com/redirect?url=http://√.com"}


def test_unicode_quotes_not_detected_as_urls():
    text = "\u2018sr.no Hem Description".encode("utf-8")
    finder = urlfinderlib.finders.TextUrlFinder(text)
    urls = finder.find_urls(domain_as_url=True)
    # The curly-quote-prefixed URL and its IDNA encoding must not appear
    assert "https://\u2018sr.no" not in urls
    assert "https://xn--sr-j2t.no" not in urls


def test_guillemet_garbled_domain_not_detected():
    text = "«™.470s.is".encode("utf-8")
    finder = urlfinderlib.finders.TextUrlFinder(text)
    urls = finder.find_urls(domain_as_url=True)
    assert "https://«™.470s.is" not in urls
    assert "https://xn--tm-yda.470s.is" not in urls
    assert len(urls) == 0


def test_url_next_to_url():
    text = "This is a test click here domain.com/test<https://protect2.fireeye.com/url?u=https://domain.com/test> test."
    finder = urlfinderlib.finders.TextUrlFinder(text)
    assert finder.find_urls() == {
        "https://domain.com/test",
        "https://protect2.fireeye.com/url?u=https://domain.com/test",
    }


def test_cidr_notation_not_detected():
    text = b'"sourceIPAddress": "0.0.0.0", "cidr": "0.0.0.0/0", "vpc": "10.0.0.0/8"'
    finder = urlfinderlib.finders.TextUrlFinder(text)
    assert finder.find_urls() == set()
    assert finder.find_urls(domain_as_url=True) == set()


def test_ip_url_with_explicit_scheme_still_detected():
    text = b"visit http://192.168.1.1/24 for details"
    finder = urlfinderlib.finders.TextUrlFinder(text)
    assert "http://192.168.1.1/24" in finder.find_urls()


def test_trailing_punctuation_stripped():
    text = b"visit http://domain.com/path, then continue"
    finder = urlfinderlib.finders.TextUrlFinder(text)
    urls = finder.find_urls()
    assert "http://domain.com/path" in urls
    assert "http://domain.com/path," not in urls
