"""
__DATA__

@@ block.html.ep
% link = begin
  % url, name = args
  Try <%= link_to(url, begin %><%= name %><% end) %>.
% end
<!DOCTYPE html>
<html>
  <head><title>Sebastians frameworks</title></head>
  <body>
    %= link('https://mojolicious.org', 'Mojolicious')
    %= link('https://pyjoyment.readthedocs.io', 'Pyjoyment')
  </body>
</html>
"""

from Pyjoyment.Lite import *


get('/with_block', 'block')

app.start()
