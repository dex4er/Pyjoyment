"""
__DATA__

@@ index.html.ep
% url = url_for('title')
<script>
  var ws = new WebSocket('<%= url.to_abs() %>');
  ws.onmessage = function (event) { document.body.innerHTML += event.data };
  ws.onopen    = function (event) { ws.send('https://mojolicious.org') };
</script>
"""

# TODO: python examples/html5.py daemon, when Pyjoyment.Commands is ported; until then pyjo-reload examples/html5.py

from Pyjoyment.Lite import app, get, websocket


# Render template "index.html.ep" from the DATA section
get('/', {'template': 'index'})


# WebSocket service used by the template to extract the title from a web site
@websocket('/title')
def title(c):
    @c.on('message')
    def message(c, msg):
        title = c.ua.get(msg).res.dom().at('title').text
        c.send(title)


app.start()
