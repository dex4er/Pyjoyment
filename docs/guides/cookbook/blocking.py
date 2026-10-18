import Pyjo.IOLoop

from Pyjoyment.Lite import *

import time


# Operation that would block the event loop for 5 seconds
@get('/')
def index(c):
    def operation(subprocess):
        time.sleep(5)
        return '♥', 'Pyjoyment'

    (
        Pyjo.IOLoop.subprocess()
        .run_p(operation)
        .then(lambda heart, name: c.render(text=f'I {heart} {name}!'))
        .catch(lambda err: c.reply.exception(err))
    )


app.start()
