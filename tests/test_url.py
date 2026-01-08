from urlfinderlib.url import *

valid_urls = [
    "http://localhost:8080/index.php",
    "http://127.0.0.1/index.html",
    "http://localhost.localdomain",
    "http://1.1.1.255",
    "http://1.1.1.0",
    "http://1.1.1.1:8080",
    "https://www.domain.com/",
    "http://domain.com/about us/index.php",
    "http://domain.com/about%20us/index.php",
    "HTTPS://WWW.DOMAIN.COM",
    "https://www.domain.com:8080",
    "ftp://user:pass@domain.com/index.html",
    "http://faß.de",
    "http://√.com",
    "http://domain.com?test=true",
    "http://domain.com/?test=true",
    "http://xn--bcher-kva.com",
    "http://domain.coffee",
    "http://www.😉.com/😉",
    "http://উদাহরণ.বাংলা",
    "http://xn--d5b6ci4b4b3a.xn--54b7fta0cc",
    "http://domain.com/&lt;",
    b"http://domain.com",
]

invalid_urls = [
    "user@domain.com",
    "domain.com",
    "domain.com/index.html" "http:/domain.com",
    "http:/\\domain.com",
    "http://domain.com\\index.html",
    "http://domain.invalidtld",
    "http://some_domain.com",
    "http://domain.com&test=true",
    "http://some domain.com",
    "http://domain.com:999999",
    b"domain.com",
    "",
]

valid_url_formats = valid_urls + ["http://domain.invalidtld"]

invalid_url_formats = list(set(invalid_urls) - set(valid_url_formats))


def test_bytes_create():
    url = URL(b"http://domain.com")
    assert url.value == "http://domain.com"


def test_child_urls():
    url = URL("https://www.domain.com/redirect?url=http%3A//domain2.com")
    assert url.child_urls == [URL("http://domain2.com")]


def test_equal_bytes():
    assert b"http://domain.com" == URL("http://domain.com")


def test_equal_other():
    assert URL("http://domain.com") != 1


def test_equal_string():
    assert "http://domain.com" == URL("http://domain.com")


def test_equal_url():
    url1 = URL("http://domain.com/index?URL=http://domain2.com/index2")
    url2 = URL("http://domain.com/index?URL=http%3A%2F%2Fdomain2.com%2Findex2")
    assert url1 == url2
    assert len({url1, url2}) == 1


def test_get_fragment_dict():
    url = URL("http://domain.com/index.php#one=1&two=2&three=3")
    assert url.fragment_dict == {"one": ["1"], "two": ["2"], "three": ["3"]}


def test_get_netloc_idna():
    assert URL("http://faß.de").netloc_idna == "xn--fa-hia.de"
    assert URL("http://DOMAIN.COM").netloc_idna == "domain.com"
    assert URL("http://dom[ain.com").netloc_idna == ""
    assert URL("http://domain\x8a.com").netloc_idna == ""


def test_get_netloc_unicode():
    assert URL("http://xn--fa-hia.de").netloc_unicode == "faß.de"
    assert URL("http://dom[ain.com").netloc_unicode == ""


def test_get_path_all_decoded():
    assert URL("http://domain.com/?index%3D1&lt;2").path_all_decoded == "/?index=1<2"


def test_get_path_html_decoded():
    assert URL("http://domain.com/?index%3D1&lt;2").path_html_decoded == "/?index%3D1<2"


def test_get_path_html_encoded():
    assert URL("http://domain.com/?index=1<2").path_html_encoded == "/?index=1&lt;2"


def test_get_path_original():
    assert URL("http://domain.com/?index%3D1&lt;2").path_original == "/?index%3D1&lt;2"
    assert URL("http://dom[ain.com/test").path_original == ""


def test_get_path_percent_decoded():
    assert URL("http://domain.com/?index%3D1&lt;2").path_percent_decoded == "/?index=1&lt;2"


def test_get_path_percent_encoded():
    assert URL("http://domain.com/?index=1&lt;2").path_percent_encoded == "/%3Findex%3D1%3C2"


def test_get_query_dict():
    url = URL("http://domain.com/index.php?one=1&two=2&three=3")
    assert url.query_dict == {"one": ["1"], "two": ["2"], "three": ["3"]}


def test_get_scheme():
    assert URL("https://domain.com").split_value.scheme == "https"
    assert URL("HTTPS://domain.com").split_value.scheme == "https"
    assert URL("http://dom[ain.com").split_value.scheme == ""


