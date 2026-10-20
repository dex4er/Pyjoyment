import Pyjo.Message.Request
import Pyjo.Message.Response
import Pyjo.Transaction.HTTP
import Pyjo.Transaction.WebSocket

from Pyjo.Test import *
from Pyjo.WebSocket import WS_BINARY, WS_CLOSE, WS_TEXT, build_frame, parse_frame

import contextlib
import io
import os
import re
import time


def output(cb):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        cb()
    return out.getvalue()


def frames(data):
    buffer, found = bytearray(data), []
    while frame := parse_frame(buffer, 262144):
        found.append(frame)
    return found


with subtest('Synopsis'):

    def synopsis_python():
        from Pyjo.Transaction.WebSocket import WebSocket

        # Send and receive WebSocket messages
        ws = WebSocket()
        ws.send('Hello World!')
        ws.on('message', lambda ws, msg: print(f'Message: {msg}'))
        ws.on('finish', lambda ws, code, reason: print(f'WebSocket closed with status {code}.'))

        ws.server_read(build_frame(0, 1, 0, 0, 0, WS_TEXT, b'Hi'))
        ws.closed()

    is_ok(output(synopsis_python), 'Message: Hi\nWebSocket closed with status 1006.\n', 'messages')
    # Or import the module, as in Google Python Style Guide

    def synopsis():
        import Pyjo.Transaction.WebSocket

        # Send and receive WebSocket messages
        ws = Pyjo.Transaction.WebSocket.new()
        ws.send('Hello World!')
        ws.on('message', lambda ws, msg: print(f'Message: {msg}'))
        ws.on('finish', lambda ws, code, reason: print(f'WebSocket closed with status {code}.'))

        ws.server_read(build_frame(0, 1, 0, 0, 0, WS_TEXT, b'Hi'))
        ws.closed()

    is_ok(output(synopsis), 'Message: Hi\nWebSocket closed with status 1006.\n', 'messages')

with subtest('binary'):
    ws = Pyjo.Transaction.WebSocket.new()
    ws.on('binary', lambda ws, data: ...)
    ok(ws.has_subscribers('binary'), 'subscribed')

    ws = Pyjo.Transaction.WebSocket.new()
    ws.on('binary', lambda ws, data: print(f'Binary: {data}'))
    is_ok(output(lambda: ws.parse_message((1, 0, 0, 0, WS_BINARY, b'\x00'))), "Binary: b'\\x00'\n", 'binary')

with subtest('drain'):
    ws = Pyjo.Transaction.WebSocket.new()
    ws.on('drain', lambda ws: ...)
    ok(ws.has_subscribers('drain'), 'subscribed')

    ws = Pyjo.Transaction.WebSocket.new()
    ws.on('drain', lambda ws: ws.send(str(time.time())))
    like_ok(ws.server_write(), rb'^\x81', 'sent on drain')

with subtest('finish'):
    ws = Pyjo.Transaction.WebSocket.new()
    ws.on('finish', lambda ws, code, reason: ...)
    ok(ws.has_subscribers('finish'), 'subscribed')

with subtest('frame'):
    ws = Pyjo.Transaction.WebSocket.new()
    ws.on('frame', lambda ws, frame: ...)
    ok(ws.has_subscribers('frame'), 'subscribed')

    ws = Pyjo.Transaction.WebSocket.new()

    @ws.on('frame')
    def frame(ws, frame):
        print(f'FIN: {frame[0]}')
        print(f'RSV1: {frame[1]}')
        print(f'RSV2: {frame[2]}')
        print(f'RSV3: {frame[3]}')
        print(f'Opcode: {frame[4]}')
        print(f'Payload: {frame[5]}')

    is_ok(
        output(lambda: ws.parse_message((1, 0, 0, 0, WS_TEXT, b'Hi'))),
        "FIN: 1\nRSV1: 0\nRSV2: 0\nRSV3: 0\nOpcode: 1\nPayload: b'Hi'\n",
        'frame',
    )

with subtest('json'):
    ws = Pyjo.Transaction.WebSocket.new()
    ws.on('json', lambda ws, json: ...)
    ok(ws.has_subscribers('json'), 'subscribed')

    ws = Pyjo.Transaction.WebSocket.new()
    ws.on('json', lambda ws, data: print(f'Message: {data["msg"]}'))
    is_ok(output(lambda: ws.parse_message((1, 0, 0, 0, WS_TEXT, b'{"msg": "Hi"}'))), 'Message: Hi\n', 'JSON')

with subtest('message'):
    ws = Pyjo.Transaction.WebSocket.new()
    ws.on('message', lambda ws, msg: ...)
    ok(ws.has_subscribers('message'), 'subscribed')

    ws = Pyjo.Transaction.WebSocket.new()
    ws.on('message', lambda ws, msg: print(f'Message: {msg}'))
    is_ok(output(lambda: ws.parse_message((1, 0, 0, 0, WS_TEXT, '☃'.encode()))), 'Message: ☃\n', 'decoded')

