import Pyjo.App.FastCGI
import Pyjo.File
import Pyjo.IOLoop
import Pyjo.Promise
import Pyjo.Server.Daemon
import Pyjo.Test.Pyjo
import Pyjo.Transaction.HTTP
import Pyjoyment

from Pyjo.Server.FastCGI import END_REQUEST, HEADER, PARAMS, STDIN, STDOUT, _pairs, _record  # pyright: ignore[reportPrivateUsage]
from Pyjo.Test import *
from Pyjo.Util import url_escape

import concurrent.futures
import http.client
import re
import socket
import struct
import sys


# An application of Pyjoyment on the FastCGI server of Pyjo, in the event loop of the test, which gives the parameters
# that it gets, and responses and chunks that come from timers
inner = Pyjoyment.new()
inner.log.level = 'fatal'


def env(c):
    c.render(json={'env': dict(c.req.env), 'body': c.req.body.decode('latin-1')})


inner.routes.any('/env/*rest', {'rest': ''}).to(cb=env)


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


@inner.routes.get('/length')
def length(c):
    c.res.headers.content_length = 6
    c.write(b'one', lambda c: Pyjo.IOLoop.timer(0.01, lambda loop: c.write(b'two', lambda c: c.finish())))


@inner.routes.get('/redirect')
def redirect(c):
    c.redirect_to('/later')


daemon = Pyjo.Server.Daemon.new(app=inner, listen=['fcgi://127.0.0.1'], silent=True).start()
URL = f'fcgi://127.0.0.1:{daemon.ports()[0]}'


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


def application(fcgi, prefix='/prefix'):
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    route = app.routes.any(prefix)
    route.partial = True
    route.to(app=fcgi)
    return app


# A responder of FastCGI that answers a request, once its body has ended, with the bytes of a reply, and closes the
# connection after them, unless it is told to keep it, and the requests that it got
def responder(reply, close=True):
    requests = []

    def accept(loop, stream, id):
        buffer = bytearray()

        def read(stream, chunk):
            buffer.extend(chunk)
            if _record(STDIN, 1) in buffer:
                requests.append(bytes(buffer))
                buffer.clear()
                if reply is not None:
                    stream.write(reply, (lambda stream: stream.close()) if close else None)

        stream.on('read', read)

    id = Pyjo.IOLoop.server(accept, address='127.0.0.1')
    return f'fcgi://127.0.0.1:{Pyjo.IOLoop.acceptor(id).port}', requests, id


def stdout(*chunks):
    return b''.join(_record(STDOUT, 1, chunk) for chunk in chunks) + _record(STDOUT, 1)


def end():
    return _record(END_REQUEST, 1, struct.pack('>IB3x', 0, 0))


# The parameters of a request that a responder got
def params(request):
    data, offset = b'', 0
    while offset + HEADER.size <= len(request):
        version, type, id, length, padding = HEADER.unpack_from(request, offset)
        if type == PARAMS:
            data += request[offset + HEADER.size : offset + HEADER.size + length]
        offset += HEADER.size + length + padding
    return _pairs(data)


with subtest('Parameters'):
    with Pyjo.App.FastCGI.new(url=URL) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/env?a=1&b=%20', {'X-Foo': 'bar'}).status_is(200)
        env = t.tx.res.json('/env')
        is_ok(env['REQUEST_METHOD'], 'GET', 'right method')
        is_ok(env['SCRIPT_NAME'], '', 'no script name')
        is_ok(env['PATH_INFO'], '/env', 'right path')
        is_ok(env['QUERY_STRING'], 'a=1&b=%20', 'right query')
        is_ok(env['REQUEST_URI'], '/env?a=1&b=%20', 'right request URI')
        is_ok(env['SERVER_NAME'], '127.0.0.1', 'right server name')
        is_ok(env['SERVER_PORT'], str(t.ua.server.url().port), 'right server port')
        is_ok(env['SERVER_PROTOCOL'], 'HTTP/1.1', 'right protocol')
        is_ok(env['GATEWAY_INTERFACE'], 'CGI/1.1', 'right gateway interface')
        is_ok(env['SERVER_SOFTWARE'], 'Pyjoyment (Python)', 'right server software')
        is_ok(env['REMOTE_ADDR'], '127.0.0.1', 'right remote address')
        ok(env['REMOTE_PORT'].isdigit(), 'remote port')
        is_ok(env['HTTP_X_FOO'], 'bar', 'right header')
        ok('HTTPS' not in env, 'not secure')
        ok('CONTENT_LENGTH' not in env, 'no content length')

    # The parameters of the application, which replace the ones of the request
    with Pyjo.App.FastCGI.new(
        url=URL, env={'SCRIPT_FILENAME': '/var/www/index.php', 'SERVER_NAME': 'example.com'}
    ) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/env').status_is(200)
        is_ok(t.tx.res.json('/env/SCRIPT_FILENAME'), '/var/www/index.php', 'added parameter')
        is_ok(t.tx.res.json('/env/SERVER_NAME'), 'example.com', 'replaced parameter')

