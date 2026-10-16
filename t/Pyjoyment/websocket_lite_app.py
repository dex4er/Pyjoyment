import Pyjo.IOLoop
import Pyjo.Test.Pyjo

from Pyjo.JSON import encode_json
from Pyjo.Test import *
from Pyjoyment.Lite import any, get, post, under, websocket

import random


# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()


def echo(c):
    c.tx.max_websocket_size = 65538
    c.tx.with_compression()
    c.on('binary', lambda c, bytes: c.send({'binary': bytes}))

    @c.on('text')
    def text(c, bytes):
        # The bytes are characters 0-255, as Perl interpolates a string of bytes
        c.send(f'echo: {bytes.decode("latin-1")}')


websocket('/echo', echo, 'echo')

get('/echo', {'text': 'plain echo!'})


@any('/not_echo/<code:num>')
def not_echo(c):
    c.res.code = int(c.param('code'))
    c.redirect_to('echo')


@websocket('/no_compression')
def no_compression(c):
    c.on('binary', lambda c, bytes: c.send({'binary': bytes}))
    c.render(text='this should be ignored', status=101)


@websocket('/protocols')
def protocols(c):
    protocol = c.tx.with_protocols('foo', 'bar', 'baz', '0')
    c.send(protocol if protocol is not None else 'none')
    c.send(c.tx.protocol if c.tx.protocol is not None else 'none')


@websocket('/json')
def json(c):
    @c.on('json')
    def message(c, json):
        if not isinstance(json, list | dict):
            return c.send({'json': json})
        if isinstance(json, list):
            return c.send({'json': [*json, 4]})
        json['test'] = json.get('test', 0) + 1
        c.send({'json': json})


@websocket('/timeout')
def timeout(c):
    @c.on('message')
    def message(c, msg):
        if msg != 'timeout':
            c.inactivity_timeout(int(msg))
        c.send(f'{msg}: {Pyjo.IOLoop.stream(c.tx.connection).timeout}')


get('/plain', {'text': 'Nothing to see here!'})


@websocket('/push')
def push(c):
    id = Pyjo.IOLoop.recurring(0.1, lambda loop: c.send('push'))
    c.on('finish', lambda c, *args: Pyjo.IOLoop.remove(id))


@websocket('/unicode')
def unicode(c):
    c.on('message', lambda c, msg: c.send(f'♥: {msg}'))


@websocket('/bytes')
def bytes_(c):
    @c.on('frame')
    def frame(ws, frame):
        ws.send({'binary' if frame[4] == 2 else 'text': frame[5]})


@websocket('/once')
def once(c):
    c.on('message', lambda c, msg: c.send(f'ONE: {msg}'))
    c.tx.once('message', lambda tx, msg: c.send(f'TWO: {msg}'))


websocket('/close', lambda c: c.finish(1001))

websocket('/one_sided', lambda c: c.send('I ♥ Mojolicious!', lambda c: c.finish()))

under('/nested')


@websocket
def nested(c):
    echo = c.cookie('echo') or ''
    c.cookie('echo', 'again')
    c.on('message', lambda c, msg: c.send(f'nested echo: {msg}{echo}').finish(1000))


get({'text': 'plain nested!'})

post({'data': b'plain nested too!'})

t = Pyjo.Test.Pyjo.new()

with subtest('Simple roundtrip'):
    t.websocket_ok('/echo').send_ok('hello').message_ok().message_is('echo: hello').finish_ok()

with subtest('Multiple roundtrips'):
    (
        t.websocket_ok('/echo')
        .send_ok('hello again')
        .message_ok()
        .message_is('echo: hello again')
        .send_ok('and one more time')
        .message_ok()
        .message_is('echo: and one more time')
        .finish_ok()
    )

with subtest('Simple roundtrip with redirect'):
    t.get_ok('/not_echo/308').status_is(308)
    t.ua.max_redirects = 10
    t.get_ok('/not_echo/302').status_is(200).content_is('plain echo!')
    t.websocket_ok('/not_echo/308').send_ok('hello').message_ok().message_is('echo: hello').finish_ok()
    t.websocket_ok('/not_echo/307').send_ok('hello').message_ok().message_is('echo: hello').finish_ok()
    t.websocket_ok('/not_echo/303').send_ok('hello').message_ok().message_is('echo: hello').finish_ok()
    t.websocket_ok('/not_echo/302').send_ok('hello').message_ok().message_is('echo: hello').finish_ok()
    t.websocket_ok('/not_echo/301').send_ok('hello').message_ok().message_is('echo: hello').finish_ok()

