import Pyjo.App.WSGI
import Pyjo.IOLoop
import Pyjo.Promise
import Pyjo.Test.Pyjo
import Pyjo.Transaction.HTTP
import Pyjoyment

from Pyjo.JSON import encode_json
from Pyjo.Test import *

import concurrent.futures
import http.client
import os
import re
import sys
import threading
import time
import warnings

from wsgiref.validate import validator


# The environment of the request without the objects of WSGI, and the body that the application reads
@validator
def echo(environ, start_response):
    body = environ['wsgi.input'].read(int(environ.get('CONTENT_LENGTH') or 0))
    values = {k: v for k, v in environ.items() if not k.startswith('wsgi.') or k == 'wsgi.url_scheme'}
    start_response('200 OK', [('Content-Type', 'application/json')])
    return [encode_json({**values, 'body': body.decode('latin-1')})]


# The value of a promise, which the event loop fulfills
def result(promise):
    values = []
    promise.then(lambda *args: values.extend(args)).wait()
    return values[0] if len(values) == 1 else values


# The event loop runs while a thread waits for the event
def wait(event):
    with concurrent.futures.ThreadPoolExecutor(1) as executor:
        return result(Pyjo.Promise.new(executor.submit(event.wait, 5)))


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


def application(wsgi, prefix='/prefix'):
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    route = app.routes.any(prefix)
    route.partial = True
    route.to(app=wsgi)
    return app


with subtest('Environment'):
    with Pyjo.App.WSGI.new(app=echo) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/foo/bar?a=1&b=%20', {'X-Foo': 'bar'}).status_is(200)
        env = t.tx.res.json()
        is_ok(env['REQUEST_METHOD'], 'GET', 'right method')
        is_ok(env['SCRIPT_NAME'], '', 'no script name')
        is_ok(env['PATH_INFO'], '/foo/bar', 'right path')
        is_ok(env['QUERY_STRING'], 'a=1&b=%20', 'right query')
        is_ok(env['SERVER_NAME'], '127.0.0.1', 'right server name')
        is_ok(env['SERVER_PORT'], str(t.ua.server.url().port), 'right server port')
        is_ok(env['SERVER_PROTOCOL'], 'HTTP/1.1', 'right protocol')
        is_ok(env['REMOTE_ADDR'], '127.0.0.1', 'right remote address')
        ok(env['REMOTE_PORT'].isdigit(), 'remote port')
        is_ok(env['HTTP_X_FOO'], 'bar', 'right header')
        is_ok(env['wsgi.url_scheme'], 'http', 'right scheme')
        ok('CONTENT_LENGTH' not in env, 'no content length')
        is_ok(env['body'], '', 'no body')

with subtest('Headers joined'):
    with Pyjo.App.WSGI.new(app=echo) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/', {'X-Foo': ['a', 'b'], 'Cookie': ['c=1', 'd=2']}).status_is(200)
        is_ok(t.tx.res.json('/HTTP_X_FOO'), 'a, b', 'joined with commas')
        is_ok(t.tx.res.json('/HTTP_COOKIE'), 'c=1; d=2', 'joined with semicolons')

with subtest('Body'):
    with Pyjo.App.WSGI.new(app=echo) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.post_ok('/', {'Content-Type': 'text/plain'}, b'Hello!').status_is(200)
        is_ok(t.tx.res.json('/CONTENT_TYPE'), 'text/plain', 'right content type')
        is_ok(t.tx.res.json('/CONTENT_LENGTH'), '6', 'right content length')
        is_ok(t.tx.res.json('/body'), 'Hello!', 'right body')

        # Chunked
        tx = t.ua.build_tx('POST', '/')
        tx.req.content.write_chunk(b'Hello').write_chunk(b' World!').write_chunk(b'')
        t.request_ok(tx).status_is(200)
        is_ok(t.tx.res.json('/CONTENT_LENGTH'), '12', 'right content length')
        ok('HTTP_TRANSFER_ENCODING' not in t.tx.res.json(), 'no transfer encoding')
        is_ok(t.tx.res.json('/body'), 'Hello World!', 'right body')

        # Multipart
        t.post_ok('/', form={'foo': 'bar', 'file': {'content': 'Hello!', 'filename': 'hello.txt'}}).status_is(200)
        env = t.tx.res.json()
        like_ok(env['CONTENT_TYPE'], r'^multipart/form-data; boundary=', 'right content type')
        is_ok(env['CONTENT_LENGTH'], str(len(env['body'])), 'right content length')
        like_ok(env['body'], r'(?s)name=\"file\"; filename=\"hello\.txt\".*Hello!', 'right file')
        like_ok(env['body'], r'(?s)name=\"foo\".*bar', 'right field')

