"""
__DATA__

@@ index.html.ep
%= trim_newline(begin
  Some text.
  %= 1 + 1
  More text.
% end)
"""

from Pyjo.String.HTML import html
from Pyjoyment.Lite import *


@helper('trim_newline')
def trim_newline(c, block):
    result = str(block()).replace('\n', '')
    return html(result)


get('/', 'index')

app.start()
