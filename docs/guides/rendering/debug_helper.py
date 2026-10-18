"""
__DATA__

@@ index.html.ep
% debug('Hello from a template!')
"""

from Pyjoyment.Lite import *


@helper('debug')
def debug(c, string):
    c.app.log.debug(string)


@get('/', 'index')
def index(c):
    c.debug('Hello from an action!')


app.start()
