import Pyjo.Cookie.Request
import Pyjo.Message.Request
import Pyjo.Parameters
import Pyjo.URL

from Pyjo.Test import *

import contextlib
import http.server
import io
import threading
import urllib.request


def output(cb):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        cb()
    return out.getvalue()


# A server of http.server for the examples with urllib.request.urlopen
class HiHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Length', '3')
        self.end_headers()
        self.wfile.write(b'Hi!')

    def log_message(self, *args):
        pass


server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), HiHandler)
threading.Thread(target=server.serve_forever, daemon=True).start()
port = server.server_address[1]


with subtest('Synopsis'):

    def parse():
        import Pyjo.Message.Request

        # Parse
        req = Pyjo.Message.Request.new()
        req.parse(b'GET /foo HTTP/1.0\x0d\x0a')
        req.parse(b'Content-Length: 12\x0d\x0a')
        req.parse(b'Content-Type: text/plain\x0d\x0a\x0d\x0a')
        req.parse(b'Hello World!')
        print(req.method)
        print(req.headers.content_type)
        print(req.body)

    is_ok(output(parse), "GET\ntext/plain\nb'Hello World!'\n", 'parse')

    def build():
        import Pyjo.Message.Request

        # Build
        req = Pyjo.Message.Request.new()
        req.url.parse('http://127.0.0.1/foo/bar')
        req.method = 'GET'
        print(req.to_bytes())

    is_ok(output(build), "b'GET /foo/bar HTTP/1.1\\r\\nHost: 127.0.0.1\\r\\n\\r\\n'\n", 'build')

with subtest('new'):
    req = Pyjo.Message.Request.new()
    is_ok(req.method, 'GET', 'default')
    req = Pyjo.Message.Request.new(method='POST', url=Pyjo.URL.new('http://127.0.0.1/'))
    is_ok(req.method, 'POST', 'method')
    is_ok(req.url, 'http://127.0.0.1/', 'URL')
    req = Pyjo.Message.Request.new(urllib.request.Request('http://127.0.0.1/', data=b'Hi!'))
    is_ok(req.method, 'POST', 'method of urllib')
    is_ok(req.url, 'http://127.0.0.1/', 'URL of urllib')
    is_ok(req.body, b'Hi!', 'data of urllib')

    import Pyjo.Message.Response

    # A request in a handler of http.server
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            req = Pyjo.Message.Request.new(self)
            res = Pyjo.Message.Response.new(code=200).set(body=bytes(req.url.path))
            self.wfile.write(res.to_bytes())

        def log_message(self, *args):
            pass

    handler_server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=handler_server.serve_forever, daemon=True).start()
    with urllib.request.urlopen(f'http://127.0.0.1:{handler_server.server_address[1]}/foo/bar') as response:
        is_ok(response.read(), b'/foo/bar', 'response of the handler')
    handler_server.shutdown()
    handler_server.server_close()

with subtest('env'):
    req = Pyjo.Message.Request.new()
    env = req.env
    is_deeply_ok(env, {}, 'default')
    req.env = {'PATH_INFO': '/'}
    is_deeply_ok(req.env, {'PATH_INFO': '/'}, 'set')

    req.env = {'GATEWAY_INTERFACE': 'CGI/1.1', 'wsgi.version': (1, 0)}
    version = req.env['GATEWAY_INTERFACE']
    is_ok(version, 'CGI/1.1', 'CGI version')
    version = req.env['wsgi.version']
    is_deeply_ok(version, (1, 0), 'WSGI version')

with subtest('method'):
    req = Pyjo.Message.Request.new()
    method = req.method
    is_ok(method, 'GET', 'default')
    req.method = 'POST'
    is_ok(req.method, 'POST', 'set')

with subtest('proxy'):
    req = Pyjo.Message.Request.new()
    url = req.proxy
    is_ok(url, None, 'default')
    req.proxy = Pyjo.URL.new('http://127.0.0.1:3000')
    is_ok(req.proxy, 'http://127.0.0.1:3000', 'set')

with subtest('reverse_proxy'):
    req = Pyjo.Message.Request.new()
    boolean = req.reverse_proxy
    is_ok(boolean, None, 'default')
    req.reverse_proxy = True
    is_ok(req.reverse_proxy, True, 'set')

with subtest('trusted_proxies'):
    req = Pyjo.Message.Request.new()
    proxies = req.trusted_proxies
    is_deeply_ok(proxies, [], 'default')
    req.trusted_proxies = ['10.0.0.0/8', '127.0.0.1', '172.16.0.0/12', '192.168.0.0/16', 'fc00::/7']
    is_ok(len(req.trusted_proxies), 5, 'set')

with subtest('via_proxy'):
    req = Pyjo.Message.Request.new()
    boolean = req.via_proxy
    is_ok(boolean, True, 'default')
    req.via_proxy = False
    is_ok(req.via_proxy, False, 'set')

with subtest('request_id'):
    req = Pyjo.Message.Request.new()
    request_id = req.request_id
    like_ok(request_id, r'^[\w-]{12}$', 'default')
    req.request_id = 'aee7d5d8'
    is_ok(req.request_id, 'aee7d5d8', 'set')

