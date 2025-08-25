### Author: Dag Wieers <dag$wieers,com>
# DOOL_OPTS: PARAM_REQUIRED

# Syntax:
#    list all mount points in /etc/mtab:
#       dool --freespace all
#
#    list specific mount points:
#       dool --freespace /mnt/disk1,/mnt/vault

class dool_plugin(dool):
    """
    Amount of used and free space per mountpoint.
    """

    def __init__(self):
        self.nick = ('used', 'free')
        self.open('/etc/mtab')
        self.cols = 2

    def vars(self):
        ret = []

        # Get the mountpoint string from the optional param at the CLI
        # or fallback to the environment variable.
        # If there is NO string we default to showing all mount points
        global op
        param = op.plugin_params['freespace']

        # Sometimes the next param after --freespace is NOT a mountpoint
        # i.e. dool --freespace 5
        # This will fallback to "all" if the param doesn't look like a mountpoint
        if (param != "all" and not param.startswith("/")):
            raise Exception("Freespace requires a comma separated list of mount points or \"all\"")

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

            # k(device + " | " + mount_point + " | " + fs_type)

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
                # print("Warning: Skipping %s because it is not readable" % [mount_point]);
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
            self.val[name] = ( (float(res.f_blocks) - float(res.f_bavail)) * int(res.f_frsize), float(res.f_bavail) * float(res.f_frsize) )
            self.val['total'] = (self.val['total'][0] + self.val[name][0], self.val['total'][1] + self.val[name][1])

    def clean_mountpoints(self, items):
        ret = []

        # Remove any trailing '/' from mount points
        for x in items:
            if (x != "/"):
                x = x.rstrip("/")

            ret.append(x);

        return ret

# vim:ts=4:sw=4:et
