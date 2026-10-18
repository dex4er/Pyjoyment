"""
__DATA__

@@ alert_me.html.ep
<!DOCTYPE html>
<html>
  <head>
    <title>Alert me!</title>
    %= include('alertassets')
  </head>
  <body>You've been alerted.</body>
</html>
"""

from Pyjoyment.Lite import *


plugin('AlertAssets')

get('/alert_me')

app.start()
