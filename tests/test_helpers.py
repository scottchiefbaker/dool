import linecache
import math
import os
import tempfile
import unittest
from io import StringIO
from unittest import mock

from load_dool import dool


class FakeTTY(StringIO):
    def isatty(self):
        return True


class TestDchg(unittest.TestCase):
    def test_fits_without_scaling(self):
        self.assertEqual(dool.dchg(1234, 4, 1000), ('1234', 0))

    def test_zero(self):
        self.assertEqual(dool.dchg(0, 4, 1000), ('0', 0))

    def test_scales_down_once(self):
        self.assertEqual(dool.dchg(12345, 4, 1000), ('12', 1))

    def test_rounds_up_to_next_scale(self):
        self.assertEqual(dool.dchg(999999, 4, 1000), ('1000', 1))

    def test_inf(self):
        self.assertEqual(dool.dchg(math.inf, 4, 1000), ('Inf', 0))


class TestFchg(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(dool.fchg(0, 4, 1000), ('0', 0))

    def test_decimals_fill_width(self):
        self.assertEqual(dool.fchg(1.5, 4, 1000), ('1.50', 0))
        self.assertEqual(dool.fchg(0.5, 4, 1000), ('0.50', 0))

    def test_truncates_to_width(self):
        self.assertEqual(dool.fchg(12.345, 4, 1000), ('12.3', 0))

    def test_scales_down_once(self):
        self.assertEqual(dool.fchg(123456.7, 4, 1000), ('123', 1))


class TestTchg(unittest.TestCase):
    def test_minutes_as_hours_and_minutes(self):
        # Full 'HHhMM' form does not fit width 4, so falls back to 'Nh'
        self.assertEqual(dool.tchg(5, 4), ' 0h')
        self.assertEqual(dool.tchg(90, 4), ' 1h')

    def test_hours(self):
        self.assertEqual(dool.tchg(30 * 60, 4), '30h')

    def test_days_when_hours_too_wide(self):
        # 480h does not fit width 3, so it falls back to days
        self.assertEqual(dool.tchg(60 * 24 * 20, 3), '20d')

    def test_weeks_when_days_too_wide(self):
        self.assertEqual(dool.tchg(60 * 24 * 7 * 150, 3), '150w')


class TestColors(unittest.TestCase):
    def test_fg_color_escape(self):
        self.assertEqual(dool.fg_color(9), '\033[38;5;9m')

    def test_bg_color_escape(self):
        self.assertEqual(dool.bg_color(9), '\033[48;5;9m')

    def test_text_color_wraps_when_tty(self):
        with mock.patch('sys.stdout', FakeTTY()):
            self.assertEqual(dool.text_color(9, 'x'), '\033[38;5;9mx\033[0m')

    def test_text_color_plain_when_not_tty(self):
        with mock.patch('sys.stdout', StringIO()):
            self.assertEqual(dool.text_color(9, 'x'), 'x')


class TestBasename(unittest.TestCase):
    def test_basename(self):
        self.assertEqual(dool.basename('/a/b/c.txt'), 'c.txt')
        self.assertEqual(dool.basename('c.txt'), 'c.txt')


class TestProcHelpers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, 'fake_proc')
        with open(self.path, 'w') as f:
            f.write('alpha 1 2\nbeta 3 4\n')
        # proc_* use linecache, which caches file contents by path
        linecache.clearcache()

    def tearDown(self):
        linecache.clearcache()
        self.tmp.cleanup()

    def test_proc_readline_first_line(self):
        self.assertEqual(dool.proc_readline(self.path), 'alpha 1 2\n')

    # Note: with the default sep=None, str.split() strips the trailing newline.
    # With an explicit separator, the newline stays in the last field.
    def test_proc_splitline_first_line(self):
        self.assertEqual(dool.proc_splitline(self.path), ['alpha', '1', '2'])
        self.assertEqual(dool.proc_splitline(self.path, ' '), ['alpha', '1', '2\n'])

    def test_proc_readlines_all_lines(self):
        self.assertEqual(list(dool.proc_readlines(self.path)),
                         ['alpha 1 2\n', 'beta 3 4\n'])

    def test_proc_splitlines_all_lines(self):
        self.assertEqual(list(dool.proc_splitlines(self.path)),
                         [['alpha', '1', '2'], ['beta', '3', '4']])


class TestFileSlurp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, 'data')
        with open(self.path, 'w') as f:
            f.write('hello world\n')

    def tearDown(self):
        self.tmp.cleanup()

    def test_reads_whole_file(self):
        self.assertEqual(dool.file_slurp(self.path), 'hello world\n')

    def test_size_limits_bytes_read(self):
        self.assertEqual(dool.file_slurp(self.path, 5), 'hello')

    def test_missing_file_raises_file_not_found(self):
        # Regression: used to raise UnboundLocalError from the finally block
        with self.assertRaises(FileNotFoundError):
            dool.file_slurp(os.path.join(self.tmp.name, 'nope'))


if __name__ == '__main__':
    unittest.main()
