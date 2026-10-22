import Pyjo.Test.Pyjo

from Pyjo.File import curfile
from Pyjo.Test import *

import os


if os.name == 'nt':
    plan(skip_all='CGI applications need pipes that the event loop watches, which Windows does not have')

# The application of examples/mount/mount_cgi.py, which the test loads without starting a server
examples = curfile().dirname().dirname().dirname().sibling('examples', 'mount')
t = Pyjo.Test.Pyjo.new(examples.child('mount_cgi.py'))

with subtest('Pyjoyment'):
    t.get_ok('/').status_is(200).content_is('I ♥ Pyjoyment!')

with subtest('CGI'):
    t.get_ok('/cgi-bin/hello.py').status_is(200).content_type_is('text/plain; charset=UTF-8')
    t.content_is('Hello CGI at /cgi-bin/hello.py for !\n')
    t.get_ok('/cgi-bin/hello.py/foo/bar?name=Pyjoyment').status_is(200)
    t.content_is('Hello Pyjoyment at /cgi-bin/hello.py for /foo/bar!\n')
    t.get_ok('/cgi-bin/missing.py').status_is(404)

done_testing()
