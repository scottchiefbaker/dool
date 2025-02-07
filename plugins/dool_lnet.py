# Author: Hans-Nikolai Viessmann <hans-nikolai.viessmann@psi.ch>

# Lustre network utilisation is tricky to capture, as the Lustre
# driver and the Luster Network driver operate outside of the
# kernel network stack, i.e. read/write IO on Lustre mount does
# not report any network activity.
#
# Implemnetation is based on stats information collected via
# LNET and _described_ in the source code, see:
# https://github.com/lustre/lustre-release/blob/master/lnet/lnet/lnet_debugfs.c

class dool_plugin(dool):
    def __init__(self):
        self.name = 'lnet'
        self.vars = ['recv', 'send']
        self.type = 'b'
        self.scale = 1000
        self.open('/sys/kernel/debug/lnet/stats')

    def check(self):
        if not os.path.exists('/sys/kernel/debug/lnet/stats'):
            raise Exception('LNET device not found')
        info(1, 'Module %s is still experimental.' % self.filename)

    def extract(self):
        l = self.splitline()

        self.set2['send'] = int(l[7])
        self.set2['recv'] = int(l[8])

        for name in self.vars:
            self.val[name] = (self.set2[name] - self.set1[name]) * 1.0 / elapsed

        if step == op.delay:
            self.set1.update(self.set2)

# vim:ts=4:sw=4