with subtest('resume'):
    tx = Pyjo.Transaction.WebSocket.new()
    tx.on('resume', lambda tx: ...)
    ok(tx.has_subscribers('resume'), 'subscribed')

with subtest('text'):
    ws = Pyjo.Transaction.WebSocket.new()
    ws.on('text', lambda ws, data: ...)
    ok(ws.has_subscribers('text'), 'subscribed')

    ws = Pyjo.Transaction.WebSocket.new()
    ws.on('text', lambda ws, data: print(f'Text: {data}'))
    is_ok(output(lambda: ws.parse_message((1, 0, 0, 0, WS_TEXT, b'Hi'))), "Text: b'Hi'\n", 'text')

with subtest('new'):
    ws = Pyjo.Transaction.WebSocket.new()
    is_ok(ws.compressed, None, 'default')
    ws = Pyjo.Transaction.WebSocket.new(compressed=True)
    is_ok(ws.compressed, True, 'compressed')

with subtest('compressed'):
    ws = Pyjo.Transaction.WebSocket.new()
    boolean = ws.compressed
    is_ok(boolean, None, 'default')
    ws.compressed = True
    is_ok(ws.compressed, True, 'set')

with subtest('established'):
    ws = Pyjo.Transaction.WebSocket.new()
    boolean = ws.established
    is_ok(boolean, None, 'default')
    ws.established = True
    is_ok(ws.established, True, 'set')

with subtest('handshake'):
    ws = Pyjo.Transaction.WebSocket.new()
    handshake = ws.handshake
    isa_ok(handshake, Pyjo.Transaction.HTTP.object, 'default')
    ws.handshake = Pyjo.Transaction.HTTP.new()
    ok(ws.handshake is not handshake, 'set')

with subtest('masked'):
    ws = Pyjo.Transaction.WebSocket.new()
    boolean = ws.masked
    is_ok(boolean, None, 'default')
    ws.masked = True
    is_ok(ws.masked, True, 'set')

with subtest('max_websocket_size'):
    ws = Pyjo.Transaction.WebSocket.new()
    size = ws.max_websocket_size
    is_ok(size, int(os.environ.get('PYJO_MAX_WEBSOCKET_SIZE') or 262144), 'default')
    ws.max_websocket_size = 1024
    is_ok(ws.max_websocket_size, 1024, 'set')

with subtest('build_message'):
    ws = Pyjo.Transaction.WebSocket.new()
    frame = ws.build_message({'binary': b'\x00'})
    is_deeply_ok(frame, (1, 0, 0, 0, WS_BINARY, b'\x00'), 'binary')
    frame = ws.build_message({'text': b'Hi'})
    is_deeply_ok(frame, (1, 0, 0, 0, WS_TEXT, b'Hi'), 'text')
    frame = ws.build_message({'json': {'test': [1, 2, 3]}})
    is_deeply_ok(frame, (1, 0, 0, 0, WS_TEXT, b'{"test":[1,2,3]}'), 'JSON')
    frame = ws.build_message('☃')
    is_deeply_ok(frame, (1, 0, 0, 0, WS_TEXT, '☃'.encode()), 'characters')

with subtest('client_read'):
    ws = Pyjo.Transaction.WebSocket.new()
    ws.on('text', lambda ws, data: print(data))
    is_ok(output(lambda: ws.client_read(build_frame(0, 1, 0, 0, 0, WS_TEXT, b'Hi'))), "b'Hi'\n", 'read')

with subtest('client_write'):
    ws = Pyjo.Transaction.WebSocket.new().send('Hi')
    data = ws.client_write()
    is_ok(data, b'\x81\x02Hi', 'written')

with subtest('closed'):
    ws = Pyjo.Transaction.WebSocket.new()
    ws.on('finish', lambda ws, code, reason: print(code, reason))
    is_ok(output(lambda: ws.finish(1000, 'Bye').closed()), '1000 Bye\n', 'closed')

with subtest('connection'):
    ws = Pyjo.Transaction.WebSocket.new()
    ws.handshake.connection = 'abc'
    id = ws.connection
    is_ok(id, 'abc', 'connection of the handshake')

with subtest('finish'):
    ws = Pyjo.Transaction.WebSocket.new()
    ws = ws.finish()
    is_deeply_ok(frames(ws.server_write()), [(1, 0, 0, 0, WS_CLOSE, b'')], 'no status')
    ws = Pyjo.Transaction.WebSocket.new()
    ws = ws.finish(1000)
    is_deeply_ok(frames(ws.server_write()), [(1, 0, 0, 0, WS_CLOSE, b'\x03\xe8')], 'status')
    ws = Pyjo.Transaction.WebSocket.new()
    ws = ws.finish(1003, 'Cannot accept data!')
    is_deeply_ok(frames(ws.server_write()), [(1, 0, 0, 0, WS_CLOSE, b'\x03\xebCannot accept data!')], 'reason')

with subtest('is_websocket'):
    ws = Pyjo.Transaction.WebSocket.new()
    boolean = ws.is_websocket
    is_ok(boolean, True, 'WebSocket')

