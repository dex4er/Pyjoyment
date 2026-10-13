r"""
Pyjo.JSON - Minimalistic JSON
=============================
::

    from Pyjo.JSON import decode_json, encode_json

    data = encode_json({'foo': [1, 2], 'bar': 'hello!', 'baz': True})
    value = decode_json(data)

:mod:`Pyjo.JSON` is a minimalistic pure-Python implementation of :rfc:`8259`.

It supports normal Python data types like :class:`dict`, :class:`list`,
:class:`tuple`, :class:`str`, numbers, booleans and ``None``, and will try to
call the ``__json__`` method on other objects, or stringify them if their class
has its own ``__str__``. Anything else becomes ``null``. Strings and numbers are
told apart by their types. ::

    [1, -2, 3]     -> [1, -2, 3]
    {"foo": "bar"} -> {'foo': 'bar'}

Literal names will be translated to and from the native Python values, which
the constants :data:`true` and :data:`false` hold too. ::

    true  -> True
    false -> False
    null  -> None

The character ``/`` will always be escaped to prevent XSS attacks. ::

    "</script>" -> "<\/script>"

For better performance the :mod:`json` module of the standard library will be
used, set up like the pure-Python implementation, with error messages of its
own. This can also be disabled with the ``PYJO_NO_JSON_STDLIB`` environment
variable.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::JSON <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/JSON.pm>`_
of Mojolicious 9.49.

Functions
---------
"""

from Pyjo.Util import decode, encode

import json
import math
import os
import re

from typing import Any, NoReturn, cast, overload


# Renamed from Mojolicious: JSON_XS and MOJO_NO_JSON_XS, after the json module of
# the standard library, which takes the place of Cpanel::JSON::XS
JSON_STDLIB = not os.environ.get('PYJO_NO_JSON_STDLIB')

# Left out from Mojolicious: CORE_BOOLS, as Python always has booleans

# Maximum nesting level for decoding, to match the default of Cpanel::JSON::XS
MAX_DEPTH = 512

# Escaped special character map
_ESCAPE = {'"': '"', '\\': '\\', '/': '/', 'b': '\x08', 'f': '\x0c', 'n': '\x0a', 'r': '\x0d', 't': '\x09'}
_REVERSE = {_ESCAPE[c]: f'\\{c}' for c in _ESCAPE} | {
    chr(c): f'\\u{c:04X}' for c in range(0x20) if chr(c) not in _ESCAPE.values()
}
_TRANSLATE = str.maketrans(_REVERSE)

_RE_ARRAY_END = re.compile(r'[\x20\x09\x0a\x0d]*\]')
_RE_COLON = re.compile(r'[\x20\x09\x0a\x0d]*:')
_RE_COMMA = re.compile(r'[\x20\x09\x0a\x0d]*,')
_RE_END = re.compile(r'[\x20\x09\x0a\x0d]*\Z')
_RE_ESCAPE = re.compile(r'\\(["\\/bfnrt])')
_RE_INVALID = re.compile(r'[\x00-\x1f\\]')
_RE_LOW_SURROGATE = re.compile(r'\\u([Dd][C-Fc-f]..)')
_RE_NUMBER = re.compile(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]*)?(?:[eE][+-]?[0-9]+)?')
_RE_OBJECT_END = re.compile(r'[\x20\x09\x0a\x0d]*\}')
_RE_QUOTE = re.compile(r'[\x20\x09\x0a\x0d]*"')
_RE_STRING = re.compile(r'(?:[^\x00-\x1f\\"]+|\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4}))*')
_RE_UNESCAPE = re.compile(r'([^\\]*)\\(?:([^u])|u(.{4}))', re.S)
_RE_WS = re.compile(r'[\x20\x09\x0a\x0d]*')


def decode_json(data: bytes | bytearray | str) -> Any:
    """::

        value = decode_json(data)

    Decode JSON to Python value and raise :exc:`ValueError` if decoding fails.
    """
    # Not in Mojolicious: the json module of the standard library, which takes
    # the place of Cpanel::JSON::XS
    if JSON_STDLIB:
        return _stdlib_decode(data)

    return _decode(data)


