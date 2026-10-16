import Pyjo.Server.WSGI

from Pyjo.JSON import decode_json
from Pyjo.Test import *
from Pyjo.Util import setenv
from Pyjoyment.Lite import app, get, post, under

import io
import os
import sys

from unittest.mock import patch


# Not in Mojolicious: a WSGI application gives the status and the headers to start_response and returns the body, where
# a PSGI application returns all three
def call(app, env):
    res = []
    body = app(env, lambda status, headers, exc_info=None: res.extend([status, headers]))
    return [*res, body]


# Silence
app.log.level = 'fatal'


@under
def finish(c):
    return c.on('finish', lambda c: setenv('PYJO_HELLO', 'world'))


get('/', {'text': 'Your Mojo is working!'})


@get('/cookies')
def cookies(c):
    params = c.req.params.to_dict()
    for key in sorted(params):
        c.cookie(key, params[key])
    c.render(text='nomnomnom')


@post('/params')
def params(c):
    c.render(json=c.req.params.to_dict())


@get('/proxy')
def proxy(c):
    reverse = ':'.join(part for part in (c.tx.remote_address, c.req.url.to_abs().protocol) if part)
    c.render(text=reverse)


# TODO: Mojolicious::Command::psgi, which turns the application into a WSGI application as here, when it is ported

with subtest('Reverse proxy'):
    ok(not Pyjo.Server.WSGI.new().reverse_proxy, 'no reverse proxy')
    with patch.dict(os.environ, {'PYJO_REVERSE_PROXY': '1'}):
        ok(Pyjo.Server.WSGI.new().reverse_proxy, 'reverse proxy')

