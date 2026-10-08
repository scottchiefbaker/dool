import os
import tempfile
import unittest
from types import SimpleNamespace

from load_dool import dool


class TestCsvQuoteStringCell(unittest.TestCase):
    def test_plain_text_is_quoted(self):
        self.assertEqual(dool.csv_quote_string_cell('abc'), '"abc"')

    def test_empty_string(self):
        self.assertEqual(dool.csv_quote_string_cell(''), '""')

    def test_embedded_quote_is_doubled(self):
        self.assertEqual(dool.csv_quote_string_cell('a"b'), '"a""b"')

    def test_formula_prefixes_are_neutralized(self):
        for prefix in ['=', '+', '-', '@']:
            with self.subTest(prefix=prefix):
                self.assertEqual(dool.csv_quote_string_cell(prefix + 'x'),
                                 "\"'" + prefix + "x\"")

    def test_prefix_only_checked_at_start(self):
        self.assertEqual(dool.csv_quote_string_cell('a=1'), '"a=1"')


class TestDevShortName(unittest.TestCase):
    def test_short_input_returned_unchanged(self):
        self.assertEqual(dool.dev_short_name('sda1'), 'sda1')
        self.assertEqual(dool.dev_short_name('dm-5'), 'dm-5')

    def test_docstring_examples(self):
        cases = {
            'sda1': 'sda1',
            'hda14': 'hd14',
            'vda99': 'vd99',
            'hdb': 'hdb',
            'nvme0n1': 'nv01',
            'nvme1n1': 'nv11',
            'md123': 'm123',
            'md124': 'm124',
            'mmcblk7p50': 'm750',
            'VxVM4': 'VxV4',
            'dm-5': 'dm-5',
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(dool.dev_short_name(name), expected)

    def test_no_match_returned_unchanged(self):
        # No letters at the start, so the regexp does not match
        self.assertEqual(dool.dev_short_name('--------'), '--------')

    def test_custom_length(self):
        self.assertEqual(dool.dev_short_name('nvme0n1', 6), 'nvme01')


class TestTextWrap(unittest.TestCase):
    def test_fits_on_one_line(self):
        self.assertEqual(dool.text_wrap('a,b,c', ',', 80), ['a,b,c'])

    def test_wraps_at_width(self):
        self.assertEqual(dool.text_wrap('a,b,c', ',', 4), ['a,b', 'c'])

    def test_no_trailing_delimiter_on_lines(self):
        for line in dool.text_wrap('one,two,three,four', ',', 8):
            with self.subTest(line=line):
                self.assertFalse(line.endswith(','))


class TestTruncatePad(unittest.TestCase):
    def test_exact_length_unchanged(self):
        self.assertEqual(dool.truncate_pad('abc', 3), 'abc')

    def test_shorter_is_padded_right(self):
        self.assertEqual(dool.truncate_pad('ab', 4), 'ab  ')

    def test_longer_is_truncated(self):
        self.assertEqual(dool.truncate_pad('abcdef', 3), 'abc')

    def test_empty_input_padded(self):
        self.assertEqual(dool.truncate_pad('', 3), '   ')


class TestExtractBetweenParens(unittest.TestCase):
    def test_extracts_contents(self):
        self.assertEqual(dool.extract_between_parens('f(a)b'), 'a')

    def test_first_pair_wins(self):
        self.assertEqual(dool.extract_between_parens('a(b)c(d)'), 'b')

    def test_no_open_delimiter(self):
        self.assertEqual(dool.extract_between_parens('abc'), '')

    def test_no_close_delimiter(self):
        self.assertEqual(dool.extract_between_parens('a(b'), '')

    def test_custom_delimiters(self):
        self.assertEqual(dool.extract_between_parens('[x]', '[', ']'), 'x')


class TestListItemDefault(unittest.TestCase):
    def test_in_range(self):
        self.assertEqual(dool.list_item_default(['a', 'b'], 1, 'd'), 'b')

    def test_out_of_range_returns_default(self):
        self.assertEqual(dool.list_item_default(['a', 'b'], 2, 'd'), 'd')

    def test_not_a_list_returns_default(self):
        self.assertEqual(dool.list_item_default('ab', 0, 'd'), 'd')
        self.assertEqual(dool.list_item_default(None, 0, 'd'), 'd')

    def test_empty_list_returns_default(self):
        self.assertEqual(dool.list_item_default([], 0, 'd'), 'd')


class TestPluginObjName(unittest.TestCase):
    def test_string_name(self):
        self.assertEqual(dool.plugin_obj_name(SimpleNamespace(name='cpu')), 'cpu')

    def test_list_name_uses_first_entry(self):
        obj = SimpleNamespace(name=['cpu', 'cpu_use'])
        self.assertEqual(dool.plugin_obj_name(obj), 'cpu')


class TestArrayDiff(unittest.TestCase):
    def test_removes_second_items(self):
        self.assertEqual(dool.array_diff([1, 2, 3], [2]), [1, 3])

    def test_keeps_duplicates_and_order(self):
        self.assertEqual(dool.array_diff([3, 1, 3, 2], [2]), [3, 1, 3])

    def test_empty_second(self):
        self.assertEqual(dool.array_diff([1, 2], []), [1, 2])

    def test_empty_first(self):
        self.assertEqual(dool.array_diff([], [1]), [])


class TestRemoveArrayItems(unittest.TestCase):
    def test_removes_matching_items(self):
        self.assertEqual(dool.remove_array_items([1, 2, 3], [2]), [1, 3])

    def test_removes_all_duplicates(self):
        self.assertEqual(dool.remove_array_items([1, 2, 1, 3], [1]), [2, 3])

    def test_preserves_order(self):
        self.assertEqual(dool.remove_array_items(['c', 'a', 'b'], ['a']), ['c', 'b'])

    def test_empty_removal_list(self):
        self.assertEqual(dool.remove_array_items([1, 2], []), [1, 2])

    def test_does_not_modify_source(self):
        source = [1, 2, 3]
        dool.remove_array_items(source, [2])
        self.assertEqual(source, [1, 2, 3])


class TestFirstExistingFile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.a = os.path.join(self.tmp.name, 'a')
        self.b = os.path.join(self.tmp.name, 'b')
        with open(self.b, 'w'):
            pass

    def tearDown(self):
        self.tmp.cleanup()

    def test_returns_first_that_exists(self):
        self.assertEqual(dool.first_existing_file([self.a, self.b]), self.b)

    def test_first_hit_wins_when_several_exist(self):
        with open(self.a, 'w'):
            pass
        self.assertEqual(dool.first_existing_file([self.a, self.b]), self.a)

    def test_none_exist_returns_none(self):
        self.assertIsNone(dool.first_existing_file([self.a]))

    def test_empty_list_returns_none(self):
        self.assertIsNone(dool.first_existing_file([]))


if __name__ == '__main__':
    unittest.main()
