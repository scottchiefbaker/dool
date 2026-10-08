### Author: Scott Baker

################################################################################
# Note this parses the last 5k of your Apache's access log once every second.
# In my testing this does not add a lot of overhead, but the possibility is
# there. If your log files are more than ~5k per second (wow!) this plugin
# will probably not report data correctly.
#
# Usage:
#   dool --apache
# or
#   EXPORT DOOL_APACHE_LOG=/var/log/apache2/access.log ; dool --apache
################################################################################

class dool_plugin(dool):
	'''
	Count the Apache HTTP status code groupings
	'''
	def __init__(self):
		self.name  = 'Apache'
		self.vars  = ( '2xx', '3xx', '4xx', '5xx' )
		self.type  = 'f'
		self.width = 4   # Each column is X chars wide
		self.scale = 100 # Change colors every 100x

		# Get the Apache stats for the last ONE second
		env_path    = os.environ.get('DOOL_APACHE_LOG','').strip()
		apache_logs = (
			"/var/log/httpd/access_log",   # Redhat
			"/var/log/apache2/access.log", # Debian
		)

		# Use the supplied ENV path, or whichever logfile from the list we find
		self.log_file = env_path or first_existing_file(apache_logs)

	def extract(self):
		x = self.get_http_stats_for_last_x_seconds(self.log_file, 1)

		# The first loop around resets the totals and sample count
		if (step == 1):
			self.totals  = {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0}
			self.samples = 0

		# Add this second's stats to the running totals
		self.samples += 1
		for code in ["2xx", "3xx", "4xx", "5xx"]:
			self.totals[code] += x.get(code, 0)
			# Output the average requests per second over all samples so far
			self.val[code] = self.totals[code] / float(self.samples)

	def check(self):
		try:
			is_readable = os.access(self.log_file, os.R_OK)

			if (not is_readable):
				raise(Exception("BEES?"))
		except:
			# If we end up with nothing in the variable we were unable to be
			# "smart" and have to error out
			if (self.log_file is None):
				raise Exception('APACHE: Log file not found in normal locations')
			else:
				raise Exception('APACHE: Log file "%s" is not readable' % (self.log_file))

	################################################################################
	################################################################################

	def get_http_stats_for_last_x_seconds(self, log_file, seconds = 1, now = None):
		with open(log_file, 'r') as file:
			if (now is None):
				now = int(time.time())
			file_size = os.path.getsize(log_file)

			# Seek to byte offset at the end of the file. For logs smaller than
			# the window, start at the beginning of the file instead.
			offset = file_size - 1024 * 5 * seconds
			if (offset > 0):
				file.seek(offset)

				# Throw away the partial line
				file.readline()

			# Time is between [ ]
			# HTTP status code is digits after "
			# Bytes transferred is after HTTP status
			pattern = r'\[(.+?)\].*" (\d+)\s+(\d+) "'
			stats   = {}
			count   = 0

			# Read lines from that position
			for line in file:
				# print(line)
				match = re.search(pattern, line)

				# If we match the regexp
				if (match):
					line_time = self.get_apache_unixtime(match.group(1))
					diff      = now - line_time

					# If this line is within the last X seconds. The lower bound
					# excludes lines stamped in the future; the upper bound
					# excludes lines from the previous window, which were already
					# counted in an earlier sample.
					if (0 <= diff < seconds):
						count += 1

						# Group the status codes by 2xx, 3xx, 4xx, 5xx
						status_code = int(match.group(2))
						status_str  = str(int(round(status_code, -2) / 100)) + "xx"

						# Increment the current number
						current           = stats.get(status_str, 0)
						stats[status_str] = current + 1

		return stats

	# Convert an Apache time string to unixtime: 17/Aug/2025:03:40:11 -0700
	def get_apache_unixtime(self, timestamp_str):
		from datetime import datetime
		import time

		dt = datetime.strptime(timestamp_str, "%d/%b/%Y:%H:%M:%S %z")

		return int(dt.timestamp())

# vim: tabstop=4 shiftwidth=4 noexpandtab autoindent softtabstop=4
