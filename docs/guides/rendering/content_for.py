"""
__DATA__

@@ foo.html.ep
% layout('mylayout')
% content_for('header', begin
  <meta http-equiv="Content-Type" content="text/html">
% end)
<div>Hello World!</div>
% content_for('header', begin
  <meta http-equiv="Pragma" content="no-cache">
% end)

@@ layouts/mylayout.html.ep
<!DOCTYPE html>
<html>
  <head><%= content('header') %></head>
  <body><%= content() %></body>
</html>
"""

from Pyjoyment.Lite import *


get('/', 'foo')

app.start()
