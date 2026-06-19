import shlex
import subprocess

### Author: Dag Wieers <dag$wieers,com>, Ming-Hung Chen <minghung.chen@gmail.com>

global mysql_options
mysql_options = shlex.split(os.getenv('DOOL_MYSQL', ''))

class dool_plugin(dool):
    def __init__(self):
        self.name = 'innodb pool'
        self.nick = ('crt', 'rea', 'wri')
        self.vars = ('created', 'read', 'written')
        self.type = 'f'
        self.width = 3
        self.scale = 1000

    def check(self): 
        if not os.access('/usr/bin/mysql', os.X_OK):
            raise Exception('Needs MySQL binary')
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
        except IOError as e:
            raise Exception('Cannot interface with MySQL binary (%s)' % e)

    def extract(self):
        try:
            self.stdin.write(b'SHOW ENGINE INNODB STATUS\\G\n')
            line = matchpipe(self.stdout, r'^Pages read \d+')

            if line:
                l = line.split()
                self.set2['read'] = int(l[2].rstrip(','))
                self.set2['created'] = int(l[4].rstrip(','))
                self.set2['written'] = int(l[6])

            for name in self.vars:
                self.val[name] = (self.set2[name] - self.set1[name]) * 1.0 / elapsed

            if step == op.delay:
                self.set1.update(self.set2)

        except IOError as e:
            if op.debug > 1: print('%s: lost pipe to mysql, %s' % (self.filename, e))
            for name in self.vars: self.val[name] = -1

        except Exception as e:
            if op.debug > 1: print('%s: exception: %s' % (self.filename, e))
            for name in self.vars: self.val[name] = -1

# vim:ts=4:sw=4:et