def test_idna_percent_encoded():
    assert (
        URL("http://উদাহরণ.বাংলা:8080/about us/index.html").idna_percent_encoded
        == "http://xn--d5b6ci4b4b3a.xn--54b7fta0cc:8080/about%20us/index.html"
    )


def test_is_netloc_ipv4():
    valid_ipv4_netloc = ["http://1.1.1.1", "http://1.1.1.1:8080", "http://user:password@1.1.1.1:8080"]

    invalid_ipv4_netloc = ["http://domain.com", "http://1.1.1", "http://do[main.com"]

    for url in valid_ipv4_netloc:
        assert URL(url).is_netloc_ipv4 is True

    for url in invalid_ipv4_netloc:
        assert URL(url).is_netloc_ipv4 is False


def test_is_netloc_localhost():
    valid_localhost_netloc = [
        "http://localhost",
        "http://localhost:8080/index.html",
        "http://user:password@localhost.localdomain:8080/index.html",
    ]

    invalid_localhost_netloc = ["http://domain.com", "http://local[host"]

    for url in valid_localhost_netloc:
        assert URL(url).is_netloc_localhost is True

    for url in invalid_localhost_netloc:
        assert URL(url).is_netloc_localhost is False


def test_is_netloc_valid_tld():
    valid_tld_netloc = ["http://domain.com", "http://domain.com:8080", "redis://user:password@domain.com"]

    invalid_tld_netloc = ["http://1.1.1.1", "http://domain.invalidtld"]

    for url in valid_tld_netloc:
        assert URL(url).is_netloc_valid_tld is True

    for url in invalid_tld_netloc:
        assert URL(url).is_netloc_valid_tld is False


def test_is_url():
    for url in valid_urls:
        assert URL(url).is_url is True, f"Valid URL not recognized as valid: {url}"

    for url in invalid_urls:
        assert URL(url).is_url is False, f"Invalid URL recognized as valid: {url}"


def test_is_url_ascii():
    assert URL("http://d😉o😉m😉a😉i😉n😉.😉c😉o😉m").is_url is False
    assert URL("http://d😉o😉m😉a😉i😉n😉.😉c😉o😉m").is_url_ascii is True


def test_is_valid_format():
    for url in valid_url_formats:
        assert URL(url).is_valid_format is True

    for url in invalid_url_formats:
        assert URL(url).is_valid_format is False


def test_remove_partial_urls():
    urls = URLList(
        [URL("http://domain.com/about us/index.php"), URL("http://domain.com/about us"), URL("http://domain.com")]
    )

    expected_urls = URLList(["http://domain.com/about us/index.php", "http://domain.com"])

    assert urls.remove_partial_urls() == expected_urls


def test_repr():
    assert (repr(URL("http://domain.com"))) == "URL: http://domain.com"


def test_string():
    assert str(URL("http://domain.com")) == "http://domain.com"


def test_url_create():
    assert URL("http://domain.com").value == "http://domain.com"
    assert URL("http://domain.com/").value == "http://domain.com"
    assert URL(b"http://domain.com").value == "http://domain.com"


def test_url_decode_barracuda():
    url = URL("https://linkprotect.cudasvc.com/url?a=http://domain.com")
    assert url.child_urls == [URL("http://domain.com")]


def test_url_decode_base64():
    url = URL("http://domain.com/dXNlckBkb21haW4uY29tCg==#aHR0cDovL2RvbWFpbjIuY29tCg")
    assert url.child_urls == [URL("http://domain2.com")]


def test_url_decode_google_redirect():
    url = URL("https://www.google.com/url?sa=t&source=web&rct=j&url=http://domain.com")
    assert url.child_urls == [URL("http://domain.com")]


