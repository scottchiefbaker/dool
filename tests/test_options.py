import unittest
from contextlib import redirect_stdout
from io import StringIO

from load_dool import dool


class FakeTTY(StringIO):
    def isatty(self):
        return True


def parse(args):
    """Build Options as if run in a terminal, with stdout captured."""
    out = FakeTTY()
    with redirect_stdout(out):
        return dool.Options(args)


class TestOptionsFlags(unittest.TestCase):
    def test_time_plugin(self):
        self.assertEqual(parse(['-t']).plugins, ['time'])

    def test_all_flag_adds_default_plugins(self):
        op = parse(['-a'])
        for name in ['cpu', 'disk', 'net', 'page', 'mem', 'sys', 'proc', 'load']:
            self.assertIn(name, op.plugins)

    def test_full(self):
        self.assertFalse(parse([]).full)
        self.assertTrue(parse(['-f']).full)
        self.assertTrue(parse(['--full']).full)

    def test_bits_and_bytes(self):
        self.assertTrue(parse([]).bits)
        self.assertFalse(parse(['--bytes']).bits)
        self.assertTrue(parse(['--bits']).bits)

    def test_debug_counts_up(self):
        self.assertEqual(parse(['--debug']).debug, 1)
        self.assertEqual(parse(['--debug', '--debug']).debug, 2)

    def test_color_modes(self):
        self.assertEqual(parse(['--color']).color, 256)
        self.assertEqual(parse(['--color16']).color, 16)
        self.assertFalse(parse(['--nocolor']).color)

    def test_delay_and_count_positional(self):
        op = parse(['-t', '2', '7'])
        self.assertEqual(op.delay, 2)
        self.assertEqual(op.count, 7)

    def test_default_delay_and_count(self):
        op = parse(['-t'])
        self.assertEqual(op.delay, 1)
        self.assertEqual(op.count, -1)


class TestOptionsLists(unittest.TestCase):
    def test_intlist(self):
        self.assertEqual(parse(['-I', 'eth0,eth1']).intlist, ['eth0', 'eth1'])

    def test_netlist(self):
        self.assertEqual(parse(['-N', 'eth0,eth1']).netlist, ['eth0', 'eth1'])

    def test_swaplist(self):
        self.assertEqual(parse(['-S', 'sda,sdb']).swaplist, ['sda', 'sdb'])


class TestOptionsErrors(unittest.TestCase):
    def assertExits(self, args, code):
        with redirect_stdout(StringIO()):
            with self.assertRaises(SystemExit) as cm:
                dool.Options(args)
        self.assertEqual(cm.exception.code, code)

    def test_unknown_option_exits_1(self):
        self.assertExits(['--definitely-not-an-option'], 1)

    def test_float_and_integer_exclusive(self):
        self.assertExits(['--float', '--integer'], 1)

    def test_zero_delay_exits_1(self):
        self.assertExits(['-t', '0'], 1)

    def test_non_integer_delay_exits_1(self):
        self.assertExits(['-t', 'abc'], 1)


if __name__ == '__main__':
    unittest.main()
