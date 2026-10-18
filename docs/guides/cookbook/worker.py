import Pyjo.IOLoop

from Pyjoyment.Lite import *

import os


Pyjo.IOLoop.next_tick(lambda loop: app.log.info(f'Worker {os.getpid()} started'))

get('/', {'text': 'Hello World!'})

app.start()
