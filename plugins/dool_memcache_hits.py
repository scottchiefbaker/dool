### Author: Dean Wilson <dean.wilson@gmail.com>
global socket
import socket

class dstat_plugin(dstat):
    """
    Memcache hit count plugin.

    Displays the number of memcache get_hits and get_misses.
    """
    def __init__(self):
        self.name = 'Memcache'
        self.nick = ('Hit', 'Miss')
        self.vars = ('get_hits', 'get_misses')
        self.type = 'd'
        self.width = 4
        self.scale = 999

    def check(self):
        return 1

    def extract(self):
        stats = self.get_stats()

        # Store the data we're looking for
        for key in self.vars:
            self.set2[key] = int(stats.get(key, -1))

        # If we're updating do the math to count how many happened in this interval
        if update:
            for key in self.vars:
                self.val[key] = (self.set2[key] - self.set1[key]) / elapsed

        if step == op.delay:
            self.set1.update(self.set2)

    def get_stats(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as err:
            print("socket creation failed with error %s" % (err))
            sys.exit(2)

        # Check some ENV variables first, then fall back to the defaults
        port = os.environ.get('DOOL_MEMCACHE_PORT', 11211)
        host = os.environ.get('DOOL_MEMCACHE_HOST', "127.0.0.1")

        try:
            s.connect((host, port))
        except:
            print("Memcache: Error connecting to %s:%d" % (host, port))
            sys.exit(1)

        # Send the stats command and then the quit command right after
        s.sendall(b"stats\n")
        s.sendall(b"quit\n")

        # Read everything in to a buffer
        buf = ""
        while 1:
            data = s.recv(1024)
            if not data:
                break
            buf += data.decode("utf-8")

        lines = buf.split("\r\n")
        stats = {}

        for line in lines:
            parts = line.split(" ")
            if parts[0] == "STAT":
                stats[parts[1]] = parts[2]

        return stats