with subtest('Custom headers and protocols'):
    headers = {'DNT': 1, 'Sec-WebSocket-Key': 'NTA2MDAyMDU1NjMzNjkwMg=='}
    (
        t.websocket_ok('/echo', headers, ['foo', 'bar', 'baz'])
        .header_is('Sec-WebSocket-Accept', 'I+x5C3/LJxrmDrWw42nMP4pCSes=')
        .header_is('Sec-WebSocket-Protocol', None)
        .send_ok('hello')
        .message_ok()
        .message_is('echo: hello')
        .finish_ok()
    )
    is_ok(t.tx.req.headers.dnt, '1', 'right "DNT" value')
    is_ok(t.tx.req.headers.sec_websocket_protocol, 'foo, bar, baz', 'right "Sec-WebSocket-Protocol" value')

with subtest('Bytes'):
    (
        t.websocket_ok('/echo')
        .send_ok({'binary': b'bytes!'})
        .message_ok()
        .message_is({'binary': b'bytes!'})
        .send_ok({'binary': b'bytes!'})
        .message_ok()
        .message_isnt({'text': b'bytes!'})
        .finish_ok()
    )

with subtest('Bytes in multiple frames'):
    (
        t.websocket_ok('/echo')
        .send_ok([0, 0, 0, 0, 2, b'a'])
        .send_ok([0, 0, 0, 0, 0, b'b'])
        .send_ok([1, 0, 0, 0, 0, b'c'])
        .message_ok()
        .message_is({'binary': b'abc'})
        .finish_ok()
    )

with subtest('Zero'):
    (
        t.websocket_ok('/echo')
        .send_ok('0')
        .message_ok()
        .message_is('echo: 0')
        .send_ok('0')
        .message_ok()
        .message_like({'text': r'0'})
        .finish_ok(1000)
        .finished_ok(1000)
    )

with subtest('64-bit binary message'):
    t.request_ok(t.ua.build_websocket_tx('/echo'))
    is_ok(t.tx.max_websocket_size, 262144, 'right size')
    t.tx.max_websocket_size = 65538
    (
        t.send_ok({'binary': b'a' * 65538})
        .message_ok()
        .message_is({'binary': b'a' * 65538})
        .finish_ok()
        .finished_ok(1005)
    )

with subtest('64-bit binary message (too large for server)'):
    t.websocket_ok('/echo').send_ok({'binary': b'b' * 65539}).finished_ok(1009)

with subtest('64-bit binary message (too large for client)'):
    t.websocket_ok('/echo')
    t.tx.max_websocket_size = 65536
    t.send_ok({'binary': b'c' * 65537}).finished_ok(1009)

with subtest('Binary message in two frames without FIN bit (too large for server)'):
    (
        t.websocket_ok('/echo')
        .send_ok([0, 0, 0, 0, 2, b'd' * 30000])
        .send_ok([0, 0, 0, 0, 0, b'd' * 35539])
        .finished_ok(1009)
    )

with subtest('Plain alternative'):
    t.get_ok('/echo').status_is(200).content_is('plain echo!')

with subtest('Compression denied by the server'):
    t.websocket_ok('/no_compression', {'Sec-WebSocket-Extensions': 'permessage-deflate'})
    is_ok(t.tx.req.headers.sec_websocket_extensions, 'permessage-deflate', 'right "Sec-WebSocket-Extensions" value')
    ok(not t.tx.compressed, 'WebSocket has no compression')
    t.send_ok({'binary': b'a' * 500}).message_ok().message_is({'binary': b'a' * 500}).finish_ok()

with subtest('Compressed message ("permessage-deflate")'):
    t.websocket_ok('/echo', {'Sec-WebSocket-Extensions': 'permessage-deflate'})
    ok(t.tx.compressed, 'WebSocket has compression')
    t.send_ok({'binary': b'a' * 10000}).header_is('Sec-WebSocket-Extensions', 'permessage-deflate')
    is_ok(t.tx.req.headers.sec_websocket_extensions, 'permessage-deflate', 'right "Sec-WebSocket-Extensions" value')
    payload = None

    @t.tx.once('frame')
    def frame(tx, frame):
        global payload
        payload = frame[5]

    t.message_ok().message_is({'binary': b'a' * 10000})
    ok(len(payload) < 10000, 'message has been compressed')
    t.finish_ok().finished_ok(1005)

