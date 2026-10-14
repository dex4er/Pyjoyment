import Pyjo.Transaction.WebSocket

from Pyjo.Test import *
from Pyjo.WebSocket import WS_BINARY, WS_CLOSE, WS_CONTINUATION, WS_PING, WS_PONG, WS_TEXT, build_frame, parse_frame

import zlib


with subtest('Simple text frame roundtrip'):
    data = build_frame(0, 1, 0, 0, 0, WS_TEXT, b'whatever')
    is_ok(data, b'\x81\x08\x77\x68\x61\x74\x65\x76\x65\x72', 'right frame')
    frame = parse_frame(bytearray(data), 262144)
    is_ok(frame[0], 1, 'fin flag is set')
    is_ok(frame[1], 0, 'rsv1 flag is not set')
    is_ok(frame[2], 0, 'rsv2 flag is not set')
    is_ok(frame[3], 0, 'rsv3 flag is not set')
    is_ok(frame[4], 1, 'text frame')
    is_ok(frame[5], b'whatever', 'right payload')
    is_ok(build_frame(0, 1, 0, 0, 0, 1, b'whatever'), data, 'frames are equal')

with subtest('Simple ping frame roundtrip'):
    data = build_frame(0, 1, 0, 0, 0, WS_PING, b'whatever')
    is_ok(data, b'\x89\x08\x77\x68\x61\x74\x65\x76\x65\x72', 'right frame')
    frame = parse_frame(bytearray(data), 262144)
    is_ok(frame[0], 1, 'fin flag is set')
    is_ok(frame[1], 0, 'rsv1 flag is not set')
    is_ok(frame[2], 0, 'rsv2 flag is not set')
    is_ok(frame[3], 0, 'rsv3 flag is not set')
    is_ok(frame[4], 9, 'ping frame')
    is_ok(frame[5], b'whatever', 'right payload')
    is_ok(build_frame(0, 1, 0, 0, 0, 9, b'whatever'), data, 'frames are equal')

with subtest('Simple pong frame roundtrip'):
    data = build_frame(0, 1, 0, 0, 0, WS_PONG, b'whatever')
    is_ok(data, b'\x8a\x08\x77\x68\x61\x74\x65\x76\x65\x72', 'right frame')
    frame = parse_frame(bytearray(data), 262144)
    is_ok(frame[0], 1, 'fin flag is set')
    is_ok(frame[1], 0, 'rsv1 flag is not set')
    is_ok(frame[2], 0, 'rsv2 flag is not set')
    is_ok(frame[3], 0, 'rsv3 flag is not set')
    is_ok(frame[4], 10, 'pong frame')
    is_ok(frame[5], b'whatever', 'right payload')
    is_ok(build_frame(0, 1, 0, 0, 0, 10, b'whatever'), data, 'frames are equal')

with subtest('Simple text frame roundtrip with all flags set'):
    data = build_frame(0, 1, 1, 1, 1, 1, b'whatever')
    is_ok(data, b'\xf1\x08\x77\x68\x61\x74\x65\x76\x65\x72', 'right frame')
    frame = parse_frame(bytearray(data), 262144)
    is_ok(frame[0], 1, 'fin flag is set')
    is_ok(frame[1], 1, 'rsv1 flag is set')
    is_ok(frame[2], 1, 'rsv2 flag is set')
    is_ok(frame[3], 1, 'rsv3 flag is set')
    is_ok(frame[4], 1, 'text frame')
    is_ok(frame[5], b'whatever', 'right payload')
    is_ok(build_frame(0, 1, 1, 1, 1, 1, b'whatever'), data, 'frames are equal')

