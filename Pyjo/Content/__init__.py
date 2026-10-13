"""
Pyjo.Content - HTTP content base class
======================================
::

    import Pyjo.Content

    class MyContent(Pyjo.Content.object):
        @property
        def body_contains(self, chunk):
            ...

        @property
        def body_size(self):
            ...

        def get_body_chunk(self, offset):
            ...

:mod:`Pyjo.Content` is an abstract base class for HTTP content based on
:rfc:`7230` and
:rfc:`7231`.

Events
------

:mod:`Pyjo.Content` inherits all events from :mod:`Pyjo.EventEmitter` and can emit
the following new ones.

body
^^^^
::

    @content.on
    def body(content):
        ...

Emitted once all headers have been parsed and the body starts. ::

    @content.on
    def body(content):
        if content.headers.header('X-No-MultiPart'):
            content.auto_upgrade = False

drain
^^^^^
::

    @content.on
    def drain(content, offset):
        ...

Emitted once all data has been written. ::

    @content.on
    def drain(content, offset):
        content.write_chunk(time.time())

read
^^^^
::

    @content.on
    def read(content, chunk):
        ...

Emitted when a new chunk of content arrives. ::

    content.unsubscribe('read')

    @content.on
    def read(content, chunk):
        print("Streaming: {0}".format(chunk))

Classess
--------
"""

import Pyjo.EventEmitter
import Pyjo.Headers

from Pyjo.Regexp import r
from Pyjo.Util import b, convert, getenv, not_implemented, notnone

import zlib


re_boundary = r(r"""multipart.*boundary\s*=\s*(?:"([^"]+)"|([\w'(),.:?\-+/]+))""", 'i')
re_charset = r(r'charset\s*=\s*"?([^"\s;]+)"?', 'i')
re_chunk = r(rb'^(?:\x0d?\x0a)?([0-9a-fA-F]+).*\x0a')


