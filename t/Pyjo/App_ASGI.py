import Pyjo.App.ASGI
import Pyjo.IOLoop
import Pyjo.Promise
import Pyjo.Reactor
import Pyjo.Server.ASGI
import Pyjo.Test.Pyjo
import Pyjo.Transaction.HTTP
import Pyjoyment

from Pyjo.JSON import encode_json
from Pyjo.Test import *

import asyncio
import concurrent.futures
import http.client
import os
import re


# The connection scope of the request, and the messages of the body that the application receives
async def echo(scope, receive, send):
    messages = []
    while True:
        message = await receive()
        messages.append({**message, 'body': message['body'].decode('latin-1')})
        if not message['more_body']:
            break
    values = {
        **scope,
        'headers': [[name.decode('latin-1'), value.decode('latin-1')] for name, value in scope['headers']],
        'raw_path': scope['raw_path'].decode('latin-1'),
        'query_string': scope['query_string'].decode('latin-1'),
    }
    body = encode_json({**values, 'messages': messages})
    await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'application/json')]})
    await send({'type': 'http.response.body', 'body': body})


# The value of a promise, which the event loop fulfills
def result(promise):
    values = []
    promise.then(lambda *args: values.extend(args)).wait()
    return values[0] if len(values) == 1 else values


# The response as it is on the wire, as the user agent removes the chunked transfer encoding
def raw(t, method, path='/'):
    url = t.ua.server.url()

    def request():
        connection = http.client.HTTPConnection(url.host, url.port, timeout=5)
        try:
            connection.request(method, path)
            res = connection.getresponse()
            try:
                body = res.read()
            except http.client.IncompleteRead:
                body = None
            return res.status, res.getheader('Content-Length'), res.getheader('Transfer-Encoding'), body
        finally:
            connection.close()

    with concurrent.futures.ThreadPoolExecutor(1) as executor:
        return result(Pyjo.Promise.new(executor.submit(request)))


def application(asgi, prefix='/prefix'):
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    route = app.routes.any(prefix)
    route.partial = True
    route.to(app=asgi)
    return app


def header(scope, name):
    return [value for key, value in scope['headers'] if key == name]


with subtest('Scope'):
    with Pyjo.App.ASGI.new(app=echo) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/foo/bar?a=1&b=%20', {'X-Foo': 'bar'}).status_is(200)
        scope = t.tx.res.json()
        is_ok(scope['type'], 'http', 'right type')
        is_deeply_ok(scope['asgi'], {'version': '3.0', 'spec_version': '2.4'}, 'right version')
        is_ok(scope['http_version'], '1.1', 'right HTTP version')
        is_ok(scope['method'], 'GET', 'right method')
        is_ok(scope['scheme'], 'http', 'right scheme')
        is_ok(scope['root_path'], '', 'no root path')
        is_ok(scope['path'], '/foo/bar', 'right path')
        is_ok(scope['raw_path'], '/foo/bar', 'right raw path')
        is_ok(scope['query_string'], 'a=1&b=%20', 'right query')
        is_deeply_ok(scope['server'], ['127.0.0.1', t.ua.server.url().port], 'right server')
        is_ok(scope['client'][0], '127.0.0.1', 'right client address')
        ok(isinstance(scope['client'][1], int), 'client port')
        is_deeply_ok(header(scope, 'x-foo'), ['bar'], 'right header')
        is_deeply_ok(header(scope, 'content-length'), [], 'no content length')
        is_deeply_ok(scope['messages'], [{'type': 'http.request', 'body': '', 'more_body': False}], 'no body')

with subtest('Headers'):
    with Pyjo.App.ASGI.new(app=echo) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/', {'X-Foo': ['a', 'b']}).status_is(200)
        is_deeply_ok(header(t.tx.res.json(), 'x-foo'), ['a', 'b'], 'every value')

