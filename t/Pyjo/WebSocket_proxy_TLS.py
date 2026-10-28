# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

import Pyjo.IOLoop
import Pyjo.IOLoop.Server
import Pyjo.IOLoop.TLS
import Pyjo.Server.Daemon
import Pyjo.UserAgent

from Pyjo.File import curfile
from Pyjo.Test import *
from Pyjoyment.Lite import app, get, websocket

import sys


sys.path.insert(0, curfile().sibling('..', 'lib').to_str())

import TestConnectProxy  # noqa: E402  # pyright: ignore[reportMissingImports]


# Left out from Mojolicious: plan skip_all unless TEST_TLS, as the ssl module comes with Python
if not Pyjo.IOLoop.TLS.object.can_tls():
    plan(skip_all='TLS support required for this test!')

# Renamed from Mojolicious: the certificates of the tests are in t/certs, where Mojo has them in t/mojo/certs
certs = curfile().sibling('..', 'certs')

# Silence
app.log.level = 'fatal'


@get('/')
def index(c):
    c.res.headers.header('X-Works', c.req.headers.header('X-Works') or '')
    rel = c.req.url
    abs = rel.to_abs()
    c.render(text=f'Hello World! {rel} {abs}')


@get('/broken_redirect')
def broken_redirect(c):
    c.render(text='Redirecting!', status=302)
    c.res.headers.location = '/'


@get('/proxy')
def proxy_action(c):
    c.render(text=c.req.url.to_abs())


@websocket('/test')
def test(c):
    c.on('message', lambda c, msg: c.send(msg + 'test2'))


# Web server with valid certificates
daemon = Pyjo.Server.Daemon.new(app=app, silent=True)
listen = (
    f'https://127.0.0.1?cert={certs.child("server.crt")}&key={certs.child("server.key")}&ca={certs.child("ca.crt")}'
)
daemon.listen = [listen]
port = daemon.start().ports()[0]

# Connect proxy server for testing
zero = b'HTTP/1.1 501 FOO\x0d\x0a' + b'Content-Length: 0\x0d\x0a' + b'Connection: close\x0d\x0a\x0d\x0a'
id = TestConnectProxy.proxy({'address': '127.0.0.1'}, {'address': '127.0.0.1', 'port': port}, None, zero)
proxy = Pyjo.IOLoop.acceptor(id).port

# User agent with valid certificates
ua = Pyjo.UserAgent.new(
    ioloop=Pyjo.IOLoop.singleton,
    ca=certs.child('ca.crt').to_str(),
    cert=certs.child('client.crt').to_str(),
    key=certs.child('client.key').to_str(),
)

got = {}

with subtest('Normal non-blocking request'):

    def normal(ua, tx):
        got['result'] = tx.res.text
        Pyjo.IOLoop.stop()

    ua.get(f'https://127.0.0.1:{port}/', normal)
    Pyjo.IOLoop.start()
    is_ok(got['result'], f'Hello World! / https://127.0.0.1:{port}/', 'right content')

with subtest('Broken redirect'):
    got['start'] = 0

    @ua.on('start')
    def start(ua, tx):
        got['start'] += 1
        tx.req.headers.header('X-Works', 'it does!')

    got['result'] = None

    def broken(ua, tx):
        got.update(result=tx.res.text, works=tx.res.headers.header('X-Works'))
        Pyjo.IOLoop.stop()

    ua.max_redirects = 3
    ua.get(f'https://127.0.0.1:{port}/broken_redirect', broken)
    Pyjo.IOLoop.start()
    is_ok(got['result'], f'Hello World! / https://127.0.0.1:{port}/', 'right content')
    is_ok(got['works'], 'it does!', 'right header')
    is_ok(got['start'], 2, 'redirected once')
    ua.unsubscribe('start')

with subtest('Normal WebSocket'):
    got['result'] = None

    @ua.websocket(f'wss://127.0.0.1:{port}/test')
    def normal_ws(ua, tx):
        tx.on('finish', lambda *args: Pyjo.IOLoop.stop())

        @tx.on('message')
        def message(tx, msg):
            tx.finish()
            got['result'] = msg

        tx.send('test1')

    Pyjo.IOLoop.start()
    is_ok(got['result'], 'test1test2', 'right result')

with subtest('Non-blocking proxy request'):
    ua.proxy.https = f'http://sri:secr3t@127.0.0.1:{proxy}'
    got['result'] = None

    def proxy_request(ua, tx):
        got.update(result=tx.res.text, auth=tx.req.headers.proxy_authorization, kept_alive=tx.kept_alive)
        Pyjo.IOLoop.stop()

    ua.get(f'https://127.0.0.1:{port}/proxy', proxy_request)
    Pyjo.IOLoop.start()
    ok(not got['auth'], 'no "Proxy-Authorization" header')
    ok(not got['kept_alive'], 'connection was not kept alive')
    is_ok(got['result'], f'https://127.0.0.1:{port}/proxy', 'right content')

