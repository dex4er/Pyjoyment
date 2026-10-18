"""
__DATA__

@@ foo/bar.html.ep
<!DOCTYPE html>
<html>
  %= include('_header', title='Howdy')
  <body>Bar</body>
</html>

@@ _header.html.ep
<head><title><%= title %></title></head>
"""

from Pyjoyment.Lite import *


get('/', {'template': 'foo/bar'})

app.start()
