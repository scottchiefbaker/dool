# Author: Hans-Nikolai Viessmann <hans-nikolai.viessmann@psi.ch>

class dool_plugin(dool):
    def __init__(self):
        self.name = 'lnet'
        self.vars = ['recv', 'send']
        self.type = 'b'
        self.cols = 1
        self.scale = 1000
        self.open('/sys/kernel/debug/lnet/stats')

    def check(self):
        if not os.path.exists('/sys/kernel/debug/lnet/stats'):
            raise Exception('LNET device not found')
        info(1, 'Module %s is still experimental.' % self.filename)

    def extract(self):
        l = self.splitline()

        self.set2['send'] = [int(l[7])]
        self.set2['recv'] = [int(l[8])]

        for name in self.vars:
            self.val[name] = [(self.set2[name][0] - self.set1[name][0]) * 1.0 / elapsed]

        if step == op.delay:
            self.set1.update(self.set2)

# vim:ts=4:sw=4
