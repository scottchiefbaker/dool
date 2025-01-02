#!/usr/bin/env python3

"""
Dool is a command line tool to monitor many aspects of your system: CPU,
Memory, Network, Load Average, etc.  It also includes a robust plug-in
architecture to allow monitoring other system metrics.
"""

### This program is free software; you can redistribute it and/or
### modify it under the terms of the GNU General Public License
### as published by the Free Software Foundation; either version 2
### of the License, or (at your option) any later version.
###
### This program is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.
###
### You should have received a copy of the GNU General Public License
### along with this program; if not, write to the Free Software
### Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

### Forked by Scott Baker in 2019
### Copyright 2004-2019 Dag Wieers <dag@wieers.com>

from __future__ import absolute_import, division, generators, print_function
__metaclass__ = type

import fnmatch
import getopt
import getpass
import glob
import linecache
import math
import os
import re
import resource
import sched
import sys
import time
import signal

from collections.abc import Sequence

__version__ = '1.3.4'

theme = { 'default': '' }

pluginpath = [
    os.path.expanduser('~/.dool/'),                           # home + /.dool/
    os.path.dirname(os.path.abspath(__file__)) + '/plugins/', # binary path + /plugins/
    '/usr/share/dool/',
    '/usr/local/share/dool/',
]

# Global variable to match drives in /proc/
# This is a regexp filter to EXCLUDE partitions, so we only add stats for the main parent drive
# i.e. use stats for sda not sda1/sda7/etc.
# NVME drives are: nvmeXnXpX
DOOL_DISKFILTER = re.compile(r'^([hsv]d[a-z]+\d+|cciss/c\d+d\d+p\d+|dm-\d+|md\d+|mmcblk\d+p\d0|VxVM\d+|nvme\d+n\d+p\d+)$')

class Options:
    def __init__(self, args):
        self.args          = args
        self.bits          = True
        self.blackonwhite  = False
        self.count         = -1
        self.cpulist       = None
        self.debug         = 0
        self.delay         = 1
        self.devel         = 0
        self.disklist      = []
        self.diskset       = {}
        self.full          = False
        self.float         = False
        self.integer       = False
        self.intlist       = None
        self.netlist       = None
        self.swaplist      = None
        self.color         = None
        self.update        = True
        self.header        = True
        self.output        = False
        self.pidfile       = False
        self.profile       = ''
        self.use_ascii     = False
        self.plugin_params = {} # Not currently used
        self.opt_params    = {} # CLI arguments that *optionally* have a param

        # See if any of the CLI arguments are "optional" and remove them
        # getopt() doesn't support optional params, so we remove them so getopt()
        # won't freak out. We store the optional params in self.opt_params
        args = self.optional_params(args)

        ### Get all the plugins and their details
        self.plugin_details = get_plugin_details()
        plugin_opt_list     = self.get_opt_list_from_details(self.plugin_details)

        ### List of plugins to show
        self.plugins = []

        ### Implicit if no terminal is used
        if not sys.stdout.isatty():
            self.color  = False
            self.header = False
            self.update = False

        long_opts = [
            'all'      , 'all-plugins', 'ascii'   , 'bits'   , 'bw'     , 'bytes'  , 'black-on-white', 'color'  ,
            'color16'  , 'defaults'   , 'debug'   , 'devel'  , 'display', 'dstat'  , 'filesystem'    , 'float'  ,
            'full'     , 'help'       , 'integer' , 'list'   , 'mods'   , 'modules', 'more'          , 'nocolor',
            'noheaders', 'noupdate'   , 'profile' , 'version', 'vmstat' ,
        ]

        param_opts = [
            'diskset=' , 'output='    , 'pidfile='
        ]

        all_opts = (long_opts + param_opts + plugin_opt_list)

        try:
            opts, args = getopt.getopt(args, 'acdfghilmno:prstTvyC:D:I:M:N:S:V', all_opts)
        except getopt.error as exc:
            print('dool: %s, try dool -h for a list of all the options' % exc)
            sys.exit(1)

        default_plugins = [ 'cpu', 'disk', 'net', 'load' ]

        plugin_defaults = 0

        # Loop through the opt array and find the keys
        opt_keys = []
        for x in opts:
            opt_keys.append(x[0])

        # We default to outputting to the display, but this may get toggled later by --output
        self.display = True

        for opt, arg in opts:
            if opt in ['-c']:
                self.plugins.append('cpu')
            elif opt in ['-C']:
                self.cpulist = arg.split(',')
            elif opt in ['-d']:
                self.plugins.append('disk')
            elif opt in ['-D']:
                self.disklist = arg.split(',')
            elif opt in ['--diskset']:
                parts   = arg.split(":", 1)
                name    = list_item_default(parts, 0, "Unknown")
                members = list_item_default(parts, 1, "").split(",")

                if (len(parts) < 2 or len(members) < 1):
                    print("Error parsing diskset...\n")
                    print("Format : diskset_name:dev1,dev2,dev3,etc...")
                    print("Example: --diskset os_drives:sda,sdb")

                # We convert /dev/sda and symlinks to their raw device name that is
                # found in /proc/diskstats
                cleaned = []
                for dev in members:
                    base = get_dev_name(dev)
                    if base:
                        cleaned.append(base)

                if len(cleaned) == 0:
                    print('dool: diskset %s has no valid members' % name)

                self.diskset[name] = cleaned
                self.disklist.append(name)
            elif opt in ['--dstat']:
                self.bits      = False
                self.use_ascii = True
                self.color     = 16

                # --dstat by itself so we load the old default plug-ins
                if len(opts) == 1:
                    self.plugins.append('cpu')
                    self.plugins.append('disk')
                    self.plugins.append('net')
                    self.plugins.append('page')
                    self.plugins.append('sys')
            elif opt in ['--filesystem']:
                self.plugins.append('fs')
            elif opt in ['-g']:
                self.plugins.append('page')
            elif opt in ['-i']:
                self.plugins.append('int')
            elif opt in ['-I']:
                self.intlist = arg.split(',')
            elif opt in ['-l']:
                self.plugins.append('load')
            elif opt in ['-m']:
                self.plugins.append('mem')
            elif opt in ['-M', '--mods', '--modules']:
                print('WARNING: Option %s is deprecated, please use --%s instead' % (opt, ' --'.join(arg.split(','))), file=sys.stderr)
                self.plugins += arg.split(',')
            elif opt in ['-n']:
                self.plugins.append('net')
            elif opt in ['-N']:
                self.netlist = arg.split(',')
            elif opt in ['-p']:
                self.plugins.append('proc')
            elif opt in ['-r']:
                self.plugins.append('io')
            elif opt in ['-s']:
                self.plugins.append('swap')
            elif opt in ['-S']:
                self.swaplist = arg.split(',')
            elif opt in ['-t']:
                self.plugins.append('time')
            elif opt in ['-T']:
                self.plugins.append('epoch')
            elif opt in ['-y']:
                self.plugins.append('sys')
            elif opt in ['--defaults']:
                self.plugins    = default_plugins
                plugin_defaults = 1
            elif opt in ['--more']:
                self.plugins += [ 'cpu', 'disk', 'net', 'mem', 'proc', 'load' ]
            elif opt in ['-a', '--all']:
                self.plugins += [ 'cpu', 'disk', 'net', 'page', 'mem', 'sys', 'proc', 'load' ]
            elif opt in ['-v', '--vmstat']:
                self.plugins += [ 'proc', 'mem', 'page', 'disk', 'sys', 'cpu' ]
            elif opt in ['-f', '--full']:
                self.full = True
            elif opt in ['--all-plugins']:
                self.plugins += plugin_opt_list
            elif opt in ['--bytes']:
                self.bits = False
            elif opt in ['--bits']:
                self.bits = True
            elif opt in ['--ascii']:
                self.use_ascii = True
            elif opt in ['--bw', '--black-on-white', '--blackonwhite']:
                self.blackonwhite = True
            elif opt in ['--color']:
                self.color = 256
                self.update = True
            elif opt in ['--color16']:
                self.color = 16
                self.update = True
            elif opt in ['--debug']:
                self.debug = self.debug + 1
            elif opt in ['--float']:
                self.float = True
            elif opt in ['--integer']:
                self.integer = True
            elif opt in ['--list']:
                show_plugins()
                sys.exit(0)
            elif opt in ['--nocolor']:
                self.color = False
            elif opt in ['--noheaders']:
                self.header = False
            elif opt in ['--noupdate']:
                self.update = False
            elif opt in ['-o', '--output']:
                self.output = arg
                self.display = False
            elif opt in ['--display']:
                self.display = True
            elif opt in ['--pidfile']:
                self.pidfile = arg
            elif opt in ['--profile']:
                self.profile = 'dool_profile.log'
            elif opt in ['--devel']:
                self.devel = 1
            elif opt in ['-h', '--help']:
                self.usage()
                self.help()
                sys.exit(0)
            elif opt in ['-V', '--version']:
                self.version()
                sys.exit(0)
            elif opt.startswith('--'):
                plugin_name = opt[2:]

                self.plugins.append(plugin_name)
                self.plugin_params[plugin_name] = arg # Not currently used
            else:
                print('dool: option %s unknown to getopt, try dool -h for a list of all the options' % opt)
                sys.exit(1)

        # If --display is before --output we have to reset it here
        if '--display' in opt_keys:
            self.display = True

        if self.float and self.integer:
            print('dool: option --float and --integer are mutual exclusive, you can only force one')
            sys.exit(1)

        # If no plugins are specified we use the defaults
        if not self.plugins:
            self.plugins    = default_plugins
            plugin_defaults = 1
            print("Using default plugins: " + ", ".join(self.plugins) + "")

        # Append the 'time' plugin to the end for 'more' and 'all'
        needs_time_added = ('time' not in self.plugins) and (("--more" in opt_keys) or ("--all" in opt_keys) or (plugin_defaults))

        if needs_time_added:
            self.plugins.append('time');

        try:
            if len(args) > 0: self.delay = int(args[0])
            if len(args) > 1: self.count = int(args[1])
        except:
            print('dool: incorrect argument, try dool -h for the correct syntax')
            sys.exit(1)

        if self.delay <= 0:
            print('dool: delay must be an integer, greater than zero')
            sys.exit(1)

        if self.debug:
            print('Plugins: %s' % self.plugins)

    # Loop through the args array and find any items that are optional. If we
    # find an optional one, check the NEXT item. If the next item does NOT
    # start with "--" it's a param for the current item.
    #
    # getopt() doesn't support optional params so we remove them here, and
    # the plugins themselves are able to read the params manually from the
    # op.opt_params dictionary
    def optional_params(self, args):
        optional_arguments = ["freespace"]
        to_remove          = []

        # Loop through each of the args
        for x in range(len(args)):
            item      = args[x]
            # Remove leading "--"
            item      = re.sub(r'^--', '', item)
            next_item = list_item_default(args, x + 1, "")

            # If the item is one of the ones we flagged as optional
            # check to see if it has optional params
            if item in optional_arguments:
                if not re.match(r"^--", next_item):
                    #print("Removing %s" % next_item)
                    to_remove.append(next_item)
                    self.opt_params[item] = next_item

        # If we found optional params we remove them from the array
        for x in to_remove:
            args.remove(x)

        return args

    def get_opt_list_from_details(self, plugin_details):
        plugin_names = list(plugin_details.keys())
        plugin_names.sort()

        builtin  = []
        external = []

        for name in plugin_names:
            path   = plugin_details[name]['file']   # Path to plugin file
            params = plugin_details[name]['params'] # Plugin needs CLI params
            ptype  = plugin_details[name]['type']   # builtin or exteral

            if params:
                param_str = "yes"

                # For getopt we need to add the '=' to the end to indicate
                # that we need a param
                if ptype == 'builtin':
                    builtin.append(name + "=")
                else:
                    external.append(name + "=")

            else:
                param_str = "no"

                if ptype == 'builtin':
                    builtin.append(name)
                else:
                    external.append(name)

            #print("%15s = %s (params: %s)" % (name, path, param_str))

        # For getopt() purposes the internal plugins have to come before the external
        ret = builtin + external

        return ret

    def version(self):
        print('Dool', __version__)
        print('Written by Scott Baker <scott@perturb.org>')
        print('Forked from Dstat written by Dag Wieers <dag@wieers.com>')
        print('Homepage at https://github.com/scottchiefbaker/dool/')
        print()
        print('Platform %s/%s' % (os.name, sys.platform))
        print('Kernel %s' % os.uname()[2])
        print('Python %s' % sys.version)
        print()

        color = ""
        if not get_term_color():
            color = "no "
        print('Terminal type: %s (%scolor support)' % (os.getenv('TERM'), color))
        rows, cols = get_term_size()
        print('Terminal size: %d lines, %d columns' % (rows, cols))
        print()
        print('Processors: %d' % getcpunr())
        print('Pagesize: %d' % resource.getpagesize())
        print('Clock ticks per secs: %d' % os.sysconf('SC_CLK_TCK'))
        print()

        global op
        op = self
        show_plugins()

    def usage(self):
        print('Usage: dool [options] [delay] [count]')

    def help(self):
        print('''\nVersatile tool for generating system resource statistics

Dool options:
  -c, --cpu                enable cpu stats
     -C 0,3,total             include cpu0, cpu3 and total
  -d, --disk               enable disk stats
     -D total,hda             include hda and total
     --diskset name:sda,sdb   group disks together for aggregate stats
  -g, --page               enable page stats
  -i, --int                enable interrupt stats
     -I 5,eth2                include int5 and interrupt used by eth2
  -l, --load               enable load stats
  -m, --mem                enable memory stats
  -n, --net                enable network stats
     -N eth1,total            include eth1 and total
  -p, --proc               enable process stats
  -r, --io                 enable io stats (I/O requests completed)
  -s, --swap               enable swap stats
     -S swap1,total           include swap1 and total
  -t, --time               enable time/date output
  -T, --epoch              enable time counter (seconds since epoch)
  -y, --sys                enable system stats

  --aio                    enable aio stats
  --fs, --filesystem       enable fs stats
  --ipc                    enable ipc stats
  --lock                   enable lock stats
  --raw                    enable raw stats
  --socket                 enable socket stats
  --tcp                    enable tcp stats
  --udp                    enable udp stats
  --unix                   enable unix stats
  --vm                     enable vm stats
  --vm-adv                 enable advanced vm stats
  --zones                  enable zoneinfo stats

  --list                   list all available plugins
  --<plugin-name>          enable external plugin by name (see --list)

  --defaults               equals -cdnlt
  --more                   equals -cdnmplt
  -a, --all                equals -cdngmyplt
  -f, --full               automatically expand -C, -D, -I, -N and -S lists
  -v, --vmstat             equals -pmgdyc -D total

  --bits                   force bits for values expressed in bytes
  --bytes                  force bytes for output measurements
  --float                  force float values on screen
  --integer                force integer values on screen

  --bw, --black-on-white   change colors for white background terminal
  --color                  force 256 colors
  --color16                force 16 colors
  --nocolor                disable colors
  --noheaders              disable repetitive headers
  --noupdate               disable intermediate updates
  --output file            write CSV output to file
  --display                output to the display (useful with --output)
  --profile                show profiling statistics when exiting dool
  --ascii                  output table data in ascii instead of ANSI

delay is the delay in seconds between each update (default: 1)
count is the number of updates to display before exiting (default: unlimited)
''')

