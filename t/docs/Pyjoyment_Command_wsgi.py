import Pyjoyment
import Pyjoyment.Command.wsgi

from Pyjo.Test import *

import io
import os
import wsgiref.util


with subtest('Synopsis'):
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    app.routes.get('/', {'text': 'Hello WSGI!'})
    wsgi = Pyjoyment.Command.wsgi.new(app=app)
    like_ok(wsgi.usage, r"^Usage: APPLICATION wsgi \[OPTIONS\]\n\n  application = app\.start\('wsgi'\)\n", 'usage')

    application = app.start('wsgi')
    environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'wsgi.input': io.BytesIO()}
    wsgiref.util.setup_testing_defaults(environ)
    statuses = []
    body = b''.join(application(environ, lambda status, headers, exc_info=None: statuses.append(status)))
    is_deeply_ok(statuses, ['200 OK'], 'status')
    is_ok(body, b'Hello WSGI!', 'body')

with subtest('Description'):
    app = Pyjoyment.new()
    os.environ['PYJO_WSGI'] = '1'
    try:
        ok(callable(app.start('daemon', '--whatever')), 'detected, whatever the arguments are')
    finally:
        del os.environ['PYJO_WSGI']

with subtest('Attributes'):
    is_ok(Pyjoyment.Command.wsgi.new().description, 'Start application with WSGI', 'description')

done_testing()
