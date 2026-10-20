r"""
Pyjo.Content.MultiPart - HTTP multipart content
===============================================
::

    from Pyjo.Content.MultiPart import MultiPart

    multi = MultiPart()
    multi.parse(b'Content-Type: multipart/mixed; boundary=---foobar')
    single = multi.parts[4]

    import Pyjo.Content.MultiPart

    multi = Pyjo.Content.MultiPart.new()
    multi.parse(b'Content-Type: multipart/mixed; boundary=---foobar')
    single = multi.parts[4]

:mod:`Pyjo.Content.MultiPart` is a container for HTTP multipart content,
based on `RFC 7230 <https://tools.ietf.org/html/rfc7230>`_,
`RFC 7231 <https://tools.ietf.org/html/rfc7231>`_ and
`RFC 2388 <https://tools.ietf.org/html/rfc2388>`_.

Events
------

:mod:`Pyjo.Content.MultiPart` inherits all events from :mod:`Pyjo.Content`
and can emit the following new ones.

part
~~~~
::

    multi.on('part', lambda multi, single: ...)

Emitted when a new :mod:`Pyjo.Content.Single` part starts, before its
headers have been parsed. ::

    @multi.on('part')
    def part(multi, single):
        @single.on('body')
        def body(single):
            if m := re.search(r'name="([^"]+)"', single.headers.content_disposition or ''):
                print(f'Field: {m[1]}')

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Content::MultiPart <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Content/MultiPart.pm>`_
of Mojolicious 9.49.
"""

import Pyjo.Content
import Pyjo.Content.Single

from Pyjo.Util import b64_encode

import random
import re

from typing import Any, Self


