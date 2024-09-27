### Author: Dag Wieers <dag$wieers,com>

class dool_plugin(dool):
    """
    Show internal Dool step and delay counters
    """

    def __init__(self):
        self.name = 'dool'
        #self.nick = ('counter',)
        self.vars = ('stp','dly','cnt',)
        self.type = 'd'
        self.width = 3
        self.scale = 10

    def extract(self):
        self.val['stp']  = step
        self.val['dly'] = op.delay

        if op.count == -1:
            xcount = 0
        else:
            xcount = op.count

        self.val['cnt'] = xcount

# vim:ts=4:sw=4:et
