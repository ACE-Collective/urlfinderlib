import urlfinderlib.finders

html = b"""
<html xmlns="xmlns">
    <head>
        <base href="http://domain.com">
        <meta HTTP-EQUIV="REFRESH" CONTENT="0; url=http://domain.com/meta">
    </head>

    <body background="background">
        <script>
            document.write (unescape('<meta HTTP-EQUIV="REFRESH" CONTENT="0; url=http://domain2.com/re.php">') ) ;
        </script>

        <style>
            #obf{
                color: transparent;
                display: none;
                height: 0;
                max-height: 0;
                max-width: 0;
                opacity: 0;
                overflow: hidden;
                mso-hide: all;
                visibility: ;
            }
        </style>

        <font id="obf">asdf</font>http://domain3.<font id="obf">asdf</font>com

        <form action="action"></form>

        <div style="background-image: url('css');">

        <a href="href"></a>

        <img src="src">

        <div id="id"></div>
    </body>
</html>"""


def test_find_urls():
    finder = urlfinderlib.finders.HtmlUrlFinder(html)
    expected_urls = {
        "http://domain.com/xmlns",
        "http://domain.com",
        "http://domain.com/background",
        "http://domain.com/meta",
        "http://domain2.com/re.php",
        "http://domain3.com",
        "http://domain.com/action",
        "http://domain.com/css",
        "http://domain.com/href",
        "http://domain.com/src",
    }
    assert finder.find_urls() == expected_urls


def test_find_urls_missing_root():
    this_html = b"""<html><head><script>document.write('</style>');</script></head></html>"""
    finder = urlfinderlib.finders.HtmlUrlFinder(this_html)
    assert finder.find_urls() == set()


def test_find_urls_using_manual_base_url():
    this_html = b"""<html><head></head><body><a href="index.php"></a></body></html>"""
    finder = urlfinderlib.finders.HtmlUrlFinder(this_html, base_url="http://domain.com")
    assert finder.find_urls() == {"http://domain.com/index.php"}
