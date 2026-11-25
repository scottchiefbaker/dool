"""Exercise the thermal plugin with deterministic sysfs directory entries."""
import io
import os
import re
import unittest
from types import SimpleNamespace

from load_dool import dool


THERMAL_DIR = '/sys/devices/virtual/thermal/'
PLUGIN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '..', 'plugins', 'dool_thermal.py')


def load_plugin(entries, selection=None, readings=None):
    if readings is None:
        readings = {}

    def read_temp(path):
        return io.StringIO(str(readings[path]))

    namespace = {
        'dool': dool.dool,
        'os': SimpleNamespace(
            path=SimpleNamespace(exists=lambda path: path == THERMAL_DIR),
            listdir=lambda path: entries,
            getenv=lambda name: selection if name == 'DOOL_THERMAL_ZONES' else None,
        ),
        're': re,
        'dopen': read_temp,
    }
    with open(PLUGIN_PATH) as source:
        exec(compile(source.read(), PLUGIN_PATH, 'exec'), namespace)
    return namespace['dool_plugin']()


class ThermalTest(unittest.TestCase):
    entries = ['thermal_zone10', 'cooling_device0', 'thermal_zone2',
               'thermal_zone0']

    def test_default_order_keeps_all_zones(self):
        plugin = load_plugin(self.entries)
        self.assertEqual(plugin.nick, ['tz0', 'tz2', 'tz10'])
        self.assertEqual(plugin.width, 4)
        self.assertEqual(plugin.vars, ['thermal_zone0', 'thermal_zone2', 'thermal_zone10'])

    def test_selection_keeps_headers_and_readings_aligned(self):
        plugin = load_plugin(self.entries, '10,2,2', {
            THERMAL_DIR + 'thermal_zone2/temp': 41000,
            THERMAL_DIR + 'thermal_zone10/temp': 47000,
        })
        plugin.val = {}
        plugin.extract()
        self.assertEqual(plugin.nick, ['tz2', 'tz10'])
        self.assertEqual(plugin.vars, ['thermal_zone2', 'thermal_zone10'])
        self.assertEqual(plugin.val, {'thermal_zone2': 41000, 'thermal_zone10': 47000})

    def test_unknown_zone_is_reported(self):
        with self.assertRaisesRegex(Exception, 'unknown thermal zone: 99'):
            load_plugin(self.entries, '2,99')

    def test_invalid_selection_is_reported(self):
        with self.assertRaisesRegex(Exception, 'comma-separated thermal zone IDs'):
            load_plugin(self.entries, '2,')