with subtest('url'):
    req = Pyjo.Message.Request.new()
    url = req.url
    isa_ok(url, Pyjo.URL.object, 'default')
    req.url = Pyjo.URL.new()
    ok(req.url is not url, 'set')

    req.parse(b'GET /foo HTTP/1.1\x0d\x0aHost: localhost\x0d\x0aAuthorization: Basic c3JpOnNlY3JldA==\x0d\x0a\x0d\x0a')
    info = req.url.to_abs().userinfo
    is_ok(info, 'sri:secret', 'userinfo')
    host = req.url.to_abs().host
    is_ok(host, 'localhost', 'host')
    path = req.url.to_abs().path
    is_ok(path, '/foo', 'path')

with subtest('clone'):
    req = Pyjo.Message.Request.new()
    clone = req.clone()
    isa_ok(clone, Pyjo.Message.Request.object, 'clone')

with subtest('cookies'):
    req = Pyjo.Message.Request.new()
    cookies = req.cookies()
    is_deeply_ok(cookies, [], 'no cookies')
    req = req.cookies(Pyjo.Cookie.Request.new(name='foo', value='bar'))
    req = req.cookies({'name': 'bar', 'value': 'baz'})
    is_ok(req.headers.cookie, 'foo=bar; bar=baz', 'added')

    def names():
        for cookie in req.cookies():
            print(cookie.name)

    is_ok(output(names), 'foo\nbar\n', 'names of all cookies')

with subtest('every_param'):
    req = Pyjo.Message.Request.new()
    req.url.parse('/?foo=bar&foo=baz')
    values = req.every_param('foo')
    is_deeply_ok(values, ['bar', 'baz'], 'values')

    is_ok(output(lambda: print(req.every_param('foo')[0])), 'bar\n', 'first value')

with subtest('extract_start_line'):
    req = Pyjo.Message.Request.new()
    buffer = bytearray(b'GET / HTTP/1.1\x0d\x0a')
    boolean = req.extract_start_line(buffer)
    ok(boolean, 'request-line extracted')
    is_ok(buffer, b'', 'buffer lost the request-line')

with subtest('fix_headers'):
    req = Pyjo.Message.Request.new()
    req.url.parse('http://127.0.0.1/')
    req = req.fix_headers()
    is_ok(req.headers.host, '127.0.0.1', 'Host')

with subtest('get_start_line_chunk'):
    req = Pyjo.Message.Request.new()
    offset = 0
    data = req.get_start_line_chunk(offset)
    is_ok(data, b'GET / HTTP/1.1\x0d\x0a', 'chunk')

with subtest('is_handshake'):
    req = Pyjo.Message.Request.new()
    req.headers.upgrade = 'websocket'
    boolean = req.is_handshake
    is_ok(boolean, True, 'handshake')

with subtest('is_secure'):
    req = Pyjo.Message.Request.new()
    req.url.parse('https://127.0.0.1/')
    boolean = req.is_secure
    is_ok(boolean, True, 'secure')

with subtest('is_xhr'):
    req = Pyjo.Message.Request.new()
    req.headers.header('X-Requested-With', 'XMLHttpRequest')
    boolean = req.is_xhr
    is_ok(boolean, True, 'XMLHttpRequest')

with subtest('param'):
    req = Pyjo.Message.Request.new()
    req.url.parse('/?foo=bar')
    value = req.param('foo')
    is_ok(value, 'bar', 'value')

with subtest('params'):
    req = Pyjo.Message.Request.new()
    req.url.parse('/?foo=bar')
    params = req.params
    isa_ok(params, Pyjo.Parameters.object, 'parameters')

    params = req.params.to_dict()
    is_deeply_ok(params, {'foo': 'bar'}, 'names and values')

with subtest('parse'):
    req = Pyjo.Message.Request.new()
    req = req.parse(b'GET /foo/bar HTTP/1.1')
    isa_ok(req, Pyjo.Message.Request.object, 'chunk')
    req = Pyjo.Message.Request.new()
    req = req.parse({'PATH_INFO': '/'})
    ok(req.is_finished, 'environment')

with subtest('query_params'):
    req = Pyjo.Message.Request.new()
    req.url.parse('/?foo=bar')
    params = req.query_params
    isa_ok(params, Pyjo.Parameters.object, 'parameters')

    is_ok(output(lambda: print(req.query_params.to_dict()['foo'])), 'bar\n', 'value')

with subtest('start_line_size'):
    req = Pyjo.Message.Request.new()
    size = req.start_line_size
    is_ok(size, 16, 'size')

with subtest('to_urllib'):
    import Pyjo.Message.Response

    req = Pyjo.Message.Request.new()
    req.url.parse(f'http://127.0.0.1:{port}/')
    request = req.to_urllib()
    isa_ok(request, urllib.request.Request, 'request')

    # Send the request with urllib
    with urllib.request.urlopen(req.to_urllib()) as response:
        res = Pyjo.Message.Response.new(response)
    is_ok(res.body, b'Hi!', 'res.body')

server.shutdown()
server.server_close()

done_testing()
