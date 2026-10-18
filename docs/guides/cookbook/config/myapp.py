"""
__DATA__
@@ with_config.html.ep
<!DOCTYPE html>
<html>
  <head><title><%= config('name') %></title></head>
  <body>Welcome to <%= config('name') %></body>
</html>
"""

from Pyjoyment.Lite import *


plugin('Config')

name = app.config('name')
app.log.debug(f'Welcome to {name}')

get('/', 'with_config')

app.start()
