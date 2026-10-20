import Pyjo.Server.ASGI

from Pyjo.Test import *

import asyncio
import importlib
import inspect
import os
import sys


# The ASGI server of the tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
ASGIClient = importlib.import_module('ASGIClient')


with subtest('Synopsis'):
    from Pyjo.Server.ASGI import ASGI

    asgi = ASGI()
    asgi.unsubscribe('request')

    @asgi.on('request')
    def request(asgi, tx):
        # Request
        method = tx.req.method
        path = tx.req.url.path

        # Response
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = f'{method} request for {path}!'.encode()

        # Resume transaction
        tx.resume()

    app = asgi.to_asgi_app()

    status, headers, body = ASGIClient.response(ASGIClient.run(app, *ASGIClient.http('GET', '/foo')))
    is_ok(status, 200, 'right status')
    is_ok(headers['content-type'], 'text/plain', 'right "Content-Type" value')
    is_ok(body, b'GET request for /foo!', 'right content')

    # Or import the module, as in Google Python Style Guide
    import Pyjo.Server.ASGI

    asgi = Pyjo.Server.ASGI.new()
    asgi.unsubscribe('request')

    # F811 "Redefinition of unused `request`": the synopsis defines it in both forms
    @asgi.on('request')
    def request(asgi, tx):  # noqa: F811
        # Request
        method = tx.req.method
        path = tx.req.url.path

        # Response
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = f'{method} request for {path}!'.encode()

        # Resume transaction
        tx.resume()

    app = asgi.to_asgi_app()

    status, headers, body = ASGIClient.response(ASGIClient.run(app, *ASGIClient.http('GET', '/foo')))
    is_ok(status, 200, 'right status')
    is_ok(headers['content-type'], 'text/plain', 'right "Content-Type" value')
    is_ok(body, b'GET request for /foo!', 'right content')

with subtest('run'):
    asgi = Pyjo.Server.ASGI.new()
    scope, messages = ASGIClient.http('GET', '/')

    async def receive():
        return messages.pop(0)

    sent = []

    async def send(message):
        sent.append(message)

    ok(inspect.iscoroutinefunction(asgi.run), 'coroutine')
    asyncio.run(asgi.run(scope, receive, send))
    is_ok(sent[0]['status'], 200, 'response sent')

with subtest('to_asgi_app'):
    asgi = Pyjo.Server.ASGI.new()
    app = asgi.to_asgi_app()
    ok(inspect.iscoroutinefunction(app), 'ASGI application')
    status, headers, body = ASGIClient.response(ASGIClient.run(app, *ASGIClient.http('GET', '/')))
    is_ok(body, b'Your Pyjo is working!', 'default application')

done_testing()
