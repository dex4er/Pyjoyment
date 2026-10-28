import Pyjo.IOLoop
import Pyjo.Promise
import Pyjo.Transaction.WebSocket

from Pyjo.String.Unicode import u
from Pyjo.Test import *
from Pyjo.WebSocket import build_frame
from Pyjoyment.Lite import app, get, websocket

import contextlib
import os
import re


# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()


# Not in Mojolicious: local of the environment
@contextlib.contextmanager
def local(**env):
    saved = {name: os.environ.get(name) for name in env}
    for name, value in env.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
    try:
        yield
    finally:
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


# Max WebSocket size
with local(PYJO_MAX_WEBSOCKET_SIZE='1024'):
    is_ok(Pyjo.Transaction.WebSocket.new().max_websocket_size, 1024, 'right value')

# Silence
app.log.level = 'trace'
app.log.unsubscribe('message')

# Avoid exception template
app.renderer.paths[0] = app.home.child('public').to_str()


@get('/link')
def link(c):
    c.render(text=c.url_for('index').to_abs())


@websocket('/', 'index')
def index(c):
    @c.on('finish')
    def finish(c, *args):
        c.stash()['finished'] = c.stash().get('finished', 0) + 1

    @c.on('message')
    def message(c, msg):
        url = c.url_for().to_abs()
        c.send(f'{msg}test2{url}')


@get('/something/else')
def something_else(c):
    timeout = Pyjo.IOLoop.singleton.stream(c.tx.connection).timeout
    # Not in Mojolicious: the number as Perl prints it, without a fraction of nothing
    c.render(text=f'{timeout:g}failed!')


@websocket('/early_start')
def early_start(c):
    c.send('test' + ('1' if c.tx.established else '0'))

    @c.on('message')
    def message(c, msg):
        c.send(f'{msg}test' + ('1' if c.tx.established else '0'))
        c.finish(1000, 'I ♥ Mojolicious!')


@websocket('/early_finish')
def early_finish(c):
    Pyjo.IOLoop.next_tick(lambda loop: c.rendered(101).finish(4000, 'kaboom'))


@websocket('/denied')
def denied(c):
    @c.tx.handshake.on('finish')
    def handshake(tx):
        c.stash()['handshake'] = c.stash().get('handshake', 0) + 1

    @c.on('finish')
    def finish(c, *args):
        c.stash()['finished'] = c.stash().get('finished', 0) + 1

    c.render(text='denied', status=403)


@websocket('/subreq')
def subreq(c):
    @c.ua().websocket('/echo')
    def echo(ua, tx):
        @tx.on('message')
        def message(tx, msg):
            c.send(msg)
            tx.finish()
            c.finish()

        tx.send('test1')

    c.send('test0')

    @c.on('finish')
    def finish(c, *args):
        c.stash()['finished'] = c.stash().get('finished', 0) + 1


@websocket('/echo')
def echo(c):
    c.on('message', lambda c, msg: c.send(msg))


@websocket('/double_echo')
def double_echo(c):
    @c.on('message')
    def message(c, msg):
        c.send(msg, lambda c: c.send(msg))


@websocket('/trim')
def trim(c):
    c.on('message', lambda c, msg: c.send(u(msg).trim()))


@websocket('/dead')
def dead(c):
    raise Exception('i see dead processes')


@websocket('/foo')
def foo(c):
    res = c.rendered().res
    res.code = 403
    res.message = "i'm a teapot"


@websocket('/close')
def close(c):
    c.on('message', lambda c, msg: Pyjo.IOLoop.remove(c.tx.connection))


@websocket('/timeout')
def timeout(c):
    @c.inactivity_timeout(0.25).on('finish')
    def finish(c, *args):
        c.stash()['finished'] = c.stash().get('finished', 0) + 1


# Not in Mojolicious: a handshake whose response waits, as an ASGI application waits for its websocket.accept
@websocket('/later')
def later(c):
    c.render_later().stash()['ws'] = c.tx

    @c.tx.on('finish')
    def finish(ws, code, reason):
        c.stash()['finished'] = code
        Pyjo.IOLoop.stop()