class Pyjo_Content_MultiPart(Pyjo.Content.object):
    """
    :mod:`Pyjo.Content.MultiPart` inherits all methods from
    :mod:`Pyjo.Content` and implements the following new ones.
    """

    def __init__(self, *, parts: list[Pyjo.Content.object] | None = None, **kwargs: Any) -> None:
        """::

            multi = Pyjo.Content.MultiPart.new()
            multi = Pyjo.Content.MultiPart.new(parts=[Pyjo.Content.Single.new()])

        Construct a new :mod:`Pyjo.Content.MultiPart` object and subscribe to
        event ``read`` with default content parser.
        """
        super().__init__(**kwargs)

        self.parts: list[Pyjo.Content.object] = parts if parts is not None else []
        """::

            parts = multi.parts
            multi.parts = [Pyjo.Content.Single.new()]

        Content parts embedded in this multipart content, usually
        :mod:`Pyjo.Content.Single` objects.
        """

        self._boundary: str | None = None
        self._last_len = 0
        self._last_part = 0
        self._multi_state: str | None = None
        self._multipart = b''
        self._offset: int | None = None
        self.on('read', Pyjo_Content_MultiPart._read)

    def body_contains(self, chunk: bytes) -> bool:
        """::

            boolean = multi.body_contains(b'foobarbaz')

        Check if content parts contain a specific string.
        """
        for part in self.parts:
            if part.headers_contain(chunk) or part.body_contains(chunk):
                return True
        return False

    @property
    def body_size(self) -> int:
        """::

            size = multi.body_size

        Content size in bytes.
        """
        # Check for existing Content-Length header
        if length := self._number(self.headers.content_length):
            return int(length)

        # Calculate length of whole body
        length = boundary_len = len(self.build_boundary()) + 6
        for part in self.parts:
            length += part.header_size + part.body_size + boundary_len

        return length

    def build_boundary(self) -> str:
        """::

            boundary = multi.build_boundary()

        Generate a suitable boundary for content and add it to
        ``Content-Type`` header.
        """
        # Check for existing boundary
        if (boundary := self.boundary) is not None:
            return boundary

        # Generate and check boundary
        size = 1
        while True:
            boundary = re.sub(r'\W', 'X', b64_encode(random.randbytes(size * 3)))
            size += 1
            if not self.body_contains(boundary.encode('latin-1')):
                break

        # Add boundary to Content-Type header
        headers = self.headers
        before, after = 'multipart/mixed', ''
        if m := re.fullmatch(r'(.*multipart/[^;]+)(.*)', headers.content_type or ''):
            before, after = m[1], m[2]
        headers.content_type = f'{before}; boundary={boundary}{after}'

        return boundary

    def clone(self) -> Self | None:
        """::

            clone = multi.clone()

        Return a new :mod:`Pyjo.Content.MultiPart` object cloned from this
        content if possible, otherwise return ``None``.
        """
        if (clone := super().clone()) is None:
            return None
        clone.parts = self.parts
        return clone

    def get_body_chunk(self, offset: int) -> bytes | None:
        """::

            chunk = multi.get_body_chunk(0)

        Get a chunk of content starting from a specific position. Note that it
        might not be possible to get the same chunk twice if content was
        generated dynamically.
        """
        # Body generator
        if self.is_dynamic:
            return self.generate_body_chunk(offset)

        # First boundary
        if self._boundary is None:
            self._boundary = self.build_boundary()
        boundary = self._boundary.encode('latin-1')
        boundary_len = len(boundary) + 6
        length = boundary_len - 2
        if length > offset:
            return (b'--' + boundary + b'\x0d\x0a')[offset:]

        # Skip parts that have already been processed
        start = 0
        if self._offset and offset > self._offset:
            length, start = self._last_len, self._last_part + 1

        # Prepare content part by part
        parts = self.parts
        for i in range(start, len(parts)):
            part = parts[i]

            # Headers
            header_len = part.header_size
            if (length + header_len) > offset:
                return part.get_header_chunk(offset - length)
            length += header_len

            # Content
            content_len = part.body_size
            if (length + content_len) > offset:
                return part.get_body_chunk(offset - length)
            length += content_len

            # Boundary
            if len(parts) - 1 == i:
                boundary += b'--'
                boundary_len += 2
            if (length + boundary_len) > offset:
                return (b'\x0d\x0a--' + boundary + b'\x0d\x0a')[offset - length :]
            length += boundary_len

            self._last_len, self._last_part, self._offset = length, i, offset

        # The end, an empty string as the value of the condition of Perl's loop, which Mojo returns
        return b''

    @property
    def is_multipart(self) -> bool:
        """::

            boolean = multi.is_multipart

        True, this is a :mod:`Pyjo.Content.MultiPart` object.
        """
        return True

    # The default content parser, without a reference to the content that would make a cycle
    @staticmethod
    def _read(multi: 'Pyjo_Content_MultiPart', chunk: bytes) -> None:
        multi._multipart += chunk
        boundary = (multi.boundary or '').encode('latin-1')
        while (multi._multi_state or 'multipart_preamble') != 'finished':
            state = multi._multi_state = multi._multi_state or 'multipart_preamble'

            # Preamble
            if state == 'multipart_preamble':
                if not multi._parse_multipart_preamble(boundary):
                    break

            # Boundary
            elif state == 'multipart_boundary':
                if not multi._parse_multipart_boundary(boundary):
                    break

            # Body
            elif state == 'multipart_body':
                if not multi._parse_multipart_body(boundary):
                    break

        # Check buffer size
        if len(multi._multipart) > multi.max_buffer_size:
            multi._state, multi._limit = 'finished', True

    def _parse_multipart_body(self, boundary: bytes) -> bool:
        # Whole part in buffer
        pos = self._multipart.find(b'\x0d\x0a--' + boundary)
        if pos < 0:
            length = len(self._multipart) - (len(boundary) + 8)
            if not length > 0:
                return False

            # Store chunk
            chunk, self._multipart = self._multipart[:length], self._multipart[length:]
            self.parts[-1] = self.parts[-1].parse(chunk)
            return False

        # Store chunk
        chunk, self._multipart = self._multipart[:pos], self._multipart[pos:]
        self.parts[-1] = self.parts[-1].parse(chunk)
        self._multi_state = 'multipart_boundary'
        return True

    def _parse_multipart_boundary(self, boundary: bytes) -> bool:
        # Boundary begins
        if self._multipart.startswith(b'\x0d\x0a--' + boundary + b'\x0d\x0a'):
            self._multipart = self._multipart[len(boundary) + 6 :]

            # New part
            part = Pyjo.Content.Single.new(relaxed=True)
            self.emit('part', part)
            self.parts.append(part)
            self._multi_state = 'multipart_body'
            return True

        # Boundary ends
        end = b'\x0d\x0a--' + boundary + b'--'
        if self._multipart.startswith(end):
            self._multipart = self._multipart[len(end) :]
            self._multi_state = 'finished'

        return False

    def _parse_multipart_preamble(self, boundary: bytes) -> bool:
        # No boundary yet
        if (pos := self._multipart.find(b'--' + boundary)) < 0:
            return False

        # Replace preamble with carriage return and line feed
        self._multipart = b'\x0d\x0a' + self._multipart[pos:]

        # Parse boundary
        self._multi_state = 'multipart_boundary'
        return True


new = Pyjo_Content_MultiPart.new
object = Pyjo_Content_MultiPart
MultiPart = Pyjo_Content_MultiPart
