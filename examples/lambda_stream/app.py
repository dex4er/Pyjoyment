import Pyjo.Promise

from Pyjoyment.Lite import *


@get('/')
def index(c):
    c.render(text='Hello Pyjoyment on AWS Lambda, streaming!')


# The lines of a count, half a second after each other, each written as it comes, as the tokens of a model are
@get('/count')
async def count(c):
    c.res.headers.content_type = 'text/plain'
    for n in range(1, 6):
        c.write_chunk(f'{n}\n'.encode())
        await Pyjo.Promise.timer(0.5)
    c.finish()


# The handler "app.handler" of the event function, and the command of the arguments otherwise
handler = app.start()
