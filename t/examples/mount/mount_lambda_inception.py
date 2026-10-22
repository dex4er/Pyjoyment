import Pyjo.Test.Pyjo

from Pyjo.File import curfile
from Pyjo.Test import *

import os


if os.name == 'nt':
    plan(skip_all='Lambda functions need pipes that the event loop watches, which Windows does not have')

# The application of examples/mount/mount_lambda_inception.py, which the test loads without starting a server
script = curfile().dirname().dirname().dirname().sibling('examples', 'mount', 'mount_lambda_inception.py')
t = Pyjo.Test.Pyjo.new(script)

with subtest('Pyjoyment.Lite'):
    t.get_ok('/').status_is(200).content_is('I ♥ Pyjoyment!')

with subtest('Pyjoyment on Lambda'):
    t.get_ok('/lambda').status_is(200).content_is('Hello Pyjoyment at /lambda on Lambda!')
    t.get_ok('/lambda/').status_is(200).content_is('Hello Pyjoyment at /lambda on Lambda!')
    t.get_ok('/lambda/pyjo/pyjo.css').status_is(200).content_type_is('text/css')
    t.get_ok('/lambda/foo').status_is(404)

done_testing()
