"""
__DATA__
@@ render.html.ep
<%= msg %>\\
"""

import Pyjo.IOLoop
import Pyjo.Test.Pyjo
import Pyjoyment.Controller

from Pyjo.Test import *
from Pyjoyment.Lite import app, get

import gc
import sys


# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# Not in Mojolicious: the templates of the DATA section are in the docstring, as the requests come before the end of the
# script


class MyTestApp_Controller(Pyjoyment.Controller.object):
    def __del__(self):
        try:
            if sys.is_finalizing():
                return
            self.stash()['destroyed'] = 1
        except Exception:
            pass


app.controller_class = MyTestApp_Controller


# Not in Mojolicious: PyPy frees the controller only when its garbage collector runs, CPython when the last reference
# goes, as Perl does
def collect():
    if sys.implementation.name == 'pypy':
        gc.collect()


@get('/write')
def write(c):
    c.res.headers.connection = 'close'
    c.on('finish', lambda c: c.stash().__setitem__('finished', c.stash().get('finished', 0) + 1))
    c.res.code = 200
    c.res.headers.content_type = 'text/plain'
    c.finish(b'this was short.')


@get('/write/length')
def write_length(c):
    c.res.code = 200
    c.res.headers.content_type = 'text/plain'
    c.res.headers.content_length = 25
    c.write(b'this was short and plain.')


@get('/write/nolength')
def write_nolength(c):
    c.res.code = 200
    c.res.headers.content_type = 'text/plain'
    c.write(b'this was short and had no length.')
    c.write(b'')


@get('/longpoll/chunked')
def longpoll_chunked(c):
    c.res.code = 200
    c.res.headers.content_type = 'text/plain'
    c.write_chunk(b'hi ')

    @Pyjo.IOLoop.timer(0.25)
    def id(loop):
        c.write_chunk(b'there,', lambda c: c.write_chunk(b' whats up?', lambda c: c.finish()))

    @c.on('finish')
    def finish(c):
        c.stash()['finished'] = c.stash().get('finished', 0) + 1
        Pyjo.IOLoop.remove(id)


@get('/longpoll/length')
def longpoll_length(c):
    c.res.code = 200
    c.res.headers.content_type = 'text/plain'
    c.res.headers.content_length = 25
    c.write(b'hi ')

    @Pyjo.IOLoop.timer(0.25)
    def timer(loop):
        c.on('finish', lambda c: c.stash().__setitem__('finished', c.stash().get('finished', 0) + 1))
        c.write(
            b'there plain,',
            lambda c: c.write(b' whats up?', lambda c: c.stash().__setitem__('drain', c.stash().get('drain', 0) + 1)),
        )


@get('/longpoll/nolength')
def longpoll_nolength(c):
    c.res.code = 200
    c.res.headers.content_type = 'text/plain'
    c.write(b'hi ')

    @Pyjo.IOLoop.timer(0.25)
    def timer(loop):
        c.write(b'there,', lambda c2: c2.write(b' what length?', lambda c3: c.finish()))


@get('/longpoll/order')
def longpoll_order(c):
    def first(c):
        c.stash()['order'] -= 1
        c.write_chunk(b'second, ', lambda c: c.finish(b'third!'))

    c.write_chunk(b'First, ', first)
    c.stash()['order'] = 2


# TODO: the route /longpoll/static, which replies with a static file, when Pyjoyment.Static is ported


@get('/longpoll/dynamic')
def longpoll_dynamic(c):
    @Pyjo.IOLoop.timer(0.25)
    def timer(loop):
        c.res.code = 201
        c.cookie('baz', 'yada')
        c.res.body = b'Dynamic!'
        c.rendered()


@get('/stream')
def stream(c):
    i = 0

    def drain(c):
        nonlocal i
        if i >= 10:
            return c.finish()
        c.write_chunk(str(i).encode(), drain)
        i += 1
        stash = c.stash()
        stash['subscribers'] = stash.get('subscribers', 0) + len(
            Pyjo.IOLoop.stream(c.tx.connection).subscribers('drain')
        )

    drain(c)


@get('/render')
def render(c):
    stream = Pyjo.IOLoop.stream(c.tx.connection)
    c.on('finish', lambda c: c.stash().__setitem__('writing', stream.is_writing))
    c.render_later()
    Pyjo.IOLoop.next_tick(lambda loop: c.render(msg='Finish!'))


@get('/too_long')
def too_long(c):
    c.res.code = 200
    c.res.headers.content_type = 'text/plain'
    c.res.headers.content_length = 17
    c.write(b'Waiting forever!')


t = Pyjo.Test.Pyjo.new()

with subtest('Stream without delay and finish'):
    with t.app.log.capture('trace') as logs:
        stash = None

        @t.app.plugins.once('before_dispatch')
        def before_dispatch(c):
            global stash
            stash = c.stash()

        (
            t.get_ok('/write')
            .status_is(200)
            .header_is('Server', 'Pyjoyment (Python)')
            .content_type_is('text/plain')
            .content_is('this was short.')
        )
        while not stash.get('finished'):
            Pyjo.IOLoop.one_tick()
        ok(not t.tx.kept_alive, 'connection was not kept alive')
        ok(not t.tx.keep_alive, 'connection will not be kept alive')
        is_ok(stash['finished'], 1, 'finish event has been emitted once')
        collect()
        ok(stash.get('destroyed'), 'controller has been destroyed')
        unlike_ok(str(logs), r'Nothing has been rendered, expecting delayed response', 'right message')