with subtest('Non-blocking kept alive proxy request'):
    got.update(kept_alive=None, result=None)

    def kept_alive_request(ua, tx):
        got.update(kept_alive=tx.kept_alive, result=tx.res.text)
        Pyjo.IOLoop.stop()

    ua.get(f'https://127.0.0.1:{port}/proxy', kept_alive_request)
    Pyjo.IOLoop.start()
    is_ok(got['result'], f'https://127.0.0.1:{port}/proxy', 'right content')
    ok(got['kept_alive'], 'connection was kept alive')

with subtest('Kept alive proxy WebSocket'):
    ua.proxy.https = f'http://127.0.0.1:{proxy}'
    got.update(kept_alive=None, result=None)

    @ua.websocket(f'wss://127.0.0.1:{port}/test')
    def kept_alive_ws(ua, tx):
        got['kept_alive'] = tx.kept_alive
        tx.on('finish', lambda *args: Pyjo.IOLoop.stop())

        @tx.on('message')
        def message(tx, msg):
            tx.finish()
            got['result'] = msg

        tx.send('test1')

    Pyjo.IOLoop.start()
    ok(got['kept_alive'], 'connection was kept alive')
    is_ok(got['result'], 'test1test2', 'right result')

with subtest('Blocking proxy requests'):
    ua.proxy.https = f'http://sri:secr3t@127.0.0.1:{proxy}'
    ua.max_connections = 0
    tx = ua.get(f'https://127.0.0.1:{port}/proxy')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.text, f'https://127.0.0.1:{port}/proxy', 'right content')
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(tx.previous.req.method, 'CONNECT', 'right method')
    ua.max_connections = 5
    tx = ua.get(f'https://127.0.0.1:{port}/proxy')
    ok(not tx.kept_alive, 'connection was not kept alive')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.text, f'https://127.0.0.1:{port}/proxy', 'right content')
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(tx.previous.req.method, 'CONNECT', 'right method')

with subtest('Proxy WebSocket with bad target'):
    ua.proxy.https = f'http://127.0.0.1:{proxy}'
    got.update(leak=None, err=None)

    @ua.websocket('wss://127.0.0.1:0/test')
    def bad_target(ua, tx):
        got.update(leak=bool(Pyjo.IOLoop.stream(tx.previous.connection)), err=tx.error)
        Pyjo.IOLoop.stop()

    Pyjo.IOLoop.start()
    ok(not got['leak'], 'connection has been removed')
    is_ok(got['err']['message'], 'Proxy connection failed', 'right error')

with subtest('Blocking proxy request again'):
    tx = ua.get(f'https://127.0.0.1:{port}/proxy')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.text, f'https://127.0.0.1:{port}/proxy', 'right content')


with subtest('Failed TLS handshake through proxy'):

    def close_server(loop, stream, id):
        stream.on('read', lambda stream, chunk: stream.close())

    close = Pyjo.IOLoop.acceptor(Pyjo.IOLoop.server(close_server)).port
    id = TestConnectProxy.proxy({'address': '127.0.0.1'}, {'address': '127.0.0.1', 'port': close})
    proxy2 = Pyjo.IOLoop.acceptor(id).port
    ua.proxy.https = f'http://127.0.0.1:{proxy2}'
    tx = ua.get('https://example.com')
    # Unlike Mojolicious: the message of the ssl module of Python, of an end of file, which CPython and PyPy word
    # differently, where IO::Socket::SSL has "SSL connect attempt"
    like_ok(tx.error['message'], r'(?i)\beof\b', 'right error')

with subtest('Idle connection through proxy'):
    idle = Pyjo.IOLoop.acceptor(Pyjo.IOLoop.server(lambda loop, stream, id: None)).port
    id = TestConnectProxy.proxy({'address': '127.0.0.1'}, {'address': '127.0.0.1', 'port': idle})
    proxy3 = Pyjo.IOLoop.acceptor(id).port

    @ua.on('start')
    def connect_timeout(ua, tx):
        if tx.req.method == 'CONNECT':
            ua.connect_timeout = 0.25

    ua.proxy.https = f'http://127.0.0.1:{proxy3}'
    tx = ua.get('https://example.com')
    is_ok(tx.error['message'], 'Connect timeout', 'right error')
    ua.connect_timeout = 10

with subtest('Blocking request to bad proxy'):
    ua = Pyjo.UserAgent.new()
    proxy = Pyjo.IOLoop.Server.object.generate_port()
    ua.proxy.https = f'http://127.0.0.1:{proxy}'
    tx = ua.get(f'https://127.0.0.1:{port}/proxy')
    is_ok(tx.error['message'], 'Proxy connection failed', 'right error')

with subtest('Non-blocking request to bad proxy'):
    ua = Pyjo.UserAgent.new()
    proxy = Pyjo.IOLoop.Server.object.generate_port()
    ua.proxy.https = f'http://127.0.0.1:{proxy}'
    got['err'] = None

    def bad_proxy(ua, tx):
        got['err'] = tx.error
        Pyjo.IOLoop.stop()

    ua.get(f'https://127.0.0.1:{port}/proxy', bad_proxy)
    Pyjo.IOLoop.start()
    is_ok(got['err']['message'], 'Proxy connection failed', 'right error')

done_testing()