### START STATS DEFINITIONS ###
class dool:
    vars   = None
    name   = None
    nick   = None
    type   = 'f'
    types  = ()
    width  = 5
    scale  = 1024
    scales = ()
    cols   = 0
    struct = None
    #val    = {}
    #set1   = {}
    #set2   = {}

    def prepare(self):
        if callable(self.discover):
            self.discover = self.discover()
        if callable(self.vars):
            self.vars = self.vars()
        if not self.vars:
            raise Exception('No counter objects to monitor')
        if callable(self.name):
            self.name = self.name()
        if callable(self.nick):
            self.nick = self.nick()
        if not self.nick:
            self.nick = self.vars

        self.val = {}; self.set1 = {}; self.set2 = {}
        if self.struct: ### Plugin API version 2
            for name in self.vars + [ 'total', ]:
                self.val[name] = self.struct
                self.set1[name] = self.struct
                self.set2[name] = {}
        elif self.cols <= 0: ### Plugin API version 1
            for name in self.vars:
                self.val[name] = self.set1[name] = self.set2[name] = 0
        else: ### Plugin API version 1
            for name in self.vars + [ 'total', ]:
                self.val[name] = list(range(self.cols))
                self.set1[name] = list(range(self.cols))
                self.set2[name] = list(range(self.cols))
                for i in list(range(self.cols)):
                    self.val[name][i] = self.set1[name][i] = self.set2[name][i] = 0
#        print(self.val)

    def open(self, *filenames):
        "Open stat file descriptor"
        self.file = []
        self.fd = []
        for filename in filenames:
            try:
                fd = dopen(filename)
                if fd:
                    self.file.append(filename)
                    self.fd.append(fd)
            except:
                pass
        if not self.fd:
            raise Exception('Cannot open file %s' % filename)

    def readlines(self):
        "Return lines from any file descriptor"
        for fd in self.fd:
            fd.seek(0)
            for line in fd.readlines():
               yield line
        ### Implemented linecache (for top-plugins) but slows down normal plugins
#        for fd in self.fd:
#            i = 1
#            while True:
#                line = linecache.getline(fd.name, i);
#                if not line: break
#                yield line
#                i += 1

    def splitline(self, sep=None):
        for fd in self.fd:
            fd.seek(0)
            return fd.read().split(sep)

    def splitlines(self, sep=None, replace=None):
        "Return split lines from any file descriptor"
        for fd in self.fd:
            fd.seek(0)
            for line in fd.readlines():
                if replace and sep:
                    yield line.replace(replace, sep).split(sep)
                elif replace:
                    yield line.replace(replace, ' ').split()
                else:
                    yield line.split(sep)
#        ### Implemented linecache (for top-plugins) but slows down normal plugins
#        for fd in self.fd:
#                if replace and sep:
#                    yield line.replace(replace, sep).split(sep)
#                elif replace:
#                    yield line.replace(replace, ' ').split()
#                else:
#                    yield line.split(sep)
#                i += 1

    def statwidth(self):
        "Return complete stat width"
        if self.cols:
            return len(self.vars) * self.colwidth() + len(self.vars) - 1
        else:
            return len(self.nick) * self.colwidth() + len(self.nick) - 1

    def colwidth(self):
        "Return column width"
        if isinstance(self.name, str):
            return self.width
        else:
            return len(self.nick) * self.width + len(self.nick) - 1

    def title(self):
        ret = theme['title']

        if isinstance(self.name, str):
            width = self.statwidth()
            return ret + self.name[0:width].center(width).replace(' ', char['dash']) + theme['default']
        for i, name in enumerate(self.name):
            width = self.colwidth()
            ret = ret + name[0:width].center(width).replace(' ', char['dash'])
            if i + 1 != len(self.vars):
                if op.color:
                    ret = ret + theme['frame'] + char['dash'] + theme['title']
                else:
                    ret = ret + char['space']

        return ret

    def subtitle(self):
        ret = ''

        # It's a string
        if isinstance(self.name, str):
            for i, nick in enumerate(self.nick):
                ret += theme['subtitle'] + nick[0:self.width].center(self.width)

                # If it's not the last one add a space between each item
                if i + 1 != len(self.nick):
                    ret += ansi['reset'] + char['space'] + ansi['reset']
                else:
                    ret += ansi['reset']

            return ret
        # It's a 'list'
        else:
            for i, name in enumerate(self.name):
                for j, nick in enumerate(self.nick):
                    ret += theme['subtitle'] + nick[0:self.width].center(self.width)

                    # If it's not the last one
                    if j + 1 != len(self.nick):
                        ret = ret + ansi['reset'] + char['space'] + ansi['reset']

                # If it's not the last one
                if i + 1 != len(self.name):
                    ret += theme['subtitle'] + char['space'] + ansi['reset']
                else:
                    ret += ansi['reset']

            return ret

    def csvtitle(self):
        if isinstance(self.name, str):
            return '"' + self.name + '"' + char['sep'] * (len(self.nick) - 1)
        else:
            ret = ''
            for i, name in enumerate(self.name):
                ret = ret + '"' + name + '"' + char['sep'] * (len(self.nick) - 1)
                if i + 1 != len(self.name): ret = ret + char['sep']
            return ret

    def csvsubtitle(self):
        ret = ''
        if isinstance(self.name, str):
            for i, nick in enumerate(self.nick):
                ret = ret + '"' + nick + '"'
                if i + 1 != len(self.nick): ret = ret + char['sep']
        elif len(self.name) == 1:
            for i, name in enumerate(self.name):
                for j, nick in enumerate(self.nick):
                    ret = ret + '"' + nick + '"'
                    if j + 1 != len(self.nick): ret = ret + char['sep']
                if i + 1 != len(self.name): ret = ret + char['sep']
        else:
            for i, name in enumerate(self.name):
                for j, nick in enumerate(self.nick):
                    ret = ret + '"' + name + ':' + nick + '"'
                    if j + 1 != len(self.nick): ret = ret + char['sep']
                if i + 1 != len(self.name): ret = ret + char['sep']
        return ret

    def check(self):
        "Check if stat is applicable"
#        if hasattr(self, 'fd') and not self.fd:
#            raise Exception, 'File %s does not exist' % self.fd
        if not self.vars:
            raise Exception('No objects found, no stats available')
        if not self.discover:
            raise Exception('No objects discovered, no stats available')
        if self.colwidth():
            return True
        raise Exception('Unknown problem, please report')

    def discover(self, *objlist):
        return True

    def show(self):
        "Display stat results"
        line = ''
        if hasattr(self, 'output'):
            return cprint(self.output, self.type, self.width, self.scale)

        for i, name in enumerate(self.vars):
            if i < len(self.types):
                ctype = self.types[i]
            else:
                ctype = self.type

            if i < len(self.scales):
                scale = self.scales[i]
            else:
                scale = self.scale

            if isinstance(self.val[name], Sequence) and not isinstance(self.val[name], str):
                line = line + cprintlist(self.val[name], ctype, self.width, scale)
                sep  = theme['subframe'] + char['colon'] + ansi['reset']

                if i + 1 != len(self.vars):
                    line = line + sep
            else:
                ### Make sure we don't show more values than we have nicknames
                if i >= len(self.nick): break

                line = line + cprint(self.val[name], ctype, self.width, scale)
                sep  = char['space']

                if i + 1 != len(self.nick):
                    line = line + sep

        return line

    def showend(self, totlist, vislist):
        if vislist and self is not vislist[-1]:
            return theme['frame'] + char['pipe']
        elif totlist != vislist:
            return theme['frame'] + char['gt']
        return ''

    def showcsv(self):
        def printcsv(var):
            if var != round(var):
                return '%.3f' % var
            return '%d' % int(round(var))

        line = ''
        for i, name in enumerate(self.vars):
            # What TYPE of variable is this. May be used for conversions later
            if i < len(self.types):
                ctype = self.types[i]
            else:
                ctype = self.type

            if isinstance(self.val[name], list) or isinstance(self.val[name], tuple):
                for j, val in enumerate(self.val[name]):
                    # If this is a bytes value and we have bits enabled we need to convert
                    if ctype == 'b' and op.bits:
                        val *= 8.0;

                    line = line + printcsv(val)
                    if j + 1 != len(self.val[name]):
                        line = line + char['sep']
            elif isinstance(self.val[name], str):
                line = line + self.val[name]
            else:
                line = line + printcsv(self.val[name])
            if i + 1 != len(self.vars):
                line = line + char['sep']
        return line

    def showcsvend(self, totlist, vislist):
        if vislist and self is not vislist[-1]:
            return char['sep']
        elif totlist and self is not totlist[-1]:
            return char['sep']
        return ''

