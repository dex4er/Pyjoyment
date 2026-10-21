import Pyjo.Test.Pyjo

from Pyjo.File import curfile
from Pyjo.Test import *


# The application of examples/mount_wsgi_inception.py, which the test loads without starting a server
t = Pyjo.Test.Pyjo.new(
    curfile().dirname().dirname().dirname().sibling('examples', 'pyjoyment', 'mount_wsgi_inception.py')
)

with subtest('Pyjoyment.Lite'):
    t.get_ok('/').status_is(200).content_is('I ♥ Pyjoyment!')

with subtest('Pyjoyment on WSGI'):
    t.get_ok('/wsgi').status_is(200).content_is('Hello Pyjoyment at /wsgi on WSGI!')
    t.get_ok('/wsgi/').status_is(200).content_is('Hello Pyjoyment at /wsgi on WSGI!')
    t.get_ok('/wsgi/pyjo/pyjo.css').status_is(200).content_type_is('text/css')
    t.get_ok('/wsgi/foo').status_is(404)

done_testing()
