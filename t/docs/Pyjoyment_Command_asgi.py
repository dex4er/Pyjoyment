import Pyjoyment
import Pyjoyment.Command.asgi

from Pyjo.Test import *

import asyncio
import os


with subtest('Synopsis'):
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    app.routes.get('/', {'text': 'Hello ASGI!'})
    asgi = Pyjoyment.Command.asgi.new(app=app)
    like_ok(asgi.usage, r"^Usage: APPLICATION asgi \[OPTIONS\]\n\n  application = app\.start\('asgi'\)\n", 'usage')

    application = app.start('asgi')
    scope = {
        'type': 'http',
        'method': 'GET',
        'path': '/',
        'raw_path': b'/',
        'query_string': b'',
        'headers': [],
        'http_version': '1.1',
        'scheme': 'http',
        'server': ('127.0.0.1', 80),
        'client': ('127.0.0.1', 1234),
    }
    messages = []

    async def receive():
        return {'type': 'http.request', 'body': b'', 'more_body': False}

    async def send(message):
        messages.append(message)

    asyncio.run(application(scope, receive, send))
    is_ok(messages[0]['status'], 200, 'status')
    is_ok(b''.join(m.get('body', b'') for m in messages[1:]), b'Hello ASGI!', 'body')

with subtest('Description'):
    app = Pyjoyment.new()
    os.environ['PYJO_ASGI'] = '1'
    try:
        ok(callable(app.start('daemon', '--whatever')), 'detected, whatever the arguments are')
    finally:
        del os.environ['PYJO_ASGI']

with subtest('Attributes'):
    is_ok(Pyjoyment.Command.asgi.new().description, 'Start application with ASGI', 'description')

done_testing()
