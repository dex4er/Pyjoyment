import Pyjo.App.Lambda

from Pyjo.File import curfile
from Pyjoyment.Lite import *


# Starlette on Mangum, the event function of hello_mangum.py, next to this script, under /mangum, which runs an event
# loop of its own in its process
plugin(
    'Mount', {'/mangum': Pyjo.App.Lambda.new(function='hello_mangum.handler', task_root=curfile().dirname().to_str())}
)

get('/', {'text': 'I ♥ Pyjoyment!'})

app.start()
