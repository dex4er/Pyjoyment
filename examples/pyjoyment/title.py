"""
__DATA__

@@ index.html.ep
% url = url_for('title')
<script>
  const ws = new WebSocket('<%= url.to_abs() %>');
  ws.onmessage = function (event) { document.body.innerHTML += event.data };
  ws.onopen    = function (event) { ws.send('https://mojolicious.org') };
</script>
"""

from Pyjoyment.Lite import *


# Render template "index.html.ep" from the DATA section
@get('/')
def index(c):
    c.render(template='index')


# WebSocket service used by the template to extract the title from a website
@websocket('/title')
def title(c):
    @c.on('message')
    def message(c, msg):
        c.ua().get_p(msg).then(lambda tx: c.send(tx.result.dom().at('title').text))


app.start()
