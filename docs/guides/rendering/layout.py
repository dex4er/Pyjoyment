"""
__DATA__

@@ foo/bar.html.ep
% layout('mylayout')
Hello World!

@@ layouts/mylayout.html.ep
<!DOCTYPE html>
<html>
  <head><title>MyApp</title></head>
  <body><%= content() %></body>
</html>
"""

from Pyjoyment.Lite import *


get('/', {'template': 'foo/bar'})

app.start()
