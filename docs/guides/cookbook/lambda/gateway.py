import Pyjo.App.Lambda

from Pyjo.File import curfile
from Pyjoyment.Lite import *


# The event function of myapp.py, next to this script, under /myapp, as API Gateway runs it on AWS
plugin('Mount', {'/myapp': Pyjo.App.Lambda.new(function='myapp.handler', task_root=curfile().dirname().to_str())})

app.start()
