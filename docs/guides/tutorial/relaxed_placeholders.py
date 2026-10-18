"""
__DATA__

@@ groovy.html.ep
Your name is <%= you %>.
"""

from Pyjoyment.Lite import *


# /hello/test
# /hello/test.html
get('/hello/#you', 'groovy')

app.start()
