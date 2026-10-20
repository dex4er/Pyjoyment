"""
Pyjo.Parameters - Parameters
============================
::

    import Pyjo.Parameters

    # Parse
    params = Pyjo.Parameters.new('foo=bar&baz=23')
    print(params.param('baz'))

    # Build
    params = Pyjo.Parameters.new('foo', 'bar', 'baz', 23)
    params.pairs.append(('i', '♥ pyjoyment'))
    print(params)

:mod:`Pyjo.Parameters` is a container for form parameters used by
:mod:`Pyjo.URL`, based on :rfc:`3986` and the
`HTML Living Standard <https://html.spec.whatwg.org>`_.

The parameters are pairs of a name and a value, as tuples. Methods that take
parameters take them as tuples, as names followed by their values, or as
keyword arguments: ::

    params.append(('foo', 'bar'), ('baz', 23))
    params.append('foo', 'bar', 'baz', 23)
    params.append(foo='bar', baz=23)

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Parameters <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Parameters.pm>`_
of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.Base
import Pyjo.String.Mixin

from Pyjo.Util import decode, url_escape, url_unescape

import builtins
import re

from collections.abc import Iterator
from typing import Self, cast, overload


# The module ends with `object = Pyjo_Parameters`, which an annotation of
# `object` would mean, as annotations are evaluated lazily
type Anything = builtins.object


class Pyjo_Parameters(Pyjo.Base.object, Pyjo.String.Mixin.object):
    """
    :mod:`Pyjo.Parameters` inherits all methods from :mod:`Pyjo.Base` and
    :mod:`Pyjo.String.Mixin` and implements the following new ones.
    """

    def __init__(self, *args: Anything, **kwargs: Anything) -> None:
        """::

            params = Pyjo.Parameters.new()
            params = Pyjo.Parameters.new('foo=b%3Bar&baz=23')
            params = Pyjo.Parameters.new('foo', 'b&ar')
            params = Pyjo.Parameters.new('foo', ['ba&r', 'baz'])
            params = Pyjo.Parameters.new('foo', ['bar', 'baz'], 'bar', 23)
            params = Pyjo.Parameters.new(foo=['bar', 'baz'], bar=23)

        Construct a new :mod:`Pyjo.Parameters` object and :meth:`parse` parameters
        if necessary.
        """
        self.charset: str | None = 'UTF-8'
        """::

            charset = params.charset
            params.charset = 'UTF-8'

        Charset used for encoding and decoding parameters, defaults to ``UTF-8``. ::

            # Disable encoding and decoding
            params.charset = None
        """

        self._pairs: list[tuple[str, str]] | None = None
        self._string: str | bytes | None = None

        if args or kwargs:
            self.parse(*args, **kwargs)

    def __bool__(self) -> bool:
        """::

            boolean = bool(params)

        Always true.
        """
        return True

    def __getitem__(self, index: int) -> tuple[str, str]:
        """::

            pair = params[0]

        Alias for :attr:`pairs`. Note that this will normalize the parameters. ::

            print(params[0])
        """
        return self.pairs[index]

    def __iter__(self) -> Iterator[tuple[str, str]]:
        """::

            pairs = list(params)

        Alias for :attr:`pairs`. Note that this will normalize the parameters. ::

            for name, value in params:
                print(name, value)
        """
        return iter(self.pairs)

    def __len__(self) -> int:
        """::

            size = len(params)

        Alias for :attr:`pairs`. Note that this will normalize the parameters.
        """
        return len(self.pairs)

    def __str__(self) -> str:
        """::

            string = str(params)

        Alias for :meth:`to_str`.
        """
        return self.to_str()

    def append(self, *args: Anything, **kwargs: Anything) -> Self:
        """::

            params = params.append('foo', 'ba&r')
            params = params.append('foo', ['ba&r', 'baz'])
            params = params.append('foo', ['bar', 'baz'], 'bar', 23)
            params = params.append(Pyjo.Parameters.new())

        Append parameters. Note that this method will normalize the parameters. ::

            # "foo=bar&foo=baz"
            Pyjo.Parameters.new('foo=bar').append(Pyjo.Parameters.new('foo=baz'))

            # "foo=bar&foo=baz"
            Pyjo.Parameters.new('foo=bar').append('foo', 'baz')

            # "foo=bar&foo=baz&foo=yada"
            Pyjo.Parameters.new('foo=bar').append('foo', ['baz', 'yada'])

            # "foo=bar&foo=baz&foo=yada&bar=23"
            Pyjo.Parameters.new('foo=bar').append('foo', ['baz', 'yada'], 'bar', 23)
        """
        old = self.pairs
        for name, value in _pairs(args, kwargs):
            # Multiple values
            if isinstance(value, (list, tuple)):
                old.extend((name, '' if v is None else _str(v)) for v in cast(list[Anything], value))

            # Single value
            elif value is not None:
                old.append((name, _str(value)))

        return self

    def clone(self) -> Self:
        """::

            params2 = params.clone()

        Return a new :mod:`Pyjo.Parameters` object cloned from these parameters.
        """
        clone = self.new()
        clone.charset = self.charset
        if self._string is not None:
            clone._string = self._string
        else:
            clone._pairs = list(self.pairs)
        return clone

    def every_param(self, name: Anything) -> list[str]:
        """::

            values = params.every_param('foo')

        Similar to :meth:`param`, but returns all values sharing the same name as a
        list. Note that this method will normalize the parameters. ::

            # Get first value
            print(params.every_param('foo')[0])
        """
        name = str(name)
        return [v for n, v in self.pairs if n == name]

    def merge(self, *args: Anything, **kwargs: Anything) -> Self:
        """::

            params = params.merge('foo', 'ba&r')
            params = params.merge('foo', ['ba&r', 'baz'])
            params = params.merge('foo', ['bar', 'baz'], 'bar', 23)
            params = params.merge(Pyjo.Parameters.new())

        Merge parameters. Note that this method will normalize the parameters. ::

            # "foo=baz"
            Pyjo.Parameters.new('foo=bar').merge(Pyjo.Parameters.new('foo=baz'))

            # "yada=yada&foo=baz"
            Pyjo.Parameters.new('foo=bar&yada=yada').merge('foo', 'baz')

            # "yada=yada"
            Pyjo.Parameters.new('foo=bar&yada=yada').merge('foo', None)
        """
        if len(args) == 1 and not kwargs and isinstance(args[0], Pyjo_Parameters):
            merge: dict[str, Anything] = {**args[0].to_dict()}
        else:
            merge = dict(_pairs(args, kwargs))

        for name in sorted(merge):
            if (value := merge[name]) is not None:
                self.param(name, value)
            else:
                self.remove(name)

        return self

    def names(self) -> list[str]:
        """::

            names = params.names()

        Return a list with all parameter names. ::

            # Names of all parameters
            for name in params.names():
                print(name)
        """
        return sorted(self.to_dict())

    @property
    def pairs(self) -> list[tuple[str, str]]:
        """::

            pairs = params.pairs
            params.pairs = [('foo', 'b&ar'), ('baz', '23')]

        Parsed parameter pairs. Note that this method will normalize the parameters. ::

            # Remove all parameters
            params.pairs = []
        """
        # Parse string
        if (string := self._string) is not None:
            self._string = None
            pairs: list[tuple[str, str]] = []
            self._pairs = pairs

            # Not in Mojolicious: bytes, which are a Perl byte string, the characters 0-255
            if isinstance(string, (bytes, bytearray)):
                string = string.decode('latin-1')

            for pair in string.split('&'):
                if not (m := re.match(r'^([^=]+)(?:=(.*))?$', pair)):
                    continue
                name, value = m[1], m[2] or ''

                # Replace "+" with whitespace, unescape and decode
                name = self._decode(url_unescape(name.replace('+', ' ')))
                value = self._decode(url_unescape(value.replace('+', ' ')))

                pairs.append((name, value))

        if self._pairs is None:
            self._pairs = []
        return self._pairs

    @pairs.setter
    def pairs(self, value: list[tuple[str, str]]) -> None:
        self._pairs = value
        self._string = None

    @overload
    def param(self, name: Anything, /) -> str | None: ...

    @overload
    def param(self, name: Anything, value: Anything, /, *values: Anything) -> Self: ...

    def param(self, name: Anything, /, *values: Anything) -> str | None | Self:
        """::

            value = params.param('foo')
            params = params.param('foo', 'ba&r')
            params = params.param('foo', 'ba&r', 'baz')
            params = params.param('foo', ['ba;r', 'baz'])

        Access parameter values. If there are multiple values sharing the same name,
        and you want to access more than just the last one, you can use
        :meth:`every_param`. Note that this method will normalize the parameters.
        """
        if not values:
            every = self.every_param(name)
            return every[-1] if every else None
        self.remove(name)
        value = cast(list[Anything], values[0]) if len(values) == 1 and isinstance(values[0], list) else list(values)
        return self.append(name, value)

    def parse(self, *args: Anything, **kwargs: Anything) -> Self:
        """::

            params = params.parse('foo=b%3Bar&baz=23')
            params = params.parse(parse_qsl('foo=b%3Bar&baz=23'))

        Parse parameters, given as characters or as bytes encoded with
        :attr:`charset`. A list of pairs, as :func:`urllib.parse.parse_qsl` gives, or
        a ``dict``, as :func:`urllib.parse.parse_qs` gives, is appended.
        """
        # Pairs
        # Not in Mojolicious: a list of pairs or a dict, as urllib.parse.parse_qsl
        # and parse_qs give
        if len(args) > 1 or kwargs or (args and isinstance(args[0], (tuple, list, dict, Pyjo_Parameters))):
            return self.append(*args, **kwargs)

        # String
        # Not in Mojolicious: bytes, encoded with the charset
        string = args[0] if args else None
        self._string = (
            '' if string is None else bytes(string) if isinstance(string, (bytes, bytearray)) else str(string)
        )
        self._pairs = None
        return self

    def remove(self, name: Anything) -> Self:
        """::

            params = params.remove('foo')

        Remove parameters. Note that this method will normalize the parameters. ::

            # "bar=yada"
            Pyjo.Parameters.new('foo=bar&foo=baz&bar=yada').remove('foo')
        """
        name = str(name)
        pairs = self.pairs
        pairs[:] = [(n, v) for n, v in pairs if n != name]
        return self

    def to_dict(self) -> dict[str, str | list[str]]:
        """::

            d = params.to_dict()

        Turn parameters into a dict. Note that this method will normalize the
        parameters. ::

            # "baz"
            Pyjo.Parameters.new('foo=bar&foo=baz').to_dict()['foo'][1]
        """
        d: dict[str, str | list[str]] = {}
        for name, value in self.pairs:
            # List
            if (old := d.get(name)) is not None:
                if isinstance(old, list):
                    old.append(value)
                else:
                    d[name] = [old, value]

            # String
            else:
                d[name] = value

        return d

    def to_str(self) -> str:
        """::

            string = params.to_str()

        Turn parameters into a string. ::

            # "foo=bar&baz=23"
            Pyjo.Parameters.new().set(pairs=[('foo', 'bar'), ('baz', '23')]).to_str()
        """
        # String (RFC 3986)
        if (string := self._string) is not None:
            return url_escape(self._encode(string), rb"^A-Za-z0-9\-._~%!$&'()*+,;=:@/?").decode('ascii')

        # Build pairs (HTML Living Standard)
        pairs: list[str] = []
        for name, value in self.pairs:
            # Escape and replace whitespace with "+"
            name = url_escape(self._encode(name), rb'^*\-.0-9A-Z_a-z').decode('ascii').replace('%20', '+')
            value = url_escape(self._encode(value), rb'^*\-.0-9A-Z_a-z').decode('ascii').replace('%20', '+')
            pairs.append(f'{name}={value}')

        return '&'.join(pairs)

    # Not in Mojolicious: urllib of the standard library
    def to_urllib(self) -> list[tuple[str, str]]:
        """::

            pairs = params.to_urllib()

        Turn parameters into a list of pairs, as :func:`urllib.parse.parse_qsl` gives,
        for the standard library. ::

            # "foo=bar&foo=baz"
            urlencode(Pyjo.Parameters.new('foo=bar&foo=baz').to_urllib())
        """
        return list(self.pairs)

    def _decode(self, string: str) -> str:
        # What does not decode stays characters 0-255, as a Perl byte string
        decoded = decode(self.charset or 'latin-1', string)
        return decoded if decoded is not None else string

    def _encode(self, string: str | bytes) -> bytes:
        # Without a charset, a character is a byte, as in a Perl byte string
        return string if isinstance(string, bytes) else string.encode(self.charset or 'latin-1')


# A value as a string, and bytes as the characters 0-255, as Perl has a byte string, which a charset encodes as
# characters, as Mojo does
def _str(value: Anything) -> str:
    return value.decode('latin-1') if isinstance(value, (bytes, bytearray)) else str(value)


def _pairs(args: tuple[Anything, ...], kwargs: dict[str, Anything]) -> Iterator[tuple[str, Anything]]:
    # Parameters as pairs: from another object, as tuples, as names followed by
    # their values, and as keyword arguments
    # Not in Mojolicious: tuples and keyword arguments, next to Mojo's names
    # followed by their values
    items = iter(args)
    for item in items:
        if isinstance(item, Pyjo_Parameters):
            yield from item.pairs
        elif isinstance(item, tuple):
            name, value = cast(tuple[Anything, Anything], item)
            yield str(name), value
        # Not in Mojolicious: a list of pairs or a dict of the standard library
        elif isinstance(item, list):
            yield from _pairs(tuple(cast(list[Anything], item)), {})
        elif isinstance(item, dict):
            yield from ((str(n), v) for n, v in cast(dict[Anything, Anything], item).items())
        else:
            yield str(item), next(items, None)
    yield from kwargs.items()


new = Pyjo_Parameters.new
object = Pyjo_Parameters
Parameters = Pyjo_Parameters
