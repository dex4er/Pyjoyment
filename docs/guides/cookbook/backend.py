"""
__DATA__

@@ github.html.ep
<!DOCTYPE html>
<html>
  <head><title>GitHub results for "pyjoyment"</title></head>
  <body>
    % for item in items:
      <p><%= item['full_name'] %></p>
    % end
  </body>
</html>
"""

from Pyjoyment.Lite import *


# Search GitHub for "pyjoyment"
@get('/')
def index(c):
    url = 'https://api.github.com/search/repositories?q=pyjoyment'
    c.ua().get(url, lambda ua, tx: c.render('github', items=tx.result.json('/items')))


app.start()