# Not in Mojolicious: a WebSocket kept alive with pings, past its inactivity timeout
@websocket('/heartbeat')
def heartbeat(c):
    c.inactivity_timeout(0.3)
    c.stash()['ws'] = c.tx.heartbeat(0.05, 0.2)
    if c.param('stop'):
        c.tx.heartbeat(None)

    @c.on('finish')
    def finish(c, code, reason):
        c.stash()['finished'] = code


ua = app.ua

with subtest('URL for WebSocket'):
    res = ua.get('/link').result
    is_ok(res.code, 200, 'right status')
    like_ok(res.text, r'ws://127\.0\.0\.1:\d+/', 'right content')

with subtest('Plain HTTP request'):
    res = ua.get('/early_start').res
    is_ok(res.code, 404, 'right status')
    like_ok(res.text, r'Page Not Found', 'right content')

with subtest('Plain WebSocket'):
    got = {}
    app.plugins.once('before_dispatch', lambda c: got.update(stash=c.stash()))

    @ua.websocket('/')
    def plain(ua, tx):
        tx.on('finish', lambda *args: Pyjo.IOLoop.stop())

        @tx.on('message')
        def message(tx, msg):
            tx.finish()
            got['result'] = msg

        tx.send('test1')

    Pyjo.IOLoop.start()
    while not got['stash'].get('finished'):
        Pyjo.IOLoop.one_tick()
    is_ok(got['stash']['finished'], 1, 'finish event has been emitted once')
    like_ok(got['result'], r'test1test2ws://127\.0\.0\.1:\d+/', 'right result')

with subtest('Failed WebSocket connection'):
    got = {}

    @ua.websocket('/something/else')
    def failed(ua, tx):
        got.update(ws=tx.is_websocket, code=tx.res.code, body=tx.res.text)
        Pyjo.IOLoop.stop()

    Pyjo.IOLoop.start()
    ok(not got['ws'], 'not a WebSocket')
    is_ok(got['code'], 200, 'right status')
    ok((m := re.match(r'^(\d+)failed!$', got['body'])) and int(m[1]) == 30, 'right content')

with subtest('Server directly sends a message'):
    got = {'result': ''}

    @ua.websocket('/early_start')
    def early(ua, tx):
        got['established'] = tx.established

        @tx.on('finish')
        def finish(tx, code, reason):
            got.update(status=code, msg=reason)
            Pyjo.IOLoop.stop()

        @tx.on('message')
        def message(tx, msg):
            got['result'] += msg
            tx.send('test2')

    Pyjo.IOLoop.start()
    ok(got['established'], 'connection established')
    is_ok(got['status'], 1000, 'right status')
    is_ok(got['msg'], 'I ♥ Mojolicious!', 'right message')
    is_ok(got['result'], 'test0test2test1', 'right result')

with subtest('WebSocket connection gets closed very fast'):
    got = {}

    @ua.websocket('/early_finish')
    def fast(ua, tx):
        @tx.on('finish')
        def finish(tx, code, reason):
            got['status'] = [code, reason]
            Pyjo.IOLoop.stop()

    Pyjo.IOLoop.start()
    is_ok(got['status'][0], 4000, 'right status')
    is_ok(got['status'][1], 'kaboom', 'right message')

with subtest('Connection denied'):
    got = {}
    app.plugins.once('before_dispatch', lambda c: got.update(stash=c.stash()))

    @ua.websocket('/denied')
    def connection_denied(ua, tx):
        got.update(ws=tx.is_websocket, code=tx.res.code)
        Pyjo.IOLoop.stop()

    Pyjo.IOLoop.start()
    while not got['stash'].get('finished'):
        Pyjo.IOLoop.one_tick()
    is_ok(got['stash']['handshake'], 1, 'finish event has been emitted once for handshake')
    is_ok(got['stash']['finished'], 1, 'finish event has been emitted once')
    ok(not got['ws'], 'not a WebSocket')
    is_ok(got['code'], 403, 'right status')

