import Pyjo.IOLoop

from Pyjoyment.Lite import *


# Wait 3 seconds before rendering a response
@get('/')
def index(c):
    Pyjo.IOLoop.timer(3, lambda loop: c.render(text='Delayed by 3 seconds!'))


app.start()
