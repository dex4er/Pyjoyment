"""
__DATA__

@@ groovy.txt.ep
My name is <%= name %> and it is <%= day %>.
"""

from Pyjoyment.Lite import *


# /hello
# /hello/Sara
@get('/hello/:name', {'name': 'Sebastian', 'day': 'Monday'})
def hello(c):
    c.render(template='groovy', format='txt')


app.start()
