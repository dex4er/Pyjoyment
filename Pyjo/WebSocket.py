r"""
Pyjo.WebSocket - The WebSocket protocol
=======================================
::

    from Pyjo.WebSocket import WS_TEXT, build_frame, parse_frame

    data = build_frame(0, 1, 0, 0, 0, WS_TEXT, b'Hello World!')
    frame = parse_frame(bytearray(data), 262144)

:mod:`Pyjo.WebSocket` implements the WebSocket protocol as described in
`RFC 6455 <https://tools.ietf.org/html/rfc6455>`_.

A frame is a tuple of the FIN bit, the RSV1, RSV2 and RSV3 bits, the opcode
and the payload, ``(fin, rsv1, rsv2, rsv3, op, payload)``.

Functions
---------

:mod:`Pyjo.WebSocket` implements the following functions, which can be
imported individually.

Constants
---------

:mod:`Pyjo.WebSocket` implements the following constants, which can be
imported individually.

WS_BINARY
~~~~~~~~~

Opcode for ``Binary`` frames.

WS_CLOSE
~~~~~~~~

Opcode for ``Close`` frames.

WS_CONTINUATION
~~~~~~~~~~~~~~~

Opcode for ``Continuation`` frames.

WS_PING
~~~~~~~

Opcode for ``Ping`` frames.

WS_PONG
~~~~~~~

Opcode for ``Pong`` frames.

WS_TEXT
~~~~~~~

Opcode for ``Text`` frames.

Debugging
---------

You can set the ``PYJO_WEBSOCKET_DEBUG`` environment variable to get some
advanced diagnostics information printed to ``STDERR``. ::

    PYJO_WEBSOCKET_DEBUG=1

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::WebSocket <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/WebSocket.pm>`_
of Mojolicious 9.49.
"""

from Pyjo.Util import b64_encode, sha1_bytes, warn, xor_encode

import os
import random
import re
import struct

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    import Pyjo.Transaction
    import Pyjo.Transaction.WebSocket

__all__ = [
    'WS_BINARY',
    'WS_CLOSE',
    'WS_CONTINUATION',
    'WS_PING',
    'WS_PONG',
    'WS_TEXT',
    'Frame',
    'build_frame',
    'challenge',
    'client_handshake',
    'parse_frame',
    'server_handshake',
]

DEBUG = bool(os.environ.get('PYJO_WEBSOCKET_DEBUG'))

# Unique value from RFC 6455
GUID = b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

# Left out from Mojolicious: MODERN, as Python's integers make 64-bit frames work without Perl's support for quads

# Opcodes
WS_CONTINUATION = 0x0
WS_TEXT = 0x1
WS_BINARY = 0x2
WS_CLOSE = 0x8
WS_PING = 0x9
WS_PONG = 0xA

# The FIN bit, the RSV1, RSV2 and RSV3 bits, the opcode and the payload
type Frame = tuple[int, int, int, int, int, bytes]


def build_frame(
    masked: object, fin: object, rsv1: object, rsv2: object, rsv3: object, op: int, payload: bytes
) -> bytes:
    r"""::

        data = build_frame(masked, fin, rsv1, rsv2, rsv3, op, payload)

    Build WebSocket frame. ::

        # Masked binary frame with FIN bit and payload
        print(build_frame(1, 1, 0, 0, 0, WS_BINARY, b'Hello World!'))

        # Text frame with payload but without FIN bit
        print(build_frame(0, 0, 0, 0, 0, WS_TEXT, b'Hello '))

        # Continuation frame with FIN bit and payload
        print(build_frame(0, 1, 0, 0, 0, WS_CONTINUATION, b'World!'))

        # Close frame with FIN bit and without payload
        print(build_frame(0, 1, 0, 0, 0, WS_CLOSE, b''))

        # Ping frame with FIN bit and payload
        print(build_frame(0, 1, 0, 0, 0, WS_PING, b'Test 123'))

        # Pong frame with FIN bit and payload
        print(build_frame(0, 1, 0, 0, 0, WS_PONG, b'Test 123'))
    """
    if DEBUG:
        warn(f'-- Building frame ({_bit(fin)}, {_bit(rsv1)}, {_bit(rsv2)}, {_bit(rsv3)}, {op})')

    # Head
    head = op + (128 if fin else 0)
    if rsv1:
        head |= 0b01000000
    if rsv2:
        head |= 0b00100000
    if rsv3:
        head |= 0b00010000
    frame = struct.pack('B', head)

    # Small payload
    length = len(payload)
    if length < 126:
        if DEBUG:
            warn(f'-- Small payload ({length})\n{payload!r}')
        frame += struct.pack('B', (length | 128) if masked else length)

    # Extended payload (16-bit)
    elif length < 65536:
        if DEBUG:
            warn(f'-- Extended 16-bit payload ({length})\n{payload!r}')
        frame += struct.pack('>BH', (126 | 128) if masked else 126, length)

    # Extended payload (64-bit)
    else:
        if DEBUG:
            warn(f'-- Extended 64-bit payload ({length})\n{payload!r}')
        frame += struct.pack('>BQ', (127 | 128) if masked else 127, length)

    # Mask payload
    if masked:
        mask = struct.pack('>I', random.randrange(9999999))
        payload = mask + xor_encode(payload, mask * 128)

    return frame + payload


