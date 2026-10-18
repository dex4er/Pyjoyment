"""
__DATA__

@@ exception.production.html.ep
<!DOCTYPE html>
<html>
  <head><title>Server error</title></head>
  <body>
    <h1>Exception</h1>
    <p><%= exception.message %></p>
    <h1>Stash</h1>
    <pre><%= dumper(snapshot) %></pre>
  </body>
</html>
"""

from Pyjoyment.Lite import *


@get('/dies')
def dies(c):
    raise Exception('Intentional error')


app.start()
