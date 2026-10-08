"""Tests for process-name lookup from /proc/<pid>/{cmdline,comm,stat}.

All /proc reads go through linecache.getline, so a fake getline that serves
per-path contents is enough. Missing paths return '' like the real call does.
"""
import unittest
from unittest import mock

from load_dool import dool


def fake_proc(files):
    """Return a getline replacement serving the given {path: text} mapping."""
    def getline(filename, lineno=0, module_globals=None):
        return files.get(filename, '')
    return getline


class ProcCase(unittest.TestCase):
    PID = '1234'

    def use_proc(self, **files):
        """files maps 'cmdline'/'comm'/'stat' to file text for PID."""
        table = {'/proc/%s/%s' % (self.PID, k): v for k, v in files.items()}
        p = mock.patch.object(dool.linecache, 'getline', fake_proc(table))
        p.start()
        self.addCleanup(p.stop)


class TestCmdlineName(ProcCase):
    def test_first_argument_basename(self):
        self.use_proc(cmdline='/usr/sbin/sshd\0-D\0')
        self.assertEqual(dool.get_name_by_proc_cmdline(self.PID), 'sshd')

    def test_relative_path_basename(self):
        self.use_proc(cmdline='./myapp\0')
        self.assertEqual(dool.get_name_by_proc_cmdline(self.PID), 'myapp')

    def test_bare_name_is_kept(self):
        self.use_proc(cmdline='nginx\0')
        self.assertEqual(dool.get_name_by_proc_cmdline(self.PID), 'nginx')

    def test_missing_cmdline_is_empty(self):
        self.use_proc()
        self.assertEqual(dool.get_name_by_proc_cmdline(self.PID), '')


class TestCommName(ProcCase):
    def test_comm_is_stripped(self):
        self.use_proc(comm='kworker/0:1\n')
        self.assertEqual(dool.get_name_by_proc_comm(self.PID), 'kworker/0:1')

    def test_missing_comm_is_empty(self):
        self.use_proc()
        self.assertEqual(dool.get_name_by_proc_comm(self.PID), '')


class TestGetNameByPid(ProcCase):
    def test_cmdline_wins_over_comm(self):
        self.use_proc(cmdline='/usr/bin/redis-server\0', comm='redis-server\n')
        self.assertEqual(dool.get_name_by_pid(self.PID), 'redis-server')

    def test_falls_back_to_comm_when_cmdline_empty(self):
        self.use_proc(comm='kthreadd\n')
        self.assertEqual(dool.get_name_by_pid(self.PID), 'kthreadd')

    def test_debug_prefixes_method_used(self):
        self.use_proc(comm='kthreadd\n')
        self.assertEqual(dool.get_name_by_pid(self.PID, debug=1), 'comm:kthreadd')

    def test_debug_reports_cmdline_method(self):
        self.use_proc(cmdline='/usr/bin/ls\0', comm='ls\n')
        self.assertEqual(dool.get_name_by_pid(self.PID, debug=1), 'cmdline:ls')

    def test_scripting_language_uses_script_name(self):
        self.use_proc(cmdline='python\0/opt/tools/dool_check.py\0', comm='python\n')
        self.assertEqual(dool.get_name_by_pid(self.PID), 'dool_check.py')

    def test_bash_uses_script_name(self):
        self.use_proc(cmdline='bash\0/usr/local/bin/backup.sh\0')
        self.assertEqual(dool.get_name_by_pid(self.PID), 'backup.sh')

    def test_kvm_guest_name_is_extracted(self):
        self.use_proc(
            cmdline='/usr/libexec/qemu-kvm\0-name guest=web01.example,debug-threads=on\0')
        self.assertEqual(dool.get_name_by_pid(self.PID), 'web01.example')

    def test_proxmox_style_kvm_name_is_extracted(self):
        self.use_proc(
            cmdline='/usr/bin/kvm\0-id 210\0-name TestDHCPServer,debug-threads=on\0')
        self.assertEqual(dool.get_name_by_pid(self.PID), 'TestDHCPServer')


class TestStatName(ProcCase):
    # Kernel-thread style stat line: the name is the text inside parentheses.
    STAT = '1234 (bash) S 1 1234 1234 0 -1 4194560\n'

    def test_stat_name_is_returned(self):
        self.use_proc(stat=self.STAT)
        self.assertEqual(dool.get_name_by_proc_stat(self.PID), 'bash')

    def test_name_containing_close_paren_is_kept_whole(self):
        # The kernel does not escape ')' in comm, so the name runs to the last ')'.
        self.use_proc(stat='1234 (foo) bar) S 1 1234 1234 0 -1 4194560\n')
        self.assertEqual(dool.get_name_by_proc_stat(self.PID), 'foo) bar')

    def test_missing_stat_is_empty(self):
        self.use_proc()
        self.assertEqual(dool.get_name_by_proc_stat(self.PID), '')


if __name__ == '__main__':
    unittest.main()
