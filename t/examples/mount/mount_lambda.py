import Pyjo.Test.Pyjo

from Pyjo.File import curfile
from Pyjo.Test import *

import os


if os.name == 'nt':
    plan(skip_all='Lambda functions need pipes that the event loop watches, which Windows does not have')

# The application of examples/mount/mount_lambda.py, which the test loads without starting a server
t = Pyjo.Test.Pyjo.new(curfile().dirname().dirname().dirname().sibling('examples', 'mount', 'mount_lambda.py'))

with subtest('Pyjoyment.Lite'):
    t.get_ok('/').status_is(200).content_is('I ♥ Pyjoyment!')

with subtest('Lambda'):
    t.get_ok('/lambda').status_is(200).content_type_is('text/plain').content_is('Hello Lambda at lambda for /lambda!')
    t.get_ok('/lambda/foo/bar').status_is(200).content_is('Hello Lambda at lambda for /lambda/foo/bar!')

done_testing()
