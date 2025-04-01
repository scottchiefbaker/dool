### Dstat all I/O process plugin
### Displays all processes' I/O read/write stats and CPU usage
###
### Authority: Guillermo Cantu Luna

class dool_plugin(dool):
    def __init__(self):
        self.name = 'most expensive cpu process'
        self.vars = ('process                 pid cpu  read write',)
        self.type = 's'
        self.width = 43
        self.scale = 0
        self.pidset1 = {}

    def check(self):
        if not os.access('/proc/self/io', os.R_OK):
            raise Exception('Kernel has no per-process I/O accounting [CONFIG_TASK_IO_ACCOUNTING], use at least 2.6.20')
        return True

    def extract(self):
        self.output = ''
        self.pidset2 = {}
        self.val['cpu_usage'] = 0
        for pid in proc_pidlist():
            try:
                ### Reset values
                if pid not in self.pidset2:
                    self.pidset2[pid] = {'rchar:': 0, 'wchar:': 0, 'cputime:': 0, 'cpuper:': 0}
                if pid not in self.pidset1:
                    self.pidset1[pid] = {'rchar:': 0, 'wchar:': 0, 'cputime:': 0, 'cpuper:': 0}

                # Read the pid name
                mystr     = proc_readline('/proc/%s/stat' % pid)
                stat_name = extract_between_parens(mystr)
                name      = getnamebypid(pid, stat_name)

                ### Extract counters
                for l in proc_splitlines('/proc/%s/io' % pid):
                    if len(l) != 2: continue
                    self.pidset2[pid][l[0]] = int(l[1])

                ### Get CPU usage
                l = proc_splitline('/proc/%s/stat' % pid)
                if len(l) < 15:
                    cpu_usage = 0.0
                else:
                    self.pidset2[pid]['cputime:'] = int(l[13]) + int(l[14])
                    cpu_usage = (self.pidset2[pid]['cputime:'] - self.pidset1[pid]['cputime:']) * 1.0 / elapsed / cpunr

            except ValueError:
                continue
            except IOError:
                continue
            except IndexError:
                continue

            read_usage = (self.pidset2[pid]['rchar:'] - self.pidset1[pid]['rchar:']) * 1.0 / elapsed
            write_usage = (self.pidset2[pid]['wchar:'] - self.pidset1[pid]['wchar:']) * 1.0 / elapsed

            ### Get the process that spends the most jiffies
            if cpu_usage > self.val['cpu_usage']:
                self.val['read_usage'] = read_usage
                self.val['write_usage'] = write_usage
                self.val['pid'] = pid
                self.val['name'] = getnamebypid(pid, name)
                self.val['cpu_usage'] = cpu_usage

        if step == op.delay:
            self.pidset1 = self.pidset2

        if self.val['cpu_usage'] != 0.0:
            # Test long/short names for alignment
            # self.val['name'] = '01234567890123456789BBBBBBBBB'
            # self.val['name'] = 'foo'

            # devel_log("PID/NAME: %s => '%s'"  % (self.val['pid'], self.val['name']))

            name     = self.val['name']
            name_fmt = f"{name[:19]:<19}"  # First truncate, then pad if needed

            column_fmt = '%s %s%-7s %s%s %s %s'
            # Debug print the format so we can see the columns
            # column_fmt = column_fmt.replace(" ", "|");

            self.output = column_fmt % (name_fmt, color['darkblue'], self.val['pid'], cprint(self.val['cpu_usage'], 'f', 3, 34), color['darkgray'],cprint(self.val['read_usage'], 'd', 5, 1024), cprint(self.val['write_usage'], 'd', 5, 1024))


    def showcsv(self):
        return 'Top: %s\t%s\t%s\t%s' % (self.val['name'][0:self.width-20], self.val['cpu_usage'], self.val['read_usage'], self.val['write_usage'])