with subtest('Body'):
    with Pyjo.App.FastCGI.new(url=URL) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.post_ok('/env', {'Content-Type': 'text/plain'}, b'Hello!').status_is(200)
        is_ok(t.tx.res.json('/env/CONTENT_TYPE'), 'text/plain', 'right content type')
        is_ok(t.tx.res.json('/env/CONTENT_LENGTH'), '6', 'right content length')
        is_ok(t.tx.res.json('/body'), 'Hello!', 'right body')

        # Chunked
        tx = t.ua.build_tx('POST', '/env')
        tx.req.content.write_chunk(b'Hello').write_chunk(b' World!').write_chunk(b'')
        t.request_ok(tx).status_is(200)
        is_ok(t.tx.res.json('/env/CONTENT_LENGTH'), '12', 'right content length')
        is_ok(t.tx.res.json('/body'), 'Hello World!', 'right body')

        # In more than one record
        body = b'0123456789' * 20000
        t.post_ok('/env', body).status_is(200)
        is_ok(t.tx.res.json('/env/CONTENT_LENGTH'), '200000', 'right content length')
        ok(t.tx.res.json('/body') == body.decode(), 'right body')

with subtest('Path of a route'):
    with Pyjo.App.FastCGI.new(url=URL) as fcgi:
        t = Pyjo.Test.Pyjo.new(application(fcgi))
        t.get_ok('/prefix/env/foo/bar?x=1').status_is(200)
        is_ok(t.tx.res.json('/env/SCRIPT_NAME'), '/prefix', 'right script name')
        is_ok(t.tx.res.json('/env/PATH_INFO'), '/env/foo/bar', 'right path')
        is_ok(t.tx.res.json('/env/REQUEST_URI'), '/prefix/env/foo/bar?x=1', 'right request URI')

        # The path of the mount itself
        t.get_ok('/prefix/later').status_is(200).content_is('Hello later at /prefix!')

        # Escaped, as the bytes of the path
        t.get_ok('/prefix/env/a%20b/%E2%99%A5').status_is(200)
        # The bytes of the path in the parameter, which the server of Pyjo escapes beyond ASCII
        is_ok(t.tx.res.json('/env/PATH_INFO'), '/env/a b/%E2%99%A5', 'right path')