class Pyjo_Content(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.Content` inherits all methods from :mod:`Pyjo.EventEmitter` and implements
    the following new ones.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.auto_decompress = kwargs.get('auto_decompress')
        """::

            boolean = content.auto_decompress
            content.auto_decompress = boolean

        Decompress content automatically if :attr:`is_compressed` is true.
        """

        self.auto_relax = kwargs.get('auto_relax')
        """::

            boolean = content.auto_relax
            content.auto_relax = boolean

        Try to detect when relaxed parsing is necessary.
        """

        self.expect_close = kwargs.get('expect_close', False)
        """::

            boolean = content.expect_close
            content.expect_close = boolean

        Expect a response that is terminated with a connection close.
        """

        self.headers = notnone(kwargs.get('headers'), lambda: Pyjo.Headers.new())
        """::

            headers = content.headers
            content.headers = Pyjo.Headers.new()

        Content headers, defaults to a :mod:`Pyjo.Headers` object.
        """

        self.max_buffer_size = notnone(
            kwargs.get('max_buffer_size'), lambda: convert(getenv('PYJO_MAX_BUFFER_SIZE', '0'), int, 0) or 262144
        )
        """::

            size = content.max_buffer_size
            content.max_buffer_size = 1024

        Maximum size in bytes of buffer for content parser, defaults to the value of
        the ``PYJO_MAX_BUFFER_SIZE` environment variable or ``262144`` (256KB).
        """

        self.max_leftover_size = notnone(
            kwargs.get('max_leftover_size'), lambda: convert(getenv('PYJO_MAX_LEFTOVER_SIZE', '0'), int, 0) or 262144
        )
        """::

            size = content.max_leftover_size
            content.max_leftover_size = 1024

        Maximum size in bytes of buffer for pipelined HTTP requests, defaults to the
        value of the ``PYJO_MAX_LEFTOVER_SIZE` environment variable or ``262144``
        (256KB).
        """

        self.relaxed = kwargs.get('relaxed', False)
        """::

            boolean = content.relaxed
            content.relaxed = boolean

        Activate relaxed parsing for responses that are terminated with a connection
        close.
        """

        self.skip_body = kwargs.get('skip_body', False)
        """::

            boolean = content.skip_body
            content.skip_body = boolean

        Skip body parsing and finish after headers.
        """

        self._body = kwargs.get('_body', False)
        self._body_buffer = kwargs.get('_body_buffer', bytearray())
        self._buffer = kwargs.get('_buffer', bytearray())
        self._chunk_len = kwargs.get('_chunk_len', 0)
        self._chunk_state = kwargs.get('_chunk_state', None)
        self._chunks = kwargs.get('_chunks', 0)
        self._delay = kwargs.get('_delay', False)
        self._dynamic = kwargs.get('_dynamic', False)
        self._eof = kwargs.get('_eof', False)
        self._gz = kwargs.get('_gz', None)
        self._gz_size = kwargs.get('_gz_size', 0)
        self._header_buffer = kwargs.get('_header_buffer', None)
        self._header_size = kwargs.get('_header_size', 0)
        self._limit = kwargs.get('_limit', False)
        self._pre_buffer = kwargs.get('_pre_buffer', bytearray())
        self._raw_size = kwargs.get('_raw_size', 0)
        self._real_size = kwargs.get('_real_size', 0)
        self._size = kwargs.get('_size', 0)
        self._state = kwargs.get('_state', None)

    @not_implemented
    def body_contains(self, chunk):
        """::

            boolean = content.body_contains(b'foo bar baz')

        Check if content contains a specific string. Meant to be overloaded in a
        subclass.
        """
        pass

    @property
    @not_implemented
    def body_size(self):
        """::

            size = content.body_size

        Content size in bytes. Meant to be overloaded in a subclass.
        """
        pass

    @property
    def boundary(self):
        """::

            boundary = content.boundary

        Extract multipart boundary from ``Content-Type`` header.
        """
        content_type = notnone(self.headers.content_type, '')
        m = re_boundary.search(content_type)
        if m:
            return notnone(m.group(1), m.group(2))
        else:
            return

    def build_body(self):
        """::

            bstring = content.build_body()

        Render whole body.
        """
        return self._build('get_body_chunk')

    def build_headers(self):
        """::

            bstring = content.build_headers()

        Render all headers.
        """
        return self._build('get_header_chunk')

    @property
    def charset(self):
        """::

            charset = content.charset

        Extract charset from ``Content-Type`` header.
        """
        content_type = self.headers.content_type
        if content_type is None:
            content_type = ''
        m = re_charset.search(content_type)
        if m:
            return m.group(1)
        else:
            return

    def clone(self):
        """::

            clone = content.clone()

        Clone content if possible, otherwise return ``None``.
        """
        if self.is_dynamic:
            return
        else:
            return self.new(headers=self.headers.clone())

    def generate_body_chunk(self, offset):
        """::

            chunk = content.generate_body_chunk(0)

        Generate dynamic content.
        """
        if not self._delay and not len(self._body_buffer):
            self.emit('drain', offset)
        else:
            self._delay = False
        chunk = self._body_buffer
        self._body_buffer = bytearray()
        if not len(chunk):
            if self._eof:
                return bytearray()
            else:
                return
        else:
            return chunk

    @not_implemented
    def get_body_chunk(self, offset):
        """::

            chunk = content.get_body_chunk(0)

        Get a chunk of content starting from a specific position. Meant to be
        overloaded in a subclass.
        """
        pass

    def get_header_chunk(self, offset):
        """::

            chunk = content.get_header_chunk(13)

        Get a chunk of the headers starting from a specific position.
        """
        if self._header_buffer is None:
            headers = bytearray(self.headers.to_bytes())
            if headers:
                self._header_buffer = headers + b'\x0d\x0a\x0d\x0a'
            else:
                self._header_buffer = bytearray(b'\x0d\x0a')

        return self._header_buffer[offset:131072]

    @property
    def header_size(self):
        """::

            size = content.header_size

        Size of headers in bytes.
        """
        return len(self.build_headers())

    @property
    def is_chunked(self):
        """::

            boolean = content.is_chunked

        Check if content is chunked.
        """
        return bool(self.headers.transfer_encoding)

    @property
    def is_compressed(self):
        """::

            boolean = content.is_compressed

        Check if content is gzip compressed.
        """
        if self.headers.content_encoding is None:
            return False
        else:
            return self.headers.content_encoding.lower() == 'gzip'

    @property
    def is_dynamic(self):
        """::

            boolean = content.is_dynamic

        Check if content will be dynamically generated, which prevents :meth:`clone` from
        working.
        """
        return self._dynamic and self.headers.content_length is None

    @property
    def is_finished(self):
        """::

            boolean = content.is_finished

        Check if parser is finished.
        """
        return self._state == 'finished'

    @property
    def is_limit_exceeded(self):
        """::

            boolean = content.is_limit_exceeded

        Check if buffer has exceeded :attr:`max_buffer_size`.
        """
        return self._limit

    @property
    def is_multipart(self):
        """::

            false = content.is_multipart

        False.
        """
        return False

    @property
    def is_parsing_body(self):
        """::

            boolean = content.is_parsing_body

        Check if body parsing started yet.
        """
        return self._state == 'body'

    @property
    def leftovers(self):
        """::

            chunk = content.leftovers

        Get leftover data from content parser.
        """
        return self._buffer

    def parse(self, chunk=None):
        r"""::

            content = content.parse(b"Content-Length: 12\x0d\x0a\x0d\x0aHello World!")

        Parse content chunk.
        """
        # Headers
        if chunk is not None:
            self._parse_until_body(b(chunk, 'ascii'))

        if self._state == 'headers':
            return self

        # Chunked content
        if self.is_chunked and self._state != 'headers':
            self._parse_chunked()
            if self._chunk_state == 'finished':
                self._state = 'finished'

        # Not chunked, pass through to second buffer
        else:
            self._real_size += len(self._pre_buffer)
            if not (self.is_finished and len(self._buffer) > self.max_leftover_size):
                self._buffer.extend(self._pre_buffer)
            self._pre_buffer = bytearray()

        # No content
        if self.skip_body:
            self._state = 'finished'
            return self

        # Relaxed parsing
        headers = self.headers
        length = headers.content_length
        if self.auto_relax and length is None or length == '':
            connection = headers.connection.lower() if headers.connection is not None else ''
            if connection == 'close' or (not connection and self.expect_close):
                self.relaxed = True

        # Chunked or relaxed content
        if self.is_chunked or self.relaxed:
            self._decompress(self._buffer)
            self._size += len(self._buffer)
            self._buffer = bytearray()
            return self

        # Normal content
        if length is not None and length.isdigit():
            length = int(length)
        else:
            length = 0
        need = length - self._size
        if need > 0:
            chunk = self._buffer[:need]
            del self._buffer[:need]
            self._decompress(chunk)
            self._size += len(chunk)

        if length <= self.progress:
            self._state = 'finished'

            # Replace Content-Encoding with Content-Length
            if self.auto_decompress and self.is_compressed:
                self.headers.content_length = self._gz_size
                self.headers.remove('Content-Encoding')

        return self

    def parse_body(self, body):
        """::

            content = content.parse_body(b'Hi!')

        Parse body chunk and skip headers.
        """
        self._state = 'body'
        return self.parse(body)

    @property
    def progress(self):
        """::

            size = content.progress

        Size of content already received from message in bytes.
        """
        state = self._state
        if not state:
            return 0
        if state == 'body' or state == 'finished':
            return self._raw_size - self._header_size
        else:
            return 0

    def to_bytes(self):
        """::

            bstring = content.to_bytes()

        Turn content into a bytes string, suitable for HTTP messages.
        """
        buf = b''
        offset = 0
        while True:
            chunk = self.get_header_chunk(offset)
            if not chunk:
                break
            buf += chunk
            offset += len(chunk)
        offset = 0
        while True:
            chunk = self.get_body_chunk(offset)
            if not chunk:
                break
            buf += chunk
            offset += len(chunk)
        return buf

    def write(self, chunk=None, cb=None):
        """::

            content = content.write(chunk)
            content = content.write(chunk, cb)

        Write dynamic content non-blocking, the optional drain callback will be invoked
        once all data has been written.
        """
        self._dynamic = True

        if chunk is not None:
            self._body_buffer.extend(chunk)
        else:
            self._delay = True

        if cb:
            self.once(cb, 'drain')

        if chunk == b'':
            self._eof = True

        return self

    def write_chunk(self, chunk=None, cb=None):
        """::

            content = content.write_chunk(chunk)
            content = content.write_chunk(chunk, cb)

        Write dynamic content non-blocking with ``chunked`` transfer encoding, the
        optional drain callback will be invoked once all data has been written.
        """
        if not self.is_chunked:
            self.headers.transfer_encoding = 'chunked'

        self.write(self._build_chunk(chunk) if chunk is not None else chunk, cb)
        if chunk == b'':
            self._eof = True

        return self

    def _build(self, method):
        buf, offset = b'', 0
        while True:
            # No chunk yet, try again
            chunk = getattr(self, method)(offset)
            if chunk is None:
                continue

            l = len(chunk)
            if not l:
                break

            offset += l
            buf += chunk

        return buf

    def _build_chunk(self, chunk):
        # End
        if not len(chunk):
            return b'\x0d\x0a0\x0d\x0a\x0d\x0a'

        # First chunk has no leading CRLF
        if self._chunks:
            crlf = b'\x0d\x0a'
        else:
            crlf = b''
        self._chunks += 1

        return crlf + b(f'{len(chunk):x}', 'ascii') + b'\x0d\x0a' + chunk

    def _decompress(self, chunk):
        # No compression
        if not self.auto_decompress or not self.is_compressed:
            return self.emit('read', chunk)

        # Decompress
        if self._gz is None:
            self._gz = zlib.decompressobj(zlib.MAX_WBITS | 16)
        gz = self._gz

        try:
            out = gz.decompress(bytes(chunk))

            l = len(out)

            if l > 0:
                self.emit('read', out)

            self._gz_size += l

        except zlib.error:
            out = b''

        # Check buffer size
        # TODO workaround for pypy bug and always empty unconsumed tail
        if len(gz.unconsumed_tail) > self.max_buffer_size:
            self._state = 'finished'
            self._limit = True

    def _parse_chunked(self):
        # Trailing headers
        if self._chunk_state == 'trailing_headers':
            return self._parse_chunked_trailing_headers()

        while True:
            l = len(self._pre_buffer)
            if not l:
                break

            # Start new chunk (ignore the chunk extension)
            if not self._chunk_len:
                m = re_chunk.search(self._pre_buffer)
                if m:
                    self._pre_buffer = bytearray(re_chunk.sub(b'', bytes(self._pre_buffer), 1))
                else:
                    break
                try:
                    self._chunk_len = int(bytes(m.group(1)), 16)
                except:
                    self._chunk_len = None
                if self._chunk_len:
                    continue

                # Last chunk
                self._chunk_state = 'trailing_headers'
                break

            # Remove as much as possible from payload
            if self._chunk_len < l:
                l = self._chunk_len
            self._buffer.extend(self._pre_buffer[:l])
            del self._pre_buffer[:l]
            self._real_size += l
            self._chunk_len -= l

        # Trailing headers
        if self._chunk_state == 'trailing_headers':
            self._parse_chunked_trailing_headers()

        # Check buffer size
        if len(self._pre_buffer) > self.max_buffer_size:
            self._state = 'finished'
            self._limit = True

    def _parse_headers(self):
        pre_buffer = self._pre_buffer
        self._pre_buffer = bytearray()
        headers = self.headers.parse(pre_buffer)
        if not headers.is_finished:
            return
        self._state = 'body'

        # Take care of leftovers
        leftovers = self._pre_buffer = bytearray(headers.leftovers())
        self._header_size = self._raw_size - len(leftovers)

    def _parse_chunked_trailing_headers(self):
        headers = self.headers.parse(self._pre_buffer)
        self._pre_buffer = bytearray()
        if not headers.is_finished:
            return
        self._chunk_state = 'finished'

        # Take care of leftover and replace Transfer-Encoding with Content-Length
        self._buffer.extend(headers.leftovers())
        headers.remove('Transfer-Encoding')
        if not headers.content_length:
            headers.content_length = self._real_size

    def _parse_until_body(self, chunk):
        self._raw_size += len(chunk)
        self._pre_buffer.extend(chunk)
        if self._state is None:
            self._state = 'headers'
        if self._state == 'headers':
            self._parse_headers()
        if self._state != 'headers' and not self._body:
            self._body = True
            self.emit('body')


new = Pyjo_Content.new
object = Pyjo_Content
