import Pyjo.Transaction.HTTP
import Pyjo.Transaction.WebSocket

from Pyjo.Test import *
from Pyjo.WebSocket import WS_TEXT, build_frame, client_handshake, parse_frame, server_handshake

import base64
import hashlib
import os
import struct
import zlib


with subtest('Handshake of RFC 6455 with hashlib and base64'):
    key = base64.b64encode(os.urandom(16)).decode()
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.headers.sec_websocket_key = key
    server_handshake(tx)
    expected = base64.b64encode(hashlib.sha1((key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest())
    is_ok(tx.res.headers.sec_websocket_accept, expected.decode(), 'same accept key')

    tx = client_handshake(Pyjo.Transaction.HTTP.new())
    is_ok(len(base64.b64decode(tx.req.headers.sec_websocket_key)), 16, 'client key of 16 bytes')

with subtest('Frames of struct'):
    data = struct.pack('!BB', 0x81, 5) + b'Hello'
    is_deeply_ok(parse_frame(bytearray(data), 262144), (1, 0, 0, 0, WS_TEXT, b'Hello'), 'parsed')
    is_ok(build_frame(0, 1, 0, 0, 0, WS_TEXT, b'Hello'), data, 'built')

    data = build_frame(1, 1, 0, 0, 0, WS_TEXT, b'Hello')
    head, length = struct.unpack('!BB', data[:2])
    mask = data[2:6]
    is_ok(length, 0x80 | 5, 'masked')
    is_ok(bytes(b ^ mask[i % 4] for i, b in enumerate(data[6:])), b'Hello', 'unmasked')

with subtest('permessage-deflate of RFC 7692 with zlib'):
    ws = Pyjo.Transaction.WebSocket.new(compressed=True)
    frame = ws.build_message({'text': b'Hello'})
    is_ok(frame[5], b'\xf2\x48\xcd\xc9\xc9\x07\x00', 'the example of RFC 7692')
    inflate = zlib.decompressobj(-zlib.MAX_WBITS)
    is_ok(inflate.decompress(frame[5] + b'\x00\x00\xff\xff'), b'Hello', 'inflated with zlib')

    deflate = zlib.compressobj(wbits=-zlib.MAX_WBITS)
    payload = deflate.compress(b'Hello World!') + deflate.flush(zlib.Z_SYNC_FLUSH)
    messages = []
    ws.on('message', lambda ws, msg: messages.append(msg))
    ws.parse_message((1, 1, 0, 0, WS_TEXT, payload[:-4]))
    is_deeply_ok(messages, ['Hello World!'], 'deflated with zlib')

done_testing()
