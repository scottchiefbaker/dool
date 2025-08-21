### Author: Scott Baker - 2025-08-20

class dool_plugin(dool):
	'''
	Skeleton plugin to serve as a starting point if you want
	write your own plugin
	'''

	def __init__(self):
		# Type of data each column in this plugin will display
		# f = float, s = string, b = bit/bytes, d = decimal, t = time, p = percent
		# Default: f
		self.type = 'd'

		# If the data is a number the color will cycle every 'scale' units
		# Default: 1024
		self.scale = 20

		# Width of each column in characters
		# Default: 5
		self.width = 4

		# Arbitrary data can be refernced in functions below
		# Note: This is not usually needed
		self.file_source = '/proc/net/'

	################################################################################
	# Make sure you can read the files you need, etc before starting the plugin
	#
	# REQUIRED
	################################################################################
	def check(self):
		try:
			list = os.listdir(self.file_source)
		except:
			raise Exception('Cannot read from %s' %s (self.file_source))

	################################################################################
	# Go out an discover what data is available and store it in the object
	# for use later. Whatever data is found can be later accessed via self.discover
	#
	# OPTIONAL (can be omitted completely)
	################################################################################
	def discover(self):
		list = os.listdir(self.file_source)

		return list

	################################################################################
	# An array of the column headers
	#
	# REQUIRED
	################################################################################
	def vars(self):
		return ('Rand', 'col2', 'Sum')

	################################################################################
	# A string for plugin heading
	#
	# REQUIRED
	################################################################################
	def name(self):
		return ("PluginName")

	################################################################################
	# If the raw column names are not correct we can remap the names here
	# to something more readable
	#
	# OPTIONAL (can be omitted completely)
	################################################################################
	def nick(self):
		if (self.vars[0] == "HDD"):
			new    = list(self.vars) # Tuple to list
			new[0] = 'SSD'

			return new

	################################################################################
	# Go out and get the actual data needed for the columns. Data must be returned
	# as a dictionary with the keys that were used in vars(). Data must be stored
	# in self.val and will be outputted automatically. Any keys in the dictionary
	# that are NOT in vars() will be silently ignored.
	#
	# REQUIRED
	################################################################################
	def extract(self):
		import random
		data = {
			'Rand': random.randint(1, 100),
			'col2': 22,
			'Sum' : 0,
		}

		data['Sum'] = data['Rand'] + data['col2']

		self.val = data;

	################################################################################
	# Notes: Some plugins access object variables directly and do not use the
	# functional interface to set names, variables etc. You *can* set some things
	# directly in __init__
	#
	# self.vars = ('one', 'two')
	# self.name = "MyPlugin"
	#
	# This does work, but is not recommened. The full functional interface is
	# the preferred and supported method to set plugin parameters
	#
	# Options can be accessed via the `op` dictionary. This can be useful if you
	# need access to --debug (op.debug) when testing
	################################################################################

# vim: tabstop=4 shiftwidth=4 noexpandtab autoindent softtabstop=4