with subtest('Body'):
    with Pyjo.App.ASGI.new(app=echo) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.post_ok('/', {'Content-Type': 'text/plain'}, b'Hello!').status_is(200)
        scope = t.tx.res.json()
        is_deeply_ok(header(scope, 'content-type'), ['text/plain'], 'right content type')
        is_deeply_ok(header(scope, 'content-length'), ['6'], 'right content length')
        is_deeply_ok(scope['messages'], [{'type': 'http.request', 'body': 'Hello!', 'more_body': False}], 'right body')

        # Chunked
        tx = t.ua.build_tx('POST', '/')
        tx.req.content.write_chunk(b'Hello').write_chunk(b' World!').write_chunk(b'')
        t.request_ok(tx).status_is(200)
        scope = t.tx.res.json()
        is_deeply_ok(header(scope, 'content-length'), ['12'], 'right content length')
        is_deeply_ok(header(scope, 'transfer-encoding'), [], 'no transfer encoding')
        is_ok(''.join(message['body'] for message in scope['messages']), 'Hello World!', 'right body')

        # Multipart
        t.post_ok('/', form={'foo': 'bar', 'file': {'content': 'Hello!', 'filename': 'hello.txt'}}).status_is(200)
        scope = t.tx.res.json()
        like_ok(header(scope, 'content-type')[0], r'^multipart/form-data; boundary=', 'right content type')
        body = ''.join(message['body'] for message in scope['messages'])
        is_deeply_ok(header(scope, 'content-length'), [str(len(body))], 'right content length')
        like_ok(body, r'(?s)name=\"file\"; filename=\"hello\.txt\".*Hello!', 'right file')

with subtest('Body in a file'):
    max_memory_size = os.environ.get('PYJO_MAX_MEMORY_SIZE')
    os.environ['PYJO_MAX_MEMORY_SIZE'] = '10'
    try:
        with Pyjo.App.ASGI.new(app=echo) as app:
            t = Pyjo.Test.Pyjo.new(app)
            body = b'0123456789' * 100000
            t.post_ok('/', body).status_is(200)
            messages = t.tx.res.json('/messages')
            ok(len(messages) > 1, 'body in more than one message')
            ok(all(message['more_body'] for message in messages[:-1]), 'more body')
            is_ok(messages[-1]['more_body'], False, 'end of the body')
            ok(''.join(message['body'] for message in messages) == body.decode(), 'right body')
    finally:
        if max_memory_size is None:
            del os.environ['PYJO_MAX_MEMORY_SIZE']
        else:
            os.environ['PYJO_MAX_MEMORY_SIZE'] = max_memory_size

with subtest('Path of a route'):
    with Pyjo.App.ASGI.new(app=echo) as asgi:
        t = Pyjo.Test.Pyjo.new(application(asgi))
        t.get_ok('/prefix').status_is(200)
        is_ok(t.tx.res.json('/root_path'), '/prefix', 'right root path')
        is_ok(t.tx.res.json('/path'), '/prefix', 'right path')
        t.get_ok('/prefix/foo/bar/?x=1').status_is(200)
        is_ok(t.tx.res.json('/root_path'), '/prefix', 'right root path')
        is_ok(t.tx.res.json('/path'), '/prefix/foo/bar/', 'right path')
        is_ok(t.tx.res.json('/query_string'), 'x=1', 'right query')

        # Not after a part of the path that does not end with a slash, which cannot be root_path
        t.get_ok('/prefixx').status_is(404)
        t.get_ok('/prefix.json').status_is(404)

        # Escaped, as UTF-8, and as they are on the wire in the raw path
        t.get_ok('/prefix/a%20b/%E2%99%A5/%2F').status_is(200)
        is_ok(t.tx.res.json('/path'), '/prefix/a b/♥//', 'right path')
        is_ok(t.tx.res.json('/raw_path'), '/prefix/a%20b/%E2%99%A5/%2F', 'right raw path')

    # Placeholders
    with Pyjo.App.ASGI.new(app=echo) as asgi:
        t = Pyjo.Test.Pyjo.new(application(asgi, '/users/:id'))
        t.get_ok('/users/%E2%99%A5/foo').status_is(200)
        is_ok(t.tx.res.json('/root_path'), '/users/♥', 'right root path')
        is_ok(t.tx.res.json('/path'), '/users/♥/foo', 'right path')

with subtest('Base path'):
    # A reverse proxy with a path prefix, which the application moves from the path to the base path
    with Pyjo.App.ASGI.new(app=echo) as asgi:
        app = application(asgi)

        @app.hook('before_dispatch')
        def before_dispatch(c):
            url = c.req.url
            url.base.path.parse('/outer/')
            url.path.leading_slash = False
            url.path.parts.pop(0)

        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/outer/prefix/foo?x=1').status_is(200)
        is_ok(t.tx.res.json('/root_path'), '/outer/prefix', 'right root path')
        is_ok(t.tx.res.json('/path'), '/outer/prefix/foo', 'right path')


