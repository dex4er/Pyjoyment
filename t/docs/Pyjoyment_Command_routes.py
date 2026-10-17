import Pyjoyment
import Pyjoyment.Command.routes

from Pyjo.Test import *

import contextlib
import io


with subtest('Synopsis'):
    app = Pyjoyment.new()
    app.routes.get('/foo').set(name='foo')
    routes = Pyjoyment.Command.routes.new(app=app)
    like_ok(routes.usage, r'^Usage: APPLICATION routes \[OPTIONS\]\n\n  \./myapp\.py routes\n', 'usage')
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        routes.run()
    like_ok(buffer.getvalue(), r'^/foo +GET +"foo"\n', 'routes')
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        routes.run('-v')
    like_ok(buffer.getvalue(), r'^/foo +\.\.\.\. +GET +"foo" +\^/foo', 'verbose')

with subtest('Attributes'):
    is_ok(Pyjoyment.Command.routes.new().description, 'Show available routes', 'description')

done_testing()
