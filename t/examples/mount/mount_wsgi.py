import Pyjo.App.WSGI
import Pyjo.Test.Pyjo

from Pyjo.File import curfile
from Pyjo.Test import *

import sys

from wsgiref.validate import validator


# The application of examples/mount/mount_wsgi.py, which the test loads without starting a server, with the directory of the
# script in sys.path, as Python has it when it runs the script, so that hello_wsgi.py is found
examples = curfile().dirname().dirname().dirname().sibling('examples', 'mount')
sys.path.insert(0, examples.to_str())
t = Pyjo.Test.Pyjo.new(examples.child('mount_wsgi.py'))

with subtest('Pyjoyment'):
    t.get_ok('/').status_is(200).content_is('I ♥ Pyjoyment!')

with subtest('WSGI'):
    t.get_ok('/wsgi').status_is(200).content_type_is('text/plain').content_is('Hello WSGI at /wsgi for !')
    t.get_ok('/wsgi/foo/bar').status_is(200).content_is('Hello WSGI at /wsgi for /foo/bar!')
    t.get_ok('/foo').status_is(404)

with subtest('WSGI on its own'):
    import hello_wsgi  # pyright: ignore[reportMissingImports]

    with Pyjo.App.WSGI.new(app=validator(hello_wsgi.app)) as app:
        Pyjo.Test.Pyjo.new(app).get_ok('/foo').status_is(200).content_is('Hello WSGI at  for /foo!')

done_testing()