with subtest('Subrequests'):
    got = {'result': ''}
    app.plugins.once('before_dispatch', lambda c: got.update(stash=c.stash()))

    @ua.websocket('/subreq')
    def subrequests(ua, tx):
        got['code'] = tx.res.code

        @tx.on('message')
        def message(tx, msg):
            got['result'] += msg

        tx.on('finish', lambda *args: Pyjo.IOLoop.stop())

    Pyjo.IOLoop.start()
    while not got['stash'].get('finished'):
        Pyjo.IOLoop.one_tick()
    is_ok(got['stash']['finished'], 1, 'finish event has been emitted once')
    is_ok(got['code'], 101, 'right status')
    is_ok(got['result'], 'test0test1', 'right result')

with subtest('Concurrent subrequests'):
    got = {'result': '', 'result2': ''}
    promise = Pyjo.Promise.new()

    @ua.websocket('/subreq')
    def concurrent(ua, tx):
        got['code'] = tx.res.code

        @tx.on('message')
        def message(tx, msg):
            got['result'] += msg
            if msg == 'test1':
                tx.finish()

        tx.on('finish', lambda *args: promise.resolve())

    promise2 = Pyjo.Promise.new()

    @ua.websocket('/subreq')
    def concurrent2(ua, tx):
        got['code2'] = tx.res.code

        @tx.on('message')
        def message(tx, msg):
            got['result2'] += msg

        tx.on('finish', lambda *args: promise2.resolve())

    Pyjo.Promise.all(promise, promise2).wait()
    is_ok(got['code'], 101, 'right status')
    is_ok(got['result'], 'test0test1', 'right result')
    is_ok(got['code2'], 101, 'right status')
    is_ok(got['result2'], 'test0test1', 'right result')

with subtest('Client-side drain callback'):
    got = {'result': '', 'drain': 0, 'counter': 0}

    @ua.websocket('/echo')
    def client_drain(ua, tx):
        tx.on('finish', lambda *args: Pyjo.IOLoop.stop())

        @tx.on('message')
        def message(tx, msg):
            got['result'] += msg
            got['counter'] += 1
            if got['counter'] == 2:
                tx.finish()

        def drain(tx):
            tx.send('there!')
            got['drain'] += len(Pyjo.IOLoop.stream(tx.connection).subscribers('drain'))

        tx.send('hi!', drain)

    Pyjo.IOLoop.start()
    is_ok(got['result'], 'hi!there!', 'right result')
    is_ok(got['drain'], 1, 'no leaking subscribers')

with subtest('Server-side drain callback'):
    got = {'result': '', 'counter': 0}

    @ua.websocket('/double_echo')
    def server_drain(ua, tx):
        tx.on('finish', lambda *args: Pyjo.IOLoop.stop())

        @tx.on('message')
        def message(tx, msg):
            got['result'] += msg
            got['counter'] += 1
            if got['counter'] == 2:
                tx.finish()

        tx.send('hi!')

    Pyjo.IOLoop.start()
    is_ok(got['result'], 'hi!hi!', 'right result')

with subtest('Sending objects'):
    got = {}

    @ua.websocket('/trim')
    def objects(ua, tx):
        tx.on('finish', lambda *args: Pyjo.IOLoop.stop())

        @tx.on('message')
        def message(tx, msg):
            tx.finish()
            got['result'] = msg

        tx.send(u(' foo bar '))

    Pyjo.IOLoop.start()
    is_ok(got['result'], 'foo bar', 'right result')

with subtest('Promises'):
    got = {}

    def then(tx):
        promise = Pyjo.Promise.new()
        tx.on('finish', lambda *args: promise.resolve())

        @tx.on('message')
        def message(tx, msg):
            tx.finish()
            got['result'] = msg

        tx.send(' also works! ')
        return promise

    ua.websocket_p('/trim').then(then).wait()
    is_ok(got['result'], 'also works!', 'right result')
    got['result'] = None
    ua.websocket_p('/foo').then(lambda tx: got.update(result='test failed')).catch(
        lambda err: got.update(result=err)
    ).wait()
    is_ok(got['result'], 'WebSocket handshake failed', 'right result')
    got['result'] = None
    ua.websocket_p(ua.server.url().to_abs().set(scheme='wsss')).then(lambda tx: got.update(result='test failed')).catch(
        lambda err: got.update(result=err)
    ).wait()
    is_ok(got['result'], 'Unsupported protocol: wsss', 'right result')

