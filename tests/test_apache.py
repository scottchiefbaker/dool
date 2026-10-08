"""Tests for the apache plugin: count status code groups per one-second window.

The plugin file is exec'd into its own namespace so the dool_plugin class can be
used without the plugin loader. Each sample is given a fixed 'now' so the
window boundaries are deterministic.
"""
import os
import re
import tempfile
import time
import unittest

from load_dool import dool

PLUGIN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '..', 'plugins', 'dool_apache.py')


def load_apache_plugin():
    namespace = {
        'dool': dool.dool,
        'os': os,
        're': re,
        'time': time,
        'first_existing_file': dool.first_existing_file,
        'step': 1,
    }
    with open(PLUGIN_PATH) as f:
        exec(compile(f.read(), PLUGIN_PATH, 'exec'), namespace)
    return namespace['dool_plugin'], namespace


APACHE_CLASS, APACHE_NS = load_apache_plugin()


def log_line(epoch, status):
    stamp = time.strftime('%d/%b/%Y:%H:%M:%S +0000', time.gmtime(epoch))
    return ('127.0.0.1 - - [%s] "GET / HTTP/1.1" %d 123 "-" "agent"\n'
            % (stamp, status))


class ApacheWindowTest(unittest.TestCase):
    NOW = 1786000000

    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix='.log')
        os.close(fd)
        self.plugin = APACHE_CLASS.__new__(APACHE_CLASS)

    def tearDown(self):
        os.remove(self.path)

    def write_log(self, lines):
        with open(self.path, 'w') as f:
            f.writelines(lines)

    def sample(self, now):
        return self.plugin.get_http_stats_for_last_x_seconds(self.path, 1, now=now)

    def test_line_in_current_second_is_counted_once(self):
        self.write_log([log_line(self.NOW, 200)])
        self.assertEqual(self.sample(self.NOW), {'2xx': 1})

    def test_previous_second_line_is_excluded(self):
        self.write_log([log_line(self.NOW - 1, 200)])
        self.assertEqual(self.sample(self.NOW), {})

    def test_older_and_future_lines_are_excluded(self):
        self.write_log([
            log_line(self.NOW - 2, 500),
            log_line(self.NOW + 1, 404),
        ])
        self.assertEqual(self.sample(self.NOW), {})

    def test_consecutive_samples_do_not_overlap(self):
        # One request in each second. Each sample should see exactly its own.
        self.write_log([
            log_line(self.NOW - 1, 200),
            log_line(self.NOW, 404),
            log_line(self.NOW + 1, 500),
        ])
        self.assertEqual(self.sample(self.NOW), {'4xx': 1})
        self.assertEqual(self.sample(self.NOW + 1), {'5xx': 1})

    def test_status_codes_are_grouped(self):
        self.write_log([
            log_line(self.NOW, 200),
            log_line(self.NOW, 204),
            log_line(self.NOW, 301),
            log_line(self.NOW, 404),
            log_line(self.NOW, 503),
        ])
        self.assertEqual(self.sample(self.NOW),
                         {'2xx': 2, '3xx': 1, '4xx': 1, '5xx': 1})

    def test_log_smaller_than_window_is_read_from_start(self):
        # Files shorter than the 5 KB seek offset used to raise on seek().
        self.write_log([log_line(self.NOW, 200)])
        self.assertLess(os.path.getsize(self.path), 1024 * 5)
        self.assertEqual(self.sample(self.NOW), {'2xx': 1})


if __name__ == '__main__':
    unittest.main()
