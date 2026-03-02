import urlfinderlib.helpers as helpers


def test_build_url():
    assert helpers.build_url("http", "domain.com", "/index.php?test") == "http://domain.com/index.php?test"


def test_fix_possible_url():
    assert helpers.fix_possible_url("//domain.com\\index\u0000.html") == "https://domain.com/index.html"


def test_fix_possible_value():
    assert helpers.fix_possible_value('"//domain.com\\index\u0000.html"') == "//domain.com/index.html"


def test_fix_slashes():
    assert helpers.fix_slashes("http:/\\domain.com") == "http://domain.com"
    assert helpers.fix_slashes("http:/domain.com/index.html") == "http://domain.com/index.html"


def test_get_ascii_url():
    assert helpers.get_ascii_url("http://d😉o😉m😉a😉i😉n😉.😉c😉o😉m") == "http://domain.com"


def test_is_base64_ascii():
    assert helpers.is_base64_ascii("asdf") is False
    assert helpers.is_base64_ascii("faß") is False
    assert helpers.is_base64_ascii("YXNkZgo=") is True


def test_might_be_html():
    assert helpers.might_be_html(b'<meta http-equiv="refresh" content="0; URL=https://blah.com/one/two">') is True
    assert helpers.might_be_html(b"https://blah.com/one/two") is False


def test_prepend_missing_scheme():
    assert helpers.prepend_missing_scheme("domain.com") == "domain.com"
    assert helpers.prepend_missing_scheme("domain.com", domain_as_url=True) == "https://domain.com"
    assert helpers.prepend_missing_scheme("domain.com/index.html") == "https://domain.com/index.html"
    assert helpers.prepend_missing_scheme("https://domain.com") == "https://domain.com"
    assert helpers.prepend_missing_scheme("redis://user:pass@domain.com") == "redis://user:pass@domain.com"


def test_prepend_missing_scheme_value_error():
    assert helpers.prepend_missing_scheme("http://dom[ain.com") == "http://dom[ain.com"


def test_remove_mailto_if_not_email_address():
    assert helpers.remove_mailto_if_not_email_address("mailto:http://domain.com") == "http://domain.com"
    assert helpers.remove_mailto_if_not_email_address("mailto:user@domain.com") == "mailto:user@domain.com"


def test_remove_mailto_if_not_email_address_value_error():
    assert helpers.remove_mailto_if_not_email_address("http://dom[ain.com") == "http://dom[ain.com"


def test_remove_null_characters():
    assert helpers.remove_null_characters("http://domain\u0000.com") == "http://domain.com"


def test_remove_surrounding_quotes():
    assert helpers.remove_surrounding_quotes('"test"') == "test"
    assert helpers.remove_surrounding_quotes("'test'") == "test"


def test_strip_trailing_punctuation():
    assert helpers.fix_possible_value("domain.com/path,") == "domain.com/path"
    assert helpers.fix_possible_value("domain.com/path;") == "domain.com/path"
    assert helpers.fix_possible_value("domain.com/path!") == "domain.com/path"
    assert helpers.fix_possible_value("domain.com/path?") == "domain.com/path"
    assert helpers.fix_possible_value("domain.com/path,;!") == "domain.com/path"
    # These should NOT be stripped
    assert helpers.fix_possible_value("domain.com/path.") == "domain.com/path."
    assert helpers.fix_possible_value("http://domain.com:8080") == "http://domain.com:8080"
    assert helpers.fix_possible_value("domain.com/path#frag") == "domain.com/path#frag"
    assert helpers.fix_possible_value("domain.com/path&key=val") == "domain.com/path&key=val"


def test_prepend_missing_scheme_cidr():
    assert helpers.prepend_missing_scheme("0.0.0.0/0") == "0.0.0.0/0"
    assert helpers.prepend_missing_scheme("10.0.0.0/8") == "10.0.0.0/8"
    assert helpers.prepend_missing_scheme("192.168.1.0/24") == "192.168.1.0/24"
    assert helpers.prepend_missing_scheme("0.0.0.0/0", domain_as_url=True) == "0.0.0.0/0"
    # Explicit scheme should still work
    assert helpers.prepend_missing_scheme("http://192.168.1.1/24") == "http://192.168.1.1/24"
    # Non-CIDR paths should still get scheme
    assert helpers.prepend_missing_scheme("192.168.1.1/index.html") == "https://192.168.1.1/index.html"


def test_is_cidr_notation():
    assert helpers._is_cidr_notation("0.0.0.0/0") is True
    assert helpers._is_cidr_notation("10.0.0.0/8") is True
    assert helpers._is_cidr_notation("192.168.1.0/24") is True
    assert helpers._is_cidr_notation("255.255.255.255/32") is True
    # Invalid cases
    assert helpers._is_cidr_notation("999.999.999.999/24") is False
    assert helpers._is_cidr_notation("192.168.1.0/33") is False
    assert helpers._is_cidr_notation("192.168.1.0/index.html") is False
    assert helpers._is_cidr_notation("domain.com/path") is False
    assert helpers._is_cidr_notation("not-cidr") is False
