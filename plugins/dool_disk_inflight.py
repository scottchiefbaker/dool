### Author: Scott Baker <scott@perturb.org>

class dool_plugin(dool):
    """
    The in-flight number of IO operations pending per disk
    """

    def __init__(self):
        # This is the plugin name that goes on top of the columns
        #self.name  = 'io/inflight'
        self.name  = self.get_devs()

        # Title of each column (or group of colums)
        self.nick = ('ioif',)
        # These are the sub headings under the main column (each disk device)
        self.vars  = self.get_devs()
        # It's a decimal number
        self.type  = 'd'
        # Each column is 7 chars wide
        self.width = 4
        # Group the colorings to chunks of 20
        self.scale = 20

    def get_devs(self):
        # If there was a disk filter specified on the CLI
        # example: dool --disk-infligh -D md123,sda
        if op.disklist:
            return op.disklist

        ret   = []
        globx = glob.glob('/sys/block/*')

        for path in globx:
            base = os.path.basename(path)
            ret.append(base)

        ret.sort()

        return ret

    def extract(self):
        for dev in self.vars:
            # Documentation for /sys/block/$DEV/stat
            # https://www.kernel.org/doc/Documentation/block/stat.txt
            path = ("/sys/block/%s/stat" % (dev))

            for l in proc_splitlines(path):
                value = int(l[8])

                # For testing we can toss random data in the buckets
                #value = random.randrange(1,100)

                self.val[dev] = (value,)
