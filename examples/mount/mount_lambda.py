import Pyjo.App.Lambda

from Pyjo.File import curfile
from Pyjoyment.Lite import *


# The event function of hello_lambda.py, next to this script, under /lambda, in a process of its own, which gets the
# requests one after another, as Lambda runs it
plugin(
    'Mount', {'/lambda': Pyjo.App.Lambda.new(function='hello_lambda.handler', task_root=curfile().dirname().to_str())}
)

get('/', {'text': 'I ♥ Pyjoyment!'})

app.start()
