
"""
Pyjo.Transaction.WebSocket - WebSocket transaction
==================================================
::

    import Pyjo.Transaction.WebSocket

    # Send and receive WebSocket messages
    ws = Pyjo.Transaction.WebSocket.new()
    ws.send('Hello World!')

    @ws.on
    def message(ws, msg):
        print("Message: {0}".format(repr(msg)))

    @ws.on
    def finish(ws, code, reason):
        print("WebSocket closed with status {0}".format(code))

:mod:`Pyjo.Transaction.WebSocket` is a container for WebSocket transactions based
on :rfc:`6455`.

Events
------

:mod:`Pyjo.Transaction.WebSocket` inherits all events from :mod:`Pyjo.Transaction` and
can emit the following new ones.

binary
~~~~~~
::

    @ws.on
    def binary(ws, chunk):
        ...

Emitted when a complete WebSocket binary message has been received.

drain
~~~~~
::

    @ws.on
    def drain(ws):
        ...

Emitted once all data has been sent.

finish
~~~~~~
::

    @ws.on
    def finish(ws, code, reason):
        ...

Emitted when the WebSocket connection has been closed.

frame
~~~~~
::

    @ws.on
    def frame(ws, frame):
        ...

Emitted when a WebSocket frame has been received. ::

    ws.unsubscribe('frame')

    @ws.on
    def frame(ws, frame):
        print("FIN: {0}".format(frame))
        print("RSV1: {1}".format(frame))
        print("RSV2: {2}".format(frame))
        print("RSV3: {3}".format(frame))
        print("Opcode: {4}".format(frame))
        print("Payload: {5}".format(frame))

json
~~~~
::

    @ws.on
    def json(ws, json):
        ...

Emitted when a complete WebSocket message has been received, all text and
binary messages will be automatically JSON decoded. Note that this event only
gets emitted when it has at least one subscriber. ::

    @ws.on
    def json(ws, json):
        print("Message: {msg}".format(json))

message
~~~~~~~
::

    @ws.on
    def message(ws, msg):
        ...

Emitted when a complete WebSocket message has been received, text messages will
be automatically decoded. Note that this event only gets emitted when it has at
least one subscriber.

text
~~~~
::

    @ws.on
    def text(ws, chunk):
        ...

Emitted when a complete WebSocket text message has been received.

Classes
-------
"""

import Pyjo.Transaction

import struct
import zlib

from Pyjo.JSON import encode_json
from Pyjo.Util import b, getenv, notnone, rand, warn, xor_encode


DEBUG = getenv('PYJO_WEBSOCKET_DEBUG', 0)

# Opcodes
CONTINUATION = 0x0
TEXT = 0x1
BINARY = 0x2
CLOSE = 0x8
PING = 0x9
PONG = 0xa


