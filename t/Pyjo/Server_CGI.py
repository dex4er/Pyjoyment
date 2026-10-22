import Pyjo.IOLoop
import Pyjo.Message.Response
import Pyjo.Promise
import Pyjo.Server.CGI
import Pyjoyment.Command.cgi

from Pyjo.Test import *
from Pyjoyment.Lite import app, get, post

import contextlib
import io
import os
import sys

from unittest.mock import patch


# Not in Mojolicious: local %ENV, *STDIN and *STDOUT, with the output of the CGI script as bytes; the tests report
# after it, as Pyjo.Test writes to sys.stdout, where Test::More writes to a copy of STDOUT
@contextlib.contextmanager
def local(env, content=b''):
    stdout = io.BytesIO()
    with (
        patch.dict(os.environ, env, clear=True),
        patch.object(sys, 'stdin', io.TextIOWrapper(io.BytesIO(content))),
        patch.object(sys, 'stdout', io.TextIOWrapper(stdout, write_through=True)),
    ):
        yield stdout


# Silence
app.log.level = 'fatal'

get('/', {'text': 'Your Mojo is working!'})


@post('/chunked')
def chunked(c):
    params = c.req.params.to_dict()
    chunks = []
    for key in sorted(params):
        chunks.append(params[key].encode())

    def cb(c):
        chunk = chunks.pop(0) if chunks else b''
        c.write_chunk(chunk, cb if chunk else None)

    cb(c)


# Not in Mojolicious: responses that come later, from the event loop
@get('/later')
def later(c):
    c.render_later()
    Pyjo.IOLoop.timer(0.01, lambda loop: c.render(text='Later!'))


@get('/later/chunks')
def later_chunks(c):
    c.render_later()
    Pyjo.IOLoop.timer(
        0.01,
        lambda loop: c.write_chunk(
            b'one', lambda c: Pyjo.IOLoop.timer(0.01, lambda loop: c.write_chunk(b'two', lambda c: c.finish()))
        ),
    )


@get('/later/promise')
async def later_promise(c):
    await Pyjo.Promise.timer(0.01)
    c.render(text='Promised!')


@get('/params')
def params(c):
    c.inactivity_timeout(60)
    c.render(json=c.req.params.to_dict())


@get('/proxy')
def proxy(c):
    reverse = ':'.join(part for part in (c.tx.remote_address, c.req.url.to_abs().protocol) if part)
    c.render(text=reverse)


with subtest('Reverse proxy'):
    ok(not Pyjo.Server.CGI.new().reverse_proxy, 'no reverse proxy')
    with patch.dict(os.environ, {'PYJO_REVERSE_PROXY': '1'}):
        ok(Pyjo.Server.CGI.new().reverse_proxy, 'reverse proxy')

with subtest('Simple'):
    with local(
        {
            'PATH_INFO': '/',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '/',
            'HTTP_HOST': 'localhost:8080',
            'SERVER_PROTOCOL': 'HTTP/1.0',
        }
    ) as stdout:
        status = Pyjoyment.Command.cgi.new(app=app).run()
        msg = stdout.getvalue()
    is_ok(status, 200, 'right status')

    res = Pyjo.Message.Response.new().parse(b'HTTP/1.1 200 OK\x0d\x0a' + msg)
    is_ok(res.code, 200, 'right status')
    is_ok(res.headers.status, '200 OK', 'right "Status" value')
    is_ok(res.headers.content_length, '21', 'right "Content-Length" value')
    is_ok(res.headers.content_type, 'text/html;charset=UTF-8', 'right "Content-Type" value')
    is_ok(res.body, b'Your Mojo is working!', 'right content')

with subtest('HEAD request'):
    with local(
        {
            'PATH_INFO': '/',
            'REQUEST_METHOD': 'HEAD',
            'SCRIPT_NAME': '/',
            'HTTP_HOST': 'localhost:8080',
            'SERVER_PROTOCOL': 'HTTP/1.0',
        }
    ) as stdout:
        status = Pyjoyment.Command.cgi.new(app=app).run()
        msg = stdout.getvalue()
    is_ok(status, 200, 'right status')

    res = Pyjo.Message.Response.new().parse(b'HTTP/1.1 200 OK\x0d\x0a' + msg)
    is_ok(res.code, 200, 'right status')
    is_ok(res.headers.status, '200 OK', 'right "Status" value')
    is_ok(res.headers.content_length, '21', 'right "Content-Length" value')
    is_ok(res.headers.content_type, 'text/html;charset=UTF-8', 'right "Content-Type" value')
    is_ok(res.body, b'', 'no content')

