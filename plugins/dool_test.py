### Author: Dag Wieers <dag@wieers.com>

class dool_plugin(dool):
    '''
    Provides a test playground to test syntax and structure.
    '''

    def __init__(self):
        self.name = 'test'
        self.vars = ( 'f1', 'f2' )
        self.type = 's'
        self.width = 4
        self.scale = 0

    def extract(self):
        self.val = { 'f1': 'test', 'f2': 'test' }

# vim:ts=4:sw=4:et