with subtest('Dies'):
    got = {}

    @ua.websocket('/dead')
    def dies(ua, tx):
        got.update(finished=tx.is_finished, ws=tx.is_websocket, code=tx.res.code, msg=tx.res.message)
        Pyjo.IOLoop.stop()

    Pyjo.IOLoop.start()
    ok(got['finished'], 'transaction is finished')
    ok(not got['ws'], 'not a websocket')
    is_ok(got['code'], 500, 'right status')
    is_ok(got['msg'], 'Internal Server Error', 'right message')

with subtest('Forbidden'):
    got = {}

    @ua.websocket('/foo')
    def forbidden(ua, tx):
        got.update(ws=tx.is_websocket, code=tx.res.code, msg=tx.res.message)
        Pyjo.IOLoop.stop()

    Pyjo.IOLoop.start()
    ok(not got['ws'], 'not a websocket')
    is_ok(got['code'], 403, 'right status')
    is_ok(got['msg'], "i'm a teapot", 'right message')

with subtest('Connection close'):
    got = {}

    @ua.websocket('/close')
    def connection_close(ua, tx):
        @tx.on('finish')
        def finish(tx, code, reason):
            got['status'] = code
            Pyjo.IOLoop.stop()

        tx.send('test1')

    Pyjo.IOLoop.start()
    is_ok(got['status'], 1006, 'right status')

with subtest('Unsupported protocol'):
    got = {}

    @ua.websocket('wsss://example.com')
    def unsupported(ua, tx):
        got['error'] = tx.error
        Pyjo.IOLoop.stop()

    Pyjo.IOLoop.start()
    is_ok(got['error']['message'], 'Unsupported protocol: wsss', 'right error')

with subtest('16-bit length'):
    got = {}

    @ua.websocket('/echo')
    def length(ua, tx):
        tx.on('finish', lambda *args: Pyjo.IOLoop.stop())

        @tx.on('message')
        def message(tx, msg):
            tx.finish()
            got['result'] = msg

        tx.send('hi!' * 100)

    Pyjo.IOLoop.start()
    is_ok(got['result'], 'hi!' * 100, 'right result')

with subtest('Timeout'):
    got = {}
    with app.log.capture('trace') as logs:
        app.plugins.once('before_dispatch', lambda c: got.update(stash=c.stash()))

        @ua.websocket('/timeout')
        def timeout_ws(ua, tx):
            tx.on('finish', lambda *args: Pyjo.IOLoop.stop())

        Pyjo.IOLoop.start()
        while not got['stash'].get('finished'):
            Pyjo.IOLoop.one_tick()
    is_ok(got['stash']['finished'], 1, 'finish event has been emitted once')
    like_ok(str(logs), r'Inactivity timeout', 'right log message')
    del logs

with subtest('Frame sent together with handshake'):
    got = {'buffer': b''}
    app.plugins.once('before_dispatch', lambda c: got.update(stash=c.stash()))

    @Pyjo.IOLoop.client(address='127.0.0.1', port=ua.server.nb_url().port)
    def frame_handshake(loop, err, stream):
        @stream.on('read')
        def read(stream, chunk):
            got['buffer'] += chunk
            if b'test1test2ws:' in got['buffer']:
                stream.close()

        stream.write(
            b'GET / HTTP/1.1\x0d\x0a'
            b'Connection: Upgrade\x0d\x0a'
            b'Upgrade: websocket\x0d\x0a'
            b'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\x0d\x0a'
            b'Sec-WebSocket-Version: 13\x0d\x0a\x0d\x0a' + build_frame(1, 1, 0, 0, 0, 1, b'test1')
        )

    while not got.get('stash', {}).get('finished'):
        Pyjo.IOLoop.one_tick()
    like_ok(got['buffer'], rb'(?s)101 Switching Protocols.*test1test2ws:', 'right response')
    is_ok(got['stash']['finished'], 1, 'finish event has been emitted once')

