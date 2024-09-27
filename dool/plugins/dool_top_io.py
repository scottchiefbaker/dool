### Author: Dag Wieers <dag@wieers.com>

class dool_plugin(dool):
    """
    Top most expensive I/O process

    Displays the name of the most expensive I/O process
    """
    def __init__(self):
        self.name = 'top-io'
        self.vars = ('    name    read  writ',)
        self.type = 's'
        self.width = 22
        self.scale = 0
        self.pidset1 = {}

    def check(self):
        if not os.access('/proc/self/io', os.R_OK):
            raise Exception('Kernel has no per-process I/O accounting [CONFIG_TASK_IO_ACCOUNTING], use at least 2.6.20')

    def extract(self):
        self.output       = ''
        self.pidset2      = {}
        self.val['usage'] = 0.0
        for pid in proc_pidlist():
            try:
                ### Reset values
                if pid not in self.pidset2:
                    self.pidset2[pid] = {'read_bytes:': 0, 'write_bytes:': 0}
                if pid not in self.pidset1:
                    self.pidset1[pid] = {'read_bytes:': 0, 'write_bytes:': 0}

                ### Extract name
                name = proc_splitline('/proc/%s/stat' % pid)[1][1:-1]

                ### Extract counters
                for l in proc_splitlines('/proc/%s/io' % pid):
                    if len(l) != 2: continue
                    self.pidset2[pid][l[0]] = int(l[1])
            except IOError:
                continue
            except IndexError:
                continue

            if (op.bits):
                factor = 8
            else:
                factor = 1

            read_usage  = (self.pidset2[pid]['read_bytes:']  - self.pidset1[pid]['read_bytes:'])  * factor / elapsed
            write_usage = (self.pidset2[pid]['write_bytes:'] - self.pidset1[pid]['write_bytes:']) * factor / elapsed
            usage       = read_usage + write_usage

            ### Get the process that spends the most jiffies
            if usage > self.val['usage']:
                self.val['usage']       = usage
                self.val['read_usage']  = read_usage
                self.val['write_usage'] = write_usage
                self.val['pid']         = pid
                self.val['name']        = getnamebypid(pid, name)

        if step == op.delay:
            self.pidset1 = self.pidset2

        if self.val['usage'] != 0.0:
            self.output = '%-*s%s %s' % (self.width-11, self.val['name'][0:self.width-11], cprint(self.val['read_usage'], 'd', 5, 1024), cprint(self.val['write_usage'], 'd', 5, 1024))

        ### Debug (show PID)
#        self.output = '%*s %-*s%s %s' % (5, self.val['pid'], self.width-17, self.val['name'][0:self.width-17], cprint(self.val['read_usage'], 'd', 5, 1024), cprint(self.val['write_usage'], 'd', 5, 1024))

    def showcsv(self):
        return '%s / %d:%d' % (self.val['name'], self.val['read_usage'], self.val['write_usage'])

# vim:ts=4:sw=4:et