with subtest('Directory of the scripts'):
    url, requests, id = responder(stdout(b'Status: 200\r\n\r\nOK') + end())
    with Pyjo.App.FastCGI.new(url=url, document_root='/var/www/') as fcgi:
        t = Pyjo.Test.Pyjo.new(application(fcgi, '/php'))
        for path, script, name, info in (
            ('/php', '/var/www/index.php', '/php/index.php', ''),
            ('/php/', '/var/www/index.php', '/php/index.php', ''),
            ('/php/phpinfo.php', '/var/www/phpinfo.php', '/php/phpinfo.php', ''),
            ('/php/index.php/foo/bar?x=1', '/var/www/index.php', '/php/index.php', '/foo/bar'),
            ('/php/index.php/', '/var/www/index.php', '/php/index.php', '/'),
            ('/php/dir/', '/var/www/dir/index.php', '/php/dir/index.php', ''),
            ('/php/foo', '/var/www/foo', '/php/foo', ''),
        ):
            t.get_ok(path).status_is(200).content_is('OK')
            env = params(requests[-1])
            is_ok(env['SCRIPT_FILENAME'], script, f'right script file of {path}')
            is_ok(env['SCRIPT_NAME'], name, f'right script name of {path}')
            is_ok(env['PATH_INFO'], info, f'right path of {path}')
            is_ok(env['DOCUMENT_ROOT'], '/var/www/', f'right document root of {path}')
        is_ok(params(requests[-4])['REQUEST_URI'], '/php/index.php/foo/bar?x=1', 'right request URI')

        # Not above the directory
        count = len(requests)
        t.get_ok('/php/%2E%2E/etc/passwd').status_is(404)
        is_ok(len(requests), count, 'no request to the application')

    # The script of the parameters of the application takes its place
    with Pyjo.App.FastCGI.new(url=url, document_root='/var/www', env={'SCRIPT_FILENAME': '/srv/app.php'}) as fcgi:
        t = Pyjo.Test.Pyjo.new(application(fcgi, '/php'))
        t.get_ok('/php/foo/bar').status_is(200)
        env = params(requests[-1])
        is_ok(env['SCRIPT_FILENAME'], '/srv/app.php', 'script of the parameters')
        is_ok(env['SCRIPT_NAME'], '/php', 'script name of the mount')
        is_ok(env['PATH_INFO'], '/foo/bar', 'path after the mount')
    Pyjo.IOLoop.remove(id)

with subtest('Response'):
    with Pyjo.App.FastCGI.new(url=URL) as fcgi:
        t = Pyjo.Test.Pyjo.new(application(fcgi))
        t.get_ok('/prefix/later').status_is(200).content_is('Hello later at /prefix!')
        is_ok(t.tx.res.headers.content_length, '23', 'whole response with its length')
        is_deeply_ok(raw(t, 'GET', '/prefix/chunks'), (200, None, 'chunked', b'012'), 'chunked response')
        is_deeply_ok(raw(t, 'GET', '/prefix/length'), (200, '6', None, b'onetwo'), 'response with its length')
        is_deeply_ok(raw(t, 'HEAD', '/prefix/later'), (200, '23', None, b''), 'response without content')
        t.get_ok('/prefix/redirect').status_is(302).header_is('Location', '/prefix/later')
        t.get_ok('/prefix/missing').status_is(404)

        # Without the chunked transfer encoding in HTTP/1.0
        tx = t.ua.build_tx('GET', '/prefix/chunks')
        tx.req.version = '1.0'
        t.request_ok(tx).status_is(200).content_is('012')
        is_ok(t.tx.keep_alive, False, 'no keep-alive')

with subtest('Response of CGI'):
    # The status in its header, the headers in records of their own, and lines that end with LF
    url, requests, id = responder(stdout(b'Status: 201 Made\nX-Foo: a\n', b'X-Foo: b\n\nHel', b'lo!') + end())
    with Pyjo.App.FastCGI.new(url=url) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/').status_is(201).content_is('Hello!')
        is_ok(t.tx.res.message, 'Made', 'right message')
        is_deeply_ok(t.tx.res.headers.every_header('X-Foo'), ['a', 'b'], 'right headers')
    Pyjo.IOLoop.remove(id)

    # A redirect for Location without a status
    url, requests, id = responder(stdout(b'Location: http://example.com/\r\n\r\n') + end())
    with Pyjo.App.FastCGI.new(url=url) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/').status_is(302).header_is('Location', 'http://example.com/')
    Pyjo.IOLoop.remove(id)

    # The standard error of the application is logged
    url, requests, id = responder(_record(7, 1, b'Something to say\n') + stdout(b'Status: 200\r\n\r\nOK') + end())
    with Pyjo.App.FastCGI.new(url=url) as app:
        t = Pyjo.Test.Pyjo.new(app)
        with app.log.capture('warn') as messages:
            t.get_ok('/').status_is(200).content_is('OK')
        like_ok(str(messages), r'FastCGI application: Something to say', 'standard error logged')
    Pyjo.IOLoop.remove(id)

    # The records of a request
    record = requests[0]
    is_ok(record[:16], _record(1, 1, struct.pack('>HB5x', 1, 0)), 'request of a responder, closed after it')