class dool_aio(dool):
    def __init__(self):
        self.name  = 'async'
        self.nick  = ('#aio',)
        self.vars  = ('aio',)
        self.type  = 'd'
        self.width = 5;
        self.open('/proc/sys/fs/aio-nr')

    def extract(self):
        for l in self.splitlines():
            if len(l) < 1: continue
            self.val['aio'] = int(l[0])

class dool_cpu(dool):
    def __init__(self):
        self.nick  = ( 'usr', 'sys', 'idl', 'wai', 'stl' )
        self.type  = 'p'
        self.width = 3
        self.scale = 34
        self.open('/proc/stat')
        self.cols  = 5

    def discover(self, *objlist):
        ret = []
        for l in self.splitlines():
            if len(l) < 9 or l[0][0:3] != 'cpu': continue
            ret.append(l[0][3:])
        ret.sort()
        for item in objlist: ret.append(item)
        return ret

    def vars(self):
        ret = []
        if op.cpulist and 'all' in op.cpulist:
            varlist = []
            cpu = 0
            while cpu < cpunr:
                varlist.append(str(cpu))
                cpu = cpu + 1
#           if len(varlist) > 2: varlist = varlist[0:2]
        elif op.cpulist:
            varlist = op.cpulist
        else:
            varlist = ('total',)
        for name in varlist:
            if name in self.discover + ['total']:
                ret.append(name)
        return ret

    def name(self):
        ret = []
        for name in self.vars:
            if name == 'total':
                ret.append('total cpu usage')
            else:
                ret.append('cpu' + name + ' usage')
        return ret

    def extract(self):
        for l in self.splitlines():
            if len(l) < 9: continue
            for name in self.vars:
                if l[0] == 'cpu' + name or ( l[0] == 'cpu' and name == 'total' ):
                    self.set2[name] = ( int(l[1]) + int(l[2]) + int(l[6]) + int(l[7]), int(l[3]), int(l[4]), int(l[5]), int(l[8]) )

        for name in self.vars:
            for i in list(range(self.cols)):
                if sum(self.set2[name]) > sum(self.set1[name]):
                    self.val[name][i] = 100.0 * (self.set2[name][i] - self.set1[name][i]) / (sum(self.set2[name]) - sum(self.set1[name]))
                else:
                    self.val[name][i] = 0
#                    print("Error: tick problem detected, this should never happen !", file=sys.stderr)

        if step == op.delay:
            self.set1.update(self.set2)

class dool_cpu_use(dool_cpu):
    def __init__(self):
        self.name  = 'per cpu usage'
        self.type  = 'p'
        self.width = 3
        self.scale = 34
        self.open('/proc/stat')
        self.cols  = 7
        if not op.cpulist:
            self.vars = [ str(x) for x in list(range(cpunr)) ]

    def extract(self):
        for l in self.splitlines():
            if len(l) < 9: continue
            for name in self.vars:
                if l[0] == 'cpu' + name or ( l[0] == 'cpu' and name == 'total' ):
                    self.set2[name] = ( int(l[1]) + int(l[2]), int(l[3]), int(l[4]), int(l[5]), int(l[6]), int(l[7]), int(l[8]) )

        for name in self.vars:
            if sum(self.set2[name]) > sum(self.set1[name]):
                self.val[name] = 100.0 - 100.0 * (self.set2[name][2] - self.set1[name][2]) / (sum(self.set2[name]) - sum(self.set1[name]))
            else:
                self.val[name] = 0
#                    print("Error: tick problem detected, this should never happen !", file=sys.stderr)

        if step == op.delay:
            self.set1.update(self.set2)

class dool_cpu_adv(dool_cpu):
    def __init__(self):
        self.nick  = ( 'usr', 'sys', 'idl', 'wai', 'hiq', 'siq', 'stl' )
        self.type  = 'p'
        self.width = 3
        self.scale = 34
        self.open('/proc/stat')
        self.cols  = 7

    def extract(self):
        for l in self.splitlines():
            if len(l) < 9: continue
            for name in self.vars:
                if l[0] == 'cpu' + name or ( l[0] == 'cpu' and name == 'total' ):
                    self.set2[name] = ( int(l[1]) + int(l[2]), int(l[3]), int(l[4]), int(l[5]), int(l[6]), int(l[7]), int(l[8]) )

        for name in self.vars:
            for i in list(range(self.cols)):
                if sum(self.set2[name]) > sum(self.set1[name]):
                    self.val[name][i] = 100.0 * (self.set2[name][i] - self.set1[name][i]) / (sum(self.set2[name]) - sum(self.set1[name]))
                else:
                    self.val[name][i] = 0
#                    print("Error: tick problem detected, this should never happen !", file=sys.stderr)

        if step == op.delay:
            self.set1.update(self.set2)

class dool_disk(dool):
    def __init__(self):
        self.nick = ('read', 'writ')
        self.type = 'b'
        self.cols = 2
        self.open('/proc/diskstats')

    def discover(self, *objlist):
        ret = []
        for l in self.splitlines():
            if len(l) < 13: continue
            if set(l[3:]) == {'0'}: continue
            name = l[2]
            ret.append(name)
        for item in objlist: ret.append(item)
        if not ret:
            raise Exception("No suitable block devices found to monitor")

        return ret

    def vars(self):
        ret = []

        if op.disklist:
            varlist = []
            for x in op.disklist:
                dev = get_dev_name(x)
                varlist.append(dev)
        elif not op.full:
            varlist = ('total',)
        else:
            varlist = []
            for name in self.discover:
                if DOOL_DISKFILTER.match(name): continue
                if name not in blockdevices(): continue
                varlist.append(name)
#           if len(varlist) > 2: varlist = varlist[0:2]
            varlist.sort()
        for name in varlist:
            if name in self.discover + ['total'] or name in op.diskset:
                ret.append(name)
        return ret

    def name(self):
        ret = []
        for name in self.vars:
            # Shorten the device name to 5 chars
            short = dev_short_name(name, 5)
            full  = "dsk/" + short

            ret.append(full)

        return ret

    def extract(self):
        for name in self.vars: self.set2[name] = (0, 0)

        # Loop through each item in /proc/diskstats
        for l in self.splitlines():
            if len(l) < 13: continue
            if l[5] == '0' and l[9] == '0': continue
            if set(l[3:]) == {'0'}: continue

            name = l[2]

            if not DOOL_DISKFILTER.match(name):
                devel_log("Adding disk stats for '%s' %d/%d to total" % (name, int(l[5]), int(l[9])))

                self.set2['total'] = ( self.set2['total'][0] + int(l[5]), self.set2['total'][1] + int(l[9]) )
            if name in self.vars and name != 'total':
                self.set2[name] = ( self.set2[name][0] + int(l[5]), self.set2[name][1] + int(l[9]) )

            # Process disksets
            for diskset in self.vars:
                if diskset in op.diskset:
                    for disk in op.diskset[diskset]:
                        if fnmatch.fnmatch(name, disk):
                            self.set2[diskset] = ( self.set2[diskset][0] + int(l[5]), self.set2[diskset][1] + int(l[9]) )

        for name in self.set2:
            self.val[name] = list(map(lambda x, y: (y - x) * 512.0 / elapsed, self.set1[name], self.set2[name]))

        if step == op.delay:
            self.set1.update(self.set2)

class dool_epoch(dool):
    def __init__(self):
        self.name  = 'epoch'
        self.vars  = ('epoch',)
        self.width = 10
        self.scale = 0

        # We append ms in debug mode so we widen this a bit
        if op.debug:
            self.width += 4

    # This is the unixtime when this loop interation ran
    def extract(self):
        self.val['epoch'] = starttime

class dool_fs(dool):
    def __init__(self):
        self.name  = 'filesystem'
        self.vars  = ('files', 'inodes')
        self.type  = 'd'
        self.width = 6
        self.scale = 1000

    def extract(self):
        for line in dopen('/proc/sys/fs/file-nr'):
            l = line.split()
            if len(l) < 1: continue
            self.val['files'] = int(l[0])
        for line in dopen('/proc/sys/fs/inode-nr'):
            l = line.split()
            if len(l) < 2: continue
            self.val['inodes'] = int(l[0]) - int(l[1])

class dool_int(dool):
    def __init__(self):
        self.name   = 'interrupts'
        self.type   = 'd'
        self.width  = 5
        self.scale  = 1000
        self.open('/proc/stat')
        self.intmap = self.intmap()

    def intmap(self):
        ret = {}
        for line in dopen('/proc/interrupts'):
            l = line.split()
            if len(l) <= cpunr: continue
            l1 = l[0].split(':')[0]
            l2 = ' '.join(l[cpunr+2:]).split(',')
            ret[l1] = l1
            for name in l2:
                ret[name.strip().lower()] = l1
        return ret

    def discover(self, *objlist):
        ret = []
        for l in self.splitlines():
            if l[0] != 'intr': continue
            for name, i in enumerate(l[2:]):
                if int(i) > 10: ret.append(str(name))
        return ret

#   def check(self):
#       if self.fd[0] and self.vars:
#           self.fd[0].seek(0)
#           for l in self.fd[0].splitlines():
#               if l[0] != 'intr': continue
#               return True
#       return False

    def vars(self):
        ret = []
        if op.intlist:
            varlist = op.intlist
        else:
            varlist = self.discover
            for name in varlist:
                if name in ('0', '1', '2', '8', 'NMI', 'LOC', 'MIS', 'CPU0'):
                    varlist.remove(name)
            if not op.full and len(varlist) > 3: varlist = varlist[-3:]
        for name in varlist:
            if name in self.discover + ['total',]:
                ret.append(name)
            elif name.lower() in self.intmap:
                ret.append(self.intmap[name.lower()])
        return ret

    def extract(self):
        for l in self.splitlines():
            if not l or l[0] != 'intr': continue
            for name in self.vars:
                if name != 'total':
                    self.set2[name] = int(l[int(name) + 2])
            self.set2['total'] = int(l[1])

        for name in self.vars:
            self.val[name] = (self.set2[name] - self.set1[name]) * 1.0 / elapsed

        if step == op.delay:
            self.set1.update(self.set2)

class dool_io(dool):
    def __init__(self):
        self.nick  = ('read', 'writ')
        self.type  = 'f'
        self.width = 5
        self.scale = 1000
        self.cols  = 2
        self.open('/proc/diskstats')

    def discover(self, *objlist):
        ret = []
        for l in self.splitlines():
            if len(l) < 13: continue
            if set(l[3:]) == {'0'}: continue
            name = l[2]
            ret.append(name)
        for item in objlist: ret.append(item)
        if not ret:
            raise Exception("No suitable block devices found to monitor")
        return ret

    def vars(self):
        ret = []
        if op.disklist:
            varlist = []
            for x in op.disklist:
                dev = get_dev_name(x)
                varlist.append(dev)

        elif not op.full:
            varlist = ('total',)
        else:
            varlist = []
            for name in self.discover:
                if DOOL_DISKFILTER.match(name): continue
                if name not in blockdevices(): continue
                varlist.append(name)
