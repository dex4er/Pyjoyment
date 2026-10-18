"""
__DATA__

@@ index.html.ep
<%= link_to('Hello', 'hello') %>.
<%= link_to('Reload', 'index') %>.

@@ hello.html.ep
Hello World!
"""

from Pyjoyment.Lite import *


# Render the template "index.html.ep"
@get('/', 'index')
def index(c):
    c.render()


# Render the template "hello.html.ep"
get('/hello')

app.start()
