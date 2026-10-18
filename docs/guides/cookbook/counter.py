import Pyjo.IOLoop

from Pyjoyment.Lite import *


# Count to 5 in 1 second steps
@get('/')
def index(c):
    # Start recurring timer
    i = 1

    @Pyjo.IOLoop.recurring(1)
    def count(loop):
        nonlocal i
        c.write_chunk(f'{i}'.encode())
        if i == 5:
            c.finish()
        i += 1

    # Stop recurring timer
    c.on('finish', lambda c: Pyjo.IOLoop.remove(count))


app.start()