#           if len(varlist) > 2: varlist = varlist[0:2]
            varlist.sort()
        for name in varlist:
            if name in self.discover + ['total'] or name in op.diskset:
                ret.append(name)
        return ret

    def name(self):
        return ['io/'+name for name in self.vars]

    def extract(self):
        for name in self.vars: self.set2[name] = (0, 0)
        for l in self.splitlines():
            if len(l) < 13: continue
            if l[3] == '0' and l[7] == '0': continue
            name = l[2]
            if set(l[3:]) == {'0'}: continue
            if not DOOL_DISKFILTER.match(name):
                self.set2['total'] = ( self.set2['total'][0] + int(l[3]), self.set2['total'][1] + int(l[7]) )
            if name in self.vars and name != 'total':
                self.set2[name] = ( self.set2[name][0] + int(l[3]), self.set2[name][1] + int(l[7]) )
            for diskset in self.vars:
                if diskset in op.diskset:
                    for disk in op.diskset[diskset]:
                        if fnmatch.fnmatch(name, disk):
                            self.set2[diskset] = ( self.set2[diskset][0] + int(l[3]), self.set2[diskset][1] + int(l[7]) )

        for name in self.set2:
            self.val[name] = list(map(lambda x, y: (y - x) * 1.0 / elapsed, self.set1[name], self.set2[name]))

        if step == op.delay:
            self.set1.update(self.set2)

class dool_ipc(dool):
    def __init__(self):
        self.name  = 'sysv ipc'
        self.vars  = ('msg', 'sem', 'shm')
        self.type  = 'd'
        self.width = 3
        self.scale = 10

    def extract(self):
        for name in self.vars:
            self.val[name] = len(dopen('/proc/sysvipc/'+name).readlines()) - 1

class dool_load(dool):
    def __init__(self):
        self.name  = 'load avg'
        self.nick  = ('1m', '5m', '15m')
        self.vars  = ('load1', 'load5', 'load15')
        self.type  = 'f'
        self.width = 4
        self.scale = 0.5
        self.open('/proc/loadavg')

    def extract(self):
        for l in self.splitlines():
            if len(l) < 3: continue
            self.val['load1'] = float(l[0])
            self.val['load5'] = float(l[1])
            self.val['load15'] = float(l[2])

class dool_lock(dool):
    def __init__(self):
        self.name  = 'file locks'
        self.nick  = ('pos', 'lck', 'rea', 'wri')
        self.vars  = ('posix', 'flock', 'read', 'write')
        self.type  = 'f'
        self.width = 3
        self.scale = 10
        self.open('/proc/locks')

    def extract(self):
        for name in self.vars: self.val[name] = 0
        for l in self.splitlines():
            if len(l) < 4: continue
            if l[1] == 'POSIX': self.val['posix'] += 1
            elif l[1] == 'FLOCK': self.val['flock'] += 1
            if l[3] == 'READ': self.val['read'] += 1
            elif l[3] == 'WRITE': self.val['write'] += 1

class dool_mem(dool):
    def __init__(self):
        self.name = 'memory usage'
        self.nick = ('used', 'free', 'cach', 'avai')
        self.vars = ('MemUsed', 'MemFree', 'Cached', 'MemAvailable')
        self.open('/proc/meminfo')

    def extract(self):
        adv_extract_vars = ('MemTotal', 'Shmem', 'SReclaimable')
        adv_val={}
        for l in self.splitlines():
            if len(l) < 2: continue
            name = l[0].split(':')[0]
            if name in self.vars:
                self.val[name] = int(l[1]) * 1024.0
            if name in adv_extract_vars:
                adv_val[name] = int(l[1]) * 1024.0

        # Original math
        #self.val['MemUsed'] = adv_val['MemTotal'] - self.val['MemFree'] - self.val['Buffers'] - self.val['Cached'] - adv_val['SReclaimable'] + adv_val['Shmem']

        # New math that is closer to the `free` output
        self.val['MemUsed'] = adv_val['MemTotal'] - self.val['MemFree'] - self.val['Cached'] - adv_val['SReclaimable']

class dool_mem_adv(dool_mem):
    """
    Advanced memory usage

    Displays memory usage similarly to the internal plugin but with added total, shared and reclaimable counters.
    Additionally, shared memory is added and reclaimable memory is subtracted from the used memory counter.
    """
    def __init__(self):
        self.name = 'advanced memory usage'
        self.nick = ('total', 'used', 'free', 'buff', 'cach', 'dirty', 'shmem', 'recl')
        self.vars = ('MemTotal', 'MemUsed', 'MemFree', 'Buffers', 'Cached', 'Dirty', 'Shmem', 'SReclaimable')
        self.open('/proc/meminfo')

class dool_net(dool):
    def __init__(self):
        self.nick        = ('recv', 'send')
        self.type        = 'b'
        self.totalfilter = re.compile(r'^(lo|bond\d+|face|.+\.\d+)$')
        self.open('/proc/net/dev')
        self.cols        = 2

    def discover(self, *objlist):
        ret = []
        for l in self.splitlines(replace=':'):
            if len(l) < 17: continue
            if l[2] == '0' and l[10] == '0': continue
            name = l[0]
            if name not in ('lo', 'face'):
                ret.append(name)
        ret.sort()
        for item in objlist: ret.append(item)
        return ret

    def vars(self):
        ret = []
        if op.netlist:
            varlist = op.netlist
        elif not op.full:
            varlist = ('total',)
        else:
            varlist = self.discover
#           if len(varlist) > 2: varlist = varlist[0:2]
            varlist.sort()
        for name in varlist:
            if name in self.discover + ['total', 'lo']:
                ret.append(name)
        if not ret:
            raise Exception("No suitable network interfaces found to monitor")
        return ret

    def name(self):
        return ['net/'+name for name in self.vars]

    def extract(self):
        self.set2['total'] = [0, 0]
        for l in self.splitlines(replace=':'):
            if len(l) < 17: continue
            if l[2] == '0' and l[10] == '0': continue
            name = l[0]
            if name in self.vars :
                self.set2[name] = ( int(l[1]), int(l[9]) )
            if not self.totalfilter.match(name):
                self.set2['total'] = ( self.set2['total'][0] + int(l[1]), self.set2['total'][1] + int(l[9]))

        if update:
            for name in self.set2:
                self.val[name] = list(map(lambda x, y: (y - x) * 1.0 / elapsed, self.set1[name], self.set2[name]))
                if self.val[name][0] < 0: self.val[name][0] += maxint + 1
                if self.val[name][1] < 0: self.val[name][1] += maxint + 1

        if step == op.delay:
            self.set1.update(self.set2)

class dool_page(dool):
    def __init__(self):
        self.name = 'paging'
        self.nick = ('in', 'out')
        self.vars = ('pswpin', 'pswpout')
        self.type = 'd'
        self.open('/proc/vmstat')

    def extract(self):
        for l in self.splitlines():
            if len(l) < 2: continue
            name = l[0]
            if name in self.vars:
                self.set2[name] = int(l[1])

        for name in self.vars:
            self.val[name] = (self.set2[name] - self.set1[name]) * pagesize * 1.0 / elapsed

        if step == op.delay:
            self.set1.update(self.set2)

class dool_proc(dool):
    def __init__(self):
        self.name  = 'procs'
        self.nick  = ('run', 'blk', 'new')
        self.vars  = ('procs_running', 'procs_blocked', 'processes')
        self.type  = 'f'
        self.width = 3
        self.scale = 10
        self.open('/proc/stat')

    def extract(self):
        for l in self.splitlines():
            if len(l) < 2: continue
            name = l[0]
            if name == 'processes':
                self.val['processes'] = 0
                self.set2[name] = int(l[1])
            elif name == 'procs_running':
                self.set2[name] = self.set2[name] + int(l[1]) - 1
            elif name == 'procs_blocked':
                self.set2[name] = self.set2[name] + int(l[1])

        self.val['processes'] = (self.set2['processes'] - self.set1['processes']) * 1.0 / elapsed
        for name in ('procs_running', 'procs_blocked'):
            self.val[name] = self.set2[name] * 1.0

        if step == op.delay:
            self.set1.update(self.set2)
            for name in ('procs_running', 'procs_blocked'):
                self.set2[name] = 0

class dool_raw(dool):
    def __init__(self):
        self.name  = 'raw'
        self.nick  = ('raw',)
        self.vars  = ('sockets',)
        self.type  = 'd'
        self.width = 4
        self.scale = 1000
        self.open('/proc/net/raw')

    def extract(self):
        lines = -1
        for line in self.readlines():
            lines += 1
        self.val['sockets'] = lines
        ### Cannot use len() on generator
#        self.val['sockets'] = len(self.readlines()) - 1

class dool_socket(dool):
    def __init__(self):
        self.name  = 'sockets'
        self.type  = 'd'
        self.width = 4
        self.scale = 1000
        self.open('/proc/net/sockstat')
        self.nick  = ('tot', 'tcp', 'udp', 'raw', 'frg')
        self.vars  = ('sockets:', 'TCP:', 'UDP:', 'RAW:', 'FRAG:')

    def extract(self):
        for l in self.splitlines():
            if len(l) < 3: continue
            self.val[l[0]] = int(l[2])

        self.val['other'] = self.val['sockets:'] - self.val['TCP:'] - self.val['UDP:'] - self.val['RAW:'] - self.val['FRAG:']

class dool_swap(dool):
    def __init__(self):
        self.nick = ('used', 'free')
        self.type = 'd'
        self.open('/proc/swaps')

    def discover(self, *objlist):
        ret = []
        for l in self.splitlines():
            if len(l) < 5: continue
            if l[0] == 'Filename': continue
            try:
                int(l[2])
                int(l[3])
            except:
                continue
#           ret.append(improve(l[0]))
            ret.append(l[0])
        ret.sort()
        for item in objlist: ret.append(item)
        return ret

    def vars(self):
        ret = []
        if op.swaplist:
            varlist = op.swaplist
        elif not op.full:
            varlist = ('total',)
        else:
            varlist = self.discover
#           if len(varlist) > 2: varlist = varlist[0:2]
            varlist.sort()
        for name in varlist:
            if name in self.discover + ['total']:
                ret.append(name)
        if not ret:
            raise Exception("No suitable swap devices found to monitor")
        return ret

    def name(self):
        num_swaps = len(self.vars)

        # If it's just ONE swap the name is simple: 'swap'
        if (num_swaps == 1):
            ret = "swap"
        # If we have more than one we break them out
        else:
            ret = []
            for dev in self.vars:
                dev        = basename(dev)
                short_name = dev_short_name(dev, 4)
                ret.append('swap/' + short_name)

        return ret


    def extract(self):
        self.val['total'] = [0, 0]
        for l in self.splitlines():
            if len(l) < 5 or l[0] == 'Filename': continue
            name = l[0]
            self.val[name] = ( int(l[3]) * 1024.0, (int(l[2]) - int(l[3])) * 1024.0 )
            self.val['total'] = ( self.val['total'][0] + self.val[name][0], self.val['total'][1] + self.val[name][1])

class dool_sys(dool):
    def __init__(self):
        self.name  = 'system'
        self.nick  = ('int', 'csw')
        self.vars  = ('intr', 'ctxt')
        self.type  = 'd'
        self.width = 5
        self.scale = 1000
        self.open('/proc/stat')

    def extract(self):
        for l in self.splitlines():
            if len(l) < 2: continue
            name = l[0]
            if name in self.vars:
                self.set2[name] = int(l[1])

        for name in self.vars:
            self.val[name] = (self.set2[name] - self.set1[name]) * 1.0 / elapsed

        if step == op.delay:
            self.set1.update(self.set2)

class dool_tcp(dool):
    def __init__(self):
        self.name  = 'tcp sockets'
        self.nick  = ('lis', 'act', 'syn', 'tim', 'clo')
        self.vars  = ('listen', 'established', 'syn', 'wait', 'close')
        self.type  = 'd'
        self.width = 4
        self.scale = 1000
        self.open('/proc/net/tcp', '/proc/net/tcp6')

    def extract(self):
        for name in self.vars: self.val[name] = 0
        for l in self.splitlines():
            if len(l) < 12: continue
            ### 01: established, 02: syn_sent,  03: syn_recv, 04: fin_wait1,
            ### 05: fin_wait2,   06: time_wait, 07: close,    08: close_wait,
            ### 09: last_ack,    0A: listen,    0B: closing
            if l[3] in ('0A',): self.val['listen'] += 1
            elif l[3] in ('01',): self.val['established'] += 1
            elif l[3] in ('02', '03', '09',): self.val['syn'] += 1
            elif l[3] in ('06',): self.val['wait'] += 1
            elif l[3] in ('04', '05', '07', '08', '0B',): self.val['close'] += 1

