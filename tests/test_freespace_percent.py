"""Tests for the freespace-percent plugin: percentage math and formatting.

The plugin file is exec'd into its own namespace so the dool_plugin class can
be used without the plugin loader. os.statvfs is replaced with a stub so the
percentage math is deterministic.
"""
import os
import unittest
from collections import namedtuple

from load_dool import dool

PLUGIN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '..', 'plugins', 'dool_freespace_percent.py')

# Field names and order match os.statvfs
Statvfs = namedtuple('Statvfs', ['f_bsize', 'f_frsize', 'f_blocks', 'f_bfree', 'f_bavail'])


class StubOs(object):
    """Just enough of the os module for the plugin: statvfs by path."""

    def __init__(self):
        self.statvfs_results = {}

    def statvfs(self, path):
        return self.statvfs_results[path]


STUB_OS = StubOs()


def load_freespace_percent_plugin():
    namespace = {
        'dool': dool.dool,
        'os': STUB_OS,
        # Minimal stand-ins for the display helpers, so the tests can assert
        # on the formatted values instead of ANSI color codes
        'cprintlist': lambda vals, ctype, width, scale: '|'.join(vals),
        'cprint': lambda var, ctype, width, scale: var,
        'theme': {'subframe': '<'},
        'char': {'colon': ':', 'sep': ','},
        'ansi': {'reset': 'R'},
    }
    with open(PLUGIN_PATH) as f:
        exec(compile(f.read(), PLUGIN_PATH, 'exec'), namespace)
    return namespace['dool_plugin']


PLUGIN_CLASS = load_freespace_percent_plugin()


def statvfs(blocks, bavail, frsize=4096, bfree=None, bsize=4096):
    if bfree is None:
        bfree = bavail
    return Statvfs(f_bsize=bsize, f_frsize=frsize, f_blocks=blocks,
                   f_bfree=bfree, f_bavail=bavail)


def make_plugin(*mounts):
    # __new__ skips __init__: no /etc/mtab is read, the attributes that
    # extract()/show()/showcsv() use are set by hand
    plugin = PLUGIN_CLASS.__new__(PLUGIN_CLASS)
    plugin.vars = list(mounts)
    plugin.val = {'total': (0, 0)}
    plugin.num_fmt = "%5.1f"
    plugin.width = 6
    return plugin


class FreespacePercentExtractTest(unittest.TestCase):

    def test_used_and_free_as_percentages(self):
        STUB_OS.statvfs_results['/data'] = statvfs(1000, 400)
        plugin = make_plugin('/data')
        plugin.extract()

        used, free = plugin.val['/data']
        self.assertAlmostEqual(used, 60.0)
        self.assertAlmostEqual(free, 40.0)

    def test_used_and_free_add_up_to_100(self):
        STUB_OS.statvfs_results['/data'] = statvfs(3000, 1000)
        plugin = make_plugin('/data')
        plugin.extract()

        used, free = plugin.val['/data']
        self.assertAlmostEqual(used + free, 100.0)

    def test_full_filesystem(self):
        # No blocks left for normal users, root reserve counted as used
        STUB_OS.statvfs_results['/data'] = statvfs(100, 0, bfree=5)
        plugin = make_plugin('/data')
        plugin.extract()

        used, free = plugin.val['/data']
        self.assertAlmostEqual(used, 100.0)
        self.assertAlmostEqual(free, 0.0)

    def test_zero_blocks_does_not_divide_by_zero(self):
        STUB_OS.statvfs_results['/data'] = statvfs(0, 0)
        plugin = make_plugin('/data')
        plugin.extract()

        self.assertEqual(plugin.val['/data'], (0.0, 0.0))

    def test_running_total_in_bytes(self):
        STUB_OS.statvfs_results['/a'] = statvfs(1000, 400)
        STUB_OS.statvfs_results['/b'] = statvfs(100, 30, frsize=1024)
        plugin = make_plugin('/a', '/b')
        plugin.extract()

        self.assertEqual(plugin.val['total'],
                         (600 * 4096 + 70 * 1024, 400 * 4096 + 30 * 1024))


class FreespacePercentFormatTest(unittest.TestCase):

    def test_show_has_one_digit_after_the_decimal(self):
        STUB_OS.statvfs_results['/data'] = statvfs(1000, 400)
        plugin = make_plugin('/data')
        plugin.extract()

        self.assertEqual(plugin.show(), ' 60.0%| 40.0%')

    def test_show_rounds_repeating_decimals(self):
        # 2000/3000 = 66.666..%, must render as 66.7
        STUB_OS.statvfs_results['/data'] = statvfs(3000, 1000)
        plugin = make_plugin('/data')
        plugin.extract()

        self.assertEqual(plugin.show(), ' 66.7%| 33.3%')

    def test_show_full_filesystem_fits_the_column(self):
        # 100.0% is the widest possible value, it must fit in one column
        STUB_OS.statvfs_results['/data'] = statvfs(100, 0, bfree=5)
        plugin = make_plugin('/data')
        plugin.extract()

        self.assertEqual(plugin.show(), '100.0%|  0.0%')

    def test_show_separates_mountpoints_with_the_framework_separator(self):
        STUB_OS.statvfs_results['/a'] = statvfs(1000, 400)
        STUB_OS.statvfs_results['/b'] = statvfs(100, 30)
        plugin = make_plugin('/a', '/b')
        plugin.extract()

        self.assertEqual(plugin.show(), ' 60.0%| 40.0%<:R 70.0%| 30.0%')

    def test_showcsv_has_one_digit_after_the_decimal(self):
        STUB_OS.statvfs_results['/data'] = statvfs(1000, 400)
        plugin = make_plugin('/data')
        plugin.extract()

        self.assertEqual(plugin.showcsv(), '60.0,40.0')

    def test_showcsv_cells_stay_numeric_without_the_percent_sign(self):
        STUB_OS.statvfs_results['/a'] = statvfs(1000, 400)
        STUB_OS.statvfs_results['/b'] = statvfs(100, 30)
        plugin = make_plugin('/a', '/b')
        plugin.extract()

        self.assertEqual(plugin.showcsv(), '60.0,40.0,70.0,30.0')


if __name__ == '__main__':
    unittest.main()
