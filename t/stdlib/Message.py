import Pyjo.Cookie.Request
import Pyjo.Message.Request
import Pyjo.Message.Response
import Pyjo.Transaction.HTTP
import Pyjo.URL
import Pyjo.UserAgent
import Pyjo.UserAgent.Transactor

from Pyjo.Test import *

import http
import http.client
import http.cookies
import http.server
import io
import json
import pathlib
import re
import tempfile
import threading
import urllib.error
import urllib.request
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

with subtest('Request from urllib.request.Request'):
    request = urllib.request.Request(
        'http://foo:bar@127.0.0.1:3000/foo?bar=baz#yada', data=b'Hello World!', headers={'Content-Type': 'text/plain'}
    )
    req = Pyjo.Message.Request.new(request)
    is_ok(req.method, 'POST', 'method of data')
    is_ok(req.url.to_unsafe_str(), 'http://foo:bar@127.0.0.1:3000/foo?bar=baz#yada', 'URL')
    is_ok(req.headers.content_type, 'text/plain', 'header')
    is_ok(req.body, b'Hello World!', 'body')
    req = Pyjo.Message.Request.new(urllib.request.Request('http://127.0.0.1/', method='DELETE'))
    is_ok(req.method, 'DELETE', 'method')
    is_ok(req.body, b'', 'no body')
    req = Pyjo.Message.Request.new(urllib.request.Request('http://127.0.0.1/', data=io.BytesIO(b'file')))
    is_ok(req.body, b'file', 'body of a file')
    req = Pyjo.Message.Request.new(urllib.request.Request('http://127.0.0.1/', data=[b'Hello ', b'World!']))
    is_ok(req.body, b'Hello World!', 'body of an iterable')
    req = Pyjo.Message.Request.new(urllib.request.Request('http://127.0.0.1/', data=memoryview(b'view')))
    is_ok(req.body, b'view', 'body of a memoryview')

with subtest('Request to urllib.request.Request'):
    req = Pyjo.Message.Request.new(method='PUT')
    req.url.parse('http://foo:bar@127.0.0.1:3000/foo?bar=baz')
    req.headers.content_type = 'text/plain'
    req.body = b'Hello World!'
    request = req.to_urllib()
    isa_ok(request, urllib.request.Request, 'request')
    is_ok(request.get_method(), 'PUT', 'method')
    is_ok(request.full_url, 'http://127.0.0.1:3000/foo?bar=baz', 'URL without userinfo')
    is_ok(request.get_header('Authorization'), 'Basic Zm9vOmJhcg==', 'userinfo as Authorization')
    is_ok(request.get_header('Content-type'), 'text/plain', 'header')
    is_ok(request.data, b'Hello World!', 'data')

    req = Pyjo.Message.Request.new().parse(b'GET /foo HTTP/1.1\x0d\x0aHost: 127.0.0.1:3000\x0d\x0a\x0d\x0a')
    request = req.to_urllib()
    is_ok(request.full_url, 'http://127.0.0.1:3000/foo', 'absolute URL of a parsed request')
    is_ok(request.data, None, 'no data')

    tx = Pyjo.UserAgent.Transactor.new().tx('POST', 'http://127.0.0.1/', form={'file': {'content': 'Hello!'}})
    request = tx.req.to_urllib()
    boundary = re.search(r'boundary=(\w+)', request.get_header('Content-type')).group(1)
    like_ok(request.data, rb'^--' + boundary.encode() + rb'\r\n.*\r\n\r\nHello!\r\n', 'multipart data')

    req = Pyjo.Message.Request.new(proxy=Pyjo.URL.new('http://foo:bar@127.0.0.1:8080'))
    req.url.parse('http://example.com/')
    request = req.to_urllib()
    is_ok(request.host, '127.0.0.1:8080', 'proxy')
    is_ok(request.selector, 'http://example.com/', 'absolute URL for the proxy')
    is_ok(request.get_header('Proxy-authorization'), 'Basic Zm9vOmJhcg==', 'userinfo as Proxy-Authorization')
    req.via_proxy = False
    request = req.to_urllib()
    is_ok(request.host, 'example.com', 'no proxy')

