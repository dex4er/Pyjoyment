"""
__DATA__

@@ magic.html.ep
The magic numbers are <%= one %> and <%= two %>.
"""

from Pyjoyment.Lite import *


# Route leading to an action that renders a template
@get('/foo')
def foo(c):
    c.stash(one=23)
    c.render(template='magic', two=24)


app.start()
