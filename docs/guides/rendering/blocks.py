"""
__DATA__

@@ welcome.html.ep
<% block = begin %>
  % name = args[0]
  Hello <%= name %>.
<% end %>
<%= block('Wolfgang') %>
<%= block('Baerbel') %>
"""

from Pyjoyment.Lite import *


get('/', 'welcome')

app.start()