with subtest('Response to http.client.HTTPResponse'):
    res = Pyjo.Message.Response.new(code=404)
    res.headers.content_type = 'text/plain'
    res.body = b'Not here!'
    response = res.to_urllib(url='http://127.0.0.1/foo')
    isa_ok(response, http.client.HTTPResponse, 'response')
    is_ok(response.status, 404, 'status')
    is_ok(response.reason, 'Not Found', 'reason')
    is_ok(response.version, 11, 'version')
    is_ok(response.getheader('Content-Type'), 'text/plain', 'header')
    is_ok(response.geturl(), 'http://127.0.0.1/foo', 'URL')
    is_ok(response.read(), b'Not here!', 'body')

    res = Pyjo.Message.Response.new(code=200)
    res.content.write_chunk(b'Hello ').write_chunk(b'World!').write_chunk(b'')
    response = res.to_urllib()
    ok(response.chunked, 'chunked')
    is_ok(response.read(), b'Hello World!', 'decoded body')

    res = Pyjo.Message.Response.new(code=200)
    res.headers.content_length = 12
    is_ok(res.to_urllib(method='HEAD').read(), b'', 'no body for HEAD')

with subtest('Response from http.client.HTTPResponse'):
    res = Pyjo.Message.Response.new(code=201, message='Done', version='1.0')
    res.content.write_chunk(b'Hello ').write_chunk(b'World!').write_chunk(b'')
    res = Pyjo.Message.Response.new(res.to_urllib())
    is_ok(res.code, 201, 'code')
    is_ok(res.message, 'Done', 'message')
    is_ok(res.version, '1.0', 'version')
    is_ok(res.headers.transfer_encoding, None, 'no transfer encoding')
    is_ok(res.headers.content_length, '12', 'length of the body')
    is_ok(res.body, b'Hello World!', 'body')

with subtest('Response from urllib.response.addinfourl'):
    res = Pyjo.Message.Response.new(urllib.request.urlopen('data:text/plain,Hello%20World!'))
    is_ok(res.code, 200, 'code of a data: URL')
    is_ok(res.headers.content_type, 'text/plain', 'header')
    is_ok(res.body, b'Hello World!', 'body')


# A server of http.server that answers with the request
class EchoHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = f'{self.command} {self.path} {self.headers["Authorization"]} '.encode()
        body += self.rfile.read(int(self.headers['Content-Length'] or 0))
        self.send_response(404 if self.path == '/missing' else 200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_POST = do_GET

    def log_message(self, *args):
        pass


with subtest('Request and response through urllib.request.urlopen'):
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), EchoHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    port = server.server_address[1]

    req = Pyjo.Message.Request.new(method='POST')
    req.url.parse(f'http://foo:bar@127.0.0.1:{port}/echo')
    req.body = b'Hello World!'
    with urllib.request.urlopen(req.to_urllib(), timeout=10) as response:
        res = Pyjo.Message.Response.new(response)
    is_ok(res.code, 200, 'code')
    is_ok(res.message, 'OK', 'message')
    is_ok(res.headers.content_type, 'text/plain', 'header')
    is_ok(res.body, b'POST /echo Basic Zm9vOmJhcg== Hello World!', 'body')

    req = Pyjo.Message.Request.new()
    req.url.parse(f'http://127.0.0.1:{port}/missing')
    try:
        urllib.request.urlopen(req.to_urllib(), timeout=10)
    except urllib.error.HTTPError as e:
        with e:
            res = Pyjo.Message.Response.new(e)
    is_ok(res.code, 404, 'code of an HTTPError')
    is_ok(res.message, 'Not Found', 'message of an HTTPError')
    is_ok(res.body, b'GET /missing None ', 'body of an HTTPError')

    with subtest('Request of urllib with the user agent'):
        request = urllib.request.Request(f'http://127.0.0.1:{port}/ua', data=b'Hi!')
        tx = Pyjo.UserAgent.new().start(Pyjo.Transaction.HTTP.new(req=Pyjo.Message.Request.new(request)))
        is_ok(tx.res.code, 200, 'code')
        is_ok(tx.res.body, b'POST /ua None Hi!', 'body')

    server.shutdown()
    server.server_close()
    thread.join()


done_testing()