with subtest('Simple text frame roundtrip without FIN bit'):
    data = build_frame(0, 0, 0, 0, 0, 1, b'whatever')
    is_ok(data, b'\x01\x08\x77\x68\x61\x74\x65\x76\x65\x72', 'right frame')
    frame = parse_frame(bytearray(data), 262144)
    is_ok(frame[0], 0, 'fin flag is not set')
    is_ok(frame[1], 0, 'rsv1 flag is not set')
    is_ok(frame[2], 0, 'rsv2 flag is not set')
    is_ok(frame[3], 0, 'rsv3 flag is not set')
    is_ok(frame[4], 1, 'text frame')
    is_ok(frame[5], b'whatever', 'right payload')
    is_ok(build_frame(0, 0, 0, 0, 0, 1, b'whatever'), data, 'frames are equal')

with subtest('Simple text frame roundtrip with RSV1 flags set'):
    data = build_frame(0, 1, 1, 0, 0, 1, b'whatever')
    is_ok(data, b'\xc1\x08\x77\x68\x61\x74\x65\x76\x65\x72', 'right frame')
    frame = parse_frame(bytearray(data), 262144)
    is_ok(frame[0], 1, 'fin flag is set')
    is_ok(frame[1], 1, 'rsv1 flag is set')
    is_ok(frame[2], 0, 'rsv2 flag is not set')
    is_ok(frame[3], 0, 'rsv3 flag is not set')
    is_ok(frame[4], 1, 'text frame')
    is_ok(frame[5], b'whatever', 'right payload')
    is_ok(build_frame(0, 1, 1, 0, 0, 1, b'whatever'), data, 'frames are equal')

with subtest('Simple continuation frame roundtrip with RSV2 flags set'):
    data = build_frame(0, 1, 0, 1, 0, WS_CONTINUATION, b'whatever')
    is_ok(data, b'\xa0\x08\x77\x68\x61\x74\x65\x76\x65\x72', 'right frame')
    frame = parse_frame(bytearray(data), 262144)
    is_ok(frame[0], 1, 'fin flag is set')
    is_ok(frame[1], 0, 'rsv1 flag is not set')
    is_ok(frame[2], 1, 'rsv2 flag is set')
    is_ok(frame[3], 0, 'rsv3 flag is not set')
    is_ok(frame[4], 0, 'continuation frame')
    is_ok(frame[5], b'whatever', 'right payload')
    is_ok(build_frame(0, 1, 0, 1, 0, 0, b'whatever'), data, 'frames are equal')

with subtest('Simple text frame roundtrip with RSV3 flags set'):
    data = build_frame(0, 1, 0, 0, 1, 1, b'whatever')
    is_ok(data, b'\x91\x08\x77\x68\x61\x74\x65\x76\x65\x72', 'right frame')
    frame = parse_frame(bytearray(data), 262144)
    is_ok(frame[0], 1, 'fin flag is set')
    is_ok(frame[1], 0, 'rsv1 flag is not set')
    is_ok(frame[2], 0, 'rsv2 flag is not set')
    is_ok(frame[3], 1, 'rsv3 flag is set')
    is_ok(frame[4], 1, 'text frame')
    is_ok(frame[5], b'whatever', 'right payload')
    is_ok(build_frame(0, 1, 0, 0, 1, 1, b'whatever'), data, 'frames are equal')

with subtest('Simple binary frame roundtrip'):
    data = build_frame(0, 1, 0, 0, 0, WS_BINARY, b'works')
    is_ok(data, b'\x82\x05\x77\x6f\x72\x6b\x73', 'right frame')
    frame = parse_frame(bytearray(data), 262144)
    is_ok(frame[0], 1, 'fin flag is set')
    is_ok(frame[1], 0, 'rsv1 flag is not set')
    is_ok(frame[2], 0, 'rsv2 flag is not set')
    is_ok(frame[3], 0, 'rsv3 flag is not set')
    is_ok(frame[4], 2, 'binary frame')
    is_ok(frame[5], b'works', 'right payload')
    is_ok((data := build_frame(0, 1, 0, 0, 0, 2, b'works')), data, 'frames are equal')