def default(value: object) -> Any:
    """::

        data = json.dumps(value, default=Pyjo.JSON.default)

    Turn an object that is not a :class:`dict`, :class:`list`, :class:`tuple`,
    :class:`str`, number, boolean or ``None`` into one that is, as
    :mod:`Pyjo.JSON` does: with its ``__json__`` method, as a string if its class
    has its own ``__str__``, or as ``None``. Bytes become a string of the
    characters 0-255. This is the ``default`` function for the encoder of the
    :mod:`json` module of the standard library. ::

        # '{"url": "http://example.com"}'
        json.dumps({'url': Pyjo.URL.new('http://example.com')}, default=Pyjo.JSON.default)
    """
    # Not in Mojolicious: _encode_value does it for blessed references, and the
    # json module of the standard library calls it for objects it does not know
    method = getattr(value, '__json__', None)
    if method is not None:
        return method()
    if isinstance(value, (bytes, bytearray)):
        return value.decode('latin-1')
    if type(value).__str__ is not object.__str__:
        return str(value)
    return None


def encode_json(value: object) -> bytes:
    """::

        data = encode_json({'i': '♥ pyjoyment'})

    Encode Python value to JSON.
    """
    return encode('UTF-8', to_json(value))


false = False
"""::

    from Pyjo.JSON import false

False value, the same as ``False``.
"""


def from_json(chars: str) -> Any:
    """::

        value = from_json(chars)

    Decode JSON text that is not ``UTF-8`` encoded to Python value and raise
    :exc:`ValueError` if decoding fails.
    """
    # Not in Mojolicious: the json module of the standard library
    if JSON_STDLIB:
        return _stdlib_decode(chars, True)

    return _decode(chars, True)


@overload
def j(value: list[Any] | tuple[Any, ...] | dict[Any, Any]) -> bytes: ...


@overload
def j(value: bytes | bytearray | str) -> Any: ...


def j(value: list[Any] | tuple[Any, ...] | dict[Any, Any] | bytes | bytearray | str) -> Any:
    """::

        data = j([1, 2, 3])
        data = j({'i': '♥ pyjoyment'})
        value = j(data)

    Encode Python data structure (which may only be a :class:`list`, a
    :class:`tuple` or a :class:`dict`) or decode JSON, a ``None`` return value
    indicates a bare ``null`` or that decoding failed.
    """
    if isinstance(value, (list, tuple, dict)):
        return encode_json(value)
    try:
        return decode_json(value)
    except ValueError:
        return None


def to_json(value: object) -> str:
    """::

        chars = to_json({'i': '♥ pyjoyment'})

    Encode Python value to JSON text without ``UTF-8`` encoding it.
    """
    # Not in Mojolicious: the json module of the standard library
    if JSON_STDLIB:
        return _stdlib_encode(value)

    return _encode_value(value)


true = True
"""::

    from Pyjo.JSON import true

True value, the same as ``True``.
"""


def _chars(data: bytes | bytearray | str, chars: bool) -> str:
    if isinstance(data, str) and chars:
        return data

    # UTF-8
    text = decode('UTF-8', bytes(data) if isinstance(data, bytearray) else data)
    if text is None:
        raise ValueError('Input is not UTF-8 encoded')
    return text


def _decode(data: bytes | bytearray | str, chars: bool = False) -> Any:
    # Missing input
    if not len(data):
        raise ValueError('Missing or empty input at offset 0')

    # UTF-8
    decoder = _Decoder(_chars(data, chars))

    # Value
    value = decoder.decode_value(0)

    # Leftover data
    if not decoder.match(_RE_END):
        decoder.throw('Unexpected data')

    return value


