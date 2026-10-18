"""
__DATA__

@@ groovy.html.ep
Your name is <%= you %>.
"""

from Pyjoyment.Lite import *


# /hello/test
# /hello/test123
# /hello/test.123/test/123
get('/hello/*you', 'groovy')

app.start()