async def whole(scope, receive, send):
    headers = [(b'content-type', b'text/plain'), (b'x-foo', b'a'), (b'x-foo', b'b')]
    await send({'type': 'http.response.start', 'status': 201, 'headers': headers})
    await send({'type': 'http.response.body', 'body': b'Hello World!'})


async def stream(scope, receive, send):
    await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/plain')]})
    for chunk in (b'one', b'', b'two', b'three'):
        await send({'type': 'http.response.body', 'body': chunk, 'more_body': True})
    await send({'type': 'http.response.body', 'body': b''})


async def length(scope, receive, send):
    headers = [(b'content-type', b'text/plain'), (b'content-length', b'6')]
    await send({'type': 'http.response.start', 'status': 200, 'headers': headers})
    await send({'type': 'http.response.body', 'body': b'one', 'more_body': True})
    await send({'type': 'http.response.body', 'body': b'two'})


with subtest('Response'):
    with Pyjo.App.ASGI.new(app=whole) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/').status_is(201).content_is('Hello World!')
        is_deeply_ok(t.tx.res.headers.every_header('X-Foo'), ['a', 'b'], 'right headers')
        is_deeply_ok(raw(t, 'GET'), (201, '12', None, b'Hello World!'), 'whole response')
        is_deeply_ok(raw(t, 'HEAD'), (201, '12', None, b''), 'whole response without content')

    with Pyjo.App.ASGI.new(app=stream) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/').status_is(200).content_is('onetwothree')
        is_deeply_ok(raw(t, 'GET'), (200, None, 'chunked', b'onetwothree'), 'chunked response')
        is_deeply_ok(raw(t, 'HEAD'), (200, None, 'chunked', b''), 'chunked response without content')

        # Without the chunked transfer encoding in HTTP/1.0
        tx = t.ua.build_tx('GET', '/')
        tx.req.version = '1.0'
        t.request_ok(tx).status_is(200).content_is('onetwothree')
        is_ok(t.tx.keep_alive, False, 'no keep-alive')

    with Pyjo.App.ASGI.new(app=length) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/').status_is(200).content_is('onetwo')
        is_ok(t.tx.keep_alive, True, 'keep-alive')
        is_deeply_ok(raw(t, 'GET'), (200, '6', None, b'onetwo'), 'response with its length')


async def fail(scope, receive, send):
    raise RuntimeError('Something went wrong')


async def silent(scope, receive, send):
    pass


async def started(scope, receive, send):
    await send({'type': 'http.response.start', 'status': 200, 'headers': []})


async def twice(scope, receive, send):
    await send({'type': 'http.response.start', 'status': 200, 'headers': []})
    await send({'type': 'http.response.start', 'status': 200, 'headers': []})


async def unknown(scope, receive, send):
    await send({'type': 'http.response.unknown'})


async def broken(scope, receive, send):
    await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/plain')]})
    await send({'type': 'http.response.body', 'body': b'one', 'more_body': True})
    raise RuntimeError('Broken body')


async def after(scope, receive, send):
    await send({'type': 'http.response.start', 'status': 500, 'headers': [(b'content-type', b'text/plain')]})
    await send({'type': 'http.response.body', 'body': b'Failed'})
    raise RuntimeError('After the response')


async def unfinished(scope, receive, send):
    await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/plain')]})
    await send({'type': 'http.response.body', 'body': b'one', 'more_body': True})


