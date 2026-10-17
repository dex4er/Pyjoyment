import Pyjoyment
import Pyjoyment.Command.version

from Pyjo.Test import *

import contextlib
import io


with subtest('Synopsis'):
    app = Pyjoyment.new()
    version = Pyjoyment.Command.version.new(app=app)
    like_ok(version.usage, r'^Usage: APPLICATION version \[OPTIONS\]\n\n  pyjo version\n', 'usage')

    # The latest version from the application itself, as a test does not ask PyPI
    app.log.level = 'fatal'
    app.ua.server.app = app

    @app.ua.once('start')
    def start(ua, tx):
        tx.req.via_proxy = False
        tx.req.url = ua.server.url().set(path='/')

    app.routes.get('/', lambda c: c.render(json={'info': {'version': '0.0.0'}}))
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        version.run()
    like_ok(buffer.getvalue(), r'(?s)^CORE\n  Python .*\n  Pyjoyment .*\nOPTIONAL\n  Reactor ', 'versions')
    like_ok(buffer.getvalue(), r'Thanks for testing a development release, you are awesome!', 'latest version')

with subtest('Attributes'):
    is_ok(Pyjoyment.Command.version.new().description, 'Show versions of available modules', 'description')

done_testing()
