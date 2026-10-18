"""
__DATA__

@@ counter.html.ep
Counter: <%= session('counter') %>
"""

from Pyjoyment.Lite import *


# Access session data in action and template
@get('/counter')
def counter(c):
    session = c.session()
    session['counter'] = session.get('counter', 0) + 1


app.start()
