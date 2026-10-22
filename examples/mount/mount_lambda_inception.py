import Pyjo.App.Lambda
import Pyjo.Server.Lambda
import Pyjoyment

from Pyjo.File import curfile
from Pyjoyment.Lite import *


# Hello world of Pyjoyment as an event function of AWS Lambda, whose stage is the path it is mounted under, as its base
# path
hello = Pyjoyment.new()
hello.routes.get('/').to(cb=lambda c: c.render(text=f'Hello Pyjoyment at {c.url_for("/")} on Lambda!'))
handler = Pyjo.Server.Lambda.new(app=hello).to_lambda_app()

# The handler above under /lambda of the application of Pyjoyment.Lite, in a process of its own, which imports this
# script as the module of the function
function = Pyjo.App.Lambda.new(function='mount_lambda_inception.handler', task_root=curfile().dirname().to_str())
plugin('Mount', {'/lambda': function})

get('/', {'text': 'I ♥ Pyjoyment!'})

app.start()