with subtest('Body in a file'):
    max_memory_size = os.environ.get('PYJO_MAX_MEMORY_SIZE')
    os.environ['PYJO_MAX_MEMORY_SIZE'] = '10'
    try:
        with Pyjo.App.WSGI.new(app=echo) as app:
            t = Pyjo.Test.Pyjo.new(app)
            body = b'0123456789' * 100000
            t.post_ok('/', body).status_is(200)
            is_ok(t.tx.res.json('/CONTENT_LENGTH'), '1000000', 'right content length')
            ok(t.tx.res.json('/body') == body.decode(), 'right body')
    finally:
        if max_memory_size is None:
            del os.environ['PYJO_MAX_MEMORY_SIZE']
        else:
            os.environ['PYJO_MAX_MEMORY_SIZE'] = max_memory_size

with subtest('Path of a route'):
    with Pyjo.App.WSGI.new(app=echo) as wsgi:
        t = Pyjo.Test.Pyjo.new(application(wsgi))
        t.get_ok('/prefix').status_is(200)
        is_ok(t.tx.res.json('/SCRIPT_NAME'), '/prefix', 'right script name')
        is_ok(t.tx.res.json('/PATH_INFO'), '', 'no path')
        t.get_ok('/prefix/').status_is(200)
        is_ok(t.tx.res.json('/SCRIPT_NAME'), '/prefix', 'right script name')
        is_ok(t.tx.res.json('/PATH_INFO'), '/', 'right path')
        t.get_ok('/prefix/foo/bar/?x=1').status_is(200)
        is_ok(t.tx.res.json('/SCRIPT_NAME'), '/prefix', 'right script name')
        is_ok(t.tx.res.json('/PATH_INFO'), '/foo/bar/', 'right path')
        is_ok(t.tx.res.json('/QUERY_STRING'), 'x=1', 'right query')

        # Escaped, as the bytes of the path
        t.get_ok('/prefix/a%20b/%E2%99%A5/%2F').status_is(200)
        is_ok(t.tx.res.json('/SCRIPT_NAME'), '/prefix', 'right script name')
        is_ok(t.tx.res.json('/PATH_INFO'), '/a b/\xe2\x99\xa5//', 'right path')

    # Placeholders
    with Pyjo.App.WSGI.new(app=echo) as wsgi:
        t = Pyjo.Test.Pyjo.new(application(wsgi, '/users/:id'))
        t.get_ok('/users/%E2%99%A5/foo').status_is(200)
        is_ok(t.tx.res.json('/SCRIPT_NAME'), '/users/\xe2\x99\xa5', 'right script name')
        is_ok(t.tx.res.json('/PATH_INFO'), '/foo', 'right path')

    # A route that is not partial gives the whole path
    with Pyjo.App.WSGI.new(app=echo) as wsgi:
        app = Pyjoyment.new()
        app.log.level = 'fatal'
        app.routes.get('/whole').to(app=wsgi)
        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/whole').status_is(200)
        is_ok(t.tx.res.json('/SCRIPT_NAME'), '', 'no script name')
        is_ok(t.tx.res.json('/PATH_INFO'), '/whole', 'right path')