with subtest('Errors'):
    # Refused
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()
    with Pyjo.App.FastCGI.new(url=f'fcgi://127.0.0.1:{port}') as app:
        app.log.level = 'fatal'
        t = Pyjo.Test.Pyjo.new(app)
        with app.log.capture('error') as messages:
            t.get_ok('/').status_is(502).content_is('Bad Gateway')
        like_ok(str(messages), r'FastCGI connection failed', 'right error')

    # Closed before the response
    url, requests, id = responder(b'')
    with Pyjo.App.FastCGI.new(url=url) as app:
        app.log.level = 'fatal'
        t = Pyjo.Test.Pyjo.new(app)
        with app.log.capture('error') as messages:
            t.get_ok('/').status_is(502)
        like_ok(str(messages), r'FastCGI connection closed before the end of the response', 'right error')
    Pyjo.IOLoop.remove(id)

    # Ended without a response
    url, requests, id = responder(end())
    with Pyjo.App.FastCGI.new(url=url) as app:
        app.log.level = 'fatal'
        t = Pyjo.Test.Pyjo.new(app)
        with app.log.capture('error') as messages:
            t.get_ok('/').status_is(502)
        like_ok(str(messages), r'FastCGI application ended without a response', 'right error')
    Pyjo.IOLoop.remove(id)

    # Closed after the start of the response, which closes the connection of the client
    url, requests, id = responder(_record(STDOUT, 1, b'Status: 200\r\n\r\none'))
    with Pyjo.App.FastCGI.new(url=url) as app:
        app.log.level = 'fatal'
        t = Pyjo.Test.Pyjo.new(app)
        with app.log.capture('error') as messages:
            is_deeply_ok(raw(t, 'GET'), (200, None, 'chunked', None), 'incomplete response')
        like_ok(str(messages), r'FastCGI connection closed before the end of the response', 'right error')
    Pyjo.IOLoop.remove(id)

    # Inactive
    url, requests, id = responder(None)
    with Pyjo.App.FastCGI.new(url=url, inactivity_timeout=0.2) as app:
        app.log.level = 'fatal'
        t = Pyjo.Test.Pyjo.new(app)
        with app.log.capture('error') as messages:
            t.get_ok('/').status_is(502)
        like_ok(str(messages), r'FastCGI connection inactive', 'right error')
    Pyjo.IOLoop.remove(id)

    throws_ok(
        lambda: Pyjo.App.FastCGI.new().handler(Pyjo.Transaction.HTTP.new()),
        re.compile(r'^No FastCGI application'),
        'no application',
    )
    throws_ok(
        lambda: Pyjo.App.FastCGI.new(url='http://127.0.0.1:9000').handler(Pyjo.Transaction.HTTP.new()),
        re.compile(r'^Invalid FastCGI location "http://127\.0\.0\.1:9000"'),
        'invalid location',
    )

with subtest('Connection of the client closed'):
    # The connection to the application is closed with the one of the client
    url, requests, id = responder(_record(STDOUT, 1, b'Status: 200\r\n\r\n' + b'x' * 20000), close=False)
    with Pyjo.App.FastCGI.new(url=url) as app:
        t = Pyjo.Test.Pyjo.new(app)
        t.ua.max_response_size = 10000
        tx = t.ua.get('/')
        is_ok(tx.error['message'], 'Maximum message size exceeded', 'right error')
    Pyjo.IOLoop.remove(id)

with subtest('UNIX domain socket'):
    if not hasattr(socket, 'AF_UNIX') or sys.platform == 'win32':
        skip('UNIX domain sockets not supported', 2)
    else:
        tmp = Pyjo.File.tempdir()
        path = tmp.child('fcgi.sock').to_str()
        unix = Pyjo.Server.Daemon.new(
            app=inner, listen=[f'fcgi+unix://{url_escape(path, rb"^A-Za-z0-9\-._~")}'], silent=True
        ).start()
        with Pyjo.App.FastCGI.new(url=f'fcgi+unix://{url_escape(path, rb"^A-Za-z0-9\-._~")}') as fcgi:
            t = Pyjo.Test.Pyjo.new(application(fcgi))
            t.get_ok('/prefix/later').status_is(200).content_is('Hello later at /prefix!')
            t.get_ok('/prefix/chunks').status_is(200).content_is('012')
        unix.close()

daemon.close()

done_testing()
