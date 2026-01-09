import os
import runpy
import sys
from unittest import mock

import pytest

from urlfinderlib.__main__ import main

this_dir = os.path.dirname(os.path.realpath(__file__))
files_dir = os.path.realpath(f"{this_dir}/files")


def test_main_finds_urls(capsys):
    """Test that main() finds and prints URLs from a file."""
    test_file = f"{files_dir}/test.csv"

    with mock.patch.object(sys, "argv", ["urlfinder", test_file]):
        main()

    captured = capsys.readouterr()
    assert "http://domain.com" in captured.out
    assert "http://domain2.com" in captured.out
    assert "http://domain3.com" in captured.out


def test_main_no_arguments(capsys):
    """Test that main() prints usage and exits with code 2 when no file path is provided."""
    with mock.patch.object(sys, "argv", ["urlfinder"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "usage:" in captured.err.lower()


def test_main_file_not_found():
    """Test that main() exits with code 1 when file does not exist."""
    with mock.patch.object(sys, "argv", ["urlfinder", "/nonexistent/file.txt"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1


def test_main_module_execution(capsys):
    """Test that the module can be executed directly via runpy."""
    test_file = f"{files_dir}/test.csv"

    with mock.patch.object(sys, "argv", ["urlfinderlib", test_file]):
        runpy.run_module("urlfinderlib", run_name="__main__", alter_sys=True)

    captured = capsys.readouterr()
    assert "http://domain.com" in captured.out


def test_main_module_execution_no_args():
    """Test that running module without args exits with error."""
    with mock.patch.object(sys, "argv", ["urlfinderlib"]):
        with pytest.raises(SystemExit) as exc_info:
            runpy.run_module("urlfinderlib", run_name="__main__", alter_sys=True)

    assert exc_info.value.code == 2


def test_main_with_base_url(capsys):
    """Test that main() passes base_url to find_urls."""
    test_file = f"{files_dir}/test_no_base_url.html"

    with mock.patch.object(sys, "argv", ["urlfinder", "-b", "https://example.com", test_file]):
        main()

    captured = capsys.readouterr()
    assert "http://domain.com" in captured.out


def test_main_with_mimetype(capsys):
    """Test that main() passes mimetype to find_urls."""
    test_file = f"{files_dir}/test.csv"

    with mock.patch.object(sys, "argv", ["urlfinder", "-m", "text/plain", test_file]):
        main()

    captured = capsys.readouterr()
    assert "http://domain.com" in captured.out


def test_main_with_domain_as_url(capsys):
    """Test that main() passes domain_as_url to find_urls."""
    test_file = f"{files_dir}/domain_as_url.txt"

    # Without --domain-as-url, standalone domains should not be treated as URLs
    with mock.patch.object(sys, "argv", ["urlfinder", test_file]):
        main()

    captured = capsys.readouterr()
    # somefakesite.com without path should not appear as a URL
    assert "http://somefakesite.com\n" not in captured.out

    # With --domain-as-url, standalone domains should be treated as URLs
    with mock.patch.object(sys, "argv", ["urlfinder", "-d", test_file]):
        main()

    captured = capsys.readouterr()
    assert "https://somefakesite.com" in captured.out


def test_main_with_verbose():
    """Test that main() enables debug logging with --verbose."""
    test_file = f"{files_dir}/test.csv"

    with mock.patch("urlfinderlib.__main__.logging.basicConfig") as mock_basic_config:
        with mock.patch.object(sys, "argv", ["urlfinder", "-v", test_file]):
            main()

        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == 10  # logging.DEBUG


def test_main_help(capsys):
    """Test that main() prints help with -h flag."""
    with mock.patch.object(sys, "argv", ["urlfinder", "-h"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "usage:" in captured.out.lower()
    assert "--base-url" in captured.out
    assert "--mimetype" in captured.out
    assert "--domain-as-url" in captured.out
    assert "--verbose" in captured.out
