import Pyjo.Test.Pyjo

from Pyjo.File import curfile
from Pyjo.Test import *


# The application of examples/mount_asgi_inception.py, which the test loads without starting a server
t = Pyjo.Test.Pyjo.new(
    curfile().dirname().dirname().dirname().sibling('examples', 'pyjoyment', 'mount_asgi_inception.py')
)

with subtest('Pyjoyment.Lite'):
    t.get_ok('/').status_is(200).content_is('I ♥ Pyjoyment!')

with subtest('Pyjoyment on ASGI'):
    t.get_ok('/asgi').status_is(200).content_is('Hello Pyjoyment at /asgi on ASGI!')
    t.get_ok('/asgi/').status_is(200).content_is('Hello Pyjoyment at /asgi on ASGI!')
    t.get_ok('/asgi/pyjo/pyjo.css').status_is(200).content_type_is('text/css')
    t.get_ok('/asgi/foo').status_is(404)

done_testing()