with subtest('Timeout'):
    (
        t.websocket_ok('/timeout')
        .send_ok('timeout')
        .message_ok()
        .message_is('timeout: 30')
        .send_ok('0')
        .message_ok()
        .message_is('0: 0')
        .send_ok('120')
        .message_ok()
        .message_is('120: 120')
        .finish_ok()
    )

with subtest('Compressed message exceeding the limit when decompressed'):
    (
        t.websocket_ok('/echo', {'Sec-WebSocket-Extensions': 'permessage-deflate'})
        .header_is('Sec-WebSocket-Extensions', 'permessage-deflate')
        .send_ok({'binary': b'a' * 1000000})
        .finished_ok(1009)
    )

with subtest("Huge message that doesn't compress very well"):
    huge = ''.join(str(random.randrange(9)) for _ in range(65538)).encode()
    (
        t.websocket_ok('/echo', {'Sec-WebSocket-Extensions': 'permessage-deflate'})
        .send_ok({'binary': huge})
        .message_ok()
        .message_is({'binary': huge})
        .finish_ok()
    )

with subtest('Protocol negotiation'):
    t.websocket_ok('/protocols', ['bar']).message_ok().message_is('bar').message_ok().message_is('bar').finish_ok()
    is_ok(t.tx.protocol, 'bar', 'right protocol')
    is_ok(t.tx.res.headers.sec_websocket_protocol, 'bar', 'right "Sec-WebSocket-Protocol" value')
    (
        t.websocket_ok('/protocols', ['baz', 'bar', 'foo'])
        .message_ok()
        .message_is('foo')
        .message_ok()
        .message_is('foo')
        .finish_ok()
    )
    is_ok(t.tx.protocol, 'foo', 'right protocol')
    is_ok(t.tx.res.headers.sec_websocket_protocol, 'foo', 'right "Sec-WebSocket-Protocol" value')
    t.websocket_ok('/protocols', ['0']).message_ok().message_is('0').message_ok().message_is('0').finish_ok()
    is_ok(t.tx.protocol, '0', 'right protocol')
    is_ok(t.tx.res.headers.sec_websocket_protocol, '0', 'right "Sec-WebSocket-Protocol" value')
    t.websocket_ok('/protocols', ['']).message_ok().message_is('none').message_ok().message_is('none').finish_ok()
    is_ok(t.tx.protocol, None, 'no protocol')
    (
        t.websocket_ok('/protocols', ['', '', ''])
        .message_ok()
        .message_is('none')
        .message_ok()
        .message_is('none')
        .finish_ok()
    )
    is_ok(t.tx.protocol, None, 'no protocol')
    t.websocket_ok('/protocols').message_ok().message_is('none').message_ok().message_is('none').finish_ok()
    is_ok(t.tx.protocol, None, 'no protocol')

with subtest('JSON roundtrips (with a lot of different tests)'):
    (
        t.websocket_ok('/json')
        .send_ok({'json': {'test': 23, 'snowman': '☃'}})
        .message_ok()
        .json_message_is('', {'test': 24, 'snowman': '☃'})
        .json_message_is('', {'test': 24, 'snowman': '☃'})
        .json_message_has('/test')
        .json_message_hasnt('/test/2')
        .send_ok({'binary': encode_json([1, 2, 3])}, 'with description')
        .message_ok('with description')
        .message_is('[1,2,3,4]')
        .message_is('[1,2,3,4]', 'with description')
        .message_isnt('[1,2,3]')
        .message_isnt('[1,2,3]', 'with description')
        .message_like(r'3')
        .message_like(r'3', 'with description')
        .message_unlike(r'5')
        .message_unlike(r'5', 'with description')
        .json_message_is([1, 2, 3, 4])
        .json_message_is([1, 2, 3, 4])
        .send_ok({'binary': encode_json([1, 2, 3])})
        .message_ok()
        .json_message_has('/2')
        .json_message_has('/2', 'with description')
        .json_message_hasnt('/5')
        .json_message_hasnt('/5', 'with description')
        .json_message_is('/2', 3)
        .json_message_is('/2', 3, 'with description')
        .send_ok({'json': {'☃': [1, 2, 3]}})
        .message_ok()
        .json_message_is('/☃', [1, 2, 3])
        .json_message_like('/☃/1', r'\d')
        .json_message_like('/☃/2', r'3', 'with description')
        .json_message_unlike('/☃/1', r'[a-z]')
        .json_message_unlike('/☃/2', r'2', 'with description')
        .send_ok({'json': 'works'})
        .message_ok()
        .json_message_is('works')
        .send_ok({'json': None})
        .message_ok()
        .json_message_is(None)
        .finish_ok()
    )

