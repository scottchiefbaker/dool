### Author: Scott Baker - 2025-08-20
# Plugin skeleton. To try it, copy this file to ~/.dool/dool_<yourname>.py,
# change the name() and vars() values as you like, and run: dool --<yourname>
# (Use the same <yourname> as in the file name, without the dool_ prefix.)
#
# Rules:
#   - File name must be dool_<name>.py and must define "class dool_plugin".
#   - Plugins are searched in ~/.dool/ first, so a copy there overrides the
#     copy in the dool plugins/ directory.

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

		# Arbitrary data can be referenced in functions below.
		# This is an example attribute, not a required one.
		self.file_source = '/proc/net/'

	################################################################################
	# Make sure you can read the files you need, etc before starting the plugin.
	# Raise an Exception here if the plugin cannot run on this system. dool will
	# then skip the plugin and report the message.
	#
	# REQUIRED
	################################################################################
	def check(self):
		try:
			list = os.listdir(self.file_source)
		except:
			raise Exception('Cannot read from %s' % (self.file_source))

	################################################################################
	# Go out and discover what data is available and store it in the object
	# for use later. Whatever data is found can be later accessed via self.discover.
	# Return a truthy value when discovery succeeds. The base class default
	# returns True, so this hook can be omitted if nothing needs discovering.
	#
	# OPTIONAL (can be omitted completely)
	################################################################################
	def discover(self):
		list = os.listdir(self.file_source)

		return list

	################################################################################
	# A tuple of the column headers. extract() must return a key for each one.
	#
	# REQUIRED
	################################################################################
	def vars(self):
		return ('Rand', 'col2', 'Sum')

	################################################################################
	# A string for the plugin heading, shown above its columns.
	#
	# REQUIRED
	################################################################################
	def name(self):
		return ("PluginName")

	################################################################################
	# Optional short column labels, same length as vars(). If this returns None,
	# the names from vars() are used as-is.
	#
	# OPTIONAL (can be omitted completely)
	################################################################################
	def nick(self):
		return ('Rnd', 'col2', 'Sum')

	################################################################################
	# Get the actual data for the columns. Return it as a dictionary whose keys
	# match vars(). Store it in self.val and it will be output automatically.
	# Keys that are not in vars() are silently ignored.
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

		self.val = data

	################################################################################
	# Notes:
	#
	# - The functional interface above (vars(), name(), nick(), etc.) is the
	#   supported way to define a plugin. Some older plugins set attributes
	#   directly in __init__ instead, for example:
	#       self.vars = ('one', 'two')
	#       self.name = 'MyPlugin'
	#   This works but is not recommended.
	#
	# - Command-line options are available through the global "op" object:
	#       op.debug                 (set by --debug; useful when testing)
	################################################################################

# vim: tabstop=4 shiftwidth=4 noexpandtab autoindent softtabstop=4
