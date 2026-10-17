import Pyjoyment
import Pyjoyment.Command.eval

from Pyjo.Test import *

import contextlib
import io


with subtest('Synopsis'):
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    app.routes.get('/', {'text': 'Hello!'})
    # The application of the user agent, as Pyjoyment.Lite makes the one of its script
    app.ua.server.app = app
    eval_ = Pyjoyment.Command.eval.new(app=app)
    like_ok(eval_.usage, r'^Usage: APPLICATION eval \[OPTIONS\] CODE\n', 'usage')
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        eval_.run('print(app.ua.get("/").result.body)')
    is_ok(buffer.getvalue(), "b'Hello!'\n", 'request')
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        eval_.run('print(*sorted(app.renderer.helpers), sep="\\n")')
    like_ok(buffer.getvalue(), r'\ndumper\n', 'helpers')
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        eval_.run('-v', 'app.home')
    is_ok(buffer.getvalue(), f'{app.home}\n', 'verbose')
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        eval_.run('-V', 'app.renderer.paths')
    is_ok(buffer.getvalue(), app.dumper(app.renderer.paths), 'data structure')

with subtest('Description'):
    app = Pyjoyment.new()
    eval_ = Pyjoyment.Command.eval.new(app=app)
    is_ok(eval_.run('x = 1\nx + 1'), 2, 'value of the last expression')
    is_ok(eval_.run('x = 1'), None, 'no expression')
    is_ok(eval_.run('import Pyjo.Promise; Pyjo.Promise.resolve(3)'), 3, 'promise')

with subtest('Attributes'):
    is_ok(Pyjoyment.Command.eval.new().description, 'Run code against application', 'description')

done_testing()
