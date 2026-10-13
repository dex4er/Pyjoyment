r"""
Pyjo.Content.MultiPart - HTTP multipart content
===============================================
::

    import Pyjo.Content.MultiPart

    multi = Pyjo.Content.MultiPart.new()
    multi.parse(b'Content-Type: multipart/mixed; boundary=---foobar')
    single = multi.parts[4]
    print(single.headers.content_length)

:mod:`Pyjo.Content.MultiPart` is a container for HTTP multipart content based on
:rfc:`7230`,
:rfc:`7231` and
:rfc:`2388`.

Events
------

:mod:`Pyjo.Content.MultiPart` inherits all events from :mod:`Pyjo.Content` and can
emit the following new ones.

part
^^^^^^^
::

    @multi.on
    def part(multi, single):
        ...

Emitted when a new :mod:`Pyjo.Content.Single` part starts. ::

    from Pyjo.Regexp import r

    @multi.on
    def part(multi, single):
        m = r('name="([^"]+)"').search(single.headers.content_disposition)
        if m:
            print("Fields: {0}".format(m.group(1)))

Classes
-------
"""

import Pyjo.Content
import Pyjo.String.Mixin

from Pyjo.Regexp import r
from Pyjo.Util import b, b64_encode, convert, notnone, rand


re_non_word = r(r'\W')
re_multipart = r(r'^(.*multipart/[^;]+)(.*)$')


