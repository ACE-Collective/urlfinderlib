import os
import runpy
import sys
from io import StringIO
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
    assert "usage: urlfinder" in captured.err


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