with subtest('Plain request'):
    t.get_ok('/plain').status_is(200).content_is('Nothing to see here!')

with subtest('Server push'):
    (
        t.websocket_ok('/push')
        .message_ok()
        .message_is('push')
        .message_ok()
        .message_is('push')
        .message_ok()
        .message_is('push')
        .finish_ok()
    )
    (
        t.websocket_ok('/push')
        .message_ok()
        .message_unlike(r'shift')
        .message_ok()
        .message_isnt('shift')
        .message_ok()
        .message_like(r'us')
        .message_ok()
        .message_unlike({'binary': r'push'})
        .finish_ok()
    )

with subtest('Another plain request'):
    t.get_ok('/plain').status_is(200).content_is('Nothing to see here!')

with subtest('Multiple roundtrips'):
    t.websocket_ok('/echo').send_ok('hello').message_ok().message_is('echo: hello').finish_ok()
    (
        t.websocket_ok('/echo')
        .send_ok('this')
        .send_ok('just')
        .send_ok('works')
        .message_ok()
        .message_is('echo: this')
        .message_ok()
        .message_is('echo: just')
        .message_ok()
        .message_is('echo: works')
        .message_like(r'orks')
        .finish_ok()
    )

with subtest('Another plain request'):
    t.get_ok('/plain').status_is(200).content_is('Nothing to see here!')

with subtest('Unicode roundtrips'):
    t.websocket_ok('/unicode').send_ok('hello').message_ok().message_is('♥: hello').finish_ok()
    (
        t.websocket_ok('/unicode')
        .send_ok('hello again')
        .message_ok()
        .message_is('♥: hello again')
        .send_ok('and one ☃ more time')
        .message_ok()
        .message_is('♥: and one ☃ more time')
        .finish_ok()
    )

with subtest('Binary frame and events'):
    bytes = 'I ♥ Mojolicious'.encode('UTF-16LE')
    t.websocket_ok('/bytes')
    binary = None

    @t.tx.on('frame')
    def binary_frame(ws, frame):
        global binary
        if frame[4] == 2:
            binary = (binary or 0) + 1

    close = None

    @t.tx.on('finish')
    def finish(ws, *args):
        global close
        close = list(args)

    t.send_ok({'binary': bytes}).message_ok().message_is(bytes)
    ok(binary, 'received binary frame')
    binary = None
    # The text message is characters, which Perl compares with the bytes as the same string
    t.send_ok({'text': bytes}).message_ok().message_is(bytes.decode())
    ok(not binary, 'received text frame')
    t.finish_ok(1000, 'Have a nice day!')
    is_deeply_ok(close, [1000, 'Have a nice day!'], 'right status and message')

with subtest('Binary roundtrips'):
    bytes = 'I ♥ Mojolicious'.encode('UTF-16LE')
    (
        t.request_ok(t.ua.build_websocket_tx('/bytes'))
        .send_ok({'binary': bytes})
        .message_ok()
        .message_is(bytes)
        .send_ok({'binary': bytes})
        .message_ok()
        .message_is(bytes)
        .finish_ok()
    )

with subtest('Two responses'):
    (
        t.websocket_ok('/once')
        .send_ok('hello')
        .message_ok()
        .message_is('ONE: hello')
        .message_ok()
        .message_is('TWO: hello')
        .send_ok('hello')
        .message_ok()
        .message_is('ONE: hello')
        .send_ok('hello')
        .message_ok()
        .message_is('ONE: hello')
        .finish_ok()
    )

with subtest('WebSocket connection gets closed right away'):
    t.websocket_ok('/close').finished_ok(1001)

with subtest('WebSocket connection gets closed after one message'):
    t.websocket_ok('/one_sided').message_ok().message_is('I ♥ Mojolicious!').finished_ok(1005)

with subtest('Nested WebSocket'):
    t.websocket_ok('/nested').send_ok('hello').message_ok().message_is('nested echo: hello').finished_ok(1000)

with subtest('Test custom message'):
    t.message = ['binary', b'foobarbaz']
    t.message_like(r'bar').message_is({'binary': b'foobarbaz'})

with subtest('Nested WebSocket with cookie'):
    t.websocket_ok('/nested').send_ok('hello').message_ok().message_is('nested echo: helloagain').finished_ok(1000)

with subtest('Nested plain request'):
    t.get_ok('/nested').status_is(200).content_is('plain nested!')

with subtest('Another nested plain request'):
    t.post_ok('/nested').status_is(200).content_is('plain nested too!')

done_testing()