class _Decoder:
    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0

    # Unlike Mojolicious: arrays and objects are decoded here, with one call for
    # each level of nesting, as Python's recursion limit has no room for the two
    # calls of _decode_value and _decode_array for each of MAX_DEPTH levels
    def decode_value(self, depth: int) -> Any:
        # Leading whitespace
        self.match(_RE_WS)
        text = self.text
        pos = self.pos

        # String
        if text.startswith('"', pos):
            self.pos += 1
            return self.decode_string()

        # Object
        if text.startswith('{', pos):
            self.pos += 1

            # Nesting limit
            if depth + 1 > MAX_DEPTH:
                self.throw('Nesting too deep')

            hash: dict[str, Any] = {}
            if not self.match(_RE_OBJECT_END):
                while True:
                    # Quote
                    if not self.match(_RE_QUOTE):
                        self.throw('Expected string while parsing object')

                    # Key
                    key = self.decode_string()

                    # Colon
                    if not self.match(_RE_COLON):
                        self.throw('Expected colon while parsing object')

                    # Value
                    hash[key] = self.decode_value(depth + 1)

                    # Separator
                    if self.match(_RE_COMMA):
                        continue

                    # End
                    if self.match(_RE_OBJECT_END):
                        break

                    # Invalid character
                    self.throw('Expected comma or right curly bracket while parsing object')

            return hash

        # Array
        if text.startswith('[', pos):
            self.pos += 1

            # Nesting limit
            if depth + 1 > MAX_DEPTH:
                self.throw('Nesting too deep')

            array: list[Any] = []
            if not self.match(_RE_ARRAY_END):
                while True:
                    # Value
                    array.append(self.decode_value(depth + 1))

                    # Separator
                    if self.match(_RE_COMMA):
                        continue

                    # End
                    if self.match(_RE_ARRAY_END):
                        break

                    # Invalid character
                    self.throw('Expected comma or right square bracket while parsing array')

            return array

        # Number
        if number := _RE_NUMBER.match(text, pos):
            self.pos = number.end()
            return float(number[0]) if any(c in number[0] for c in '.eE') else int(number[0])

        # True
        if text.startswith('true', pos):
            self.pos += 4
            return true

        # False
        if text.startswith('false', pos):
            self.pos += 5
            return false

        # Null
        if text.startswith('null', pos):
            self.pos += 4
            return None

        # Invalid character
        self.throw('Expected string, array, object, number, boolean or null')

    def decode_string(self) -> str:
        pos = self.pos

        # Extract string with escaped characters
        self.match(_RE_STRING)
        string = self.text[pos : self.pos]

        # Invalid character
        if not self.text.startswith('"', self.pos):
            if _RE_INVALID.match(self.text, self.pos):
                self.throw('Unexpected character or invalid escape while parsing string')
            self.throw('Unterminated string')
        self.pos += 1

        # Unescape popular characters
        if '\\u' not in string:
            return _RE_ESCAPE.sub(lambda m: _ESCAPE[m[1]], string)

        # Unescape everything else
        buffer = ''
        offset = 0
        while m := _RE_UNESCAPE.match(string, offset):
            offset = m.end()
            buffer += m[1]

            # Popular character
            if m[2]:
                buffer += _ESCAPE[m[2]]

            # Escaped
            else:
                ord = int(m[3], 16)

                # Surrogate pair
                if (ord & 0xF800) == 0xD800:
                    # High surrogate
                    if (ord & 0xFC00) != 0xD800:
                        self.pos = pos + offset
                        self.throw('Missing high-surrogate')

                    # Low surrogate
                    low = _RE_LOW_SURROGATE.match(string, offset)
                    if not low:
                        self.pos = pos + offset
                        self.throw('Missing low-surrogate')
                    offset = low.end()

                    ord = 0x10000 + (ord - 0xD800) * 0x400 + (int(low[1], 16) - 0xDC00)

                # Character
                buffer += chr(ord)

        # The rest
        return buffer + string[offset:]

    def match(self, regex: re.Pattern[str]) -> bool:
        m = regex.match(self.text, self.pos)
        if m:
            self.pos = m.end()
        return m is not None

    def throw(self, message: str) -> NoReturn:
        # Leading whitespace
        pos = self.pos
        self.match(_RE_WS)

        # Context
        context = 'Malformed JSON: ' + message

        # Perl matches \z after a match of no length only when it has moved on,
        # so "before end of data" needs whitespace before the end
        if self.pos > pos and self.pos == len(self.text):
            context += ' before end of data'
        else:
            lines = self.text[: self.pos].split('\n')
            while lines and not lines[-1]:
                lines.pop()

            # Unlike Mojolicious: a last line "0" has its length, where Perl takes
            # it for false and gives offset 0
            context += f' at line {len(lines)}, offset {len(lines[-1]) if lines else 0}'

        raise ValueError(context)