class Pyjo_Content_MultiPart(Pyjo.Content.object, Pyjo.String.Mixin.object):
    """
    :mod:`Pyjo.Content.MultiPart` inherits all attributes and methods from
    :mod:`Pyjo.Content` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        """::

            multi = Pyjo.Content.MultiPart.new()
            multi = Pyjo.Content.MultiPart.new(parts=[Pyjo.Content.Single.new()])

        Construct a new :mod:`Pyjo.Content.MultiPart` object and subscribe to ``read``
        event with default content parser.
        """
        super().__init__(**kwargs)

        self.parts = kwargs.get('parts', [])
        """::

            parts = multi.parts
            multi.parts = []

        Content parts embedded in this multipart content, usually
        :mod:`Pyjo.Content.Single` objects.
        """

        self._multi_state = None
        self._multipart = bytearray()

        def read_cb(content, chunk):
            content._read(chunk)

        self.on('read', read_cb)

    def body_contains(self, chunk):
        """::

            boolean = multi.body_contains(b'1234567')

        Check if content contains a specific string.
        """
        for part in self.parts:
            if part.build_headers().find(chunk) >= 0:
                return True
            if part.body_contains(chunk):
                return True
        return False

    @property
    def body_size(self):
        """::

            size = multi.body_size

        Content size in bytes.
        """
        # Check for existing Content-Lenght header
        length = convert(self.headers.content_length, int, 0)
        if length:
            return length

        # Calculate length of whole body
        length = boundary_length = len(self.build_boundary()) + 6
        for part in self.parts:
            length += part.header_size + part.body_size + boundary_length

        return length

    def build_boundary(self):
        """::

            boundary = multi.build_boundary()

        Generate a suitable boundary for content and add it to ``Content-Type`` header.
        """
        # Check for existing boundary
        boundary = self.boundary
        if boundary is not None:
            return boundary

        # Generate and check boundary
        size = 1
        while True:
            boundary = b64_encode(b(''.join([chr(int(rand(256))) for _ in range(size * 3)]), 'iso-8859-1'), '')
            size += 1
            boundary = re_non_word.sub('X', boundary)
            if not self.body_contains(b(boundary, 'ascii')):
                break

        # Add boundary to Content-Type header
        headers = self.headers
        m = re_multipart.search(notnone(headers.content_type, ''))
        if m:
            before, after = m.groups()
        else:
            before, after = ('multipart/mixed', '')
        headers.content_type = before + '; boundary=' + boundary + after

        return boundary

    def clone(self):
        """::

            clone = multi.clone()

        Clone content if possible, otherwise return ``None``.
        """
        clone = super().clone()
        if clone is not None:
            clone.parts = self.parts
            return clone
        else:
            return

    def get_body_chunk(self, offset):
        """::

            bstring = multi.get_body_chunk(0)

        Get a chunk of content starting from a specific position.
        """
        # Body generator
        if self._dynamic:
            return self.generate_body_chunk(offset)

        # First boundary
        boundary = self.build_boundary()
        boundary_length = len(boundary) + 6
        length = boundary_length - 2
        if length > offset:
            return bytearray(b('--' + boundary + '\x0d\x0a', 'ascii')[offset:])

        # Prepare content part by part
        parts = self.parts
        i = 0
        for part in parts:
            # Headers
            header_length = part.header_size
            if length + header_length > offset:
                return part.get_header_chunk(offset - length)
            length += header_length

            # Content
            content_length = part.body_size
            if length + content_length > offset:
                return part.get_body_chunk(offset - length)
            length += content_length

            # Boundary
            if i == len(parts) - 1:
                boundary += '--'
                boundary_length += 2

            if length + boundary_length > offset:
                return bytearray(b('\x0d\x0a--' + boundary + '\x0d\x0a', 'ascii')[offset - length :])

            length += boundary_length
            i += 1

        return bytearray()

    @property
    def is_multipart(self):
        """::

            true = multi.is_multipart

        True.
        """
        return True

    def _parse_multipart_body(self, boundary):
        # Whole part in buffer
        pos = self._multipart.find(b'\x0d\x0a--' + b(boundary, 'ascii'))
        if pos < 0:
            length = len(self._multipart) - (len(boundary) + 8)
            if length <= 0:
                return False

            # Store chunk
            chunk = self._multipart[:length]
            del self._multipart[:length]
            self.parts[-1] = self.parts[-1].parse(chunk)
            return False

        else:
            # Store chunk
            chunk = self._multipart[:pos]
            del self._multipart[:pos]
            self.parts[-1] = self.parts[-1].parse(chunk)
            self._multi_state = 'multipart_boundary'
            return True

    def _parse_multipart_boundary(self, boundary):
        # Boundary begins
        if self._multipart.find(b('\x0d\x0a--' + boundary + '\x0d\x0a', 'ascii')) == 0:
            del self._multipart[: len(boundary) + 6]

            # New part
            part = Pyjo.Content.Single.new(relaxed=True)
            self.emit('part', part)
            self.parts.append(part)
            self._multi_state = 'multipart_body'
            return True

        # Boundary ends
        end = b('\x0d\x0a--' + boundary + '--', 'ascii')
        if self._multipart.find(end) == 0:
            del self._multipart[: len(end)]
            self._multi_state = 'finished'

        return False

    def _parse_multipart_preamble(self, boundary):
        # No boundary yet
        pos = self._multipart.find(b('--' + boundary, 'ascii'))
        if pos < 0:
            return False

        else:
            # Replace preamble with carriage return and line feed
            del self._multipart[:pos]
            self._multipart.insert(0, 10)
            self._multipart.insert(0, 13)

            # Parse boundary
            self._multi_state = 'multipart_boundary'
            return True

    def _read(self, chunk):
        self._multipart.extend(chunk)
        boundary = self.boundary

        if self._multi_state is None:
            self._multi_state = 'multipart_preamble'

        while self._multi_state != 'finished':
            # Preamble
            if self._multi_state == 'multipart_preamble':
                if not self._parse_multipart_preamble(boundary):
                    break

            # Boundary
            elif self._multi_state == 'multipart_boundary':
                if not self._parse_multipart_boundary(boundary):
                    break

            # Body
            elif self._multi_state == 'multipart_body':
                if not self._parse_multipart_body(boundary):
                    break

        # Check buffer size
        if len(notnone(self._multipart, b'')) > self.max_buffer_size:
            self._state = 'finished'
            self._limit = True


new = Pyjo_Content_MultiPart.new
object = Pyjo_Content_MultiPart
