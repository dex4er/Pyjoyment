# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor that Pyjo.Reactor.detect gives

import Pyjo.IOLoop
import Pyjo.Server.Daemon
import Pyjo.UserAgent

from Pyjo.File import tempdir
from Pyjo.Test import *
from Pyjo.Util import url_escape

import gc
import importlib
import os
import re
import socket
import stat
import sys


# Left out from Mojolicious: plan skip_all unless TEST_UNIX, as the test needs nothing but UNIX domain sockets
dir = tempdir()
dummy = dir.child('dummy.sock').to_str()
try:
    with socket.socket(socket.AF_UNIX) as sock:
        sock.bind(dummy)
        sock.listen(1)
except (AttributeError, OSError):
    plan(skip_all='UNIX domain socket support required for this test!')

# The minimal Mojolicious::Lite and the CONNECT proxy of the tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
Lite = importlib.import_module('Lite')
TestConnectProxy = importlib.import_module('TestConnectProxy')
app, get, websocket = Lite.app, Lite.get, Lite.websocket

# Silence
app.log.level = 'fatal'


@get('/')
def root(c):
    c.render(text=c.req.url)


@get('/info')
def info(c):
    local_address = c.tx.local_address
    local_port = c.tx.local_port
    remote_address = c.tx.remote_address
    remote_port = c.tx.remote_port
    c.render(text=f'{local_address}:{local_port}:{remote_address}:{remote_port}')


@websocket('/echo')
def echo(c):
    c.on('message', lambda c, msg: c.send(f'{c.req.url.to_abs().host}: {msg}').finish())


# UNIX domain socket server
test = dir.child('test.sock')
encoded = url_escape(test.to_str())
ok(not os.environ.get('PYJO_REUSE'), 'environment is clean')
daemon = Pyjo.Server.Daemon.new(app=app, listen=[f'http+unix://{encoded}'], silent=True).start()
ok(stat.S_ISSOCK(os.stat(test).st_mode), 'UNIX domain socket exists')
fd = daemon.ioloop.acceptor(daemon.acceptors[0]).handle.fileno()
like_ok(os.environ.get('PYJO_REUSE', ''), rf'^unix:{re.escape(test.to_str())}:{fd}', 'file descriptor can be reused')

ua = Pyjo.UserAgent.new(ioloop=daemon.ioloop)

with subtest('Root'):
    tx = ua.get(f'http+unix://{encoded}/')
    ok(not tx.kept_alive, 'connection was not kept alive')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, b'/', 'right content')
    tx = ua.get(f'http+unix://{encoded}/')
    ok(tx.kept_alive, 'connection was kept alive')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, b'/', 'right content')

with subtest('Connection information'):
    tx = ua.get(f'http+unix://{encoded}/info')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, b'None:None:None:None', 'right content')


def roundtrip(results):
    def cb(ua, tx):
        tx.on('finish', lambda tx, *args: Pyjo.IOLoop.stop())

        @tx.on('message')
        def message(tx, msg):
            tx.finish()
            results.append(msg)

        tx.send('roundtrip works!')

    return cb


with subtest('WebSocket'):
    result = []
    ua.websocket(f'ws+unix://{encoded}/echo', roundtrip(result))
    Pyjo.IOLoop.start()
    is_ok(result[0], f'{test}: roundtrip works!', 'right result')

with subtest('WebSocket again'):
    result = []
    ua.websocket(f'ws+unix://{encoded}/echo', roundtrip(result))
    Pyjo.IOLoop.start()
    is_ok(result[0], f'{test}: roundtrip works!', 'right result')

with subtest('WebSocket with proxy'):
    proxy = dir.child('proxy.sock')
    encoded_proxy = url_escape(proxy.to_str())
    id = TestConnectProxy.proxy({'path': proxy.to_str()}, {'path': test.to_str()})
    result = []
    ua.proxy.http = f'http+unix://{encoded_proxy}'
    ua.websocket('ws://example.com/echo', roundtrip(result))
    Pyjo.IOLoop.start()
    is_ok(result[0], 'example.com: roundtrip works!', 'right result')
    Pyjo.IOLoop.remove(id)

with subtest('Proxy'):
    ua.proxy.http = f'http+unix://{encoded}'
    tx = ua.get('http://example.com')
    ok(not tx.kept_alive, 'connection was not kept alive')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, b'http://example.com', 'right content')
    tx = ua.get('http://example.com')
    ok(tx.kept_alive, 'connection was kept alive')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, b'http://example.com', 'right content')

# Cleanup
del daemon
# Not in Mojolicious: PyPy frees the daemon when its garbage collector runs
gc.collect()
ok(not os.environ.get('PYJO_REUSE'), 'environment is clean')

done_testing()
