### Author: Dag Wieers <dag@wieers.com>

class dool_plugin(dool):
    """
    Top most expensive I/O process

    Displays the name of the most expensive I/O process
    """
    def __init__(self):
        self.name = 'top-io'
        self.vars = ('name        read write',)
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

        # These are the only fields from /proc/ we care about for this plug-in
        empty_counters   = {'rchar:': 0, 'wchar:': 0}
        mandatory_fields = empty_counters.keys()

        for pid in proc_pidlist():
            newdata   = {}
            proc_file = f'/proc/{pid}/io'

            # Extract counters
            for parts in proc_splitlines(proc_file):
                # Make sure we have key => val
                if len(parts) != 2: continue

                key   = parts[0]
                value = parts[1]

                if key not in mandatory_fields:
                    continue

                newdata[key] = int(value)

            # Output can be missing when reading process info for other users.
            if len(newdata) != len(mandatory_fields):
                continue

            # Extract PID name
            name = get_name_by_pid(pid)

            # New process? Pretend the counters started at zero.
            if pid not in self.pidset1:
                self.pidset1[pid] = empty_counters

            # Store the data we captured for this loop
            self.pidset2[pid] = newdata

            if (op.bits):
                factor = 8
            else:
                factor = 1

            # INFO: https://www.kernel.org/doc/html/latest/filesystems/proc.html#proc-pid-io-display-the-io-accounting-fields
            #
            # 'rchar' counts bytes read from the task POV, e.g. open files which may be read from page cache, reading from a socket or pipe
            read_usage  = (self.pidset2[pid]['rchar:'] - self.pidset1[pid]['rchar:']) * factor / elapsed
            write_usage = (self.pidset2[pid]['wchar:'] - self.pidset1[pid]['wchar:']) * factor / elapsed
            usage       = read_usage + write_usage

            # Get the process that spends the most jiffies
            if usage > self.val['usage']:
                self.val['usage']       = usage
                self.val['read_usage']  = read_usage
                self.val['write_usage'] = write_usage
                self.val['pid']         = pid
                self.val['name']        = get_name_by_pid(pid)

        if step == op.delay:
            self.pidset1 = self.pidset2

        if self.val['usage'] != 0.0:
            # Test long/short names for alignment
            # self.val['name'] = '01234567890123456789BBBBBBBBB'
            # self.val['name'] = 'foo'

            name       = self.val['name']
            name_fmt   = f"{name[:10]:<10}" # First truncate, then pad if needed
            column_fmt = '%s %s %s'

            # Debug print the format so we can see the columns
            # column_fmt = column_fmt.replace(" ", "|");

            self.output = column_fmt % (name_fmt, cprint(self.val['read_usage'], 'd', 5, 1024), cprint(self.val['write_usage'], 'd', 5, 1024))

    def showcsv(self):
        return '%s / %d:%d' % (self.val['name'], self.val['read_usage'], self.val['write_usage'])

# vim:ts=4:sw=4:et