with subtest('Base path'):
    # A reverse proxy with a path prefix, which the application moves from the path to the base path
    with Pyjo.App.WSGI.new(app=echo) as wsgi:
        app = application(wsgi)

        @app.hook('before_dispatch')
        def before_dispatch(c):
            url = c.req.url
            url.base.path.parse('/outer/')
            url.path.leading_slash = False
            url.path.parts.pop(0)

        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/outer/prefix/foo?x=1').status_is(200)
        is_ok(t.tx.res.json('/SCRIPT_NAME'), '/outer/prefix', 'right script name')
        is_ok(t.tx.res.json('/PATH_INFO'), '/foo', 'right path')
        is_ok(t.tx.res.json('/QUERY_STRING'), 'x=1', 'right query')


# A list, without the validator, whose iterator would hide it
def whole(environ, start_response):
    start_response('201 Created', [('Content-Type', 'text/plain'), ('X-Foo', 'a'), ('X-Foo', 'b')])
    return [b'Hello', b' ', b'World!']


@validator
def stream(environ, start_response):
    # start_response once the body is iterated, and an empty chunk before the first one
    def body():
        start_response('200 OK', [('Content-Type', 'text/plain')])
        yield b''
        yield b'one'
        yield b'two'
        yield b'three'

    return body()


@validator
def length(environ, start_response):
    def body():
        yield b'one'
        yield b'two'

    start_response('200 OK', [('Content-Type', 'text/plain'), ('Content-Length', '6')])
    return body()


def written(environ, start_response):
    write = start_response('200 OK', [('Content-Type', 'text/plain')])
    write(b'one')
    write(b'two')
    return iter([b'three'])


with subtest('Response'):
    with Pyjo.App.WSGI.new(app=whole) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/').status_is(201).content_is('Hello World!')
        is_deeply_ok(t.tx.res.headers.every_header('X-Foo'), ['a', 'b'], 'right headers')
        is_deeply_ok(raw(t, 'GET'), (201, '12', None, b'Hello World!'), 'whole response')
        is_deeply_ok(raw(t, 'HEAD'), (201, '12', None, b''), 'whole response without content')

    with Pyjo.App.WSGI.new(app=stream) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/').status_is(200).content_is('onetwothree')
        is_deeply_ok(raw(t, 'GET'), (200, None, 'chunked', b'onetwothree'), 'chunked response')
        is_deeply_ok(raw(t, 'HEAD'), (200, None, 'chunked', b''), 'chunked response without content')

        # Without the chunked transfer encoding in HTTP/1.0
        tx = t.ua.build_tx('GET', '/')
        tx.req.version = '1.0'
        t.request_ok(tx).status_is(200).content_is('onetwothree')
        is_ok(t.tx.keep_alive, False, 'no keep-alive')

    with Pyjo.App.WSGI.new(app=length) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/').status_is(200).content_is('onetwo')
        is_ok(t.tx.keep_alive, True, 'keep-alive')
        is_deeply_ok(raw(t, 'GET'), (200, '6', None, b'onetwo'), 'response with its length')

    with Pyjo.App.WSGI.new(app=written) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/').status_is(200).content_is('onetwothree')


def fail(environ, start_response):
    raise RuntimeError('Something went wrong')


def silent(environ, start_response):
    return [b'Hello!']


def twice(environ, start_response):
    start_response('200 OK', [])
    start_response('200 OK', [])
    return [b'Hello!']