def test_url_decode_mandrillapp():
    url = URL(
        "https://mandrillapp.com/track/click/30233568/domain.com?p=eyJzIjoiQnU1NFZhQV9RUTJyTnA0OGxZVllHdFZIdVVzIiwidiI6MSwicCI6IntcInVcIjozMDIzMzU2OCxcInZcIjoxLFwidXJsXCI6XCJodHRwOlxcXC9cXFwvZG9tYWluLmNvbVxcXC90ZXN0XCIsXCJpZFwiOlwiMjIyMjk4YmUyNGU0NDE4MzhlMDFmZjcxN2ZlNzE5YjFcIixcInVybF9pZHNcIjpbXCI5ODdjODQ1Y2ZmZGRmYTU4MjYxN2Y5NDFjZmNmNTE4NmU0MGZlNjY5XCJdfSJ9Cg=="
    )
    assert url.is_mandrillapp is True
    assert url.child_urls == [URL("http://domain.com/test")]

    json_decode_error_url = URL(
        "https://mandrillapp.com/track/click/30233568/domain.com?p=eyJzIjoiQnU1NFZhQV9RUTJyTnA0OGxZVllHdFZIdVVzIiwidiI6MSwicCI6IntcInVcIjozMDIzMzU2OCxcInZcIjoxLFwidXJsXCI6XCJodHRwOlxcXC9cXFwvZG9tYWluLmNvbVxcXC90ZXN0XCIsXCJpZFwiOlwiMjIyMjk4YmUyNGU0NDE4MzhlMDFmZjcxN2ZlNzE5YjFcIixcInVybF9pZHNcIjpbXCI5ODdjODQ1Y2ZmZGRmYTU4MjYxN2Y5NDFjZmNmNTE4NmU0MGZlNjY5XCJdCg=="
    )
    assert json_decode_error_url.decode_mandrillapp() == ""

    unicode_decode_error_url = URL("https://mandrillapp.com/track/click/30233568/domain.com?p=eyJzasdf")
    assert unicode_decode_error_url.decode_mandrillapp() == ""


def test_url_decode_outlook_safelink():
    url = URL("https://na01.safelinks.protection.outlook.com/?url=http%3A%2F%2Fdomain.com")
    assert url.child_urls == [URL("http://domain.com")]


def test_url_decode_proofpoint_v2():
    url = URL("https://urldefense.proofpoint.com/v2/url?u=http-3A__domain.com")
    assert url.is_proofpoint_v2 is True
    assert url.child_urls == [URL("http://domain.com")]

    # Test a URL with an incorrect scheme
    url = URL("https://urldefense.proofpoint.com/v2/url?u=http-3A_domain.com")
    assert url.is_proofpoint_v2 is True
    assert url.child_urls == [URL("http://domain.com")]

    keyerror_url = URL("https://urldefense.proofpoint.com/v2/url")
    assert keyerror_url.decode_proofpoint_v2() == ""


def test_url_decode_proofpoint_v3():
    # Test a URL with tokens to replace
    url = URL(
        "https://urldefense.com/v3/__https://domain.com/index.php?token=asdf*2babcd*2b1234*a*b__;fn5-fg!asdf!asdf!asdf-asdf$"
    )
    assert url.is_proofpoint_v3 is True
    assert url.child_urls == [URL("https://domain.com/index.php?token=asdf~2babcd~2b1234~a~b")]

    # Test a URL without any tokens to replace
    url = URL("https://urldefense.com/v3/__https://domain.com/index.php?token=asdf__;!asdf!asdf!asdf-asdf$")
    assert url.is_proofpoint_v3 is True
    assert url.child_urls == [URL("https://domain.com/index.php?token=asdf")]

    # Test a URL with an incorrect scheme
    url = URL("https://urldefense.com/v3/__https:/domain.com/index.php?token=asdf__;!asdf!asdf!asdf-asdf$")
    assert url.is_proofpoint_v3 is True
    assert url.child_urls == [URL("https://domain.com/index.php?token=asdf")]

    error_url = URL("https://urldefense.com/v3/____;")
    assert error_url.decode_proofpoint_v3() == ""

    # Test a URL that has more than 1 asterisk token
    url = URL(
        "https://urldefense.com/v3/__https://link.edgepilot.com/s/822cebfe/5ZxIVsowtUueiP3V0OatBg?u=https:**Ago.microsoft.com*fwlink**ALinkid=844050__;Ly8vLz8!!NAqySMJg!B2KGwyFP3G5bqSRMBCEyMq9ccomB-Bybhf53qbl7ZlsYnJ3UKkAO0beFX-yj1V-raXJsLn3FHZlSQTjIvxO4_2Y$"
    )
    assert url.is_proofpoint_v3 is True
    assert url.child_urls == ["https://link.edgepilot.com/s/822cebfe/5ZxIVsowtUueiP3V0OatBg?u=https://go.microsoft.com/fwlink/?Linkid=844050"]

def test_url_get_fragment_values():
    url = URL("https://domain.com/index.php#a=1&b=2&c=3")
    assert url.get_fragment_values() == {"1", "2", "3"}


def test_url_get_query_values():
    url = URL("https://domain.com/index.php?a=1&b=2&c=3")
    assert url.get_query_values() == {"1", "2", "3"}


