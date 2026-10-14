import Pyjo.Transaction.HTTP
import Pyjo.Transaction.WebSocket

from Pyjo.Test import *

import contextlib
import io
import os
import subprocess
import sys


def output(cb):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        cb()
    return out.getvalue()


with subtest('Synopsis'):
    from Pyjo.WebSocket import WS_TEXT, build_frame, parse_frame

    data = build_frame(0, 1, 0, 0, 0, WS_TEXT, b'Hello World!')
    frame = parse_frame(bytearray(data), 262144)
    is_deeply_ok(frame, (1, 0, 0, 0, WS_TEXT, b'Hello World!'), 'roundtrip')

with subtest('build_frame'):
    from Pyjo.WebSocket import WS_BINARY, WS_CLOSE, WS_CONTINUATION, WS_PING, WS_PONG, build_frame

    masked, fin, rsv1, rsv2, rsv3, op, payload = 0, 1, 0, 0, 0, WS_TEXT, b'Hello World!'
    data = build_frame(masked, fin, rsv1, rsv2, rsv3, op, payload)
    is_ok(data, b'\x81\x0cHello World!', 'frame')

    like_ok(
        output(lambda: print(build_frame(1, 1, 0, 0, 0, WS_BINARY, b'Hello World!'))), r"^b['\"]\\x82\\x8c", 'masked'
    )
    is_ok(output(lambda: print(build_frame(0, 0, 0, 0, 0, WS_TEXT, b'Hello '))), "b'\\x01\\x06Hello '\n", 'no FIN')
    is_ok(
        output(lambda: print(build_frame(0, 1, 0, 0, 0, WS_CONTINUATION, b'World!'))), "b'\\x80\\x06World!'\n", 'cont'
    )
    is_ok(output(lambda: print(build_frame(0, 1, 0, 0, 0, WS_CLOSE, b''))), "b'\\x88\\x00'\n", 'close')
    is_ok(output(lambda: print(build_frame(0, 1, 0, 0, 0, WS_PING, b'Test 123'))), "b'\\x89\\x08Test 123'\n", 'ping')
    is_ok(output(lambda: print(build_frame(0, 1, 0, 0, 0, WS_PONG, b'Test 123'))), "b'\\x8a\\x08Test 123'\n", 'pong')

with subtest('challenge'):
    from Pyjo.WebSocket import challenge, client_handshake, server_handshake

    boolean = challenge(Pyjo.Transaction.WebSocket.new())
    is_ok(boolean, False, 'no handshake')

    ws = Pyjo.Transaction.WebSocket.new()
    client_handshake(ws.handshake)
    server_handshake(ws.handshake)
    ok(challenge(ws), 'handshake')

with subtest('client_handshake'):
    from Pyjo.WebSocket import client_handshake

    tx = client_handshake(Pyjo.Transaction.HTTP.new())
    is_ok(tx.req.headers.upgrade, 'websocket', 'Upgrade')
    is_ok(tx.req.headers.connection, 'Upgrade', 'Connection')
    is_ok(tx.req.headers.sec_websocket_version, '13', 'Sec-WebSocket-Version')
    like_ok(tx.req.headers.sec_websocket_key, r'^[\w+/]{22}==$', 'Sec-WebSocket-Key')

with subtest('parse_frame'):
    from Pyjo.WebSocket import parse_frame

    data, limit = b'\x81\x05Hello', 262144
    frame = parse_frame(bytearray(data), limit)
    is_deeply_ok(frame, (1, 0, 0, 0, 1, b'Hello'), 'frame')

    buffer = bytearray(b'\x81\x05Hello\x88\x00')

    def parse():
        # Parse single frame and remove it from buffer
        frame = parse_frame(buffer, 262144)
        print(f'FIN: {frame[0]}')
        print(f'RSV1: {frame[1]}')
        print(f'RSV2: {frame[2]}')
        print(f'RSV3: {frame[3]}')
        print(f'Opcode: {frame[4]}')
        print(f'Payload: {frame[5]}')

    is_ok(output(parse), "FIN: 1\nRSV1: 0\nRSV2: 0\nRSV3: 0\nOpcode: 1\nPayload: b'Hello'\n", 'parsed')
    is_ok(buffer, b'\x88\x00', 'frame removed from buffer')

with subtest('server_handshake'):
    from Pyjo.WebSocket import server_handshake

    tx = Pyjo.Transaction.HTTP.new()
    tx.req.headers.sec_websocket_key = 'dGhlIHNhbXBsZSBub25jZQ=='
    tx = server_handshake(tx)
    is_ok(tx.res.headers.sec_websocket_accept, 's3pPLMBiTxaQ9kYGzzhZRbK+xOo=', 'Sec-WebSocket-Accept')

with subtest('Debugging'):
    env = dict(os.environ, PYJO_WEBSOCKET_DEBUG='1')
    script = 'from Pyjo.WebSocket import build_frame; build_frame(0, 1, 0, 0, 0, 1, b"Hi")'
    result = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True, env=env)
    like_ok(result.stderr, r'-- Building frame \(1, 0, 0, 0, 1\)', 'diagnostics')

done_testing()
