### Author: Dag Wieers <dag$wieers,com>

class dool_plugin(dool):
    """
    Number of read and write transactions per device.

    Displays the number of read and write I/O transactions per device.
    """

    def __init__(self):
        self.nick = ('#read', '#writ' )
        self.type = 'd'
        self.width = 5
        self.scale = 1000
        self.open('/proc/diskstats')
        self.cols = 2

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
        elif not op.full:
            varlist = ('total',)
        else:
            varlist = []
            for name in self.discover:
                if DOOL_DISKFILTER.match(name): continue
                if name not in blockdevices(): continue
                varlist.append(name)
#           if len(varlist) > 2: varlist = varlist[0:2]
            varlist.sort()
        for name in varlist:
            if name in self.discover + ['total'] or name in op.diskset:
                ret.append(name)
        return ret

    def name(self):
        return ['dsk/'+sysfs_dev(name) for name in self.vars]

    def extract(self):
        for name in self.vars: self.set2[name] = (0, 0)
        for l in self.splitlines():
            if len(l) < 13: continue
            if l[3] == '0' and l[7] == '0': continue
            if set(l[3:]) == {'0'}: continue
            name = l[2]
            if not DOOL_DISKFILTER.match(name):
                self.set2['total'] = ( self.set2['total'][0] + int(l[3]), self.set2['total'][1] + int(l[7]) )
            if name in self.vars and name != 'total':
                self.set2[name] = ( self.set2[name][0] + int(l[3]), self.set2[name][1] + int(l[7]))
            for diskset in self.vars:
                if diskset in op.diskset:
                    for disk in op.diskset[diskset]:
                        if re.match('^'+disk+'$', name):
                            self.set2[diskset] = ( self.set2[diskset][0] + int(l[3]), self.set2[diskset][1] + int(l[7]) )

        for name in self.set2:
            self.val[name] = list(map(lambda x, y: (y - x) / elapsed, self.set1[name], self.set2[name]))

        if step == op.delay:
            self.set1.update(self.set2)