def test_url_less_than():
    assert URL("http://domain.com") < URL("http://domain2.com")
    assert (URL("http://domain.com") < "http://domain2.com") is False


def test_url_netlocs():
    idna_url = URL("http://xn--n28h.com")
    assert idna_url.netloc_idna == "xn--n28h.com"
    assert idna_url.netloc_original == "xn--n28h.com"
    assert idna_url.netloc_unicode == "😉.com"

    unicode_url = URL("http://😉.com")
    assert unicode_url.netloc_idna == "xn--n28h.com"
    assert unicode_url.netloc_original == "😉.com"
    assert unicode_url.netloc_unicode == "😉.com"

    url = URL("http://DOMAIN.COM")
    assert url.netloc_idna == "domain.com"
    assert url.netloc_original == "domain.com"
    assert url.netloc_unicode == "domain.com"


def test_url_netloc_unicode_twice():
    """This test is purely for code coverage."""
    url = URL("http://domain.com")
    assert url.netloc_unicode == "domain.com"
    assert url.netloc_unicode == "domain.com"


def test_url_original_url():
    assert (
        URL("http://domain.com/test_path?test_query=1<2#😉").original_url
        == "http://domain.com/test_path?test_query=1<2#😉"
    )


def test_url_paths():
    decoded_url = URL("http://domain.com/test_path?test_query=1<2#😉")
    assert decoded_url.path_all_decoded == "/test_path?test_query=1<2#😉"
    assert decoded_url.path_html_decoded == "/test_path?test_query=1<2#😉"
    assert decoded_url.path_html_encoded == "/test_path?test_query=1&lt;2#😉"
    assert decoded_url.path_original == "/test_path?test_query=1<2#😉"
    assert decoded_url.path_percent_decoded == "/test_path?test_query=1<2#😉"
    assert decoded_url.path_percent_encoded == "/test_path%3Ftest_query%3D1%3C2%23%F0%9F%98%89"

    html_encoded_url = URL("http://domain.com/test_path?test_query=1&lt;2#😉")
    assert html_encoded_url.path_all_decoded == "/test_path?test_query=1<2#😉"
    assert html_encoded_url.path_html_decoded == "/test_path?test_query=1<2#😉"
    assert html_encoded_url.path_html_encoded == "/test_path?test_query=1&lt;2#😉"
    assert html_encoded_url.path_original == "/test_path?test_query=1&lt;2#😉"
    assert html_encoded_url.path_percent_decoded == "/test_path?test_query=1&lt;2#😉"
    assert html_encoded_url.path_percent_encoded == "/test_path%3Ftest_query%3D1%3C2%23%F0%9F%98%89"

    percent_encoded_url = URL("http://domain.com/test_path%3Ftest_query%3D1%3C2%23%F0%9F%98%89")
    assert percent_encoded_url.path_all_decoded == "/test_path?test_query=1<2#😉"
    assert percent_encoded_url.path_html_decoded == "/test_path%3Ftest_query%3D1%3C2%23%F0%9F%98%89"
    assert percent_encoded_url.path_html_encoded == "/test_path?test_query=1&lt;2#😉"
    assert percent_encoded_url.path_original == "/test_path%3Ftest_query%3D1%3C2%23%F0%9F%98%89"
    assert percent_encoded_url.path_percent_decoded == "/test_path?test_query=1<2#😉"
    assert percent_encoded_url.path_percent_encoded == "/test_path%3Ftest_query%3D1%3C2%23%F0%9F%98%89"

    mixed_encoded_url = URL("http://domain.com/test_path%3Ftest_query%3D1&lt;2%23%F0%9F%98%89")
    assert mixed_encoded_url.path_all_decoded == "/test_path?test_query=1<2#😉"
    assert mixed_encoded_url.path_html_decoded == "/test_path%3Ftest_query%3D1<2%23%F0%9F%98%89"
    assert mixed_encoded_url.path_html_encoded == "/test_path?test_query=1&lt;2#😉"
    assert mixed_encoded_url.path_original == "/test_path%3Ftest_query%3D1&lt;2%23%F0%9F%98%89"
    assert mixed_encoded_url.path_percent_decoded == "/test_path?test_query=1&lt;2#😉"
    assert mixed_encoded_url.path_percent_encoded == "/test_path%3Ftest_query%3D1%3C2%23%F0%9F%98%89"


