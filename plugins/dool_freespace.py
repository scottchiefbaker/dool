### Author: Dag Wieers <dag$wieers,com>

### FIXME: This module needs infrastructure to provide a list of mountpoints
### FIXME: Would be nice to have a total by default (half implemented)

class dstat_plugin(dstat):
    """
    Amount of used and free space per mountpoint.
    """

    def __init__(self):
        self.nick = ('used', 'free')
        self.open('/etc/mtab')
        self.cols = 2

    def vars(self):
        ret = []

        include_fs_types = (
            'ext2', 'ext3', 'ext4', 'btrfs', 'xfs'
        )

        ### FIXME: Excluding 'none' here may not be what people want (/dev/shm)
        exclude_fs_types = (
            'devpts', 'none', 'proc', 'sunrpc', 'usbfs', 'securityfs', 'hugetlbfs',
            'configfs', 'selinuxfs', 'pstore', 'nfsd', 'tracefs', 'cgroup2', 'bpf'
        )

        for l in self.splitlines():
            if len(l) < 6: continue

            device      = l[0]
            mount_point = l[1]
            fs_type     = l[2]

            if fs_type not in (include_fs_types):
                continue

            name = l[1]
            res  = os.statvfs(name)

            if res[0] == 0: continue ### Skip zero block filesystems
            ret.append(name)

            #print(l[0] + " / " + name + " / " + l[2])
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