with subtest('Masked text frame roundtrip'):
    data = build_frame(1, 1, 0, 0, 0, 1, b'also works')
    frame = parse_frame(bytearray(data), 262144)
    is_ok(frame[0], 1, 'fin flag is set')
    is_ok(frame[1], 0, 'rsv1 flag is not set')
    is_ok(frame[2], 0, 'rsv2 flag is not set')
    is_ok(frame[3], 0, 'rsv3 flag is not set')
    is_ok(frame[4], 1, 'text frame')
    is_ok(frame[5], b'also works', 'right payload')
    isnt_ok(build_frame(0, 1, 0, 0, 0, 2, b'also works'), data, 'frames are not equal')

with subtest('Masked binary frame roundtrip'):
    data = build_frame(1, 1, 0, 0, 0, 2, b'just works')
    frame = parse_frame(bytearray(data), 262144)
    is_ok(frame[0], 1, 'fin flag is set')
    is_ok(frame[1], 0, 'rsv1 flag is not set')
    is_ok(frame[2], 0, 'rsv2 flag is not set')
    is_ok(frame[3], 0, 'rsv3 flag is not set')
    is_ok(frame[4], 2, 'binary frame')
    is_ok(frame[5], b'just works', 'right payload')
    isnt_ok(build_frame(0, 1, 0, 0, 0, 2, b'just works'), data, 'frames are not equal')

with subtest('One-character text frame roundtrip'):
    data = build_frame(0, 1, 0, 0, 0, 1, b'a')
    is_ok(data, b'\x81\x01\x61', 'right frame')
    frame = parse_frame(bytearray(data), 262144)
    is_ok(frame[0], 1, 'fin flag is set')
    is_ok(frame[1], 0, 'rsv1 flag is not set')
    is_ok(frame[2], 0, 'rsv2 flag is not set')
    is_ok(frame[3], 0, 'rsv3 flag is not set')
    is_ok(frame[4], 1, 'text frame')
    is_ok(frame[5], b'a', 'right payload')
    is_ok(build_frame(0, 1, 0, 0, 0, 1, b'a'), data, 'frames are equal')

with subtest('One-byte binary frame roundtrip'):
    data = build_frame(0, 1, 0, 0, 0, 2, b'a')
    is_ok(data, b'\x82\x01\x61', 'right frame')
    frame = parse_frame(bytearray(data), 262144)
    is_ok(frame[0], 1, 'fin flag is set')
    is_ok(frame[1], 0, 'rsv1 flag is not set')
    is_ok(frame[2], 0, 'rsv2 flag is not set')
    is_ok(frame[3], 0, 'rsv3 flag is not set')
    is_ok(frame[4], 2, 'binary frame')
    is_ok(frame[5], b'a', 'right payload')
    is_ok((data := build_frame(0, 1, 0, 0, 0, 2, b'a')), data, 'frames are equal')

with subtest('16-bit text frame roundtrip'):
    data = build_frame(0, 1, 0, 0, 0, 1, b'hi' * 10000)
    is_ok(data, b'\x81\x7e\x4e\x20' + (b'\x68\x69' * 10000), 'right frame')
    frame = parse_frame(bytearray(data), 262144)
    is_ok(frame[0], 1, 'fin flag is set')
    is_ok(frame[1], 0, 'rsv1 flag is not set')
    is_ok(frame[2], 0, 'rsv2 flag is not set')
    is_ok(frame[3], 0, 'rsv3 flag is not set')
    is_ok(frame[4], 1, 'text frame')
    is_ok(frame[5], b'hi' * 10000, 'right payload')
    is_ok(build_frame(0, 1, 0, 0, 0, 1, b'hi' * 10000), data, 'frames are equal')

