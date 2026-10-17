"""
__DATA__
@@ works.html.ep
It is <%= name %>!

@@ too.html.ep
It <%= config()['it'] %>!
"""

from Pyjoyment.Lite import get, plugin


plugin('JSONConfig')

get('/works')

get('/works/too', 'too')