def _encode_array(array: list[Any] | tuple[Any, ...]) -> str:
    return '[' + ','.join(_encode_value(v) for v in array) + ']'


def _encode_key(key: object) -> str:
    # Not in Mojolicious: keys that are not strings, converted as the json
    # module of the standard library does, as Perl's hash keys are strings
    if isinstance(key, str):
        return key
    if key is None or isinstance(key, bool):
        return _encode_value(key)
    if isinstance(key, (int, float)):
        return _encode_number(key)
    return str(key)


def _encode_number(number: int | float) -> str:
    if isinstance(number, int):
        return str(int(number))

    # Unlike Mojolicious: "inf" and "nan" are stringified the Python way, where
    # Perl gives "Inf" and "NaN"
    if not math.isfinite(number):
        return _encode_string(str(number))

    # As Perl renders numbers
    return f'{number:.15g}'


def _encode_object(object: dict[Any, Any]) -> str:
    pairs = sorted(((_encode_key(k), v) for k, v in object.items()), key=lambda pair: pair[0])
    return '{' + ','.join(_encode_string(k) + ':' + _encode_value(v) for k, v in pairs) + '}'


def _encode_string(string: str) -> str:
    return '"' + string.translate(_TRANSLATE) + '"'


def _encode_value(value: object) -> str:
    # Null
    if value is None:
        return 'null'

    # True or false
    if isinstance(value, bool):
        return 'true' if value else 'false'

    # String
    if isinstance(value, str):
        return _encode_string(value)

    # Number
    if isinstance(value, (int, float)):
        return _encode_number(value)

    # Object
    if isinstance(value, dict):
        return _encode_object(cast(dict[Any, Any], value))

    # Array
    if isinstance(value, (list, tuple)):
        return _encode_array(cast(list[Any] | tuple[Any, ...], value))

    # Everything else
    return _encode_value(default(value))


# Not in Mojolicious: the json module of the standard library, set up as Mojo
# sets up Cpanel::JSON::XS
def _stdlib_constant(name: str) -> NoReturn:
    raise ValueError(f'Malformed JSON: Unexpected {name}')


def _stdlib_decode(data: bytes | bytearray | str, chars: bool = False) -> Any:
    try:
        return json.loads(_chars(data, chars), parse_constant=_stdlib_constant)
    except RecursionError:
        raise ValueError('Malformed JSON: Nesting too deep') from None


def _stdlib_dumps(value: object) -> str:
    return json.dumps(
        value, default=default, ensure_ascii=False, allow_nan=False, separators=(',', ':'), sort_keys=True
    ).replace('/', '\\/')


def _stdlib_encode(value: object) -> str:
    try:
        return _stdlib_dumps(value)

    # "inf" and "nan", or keys that cannot be sorted
    except (TypeError, ValueError):
        return _stdlib_dumps(_stdlib_plain(value))


def _stdlib_plain(value: object) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {_encode_key(k): _stdlib_plain(v) for k, v in cast(dict[Any, Any], value).items()}
    if isinstance(value, (list, tuple)):
        return [_stdlib_plain(v) for v in cast(list[Any] | tuple[Any, ...], value)]
    return _stdlib_plain(default(value))