with subtest('64-bit text frame roundtrip'):
    data = build_frame(0, 1, 0, 0, 0, 1, b'hi' * 200000)
    is_ok(data, b'\x81\x7f\x00\x00\x00\x00\x00\x06\x1a\x80' + (b'\x68\x69' * 200000), 'right frame')
    frame = parse_frame(bytearray(data), 500000)
    is_ok(frame[0], 1, 'fin flag is set')
    is_ok(frame[1], 0, 'rsv1 flag is not set')
    is_ok(frame[2], 0, 'rsv2 flag is not set')
    is_ok(frame[3], 0, 'rsv3 flag is not set')
    is_ok(frame[4], 1, 'text frame')
    is_ok(frame[5], b'hi' * 200000, 'right payload')
    is_ok(build_frame(0, 1, 0, 0, 0, 1, b'hi' * 200000), data, 'frames are equal')

with subtest('Empty text frame roundtrip'):
    data = build_frame(0, 1, 0, 0, 0, 1, b'')
    is_ok(data, b'\x81\x00', 'right frame')
    frame = parse_frame(bytearray(data), 262144)
    is_ok(frame[0], 1, 'fin flag is set')
    is_ok(frame[1], 0, 'rsv1 flag is not set')
    is_ok(frame[2], 0, 'rsv2 flag is not set')
    is_ok(frame[3], 0, 'rsv3 flag is not set')
    is_ok(frame[4], 1, 'text frame')
    is_ok(frame[5], b'', 'no payload')
    is_ok(build_frame(0, 1, 0, 0, 0, 1, b''), data, 'frames are equal')

with subtest('Empty close frame roundtrip'):
    data = build_frame(0, 1, 0, 0, 0, WS_CLOSE, b'')
    is_ok(data, b'\x88\x00', 'right frame')
    frame = parse_frame(bytearray(data), 262144)
    is_ok(frame[0], 1, 'fin flag is set')
    is_ok(frame[1], 0, 'rsv1 flag is not set')
    is_ok(frame[2], 0, 'rsv2 flag is not set')
    is_ok(frame[3], 0, 'rsv3 flag is not set')
    is_ok(frame[4], 8, 'close frame')
    is_ok(frame[5], b'', 'no payload')
    is_ok(build_frame(0, 1, 0, 0, 0, 8, b''), data, 'frames are equal')

with subtest('Masked empty binary frame roundtrip'):
    data = build_frame(1, 1, 0, 0, 0, 2, b'')
    frame = parse_frame(bytearray(data), 262144)
    is_ok(frame[0], 1, 'fin flag is set')
    is_ok(frame[1], 0, 'rsv1 flag is not set')
    is_ok(frame[2], 0, 'rsv2 flag is not set')
    is_ok(frame[3], 0, 'rsv3 flag is not set')
    is_ok(frame[4], 2, 'binary frame')
    is_ok(frame[5], b'', 'no payload')
    isnt_ok(build_frame(0, 1, 0, 0, 0, 2, b''), data, 'frames are not equal')

with subtest('Size limit'):
    data = build_frame(0, 1, 0, 0, 0, WS_BINARY, b'works')
    is_ok(data, b'\x82\x05\x77\x6f\x72\x6b\x73', 'right frame')
    frame = parse_frame(bytearray(data), 4)
    ok(frame, 'true')
    ok(not isinstance(frame, tuple), 'not a frame')

with subtest('Incomplete frame'):
    is_ok(parse_frame(bytearray(b'\x82\x05\x77\x6f\x72\x6b'), 262144), None, 'incomplete frame')

with subtest('Fragmented message'):
    fragmented = Pyjo.Transaction.WebSocket.new()
    text = None

    @fragmented.on('text')
    def text_cb(ws, chunk):
        global text
        text = chunk

    fragmented.parse_message([0, 0, 0, 0, WS_TEXT, b'wo'])
    ok(not text, 'text event has not been emitted yet')
    fragmented.parse_message([0, 0, 0, 0, WS_CONTINUATION, b'r'])
    ok(not text, 'text event has not been emitted yet')
    fragmented.parse_message([1, 0, 0, 0, WS_CONTINUATION, b'ks!'])
    is_ok(text, b'works!', 'right payload')

