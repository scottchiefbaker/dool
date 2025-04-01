### Author: Dag Wieers <dag@wieers.com>

class dool_plugin(dool):
    """
    Top most expensive block I/O process.

    Displays the name of the most expensive block I/O process.
    """
    def __init__(self):
        self.name = 'top block-io'
        self.vars = ('name         read write',)
        self.type = 's'
        self.width = 23
        self.scale = 0
        self.pidset1 = {}

    def check(self):
        if not os.access('/proc/self/io', os.R_OK):
            raise Exception('Kernel has no per-process I/O accounting [CONFIG_TASK_IO_ACCOUNTING], use at least 2.6.20')

    def extract(self):
        self.output = ''
        self.pidset2 = {}
        self.val['usage'] = 0.0
        for pid in proc_pidlist():
            try:
                ### Reset values
                if pid not in self.pidset2:
                    self.pidset2[pid] = {'read_bytes:': 0, 'write_bytes:': 0}
                if pid not in self.pidset1:
                    self.pidset1[pid] = {'read_bytes:': 0, 'write_bytes:': 0}

                ### Extract name
                mystr  = proc_readline('/proc/%s/stat' % pid)
                name   = extract_between_parens(mystr)

                ### Extract counters
                for l in proc_splitlines('/proc/%s/io' % pid):
                    if len(l) != 2: continue
                    self.pidset2[pid][l[0]] = int(l[1])
            except IOError:
                continue
            except IndexError:
                continue

            # INFO: https://www.kernel.org/doc/html/latest/filesystems/proc.html#proc-pid-io-display-the-io-accounting-fields
            #
            ### 'read_bytes' counts bytes read from the storage layer, i.e. when the block device driver is used
            read_usage  = (self.pidset2[pid]['read_bytes:']  - self.pidset1[pid]['read_bytes:'])  * 1.0 / elapsed
            write_usage = (self.pidset2[pid]['write_bytes:'] - self.pidset1[pid]['write_bytes:']) * 1.0 / elapsed
            usage       = read_usage + write_usage

            ### Get the process that spends the most jiffies
            if usage > self.val['usage']:
                self.val['usage'] = usage
                self.val['read_usage'] = read_usage
                self.val['write_usage'] = write_usage
                self.val['pid'] = pid
                self.val['name'] = getnamebypid(pid, name)
#                st = os.stat("/proc/%s" % pid)

        if step == op.delay:
            self.pidset1 = self.pidset2

        if self.val['usage'] != 0.0:
            # Test long/short names for alignment
            # self.val['name'] = '01234567890123456789BBBBBBBBB'
            # self.val['name'] = 'foo'

            # devel_log("PID/NAME: %s => '%s'"  % (self.val['pid'], self.val['name']))

            name     = self.val['name']
            name_fmt = f"{name[:11]:<11}"  # First truncate, then pad if needed

            self.output = '%-11s %s %s' % (name_fmt, cprint(self.val['read_usage'], 'd', 5, 1024), cprint(self.val['write_usage'], 'd', 5, 1024))

        ### Debug (show PID)
#        self.output = '%*s %-*s%s %s' % (5, self.val['pid'], self.width-17, self.val['name'][0:self.width-17], cprint(self.val['read_usage'], 'd', 5, 1024), cprint(self.val['write_usage'], 'd', 5, 1024))

    def showcsv(self):
        return '%s / %d:%d' % (self.val['name'], self.val['read_usage'], self.val['write_usage'])

# vim:ts=4:sw=4:et
