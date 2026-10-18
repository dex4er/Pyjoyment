from Pyjoyment.Lite import *


# Route leading to an action that renders some text
@get('/foo')
def foo(c):
    c.render(text='Hello World!')


app.start()