def challenge(tx: 'Pyjo.Transaction.WebSocket.object') -> bool:
    """::

        boolean = challenge(Pyjo.Transaction.WebSocket.new())

    Check WebSocket handshake challenge.
    """
    # "permessage-deflate" extension
    headers = tx.res.headers
    if re.search(r'permessage-deflate', headers.sec_websocket_extensions or ''):
        tx.compressed = True

    return _challenge(tx.req.headers.sec_websocket_key) == headers.sec_websocket_accept


def client_handshake[T: 'Pyjo.Transaction.object'](tx: T) -> T:
    """::

        tx = client_handshake(Pyjo.Transaction.HTTP.new())

    Perform WebSocket handshake client-side.
    """
    headers = tx.req.headers
    if not headers.upgrade:
        headers.upgrade = 'websocket'
    if not headers.connection:
        headers.connection = 'Upgrade'
    if not headers.sec_websocket_version:
        headers.sec_websocket_version = 13

    # Generate 16 byte WebSocket challenge
    challenge = b64_encode(f'{random.randrange(9999999999999999):16d}'.encode(), '')
    if not headers.sec_websocket_key:
        headers.sec_websocket_key = challenge

    return tx


# Unlike Mojolicious: the buffer is a bytearray, which parse_frame changes, where Mojo takes a reference to a string
def parse_frame(buffer: bytearray, max: int) -> Frame | bool | None:
    r"""::

        frame = parse_frame(buffer, limit)

    Parse WebSocket frame from a :class:`bytearray`, which loses the parsed
    frame. Returns ``None`` if no complete frame was found, and ``True`` if
    the frame is bigger than the limit. ::

        # Parse single frame and remove it from buffer
        frame = parse_frame(buffer, 262144)
        print(f'FIN: {frame[0]}')
        print(f'RSV1: {frame[1]}')
        print(f'RSV2: {frame[2]}')
        print(f'RSV3: {frame[3]}')
        print(f'Opcode: {frame[4]}')
        print(f'Payload: {frame[5]}')
    """
    # Head
    if len(buffer) < 2:
        return None
    first, second = buffer[0], buffer[1]

    # FIN
    fin = 1 if (first & 0b10000000) == 0b10000000 else 0

    # RSV1-3
    rsv1 = 1 if (first & 0b01000000) == 0b01000000 else 0
    rsv2 = 1 if (first & 0b00100000) == 0b00100000 else 0
    rsv3 = 1 if (first & 0b00010000) == 0b00010000 else 0

    # Opcode
    op = first & 0b00001111
    if DEBUG:
        warn(f'-- Parsing frame ({fin}, {rsv1}, {rsv2}, {rsv3}, {op})')

    # Small payload
    hlen, length = 2, second & 0b01111111
    if length < 126:
        if DEBUG:
            warn(f'-- Small payload ({length})')

    # Extended payload (16-bit)
    elif length == 126:
        if not len(buffer) > 4:
            return None
        hlen = 4
        length = struct.unpack_from('>H', buffer, 2)[0]
        if DEBUG:
            warn(f'-- Extended 16-bit payload ({length})')

    # Extended payload (64-bit)
    else:
        if not len(buffer) > 10:
            return None
        hlen = 10
        length = struct.unpack_from('>Q', buffer, 2)[0]
        if DEBUG:
            warn(f'-- Extended 64-bit payload ({length})')

    # Check message size
    if length > max:
        return True

    # Check if whole packet has arrived
    if masked := second & 0b10000000:
        length += 4
    if len(buffer) < hlen + length:
        return None
    del buffer[:hlen]

    # Payload
    payload = bytes(buffer[:length])
    del buffer[:length]
    if masked:
        payload = xor_encode(payload[4:], payload[:4] * 128)
    if DEBUG:
        warn(repr(payload))

    return (fin, rsv1, rsv2, rsv3, op, payload)


def server_handshake[T: 'Pyjo.Transaction.object'](tx: T) -> T:
    """::

        tx = server_handshake(Pyjo.Transaction.HTTP.new())

    Perform WebSocket handshake server-side.
    """
    headers = tx.res.headers
    headers.upgrade = 'websocket'
    headers.connection = 'Upgrade'
    headers.sec_websocket_accept = _challenge(tx.req.headers.sec_websocket_key)

    return tx


def _bit(value: object) -> int:
    return 1 if value else 0


def _challenge(key: str | None) -> str:
    return b64_encode(sha1_bytes((key or '').encode('latin-1') + GUID), '')