with subtest('Compressed binary message'):
    compressed = Pyjo.Transaction.WebSocket.new(**{'compressed': True})
    frame = compressed.build_message({'binary': b'just works'})
    is_ok(frame[0], 1, 'fin flag is set')
    is_ok(frame[1], 1, 'rsv1 flag is set')
    is_ok(frame[2], 0, 'rsv2 flag is not set')
    is_ok(frame[3], 0, 'rsv3 flag is not set')
    is_ok(frame[4], WS_BINARY, 'binary frame')
    ok(frame[5], 'has payload')
    uncompressed = Pyjo.Transaction.WebSocket.new()
    frame2 = uncompressed.build_message({'binary': b'just works'})
    is_ok(frame2[0], 1, 'fin flag is set')
    is_ok(frame2[1], 0, 'rsv1 flag is not set')
    is_ok(frame2[2], 0, 'rsv2 flag is not set')
    is_ok(frame2[3], 0, 'rsv3 flag is not set')
    is_ok(frame2[4], WS_BINARY, 'binary frame')
    ok(frame2[5], 'has payload')
    isnt_ok(frame[5], frame2[5], 'different payload')
    is_ok(frame2[5], uncompressed.build_message({'binary': b'just works'})[5], 'same payload')

with subtest('Compressed fragmented message'):
    fragmented_compressed = Pyjo.Transaction.WebSocket.new(**{'compressed': True})
    text = None

    @fragmented_compressed.on('message')
    def message(ws, msg):
        global text
        text = msg

    compressed_payload = fragmented_compressed.build_message({'text': b'just works'})[5]
    ok(not text, 'message event has not been emitted yet')
    fragmented_compressed.parse_message([0, 1, 0, 0, WS_TEXT, compressed_payload[0:3]])
    ok(not text, 'message event has not been emitted yet')
    fragmented_compressed.parse_message([0, 0, 0, 0, WS_CONTINUATION, compressed_payload[3:6]])
    ok(not text, 'message event has not been emitted yet')
    fragmented_compressed.parse_message([1, 0, 0, 0, WS_CONTINUATION, compressed_payload[6:]])
    is_ok(text, 'just works', 'decoded correctly')

with subtest('Compressed messages are independently decodable per message'):
    tx = Pyjo.Transaction.WebSocket.new(**{'compressed': True})
    payloads = [f'{{"action":"heartbeat","client_ts":{i}}}'.encode() for i in range(1, 4)]

    for i in range(len(payloads)):
        frame = tx.build_message({'text': payloads[i]})

        inflate = zlib.decompressobj(-15)
        data = frame[5] + b'\x00\x00\xff\xff'
        try:
            out = inflate.decompress(data, 65536)
            status = 0
        except zlib.error:
            out, status = b'', -3

        # Left out from Mojolicious: Z_OK of Compress::Raw::Zlib, Python's zlib raises an exception for an error
        cmp_ok(status, '==', 0, f'message {i + 1} inflates without error')
        is_ok(len(inflate.unconsumed_tail), 0, f'message {i + 1} fully consumed')
        is_ok(out, payloads[i], f'message {i + 1} round-trips')

with subtest('Compressed messages round-trip between two transactions'):
    sender = Pyjo.Transaction.WebSocket.new(**{'compressed': True})
    peer = Pyjo.Transaction.WebSocket.new(**{'compressed': True})

    got = []
    peer.on('message', lambda ws, msg: got.append(msg))

    payloads = [f'{{"action":"heartbeat","client_ts":{i}}}' for i in range(1, 4)]
    for payload in payloads:
        peer.parse_message(sender.build_message({'text': payload.encode()}))

    is_deeply_ok(got, payloads, 'all messages decoded')

done_testing()
