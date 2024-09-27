# Author: Brock Palen <brockp@mlds-networks.com>, Kilian Cavalotti <kilian@stanford.edu>

class dool_plugin(dool):
    def __init__(self):
        self.nick = ('read', 'write')
        self.cols = 2
        self.stat_path = '/proc/fs/lustre/llite'

    def check(self):
        if os.path.exists('/proc/fs/lustre/llite'):
            self.stat_path = '/proc/fs/lustre/llite'
        elif os.path.exists('/sys/kernel/debug/lustre/llite'):
            self.stat_path = '/sys/kernel/debug/lustre/llite'
        else:
            raise Exception('Lustre filesystem not found')
        info(1, 'Module %s is still experimental.' % self.filename)

    def name(self):
        return [mount for mount in os.listdir(self.stat_path)]

    def vars(self):
        return [mount for mount in os.listdir(self.stat_path)]

    def extract(self):
        for name in self.vars:
            read = write = 0
            for line in dopen(os.path.join(self.stat_path, name, 'stats')).readlines():
                l = line.split()
                if len(l) < 6: continue
                if l[0] == 'read_bytes':
                    read = int(l[6])
                elif l[0] == 'write_bytes':
                    write = int(l[6])
            self.set2[name] = (read, write)

            self.val[name] = list(map(lambda x, y: (y - x) * 1.0 / elapsed, self.set1[name], self.set2[name]))

        if step == op.delay:
            self.set1.update(self.set2)

# vim:ts=4:sw=4
