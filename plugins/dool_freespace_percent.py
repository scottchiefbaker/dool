### Based on dool_freespace.py by Dag Wieers <dag$wieers,com>
# DOOL_OPTS: PARAM_REQUIRED

# Syntax:
#    list all mount points in /etc/mtab:
#       dool --freespace-percent all
#
#    list specific mount points:
#       dool --freespace-percent /mnt/disk1,/mnt/vault

class dool_plugin(dool):
    """
    Amount of used and free space per mountpoint, as a percentage.
    """

    def __init__(self):
        self.nick    = ('used', 'free')
        self.type    = 'p'
        self.scale   = 0
        # num_fmt plus the '%' suffix added in show() must fit in width
        self.width   = 6
        self.num_fmt = "%5.1f"
        self.open('/etc/mtab')
        self.cols    = 2

    def vars(self):
        ret = []

        # Get the mountpoint string from the optional param at the CLI
        # or fallback to the environment variable.
        # If there is NO string we default to showing all mount points
        global op
        param = op.plugin_params['freespace-percent']

        # Sometimes the next param after --freespace-percent is NOT a mountpoint
        # i.e. dool --freespace-percent 5
        # This will raise an Exception if the param doesn't look like a mountpoint
        if (param != "all" and not param.startswith("/")):
            raise Exception("Freespace-percent requires a comma separated list of mount points or \"all\"")

        if (param != "all" and len(param) > 0):
            mp = param.split(',')

            # Remove any trailing `/` from any paths
            mp = self.clean_mountpoints(mp)
        elif (param == "all"):
            mp = []

        include_fs_types = (
            'ext2', 'ext3', 'ext4', 'btrfs', 'xfs', 'zfs'
        )

        for l in self.splitlines():
            if len(l) < 6: continue

            device      = l[0]
            mount_point = l[1]
            fs_type     = l[2]

            # If there is an array of mount points (whitelist) and this
            # mount point is *NOT* in that list, skip it
            if (mp):
                if (not mount_point in mp):
                    continue
            # If there is NOT an array of mount points check it against a
            # whitelisted array of fs_types
            elif (fs_type not in include_fs_types):
                continue

            is_readable = os.access(mount_point, os.R_OK)

            if (not is_readable):
                continue

            res = os.statvfs(mount_point)

            if res[0] == 0: continue ### Skip zero block filesystems
            ret.append(mount_point)

        # Make sure we found all the requested mount points
        missing_mps = array_diff(mp, ret)

        for item in missing_mps:
            msg = text_color(214, "Warning: unable to find mount point %s in /etc/mtab" % (item));
            print(msg)

        return ret

    def name(self):
        return ['/' + os.path.basename(name) for name in self.vars]

    def extract(self):
        self.val['total'] = (0, 0)
        for name in self.vars:
            res = os.statvfs(name)

            f_blocks = float(res.f_blocks)
            f_bavail = float(res.f_bavail)
            f_frsize = int(res.f_frsize)

            # Keep a running total in bytes, like dool_freespace does
            used_bytes = (f_blocks - f_bavail) * f_frsize
            free_bytes = f_bavail * f_frsize
            self.val['total'] = (self.val['total'][0] + used_bytes, self.val['total'][1] + free_bytes)

            # dool counts the blocks reserved for root as used, so the
            # used and free percentages add up to exactly 100%
            if (f_blocks > 0):
                used = ((f_blocks - f_bavail) / f_blocks) * 100
                free = (f_bavail / f_blocks) * 100
            else:
                # Don't divide by zero on filesystems with no blocks
                used = free = 0.0

            self.val[name] = (used, free)

    def show(self):
        # cprint()'s 'p' type rounds to an integer (unless --float is used),
        # so format each value ourselves and let cprint() render it as a
        # string. This always gives one digit after the decimal point, with
        # a '%' suffix so the numbers read as percentages.
        line = ''
        if hasattr(self, 'output'):
            return cprint(self.output, self.type, self.width, self.scale)

        for i, name in enumerate(self.vars):
            vals = [(self.num_fmt % val) + '%' for val in self.val[name]]
            line = line + cprintlist(vals, 's', self.width, self.scale)
            if i + 1 != len(self.vars):
                line = line + theme['subframe'] + char['colon'] + ansi['reset']

        return line

    def showcsv(self):
        # The base class renders floats with three digits ("%.3f"), emit the
        # same one-decimal format that is shown on screen instead, without
        # the '%' suffix so the cells stay numeric like all other plugins
        line = ''
        for i, name in enumerate(self.vars):
            for j, val in enumerate(self.val[name]):
                line = line + (self.num_fmt % val).strip()
                if j + 1 != len(self.val[name]):
                    line = line + char['sep']
            if i + 1 != len(self.vars):
                line = line + char['sep']

        return line

    def clean_mountpoints(self, items):
        ret = []

        # Remove any trailing '/' from mount points
        for x in items:
            if (x != "/"):
                x = x.rstrip("/")

            ret.append(x);

        return ret

# vim:ts=4:sw=4:et
