### Author: Scott Baker <scott@perturb.org>

class dool_plugin(dool):
    def __init__(self):
        self.name    = 'memory percent'
        self.nick    = ('used', 'free', 'cach', 'avai')
        self.vars    = ('MemUsed', 'MemFree', 'Cached', 'MemAvailable')
        self.type    = 's'
        self.scale   = 0
        self.num_fmt = "%5.1f"

        # If the user passed --integer
        if op.integer:
            self.num_fmt = "%5.0f"

        self.open('/proc/meminfo')

    def colorize_percent(self, num, red_high):

        if red_high:
            color_low = theme['colors_lo'][0]
            color_med = theme['colors_lo'][1]
            color_hig = theme['colors_lo'][2]
        else:
            color_low = theme['colors_lo'][2]
            color_med = theme['colors_lo'][1]
            color_hig = theme['colors_lo'][0]

        num_str = self.num_fmt % (num)

        # We're doing a simple red/yellow/green every 33%
        if num <= 33.3333:
            ret = color_low + num_str + ansi['reset']
        elif num <= 66.6666:
            ret = color_med + num_str + ansi['reset']
        else:
            ret = color_hig + num_str + ansi['reset']

        return ret

    def extract(self):
        extra_extract_vars = ('MemTotal', 'Shmem', 'SReclaimable')
        extra_val          = {}

        for l in self.splitlines():
            if len(l) < 2: continue
            name = l[0].split(':')[0]

            if name in self.vars:
                self.val[name] = int(l[1]) * 1024.0
            if name in extra_extract_vars:
                extra_val[name] = int(l[1]) * 1024.0

        total  = extra_val['MemTotal']
        free   = (self.val['MemFree']      / total) * 100
        avail  = (self.val['MemAvailable'] / total) * 100
        cached = (self.val['Cached']       / total) * 100

        # This math is borrow from the regular mem plugin
        used   = (((extra_val['MemTotal'] - self.val['Cached'] - extra_val['SReclaimable']) / total) * 100)

        self.val['MemUsed']      = self.colorize_percent(used, False)
        self.val['MemFree']      = self.colorize_percent(free, True)
        self.val['MemAvailable'] = self.colorize_percent(avail, True)

        # Cached is NOT colorized
        self.val['Cached'] = self.num_fmt % cached


