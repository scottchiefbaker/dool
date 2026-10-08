"""Tests for counter plugins: parse /proc fixtures and compute per-interval deltas.

Each plugin reads its file through dool.open() and stores counters in
set1 (previous sample) and set2 (current sample). Values are computed from
the difference, and set1 is advanced only when step == op.delay.
"""
import unittest
from io import StringIO
from types import SimpleNamespace
from unittest import mock

from load_dool import dool


def make_plugin(cls, text):
    """Build a plugin without touching the real /proc files."""
    def fake_open(self, *names):
        self.file = list(names)
        self.fd = [StringIO(text)]

    with mock.patch.object(dool.dool, 'open', fake_open):
        return cls()


def set_text(plugin, text):
    """Replace the 'file' contents, simulating the next sample."""
    plugin.fd = [StringIO(text)]


def cpu_line(name, user, nice, system, idle, iowait, irq, softirq, steal):
    # name is '' for the aggregate "cpu " line, or a cpu number like '0'
    return 'cpu%s %d %d %d %d %d %d %d %d 0 0\n' % (
        name, user, nice, system, idle, iowait, irq, softirq, steal)


def disk_line(name, reads, writes):
    # major minor name, then 11 stat fields. The plugin reads l[3] and l[7].
    return '   8       0 %s %d 0 800 50 %d 0 400 30 0 60 80\n' % (name, reads, writes)


def idle_disk_line(name):
    # A device with no activity at all (every counter is zero)
    return '   7       0 %s 0 0 0 0 0 0 0 0 0 0 0\n' % name


class PluginCase(unittest.TestCase):
    """Patches the dool globals that plugin extract() methods read."""

    def setUp(self):
        self.op = SimpleNamespace(
            cpulist=None, disklist=[], diskset={}, full=False,
            delay=1, bits=False, color=False)
        self.set_global('op', self.op)
        self.set_global('step', self.op.delay)
        self.set_global('elapsed', 2)
        self.set_global('cpunr', 2)

    def set_global(self, name, value):
        p = mock.patch.object(dool, name, value, create=True)
        p.start()
        self.addCleanup(p.stop)


class TestCpuPlugin(PluginCase):
    # Two samples of the aggregate line. Per-state ticks for sample A:
    #   usr (user+nice+irq+softirq)=1000, sys=500, idl=8000, wai=500, stl=0
    STAT_A = (cpu_line('', 1000, 0, 500, 8000, 500, 0, 0, 0)
              + cpu_line('0', 500, 0, 250, 4000, 250, 0, 0, 0)
              + 'intr 12345 1 2 3\n')
    # Sample B adds usr +100, sys +50, idl +300, wai +50, stl +0 (total +500)
    STAT_B = (cpu_line('', 1100, 0, 550, 8300, 550, 0, 0, 0)
              + cpu_line('0', 600, 0, 300, 4100, 300, 0, 0, 0)
              + 'intr 12999 1 2 3\n')

    def make(self):
        plugin = make_plugin(dool.dool_cpu, self.STAT_A)
        plugin.prepare()
        return plugin

    def test_discover_lists_cpu_ids_and_ignores_other_lines(self):
        plugin = make_plugin(dool.dool_cpu, self.STAT_A)
        found = plugin.discover()
        self.assertIn('0', found)
        self.assertNotIn('intr', found)
        self.assertNotIn('12345', found)

    def test_default_vars_is_total(self):
        self.assertEqual(self.make().vars, ['total'])

    def test_cpulist_selects_listed_cpus_only(self):
        self.op.cpulist = ['0', '9']  # '9' does not exist and is dropped
        plugin = make_plugin(dool.dool_cpu, self.STAT_A)
        plugin.prepare()
        self.assertEqual(plugin.vars, ['0'])

    def test_percentages_come_from_delta_between_samples(self):
        plugin = self.make()
        set_text(plugin, self.STAT_A)
        plugin.extract()  # first sample: sets the baseline (step == delay)
        set_text(plugin, self.STAT_B)
        plugin.extract()  # delta A -> B, total delta = 500 ticks
        # usr 100/500, sys 50/500, idl 300/500, wai 50/500, stl 0/500
        self.assertEqual(list(plugin.val['total']), [20.0, 10.0, 60.0, 10.0, 0.0])

    def test_no_progress_gives_all_zero(self):
        plugin = self.make()
        set_text(plugin, self.STAT_A)
        plugin.extract()
        plugin.extract()  # same counters again: nothing elapsed
        self.assertEqual(list(plugin.val['total']), [0, 0, 0, 0, 0])

    def test_baseline_not_advanced_when_step_is_not_delay(self):
        self.set_global('step', self.op.delay + 1)
        plugin = self.make()
        set_text(plugin, self.STAT_A)
        plugin.extract()
        self.assertEqual(list(plugin.set1['total']), [0, 0, 0, 0, 0])


class TestIoPlugin(PluginCase):
    # sda reads=100 writes=20, sdb reads=50 writes=10. sda1 is a partition:
    # it is excluded from the total. loop0 is all zeros and is skipped.
    DISK_A = (disk_line('sda', 100, 20)
              + disk_line('sdb', 50, 10)
              + disk_line('sda1', 999, 999)
              + idle_disk_line('loop0'))
    # Totals: reads 150 -> 360 (+210), writes 30 -> 60 (+30). elapsed = 2.
    DISK_B = (disk_line('sda', 300, 50)
              + disk_line('sdb', 60, 10)
              + disk_line('sda1', 1000, 1000)
              + idle_disk_line('loop0'))

    def make(self):
        plugin = make_plugin(dool.dool_io, self.DISK_A)
        plugin.prepare()
        return plugin

    def test_discover_skips_all_zero_devices(self):
        plugin = make_plugin(dool.dool_io, self.DISK_A)
        found = plugin.discover()
        self.assertIn('sda', found)
        self.assertNotIn('loop0', found)

    def test_discover_raises_when_no_devices_have_activity(self):
        plugin = make_plugin(dool.dool_io, idle_disk_line('loop0'))
        with self.assertRaises(Exception):
            plugin.discover()

    def test_default_vars_is_total_and_name_is_io_total(self):
        plugin = self.make()
        self.assertEqual(plugin.vars, ['total'])
        self.assertEqual(plugin.name, ['io/total'])

    def test_total_excludes_partitions_and_sums_rates_over_elapsed(self):
        plugin = self.make()
        set_text(plugin, self.DISK_A)
        plugin.extract()
        set_text(plugin, self.DISK_B)
        plugin.extract()
        # (360 - 150) / 2 and (60 - 30) / 2
        self.assertEqual(list(plugin.val['total']), [105.0, 15.0])

    def test_single_disk_selected_with_disklist(self):
        self.op.disklist = ['sda']
        plugin = self.make()
        self.assertEqual(plugin.vars, ['sda'])
        set_text(plugin, self.DISK_A)
        plugin.extract()
        set_text(plugin, self.DISK_B)
        plugin.extract()
        # sda: reads 100 -> 300, writes 20 -> 50, over elapsed = 2
        self.assertEqual(list(plugin.val['sda']), [100.0, 15.0])


if __name__ == '__main__':
    unittest.main()
