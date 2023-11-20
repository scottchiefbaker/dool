### Author: Scott Baker - <https://www.perturb.org/>

class dool_plugin(dool):
	"""
	Plugin to gather data about a specific PID
	"""

	def __init__(self):
		self.vars  = ('cpu  read  writ  mem',)
		self.type  = 's'
		self.width = 20
		self.scale = 0
		self.prev  = { 'read': -1, 'write': -1, 'cpu': 0, 'mem': 0}

		# Get the pid from the CLI options
		try:
			pid  = int(op.plugin_params['pid-detail'])
		except:
			msg = 'pid-detail: %s is not a number' % (op.plugin_params['pid-detail'])
			raise Exception(msg)

		path = '/proc/%s/stat' % pid
		if not os.path.exists(path):
			msg = 'pid-detail: %d is not an active pid' % (pid)
			raise Exception(msg)

		name = getnamebypid(pid, 'unknown')

		# Set the plugin title at the top of the column
		self.name = "pid info: %s" % name

		# Save the pid name and number for easier access later
		self.pid_name = name
		self.pid      = pid

	def extract(self):
		pid = self.pid

		# Make sure we have data for this pid
		path = '/proc/%s/stat' % pid
		if not os.path.exists(path):
			self.output = 'Pid #%s not found' % pid
			return

		(disk_rd, disk_wr) = self.get_pid_disk(pid)
		cpu_usage = self.get_pid_cpu(pid)
		mem_usage = self.get_pid_mem(pid)

		cpu_str   = cprint(cpu_usage, 'f', 3, 34)
		disk_rd   = cprint(disk_rd	, 'd', 5, 1024)
		disk_wr   = cprint(disk_wr	, 'd', 5, 1024)
		mem_usage = cprint(mem_usage, 'd', 4, 1024)

		self.output = "%s %s %s %s" % (cpu_str, disk_rd, disk_wr, mem_usage)

	# Sometimes /proc/12345/stat has a space in the proc name field
	# which messes up the split. This tries to be smart and work around that
	def get_proc_pid_stat(self, pid):
		path = '/proc/%s/stat' % pid
		if not os.path.exists(path):
			return []

		# Read the first line
		line = proc_readline(path)
		line = line.strip()

		# Find the proc name that's between the ( )
		x     = re.search("\((.*?)\)", line)
		paren = x.group(1)

		# Replace any spaces in the parens part with underscores
		cleaned  = paren.replace(" ", "_")
		new_line = line.replace(paren, cleaned, 1)

		# Return the split array
		parts = new_line.split(" ")

		return parts

	def get_pid_cpu(self, pid):
		path = '/proc/%s/stat' % pid
		if not os.path.exists(path):
			self.output = 'Pid #%s not found' % pid

		l = self.get_proc_pid_stat(pid)
		if len(l) < 35: return 0

		user_time   = int(l[13])
		kernel_time = int(l[14])

		current_cpu = user_time + kernel_time
		prev_cpu    = self.prev['cpu']
		usage       = (current_cpu - prev_cpu) * 1.0 / elapsed / cpunr

		if prev_cpu:
			ret = usage
		else:
			ret = 0

		# If we're at a real update (not interim) we save the data
		if step == op.delay:
			self.prev['cpu'] = current_cpu

		return ret

	def get_pid_disk(self, pid):
		path  = '/proc/%s/io' % pid
		count = 0
		for p in proc_splitlines(path):
			key = p[0]
			val = p[1]

			if key == "read_bytes:":
				cur_read = int(val)
			elif key == "write_bytes:":
				cur_write = int(val)

			count += 1

		# This is usually a permission error reading that part of /proc/
		if count == 0:
			return (0,0)

		if (op.bits):
			factor = 8
		else:
			factor = 1

		# We have previous data so we calculate the difference
		# between the two
		if self.prev['read'] > -1:
			rread	= (cur_read - self.prev['read'])   * factor / elapsed
			rwrite	= (cur_write - self.prev['write']) * factor / elapsed
		# First round we just gather data
		else:
			rread  = 0
			rwrite = 0

		# If we're at a real update (not interim) we save the data
		if step == op.delay:
			self.prev['read']  = cur_read
			self.prev['write'] = cur_write

		ret = (rread, rwrite)

		return ret

	def get_pid_mem(self, pid):
		l = proc_splitline('/proc/%s/statm' % pid)

		if len(l) < 2: return 0

		prev_usage = self.prev['mem']
		cur_usage  = (int(l[1]) * pagesize)

		# If we have previous numbers we return the average
		if prev_usage:
			usage = self.prev['mem'] / elapsed
		# First run just gets the current number
		else:
			usage = cur_usage

		self.prev['mem'] += cur_usage

		if step == op.delay:
			self.prev['mem'] = cur_usage

		# Uncomment this to always return the absolute (not average)
		#usage = cur_usage

		return usage

	def showcsv(self):
		xstr = "%s %s %s %s" % (1,2,3,4)

		return xstr

# vim: tabstop=4 shiftwidth=4 noexpandtab autoindent softtabstop=4
