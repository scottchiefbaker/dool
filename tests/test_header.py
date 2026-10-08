"""Tests for the title/subtitle header and CSV header output.

header() and csv_header() only call title()/subtitle()/csvtitle()/csvsubtitle()
on each column, so stub columns with fixed strings are enough to check layout.
"""
import unittest
from unittest import mock

from load_dool import dool


class StubColumn:
    def __init__(self, title, subtitle, csvtitle, csvsubtitle):
        self._title = title
        self._subtitle = subtitle
        self._csvtitle = csvtitle
        self._csvsubtitle = csvsubtitle

    def title(self):
        return self._title

    def subtitle(self):
        return self._subtitle

    def csvtitle(self):
        return self._csvtitle

    def csvsubtitle(self):
        return self._csvsubtitle


def col(name):
    """A column whose title is NAME and subtitle is 'n<NAME>'."""
    return StubColumn(name, 'n' + name, '"' + name + '"', '"n' + name + '"')


STUB_THEME = {'frame': '<f>', 'title': '<t>', 'default': '', 'subtitle': '<s>'}


class HeaderCase(unittest.TestCase):
    def setUp(self):
        patches = [
            mock.patch.object(dool, 'theme', STUB_THEME, create=True),
            mock.patch.object(dool, 'update', 0, create=True),
            mock.patch.dict(dool.char, {'title_sep': '+', 'title_sep_first': 'T'}),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def set_update(self, value):
        p = mock.patch.object(dool, 'update', value, create=True)
        p.start()
        self.addCleanup(p.stop)


class TestHeaderLayout(HeaderCase):
    def test_single_column_has_no_separator(self):
        cols = [col('A')]
        self.assertEqual(dool.header(cols, cols), 'A\nnA\n')

    def test_columns_are_joined_by_first_separator(self):
        cols = [col('A'), col('B')]
        # update == 0 selects title_sep_first ('T') for the title row
        # and the plain pipe for the subtitle row.
        self.assertEqual(dool.header(cols, cols),
                         'A<f>T' 'B\nnA<f>|nB\n')

    def test_later_headers_use_title_sep(self):
        self.set_update(1)
        cols = [col('A'), col('B')]
        self.assertEqual(dool.header(cols, cols),
                         'A<f>+B\nnA<f>|nB\n')

    def test_totlist_longer_than_vislist_adds_gt_marker(self):
        totlist = [col('A'), col('B'), col('C')]
        vislist = [col('A'), col('B')]
        self.assertEqual(dool.header(totlist, vislist),
                         'A<f>TB<t>>\nnA<f>|nB<t>>\n')

    def test_all_visible_has_no_gt_marker(self):
        cols = [col('A'), col('B')]
        # The '>' marker is emitted with the title theme color in front of it.
        self.assertNotIn('<t>>', dool.header(cols, cols))


class TestCsvHeader(unittest.TestCase):
    def test_single_column(self):
        self.assertEqual(dool.csv_header([col('A')]), '"A"\n"nA"\n')

    def test_columns_joined_with_csv_separator(self):
        cols = [col('A'), col('B')]
        self.assertEqual(dool.csv_header(cols),
                         '"A","B"\n"nA","nB"\n')

    def test_separator_follows_char_sep(self):
        cols = [col('A'), col('B')]
        with mock.patch.dict(dool.char, {'sep': ';'}):
            self.assertEqual(dool.csv_header(cols),
                             '"A";"B"\n"nA";"nB"\n')


if __name__ == '__main__':
    unittest.main()
