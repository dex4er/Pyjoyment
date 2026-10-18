"""
__DATA__

@@ index.html.ep
<!DOCTYPE html>
<html>
  <head><title>Echo</title></head>
  <body>
    <script>
      const ws = new WebSocket('<%= url_for('echo').to_abs() %>');

      // Incoming messages
      ws.onmessage = function (event) {
        document.body.innerHTML += event.data + '<br/>';
      };

      // Outgoing messages
      ws.onopen = function (event) {
        window.setInterval(function () { ws.send('Hello Pyjo!') }, 1000);
      };
    </script>
  </body>
</html>
"""

from Pyjoyment.Lite import *


# Template with browser-side code
get('/', 'index')


# WebSocket echo service
@websocket('/echo')
def echo(c):
    # Opened
    c.app.log.debug('WebSocket opened')

    # Increase inactivity timeout for connection a bit
    c.inactivity_timeout(300)

    # Incoming message
    c.on('message', lambda c, msg: c.send(f'echo: {msg}'))

    # Closed
    c.on('finish', lambda c, code, reason=None: c.app.log.debug(f'WebSocket closed with status {code}'))


app.start()