with subtest('kept_alive'):
    ws = Pyjo.Transaction.WebSocket.new()
    ws.handshake.kept_alive = True
    boolean = ws.kept_alive
    is_ok(boolean, True, 'of the handshake')

with subtest('local_address'):
    ws = Pyjo.Transaction.WebSocket.new()
    ws.handshake.local_address = '127.0.0.1'
    address = ws.local_address
    is_ok(address, '127.0.0.1', 'of the handshake')

with subtest('local_port'):
    ws = Pyjo.Transaction.WebSocket.new()
    ws.handshake.local_port = 8080
    port = ws.local_port
    is_ok(port, 8080, 'of the handshake')

with subtest('parse_message'):
    ws = Pyjo.Transaction.WebSocket.new()
    ws.on('text', lambda ws, data: print(data))
    fin, rsv1, rsv2, rsv3, op, payload = 1, 0, 0, 0, WS_TEXT, b'Hi'
    is_ok(output(lambda: ws.parse_message((fin, rsv1, rsv2, rsv3, op, payload))), "b'Hi'\n", 'parsed')

with subtest('protocol'):
    ws = Pyjo.Transaction.WebSocket.new()
    proto = ws.protocol
    is_ok(proto, None, 'no subprotocol')

with subtest('remote_address'):
    ws = Pyjo.Transaction.WebSocket.new()
    ws.handshake.remote_address = '127.0.0.1'
    address = ws.remote_address
    is_ok(address, '127.0.0.1', 'of the handshake')

with subtest('remote_port'):
    ws = Pyjo.Transaction.WebSocket.new()
    ws.handshake.remote_port = 8081
    port = ws.remote_port
    is_ok(port, 8081, 'of the handshake')

with subtest('req'):
    ws = Pyjo.Transaction.WebSocket.new()
    req = ws.req
    isa_ok(req, Pyjo.Message.Request.object, 'handshake request')

with subtest('res'):
    ws = Pyjo.Transaction.WebSocket.new()
    res = ws.res
    isa_ok(res, Pyjo.Message.Response.object, 'handshake response')

with subtest('resume'):
    ws = Pyjo.Transaction.WebSocket.new()
    resumed = []
    ws.handshake.on('resume', lambda tx: resumed.append(True))
    ws = ws.resume()
    is_deeply_ok(resumed, [True], 'handshake resumed')

with subtest('send'):
    ws = Pyjo.Transaction.WebSocket.new()
    ws = ws.send({'binary': b'\x00'})
    ws = ws.send({'text': b'Hi'})
    ws = ws.send({'json': {'test': [1, 2, 3]}})
    ws = ws.send((1, 0, 0, 0, WS_BINARY, b'\x01'))
    ws = ws.send('☃')
    ws = ws.send('☃', lambda ws: ...)
    is_deeply_ok(
        frames(ws.server_write()),
        [
            (1, 0, 0, 0, WS_BINARY, b'\x00'),
            (1, 0, 0, 0, WS_TEXT, b'Hi'),
            (1, 0, 0, 0, WS_TEXT, b'{"test":[1,2,3]}'),
            (1, 0, 0, 0, WS_BINARY, b'\x01'),
            (1, 0, 0, 0, WS_TEXT, '☃'.encode()),
            (1, 0, 0, 0, WS_TEXT, '☃'.encode()),
        ],
        'sent',
    )

    # Send "Ping" frame
    from Pyjo.WebSocket import WS_PING

    ws.send((1, 0, 0, 0, WS_PING, b'Hello World!'))
    is_deeply_ok(frames(ws.server_write()), [(1, 0, 0, 0, WS_PING, b'Hello World!')], 'ping')

with subtest('server_read'):
    ws = Pyjo.Transaction.WebSocket.new()
    ws.on('text', lambda ws, data: print(data))
    is_ok(output(lambda: ws.server_read(build_frame(1, 1, 0, 0, 0, WS_TEXT, b'Hi'))), "b'Hi'\n", 'read masked')

with subtest('server_write'):
    ws = Pyjo.Transaction.WebSocket.new().send('Hi')
    data = ws.server_write()
    is_ok(data, b'\x81\x02Hi', 'written')

with subtest('with_compression'):
    ws = Pyjo.Transaction.WebSocket.new()
    ws.req.headers.sec_websocket_extensions = 'permessage-deflate'
    ws.with_compression()
    ok(ws.compressed, 'compressed')
    is_ok(ws.res.headers.sec_websocket_extensions, 'permessage-deflate', 'negotiated')

with subtest('with_protocols'):
    ws = Pyjo.Transaction.WebSocket.new()
    ws.req.headers.sec_websocket_protocol = 'v1.proto, v3.proto'
    proto = ws.with_protocols('v2.proto', 'v1.proto')
    is_ok(proto, 'v1.proto', 'negotiated')
    is_ok(ws.protocol, 'v1.proto', 'subprotocol')
    like_ok(str(ws.res.headers), re.compile(r'Sec-WebSocket-Protocol: v1\.proto'), 'header')

done_testing()
