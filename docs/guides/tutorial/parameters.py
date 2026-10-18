from Pyjoyment.Lite import *


# /foo?user=sri
@get('/foo')
def foo(c):
    user = c.param('user')
    c.render(text=f'Hello {user}.')


app.start()
