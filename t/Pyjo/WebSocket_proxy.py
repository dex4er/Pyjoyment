# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

import Pyjo.IOLoop
import Pyjo.Server.Daemon
import Pyjo.UserAgent

from Pyjo.File import curfile
from Pyjo.Test import *
from Pyjoyment.Lite import app, get, websocket

import sys


sys.path.insert(0, curfile().sibling('..', 'lib').to_str())

import TestConnectProxy  # noqa: E402  # pyright: ignore[reportMissingImports]


# Silence
app.log.level = 'fatal'


@get('/')
def index(c):
    rel = c.req.url
    abs = rel.to_abs()
    c.render(text=f'Hello World! {rel} {abs}')


@get('/proxy')
def proxy_action(c):
    c.render(text=c.req.url)


@websocket('/test')
def test(c):
    c.on('message', lambda c, msg: c.send(msg + 'test2'))


# HTTP server for testing
daemon = Pyjo.Server.Daemon.new(app=app, silent=True)
daemon.listen = ['http://127.0.0.1']
port = daemon.start().ports()[0]

# CONNECT proxy server for testing
id = TestConnectProxy.proxy({'address': '127.0.0.1'}, {'address': '127.0.0.1', 'port': port})
proxy = Pyjo.IOLoop.acceptor(id).port

with subtest('Normal requests'):
    ua = Pyjo.UserAgent.new(ioloop=Pyjo.IOLoop.singleton)

    with subtest('Normal non-blocking request'):
        got = {}

        def normal(ua, tx):
            got['result'] = tx.res.text
            Pyjo.IOLoop.stop()

        ua.get(f'http://127.0.0.1:{port}/', normal)
        Pyjo.IOLoop.start()
        is_ok(got['result'], f'Hello World! / http://127.0.0.1:{port}/', 'right content')

    with subtest('Normal WebSocket'):
        got = {}

        @ua.websocket(f'ws://127.0.0.1:{port}/test')
        def normal_ws(ua, tx):
            tx.on('finish', lambda *args: Pyjo.IOLoop.stop())

            @tx.on('message')
            def message(tx, msg):
                tx.finish()
                got['result'] = msg

            tx.send('test1')

        Pyjo.IOLoop.start()
        is_ok(got['result'], 'test1test2', 'right result')

with subtest('Proxy requests'):
    ua = Pyjo.UserAgent.new(ioloop=Pyjo.IOLoop.singleton)
    ua.proxy.http = f'http://127.0.0.1:{port}'

    with subtest('Non-blocking proxy request'):
        got = {}

        def proxy_request(ua, tx):
            got.update(kept_alive=tx.kept_alive, result=tx.res.text)
            Pyjo.IOLoop.stop()

        ua.get('http://example.com/proxy', proxy_request)
        Pyjo.IOLoop.start()
        ok(not got['kept_alive'], 'connection was not kept alive')
        is_ok(got['result'], 'http://example.com/proxy', 'right content')

    with subtest('Kept alive proxy WebSocket'):
        got = {}

        @ua.websocket(f'ws://127.0.0.1:{port}/test')
        def kept_alive(ua, tx):
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

    with subtest('Blocking proxy request'):
        tx = ua.get('http://example.com/proxy')
        is_ok(tx.res.code, 200, 'right status')
        is_ok(tx.res.text, 'http://example.com/proxy', 'right content')

with subtest('Proxy Websocket requests'):
    ua = Pyjo.UserAgent.new()
    ua.proxy.http = f'http://127.0.0.1:{proxy}'

    with subtest('Proxy WebSocket'):
        got = {}

        @ua.websocket(f'ws://127.0.0.1:{port}/test')
        def proxy_ws(ua, tx):
            tx.on('finish', lambda *args: Pyjo.IOLoop.stop())

            @tx.on('message')
            def message(tx, msg):
                tx.finish()
                got['result'] = msg

            tx.send('test1')

        Pyjo.IOLoop.start()
        is_ok(got['result'], 'test1test2', 'right result')

    with subtest('Proxy WebSocket with bad target'):
        got = {}

        @ua.websocket('ws://127.0.0.1:0/test')
        def bad_target(ua, tx):
            got.update(leak=bool(Pyjo.IOLoop.stream(tx.previous.connection)), err=tx.error)
            Pyjo.IOLoop.stop()

        Pyjo.IOLoop.start()
        ok(not got['leak'], 'connection has been removed')
        is_ok(got['err']['message'], 'Proxy connection failed', 'right message')

done_testing()
