### Author: Dag Wieers <dag$wieers,com>

### FIXME: This module needs infrastructure to provide a list of mountpoints
### FIXME: Would be nice to have a total by default (half implemented)

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

        mystr = os.environ.get('DOOL_FREESPACE_MOUNT_POINTS','').strip()

        if (len(mystr) > 0):
            mp = mystr.split(',')
        else:
            mp = []

        include_fs_types = (
            'ext2', 'ext3', 'ext4', 'btrfs', 'xfs'
        )

        for l in self.splitlines():
            if len(l) < 6: continue

            device      = l[0]
            mount_point = l[1]
            fs_type     = l[2]

            #print(device + " | " + mount_point + " | " + fs_type)

            # If there is an array of mount points (whitelist) and this
            # mount point is *NOT* in that list, skip it
            if (mp):
                if (not mount_point in mp):
                    continue
            # If there is NOT an array of mount points check it against a
            # whitelisted array of fs_types
            elif (fs_type not in include_fs_types):
                continue

            res = os.statvfs(mount_point)

            if res[0] == 0: continue ### Skip zero block filesystems
            ret.append(mount_point)

        return ret

    def name(self):
        return ['/' + os.path.basename(name) for name in self.vars]

    def extract(self):
        self.val['total'] = (0, 0)
        for name in self.vars:
            res = os.statvfs(name)
            self.val[name] = ( (float(res.f_blocks) - float(res.f_bavail)) * int(res.f_frsize), float(res.f_bavail) * float(res.f_frsize) )
            self.val['total'] = (self.val['total'][0] + self.val[name][0], self.val['total'][1] + self.val[name][1])

# vim:ts=4:sw=4:et
