"""
__DATA__

@@ hello.html.ep
<!DOCTYPE html>
<html>
  <head><title><%= c.title() %></title></head>
  <body>Compressed content.</body>
</html>
"""

from Pyjoyment.Lite import *

import gzip
import re


@hook('after_render')
def after_render(c, output, format):

    # Check if "gzip=True" has been set in the stash
    if not c.stash().get('gzip'):
        return

    # Check if user agent accepts gzip compression
    if not re.search(r'gzip', c.req.headers.accept_encoding or '', re.I):
        return
    c.res.headers.append('Vary', 'Accept-Encoding')

    # Compress content with gzip
    c.res.headers.content_encoding = 'gzip'
    compressed = gzip.compress(output.getvalue())
    output.seek(0)
    output.truncate()
    output.write(compressed)


get('/', {'template': 'hello', 'title': 'Hello', 'gzip': True})

app.start()