with subtest('Non-parsed headers'):
    with local(
        {
            'PATH_INFO': '/',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '/',
            'HTTP_HOST': 'localhost:8080',
            'SERVER_PROTOCOL': 'HTTP/1.0',
        }
    ) as stdout:
        status = Pyjoyment.Command.cgi.new(app=app).run('--nph')
        msg = stdout.getvalue()
    is_ok(status, 200, 'right status')

    res = Pyjo.Message.Response.new().parse(msg)
    is_ok(res.code, 200, 'right status')
    is_ok(res.headers.status, None, 'no "Status" value')
    is_ok(res.headers.content_length, '21', 'right "Content-Length" value')
    is_ok(res.headers.content_type, 'text/html;charset=UTF-8', 'right "Content-Type" value')
    is_ok(res.body, b'Your Mojo is working!', 'right content')

with subtest('Chunked'):
    content = b'test1=1&test2=2&test3=3&test4=4&test5=5&test6=6&test7=7'
    with local(
        {
            'PATH_INFO': '/chunked',
            'CONTENT_LENGTH': str(len(content)),
            'CONTENT_TYPE': 'application/x-www-form-urlencoded',
            'REQUEST_METHOD': 'POST',
            'SCRIPT_NAME': '/',
            'HTTP_HOST': 'localhost:8080',
            'SERVER_PROTOCOL': 'HTTP/1.0',
        },
        content,
    ) as stdout:
        status = Pyjoyment.Command.cgi.new(app=app).run()
        msg = stdout.getvalue()
    is_ok(status, 200, 'right status')

    # Unlike Mojolicious: the body without the chunked transfer encoding, which a CGI script does not return (RFC 3875
    # 6.3.4)
    unlike_ok(msg, rb'chunked', 'is not chunked')
    res = Pyjo.Message.Response.new().parse(b'HTTP/1.1 200 OK\x0d\x0a' + msg)
    is_ok(res.code, 200, 'right status')
    is_ok(res.headers.status, '200 OK', 'right "Status" value')
    is_ok(res.body, b'1234567', 'right content')
    # Not in Mojolicious: the chunks without their sizes
    ok(msg.endswith(b'\x0d\x0a\x0d\x0a1234567'), 'body without sizes')

# Not in Mojolicious: responses that come later, once the application resumes the transaction, where Mojo writes the
# default response
with subtest('Later'):
    for path, body in (('/later', b'Later!'), ('/later/chunks', b'onetwo'), ('/later/promise', b'Promised!')):
        with local(
            {
                'PATH_INFO': path,
                'REQUEST_METHOD': 'GET',
                'SCRIPT_NAME': '/',
                'HTTP_HOST': 'localhost:8080',
                'SERVER_PROTOCOL': 'HTTP/1.1',
            }
        ) as stdout:
            status = Pyjoyment.Command.cgi.new(app=app).run()
            msg = stdout.getvalue()
        is_ok(status, 200, f'right status of {path}')
        res = Pyjo.Message.Response.new().parse(b'HTTP/1.1 200 OK\x0d\x0a' + msg)
        is_ok(res.headers.status, '200 OK', f'right "Status" value of {path}')
        is_ok(res.headers.transfer_encoding, None, f'no "Transfer-Encoding" value of {path}')
        ok(msg.endswith(b'\x0d\x0a\x0d\x0a' + body), f'right content of {path}')

    # The chunks of non-parsed header mode with their sizes, as the client gets them
    with local(
        {
            'PATH_INFO': '/later/chunks',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '/',
            'HTTP_HOST': 'localhost:8080',
            'SERVER_PROTOCOL': 'HTTP/1.1',
        }
    ) as stdout:
        status = Pyjoyment.Command.cgi.new(app=app).run('--nph')
        msg = stdout.getvalue()
    res = Pyjo.Message.Response.new().parse(msg)
    is_ok(res.code, 200, 'right status')
    like_ok(msg, rb'\x0d\x0aTransfer-Encoding: chunked\x0d\x0a', 'is chunked')
    is_ok(res.body, b'onetwo', 'right content')

with subtest('Parameters'):
    with local(
        {
            'PATH_INFO': '/params',
            'QUERY_STRING': 'lalala=23&bar=baz',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '/',
            'HTTP_HOST': 'localhost:8080',
            'SERVER_PROTOCOL': 'HTTP/1.0',
        }
    ) as stdout:
        status = Pyjoyment.Command.cgi.new(app=app).run()
        msg = stdout.getvalue()
    is_ok(status, 200, 'right status')

    res = Pyjo.Message.Response.new().parse(b'HTTP/1.1 200 OK\x0d\x0a' + msg)
    is_ok(res.code, 200, 'right status')
    is_ok(res.headers.status, '200 OK', 'right "Status" value')
    is_ok(res.headers.content_type, 'application/json;charset=UTF-8', 'right "Content-Type" value')
    is_ok(res.headers.content_length, '27', 'right "Content-Length" value')
    is_ok(res.json()['lalala'], '23', 'right value')
    is_ok(res.json()['bar'], 'baz', 'right value')