with subtest('Errors'):
    for application_, error in (
        (fail, r'Something went wrong'),
        (silent, r'returned without a response'),
        (started, r'returned without a response'),
        (twice, r'"http\.response\.start" has already been sent'),
        (unknown, r'Unknown ASGI message "http\.response\.unknown"'),
    ):
        with Pyjo.App.ASGI.new(app=application_) as app:
            app.log.level = 'fatal'
            t = Pyjo.Test.Pyjo.new(app)
            with app.log.capture('error') as messages:
                t.get_ok('/').status_is(500).content_is('Internal Server Error')
            like_ok(str(messages), error, f'right error of {application_.__name__}')

    # The connection is closed, as the response has started
    for application_, error in ((broken, r'Broken body'), (unfinished, r'without the end of its response')):
        with Pyjo.App.ASGI.new(app=application_) as app:
            app.log.level = 'fatal'
            t = Pyjo.Test.Pyjo.new(app)
            with app.log.capture('error') as messages:
                is_deeply_ok(
                    raw(t, 'GET'), (200, None, 'chunked', None), f'incomplete response of {application_.__name__}'
                )
            like_ok(str(messages), error, f'right error of {application_.__name__}')

    # The response that has ended is written
    with Pyjo.App.ASGI.new(app=after) as app:
        app.log.level = 'fatal'
        t = Pyjo.Test.Pyjo.new(app)
        with app.log.capture('error') as messages:
            t.get_ok('/').status_is(500).content_is('Failed')
        like_ok(str(messages), r'After the response', 'right error of after')

    # The exception page of Pyjoyment, in a route
    with Pyjo.App.ASGI.new(app=fail) as asgi:
        t = Pyjo.Test.Pyjo.new(application(asgi))
        t.get_ok('/prefix').status_is(500).content_like(r'Something went wrong')

    throws_ok(
        lambda: Pyjo.App.ASGI.new().handler(Pyjo.Transaction.HTTP.new()),
        re.compile(r'^No ASGI application'),
        'no application',
    )

with subtest('Connection closed'):
    sent = []
    events = []

    async def endless(scope, receive, send):
        await receive()
        await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/plain')]})
        for _ in range(100):
            await send({'type': 'http.response.body', 'body': b'x' * 1024, 'more_body': True})
            sent.append(1)
        events.append((await receive())['type'])

    with Pyjo.App.ASGI.new(app=endless) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.ua.max_response_size = 10000
        tx = t.ua.get('/')
        is_ok(tx.error['message'], 'Maximum message size exceeded', 'right error')
        while not events:
            Pyjo.IOLoop.one_tick()
        is_ok(len(sent), 100, 'send does nothing once the connection is gone')
        is_deeply_ok(events, ['http.disconnect'], 'disconnect')

with subtest('Disconnect after the response'):
    events = []

    async def disconnect(scope, receive, send):
        await receive()
        await send({'type': 'http.response.start', 'status': 200, 'headers': []})
        await send({'type': 'http.response.body', 'body': b'Hello!'})
        events.append((await receive())['type'])

    with Pyjo.App.ASGI.new(app=disconnect) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/').status_is(200).content_is('Hello!')
        while not events:
            Pyjo.IOLoop.one_tick()
        is_deeply_ok(events, ['http.disconnect'], 'disconnect')

with subtest('Pyjoyment on ASGI'):
    # An application of Pyjoyment as the ASGI application, whose response and content come in later ticks of the event
    # loop
    inner = Pyjoyment.new()
    inner.log.level = 'fatal'

    @inner.routes.get('/later')
    def later(c):
        c.render_later()
        Pyjo.IOLoop.timer(0.01, lambda loop: c.render(text=f'Hello later at {c.url_for("/")}!'))

    @inner.routes.get('/chunks')
    def chunks(c):
        def write(n):
            if n < 3:
                Pyjo.IOLoop.timer(0.01, lambda loop: c.write_chunk(f'{n}'.encode(), lambda c: write(n + 1)))
            else:
                c.finish()

        write(0)

    with Pyjo.App.ASGI.new(app=Pyjo.Server.ASGI.new(app=inner).to_asgi_app()) as asgi:
        t = Pyjo.Test.Pyjo.new(application(asgi))
        t.get_ok('/prefix/later').status_is(200).content_is('Hello later at /prefix!')
        t.get_ok('/prefix/chunks').status_is(200).content_is('012')
        t.get_ok('/prefix/missing').status_is(404)

with subtest('Event loop of asyncio'):

    async def sleepy(scope, receive, send):
        await asyncio.sleep(0.01)
        await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/plain')]})
        await send({'type': 'http.response.body', 'body': b'Hello after a sleep!'})

    with Pyjo.App.ASGI.new(app=sleepy) as app:
        app.log.level = 'fatal'
        t = Pyjo.Test.Pyjo.new(app)

        # Not on another reactor, which drives a coroutine that awaits only the promises of Pyjoyment
        if Pyjo.Reactor.detect() != 'Pyjo.Reactor.Asyncio':
            with app.log.capture('error') as messages:
                t.get_ok('/').status_is(500)
            like_ok(str(messages), r'no running event loop|cannot wait for', 'right error')
        else:
            t.get_ok('/').status_is(200).content_is('Hello after a sleep!')

done_testing()