def test_url_permutations():
    url = URL("http://faß.de/test_path?test_query=1<2#😉")
    expected_permutations = {
        "http://faß.de/test_path?test_query=1<2#😉",
        "http://faß.de/test_path?test_query=1&lt;2#😉",
        "http://faß.de/test_path%3Ftest_query%3D1%3C2%23%F0%9F%98%89",
        "http://xn--fa-hia.de/test_path?test_query=1<2#😉",
        "http://xn--fa-hia.de/test_path?test_query=1&lt;2#😉",
        "http://xn--fa-hia.de/test_path%3Ftest_query%3D1%3C2%23%F0%9F%98%89",
    }
    assert url.permutations == expected_permutations


def test_url_split_value():
    assert URL("http://domain.com").split_value == urlsplit("http://domain.com")


def test_urllist_append():
    urllist = URLList()
    urllist.append("http://domain.com")
    urllist.append("domain")
    urllist.append("http://d😉o😉m😉a😉i😉n😉2😉.😉c😉o😉m"),
    urllist.append("email@domain3.com")
    assert urllist == ["http://domain.com", "http://domain2.com"]


def test_urllist_equal():
    assert URLList(["http://domain.com", "http://domain2.com"]) == ["http://domain2.com", "http://domain.com"]
    assert URLList(["http://domain.com", "http://domain2.com"]) == URLList(["http://domain2.com", "http://domain.com"])
    assert URLList(["http://domain.com"]) != "http://domain.com"


def test_urllist_get_all_urls_double_nested():
    urllist = URLList(
        [
            URL("http://domain.com"),
            URL(
                "https://protect2.fireeye.com/url?k=225eb64e-7e024241-225e9cd6-0cc47a33347c-67785364a067dbfc&u=https://mandrillapp.com/track/click/30233568/domain.com?p=eyJzIjoiQnU1NFZhQV9RUTJyTnA0OGxZVllHdFZIdVVzIiwidiI6MSwicCI6IntcInVcIjozMDIzMzU2OCxcInZcIjoxLFwidXJsXCI6XCJodHRwOlxcXC9cXFwvZG9tYWluLmNvbVxcXC90ZXN0XCIsXCJpZFwiOlwiMjIyMjk4YmUyNGU0NDE4MzhlMDFmZjcxN2ZlNzE5YjFcIixcInVybF9pZHNcIjpbXCI5ODdjODQ1Y2ZmZGRmYTU4MjYxN2Y5NDFjZmNmNTE4NmU0MGZlNjY5XCJdfSJ9Cg=="
            ),
        ]
    )
    assert len(urllist) == 2

    expected_urls = {
        URL("http://domain.com"),
        URL(
            "https://protect2.fireeye.com/url?k=225eb64e-7e024241-225e9cd6-0cc47a33347c-67785364a067dbfc&u=https://mandrillapp.com/track/click/30233568/domain.com?p=eyJzIjoiQnU1NFZhQV9RUTJyTnA0OGxZVllHdFZIdVVzIiwidiI6MSwicCI6IntcInVcIjozMDIzMzU2OCxcInZcIjoxLFwidXJsXCI6XCJodHRwOlxcXC9cXFwvZG9tYWluLmNvbVxcXC90ZXN0XCIsXCJpZFwiOlwiMjIyMjk4YmUyNGU0NDE4MzhlMDFmZjcxN2ZlNzE5YjFcIixcInVybF9pZHNcIjpbXCI5ODdjODQ1Y2ZmZGRmYTU4MjYxN2Y5NDFjZmNmNTE4NmU0MGZlNjY5XCJdfSJ9Cg=="
        ),
        URL(
            "https://mandrillapp.com/track/click/30233568/domain.com?p=eyJzIjoiQnU1NFZhQV9RUTJyTnA0OGxZVllHdFZIdVVzIiwidiI6MSwicCI6IntcInVcIjozMDIzMzU2OCxcInZcIjoxLFwidXJsXCI6XCJodHRwOlxcXC9cXFwvZG9tYWluLmNvbVxcXC90ZXN0XCIsXCJpZFwiOlwiMjIyMjk4YmUyNGU0NDE4MzhlMDFmZjcxN2ZlNzE5YjFcIixcInVybF9pZHNcIjpbXCI5ODdjODQ1Y2ZmZGRmYTU4MjYxN2Y5NDFjZmNmNTE4NmU0MGZlNjY5XCJdfSJ9Cg=="
        ),
        URL("http://domain.com/test"),
    }

    assert urllist.get_all_urls() == expected_urls


def test_urllist_get_all_urls_empty():
    urllist = URLList([])
    assert len(urllist) == 0
    assert urllist.get_all_urls() == set()
