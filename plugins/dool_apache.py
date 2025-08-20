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
		self.type  = 's'
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

		# The first loop around sets everything to zero
		if (step == 1):
			for code in ["2xx", "3xx", "4xx", "5xx"]:
				self.val[code] = 0

		# Add the stats to what is already there
		for code in ["2xx", "3xx", "4xx", "5xx"]:
			self.val[code] += x.get(code, 0)

	def check(self):
		try:
			is_readable = os.access(self.log_file, os.R_OK)

			if (not is_readable):
				raise(Expection("BEES?"))
		except:
			# If we end up with nothing in the variable we were unable to be
			# "smart" and have to error out
			if (self.log_file is None):
				raise Exception('APACHE: Log file not found in normal locations')
			else:
				raise Exception('APACHE: Log file "%s" is not readable' % (self.log_file))

	################################################################################
	################################################################################

	def get_http_stats_for_last_x_seconds(self, log_file, seconds = 1):
		with open(log_file, 'r') as file:
			now       = int(time.time())
			file_size = os.path.getsize(log_file)

			# Seek to byte offset at the end of the file
			file.seek(file_size - 1024 * 5 * seconds)

			# Throw away the partial line
			file.readline()

			pattern = r'(\S+) (\S+) (\S+) \[([^\]]+)\] "([^"]+)" (\d+) (\S+) "([^"]*)" "([^"]*)"'
			stats   = {}
			count   = 0

			# Read lines from that position
			for line in file:
				# print(line)
				match = re.match(pattern, line)

				# If we match the regexp
				if (match):
					line_time = self.get_apache_unixtime(match.group(4))
					diff      = now - line_time

					# If this line is within the last X seconds
					if (diff <= seconds):
						count += 1

						# Group the status codes by 2xx, 3xx, 4xx, 5xx
						status_code = int(match.group(6))
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
