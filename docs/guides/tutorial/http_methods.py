from Pyjoyment.Lite import *


# GET /hello
@get('/hello')
def hello(c):
    c.render(text='Hello World!')


# PUT /hello
@put('/hello')
def upload(c):
    size = len(c.req.body)
    c.render(text=f'You uploaded {size} bytes to /hello.')


# GET|POST|PATCH /bye
@any(['GET', 'POST', 'PATCH'], '/bye')
def bye(c):
    c.render(text='Bye World!')


# * /whatever
@any('/whatever')
def whatever(c):
    method = c.req.method
    c.render(text=f'You called /whatever with {method}.')


app.start()
