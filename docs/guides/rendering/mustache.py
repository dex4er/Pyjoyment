"""
__DATA__

@@ index.html.mustache
Hello {{= name }}.
"""

from Pyjoyment.Lite import *


plugin('EPRenderer', {'name': 'mustache', 'template': {'tag_start': '{{', 'tag_end': '}}'}})

get('/:name', {'name': 'Anonymous'}, 'index')

app.start()