def replaced(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    try:
        raise RuntimeError('Something went wrong')
    except RuntimeError:
        start_response('503 Service Unavailable', [('Content-Type', 'text/plain')], sys.exc_info())
    return [b'Try again later']


def broken(environ, start_response):
    def body():
        yield b'one'
        raise RuntimeError('Broken body')

    start_response('200 OK', [('Content-Type', 'text/plain')])
    return body()


with subtest('Errors'):
    with Pyjo.App.WSGI.new(app=fail) as app:
        app.log.level = 'fatal'
        t = Pyjo.Test.Pyjo.new(app)
        with app.log.capture('error') as messages:
            t.get_ok('/').status_is(500).content_is('Internal Server Error')
        like_ok(str(messages), r'Something went wrong', 'right error')

    with Pyjo.App.WSGI.new(app=silent) as app:
        app.log.level = 'fatal'
        t = Pyjo.Test.Pyjo.new(app)
        with app.log.capture('error') as messages:
            t.get_ok('/').status_is(500)
        like_ok(str(messages), r'did not call start_response', 'right error')

    with Pyjo.App.WSGI.new(app=twice) as app:
        app.log.level = 'fatal'
        t = Pyjo.Test.Pyjo.new(app)
        with app.log.capture('error') as messages:
            t.get_ok('/').status_is(500)
        like_ok(str(messages), r'start_response has already been called', 'right error')

    with Pyjo.App.WSGI.new(app=replaced) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/').status_is(503).content_is('Try again later')

    # The connection is closed, as the response has started
    with Pyjo.App.WSGI.new(app=broken) as app:
        app.log.level = 'fatal'
        t = Pyjo.Test.Pyjo.new(app)
        with app.log.capture('error') as messages:
            is_deeply_ok(raw(t, 'GET'), (200, None, 'chunked', None), 'incomplete response')
        like_ok(str(messages), r'Broken body', 'right error')

    # The exception page of Pyjoyment, in a route
    with Pyjo.App.WSGI.new(app=fail) as wsgi:
        t = Pyjo.Test.Pyjo.new(application(wsgi))
        t.get_ok('/prefix').status_is(500).content_like(r'Something went wrong')

    throws_ok(
        lambda: Pyjo.App.WSGI.new().handler(Pyjo.Transaction.HTTP.new()),
        re.compile(r'^No WSGI application'),
        'no application',
    )

with subtest('Connection closed'):
    closed = threading.Event()

    def endless(environ, start_response):
        def body():
            try:
                while True:
                    yield b'x' * 1024
                    time.sleep(0.01)
            finally:
                closed.set()

        start_response('200 OK', [('Content-Type', 'text/plain')])
        return body()

    with Pyjo.App.WSGI.new(app=endless) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.ua.max_response_size = 10000
        tx = t.ua.get('/')
        is_ok(tx.error['message'], 'Maximum message size exceeded', 'right error')
        ok(wait(closed), 'body closed')

with subtest('Closed body'):
    closed = threading.Event()

    class Body:
        def __iter__(self):
            yield b'Hello!'

        def close(self):
            closed.set()

    def closing(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return Body()

    with Pyjo.App.WSGI.new(app=closing) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/').status_is(200).content_is('Hello!')
        ok(wait(closed), 'body closed')

with subtest('Threads'):
    barrier = threading.Barrier(2, timeout=5)

    def together(environ, start_response):
        barrier.wait()
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [environ['PATH_INFO'].encode()]

    with Pyjo.App.WSGI.new(app=together, threads=2) as app:
        is_ok(app.threads, 2, 'right number of threads')
        t = Pyjo.Test.Pyjo.new(app)
        results = result(Pyjo.Promise.all(t.ua.get_p('/a'), t.ua.get_p('/b')))
        is_deeply_ok([tx[0].res.body for tx in results], [b'/a', b'/b'], 'both requests at the same time')

with subtest('Fork'):
    if not hasattr(os, 'fork'):
        skip('fork not supported', 1)
    else:
        with Pyjo.App.WSGI.new(app=whole) as app:
            t = Pyjo.Test.Pyjo.new(app)
            t.get_ok('/').status_is(201)

            # The threads are stopped before the fork, and the next request starts them again
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                forked = result(Pyjo.IOLoop.subprocess().run_p(lambda subprocess: 'forked'))
            is_ok(forked, 'forked', 'right result')
            is_deeply_ok([str(w.message) for w in caught if 'fork' in str(w.message)], [], 'no warning of a fork')
            t.get_ok('/').status_is(201).content_is('Hello World!')

done_testing()
