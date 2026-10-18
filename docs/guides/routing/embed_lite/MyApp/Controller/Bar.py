# Controller
from Pyjoyment.Lite import *


# /hello
@get('/hello')
def hello(c):
    name = c.param('name')
    c.render(text=f'Hello {name}.')
