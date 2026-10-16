import urlfinderlib.finders as finders


def test_create_text():
    assert finders.TextUrlFinder("test")


def test_find_urls_returns_strings():
    urls = finders.TextUrlFinder("see http://domain.com/x").find_urls()
    assert urls == {"http://domain.com/x"}
    assert all(type(url) is str for url in urls)
