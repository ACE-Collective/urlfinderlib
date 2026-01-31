import urlfinderlib.finders as finders


def test_create_text():
    assert finders.TextUrlFinder("test")


def test_ocr_safe_filters_short_domains():
    """Test that OCR-safe mode filters domains with short labels."""
    # Use angle brackets to ensure domains are extracted by both token iterators
    # (angle brackets make token_iter extract the domain, space separation makes split_token_iter extract it)
    text = b"Check <ng.cam> and ur.com and example.com"
    finder = finders.TextUrlFinder(text)

    # Without OCR-safe, short domains should be found
    urls = finder.find_urls(domain_as_url=True, ocr_safe=False)
    assert any("ng.cam" in str(u) for u in urls)
    assert any("ur.com" in str(u) for u in urls)
    assert any("example.com" in str(u) for u in urls)

    # With OCR-safe, short domains should be filtered
    urls = finder.find_urls(domain_as_url=True, ocr_safe=True)
    assert not any("ng.cam" in str(u) for u in urls)
    assert not any("ur.com" in str(u) for u in urls)
    assert any("example.com" in str(u) for u in urls)


def test_ocr_safe_filters_non_ascii_domains():
    """Test that OCR-safe mode filters domains with non-ASCII characters."""
    text = "Check \u00ab\u2122.470s.is and example.com".encode("utf-8")
    finder = finders.TextUrlFinder(text)

    # With OCR-safe, non-ASCII domains should be filtered
    urls = finder.find_urls(domain_as_url=True, ocr_safe=True)
    assert not any("470s.is" in str(u) for u in urls)
    assert any("example.com" in str(u) for u in urls)


def test_ocr_safe_preserves_valid_domains():
    """Test that OCR-safe mode preserves legitimate domains."""
    text = b"Visit google.com and microsoft.com and github.io"
    finder = finders.TextUrlFinder(text)

    urls = finder.find_urls(domain_as_url=True, ocr_safe=True)
    assert any("google.com" in str(u) for u in urls)
    assert any("microsoft.com" in str(u) for u in urls)
    assert any("github.io" in str(u) for u in urls)


def test_ocr_safe_domain_validation_rules():
    """Test the individual OCR-safe domain validation rules."""
    finder = finders.TextUrlFinder(b"")

    # Rule 1: Non-ASCII should fail
    assert not finder._is_ocr_safe_domain("\u00ab\u2122.example.com")

    # Rule 2: Short labels (< 3 chars) should fail
    assert not finder._is_ocr_safe_domain("ng.cam")
    assert not finder._is_ocr_safe_domain("ur.com")
    assert not finder._is_ocr_safe_domain("a.b.com")

    # Rule 3: Total length < 4 should fail
    assert not finder._is_ocr_safe_domain("abc.com")  # 3 chars, fails rule 3

    # Valid domains should pass
    assert finder._is_ocr_safe_domain("example.com")
    assert finder._is_ocr_safe_domain("test.example.com")
    assert finder._is_ocr_safe_domain("abcd.io")  # 4 chars, passes

    # Domain without dots should fail (less than 2 parts)
    assert not finder._is_ocr_safe_domain("nodots")
    assert not finder._is_ocr_safe_domain("localhost")
