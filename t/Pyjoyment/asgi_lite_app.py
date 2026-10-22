import Pyjo.App.ASGI
import Pyjo.File
import Pyjo.Test.Pyjo
import Pyjoyment

from Pyjo.Test import *
from Pyjoyment.Lite import app, get, plugin

import sys


# The modules of the applications are in a temporary directory, as a test writes nothing into t
tmp = Pyjo.File.tempdir()
tmp.child('asgi_hello.py').spew(b"""\
async def app(scope, receive, send):
    body = f"Hello from {scope['root_path']} and {scope['path']}!".encode()
    await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/plain')]})
    await send({'type': 'http.response.body', 'body': body})


class handlers:
    @staticmethod
    async def app(scope, receive, send):
        await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/plain')]})
        await send({'type': 'http.response.body', 'body': b'Hello from handlers!'})
""")
sys.path.insert(0, tmp.to_str())


async def hello(scope, receive, send):
    host = dict(scope['headers'])[b'host'].decode()
    await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/plain')]})
    await send({'type': 'http.response.body', 'body': f'Hello from {host}{scope["path"]}!'.encode()})


# An application whose __call__ is a coroutine function, as the one of Starlette
class Callable:
    async def __call__(self, scope, receive, send):
        await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/plain')]})
        await send({'type': 'http.response.body', 'body': b'Hello from an object!'})


class MyApp(Pyjoyment.object):
    def startup(self):
        self.routes.get('/').to(cb=lambda c: c.render(text='Hello from MyApp!'))


# Silence
app.log.level = 'fatal'

get('/', lambda c: c.render(text='Hello from the main app!'))

route = plugin('Mount', {'/function': hello})
embedded = route.pattern.defaults['app']
plugin('Mount', {'/object': Callable()})
plugin('Mount', {'/module': 'asgi_hello:app'})
plugin('Mount', {'/attribute': 'asgi_hello:handlers.app'})
plugin('Mount', {'example.com/host': hello})
plugin('Mount', {'/wrapped': Pyjo.App.ASGI.new(app=hello)})
plugin('Mount', {'/myapp': MyApp.new()})

t = Pyjo.Test.Pyjo.new()

with subtest('Main application'):
    t.get_ok('/').status_is(200).content_is('Hello from the main app!')

with subtest('ASGI application as a function'):
    ok(isinstance(embedded, Pyjo.App.ASGI.object), 'ASGI application')
    ok(embedded.app is hello, 'right application')
    ok(embedded.log is app.log, 'same log')
    t.get_ok('/function').status_is(200).content_like(r'^Hello from 127\.0\.0\.1:\d+/function!$')
    t.get_ok('/function/foo/bar').status_is(200).content_like(r'^Hello from 127\.0\.0\.1:\d+/function/foo/bar!$')

with subtest('ASGI application as an object'):
    t.get_ok('/object').status_is(200).content_is('Hello from an object!')

with subtest('ASGI application as the name of a module and its attribute'):
    t.get_ok('/module/foo').status_is(200).content_is('Hello from /module and /module/foo!')
    t.get_ok('/attribute').status_is(200).content_is('Hello from handlers!')

with subtest('ASGI application with host'):
    t.get_ok('/host/foo', {'Host': 'example.com'}).status_is(200).content_is('Hello from example.com/host/foo!')
    t.get_ok('/host/foo', {'Host': 'example.org'}).status_is(404)

with subtest('ASGI application in its adapter'):
    t.get_ok('/wrapped/foo').status_is(200).content_like(r'/wrapped/foo!$')

with subtest('Application object'):
    t.get_ok('/myapp').status_is(200).content_is('Hello from MyApp!')

with subtest('Lifespan of a mounted application'):
    import Pyjo.Server.Daemon

    events = []

    async def lifespan(scope, receive, send):
        if scope['type'] == 'lifespan':
            while True:
                message = await receive()
                events.append(message['type'])
                if message['type'] == 'lifespan.startup':
                    scope['state']['greeting'] = 'Hello'
                    await send({'type': 'lifespan.startup.complete'})
                else:
                    return await send({'type': 'lifespan.shutdown.complete'})
        await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/plain')]})
        await send({'type': 'http.response.body', 'body': f'{scope["state"]["greeting"]} with a lifespan!'.encode()})

    mounting = Pyjoyment.new()
    mounting.log.level = 'fatal'
    mounting.plugin('Mount', {'/lifespan': lifespan})
    t2 = Pyjo.Test.Pyjo.new(mounting)
    t2.get_ok('/lifespan').status_is(200).content_is('Hello with a lifespan!')
    is_deeply_ok(events, ['lifespan.startup'], 'started by the first request')

    # The end of the server of the application that mounts it
    promise = mounting.server_stopped(Pyjo.Server.Daemon.new())
    ok(promise is not None, 'cleanup to wait for')
    promise.wait()
    is_deeply_ok(events, ['lifespan.startup', 'lifespan.shutdown'], 'shut down by the end of the server')
    is_ok(mounting.server_stopped(Pyjo.Server.Daemon.new()), None, 'nothing to wait for')

done_testing()
