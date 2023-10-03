### Author: Scott Baker <scott@perturb.org>

class dool_plugin(dool):
	"""
	The number of in-flight IO operations pending per disk
	"""

	def __init__(self):
		# Each column is X chars wide
		self.width = 4 # Defaults to 5 if not specified

		devices    = self.get_devs()
		short_devs = []
		for x in devices:
			short_name = self.dev_short_name(x, self.width)
			short_devs.append(short_name)

		# This is the plugin name that goes on top of the columns
		#self.name	= 'io/inflight'
		self.name  = short_devs
		# Title of each column (or group of colums)
		self.nick = ('ioif',)
		# These are the sub headings under the main column (each disk device)
		self.vars  = devices
		# It's a decimal number
		self.type  = 'd'
		# Group the colorings to chunks of 20
		self.scale = 20

	def get_devs(self):
		# If there was a disk filter specified on the CLI
		# example: dool --disk-infligh -D md123,sda
		if op.disklist:
			return op.disklist

		ret   = []
		globx = glob.glob('/sys/block/*')

		for path in globx:
			base = os.path.basename(path)
			ret.append(base)

		ret.sort()

		return ret

	def extract(self):
		for dev in self.vars:
			# Documentation for /sys/block/$DEV/stat
			# https://www.kernel.org/doc/Documentation/block/stat.txt
			path = ("/sys/block/%s/stat" % (dev))

			for l in proc_splitlines(path):
				value = int(l[8])

				# For testing we can toss random data in the buckets
				#value = random.randrange(1,100)

				self.val[dev] = (value,)

	# Make human readable device names that are shorter
	#
	# Example mappings:
	#	sda1       => sda1
	#	hda14      => hd14
	#	vda99      => vd99
	#	hdb        => hdb
	#	nvme0n1    => nv01
	#	nvme1n1    => nv11
	#	md123      => m123
	#	md124      => m124
	#	md125      => m125
	#	mmcblk7p50 => m750
	#	VxVM4      => VxV4
	#	dm-5       => dm-5
	def dev_short_name(self, xinput, xlen = 4):
		# Too short just return the input
		if len(xinput) <= xlen:
			ret = xinput
		# Break out the parts and build a new string
		else:
			# This gets all the a-z chars up to the first digit
			# Then it gets any sequential digits followed by a
			# non-digit separator, and any remaining digits
			x = re.match("([a-zA-Z]+).*?(\d+)(.*\D.*?(\d+))?", xinput)

			# If we match the regexp we build a shorter string
			if x:
				let  = x.group(1)
				num1 = x.group(2)
				num2 = x.group(4) or ""

				# Concate the two number parts together
				num_part = num1 + num2
				# Figure out how long they are and how many remaining
				# chars we have for the letter part
				remain = xlen - len(num_part)
				# Get the first chars of letter
				letter_part = let[0:remain]
				# Prepend the letter part to meet the correct length
				ret = letter_part + num_part
			# Doesn't match the regexp pattern, not sure what it is
			else:
				ret = xinput

		return ret

# vim: tabstop=4 shiftwidth=4 noexpandtab autoindent softtabstop=4
