"""
__DATA__

@@ test.html.mine
Hello World from the DATA section!
"""

from Pyjoyment.Lite import *


plugin('MyRenderer')

# Render an inline template
get('/inline', {'inline': 'Hello World inline!', 'handler': 'mine'})

# Render a template from the DATA section
get('/data', {'template': 'test'})

app.start()
