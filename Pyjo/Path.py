"""
Pyjo.Path - Path
================
::

    import Pyjo.Path

    # Parse
    path = Pyjo.Path.new('/foo%2Fbar%3B/baz.html')
    print(path[0])

    # Build
    path = Pyjo.Path.new('/i/♥')
    path.parts.append('pyjoyment')
    print(path)

:mod:`Pyjo.Path` is a container for paths used by :mod:`Pyjo.URL`, based on
:rfc:`3986`.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Path <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Path.pm>`_
of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.Base
import Pyjo.String.Mixin

from Pyjo.Util import decode, url_escape, url_unescape

import re

from collections.abc import Iterator
from typing import Self


class Pyjo_Path(Pyjo.Base.object, Pyjo.String.Mixin.object):
    """
    :mod:`Pyjo.Path` inherits all methods from :mod:`Pyjo.Base` and
    :mod:`Pyjo.String.Mixin` and implements the following new ones.
    """

    def __init__(self, path: 'str | bytes | Pyjo_Path | None' = None) -> None:
        """::

            path = Pyjo.Path.new()
            path = Pyjo.Path.new('/foo%2Fbar%3B/baz.html')

        Construct a new :mod:`Pyjo.Path` object and :meth:`parse` path if necessary.
        """
        self.charset: str | None = 'UTF-8'
        """::

            charset = path.charset
            path.charset = 'UTF-8'

        Charset used for encoding and decoding, defaults to ``UTF-8``. ::

            # Disable encoding and decoding
            path.charset = None
        """

        self._path: str | bytes | None = None
        self._parts: list[str] | None = None
        self._leading_slash = False
        self._trailing_slash = False

        if path is not None:
            self.parse(path)

    def __bool__(self) -> bool:
        """::

            boolean = bool(path)

        Always true.
        """
        return True

    def __getitem__(self, index: int) -> str:
        """::

            part = path[0]

        Alias for :attr:`parts`. Note that this will normalize the path and that
        ``%2F`` will be treated as ``/`` for security reasons. ::

            print(path[0])
        """
        return self.parts[index]

    def __iter__(self) -> Iterator[str]:
        """::

            parts = list(path)

        Alias for :attr:`parts`. Note that this will normalize the path and that
        ``%2F`` will be treated as ``/`` for security reasons. ::

            for part in path:
                print(part)
        """
        return iter(self.parts)

    def __len__(self) -> int:
        """::

            size = len(path)

        Alias for :attr:`parts`. Note that this will normalize the path and that
        ``%2F`` will be treated as ``/`` for security reasons.
        """
        return len(self.parts)

    def __str__(self) -> str:
        """::

            string = str(path)

        Alias for :meth:`to_str`.
        """
        return self.to_str()

    def canonicalize(self) -> Self:
        """::

            path = path.canonicalize()

        Canonicalize path by resolving ``.`` and ``..``, in addition ``...`` will be
        treated as ``.`` to protect from path traversal attacks. ::

            # "/foo/baz"
            Pyjo.Path.new('/foo/./bar/../baz').canonicalize()

            # "/../baz"
            Pyjo.Path.new('/foo/../bar/../../baz').canonicalize()

            # "/foo/bar"
            Pyjo.Path.new('/foo/.../bar').canonicalize()
        """
        parts = self.parts
        i = 0
        while i < len(parts):
            if parts[i] in ('', '.', '...'):
                del parts[i]
            elif i < 1 or parts[i] != '..' or parts[i - 1] == '..':
                i += 1
            else:
                i -= 1
                del parts[i : i + 2]

        if not parts:
            self.trailing_slash = False
        return self

    def clone(self) -> Self:
        """::

            clone = path.clone()

        Return a new :mod:`Pyjo.Path` object cloned from this path.
        """
        clone = self.new()
        clone.charset = self.charset
        if self._parts is not None:
            clone._leading_slash = self._leading_slash
            clone._trailing_slash = self._trailing_slash
            clone._parts = list(self._parts)
        else:
            clone._path = self._path
        return clone

    def contains(self, prefix: str) -> bool:
        """::

            boolean = path.contains('/i/♥/pyjoyment')

        Check if path contains given prefix. ::

            # True
            Pyjo.Path.new('/foo/bar').contains('/')
            Pyjo.Path.new('/foo/bar').contains('/foo')
            Pyjo.Path.new('/foo/bar').contains('/foo/bar')

            # False
            Pyjo.Path.new('/foo/bar').contains('/f')
            Pyjo.Path.new('/foo/bar').contains('/bar')
            Pyjo.Path.new('/foo/bar').contains('/whatever')
        """
        return prefix == '/' or re.match(re.escape(prefix) + r'(?:/|$)', self.to_route()) is not None

    @property
    def leading_slash(self) -> bool:
        """::

            boolean = path.leading_slash
            path.leading_slash = boolean

        Path has a leading slash. Note that this method will normalize the path and
        that ``%2F`` will be treated as ``/`` for security reasons. ::

            # "/foo/bar"
            Pyjo.Path.new('foo/bar').set(leading_slash=True)

            # "foo/bar"
            Pyjo.Path.new('/foo/bar').set(leading_slash=False)
        """
        self._parse()
        return self._leading_slash

    @leading_slash.setter
    def leading_slash(self, value: bool) -> None:
        self._parse()
        self._leading_slash = value

    def merge(self, path: 'str | bytes | Pyjo_Path') -> Self:
        """::

            path = path.merge('/foo/bar')
            path = path.merge('foo/bar')
            path = path.merge(Pyjo.Path.new())

        Merge paths. Note that this method will normalize both paths if necessary and
        that ``%2F`` will be treated as ``/`` for security reasons. ::

            # "/baz/yada"
            Pyjo.Path.new('/foo/bar').merge('/baz/yada')

            # "/foo/baz/yada"
            Pyjo.Path.new('/foo/bar').merge('baz/yada')

            # "/foo/bar/baz/yada"
            Pyjo.Path.new('/foo/bar/').merge('baz/yada')
        """
        # Replace
        # Not in Mojolicious: bytes, encoded with the charset
        if path.startswith(b'/') if isinstance(path, bytes) else str(path).startswith('/'):
            return self.parse(path)

        # Merge
        if not self.trailing_slash and self.parts:
            self.parts.pop()
        other = self.new(path)
        self.parts.extend(other.parts)
        self.trailing_slash = other.trailing_slash
        return self

    def parse(self, path: 'str | bytes | Pyjo_Path') -> Self:
        """::

            path = path.parse('/foo%2Fbar%3B/baz.html')

        Parse path, given as characters or as bytes encoded with :attr:`charset`.
        """
        # Not in Mojolicious: bytes, encoded with the charset
        self._path = path if isinstance(path, bytes) else str(path)
        self._parts = None
        self._leading_slash = self._trailing_slash = False
        return self

    @property
    def parts(self) -> list[str]:
        """::

            parts = path.parts
            path.parts = ['foo', 'bar', 'baz']

        The path parts. Note that this method will normalize the path and that
        ``%2F`` will be treated as ``/`` for security reasons. ::

            # Part with slash
            path.parts.append('foo/bar')
        """
        return self._parse()

    @parts.setter
    def parts(self, value: list[str]) -> None:
        self._parse()
        self._parts = value

    def to_abs_str(self) -> str:
        """::

            string = path.to_abs_str()

        Turn path into an absolute string. ::

            # "/i/%E2%99%A5/pyjoyment"
            Pyjo.Path.new('/i/%E2%99%A5/pyjoyment').to_abs_str()
            Pyjo.Path.new('i/%E2%99%A5/pyjoyment').to_abs_str()
        """
        path = self.to_str()
        return path if path.startswith('/') else f'/{path}'

    def to_dir(self) -> Self:
        """::

            dir = route.to_dir()

        Clone path and remove everything after the right-most slash. ::

            # "/i/%E2%99%A5/"
            Pyjo.Path.new('/i/%E2%99%A5/pyjoyment').to_dir().to_abs_str()

            # "i/%E2%99%A5/"
            Pyjo.Path.new('i/%E2%99%A5/pyjoyment').to_dir().to_abs_str()
        """
        clone = self.clone()
        if not clone.trailing_slash and clone.parts:
            clone.parts.pop()
        clone.trailing_slash = bool(clone.parts)
        return clone

    def to_route(self) -> str:
        """::

            route = path.to_route()

        Turn path into a route. ::

            # "/i/♥/pyjoyment"
            Pyjo.Path.new('/i/%E2%99%A5/pyjoyment').to_route()
            Pyjo.Path.new('i/%E2%99%A5/pyjoyment').to_route()
        """
        clone = self.clone()
        return '/' + '/'.join([*clone.parts, ''] if clone.trailing_slash else clone.parts)

    def to_str(self) -> str:
        """::

            string = path.to_str()

        Turn path into a string. ::

            # "/i/%E2%99%A5/pyjoyment"
            Pyjo.Path.new('/i/%E2%99%A5/pyjoyment').to_str()

            # "i/%E2%99%A5/pyjoyment"
            Pyjo.Path.new('i/%E2%99%A5/pyjoyment').to_str()
        """
        # Path
        if self._path is not None:
            return url_escape(self._encode(self._path), rb"^A-Za-z0-9\-._~!$&'()*+,;=%:@/").decode('ascii')

        # Build path
        path = '/'.join(
            url_escape(self._encode(p), rb"^A-Za-z0-9\-._~!$&'()*+,;=:@").decode('ascii') for p in self.parts
        )
        if self.leading_slash:
            path = f'/{path}'
        if self.trailing_slash:
            path = f'{path}/'
        return path

    @property
    def trailing_slash(self) -> bool:
        """::

            boolean = path.trailing_slash
            path.trailing_slash = boolean

        Path has a trailing slash. Note that this method will normalize the path and
        that ``%2F`` will be treated as ``/`` for security reasons. ::

            # "/foo/bar/"
            Pyjo.Path.new('/foo/bar').set(trailing_slash=True)

            # "/foo/bar"
            Pyjo.Path.new('/foo/bar/').set(trailing_slash=False)
        """
        self._parse()
        return self._trailing_slash

    @trailing_slash.setter
    def trailing_slash(self, value: bool) -> None:
        self._parse()
        self._trailing_slash = value

    def _encode(self, string: str | bytes) -> bytes:
        # Without a charset, a character is a byte, as in a Perl byte string
        return string if isinstance(string, bytes) else string.encode(self.charset or 'latin-1')

    def _decode(self, path: str | bytes) -> str:
        # What does not decode stays characters 0-255, as a Perl byte string
        if (decoded := decode(self.charset or 'latin-1', path)) is not None:
            return decoded
        return path if isinstance(path, str) else path.decode('latin-1')

    def _parse(self) -> list[str]:
        if self._parts is None:
            path = self._decode(url_unescape(self._path or ''))
            self._path = None

            self._leading_slash = path.startswith('/')
            path = path.removeprefix('/')
            self._trailing_slash = path.endswith('/')
            path = path.removesuffix('/')
            self._parts = path.split('/') if path else []

        return self._parts


new = Pyjo_Path.new
object = Pyjo_Path
Path = Pyjo_Path
