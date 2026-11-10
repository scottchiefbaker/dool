"""Unit tests for text_wrap() with a non-comma delimiter.

The dool script imports the Unix-only `resource` module at top level, so on
platforms without it (e.g. Windows) provide a minimal stub before loading.
Only resource.getpagesize is stubbed; it is never called by text_wrap().
"""
import sys
import unittest
from types import SimpleNamespace

try:
    import resource  # noqa: F401
except ImportError:  # pragma: no cover - non-Unix platforms only
    sys.modules["resource"] = SimpleNamespace(getpagesize=lambda: 4096)

from load_dool import dool


class TestTextWrapDelim(unittest.TestCase):
    def test_other_delimiter_is_honored(self):
        self.assertEqual(dool.text_wrap("a:b:c", ":", 80), ["a:b:c"])

    def test_other_delimiter_wraps(self):
        self.assertEqual(
            dool.text_wrap("one:two:three:four", ":", 8),
            ["one:two", "three", "four"],
        )

    def test_no_comma_leaks_with_other_delimiter(self):
        for line in dool.text_wrap("one:two:three:four", ":", 8):
            with self.subTest(line=line):
                self.assertNotIn(",", line)


if __name__ == "__main__":
    unittest.main()