with subtest('Binding'):
    server = []

    def before_server_start(server_, app):
        server.extend([f'{type(server_).__module__}.{type(server_).__qualname__}', app.mode])

    app.hook('before_server_start', before_server_start)
    wsgi_app = Pyjo.Server.WSGI.new(app=app).to_wsgi_app()
    content = b'hello=world'
    body = io.BytesIO(content)
    env = {
        'CONTENT_LENGTH': '11',
        'CONTENT_TYPE': 'application/x-www-form-urlencoded',
        'PATH_INFO': '/params',
        'QUERY_STRING': 'lalala=23&bar=baz',
        'REQUEST_METHOD': 'POST',
        'SCRIPT_NAME': '/',
        'HTTP_HOST': 'localhost:8080',
        'SERVER_PROTOCOL': 'HTTP/1.0',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': body,
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    res = call(wsgi_app, env)
    # Unlike Mojolicious: the status of WSGI has its reason phrase
    is_ok(res[0], '200 OK', 'right status')
    headers = dict(res[1])
    ok(len(headers) >= 3, 'enough headers')
    ok(headers['Date'], 'has "Date" value')
    is_ok(headers['Content-Length'], '43', 'right "Content-Length" value')
    is_ok(headers['Content-Type'], 'application/json;charset=UTF-8', 'right "Content-Type" value')
    params = b''
    for chunk in res[2]:
        params += chunk
    is_ok(os.environ.get('PYJO_HELLO'), None, 'finish event has not been emitted')
    res[2].close()
    is_ok(os.environ.pop('PYJO_HELLO', None), 'world', 'finish event has been emitted')
    is_deeply_ok(decode_json(params), {'bar': 'baz', 'hello': 'world', 'lalala': '23'}, 'right structure')
    is_deeply_ok(server, ['Pyjo.Server.WSGI.Pyjo_Server_WSGI', 'development'], 'hook has been emitted once')

with subtest('Command'):
    content = b'world=hello'
    body = io.BytesIO(content)
    env = {
        'CONTENT_LENGTH': '11',
        'CONTENT_TYPE': 'application/x-www-form-urlencoded',
        'PATH_INFO': '/params',
        'QUERY_STRING': 'lalala=23&bar=baz',
        'REQUEST_METHOD': 'POST',
        'SCRIPT_NAME': '/',
        'HTTP_HOST': 'localhost:8080',
        'SERVER_PROTOCOL': 'HTTP/1.0',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': body,
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    wsgi_app = Pyjo.Server.WSGI.new(app=app).to_wsgi_app()
    res = call(wsgi_app, env)
    is_ok(res[0], '200 OK', 'right status')
    headers = dict(res[1])
    ok(len(headers) >= 3, 'enough headers')
    ok(headers['Date'], 'has "Date" value')
    is_ok(headers['Content-Length'], '43', 'right "Content-Length" value')
    is_ok(headers['Content-Type'], 'application/json;charset=UTF-8', 'right "Content-Type" value')
    params = b''
    for chunk in res[2]:
        params += chunk
    is_ok(os.environ.get('PYJO_HELLO'), None, 'finish event has not been emitted')
    res[2].close()
    is_ok(os.environ.pop('PYJO_HELLO', None), 'world', 'finish event has been emitted')
    is_deeply_ok(decode_json(params), {'bar': 'baz', 'world': 'hello', 'lalala': '23'}, 'right structure')

# Not in Mojolicious: *STDIN as the input, which is not read, is an empty one
stdin = io.BytesIO()

with subtest('Simple'):
    env = {
        'CONTENT_LENGTH': '0',
        'PATH_INFO': '/',
        'REQUEST_METHOD': 'GET',
        'SCRIPT_NAME': '/',
        'HTTP_HOST': 'localhost:8080',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': stdin,
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    wsgi_app = Pyjo.Server.WSGI.new(app=app).to_wsgi_app()
    res = call(wsgi_app, env)
    is_ok(res[0], '200 OK', 'right status')
    headers = dict(res[1])
    is_ok(headers['Content-Length'], '21', 'right "Content-Length" value')
    is_ok(headers['Content-Type'], 'text/html;charset=UTF-8', 'right "Content-Type" value')
    body = b''
    for chunk in res[2]:
        body += chunk
    is_ok(body, b'Your Mojo is working!', 'right content')
    is_ok(os.environ.get('PYJO_HELLO'), None, 'finish event has not been emitted')
    res[2].close()
    is_ok(os.environ.pop('PYJO_HELLO', None), 'world', 'finish event has been emitted')

with subtest('HEAD request'):
    env = {
        'CONTENT_LENGTH': '0',
        'PATH_INFO': '/',
        'REQUEST_METHOD': 'HEAD',
        'SCRIPT_NAME': '/',
        'HTTP_HOST': 'localhost:8080',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': stdin,
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    wsgi_app = Pyjo.Server.WSGI.new(app=app).to_wsgi_app()
    res = call(wsgi_app, env)
    is_ok(res[0], '200 OK', 'right status')
    headers = dict(res[1])
    is_ok(headers['Content-Length'], '21', 'right "Content-Length" value')
    is_ok(headers['Content-Type'], 'text/html;charset=UTF-8', 'right "Content-Type" value')
    body = b''
    for chunk in res[2]:
        body += chunk
    is_ok(body, b'', 'no content')
    is_ok(os.environ.get('PYJO_HELLO'), None, 'finish event has not been emitted')
    res[2].close()
    is_ok(os.environ.pop('PYJO_HELLO', None), 'world', 'finish event has been emitted')

with subtest('Cookies'):
    env = {
        'CONTENT_LENGTH': '0',
        'PATH_INFO': '/cookies',
        'QUERY_STRING': 'lalala=23&bar=baz',
        'REQUEST_METHOD': 'GET',
        'SCRIPT_NAME': '/',
        'HTTP_HOST': 'localhost:8080',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': stdin,
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    wsgi_app = Pyjo.Server.WSGI.new(app=app).to_wsgi_app()
    res = call(wsgi_app, env)
    is_ok(res[0], '200 OK', 'right status')
    # Unlike Mojolicious: the headers of WSGI are pairs, where PSGI has a flat list of names and values
    ok(len(res[1]) >= 5, 'enough headers')
    i = 0
    for name, _value in res[1]:
        if name == 'Set-Cookie':
            i += 1
    is_ok(i, 2, 'right number of "Set-Cookie" headers')

with subtest('Reverse proxy'):
    env = {
        'CONTENT_LENGTH': '0',
        'PATH_INFO': '/proxy',
        'REQUEST_METHOD': 'GET',
        'SCRIPT_NAME': '/',
        'HTTP_HOST': 'localhost:8080',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'HTTP_X_FORWARDED_FOR': '192.0.2.2, 192.0.2.1',
        'HTTP_X_FORWARDED_PROTO': 'https',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': stdin,
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    with patch.dict(os.environ, {'PYJO_REVERSE_PROXY': '1'}):
        wsgi_app = Pyjo.Server.WSGI.new(app=app).to_wsgi_app()
        res = call(wsgi_app, env)
    is_ok(res[0], '200 OK', 'right status')
    headers = dict(res[1])
    is_ok(headers['Content-Length'], '15', 'right "Content-Length" value')
    is_ok(headers['Content-Type'], 'text/html;charset=UTF-8', 'right "Content-Type" value')
    body = b''
    for chunk in res[2]:
        body += chunk
    is_ok(body, b'192.0.2.1:https', 'right content')
    is_ok(os.environ.get('PYJO_HELLO'), None, 'finish event has not been emitted')
    res[2].close()
    is_ok(os.environ.pop('PYJO_HELLO', None), 'world', 'finish event has been emitted')

with subtest('Trusted proxies'):
    env = {
        'CONTENT_LENGTH': '0',
        'PATH_INFO': '/proxy',
        'REQUEST_METHOD': 'GET',
        'SCRIPT_NAME': '/',
        'HTTP_HOST': 'localhost:8080',
        'REMOTE_ADDR': '127.0.0.1',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'HTTP_X_FORWARDED_FOR': '10.10.10.10, 192.0.2.2, 192.0.2.1',
        'HTTP_X_FORWARDED_PROTO': 'https',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': stdin,
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    with patch.dict(os.environ, {'PYJO_TRUSTED_PROXIES': '127.0.0.0/8, 192.0.0.0/8'}):
        wsgi_app = Pyjo.Server.WSGI.new(app=app).to_wsgi_app()
        res = call(wsgi_app, env)
    is_ok(res[0], '200 OK', 'right status')
    headers = dict(res[1])
    is_ok(headers['Content-Length'], '17', 'right "Content-Length" value')
    is_ok(headers['Content-Type'], 'text/html;charset=UTF-8', 'right "Content-Type" value')
    body = b''
    for chunk in res[2]:
        body += chunk
    is_ok(body, b'10.10.10.10:https', 'right content')
    is_ok(os.environ.get('PYJO_HELLO'), None, 'finish event has not been emitted')
    res[2].close()
    is_ok(os.environ.pop('PYJO_HELLO', None), 'world', 'finish event has been emitted')

with subtest('Trusted proxies (no REMOTE_ADDR)'):
    env = {
        'CONTENT_LENGTH': '0',
        'PATH_INFO': '/proxy',
        'REQUEST_METHOD': 'GET',
        'SCRIPT_NAME': '/',
        'HTTP_HOST': 'localhost:8080',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'HTTP_X_Forwarded_For': '10.10.10.10, 192.0.2.2, 192.0.2.1',
        'HTTP_X_Forwarded_Proto': 'https',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': stdin,
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    with patch.dict(os.environ, {'PYJO_TRUSTED_PROXIES': '127.0.0.0/8, 192.0.0.0/8'}):
        wsgi_app = Pyjo.Server.WSGI.new(app=app).to_wsgi_app()
        res = call(wsgi_app, env)
    is_ok(res[0], '200 OK', 'right status')
    headers = dict(res[1])
    is_ok(headers['Content-Length'], '5', 'right "Content-Length" value')
    is_ok(headers['Content-Type'], 'text/html;charset=UTF-8', 'right "Content-Type" value')
    body = b''
    for chunk in res[2]:
        body += chunk
    is_ok(body, b'https', 'right content')
    is_ok(os.environ.get('PYJO_HELLO'), None, 'finish event has not been emitted')
    res[2].close()
    is_ok(os.environ.pop('PYJO_HELLO', None), 'world', 'finish event has been emitted')

done_testing()