with subtest('Ping/pong'):
    got = {}

    @ua.websocket('/echo')
    def ping(ua, tx):
        @tx.on('frame')
        def frame(tx, frame):
            if frame[4] != 10:
                return
            got['pong'] = frame[5]
            tx.finish()

        tx.on('finish', lambda *args: Pyjo.IOLoop.stop())
        tx.send([1, 0, 0, 0, 9, b'test'])

    Pyjo.IOLoop.start()
    # Unlike Mojolicious: the payload of a frame is bytes
    is_ok(got['pong'], b'test', 'received pong with payload')

# Not in Mojolicious: the WebSocket of a handshake whose connection is closed before its response, which Mojo drops
# without its event finish
with subtest('Connection closed before the response of the handshake'):
    got = {}
    app.plugins.once('before_dispatch', lambda c: got.update(stash=c.stash()))
    port = ua.server.nb_url().port

    @Pyjo.IOLoop.client(address='127.0.0.1', port=port)
    def handshake(loop, err, stream):
        stream.on('read', lambda stream, chunk: got.update(read=chunk))
        stream.write(
            b'GET /later HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: Upgrade\r\nUpgrade: websocket\r\n'
            b'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n',
            lambda stream: Pyjo.IOLoop.timer(0.1, lambda loop: stream.close()),
        )

    timer = Pyjo.IOLoop.timer(5, lambda loop: loop.stop())
    Pyjo.IOLoop.start()
    Pyjo.IOLoop.remove(timer)
    is_ok(got['stash'].get('finished'), 1006, 'finish event has been emitted')
    ok('read' not in got, 'no response')

# Not in Mojolicious: pings that keep a WebSocket alive, and close the connection of a client that does not answer
with subtest('Heartbeat'):
    got = {'frames': []}
    app.plugins.once('before_dispatch', lambda c: got.update(stash=c.stash()))

    @ua.websocket('/heartbeat')
    def pinged(ua, tx):
        tx.on('frame', lambda tx, frame: got['frames'].append(frame[4]))
        Pyjo.IOLoop.timer(0.6, lambda loop: tx.finish())
        tx.on('finish', lambda tx, code, reason: Pyjo.IOLoop.stop())

    Pyjo.IOLoop.start()
    ok(len(got['frames']) > 5, 'pings')
    # The close of the server may come after the end of the connection of the client
    is_deeply_ok(set(got['frames']) - {8}, {9}, 'only pings')
    while got['stash'].get('finished') is None:
        Pyjo.IOLoop.one_tick()
    is_ok(got['stash']['finished'], 1005, 'closed by the client after its inactivity timeout')

    # Stopped
    got = {'frames': []}
    app.plugins.once('before_dispatch', lambda c: got.update(stash=c.stash()))

    @ua.websocket('/heartbeat?stop=1')
    def stopped(ua, tx):
        tx.on('frame', lambda tx, frame: got['frames'].append(frame[4]))
        tx.on('finish', lambda tx, code, reason: Pyjo.IOLoop.stop())

    Pyjo.IOLoop.start()
    is_deeply_ok(got['frames'], [], 'no pings')
    is_ok(got['stash']['finished'], 1006, 'closed by the inactivity timeout')

    # A client that does not answer
    got = {'read': b''}
    app.plugins.once('before_dispatch', lambda c: got.update(stash=c.stash()))
    port = ua.server.nb_url().port

    @Pyjo.IOLoop.client(address='127.0.0.1', port=port)
    def silent(loop, err, stream):
        stream.on('read', lambda stream, chunk: got.update(read=got['read'] + chunk))
        stream.on('close', lambda stream: Pyjo.IOLoop.stop())
        stream.timeout = 0
        stream.write(
            b'GET /heartbeat HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: Upgrade\r\nUpgrade: websocket\r\n'
            b'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n'
        )

    timer = Pyjo.IOLoop.timer(5, lambda loop: loop.stop())
    Pyjo.IOLoop.start()
    Pyjo.IOLoop.remove(timer)
    like_ok(got['read'].decode('latin-1'), r'^HTTP/1\.1 101', 'handshake')
    ok(got['read'].endswith(b'\x89\x00'), 'ping')
    is_ok(got['stash']['finished'], 1006, 'connection closed')

done_testing()