class Pyjo_Transaction_WebSocket(Pyjo.Transaction.object):
    """
    :mod:`Pyjo.Transaction.WebSocket` inherits all attributes and methods from
    :mod:`Pyjo.Transaction` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.compressed = kwargs.get('compressed', False)
        """::

            boolean = ws.compressed
            ws.compressed = boolean

        Compress messages with ``permessage-deflate`` extension.
        """

        self.masked = kwargs.get('masked', False)
        """::

            boolean = ws.masked
            ws.masked = boolean

        Mask outgoing frames with XOR cipher and a random 32-bit key.
        """

        self.max_websocket_size = notnone(kwargs.get('max_websocket_size'), lambda: getenv('PYJO_MAX_WEBSOCKET_SIZE', 0) or 262144)
        """::

            size = ws.max_websocket_size
            ws.max_websocket_size = 1024

        Maximum WebSocket message size in bytes, defaults to the value of the
        ``PYJO_MAX_WEBSOCKET_SIZE`` environment variable or ``262144`` (256KB).
        """

        self._close = None
        self._deflate = None
        self._finished = False
        self._state = None
        self._write = bytearray()

        def frame_cb(ws, frame):
            ws._message(*frame)

        self.on(frame_cb, 'frame')

    def build_frame(self, fin, rsv1, rsv2, rsv3, op, payload):
        """::

            chunk = ws.build_frame(fin, rsv1, rsv2, rsv3, op, payload)

        Build WebSocket frame. ::

            # Binary frame with FIN bit and payload
            print(ws.build_frame(1, 0, 0, 0, 2, b'Hello World!'))

            # Text frame with payload but without FIN bit
            print(ws.build_frame(0, 0, 0, 0, 1, b'Hello '))

            # Continuation frame with FIN bit and payload
            print(ws.build_frame(1, 0, 0, 0, 0, b'World!'))

            # Close frame with FIN bit and without payload
            print(ws.build_frame(1, 0, 0, 0, 8, b''))

            # Ping frame with FIN bit and payload
            print(ws.build_frame(1, 0, 0, 0, 9, b'Test 123'))

            # Pong frame with FIN bit and payload
            print(ws.build_frame(1, 0, 0, 0, 10, b'Test 123'))
        """

        if DEBUG:
            warn("-- Building frame ({0}, {1}, {2}, {3}, {4})\n".format(fin, rsv1, rsv2, rsv3, op))

        frame = bytearray()

        # Head
        head = op + (128 if fin else 0)
        if rsv1:
            head |= 0b01000000
        if rsv2:
            head |= 0b00100000
        if rsv3:
            head |= 0b00010000
        frame += struct.pack('B', head)

        # Small payload
        length = len(payload)
        masked = self.masked
        if length < 126:
            if DEBUG:
                warn("-- Small payload ({0})\n-- {1}".format(length, repr(payload)))
            frame += struct.pack('B', length | 128 if masked else length)

        # Extended payload (16-bit)
        elif length < 65536:
            if DEBUG:
                warn("-- Extended 16-bit payload ({0})\n-- {1}".format(length, repr(payload)))
            frame += struct.pack('B', 126 | 128 if masked else 126) + struct.pack('!H', length)

        # Extended payload (64-bit with 32-bit fallback)
        else:
            if DEBUG:
                warn("-- Extended 64-bit payload ({0})\n-- {1}".format(length, repr(payload)))
            frame += struct.pack('B', 127 | 128 if masked else 127)
            frame += struct.pack('!Q', length)

        # Mask payload
        if masked:
            mask = struct.pack('!L', int(rand(9999999)))
            payload = mask + xor_encode(payload, mask * 128)

        return frame + payload

    def build_message(self, **kwargs):
        """::

            chunk = ws.build_message(binary=message)
            chunk = ws.build_message(text=message)
            chunk = ws.build_message(json={'test': [1, 2, 3]})

        Build WebSocket message.
        """
        # JSON
        if 'json' in kwargs:
            text = encode_json(kwargs['json'])
        elif 'text' in kwargs:
            text = b(kwargs['text'])
        else:
            text = None

        if text is not None:
            frame = [1, 0, 0, 0, TEXT, text]
        elif 'binary' in kwargs:
            frame = [1, 0, 0, 0, BINARY, kwargs['binary']]
        else:
            return

        # "permessage-deflate" extension
        if not self.compressed:
            return self.build_frame(*frame)

        if self._deflate is None:
            self._deflate = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION,
                                             zlib.DEFLATED,
                                             -zlib.MAX_WBITS,
                                             zlib.DEF_MEM_LEVEL)
        deflate = self._deflate
        out = deflate.compress(frame[5])
        out += deflate.flush(zlib.Z_FULL_FLUSH)
        frame[1] = 1
        frame[5] = out[:len(out) - 4]
        return self.build_frame(*frame)

    def finish(self, code=None, reason=None):
        """::

            ws = ws->finish()
            ws = ws->finish(1000)
            ws = ws->finish(1003, 'Cannot accept data!')

        Close WebSocket connection gracefully.
        """
        close = self._close = [code, reason]
        payload = struct.pack('!H', close[0]) if close[0] else b''
        if close[1] is not None:
            payload += b(close[1])
        if close[0] is None:
            close[0] = 1005
        self.send([1, 0, 0, 0, CLOSE, payload])
        self._finished = True
        return self

    def parse_frame(self, chunk):
        """::

            frame = ws.parse_frame(chunk)

        Parse WebSocket frame. ::

            # Parse single frame and remove it from buffer
            frame = ws.parse_frame(chunk)
            print("FIN: {0}".format(frame))
            print("RSV1: {1}".format(frame))
            print("RSV2: {2}".format(frame))
            print("RSV3: {3}".format(frame))
            print("Opcode: {4}".format(frame))
            print("Payload: {5}".format(frame))
        """
        if not isinstance(chunk, bytearray):
            chunk = bytearray(chunk)

        # Head
        if len(chunk) < 2:
            return

        first, second = struct.unpack('BB', bytes(chunk[:2]))

        # FIN
        fin = 1 if first & 0b10000000 == 0b10000000 else 0

        # RSV1-3
        rsv1 = 1 if first & 0b01000000 == 0b01000000 else 0
        rsv2 = 1 if first & 0b00100000 == 0b00100000 else 0
        rsv3 = 1 if first & 0b00010000 == 0b00010000 else 0

        # Opcode
        op = first & 0b00001111
        if DEBUG:
            warn("-- Parsing frame ({0}, {1}, {2}, {3}, {4})\n".format(fin, rsv1, rsv2, rsv3, op))

        # Small payload
        hlength, length = 2, second & 0b01111111
        if length < 126:
            if DEBUG:
                warn("-- Small payload ({0})\n".format(length))

        # Extended payload (16-bit)
        elif length == 126:
            if len(chunk) <= 4:
                return

            hlength = 4
            length, = struct.unpack('!H', bytes(chunk[2:4]))
            if DEBUG:
                warn("-- Extended 16-bit payload ({0})\n".format(length))

        # Extended payload (64-bit with 32-bit fallback)
        elif length == 127:
            if len(chunk) <= 10:
                return

            hlength = 10
            ext = chunk[2:10]
            length, = struct.unpack('!Q', bytes(ext))
            if DEBUG:
                warn("-- Extended 64-bit payload ({0})\n".format(length))

        # Check message size
        if length > self.max_websocket_size:
            self.finish(1009)
            return

        # Check if whole packet has arrived
        masked = bool(second & 0b10000000)
        if masked:
            length += 4
        if len(chunk) < (hlength + length):
            return
        del chunk[:hlength]

        # Payload
        if length > 0:
            payload = chunk[:length]
            del chunk[:length]
            if masked:
                mask = payload[:4]
                del payload[:4]
                payload = xor_encode(payload, mask * 128)
        else:
            payload = bytearray()

        if DEBUG:
            warn("-- {0}\n".format(repr(payload)))

        return fin, rsv1, rsv2, rsv3, op, payload

    def send(self, cb=None, **kwargs):
        """::

            ws = ws.send(binary=message)
            ws = ws.send(text=message)
            ws = ws.send(json={'test': [1, 2, 3]})
            ws = ws.send(frame=[fin, rsv1, rsv2, rsv3, op, payload])
            ws = ws.send(cb, ...)

        Send message or frame non-blocking via WebSocket, the optional drain callback
        will be invoked once all data has been written.

            # Send "Ping" frame
            ws.send(frame=[1, 0, 0, 0, 9, b'Hello World!'])
        """
        if cb:
            self.once('drain', cb)

        if 'frame' in kwargs:
            self._write += self.build_frame(*kwargs['frame'])
        else:
            self._write += self.build_message(**kwargs)
        self._state = 'write'

        return self.emit('resume')


new = Pyjo_Transaction_WebSocket.new
object = Pyjo_Transaction_WebSocket
