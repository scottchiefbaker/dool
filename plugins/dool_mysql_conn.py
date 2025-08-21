### Author: <lefred$inuits,be>

global mysql_user
mysql_user = os.getenv('DOOL_MYSQL_USER')

global mysql_pwd
mysql_pwd = os.getenv('DOOL_MYSQL_PWD')

global mysql_host
mysql_host = os.getenv('DOOL_MYSQL_HOST')

global mysql_port
mysql_port = os.getenv('DOOL_MYSQL_PORT')

global mysql_socket
mysql_socket = os.getenv('DOOL_MYSQL_SOCKET')

global read_default_file
read_default_file = os.getenv('DOOL_MYSQL_DEFAULTS_FILE')

global read_default_group
read_default_group = os.getenv('DOOL_MYSQL_DEFAULTS_GROUP')

class dool_plugin(dool):
    """
    Plugin for MySQL 5 connections.
    """

    def __init__(self):
        self.name  = 'mysql5 conn'
        self.nick  = ('ThCon', 'ThRun', '%Con')
        self.vars  = ('Threads_connected', 'Threads_running', 'Threads')
        self.types = ('d', 'd', 'f')
        self.width = 4
        self.scale = 1

    def check(self): 
        global MySQLdb
        import MySQLdb
        try:
            args = {
                    'read_default_group': 'client',
                    'read_default_file': os.path.expanduser('~/.my.cnf'),
                    }
            if mysql_user:
                args['user'] = mysql_user
            if mysql_pwd:
                args['passwd'] = mysql_pwd
            if mysql_host:
                args['host'] = mysql_host
            if mysql_port:
                args['port'] = mysql_port
            if mysql_socket:
                args['unix_socket'] = mysql_socket
            if read_default_file:
                args['read_default_file'] = read_default_file
            if read_default_group:
                args['read_default_group'] = read_default_group

            self.db = MySQLdb.connect(**args)
        except Exception as e:
            raise Exception('Cannot interface with MySQL server, %s' % e)

    def extract(self):
        try:
            c = self.db.cursor()

            c.execute("SHOW GLOBAL VARIABLES LIKE 'max_connections'")
            max = c.fetchone()

            c.execute("SHOW GLOBAL STATUS LIKE 'Threads%'")
            for name, val in c.fetchall():
                if name in self.vars:
                    self.set2[name] = float(val)
                    if name == 'Threads_connected':
                        self.set2['Threads'] = float(val) / float(max[1]) * 100.0

            for name in self.vars:
                self.val[name] = self.set2[name] * 1.0 / elapsed

            if step == op.delay:
                self.set1.update(self.set2)

        except Exception as e:
            for name in self.vars:
                self.val[name] = -1

# vim:ts=4:sw=4:et
