import shlex
import subprocess

### Author: Dag Wieers <dag$wieers,com>, Ming-Hung Chen <minghung.chen@gmail.com>

global mysql_options
mysql_options = shlex.split(os.getenv('DOOL_MYSQL', ''))

class dool_plugin(dool):
    def __init__(self):
        self.name = 'innodb ops'
        self.nick = ('ins', 'upd', 'del', 'rea')
        self.vars = ('inserted', 'updated', 'deleted', 'read')
        self.type = 'f'
        self.width = 3
        self.scale = 1000

    def check(self):
        if os.access('/usr/bin/mysql', os.X_OK):
            try:
                p = subprocess.Popen(
                    ['/usr/bin/mysql', '-n'] + mysql_options,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    close_fds=True,
                )
                self.stdin, self.stdout, self.stderr = p.stdin, p.stdout, p.stderr
                checkerrpipe(self.stderr, '.+')
            except IOError:
                raise Exception('Cannot interface with MySQL binary')
            return True
        raise Exception('Needs MySQL binary')

    def extract(self):
        try:
            self.stdin.write(b'SHOW ENGINE INNODB STATUS\\G\n')
            line = greppipe(self.stdout, 'Number of rows inserted')

            if line:
                l = line.split()
                self.set2['inserted'] = int(l[4].rstrip(','))
                self.set2['updated'] = int(l[6].rstrip(','))
                self.set2['deleted'] = int(l[8].rstrip(','))
                self.set2['read'] = int(l[10])

            for name in self.vars:
                self.val[name] = (self.set2[name] - self.set1[name]) * 1.0 / elapsed

            if step == op.delay:
                self.set1.update(self.set2)

        except IOError as e:
            if op.debug > 1: print('%s: lost pipe to mysql, %s' % (self.filename, e))
            for name in self.vars: self.val[name] = -1

        except Exception as e:
            if op.debug > 1: print('%s: exception' % (self.filename, e))
            for name in self.vars: self.val[name] = -1

# vim:ts=4:sw=4:et
