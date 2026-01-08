import pytest

from urlfinderlib.tokenizer import UTF8Tokenizer

bytes_0_char = b"Test with 0 chars"
expected_0_char = []


bytes_1_char = b"%(char)sTest with 1 char"
expected_1_char = []


bytes_2_char = b"%(char)sTest%(char)s with 1 char"
expected_2_char = ["Test"]


bytes_3_char = b"%(char)sTest%(char)s with%(char)s 1 char"
expected_3_char = ["Test", " with"]


def generate_same_character_decorator(character: bytes) -> pytest.mark.parametrize:
    return pytest.mark.parametrize(
        "char_blob,expected",
        [
            (bytes_0_char, expected_0_char),
            (bytes_1_char % {b"char": character}, expected_1_char),
            (bytes_2_char % {b"char": character}, expected_2_char),
            (bytes_3_char % {b"char": character}, expected_3_char),
        ],
    )


bytes_0_open_close = b"Test with 0 open close chars"
expected_0_open_close = []


bytes_1_open_close = b"%(open)sTest with 1 open close chars"
expected_1_open_close = []


bytes_2_open_close = b"%(open)sTest%(close)s with 2 open close chars"
expected_2_open_close = ["Test"]


bytes_3_open_close = b"%(open)sTest%(close)s with 3%(close)s open close chars"
expected_3_open_close = ["Test", "Test%(close)s with 3"]


def generate_open_close_decorator(open_char: bytes, close_char: bytes) -> pytest.mark.parametrize:
    return pytest.mark.parametrize(
        "open_close_blob,expected",
        [
            (bytes_0_open_close, expected_0_open_close),
            (bytes_1_open_close % {b"open": open_char, b"close": close_char}, expected_1_open_close),
            (bytes_2_open_close % {b"open": open_char, b"close": close_char}, expected_2_open_close),
            (
                bytes_3_open_close % {b"open": open_char, b"close": close_char},
                [
                    x % {"open": open_char.decode("utf8"), "close": close_char.decode("utf8")}
                    for x in expected_3_open_close
                ],
            ),
        ],
    )


def test_get_ascii_strings():
    tok = UTF8Tokenizer(b"This is\x8aa test with strings and \xc2\xa9 unicode characters")
    expected = ["This is", "a test with strings and ", " unicode characters"]
    results = tok.get_ascii_strings(length=4)
    assert sorted(results) == sorted(expected)

    expected = ["a test with strings and ", " unicode characters"]
    results = tok.get_ascii_strings(length=8)
    assert sorted(results) == sorted(expected)


def test_get_byte_lines():
    test_bytes = b"""This is a test
that has
multiple
lines."""
    tok = UTF8Tokenizer(test_bytes)
    expected = ["This is a test", "that has", "multiple", "lines."]
    results = list(tok.get_line_tokens())
    assert sorted(results) == sorted(expected)


def test_get_split_bytes():
    tok = UTF8Tokenizer(b"This is a simple\ttest.")
    expected = ["This", "is", "a", "simple", "test."]
    results = tok.get_split_tokens()
    assert sorted(results) == sorted(expected)


def test_get_split_bytes_after_replace():
    tok = UTF8Tokenizer(b'This is a "simple"\t<test].')
    expected = ["This", "is", "a", "simple", "test", "."]
    results = tok.get_split_tokens_after_replace(['"', "<", "]"])
    assert sorted(results) == sorted(expected)


@generate_open_close_decorator(b"<", b">")
def test_get_tokens_between_angle_brackets(open_close_blob, expected):
    tok = UTF8Tokenizer(open_close_blob)
    results = tok.get_tokens_between_angle_brackets(strict=False)
    assert sorted(results) == sorted(expected)


@generate_same_character_decorator(b"`")
def test_get_tokens_between_backticks(char_blob, expected):
    tok = UTF8Tokenizer(char_blob)
    results = tok.get_tokens_between_backticks()
    assert sorted(results) == sorted(expected)


@generate_open_close_decorator(b"[", b"]")
def test_get_tokens_between_brackets(open_close_blob, expected):
    tok = UTF8Tokenizer(open_close_blob)
    results = tok.get_tokens_between_brackets(strict=False)
    assert sorted(results) == sorted(expected)


@generate_open_close_decorator(b"{", b"}")
def test_get_tokens_between_curly_brackets(open_close_blob, expected):
    tok = UTF8Tokenizer(open_close_blob)
    results = tok.get_tokens_between_curly_brackets(strict=False)
    assert sorted(results) == sorted(expected)


@generate_same_character_decorator(b'"')
def test_get_tokens_between_double_quotes(char_blob, expected):
    tok = UTF8Tokenizer(char_blob)
    results = tok.get_tokens_between_double_quotes()
    assert sorted(results) == sorted(expected)


def test_get_tokens_between_open_and_close_sequence():
    tok = UTF8Tokenizer(b"(https://www.domain.com)")
    expected = ["https://www.domain.com"]
    results = tok.get_tokens_between_open_and_close_sequence("(http", ")")
    assert sorted(results) == sorted(expected)


def test_get_tokens_between_open_and_close_sequence_strict():
    blob = b"""<</S/URI/URI(http://domain.com/URI)>>
<</Type/Action/S/URI/URI(http://domain2.com) >>
<< /A << /S /URI /Type /Action /URI (http://domain3.com) >>
"""

    expected = ["http://domain.com/URI", "http://domain2.com", "http://domain3.com"]

    tok = UTF8Tokenizer(blob)
    results = list(tok.get_tokens_between_open_and_close_sequence("(", ")", strict=True))
    assert sorted(results) == sorted(expected)


@generate_open_close_decorator(b"(", b")")
def test_get_tokens_between_parentheses(open_close_blob, expected):
    tok = UTF8Tokenizer(open_close_blob)
    results = tok.get_tokens_between_parentheses(strict=False)
    assert sorted(results) == sorted(expected)


@generate_same_character_decorator(b"'")
def test_get_tokens_between_single_quotes(char_blob, expected):
    tok = UTF8Tokenizer(char_blob)
    results = tok.get_tokens_between_single_quotes()
    assert sorted(results) == sorted(expected)


def test_get_tokens_between_spaces():
    tok = UTF8Tokenizer(b"This is a simple test with spaces in it.")
    expected = ["is", "a", "simple", "test", "with", "spaces", "in"]
    results = tok.get_tokens_between_spaces()
    assert sorted(results) == sorted(expected)


def test_get_tokens_between_spaces_after_replace():
    tok = UTF8Tokenizer(b'This is a "simple" <test].')
    expected = ["is", "a", "simple", "test"]
    results = tok.get_tokens_between_spaces_after_replace(['"', "<", "]"])
    assert sorted(results) == sorted(expected)


def test_non_utf8():
    tok = UTF8Tokenizer(b"This is a simple\x00 test\x8a.")
    expected = ["This", "is", "a", "simple\x00", "test."]
    results = tok.get_split_tokens()
    assert sorted(results) == sorted(expected)
