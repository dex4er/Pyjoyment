import Pyjo.Message.Response
import Pyjo.Server.CGI

from Pyjo.Test import *

import contextlib
import importlib
import io
import os
import sys

from unittest.mock import patch


# The minimal Mojolicious::Lite of the tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
Lite = importlib.import_module('Lite')
app, get, post = Lite.app, Lite.get, Lite.post


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
        chunks.append(params[key])

    def cb(c):
        chunk = chunks.pop(0) if chunks else ''
        c.write_chunk(chunk, cb if chunk else None)

    cb(c)


@get('/params')
def params(c):
    c.inactivity_timeout(60)
    c.render(json=c.req.params.to_dict())


@get('/proxy')
def proxy(c):
    reverse = ':'.join(part for part in (c.tx.remote_address, c.req.url.to_abs().protocol) if part)
    c.render(text=reverse)


# TODO: Mojolicious::Command::cgi, which runs the server as here, when it is ported

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
        status = Pyjo.Server.CGI.new(app=app).run()
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
        status = Pyjo.Server.CGI.new(app=app).run()
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
        status = Pyjo.Server.CGI.new(app=app, nph=True).run()
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
        status = Pyjo.Server.CGI.new(app=app).run()
        msg = stdout.getvalue()
    is_ok(status, 200, 'right status')

    like_ok(msg, rb'chunked', 'is chunked')
    res = Pyjo.Message.Response.new().parse(b'HTTP/1.1 200 OK\x0d\x0a' + msg)
    is_ok(res.code, 200, 'right status')
    is_ok(res.headers.status, '200 OK', 'right "Status" value')
    is_ok(res.body, b'1234567', 'right content')

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
        status = Pyjo.Server.CGI.new(app=app).run()
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
        status = Pyjo.Server.CGI.new(app=app).run()
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
        status = Pyjo.Server.CGI.new(app=app).run()
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
        status = Pyjo.Server.CGI.new(app=app).run()
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
        status = Pyjo.Server.CGI.new(app=app).run()
        msg = stdout.getvalue()
    is_ok(status, 200, 'right status')

    res = Pyjo.Message.Response.new().parse(b'HTTP/1.1 200 OK\x0d\x0a' + msg)
    is_ok(res.code, 200, 'right status')
    is_ok(res.headers.status, '200 OK', 'right "Status" value')
    is_ok(res.headers.content_length, '5', 'right "Content-Length" value')
    is_ok(res.headers.content_type, 'text/html;charset=UTF-8', 'right "Content-Type" value')
    is_ok(res.body, b'https', 'right content')

done_testing()
