import contextlib
import unittest
from io import StringIO
from unittest import mock

from load_dool import dool


def make_options(args):
    with contextlib.redirect_stdout(StringIO()):
        return dool.Options(args)


# A theme with readable markers instead of ANSI codes, so assertions check
# the layout logic rather than escape sequences.
STUB_THEME = {
    'error': '<error>', 'default': '<default>',
    'text_lo': '<text_lo>', 'text_hi': '<text_hi>',
    'unit_lo': '<unit_lo>', 'unit_hi': '<unit_hi>',
    'done_lo': '<done_lo>', 'done_hi': '<done_hi>',
    'colors_lo': tuple('L%d' % i for i in range(8)),
    'colors_hi': tuple('H%d' % i for i in range(8)),
}


class FormatCase(unittest.TestCase):
    """Patches the dool globals that cprint() reads: theme, op, step."""

    def setUp(self):
        self.op = make_options(['-t'])
        self.step = 1  # step == op.delay selects the faded _lo colors
        patches = [
            mock.patch.object(dool, 'theme', STUB_THEME, create=True),
            mock.patch.object(dool, 'op', self.op, create=True),
            mock.patch.object(dool, 'step', self.step, create=True),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def set_step(self, step):
        dool.step = step


class TestDchgBoundaries(unittest.TestCase):
    def test_exact_width_does_not_scale(self):
        self.assertEqual(dool.dchg(9999, 4, 1000), ('9999', 0))

    def test_one_over_width_scales(self):
        self.assertEqual(dool.dchg(10000, 4, 1000), ('10', 1))

    def test_negative_is_not_special_cased(self):
        # cprint() handles negatives before calling dchg(); dchg itself just
        # formats the number.
        self.assertEqual(dool.dchg(-5, 4, 1000), ('-5', 0))


class TestFchgBoundaries(unittest.TestCase):
    def test_integer_part_fills_width(self):
        self.assertEqual(dool.fchg(123.4, 4, 1000), ('123', 0))

    def test_small_fraction_keeps_precision(self):
        self.assertEqual(dool.fchg(0.05, 4, 1000), ('0.05', 0))


class TestCprintLayout(FormatCase):
    def test_zero_uses_unit_color(self):
        self.assertEqual(dool.cprint(0, 'd', 4, 1000), '<unit_lo>  0 ')

    def test_negative_renders_dash_in_error_color(self):
        self.assertEqual(dool.cprint(-5, 'f', 4, 1000), '<error>  - <default>')

    def test_scaled_value_gets_unit_letter(self):
        # width 4 minus the unit column leaves 3 chars; 1500 -> 1.5 -> '2' (round half to even)
        self.assertEqual(dool.cprint(1500, 'd', 4, 1000), 'L1  2<unit_lo>k')

    def test_float_value_uses_fchg(self):
        # width 3 after the unit column, so '1.2' takes it all with no padding
        self.assertEqual(dool.cprint(1234, 'f', 4, 1000), 'L11.2<unit_lo>k')

    def test_unscaled_value_has_no_unit(self):
        self.assertEqual(dool.cprint(5, 'd', 4, 0), '<text_lo>   5')

    def test_percent_under_100_uses_text_color(self):
        self.assertEqual(dool.cprint(1, 'p', 4, 1000), '<text_lo>  1<unit_lo> ')

    def test_percent_at_100_uses_done_color(self):
        self.assertEqual(dool.cprint(100, 'p', 4, 1000), '<done_lo>100<unit_lo> ')

    def test_time_is_formatted_with_tchg(self):
        self.assertEqual(dool.cprint(90, 't', 4, 0), '<text_lo>  1h')

    def test_string_is_left_justified(self):
        self.assertEqual(dool.cprint('ab', 's', 4, 0), '<text_lo>ab  ')

    def test_string_with_unit_scale_has_no_unit(self):
        # Regression: used to raise TypeError indexing units[] with a color string
        self.assertEqual(dool.cprint('ab', 's', 4, 1000), '<text_lo>ab  ')

    def test_time_with_unit_scale_has_no_unit(self):
        # Regression: used to raise TypeError indexing units[] with a color string
        self.assertEqual(dool.cprint(90, 't', 4, 1000), '<text_lo>  1h')

    def test_unknown_type_raises(self):
        with self.assertRaises(Exception):
            dool.cprint(1, 'z', 4, 1000)


class TestCprintColors(FormatCase):
    def test_faded_step_uses_lo_colors(self):
        # step == op.delay is an interim update
        self.assertEqual(dool.cprint(1500, 'd', 4, 1000), 'L1  2<unit_lo>k')

    def test_bright_step_uses_hi_colors(self):
        self.set_step(2)
        self.assertEqual(dool.cprint(1500, 'd', 4, 1000), 'H1  2<unit_hi>k')

    def test_scale_not_1000_uses_value_bucket_color(self):
        # 2 * 10 = 20 -> bucket int(20/10) % 8 = 2
        self.assertEqual(dool.cprint(20, 'd', 4, 10), 'L2  20')


class TestCprintBase1024(FormatCase):
    def test_bytes_use_base_1024_units(self):
        self.op.bits = False
        self.assertEqual(dool.cprint(1, 'b', 4, 1024), 'L0  1<unit_lo>B')

    def test_bits_multiply_by_8_and_use_base_1000(self):
        self.op.bits = True
        self.assertEqual(dool.cprint(1, 'b', 4, 1024), 'L0  8<unit_lo>b')

    def test_bits_scale_up_with_base_1000_units(self):
        # 2048 bytes = 16384 bits -> 16.384 kbit
        self.op.bits = True
        self.assertEqual(dool.cprint(2048, 'b', 4, 1024), 'L1 16<unit_lo>k')

    def test_bytes_base_1024_does_not_multiply(self):
        self.op.bits = False
        self.assertEqual(dool.cprint(2048, 'b', 4, 1024), 'L1  2<unit_lo>K')


class TestCprintList(FormatCase):
    def test_columns_are_joined_with_a_space(self):
        self.assertEqual(dool.cprintlist([1, 2], 'd', 4, 1000),
                         'L0  1<unit_lo>  L0  2<unit_lo> ')

    def test_empty_list(self):
        self.assertEqual(dool.cprintlist([], 'd', 4, 1000), '')


if __name__ == '__main__':
    unittest.main()
