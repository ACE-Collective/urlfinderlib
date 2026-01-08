import urlfinderlib.finders


def test_find_urls_in_text():
    text = b"""
<http://domain.com/angle_brackets>
`http://domain.com/backticks`
[http://domain.com/brackets]
{http://domain.com/curly_brackets}
"http://domain.com/double_quotes"
(http://domain.com/parentheses)
'http://domain.com/single_quotes'
 http://domain.com/spaces 
http://domain.com/lines
http://domain.com/text<http://domain.com/actual>
"""

    finder = urlfinderlib.finders.TextUrlFinder(text)

    expected_urls = {
        "http://domain.com/angle_brackets",
        "http://domain.com/backticks",
        "http://domain.com/brackets",
        "http://domain.com/curly_brackets",
        "http://domain.com/double_quotes",
        "http://domain.com/parentheses",
        "http://domain.com/single_quotes",
        "http://domain.com/spaces",
        "http://domain.com/lines",
        "http://domain.com/text",
        "http://domain.com/actual",
    }

    assert finder.find_urls() == expected_urls


def test_invalid_ipv6():
    text = b"""
https://domain.com.  [https://domain2.com]
"""
    finder = urlfinderlib.finders.TextUrlFinder(text)

    expected_urls = {
        "https://domain.com",
        "https://domain2.com",
    }

    assert finder.find_urls() == expected_urls
