### Author: Ming-Hung Chen <minghung.chen@gmail.com>


class dool_plugin(dool):
    bonddirname = '/proc/net/bonding/'
    netdirname = '/sys/class/net/'
    """
    Bytes received or sent through bonding interfaces.
    Usage:
        dool --bond -N <adapter name>,total
        default dool --bond is the same as
        dool --bond -N total

    """

    def __init__(self):
        self.nick = ('recv', 'send')
        self.type = 'd'
        self.cols = 2
        self.width = 6

    def discover(self, *objlist):
        ret = []
        for subdirname in os.listdir(self.bonddirname):
            if not os.path.isdir(os.path.join(self.netdirname,subdirname, 'statistics')) : continue
            device_dir =  os.path.join(self.netdirname, subdirname, 'statistics')
            ret.append(subdirname)
        ret.sort()
        for item in objlist: ret.append(item)
        return ret

    def vars(self):
        ret = []
        if op.netlist:
            varlist = op.netlist
        elif not op.full:
            varlist = ('total',)
        else:
            varlist = self.discover
            varlist.sort()
        for name in varlist:
            if name in self.discover + ['total']:
                ret.append(name)
        if not ret:
            raise Exception('No suitable network interfaces found to monitor')
        return ret

    def name(self):
        return ['bond/'+name for name in self.vars]

    def extract(self):
        self.set2['total'] = [0, 0]
        ifaces = self.discover
        for name in self.vars: self.set2[name] = [0, 0]
        for name in ifaces:
            rcv_counter_name=os.path.join(self.netdirname, name, 'statistics/rx_bytes')
            xmit_counter_name=os.path.join(self.netdirname, name, 'statistics/tx_bytes')
            rcv_lines = dopen(rcv_counter_name).readlines()
            xmit_lines = dopen(xmit_counter_name).readlines()
            if len(rcv_lines) < 1 or len(xmit_lines) < 1:
                continue
            rcv_value = int(rcv_lines[0])
            xmit_value = int(xmit_lines[0])
            if name in self.vars :
                self.set2[name] = (rcv_value, xmit_value)
            self.set2['total'] = ( self.set2['total'][0] + rcv_value, self.set2['total'][1] + xmit_value)
        if update:
            for name in self.set2:
                self.val[name] = [
                    (self.set2[name][0] - self.set1[name][0]) / elapsed,
                    (self.set2[name][1] - self.set1[name][1]) / elapsed,                    
                ]
                if self.val[name][0] < 0: self.val[name][0] += maxint + 1
                if self.val[name][1] < 0: self.val[name][1] += maxint + 1
        if step == op.delay:
            self.set1.update(self.set2)