with subtest('Binding'):
    server = []

    def before_server_start(server_, app):
        server.extend([f'{type(server_).__module__}.{type(server_).__qualname__}', app.mode])

    app.hook('before_server_start', before_server_start)

    with local(
        {
            'PATH_INFO': '/',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '/',
            'HTTP_HOST': 'localhost:8080',
            'SERVER_PROTOCOL': 'HTTP/1.0',
        }
    ) as stdout:
        status = Pyjoyment.Command.cgi.new(app=app).run()
        msg = stdout.getvalue()
    is_ok(status, 200, 'right status')
    res = Pyjo.Message.Response.new().parse(b'HTTP/1.1 200 OK\x0d\x0a' + msg)
    is_ok(res.code, 200, 'right status')
    is_ok(res.headers.status, '200 OK', 'right "Status" value')
    is_ok(res.headers.content_length, '21', 'right "Content-Length" value')
    is_ok(res.headers.content_type, 'text/html;charset=UTF-8', 'right "Content-Type" value')
    is_ok(res.body, b'Your Mojo is working!', 'right content')
    is_deeply_ok(server, ['Pyjo.Server.CGI.Pyjo_Server_CGI', 'development'], 'hook has been emitted once')

with subtest('Reverse proxy'):
    with local(
        {
            'PATH_INFO': '/proxy',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '/',
            'HTTP_HOST': 'localhost:8080',
            'SERVER_PROTOCOL': 'HTTP/1.0',
            'HTTP_X_FORWARDED_FOR': '192.0.2.2, 192.0.2.1',
            'HTTP_X_FORWARDED_PROTO': 'https',
            'PYJO_REVERSE_PROXY': '1',
        }
    ) as stdout:
        status = Pyjoyment.Command.cgi.new(app=app).run()
        msg = stdout.getvalue()
    is_ok(status, 200, 'right status')

    res = Pyjo.Message.Response.new().parse(b'HTTP/1.1 200 OK\x0d\x0a' + msg)
    is_ok(res.code, 200, 'right status')
    is_ok(res.headers.status, '200 OK', 'right "Status" value')
    is_ok(res.headers.content_length, '15', 'right "Content-Length" value')
    is_ok(res.headers.content_type, 'text/html;charset=UTF-8', 'right "Content-Type" value')
    is_ok(res.body, b'192.0.2.1:https', 'right content')

with subtest('Trusted proxies'):
    with local(
        {
            'PATH_INFO': '/proxy',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '/',
            'HTTP_HOST': 'localhost:8080',
            'REMOTE_ADDR': '127.0.0.1',
            'SERVER_PROTOCOL': 'HTTP/1.0',
            'HTTP_X_FORWARDED_FOR': '10.10.10.10, 192.0.2.2, 192.0.2.1',
            'HTTP_X_FORWARDED_PROTO': 'https',
            'PYJO_TRUSTED_PROXIES': '127.0.0.0/8, 192.0.0.0/8',
        }
    ) as stdout:
        status = Pyjoyment.Command.cgi.new(app=app).run()
        msg = stdout.getvalue()
    is_ok(status, 200, 'right status')

    res = Pyjo.Message.Response.new().parse(b'HTTP/1.1 200 OK\x0d\x0a' + msg)
    is_ok(res.code, 200, 'right status')
    is_ok(res.headers.status, '200 OK', 'right "Status" value')
    is_ok(res.headers.content_length, '17', 'right "Content-Length" value')
    is_ok(res.headers.content_type, 'text/html;charset=UTF-8', 'right "Content-Type" value')
    is_ok(res.body, b'10.10.10.10:https', 'right content')

with subtest('Trusted proxies (no REMOTE_ADDR)'):
    with local(
        {
            'PATH_INFO': '/proxy',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '/',
            'HTTP_HOST': 'localhost:8080',
            'SERVER_PROTOCOL': 'HTTP/1.0',
            'HTTP_X_FORWARDED_FOR': '10.10.10.10, 192.0.2.2, 192.0.2.1',
            'HTTP_X_FORWARDED_PROTO': 'https',
            'PYJO_TRUSTED_PROXIES': '127.0.0.0/8, 192.0.0.0/8',
        }
    ) as stdout:
        status = Pyjoyment.Command.cgi.new(app=app).run()
        msg = stdout.getvalue()
    is_ok(status, 200, 'right status')

    res = Pyjo.Message.Response.new().parse(b'HTTP/1.1 200 OK\x0d\x0a' + msg)
    is_ok(res.code, 200, 'right status')
    is_ok(res.headers.status, '200 OK', 'right "Status" value')
    is_ok(res.headers.content_length, '5', 'right "Content-Length" value')
    is_ok(res.headers.content_type, 'text/html;charset=UTF-8', 'right "Content-Type" value')
    is_ok(res.body, b'https', 'right content')

done_testing()
