# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor that Pyjo.Reactor.detect gives

import Pyjo.IOLoop
import Pyjo.IOLoop.Client
import Pyjo.IOLoop.TLS
import Pyjo.UserAgent

from Pyjo.Test import *
from Pyjoyment.Lite import app, get, websocket

import importlib
import os
import sys


# Left out from Mojolicious: plan skip_all unless TEST_SOCKS, as the SOCKS5 client and the proxy server of the tests are
# of Pyjoyment
if not Pyjo.IOLoop.Client.object.can_socks():
    plan(skip_all='SOCKS5 support required for this test!')
if not Pyjo.IOLoop.TLS.object.can_tls():
    plan(skip_all='TLS support required for this test!')

# The SOCKS proxy server of the tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
SocksServer = importlib.import_module('SocksServer')


# Silence
app.log.level = 'fatal'


@get('/')
def root(c):
    c.render(text=c.tx.remote_port)


@websocket('/echo')
def echo(c):
    c.on('message', lambda c, msg: c.send(str(c.tx.remote_port)))


@get('/secure')
def secure(c):
    c.render(text=f'{c.req.url.to_abs().protocol}:{c.tx.remote_port}')


# SOCKS proxy server for testing, in threads of its own, as the server of IO::Socket::Socks in Mojo's test
server = SocksServer.new('foo', 'bar')
port = server.port

with subtest('Failed authentication with SOCKS proxy'):
    ua = Pyjo.UserAgent.new(ioloop=Pyjo.IOLoop.singleton, insecure=True)
    ua.proxy.http = f'socks://foo:baz@127.0.0.1:{port}'
    tx = ua.get('/')
    ok(tx.error, 'has error')

with subtest('Simple request with SOCKS proxy'):
    ua = Pyjo.UserAgent.new(ioloop=Pyjo.IOLoop.singleton, insecure=True)
    ua.proxy.http = f'socks://foo:bar@127.0.0.1:{port}'
    tx = ua.get('/')
    ok(not tx.error, 'no error')
    ok(not tx.kept_alive, 'kept connection not alive')
    ok(tx.keep_alive, 'keep connection alive')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.req.headers.proxy_authorization, None, 'no "Proxy-Authorization" value')
    is_ok(tx.res.body, str(server.last).encode(), 'right content')
    isnt_ok(Pyjo.IOLoop.stream(tx.connection).handle.getsockname()[1], server.last, 'different ports')

    before = server.last
    tx = ua.get('/')
    ok(not tx.error, 'no error')
    ok(tx.kept_alive, 'kept connection alive')
    ok(tx.keep_alive, 'keep connection alive')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, str(server.last).encode(), 'right content')
    is_ok(before, server.last, 'same port')
    isnt_ok(Pyjo.IOLoop.stream(tx.connection).handle.getsockname()[1], server.last, 'different ports')

with subtest('WebSocket with SOCKS proxy'):
    ua = Pyjo.UserAgent.new(ioloop=Pyjo.IOLoop.singleton, insecure=True)
    ua.proxy.http = f'socks://foo:bar@127.0.0.1:{port}'
    result = {}

    @ua.websocket('/echo')
    def ws(ua, tx):
        result['id'] = tx.connection

        @tx.on('message')
        def message(tx, msg):
            result['msg'] = msg
            Pyjo.IOLoop.stop()

        tx.send('test')

    Pyjo.IOLoop.start()
    is_ok(result['msg'], str(server.last), 'right result')
    isnt_ok(Pyjo.IOLoop.stream(result['id']).handle.getsockname()[1], server.last, 'different ports')

with subtest('HTTPS request with SOCKS proxy'):
    ua = Pyjo.UserAgent.new(ioloop=Pyjo.IOLoop.singleton, insecure=True)
    ua.proxy.https = f'socks://foo:bar@127.0.0.1:{port}'
    ua.server.url('https')
    tx = ua.get('/secure')
    ok(not tx.error, 'no error')
    ok(not tx.kept_alive, 'kept connection not alive')
    ok(tx.keep_alive, 'keep connection alive')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, f'https:{server.last}'.encode(), 'right content')
    isnt_ok(Pyjo.IOLoop.stream(tx.connection).handle.getsockname()[1], server.last, 'different ports')

with subtest('Disabled SOCKS proxy'):
    ua = Pyjo.UserAgent.new(ioloop=Pyjo.IOLoop.singleton, insecure=True)
    ua.server.url('http')
    ua.proxy.http = f'socks://foo:baz@127.0.0.1:{port}'
    tx = ua.build_tx('GET', '/')
    tx.req.via_proxy = False
    tx = ua.start(tx)
    ok(not tx.error, 'no error')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, str(tx.local_port).encode(), 'right content')

server.close()

done_testing()
