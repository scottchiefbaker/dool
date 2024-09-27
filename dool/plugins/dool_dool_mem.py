### Author: Dag Wieers <dag$wieers,com>

class dool_plugin(dool):
    """
    Provide memory information related to the dstat process.

    The various values provide information about the memory usage of the
    dstat process. This plugin gives you the possibility to follow memory
    usage changes of dstat over time. It may help to vizualise the
    performance of Dstat and its selection of plugins.
    """
    def __init__(self):
        self.name = 'dstat memory usage'
        self.vars = ('virtual', 'resident', 'shared', 'data')
        self.type = 'd'
        self.open('/proc/%s/statm' % ownpid)

    def extract(self):
        l = self.splitline()
#        l = linecache.getline('/proc/%s/schedstat' % self.pid, 1).split()
        self.val['virtual'] = int(l[0]) * pagesize / 1024
        self.val['resident'] = int(l[1]) * pagesize / 1024
        self.val['shared'] = int(l[2]) * pagesize / 1024
#        self.val['text'] = int(l[3]) * pagesize / 1024
#        self.val['library'] = int(l[4]) * pagesize / 1024
        self.val['data'] = int(l[5]) * pagesize / 1024

# vim:ts=4:sw=4:et
