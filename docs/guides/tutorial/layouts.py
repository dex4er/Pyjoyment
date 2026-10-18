"""
__DATA__

@@ with_layout.html.ep
% title('Green')
% layout('green')
Hello World!

@@ layouts/green.html.ep
<!DOCTYPE html>
<html>
  <head><title><%= c.title() %></title></head>
  <body><%= content() %></body>
</html>
"""

from Pyjoyment.Lite import *


get('/with_layout')

app.start()
