### Author: David Nicklay <david-d$nicklay,com>
### Modified from disk-util: Dag Wieers <dag$wieers,com>

class dool_plugin(dool):
    """
    Read and Write average wait times of block devices.

    Displays the average read and write wait times of block devices
    """

    def __init__(self):
        self.nick = ('rawait', 'wawait')
        self.type = 'f'
        self.width = 4
        self.scale = 1
        self.open('/proc/diskstats')
        self.cols = 1
        self.struct = dict( rd_ios=0, wr_ios=0, rd_ticks=0, wr_ticks=0 )

    def discover(self, *objlist):
        ret = []
        for l in self.splitlines():
            if len(l) < 13: continue
            if set(l[3:]) == {'0'}: continue
            name = l[2]
            ret.append(name)
        for item in objlist: ret.append(item)
        if not ret:
            raise Exception('No suitable block devices found to monitor')
        return ret

    def vars(self):
        ret = []
        if op.disklist:
            varlist = op.disklist
        else:
            varlist = []
            blockdevices = [os.path.basename(filename) for filename in glob.glob('/sys/block/*')]
            for name in self.discover:
                if DOOL_DISKFILTER.match(name): continue
                if name not in blockdevices: continue
                varlist.append(name)
            varlist.sort()
        for name in varlist:
            if name in self.discover:
                ret.append(name)
        return ret

    def name(self):
        return self.vars

    def extract(self):
        for l in self.splitlines():
            if len(l) < 13: continue
            if l[5] == '0' and l[9] == '0': continue
            if set(l[3:]) == {'0'}: continue
            name = l[2]
            if name not in self.vars: continue
            self.set2[name] = dict(
                rd_ios = int(l[3]),
                wr_ios = int(l[7]),
                rd_ticks = int(l[6]),
                wr_ticks = int(l[10]),
            )

        for name in self.vars:
            rd_tput = self.set2[name]['rd_ios'] - self.set1[name]['rd_ios']
            wr_tput = self.set2[name]['wr_ios'] - self.set1[name]['wr_ios']
            if rd_tput:
                rd_wait = ( self.set2[name]['rd_ticks'] - self.set1[name]['rd_ticks'] ) * 1.0 / rd_tput
            else:
                rd_wait = 0
            if wr_tput:
                wr_wait = ( self.set2[name]['wr_ticks'] - self.set1[name]['wr_ticks'] ) * 1.0 / wr_tput
            else:
                wr_wait = 0
            self.val[name] = ( rd_wait, wr_wait )

        if step == op.delay:
            self.set1.update(self.set2)