with subtest('Stream without delay and content length'):
    (
        t.get_ok('/write/length')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_type_is('text/plain')
        .content_is('this was short and plain.')
    )
    ok(not t.tx.kept_alive, 'connection was not kept alive')
    ok(t.tx.keep_alive, 'connection will be kept alive')

with subtest('Stream without delay and empty write'):
    (
        t.get_ok('/write/nolength')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .header_is('Content-Length', None)
        .content_type_is('text/plain')
        .content_is('this was short and had no length.')
    )
    ok(t.tx.kept_alive, 'connection was kept alive')
    ok(not t.tx.keep_alive, 'connection will not be kept alive')

with subtest('Chunked response with delay'):
    stash = None

    @t.app.plugins.once('before_dispatch')
    def before_dispatch(c):
        global stash
        stash = c.stash()

    (
        t.get_ok('/longpoll/chunked')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_type_is('text/plain')
        .content_is('hi there, whats up?')
    )
    while not stash.get('finished'):
        Pyjo.IOLoop.one_tick()
    ok(not t.tx.kept_alive, 'connection was not kept alive')
    ok(t.tx.keep_alive, 'connection will be kept alive')
    is_ok(stash['finished'], 1, 'finish event has been emitted once')
    collect()
    ok(stash.get('destroyed'), 'controller has been destroyed')

with subtest('Interrupted by closing the connection'):
    stash = None

    @t.app.plugins.once('before_dispatch')
    def before_dispatch(c):
        global stash
        stash = c.stash()

    port = t.ua.server.url().port

    @Pyjo.IOLoop.client(port=port)
    def client(loop, err, stream):
        stream.on('read', lambda stream, bytes: stream.close())
        stream.write(b'GET /longpoll/chunked HTTP/1.1\x0d\x0a\x0d\x0a')

    while not (stash and stash.get('finished')):
        Pyjo.IOLoop.one_tick()
    is_ok(stash['finished'], 1, 'finish event has been emitted once')
    collect()
    ok(stash.get('destroyed'), 'controller has been destroyed')

with subtest('Interrupted by raising an error'):
    tx = t.ua.build_tx('GET', '/longpoll/chunked')
    buffer = b''

    @tx.res.content.unsubscribe('read').on('read')
    def read(content, chunk):
        global buffer
        buffer += chunk
        if len(buffer) == 3:
            tx.res.error = {'message': 'Interrupted'}

    t.ua.start(tx)
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.error['message'], 'Interrupted', 'right error')
    is_ok(buffer, b'hi ', 'right content')

with subtest('Stream with delay and content length'):
    stash = None

    @t.app.plugins.once('before_dispatch')
    def before_dispatch(c):
        global stash
        stash = c.stash()

    (
        t.get_ok('/longpoll/length')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_type_is('text/plain')
        .content_is('hi there plain, whats up?')
    )
    is_ok(stash['drain'], 1, 'drain event has been emitted once')

with subtest('Stream with delay and finish'):
    (
        t.get_ok('/longpoll/nolength')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .header_is('Content-Length', None)
        .content_type_is('text/plain')
        .content_is('hi there, what length?')
    )
    ok(not t.tx.keep_alive, 'connection will not be kept alive')

with subtest('The drain event should be emitted on the next reactor tick'):
    stash = None

    @t.app.plugins.once('before_dispatch')
    def before_dispatch(c):
        global stash
        stash = c.stash()

    (
        t.get_ok('/longpoll/order')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_is('First, second, third!')
    )
    is_ok(stash['order'], 1, 'the drain event was emitted on the next reactor tick')

# TODO: the subtest "Static file with cookies and session", when Pyjoyment.Static is ported

with subtest('Custom response'):
    (
        t.get_ok('/longpoll/dynamic')
        .status_is(201)
        .header_is('Server', 'Pyjoyment (Python)')
        .header_like('Set-Cookie', r'baz=yada')
        .content_is('Dynamic!')
    )

with subtest('Chunked response streaming with drain event'):
    stash = None

    @t.app.plugins.once('before_dispatch')
    def before_dispatch(c):
        global stash
        stash = c.stash()

    t.get_ok('/stream').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('0123456789')
    is_ok(stash['subscribers'], 0, 'no leaking subscribers')
    collect()
    ok(stash.get('destroyed'), 'controller has been destroyed')

with subtest('Rendering of template'):
    stash = None

    @t.app.plugins.once('before_dispatch')
    def before_dispatch(c):
        global stash
        stash = c.stash()

    t.get_ok('/render').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('Finish!')
    collect()
    while not stash.get('destroyed'):
        Pyjo.IOLoop.one_tick()
        collect()
    ok(not stash.get('writing'), 'finish event timing is right')
    ok(stash.get('destroyed'), 'controller has been destroyed')

with subtest('Request timeout'):
    t.ua.request_timeout = 0.5
    tx = t.ua.get('/too_long')
    is_ok(tx.error['message'], 'Request timeout', 'right error')
    t.ua.request_timeout = 0

with subtest('Inactivity timeout'):
    t.ua.inactivity_timeout = 0.5
    tx = t.ua.get('/too_long')
    is_ok(tx.error['message'], 'Inactivity timeout', 'right error')
    t.ua.inactivity_timeout = 20

done_testing()