class dool_time(dool):
    def __init__(self):
        self.name    = 'system'
        self.vars    = ('time',)
        self.type    = 's'
        self.scale   = 0
        self.timefmt = os.getenv('DOOL_TIMEFMT') or '%b-%d %H:%M:%S'
        self.width   = len(time.strftime(self.timefmt, time.localtime()))

        # In debug we append ms, so we extend the width to accomodate
        if op.debug:
            self.width += 4

    # starttime is the unixtime this loop started
    def extract(self):
        self.val['time'] = time.strftime(self.timefmt, time.localtime(starttime))

        if op.debug:
            self.val['time'] += ".%03d" % (round(starttime * 1000 % 1000))

class dool_udp(dool):
    def __init__(self):
        self.name  = 'udp'
        self.nick  = ('lis', 'act')
        self.vars  = ('listen', 'established')
        self.type  = 'd'
        self.width = 4
        self.scale = 1000
        self.open('/proc/net/udp', '/proc/net/udp6')

    def extract(self):
        for name in self.vars: self.val[name] = 0
        for l in self.splitlines():
            if l[3] == '07': self.val['listen'] += 1
            elif l[3] == '01': self.val['established'] += 1

class dool_unix(dool):
    def __init__(self):
        self.name  = 'unix sockets'
        self.nick  = ('dgm', 'str', 'lis', 'act')
        self.vars  = ('datagram', 'stream', 'listen', 'established')
        self.type  = 'd'
        self.width = 4
        self.scale = 1000
        self.open('/proc/net/unix')

    def extract(self):
        for name in self.vars: self.val[name] = 0
        for l in self.splitlines():
            if l[4] == '0002': self.val['datagram'] += 1
            elif l[4] == '0001':
                self.val['stream'] += 1
                if l[5] == '01': self.val['listen'] += 1
                elif l[5] == '03': self.val['established'] += 1

class dool_vm(dool):
    def __init__(self):
        self.name  = 'virtual memory'
        self.nick  = ('majpf', 'minpf', 'alloc', 'free')
        ### Page allocations should include all page zones, not just ZONE_NORMAL,
        ### but also ZONE_DMA, ZONE_HIGHMEM, ZONE_DMA32 (depending on architecture)
        self.vars  = ('pgmajfault', 'pgfault', 'pgalloc_*', 'pgfree')
        self.type  = 'd'
        self.width = 5
        self.scale = 1000
        self.open('/proc/vmstat')

    def extract(self):
        for name in self.vars:
            self.set2[name] = 0
        for l in self.splitlines():
            if len(l) < 2: continue
            for name in self.vars:
                if fnmatch.fnmatch(l[0], name):
                    self.set2[name] += int(l[1])

        for name in self.vars:
            self.val[name] = (self.set2[name] - self.set1[name]) * 1.0 / elapsed

        if step == op.delay:
            self.set1.update(self.set2)

class dool_vm_adv(dool_vm):
    def __init__(self):
        self.name  = 'advanced virtual memory'
        self.nick  = ('steal', 'scanK', 'scanD', 'pgoru', 'astll')
        self.vars  = ('pgsteal_*', 'pgscan_kswapd_*', 'pgscan_direct_*', 'pageoutrun', 'allocstall')
        self.type  = 'd'
        self.width = 5
        self.scale = 1000
        self.open('/proc/vmstat')

class dool_zones(dool):
    def __init__(self):
        self.name  = 'zones memory'
#        self.nick = ('dmaF', 'dmaH', 'd32F', 'd32H', 'movaF', 'movaH')
#        self.vars = ('DMA_free', 'DMA_high', 'DMA32_free', 'DMA32_high', 'Movable_free', 'Movable_high')
        self.nick  = ('d32F', 'd32H', 'normF', 'normH')
        self.vars  = ('DMA32_free', 'DMA32_high', 'Normal_free', 'Normal_high')
        self.type  = 'd'
        self.width = 5
        self.scale = 1000
        self.open('/proc/zoneinfo')

    ### Page allocations should include all page zones, not just ZONE_NORMAL,
    ### but also ZONE_DMA, ZONE_HIGHMEM, ZONE_DMA32 (depending on architecture)
    def extract(self):
        for l in self.splitlines():
            if len(l) < 2: continue
            if l[0].startswith('Node'):
                zone = l[3]
                found_high = 0
            if l[0].startswith('pages'):
                self.val[zone+'_free'] = int(l[2])
            if l[0].startswith('high') and not found_high:
                self.val[zone+'_high'] = int(l[1])
                found_high = 1

### END STATS DEFINITIONS ###

###############################################################################
###############################################################################
###############################################################################

# Handle catching CTRL + C when we quit
def signal_handler(signum, frame):
    #print("%s\n\nWe caught signal #%d!" % (fg_color(15), signum))

    # If we're outputting to a file do some cleanup
    if op.output:
        outputfile.flush()

    # If we're outputting to the display
    if op.display:
        # Print a couple of spaces to cover up the "^C" that gets printed
        sys.stdout.write("\b\b        ")
        # Reset the ANSI colors just in case
        sys.stdout.write(ansi['reset'])
        sys.stdout.write("\n")
        sys.stdout.flush()

    sys.exit(0)

# Configure which signals to listen for
def init_signal_handling():
    if os.name == 'nt':
        signal.signal(signal.SIGBREAK, signal_handler)
    elif os.name == 'posix':
        signal.signal(signal.SIGHUP, signal_handler)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

# Set the ANSI foreground color
def fg_color(num):
   ret = "\033[38;5;" + str(num) + "m"

   return ret

# Set the ANSI background color
def bg_color(num):
   ret = "\033[48;5;" + str(num) + "m"

   return ret

# Wrap some text in a color and then a reset
def text_color(num, mystr):
   ret = "\033[38;5;" + str(num) + "m" + mystr +  "\033[0m"

   return ret

# Colors for a 256 color terminal
color = {
     'black'      : fg_color(0),
     'white'      : fg_color(15),
     'red'        : fg_color(9),
     'darkred'    : fg_color(88),
     'blue'       : fg_color(51),
     'darkblue'   : fg_color(39),
     'green'      : fg_color(83),
     'darkgreen'  : fg_color(28),
     'yellow'     : fg_color(227),
     'darkyellow' : fg_color(214),
     'gray'       : fg_color(7),
     'darkgray'   : fg_color(239),
     'magenta'    : fg_color(13),
     'darkmagenta': fg_color(5),
     'cyan'       : fg_color(14),
     'darkcyan'   : fg_color(5),

     'blackbg'  : '\033[40m',
     'redbg'    : '\033[41m',
     'greenbg'  : '\033[42m',
     'yellowbg' : '\033[43m',
     'bluebg'   : '\033[44m',
     'magentabg': '\033[45m',
     'cyanbg'   : '\033[46m',
     'whitebg'  : '\033[47m',
}

# Colors for a 16 color terminal
color16 = {
    'black'      : '\033[0;30m',
    'white'      : '\033[1;37m',
    'red'        : '\033[1;31m',
    'darkred'    : '\033[0;31m',
    'blue'       : '\033[1;34m',
    'darkblue'   : '\033[0;34m',
    'green'      : '\033[1;32m',
    'darkgreen'  : '\033[0;32m',
    'yellow'     : '\033[1;33m',
    'darkyellow' : '\033[0;33m',
    'gray'       : '\033[0;37m',
    'darkgray'   : '\033[1;30m',
    'magenta'    : '\033[1;35m',
    'darkmagenta': '\033[0;35m',
    'cyan'       : '\033[1;36m',
    'darkcyan'   : '\033[0;36m',

    'blackbg'  : '\033[40m',
    'redbg'    : '\033[41m',
    'greenbg'  : '\033[42m',
    'yellowbg' : '\033[43m',
    'bluebg'   : '\033[44m',
    'magentabg': '\033[45m',
    'cyanbg'   : '\033[46m',
    'whitebg'  : '\033[47m',
}

# Some ANSI presets to make the code easier to read
ansi = {
    'reset'    : '\033[0;0m',
    'bold'     : '\033[1m',
    'reverse'  : '\033[2m',
    'underline': '\033[4m',

    'clear'       : '\033[2J',
    'clearline'   : '\033[2K',
    'save'        : '\033[s',
    'restore'     : '\033[u',
    'save_all'    : '\0337',
    'restore_all' : '\0338',
    'linewrap'    : '\033[7h',
    'nolinewrap'  : '\033[7l',
    'column_zero' : '\033[0G',

    'up'   : '\033[1A',
    'down' : '\033[1B',
    'right': '\033[1C',
    'left' : '\033[1D',

    'default': '\033[0;0m',
}

# Characters we use to draw the boxes
char = {
    'pipe'           : '|',
    'colon'          : ':',
    'gt'             : '>',
    'space'          : ' ',
    'dash'           : '-',
    'plus'           : '+',
    'underscore'     : '_',
    'sep'            : ',',
    'title_sep'      : '|',
    'title_sep_first': '|',
}

# Unicode chars we use to override the defaults to get cleaner boxes
char_box_draw = {
    'pipe'           : u'\u2502',
    'dash'           : u'\u2504',
    'title_sep_first': u'\u252c', # T
    'title_sep'      : u'\u253c', # +
    'colon'          : u'\u250a',
}

# Build a theme based on the color choice 16/256
def set_theme():
    "Provide a set of colors to use"
    global color
    if op.color == 16:
        color = color16

    if op.blackonwhite:
        theme = {
            'title'     : color['darkblue'],
            'subtitle'  : color['darkcyan'] + ansi['underline'],
            'frame'     : color['darkblue'],
            'subframe'  : color['darkcyan'],
            'default'   : ansi['default'],
            'error'     : color['white'] + color['redbg'],
            'roundtrip' : color['darkblue'],
            'debug'     : color['darkred'],
            'input'     : color['darkgray'],
            'done_lo'   : color['black'],
            'done_hi'   : color['darkgray'],
            'text_lo'   : color['black'],
            'text_hi'   : color['darkgray'],
            'unit_lo'   : color['black'],
            'unit_hi'   : color['darkgray'],
            'colors_lo' : (color['darkred'], color['darkmagenta'], color['darkgreen'], color['darkblue'],
                          color['darkcyan'], color['black'], color['red'], color['green']),
            'colors_hi' : (color['red'], color['magenta'], color['green'], color['blue'],
                          color['cyan'], color['darkgray'], color['darkred'], color['darkgreen']),
        }
    else:
        theme = {
            'title'     : color['darkblue'],
            'subtitle'  : color['blue'] + ansi['underline'],
            'frame'     : color['darkblue'],
            'subframe'  : color['blue'],
            'default'   : ansi['default'],
            'error'     : color['white'] + color['redbg'],
            'roundtrip' : color['darkblue'],
            'debug'     : color['darkred'],
            'input'     : color['darkgray'],
            'done_lo'   : color['white'],
            'done_hi'   : color['gray'],
            'text_lo'   : color['gray'],
            'text_hi'   : color['darkgray'],
            'unit_lo'   : color['gray'],
            'unit_hi'   : color['darkgray'],
            'colors_lo' : (color['red'], color['yellow'], color['green'], color['blue'],
                          color['cyan'], color['white'], color['darkred'], color['darkgreen']),
            'colors_hi' : (color['darkred'], color['darkyellow'], color['darkgreen'], color['darkblue'],
                          color['darkcyan'], color['gray'], color['red'], color['green']),
        }
    return theme

