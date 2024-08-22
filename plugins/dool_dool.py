### Author: Dag Wieers <dag$wieers,com>

class dool_plugin(dool):
    """
    Provide more information related to the Dool process.

    The Dool cputime is the total cputime Dool requires per second. On a
    system with one cpu and one core, the total cputime is 1000ms. On a system
    with 2 cores the total is 2000ms. It may help to vizualise the performance
    of Dool land its selection of plugins.
    """
    def __init__(self):
        self.name  = 'dool'
        self.vars  = ('cputime', 'latency')
        self.type  = 'd'
        self.width = 5
        self.scale = 1000
        self.open('/proc/%s/schedstat' % ownpid)

    def extract(self):
        l = self.splitline()

        #l = linecache.getline('/proc/%s/schedstat' % self.pid, 1).split()
        self.set2['cputime'] = int(l[0])
        self.set2['latency'] = int(l[1])

        for name in self.vars:
            self.val[name] = (self.set2[name] - self.set1[name]) * 1.0 / elapsed

        if step == op.delay:
            self.set1.update(self.set2)

# vim:ts=4:sw=4:et
