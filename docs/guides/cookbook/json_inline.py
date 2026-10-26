"""
__DATA__

@@ index.html.ep
% import Pyjo.JSON
<!DOCTYPE html>
<html>
  <head><title>Greeting</title></head>
  <body>
    <h1 id="greeting"></h1>
    <script type="application/json" id="state"><%== Pyjo.JSON.to_json(state) %></script>
    <script>
      const state = JSON.parse(document.getElementById('state').textContent);
      document.getElementById('greeting').textContent = state.greeting;
    </script>
  </body>
</html>
"""

from Pyjoyment.Lite import *


@get('/')
def index(c):
    c.render('index', state={'greeting': c.param('greeting') or 'Hello World!'})


app.start()