def ticks():
    "Return the number of 'ticks' since bootup"
    try:
        for line in open('/proc/uptime', 'r').readlines():
            l = line.split()
            if len(l) < 2: continue
            return float(l[0])
    except:
        for line in dopen('/proc/stat').readlines():
            l = line.split()
            if len(l) < 2: continue
            if l[0] == 'btime':
                return time.time() - int(l[1])

def dopen(filename):
    "Open a file for reuse, if already opened, return file descriptor"
    global fds
    if not os.path.exists(filename):
        raise Exception('File %s does not exist' % filename)
    if 'fds' not in globals():
        fds = {}
    if filename in fds:
        fds[filename].seek(0)
    else:
        fds[filename] = open(filename, 'r')
    return fds[filename]

def dclose(filename):
    "Close an open file and remove file descriptor from list"
    global fds
    if not 'fds' in globals(): fds = {}
    if filename in fds:
        fds[filename].close()
        del(fds[filename])

def dpopen(cmd):
    "Open a pipe for reuse, if already opened, return pipes"
    global pipes, select
    import select

    if 'pipes' not in globals(): pipes = {}

    if cmd not in pipes:
        try:
            import subprocess
            p = subprocess.Popen(cmd, shell=True, bufsize=0, close_fds=True,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            pipes[cmd] = (p.stdin, p.stdout, p.stderr)
        except ImportError:
            msg = 'Error opening cmd "%s"' % (cmd)
            raise Exception(msg)

    return pipes[cmd]

def readpipe(fileobj, tmout = 0.001):
    "Read available data from pipe in a non-blocking fashion"
    ret = ''
    while not select.select([fileobj.fileno()], [], [], tmout)[0]:
        pass
    while select.select([fileobj.fileno()], [], [], tmout)[0]:
        ret = ret + fileobj.read(1)
    return ret.split('\n')

def greppipe(fileobj, str, tmout = 0.001):
    "Grep available data from pipe in a non-blocking fashion"
    ret = ''
    while not select.select([fileobj.fileno()], [], [], tmout)[0]:
        pass
    while select.select([fileobj.fileno()], [], [], tmout)[0]:
        character = fileobj.read(1)
        if character != '\n':
            ret = ret + character
        elif ret.startswith(str):
            return ret
        else:
            ret = ''
    if op.debug:
        raise Exception('Nothing found during greppipe data collection')
    return None

def matchpipe(fileobj, string, tmout = 0.001):
    "Match available data from pipe in a non-blocking fashion"
    ret = ''
    regexp = re.compile(string)
    while not select.select([fileobj.fileno()], [], [], tmout)[0]:
        pass
    while select.select([fileobj.fileno()], [], [], tmout)[0]:
        character = fileobj.read(1)
        if character != '\n':
            ret = ret + character
        elif regexp.match(ret):
            return ret
        else:
            ret = ''
    if op.debug:
        raise Exception('Nothing found during matchpipe data collection')
    return None

# Test if a command is capable of being run
def cmd_test(cmd):
    pipes = os.popen3(cmd, 't', 0)
    for line in pipes[2].readlines():
        raise Exception(line.strip())

# Read command output line by line
def cmd_readlines(cmd):
    pipes = os.popen3(cmd, 't', 0)
    for line in pipes[1].readlines():
       yield line

# Read command output column by column
def cmd_splitlines(cmd, sep=None):
    pipes = os.popen3(cmd, 't', 0)
    for line in pipes[1].readlines():
       yield line.split(sep)

def proc_readlines(filename):
    "Return the lines of a file, one by one"
#    for line in open(filename).readlines():
#       yield line

    ### Implemented linecache (for top-plugins)
    i = 1
    while True:
        line = linecache.getline(filename, i);
        if not line: break
        yield line
        i += 1

def proc_splitlines(filename, sep=None):
    "Return the splitted lines of a file, one by one"
#    for line in open(filename).readlines():
#       yield line.split(sep)

    ### Implemented linecache (for top-plugins)
    i = 1
    while True:
        line = linecache.getline(filename, i);
        if not line: break
        yield line.split(sep)
        i += 1

def proc_readline(filename):
    "Return the first line of a file"
#    return open(filename).read()
    return linecache.getline(filename, 1)

def proc_splitline(filename, sep=None):
    "Return the first line of a file splitted"
#    return open(filename).read().split(sep)
    return linecache.getline(filename, 1).split(sep)

### FIXME: Should we cache this within every step ?
def proc_pidlist():
    "Return a list of process IDs"
    dool_pid = str(os.getpid())
    for pid in os.listdir('/proc/'):
        try:
            ### Is it a pid ?
            int(pid)

            ### Filter out dool
            if pid == dool_pid: continue

            yield pid

        except ValueError:
            continue

# Get a single SNMP OID
def snmpget(server, community, oid):
    errorIndication, errorStatus, errorIndex, varBinds = cmdgen.CommandGenerator().getCmd(
        cmdgen.CommunityData('test-agent', community, 0),
        cmdgen.UdpTransportTarget((server, 161)),
        oid
    )
#    print('%s -> ind: %s, stat: %s, idx: %s' % (oid, errorIndication, errorStatus, errorIndex))
    for x in varBinds:
        return str(x[1])

# Do a full SNMP walk
def snmpwalk(server, community, oid):
    ret = []
    errorIndication, errorStatus, errorIndex, varBindTable = cmdgen.CommandGenerator().nextCmd(
        cmdgen.CommunityData('test-agent', community, 0),
        cmdgen.UdpTransportTarget((server, 161)),
        oid
    )
#    print('%s -> ind: %s, stat: %s, idx: %s' % (oid, errorIndication, errorStatus, errorIndex))
    for x in varBindTable:
        for y in x:
            ret.append(str(y[1]))
    return ret

def dchg(var, width, base):
    "Convert decimal to string given base and length"
    c = 0
    while True:
        if math.isinf(var):
            ret = 'Inf'
            break
        ret = str(int(round(var)))
        if len(ret) <= width:
            break
        var = var / base
        c = c + 1
    else:
        c = -1
    return ret, c

def fchg(var, width, base):
    "Convert float to string given scale and length"
    c = 0
    while True:
        if var == 0:
            ret = str('0')
            break
#       ret = repr(round(var))
#       ret = repr(int(round(var, maxlen)))
        ret = str(int(round(var, width)))
        if len(ret) <= width:
            i = width - len(ret) - 1
            while i > 0:
                ret = ('%%.%df' % i) % var
                if len(ret) <= width and ret != str(int(round(var, width))):
                    break
                i = i - 1
            else:
                ret = str(int(round(var)))
            break
        var = var / base
        c = c + 1
    else:
        c = -1
    return ret, c

def tchg(var, width):
    "Convert time string to given length"
    ret = '%2dh%02d' % (var / 60, var % 60)
    if len(ret) > width:
        ret = '%2dh' % (var / 60)
        if len(ret) > width:
            ret = '%2dd' % (var / 60 / 24)
            if len(ret) > width:
                ret = '%2dw' % (var / 60 / 24 / 7)
    return ret

# Global/static variables to speed up repeated calls to devel_log()
DEBUG_LAST = 0
DEBUG_FH   = 0

# Write some debug data to a log if we enabled --devel
def devel_log(msg):
    global DEBUG_LAST, DEBUG_FH

    # If we didn't enable `--devel` on the CLI we don't do anything
    if not op.devel:
        return -1

    # If the filehandle isn't already open, we open it
    if not DEBUG_FH:
        log_file = "/tmp/dool-devel.log"
        print("Writing devel log: '%s'" % log_file)
        DEBUG_FH = open(log_file, "w", 1)

    xtime    = time.time()
    time_fmt = os.getenv('DOOL_TIMEFMT') or '%b-%d %H:%M:%S'
    time_str = time.strftime(time_fmt, time.localtime())

    # Append MS the ghetto way
    time_ms  = "." + str(round(xtime * 1000 % 1000))
    time_str += time_ms

    # Calculate the ms since the previous call
    if DEBUG_LAST > 0:
       time_diff = (xtime - DEBUG_LAST) * 1000 # Milliseconds
    else:
       time_diff = 0

    log_line = "%s %4d ms: %s\n" % (time_str, time_diff, msg.strip())
    DEBUG_FH.write(log_line);

    # Save the time of this call for the next call
    DEBUG_LAST = xtime

def cprintlist(varlist, ctype, width, scale):
    "Return all columns color printed"
    ret = sep = ''
    for var in varlist:
        ret = ret + sep + cprint(var, ctype, width, scale)
        sep = char['space']
    return ret

# var   : data to output
# ctypes: f = float, s = string, b = bit/bytes, d = decimal, t = time, p = percent
# width : width in chars of the column
def cprint(var, ctype = 'f', width = 4, scale = 1000):
    "Color print one column"

    base = 1000
    if scale == 1024:
        base = 1024

    ### Use units when base is exact 1000 or 1024
    unit = False
    if scale in (1000, 1024) and width >= len(str(base)):
        unit = True
        width = width - 1

    ### If this is a negative value, return a dash
    if ctype != 's' and var < 0:
        if unit:
            return theme['error'] + '-'.rjust(width) + char['space'] + theme['default']
        else:
            return theme['error'] + '-'.rjust(width) + theme['default']

    # There is a big discussion of bits vs bytes and the various unit lables
    # here: https://github.com/scottchiefbaker/dool/pull/34
    # which may help explain why these are inconsistent case
    if base != 1024:
        # Miscellaneous value using base of 1000 (1, kilo-, mega-, giga-, ...)
        units = (char['space'], 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    elif op.bits and ctype in ('b', ):
        # Bit value using base of 1000 (bit, kilobit, megabit, gigabit, ...)
        units = ('b', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
        base = scale = 1000
        var = var * 8.0
    else:
        # Byte value using base of 1024 (byte, kibibyte, mebibyte, gibibyte, ...)
        units = ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')

    # Interim update is faded out a bit
    if step == op.delay:
        colors = theme['colors_lo']
        ctext  = theme['text_lo']
        cunit  = theme['unit_lo']
        cdone  = theme['done_lo']
    # Real update is bright color
    else:
        colors = theme['colors_hi']
        ctext  = theme['text_hi']
        cunit  = theme['unit_hi']
        cdone  = theme['done_hi']

    ### Convert value to string given base and field-length
    if op.integer and ctype in ('b', 'd', 'p', 'f'):
        ret, c = dchg(var, width, base)
    elif op.float and ctype in ('b', 'd', 'p', 'f'):
        ret, c = fchg(var, width, base)
    elif ctype in ('b', 'd', 'p'):
        ret, c = dchg(var, width, base)
    elif ctype in ('f',):
        ret, c = fchg(var, width, base)
    elif ctype in ('s',):
        ret, c = str(var), ctext
    elif ctype in ('t',):
        ret, c = tchg(var, width), ctext
    else:
        raise Exception('Type %s not known to dool.' % ctype)

    ### Set the counter color
    if ret == '0':
        color = cunit
    elif scale <= 0:
        color = ctext
    elif ctype in ('p') and round(var) >= 100.0:
        color = cdone
#    elif type in ('p'):
#        color = colors[int(round(var)/scale)%len(colors)]
    elif scale not in (1000, 1024):
        color = colors[int(var/scale)%len(colors)]
    elif ctype in ('b', 'd', 'f'):
        color = colors[c%len(colors)]
    else:
        color = ctext

    ### Justify value to left if string
    if ctype in ('s',):
        ret = color + ret.ljust(width)
    else:
        ret = color + ret.rjust(width)

    ### Add unit to output
    if unit:
        try:
            if c != -1 and round(var) != 0:
                ret += cunit + units[c]
            else:
                ret += char['space']
        except OverflowError:
            ret += char['space']

    return ret

def header(totlist, vislist):
    "Return the header for a set of module counters"
    line = ''

    # If it's the FIRST header we have outputted
    first_header = (update == 0)

    ### Process title
    for o in vislist:
        line += o.title()
        if o is not vislist[-1]:

            # First header gets T
            if (first_header):
                sep = char['title_sep_first']
            # All other headers get +
            else:
                sep = char['title_sep']

            line += theme['frame'] + sep
        elif totlist != vislist:
            line += theme['title'] + char['gt']

    line += '\n'

    ### Process subtitle
    for o in vislist:
        line += o.subtitle()
        if o is not vislist[-1]:
            line += theme['frame'] + char['pipe']
        elif totlist != vislist:
            line += theme['title'] + char['gt']

    return line + '\n'

def csv_header(totlist):
    "Return the CVS header for a set of module counters"
    line = ''
    ### Process title
    for o in totlist:
        line = line + o.csvtitle()
        if o is not totlist[-1]:
            line = line + char['sep']
    line += '\n'
    ### Process subtitle
    for o in totlist:
        line = line + o.csvsubtitle()
        if o is not totlist[-1]:
            line = line + char['sep']
    return line + '\n'

def info(level, msg):
    "Output info message"
#   if level <= op.verbose:
    print(msg, file=sys.stderr)

def die(ret, msg):
    "Print error and exit with errorcode"
    print(msg, file=sys.stderr)
    exit(ret)

# Quit in a clean way
def exit(ret):
    sys.stdout.write(ansi['reset'])
    sys.stdout.flush()

    # Remove any pidfiles
    if op.pidfile and os.path.exists(op.pidfile):
        os.remove(op.pidfile)

    if op.profile and os.path.exists(op.profile):
        rows, cols = get_term_size()
        import pstats

        p = pstats.Stats(op.profile)
        p.sort_stats('cumulative').print_stats(rows - 13)
    elif op.profile:
        print('No profiling data was found, maybe profiler was interrupted ?', file=sys.stderr)

    sys.exit(ret)

def init_term():
    "Initialise terminal"
    global termsize

    ### Unbuffered sys.stdout
#    sys.stdout = os.fdopen(1, 'w', 0)

    termsize = None, 0
    try:
        global fcntl, struct, termios
        import fcntl, struct, termios
        termios.TIOCGWINSZ
    except:
        try:
            curses.setupterm()
            curses.tigetnum('lines'), curses.tigetnum('cols')
        except:
            pass
        else:
            termsize = None, 2
    else:
        termsize = None, 1

def get_term_size():
    "Return the dynamic terminal geometry"
    global termsize

#    if not termsize[0] and not termsize[1]:
    if not termsize[0]:
        try:
            if termsize[1] == 1:
                s = struct.pack('HHHH', 0, 0, 0, 0)
                x = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, s)
                return struct.unpack('HHHH', x)[:2]
            elif termsize[1] == 2:
                curses.setupterm()
                return curses.tigetnum('lines'), curses.tigetnum('cols')
            else:
                termsize = (int(os.environ['LINES']), int(os.environ['COLUMNS']))
        except:
            termsize = 25, 80
    return termsize

def get_term_color():
    "Return whether the system can use colors or not"
    if sys.stdout.isatty():
        try:
            import curses
            curses.setupterm()
            colors = curses.tigetnum('colors')
            if colors < 0:
                return False
        except ImportError:
            print('Color support is disabled as python-curses is not installed.', file=sys.stderr)
            return False
        except:
            print('Color support is disabled as curses does not find terminal "%s".' % os.getenv('TERM'), file=sys.stderr)
            return False
        if colors == 256:
            return colors
        return 16
    return False

### We only want to filter out paths, not ksoftirqd/1
def basename(name):
    "Perform basename on paths only"
    if name[0] in ('/', '.'):
        return os.path.basename(name)
    return name

def getnamebypid(pid, name):
    "Return the name of a process by taking best guesses and exclusion"
    ret = None

    try:
        #### man proc tells me there should be nulls in here, but sometimes it seems like spaces (esp google chrome)
        # cmdline = open('/proc/%s/cmdline' % pid).read().split(('\0', ' '))

        cmdline = linecache.getline('/proc/%s/cmdline' % pid, 1).split('\0')
        ret     = basename(cmdline[0])

        # Strip off any scripting language name
        if ret in ('bash', 'csh', 'ksh', 'perl', 'python', 'ruby', 'sh'):
            ret = basename(cmdline[1])
        if ret.startswith('-'):
            ret = basename(cmdline[-2])
            if ret.startswith('-'): raise

        is_vm = "kvm" in cmdline[0] or "qemu" in cmdline[0]
        if is_vm:
            # Proxmox    : /usr/bin/kvm -id 210 -name TestDHCPServer,debug-threads=on ...
            # LibVirt+KVM: /usr/libexec/qemu-kvm -name guest=test.ewheeler.net,debug-threads=on ...

            cmd_str = " ".join(cmdline)
            xmatch  = re.search("-name (.+?),", cmd_str)

            if xmatch:
                ret = xmatch.group(1)
                ret = ret.replace("guest=", "") # Hack to remove guest= for LibVirt+KVM

        if not ret: raise
    except:
        ret = basename(name)

    return ret

def getcpunr():
    "Return the number of CPUs in the system"

    # POSIX
    try:
        return os.sysconf("SC_NPROCESSORS_ONLN")
    except ValueError:
        pass

    # Python 2.6+
    try:
        import multiprocessing
        return multiprocessing.cpu_count()
    except (ImportError, NotImplementedError):
        pass

    # Fallback 1
    try:
        cpunr = open('/proc/cpuinfo', 'r').read().count('processor\t:')
        if cpunr > 0:
            return cpunr
    except IOError:
        pass

    # Fallback 2
    try:
        search = re.compile(r'^cpu\d+')
        cpunr = 0
        for line in dopen('/proc/stat').readlines():
            if search.match(line):
                cpunr += 1
        if cpunr > 0:
            return cpunr
    except:
        raise Exception("Problem finding number of CPUs in system.")

# Find all the block devices in /sys/block
def blockdevices():
    ### We have to replace '!' by '/' to support cciss!c0d0 type devices :-/
    return [os.path.basename(filename).replace('!', '/') for filename in glob.glob('/sys/block/*')]

### FIXME: Add scsi support too and improve
def sysfs_dev(device):
    "Convert sysfs device names into device names"
    m = re.match(r'ide/host(\d)/bus(\d)/target(\d)/lun(\d)/disc', device)
    if m:
        l = m.groups()
        # ide/host0/bus0/target0/lun0/disc -> 0 -> hda
        # ide/host0/bus1/target0/lun0/disc -> 2 -> hdc
        nr = int(l[1]) * 2 + int(l[3])
        return 'hd' + chr(ord('a') + nr)
    m = re.match(r'cciss/(c\dd\d)', device)
    if m:
        l = m.groups()
        return l[0]
    m = re.match('placeholder', device)
    if m:
        return 'sdX'
    return device

def dev(maj, min):
    "Convert major/minor pairs into device names"
    ram   = [1, ]
    ide   = [3, 22, 33, 34, 56, 57, 88, 89, 90, 91]
    loop  = [7, ]
    scsi  = [8, 65, 66, 67, 68, 69, 70, 71, 128, 129, 130, 131, 132, 133, 134, 135]
    md    = [9, ]
    ida   = [72, 73, 74, 75, 76, 77, 78, 79]
    ubd   = [98,]
    cciss = [104,]
    dm    = [253,]
    if maj in scsi:
        disc = chr(ord('a') + scsi.index(maj) * 16 + min / 16)
        part = min % 16
        if not part: return 'sd%s' % disc
        return 'sd%s%d' % (disc, part)
    elif maj in ide:
        disc = chr(ord('a') + ide.index(maj) * 2 + min / 64)
        part = min % 64
        if not part: return 'hd%s' % disc
        return 'hd%s%d' % (disc, part)
    elif maj in dm:
        return 'dm-%d' % min
    elif maj in md:
        return 'md%d' % min
    elif maj in loop:
        return 'loop%d' % min
    elif maj in ram:
        return 'ram%d' % min
    elif maj in cciss:
        disc = cciss.index(maj) * 16 + min / 16
        part = min % 16
        if not part: return 'c0d%d' % disc
        return 'c0d%dp%d' % (disc, part)
    elif maj in ida:
        cont = ida.index(maj)
        disc = min / 16
        part = min % 16
        if not part: return 'ida%d-%d' % (cont, disc)
        return 'ida%d-%d-%d' % (cont, disc, part)
    elif maj in ubd:
        disc = ubd.index(maj) * 16 + min / 16
        part = min % 16
        if not part: return 'ubd%d' % disc
        return 'ubd%d-%d' % (disc, part)
    else:
        return 'dev%d-%d' % (maj, min)

# Gather all the plugins from their assorted directory locations
def get_plugin_details():
    # These are the built-in plugins
    remod   = re.compile('dool_(.+)$')
    ret     = {}

    for function_name in globals():
        if function_name.startswith('dool_'):
            plugin_name = remod.match(function_name).group(1)
            name        = plugin_name.replace('_', '-')

            # If the function name is dool__ that means it needs params
            needs_params = function_name.startswith("dool__")

            obj           = {}
            obj['file']   = function_name
            obj['type']   = 'builtin'
            obj['params'] = needs_params

            ret[name] = obj

    # The external `.py` plugins
    remod     = re.compile('.+/dool__?(.+).py$')
    external  = []
    for path in pluginpath:
        for filename in glob.glob(path + '/dool_*.py'):
            plugin_name = remod.match(filename).group(1)
            name        = plugin_name.replace('_', '-')

            ret[name] = filename

            # If the filename has 'dool__' in it that means it needs params
            basename     = os.path.basename(filename)
            needs_params = basename.startswith("dool__")

            obj           = {}
            obj['file']   = filename
            obj['type']   = 'external'
            obj['params'] = needs_params

            ret[name] = obj

    return ret

# For the --help print out a list of all the plugins and what/where they are
def show_plugins():
    plugin_details = get_plugin_details()
    plugin_names   = list(plugin_details.keys())
    plugin_names.sort()

    builtin  = []
    external = []

    for name in plugin_names:
        ptype    = plugin_details[name]['type']
        params   = plugin_details[name]['params']
        filename = plugin_details[name]['file']
        path     = os.path.dirname(filename)

        if ptype == 'builtin':
            builtin.append(name)
        else:
            external.append(name)

    # Print the builtin plugins
    rows, cols = get_term_size()
    print('internal:\n\t', end='')
    cols2 = cols - 8

    for mod in builtin:
        cols2 = cols2 - len(mod) - 2
        if cols2 <= 0:
            print('\n\t', end='')
            cols2 = cols - len(mod) - 10
        if mod != builtin[-1]:
            print(mod, end=',')

    print(mod)

    ######################################################################

    # Print the external plugins sorted by path
    for path in pluginpath:
        plugins = []
        for name in external:
            pfile = plugin_details[name]['file']
            pdir  = os.path.dirname(pfile) + "/"

            #print("%s = %s" % (pdir,path))

            # If this plugin is in the dir we're looking for we put it
            # in this grouping
            if (pdir == path):
                plugins.append(name)

        if not plugins: continue
        plugins.sort()

        cols2 = cols - 8
        print('%s:' % os.path.abspath(path), end='\n\t')

        for mod in plugins:
            cols2 = cols2 - len(mod) - 2
            if cols2 <= 0:
                print(end='\n\t')
                cols2 = cols - len(mod) - 10
            if mod != plugins[-1]:
                print(mod, end=',')

        print(mod)

# The main ingress point of the whole thing
def main():
    "Initialization of the program, terminal, internal structures"
    global cpunr, hz, maxint, ownpid, pagesize
    global ansi, theme, outputfile
    global totlist, inittime
    global update, missed

    devel_log("Dool startup")

    # Handle signals like CTRL+C
    init_signal_handling()

    cpunr  = getcpunr()
    hz     = os.sysconf('SC_CLK_TCK')
    maxint = float("inf")

    ownpid   = str(os.getpid())
    pagesize = resource.getpagesize()
    interval = 1
    user     = getpass.getuser()
    hostname = os.uname()[1]

    ### Write term-title
    if sys.stdout.isatty():
        shell = os.getenv('XTERM_SHELL')
        term = os.getenv('TERM')
        if shell == '/bin/bash' and term and re.compile('(screen*|xterm*)').match(term):
            sys.stdout.write('\033]0;(%s@%s) %s %s\007' % (user, hostname.split('.')[0], os.path.basename(sys.argv[0]), ' '.join(op.args)))

    ### Check terminal capabilities
    if op.color == None:
        op.color = get_term_color()

    ### If we're *not* doing ASCII then we are using the
    ### Unicode chars so we overwrite the ASCII ones
    if not op.use_ascii:
        for key in char_box_draw:
            char[key] = char_box_draw[key]

    ### Prepare CSV output file (unbuffered)
    if op.output:
        if not os.path.exists(op.output):
            outputfile = open(op.output, 'w')
            outputfile.write('"dool %s CSV output"\n' % __version__)
            header = ('"Author:","Scott Baker"','','','','"URL:"','"https://github.com/scottchiefbaker/dool/"\n')
            outputfile.write(char['sep'].join(header))
        else:
            outputfile = open(op.output, 'a')
            outputfile.write('\n\n')

        header = ('"Host:"','"%s"' % hostname,'','','','"User:"','"%s"\n' % user)
        outputfile.write(char['sep'].join(header))

        run_cmd = " ".join(sys.argv)

        header = ('"Cmdline:"','"' + run_cmd + '"','','','','"Date:"','"%s"\n' % time.strftime('%d %b %Y %H:%M:%S %Z', time.localtime()))
        outputfile.write(char['sep'].join(header))

    ### Create pidfile
    if op.pidfile:
        try:
            pidfile = open(op.pidfile, 'w')
            pidfile.write(str(os.getpid()))
            pidfile.close()
        except Exception as e:
            print('Failed to create pidfile %s: %s' % (op.pidfile, e), file=sys.stderr)
            op.pidfile = False

    ### Empty ansi and theme database if no colors are requested
    if not op.color:

        for key in color:
            color[key] = ''

        for key in theme:
            theme[key] = ''

        # With this enabled --nocolor with a delay doesn't display correctly so
        # I've disabled it for now
        #for key in ansi:
            #ansi[key] = ''

        theme['colors_hi'] = (ansi['default'],)
        theme['colors_lo'] = (ansi['default'],)

    ### Disable line-wrapping (does not work ?)
    sys.stdout.write(ansi['nolinewrap'])

    if not op.update:
        interval = op.delay

    ### Build list of requested plugins
    linewidth = 0
    totlist   = []

    for plugin in op.plugins:
        pluginfile = op.plugin_details[plugin]['file']

        try:
            if pluginfile not in globals():
                scope = {}
                exec(open(pluginfile).read(), globals(), scope)
                plug = scope['dool_plugin']()
                plug.filename = pluginfile
                plug.check()
                plug.prepare()
            else:
                plug = globals()[pluginfile]()
                plug.check()
                plug.prepare()

        except Exception as e:
            if plugin == op.plugins[-1]:
                print('Module %s failed to load. (%s)' % (pluginfile, e), file=sys.stderr)
            elif op.debug:
                print('Module %s failed to load, trying another. (%s)' % (pluginfile, e), file=sys.stderr)
            if op.debug >= 3:
                raise

            continue

        except:
            print('Module %s caused unknown exception' % pluginfile, file=sys.stderr)

        linewidth = linewidth + plug.statwidth() + 1
        totlist.append(plug)

    if not totlist:
        die(8, 'None of the stats you selected are available.')

    if op.output:
        outputfile.write(csv_header(totlist))

    scheduler = sched.scheduler(time.time, time.sleep)
    inittime  = time.time()

    update = 0
    missed = 0

    # This the main loop that does all the output. It has two options:
    # Loop X number of times where X is (delay * count) and stop
    # or
    # loop forever (op.count = -1 is how we say "forever")
    while (update <= (op.delay * (op.count - 1))) or (op.count == -1):
        # We are scheduling to run perform(update) every 1 second
        scheduler.enterabs(inittime + update, 1, perform, (update,))
        scheduler.run()
        sys.stdout.flush()
        # The time the next update will run
        update = update + interval
        linecache.clearcache()
        devel_log("Loop #%d" % update)

    print()

def perform(update):
        "Inner loop that calculates counters and constructs output"
        global totlist, oldvislist, vislist, showheader, rows, cols
        global elapsed, totaltime, starttime
        global loop, step, missed

        starttime = time.time()

        # The number of the current loop (not counting subdates)
        loop = int((update - 1 + op.delay) / op.delay)
        # The step (subupdate) number inside of the current loop
        step = ((update - 1) % op.delay) + 1

        ### Get current time (may be different from schedule) for debugging
        if not op.debug:
            curwidth = 0
        else:
            if step == 1 or loop == 0:
                totaltime = 0
            curwidth = 8

        ### FIXME: This is temporary functionality, we should do this better
        ### If it takes longer than 500ms, than warn !
        if loop != 0 and starttime - inittime - update > 1:
            missed = missed + 1
            return 0

        ### Initialise certain variables
        if loop == 0:
            elapsed = ticks()
            rows, cols = 0, 0
            vislist = []
            oldvislist = []
            showheader = True
        else:
            elapsed = step

        ### FIXME: Make this part smarter
        if sys.stdout.isatty():
            oldcols = cols
            rows, cols = get_term_size()

            ### Trim object list to what is visible on screen
            if oldcols != cols:
                vislist = []
                for o in totlist:
                    newwidth = curwidth + o.statwidth() + 1
                    if newwidth <= cols or ( vislist == totlist[:-1] and newwidth < cols ):
                        vislist.append(o)
                        curwidth = newwidth

            ### Check when to display the header
            if op.header and rows >= 6:
                if oldvislist != vislist:
                    showheader = True
                elif not op.update and loop % (rows - 2) == 0:
                    showheader = True
                elif op.update and step == 1 and loop % (rows - 1) == 0:
                    showheader = True

            oldvislist = vislist
        else:
            vislist = totlist

        # If we're on the last step of the loop it's definitive and is colored differently
        if step == op.delay:
            theme['default'] = ansi['reset']
        # It's a step/subupdate
        else:
            theme['default'] = theme['text_lo']

        ### The first step is to show the definitive line if necessary
        newline = ''
        if op.update:
            ### If we are starting a whole new line we \n and reset
            if step == 1 and update != 0:
                newline = '\n' + ansi['reset'] + ansi['clearline']
            ### If we're in a delay we just go to column 0 and overwrite what's there
            elif loop != 0:
                newline = ansi['clearline'] + ansi['column_zero'];
        elif not op.update:
            newline = "\n"

        ### Display header
        if showheader:
            if loop == 0 and totlist != vislist:
                print('Terminal width too small, trimming output.', file=sys.stderr)
            showheader = False
            sys.stdout.write(newline)
            newline = header(totlist, vislist)

        ### Calculate all objects (visible, invisible)
        line = newline
        oline = ''

        # Loop through each param section and build the output string
        for o in totlist:
            o.extract()

            if o in vislist:
                line = line + o.show() + o.showend(totlist, vislist)

            # Prep the line for the CSV file
            if op.output and step == op.delay:
                oline = oline + o.showcsv() + o.showcsvend(totlist, vislist)

        ### Put the output in the csv file
        if op.output and step == op.delay:
            outputfile.write(oline + '\n')
            outputfile.flush()

        ### Print stats to display
        if op.display:
            sys.stdout.write(line + theme['input'])

        ### Print debugging output
        if op.debug:
            totaltime = totaltime + (time.time() - starttime) * 1000.0
            if loop == 0:
                totaltime = totaltime * step
            if op.debug == 1:
                sys.stdout.write('%s%6.2fms%s' % (theme['roundtrip'], totaltime / step, theme['input']))
            elif op.debug == 2:
                sys.stdout.write('%s%6.2f %s%d:%d%s' % (theme['roundtrip'], totaltime / step, theme['debug'], loop, step, theme['input']))
            elif op.debug > 2:
                sys.stdout.write('%s%6.2f %s%d:%d:%d%s' % (theme['roundtrip'], totaltime / step, theme['debug'], loop, step, update, theme['input']))

        if missed > 0:
            # sys.stdout.write(' '+theme['error']+'= warn =')
            sys.stdout.write(' ' + theme['error'] + 'missed ' + str(missed+1) + ' ticks' + theme['input'])
            missed = 0

# Get an item from a list, or a default value if the array isn't big enough (null coalesce)
def list_item_default(mylist, num, default):
    if num > len(mylist) - 1:
        return default
    else:
        return mylist[num]

# Krumo style debug printing
def k(obj, prefix = "DEBUG"):
    import inspect

    # https://stackoverflow.com/questions/6810999/how-to-determine-file-function-and-line-number
    x    = inspect.stack()[1]
    info = inspect.getframeinfo(x[0])

    line_str = "#" + str(info.lineno)
    myfile   = os.path.basename(__file__)

    sys.stdout.write("%s %s @ %s: " % (prefix, text_color(228, myfile), text_color(117,line_str)))
    print(obj)

# Krumo print and die
def kd(obj):
    k(obj, "DIED")
    sys.exit(99)

# Read in a full file (or optional only X bytes)
def file_slurp(filename, size = -1):
    ret = ""

    try:
        fd  = open(filename)
        ret = fd.read(size)
    finally:
        fd.close()

    return ret

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
def dev_short_name(xinput, xlen = 4):
    # Too short just return the input
    if len(xinput) <= xlen:
        ret = xinput
    # Break out the parts and build a new string
    else:
        # This gets all the a-z chars up to the first digit
        # Then it gets any sequential digits followed by a
        # non-digit separator, and any remaining digits
        x = re.match(r"([a-zA-Z]+).*?(\d+)(.*\D.*?(\d+))?", xinput)

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

def get_dev_name(disk):
    "Strip /dev/ and convert symbolic link"

    ret = ''

    # If it starts with '/dev/'
    if disk[:5] == '/dev/':
        # file or symlink
        if os.path.exists(disk):
            # e.g. /dev/disk/by-uuid/15e40cc5-85de-40ea-b8fb-cb3a2eaf872
            if os.path.islink(disk):
                target = os.readlink(disk)

                # convert relative pathname to absolute
                if target[0] != '/':
                    target = os.path.join(os.path.dirname(disk), target)
                    target = os.path.normpath(target)

                    print('dool: symlink %s -> %s' % (disk, target))

                disk = target

            # trim leading /dev/
            ret = disk[5:]
        else:
            print('dool: %s does not exist' % disk)
    else:
        ret = disk

    return ret

# Calculate the differences of two arrays
def array_diff(first, second):
    second = set(second)
    return [item for item in first if item not in second]

# Start performance profiling
def start_profiling():
    import profile

    # Remove any previous profile data
    if os.path.exists(op.profile):
        os.remove(op.profile)

    profile.run('main()', op.profile)

# Main ingress point
def __main():
    global op
    global theme

    try:
        init_term()

        # We use $DOOL_OPTS env variable and the CLI params to get all requested options
        env_opts = os.getenv('DOOL_OPTS','').split()
        cli_opts = sys.argv[1:]
        op       = Options(env_opts + cli_opts)

        # Pick color depth theme we're going to use
        theme = set_theme()

        # If we're doing performance profiling
        if op.profile:
            start_profiling()
        else:
            main()

    # This should handle catching CTRL + C and finalizing the output
    except KeyboardInterrupt as e:
        if op.update:
            sys.stdout.write('\n')

    # Exit cleanly
    exit(0)

# Standard Python entry point
if __name__ == '__main__':
    __main()

# vim: tabstop=4 shiftwidth=4 expandtab autoindent softtabstop=4
