### Dstat all I/O process plugin
### Displays all processes' I/O read/write stats and CPU usage
###
### Authority: Guillermo Cantu Luna

class dool_plugin(dool):
	def __init__(self):
		self.name    = 'most expensive i/o process'
		self.vars    = ('process               pid    read  writ  cpu ',)
		self.type    = 's'
		self.width   = 45
		self.scale   = 0
		self.pidset1 = {}

	def check(self):
		if not os.access('/proc/self/io', os.R_OK):
			raise Exception('Kernel has no per-process I/O accounting [CONFIG_TASK_IO_ACCOUNTING], use at least 2.6.20')
		return True

	def extract(self):
		self.output = ''
		self.pidset2 = {}
		self.val['usage'] = 0.0
		for pid in proc_pidlist():
			try:
				### Reset values
				if pid not in self.pidset2:
					self.pidset2[pid] = {'rchar:': 0, 'wchar:': 0, 'cputime:': 0, 'cpuper:': 0}
				if pid not in self.pidset1:
					self.pidset1[pid] = {'rchar:': 0, 'wchar:': 0, 'cputime:': 0, 'cpuper:': 0}

				### Extract name
				name = proc_splitline('/proc/%s/stat' % pid)[1][1:-1]

				### Extract counters
				for l in proc_splitlines('/proc/%s/io' % pid):
					if len(l) != 2: continue
					self.pidset2[pid][l[0]] = int(l[1])

				### Get CPU usage
				l = proc_splitline('/proc/%s/stat' % pid)
				if len(l) < 15:
					cpu_usage = 0
				else:
					self.pidset2[pid]['cputime:'] = int(l[13]) + int(l[14])
					cpu_usage = (self.pidset2[pid]['cputime:'] - self.pidset1[pid]['cputime:']) * 1.0 / elapsed / cpunr

			except ValueError:
				continue
			except IOError:
				continue
			except IndexError:
				continue

			read_usage  = (self.pidset2[pid]['rchar:'] - self.pidset1[pid]['rchar:']) * 1.0 / elapsed
			write_usage = (self.pidset2[pid]['wchar:'] - self.pidset1[pid]['wchar:']) * 1.0 / elapsed
			usage       = read_usage + write_usage

			### Get the process that spends the most jiffies
			if usage > self.val['usage']:
				self.val['usage']       = usage
				self.val['read_usage']  = read_usage
				self.val['write_usage'] = write_usage
				self.val['pid']         = pid
				self.val['name']        = getnamebypid(pid, name)
				self.val['cpu_usage']   = cpu_usage

		if step == op.delay:
			self.pidset1 = self.pidset2

		if self.val['usage'] != 0.0:
			#self.output = '%-*s%s%-5s%s%s%s%s%%' % (self.width-14-len(pid), self.val['name'][0:self.width-14-len(pid)], color['darkblue'], self.val['pid'], cprint(self.val['read_usage'], 'd', 5, 1024), cprint(self.val['write_usage'], 'd', 5, 1024), cprint(self.val['cpu_usage'], 'f', 3, 34), color['darkgray'])

			pid_str   = color['darkblue'] + ("%-6s" % self.val['pid']) + ansi['reset']
			read_str  = cprint(self.val['read_usage'] , 'd', 5, 1024)
			write_str = cprint(self.val['write_usage'], 'd', 5, 1024)
			cpu_str   = cprint(self.val['cpu_usage']  , 'f', 4, 34)

			self.output = '%-20s %s %s %s %s%%' % (self.val['name'], pid_str, read_str, write_str, cpu_str)

	def showcsv(self):
		return 'Top: %s\t%s\t%s\t%s' % (self.val['name'][0:self.width-20], self.val['read_usage'], self.val['write_usage'], self.val['cpu_usage'])

# vim: tabstop=4 shiftwidth=4 noexpandtab autoindent softtabstop=4
