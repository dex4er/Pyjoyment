"""
__DATA__

@@ index.html.ep
<!DOCTYPE html>
<html>
  <head>
    <title>Echo</title>
    <script>
      const ws = new WebSocket('<%= url_for('echo').to_abs() %>');
      ws.onmessage = function (event) {
        document.body.innerHTML += JSON.parse(event.data).msg;
      };
      ws.onopen = function (event) {
        ws.send(JSON.stringify({msg: 'I ♥ Pyjoyment!'}));
      };
    </script>
  </head>
</html>
"""

from Pyjoyment.Lite import *


@websocket('/echo')
def echo(c):
    @c.on('json')
    def json(c, document):
        document['msg'] = f'echo: {document["msg"]}'
        c.send({'json': document})


get('/', 'index')

app.start()
