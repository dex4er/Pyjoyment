"""
__DATA__

@@ layouts/mylayout.html.ep
<!DOCTYPE html>
<html>
  <head><title>Hello</title></head>
  <body><%= content() %></body>
</html>

@@ first.html.ep
%= content('header', begin
  Default header
% end)
<div>Hello World!</div>
%= content('footer', begin
  Default footer
% end)

@@ second.html.ep
% extends('first')
% content('header', begin
  New header
% end)

@@ third.html.ep
% extends('second')
% content('footer', begin
  New footer
% end)
"""

from Pyjoyment.Lite import *


# first > mylayout
get('/first', {'template': 'first', 'layout': 'mylayout'})

# third > second > first > mylayout
get('/third', {'template': 'third', 'layout': 'mylayout'})

app.start()
