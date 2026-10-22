import Pyjo.App.ASGI
import Pyjo.Test.Pyjo

from Pyjo.File import curfile
from Pyjo.Test import *

import sys


# The application of examples/mount/mount_asgi.py, which the test loads without starting a server, with the directory of the
# script in sys.path, as Python has it when it runs the script, so that hello_asgi.py is found
examples = curfile().dirname().dirname().dirname().sibling('examples', 'mount')
sys.path.insert(0, examples.to_str())
t = Pyjo.Test.Pyjo.new(examples.child('mount_asgi.py'))

with subtest('Pyjoyment'):
    t.get_ok('/').status_is(200).content_is('I ♥ Pyjoyment!')

with subtest('ASGI'):
    t.get_ok('/asgi').status_is(200).content_type_is('text/plain').content_is('Hello ASGI at /asgi for /asgi!')
    t.get_ok('/asgi/foo/bar').status_is(200).content_is('Hello ASGI at /asgi for /asgi/foo/bar!')
    t.get_ok('/asgi/events').status_is(200).content_type_is('text/event-stream')
    t.content_is('data: 0\n\ndata: 1\n\ndata: 2\n\n')
    t.get_ok('/foo').status_is(404)

with subtest('ASGI on its own'):
    import hello_asgi  # pyright: ignore[reportMissingImports]

    with Pyjo.App.ASGI.new(app=hello_asgi.app) as app:
        Pyjo.Test.Pyjo.new(app).get_ok('/foo').status_is(200).content_is('Hello ASGI at  for /foo!')

done_testing()
