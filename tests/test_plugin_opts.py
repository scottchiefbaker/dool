"""Tests for get_plugin_file_opts(): reading DOOL_OPTS from a plugin's header."""
import os
import tempfile
import unittest

from load_dool import dool


class TestGetPluginFileOpts(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix='.py')
        os.close(fd)
        self.addCleanup(os.remove, self.path)

    def write(self, text):
        with open(self.path, 'w') as f:
            f.write(text)

    def test_opts_are_split_on_commas(self):
        self.write('# DOOL_OPTS: foo,bar,baz\nprint(1)\n')
        self.assertEqual(dool.get_plugin_file_opts(self.path), ['foo', 'bar', 'baz'])

    def test_no_marker_returns_empty_list(self):
        self.write('# just a plugin\n')
        self.assertEqual(dool.get_plugin_file_opts(self.path), [])

    def test_single_opt(self):
        self.write('DOOL_OPTS: only\n')
        self.assertEqual(dool.get_plugin_file_opts(self.path), ['only'])

    def test_marker_without_space_after_colon(self):
        self.write('DOOL_OPTS:tight\n')
        self.assertEqual(dool.get_plugin_file_opts(self.path), ['tight'])

    def test_value_stops_at_end_of_line(self):
        self.write('DOOL_OPTS: a,b\nDOOL_OPTS: ignored\n')
        self.assertEqual(dool.get_plugin_file_opts(self.path), ['a', 'b'])

    def test_marker_beyond_first_256_bytes_is_ignored(self):
        self.write('x' * 300 + '\nDOOL_OPTS: late\n')
        self.assertEqual(dool.get_plugin_file_opts(self.path), [])


if __name__ == '__main__':
    unittest.main()
