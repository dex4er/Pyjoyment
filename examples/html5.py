# TODO: runs once Pyjoyment.Lite is ported

from Pyjoyment.Lite import app, get, path


# Render template "index.html.ep" from the DATA section
get('/', template='index')


# WebSocket service used by the template to extract the title from a web site
@path('/title')
def websocket(c):
    @c.on
    def message(c, msg):
        title = c.ua.get(msg).res.dom().at('title').text
        c.send(title)


app.start()


DATA = """
@@ index.html.ep
% url = url_for('title')
<script>
  var ws = new WebSocket('<%= url.to_abs() %>');
  ws.onmessage = function (event) { document.body.innerHTML += event.data };
  ws.onopen    = function (event) { ws.send('https://mojolicious.org') };
</script>
"""
