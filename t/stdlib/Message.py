import Pyjo.Cookie.Request
import Pyjo.Message.Request
import Pyjo.Message.Response

from Pyjo.Test import *

import http
import http.client
import http.cookies
import http.server
import io
import json
import pathlib
import tempfile
import wsgiref.util


# A socket that http.client reads a response from and writes a request to
class FakeSocket:
    def __init__(self, data=b''):
        self.rfile = io.BytesIO(data)
        self.sent = b''

    def makefile(self, mode, *args, **kwargs):
        return self.rfile

    def sendall(self, data):
        self.sent += data

    def close(self):
        pass


# A handler of http.server that parses a request from bytes
class Handler(http.server.BaseHTTPRequestHandler):
    def __init__(self, data):
        self.rfile = io.BytesIO(data)
        self.wfile = io.BytesIO()
        self.raw_requestline = self.rfile.readline()
        self.parsed = self.parse_request()


with subtest('Response for http.client'):
    res = Pyjo.Message.Response.new(code=200)
    res.headers.content_type = 'text/plain'
    res.body = b'Hello World!'
    response = http.client.HTTPResponse(FakeSocket(res.to_bytes()))
    response.begin()
    is_ok(response.status, 200, 'status')
    is_ok(response.reason, 'OK', 'reason')
    is_ok(response.getheader('Content-Type'), 'text/plain', 'header')
    is_ok(response.read(), b'Hello World!', 'body')

with subtest('Response for http.client (chunked)'):
    res = Pyjo.Message.Response.new(code=200)
    res.content.write_chunk(b'Hello ').write_chunk(b'World!').write_chunk(b'')
    response = http.client.HTTPResponse(FakeSocket(res.to_bytes()))
    response.begin()
    ok(response.chunked, 'chunked')
    is_ok(response.read(), b'Hello World!', 'body')

with subtest('Request from http.client'):
    sock = FakeSocket()
    conn = http.client.HTTPConnection('127.0.0.1', 3000)
    conn.sock = sock
    conn.request('POST', '/foo?bar=baz', body=b'Hello World!', headers={'Content-Type': 'text/plain'})
    req = Pyjo.Message.Request.new().parse(sock.sent)
    ok(req.is_finished, 'finished')
    is_ok(req.method, 'POST', 'method')
    is_ok(req.url.path, '/foo', 'path')
    is_ok(req.param('bar'), 'baz', 'query parameter')
    is_ok(req.headers.host, '127.0.0.1:3000', 'host')
    is_ok(req.url.to_abs(), 'http://127.0.0.1:3000/foo?bar=baz', 'absolute URL')
    is_ok(req.body, b'Hello World!', 'body')

with subtest('Request for http.server'):
    req = Pyjo.Message.Request.new(method='PUT')
    req.url.parse('http://127.0.0.1:3000/foo?bar=baz')
    req.body = b'Hello World!'
    handler = Handler(req.to_bytes())
    ok(handler.parsed, 'parsed')
    is_ok(handler.command, 'PUT', 'command')
    is_ok(handler.path, '/foo?bar=baz', 'path')
    is_ok(handler.request_version, 'HTTP/1.1', 'version')
    is_ok(handler.headers['Host'], '127.0.0.1:3000', 'host')
    is_ok(handler.rfile.read(int(handler.headers['Content-Length'])), b'Hello World!', 'body')

with subtest('WSGI environment of wsgiref'):
    environ = {'PATH_INFO': '/foo/bar', 'QUERY_STRING': 'baz=yada', 'REQUEST_METHOD': 'GET'}
    wsgiref.util.setup_testing_defaults(environ)
    req = Pyjo.Message.Request.new().parse(environ)
    ok(req.is_finished, 'finished')
    ok(req.env is environ, 'environment')
    is_ok(req.method, 'GET', 'method')
    is_ok(req.url.path, '/foo/bar', 'path')
    is_ok(req.param('baz'), 'yada', 'query parameter')
    is_ok(req.url.to_abs(), wsgiref.util.request_uri(environ), 'same URL as wsgiref')

with subtest('Status codes of http.HTTPStatus'):
    res = Pyjo.Message.Response.new(code=http.HTTPStatus.NOT_FOUND)
    ok(res.is_client_error, 'client error')
    is_ok(res.default_message(), http.HTTPStatus.NOT_FOUND.phrase, 'same message')
    is_ok(res.default_message(http.HTTPStatus.OK), http.HTTPStatus.OK.phrase, 'same message for status')
    is_ok(res.build_start_line(), b'HTTP/1.1 404 Not Found\x0d\x0a', 'status-line')

with subtest('Cookies of http.cookies'):
    res = Pyjo.Message.Response.new()
    res.cookies({'name': 'foo', 'value': 'bar', 'path': '/test'}, {'name': 'baz', 'value': 'yada'})
    cookie = http.cookies.SimpleCookie()
    for header in res.headers.every_header('Set-Cookie'):
        cookie.load(header)
    is_ok(cookie['foo'].value, 'bar', 'value')
    is_ok(cookie['foo']['path'], '/test', 'path')
    is_ok(cookie['baz'].value, 'yada', 'other value')

    req = Pyjo.Message.Request.new()
    req.cookies(*(Pyjo.Cookie.Request.new(morsel) for morsel in cookie.values()))
    is_ok(req.headers.cookie, 'foo=bar; baz=yada', 'request cookies from morsels')

with subtest('JSON of the json module'):
    res = Pyjo.Message.Response.new().set(body=json.dumps({'foo': [1, 2, 3]}).encode())
    is_deeply_ok(res.json(), json.loads(res.body), 'same data')

with subtest('save_to with pathlib'):
    res = Pyjo.Message.Response.new().set(body=b'Hello World!')
    with tempfile.TemporaryDirectory() as dir:
        path = pathlib.Path(dir) / 'hello.txt'
        res.save_to(path)
        is_ok(path.read_bytes(), b'Hello World!', 'saved')

done_testing()
