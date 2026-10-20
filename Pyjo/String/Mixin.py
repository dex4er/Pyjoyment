"""
Pyjo.String.Mixin - Object with to_bytes/to_str methods
=======================================================
::

    import Pyjo.Base

    from Pyjo.String.Mixin import Mixin

    class SubClass(Pyjo.Base.object, Mixin):
        def to_bytes(self):
            return b'value'

        def to_str(self):
            return 'value'

    # Use it as a string
    obj = SubClass()
    print(f'{obj:>10}')
    print(obj + '!')

    # Or import the module, as in Google Python Style Guide

    import Pyjo.Base
    import Pyjo.String.Mixin

    class SubClass(Pyjo.Base.object, Pyjo.String.Mixin.object):
        def to_bytes(self):
            return b'value'

        def to_str(self):
            return 'value'

    # Use it as a string
    obj = SubClass.new()
    print(f'{obj:>10}')
    print(obj + '!')

:mod:`Pyjo.String.Mixin` is the mixin class for objects with a
:meth:`to_str` and/or a :meth:`to_bytes` method, which turns them into strings
wherever Python converts, compares or concatenates them, as Perl does with the
overloaded ``""`` of Mojo's objects. The string form is the one of
:meth:`to_str`, or of :meth:`to_bytes` for an object that has only it.

A class that mixes it in overrides a conversion where its value means
something else than its string form, as :mod:`Pyjo.Date` does with
:meth:`~Pyjo_String_Mixin.__float__`, or where it is a container of its own,
as :mod:`Pyjo.Path` is a sequence of its parts: the mixin leaves out
``__len__``, ``__iter__`` and ``__contains__``, which would make every
object a sequence of characters.

The object is not a :class:`str`, so a function that takes only an instance
of it, like :meth:`str.join` or :func:`urllib.parse.quote`, gets
``str(obj)``. ::

    # 'value/value'
    '/'.join(str(obj) for obj in (SubClass.new(), SubClass.new()))

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Classes
-------
"""

import Pyjo.Base
import Pyjo.String.Bytes
import Pyjo.String.Unicode

import builtins
import math

from typing import Any


type Anything = builtins.object


class Pyjo_String_Mixin:
    """
    This mixin does not provide own constructor method
    and implements the following new methods.
    """

    def __add__(self, other: Anything) -> 'Pyjo.String.Unicode.object | Pyjo.String.Bytes.object':
        """::

            string = obj + 'string'

        Concatenate the string form of the object with another string, as a
        :mod:`Pyjo.String.Unicode` object, or a :mod:`Pyjo.String.Bytes` object
        for bytes.
        """
        if (result := _concat(_string(self), other)) is None:
            return NotImplemented
        return result

    def __bool__(self) -> bool:
        """::

            boolean = bool(obj)

        True if the string form is not empty.
        """
        return bool(_string(self))

    def __bytes__(self) -> bytes:
        """::

            bstring = bytes(obj)

        Bytes of the object, :meth:`to_bytes`, or :meth:`to_str` encoded with
        ``UTF-8``.
        """
        if (to_bytes := getattr(self, 'to_bytes', None)) is not None:
            return bytes(to_bytes())
        string = _string(self)
        return string.encode() if isinstance(string, str) else string

    def __ceil__(self) -> int:
        """::

            number = math.ceil(obj)

        The smallest integer that is not less than ``float(obj)``.
        """
        return math.ceil(float(self))

    def __complex__(self) -> complex:
        """::

            number = complex(obj)

        Convert the string form into a complex number.
        """
        string = _string(self)
        return complex(string.decode() if isinstance(string, bytes) else string)

    def __eq__(self, other: Anything) -> bool:
        """::

            boolean = obj == other

        True if the string form of the object is equal to the other value.
        """
        return _string(self) == other

    def __float__(self) -> float:
        """::

            number = float(obj)

        Convert the string form into a float number.
        """
        return float(_string(self))

    def __floor__(self) -> int:
        """::

            number = math.floor(obj)

        The largest integer that is not greater than ``float(obj)``.
        """
        return math.floor(float(self))

    def __format__(self, format_spec: str) -> str:
        """::

            string = format(obj, '>10')
            string = f'{obj:>10}'

        Format the string form, ``str(obj)``, as :func:`format` formats a
        :class:`str`.
        """
        return format(str(self), format_spec)

    def __ge__(self, other: Anything) -> bool:
        """::

            boolean = obj >= other

        True if the string form of the object is equal to or greater than the
        other value.
        """
        return _cmp(self) >= other

    def __gt__(self, other: Anything) -> bool:
        """::

            boolean = obj > other

        True if the string form of the object is greater than the other value.
        """
        return _cmp(self) > other

    def __hash__(self) -> int:
        """::

            number = hash(obj)

        Hash of the string form, so that the object and its string are the
        same key of a :class:`dict`.
        """
        return hash(_string(self))

    def __int__(self) -> int:
        """::

            number = int(obj)

        Convert the string form into an integer number.
        """
        return int(_string(self))

    def __le__(self, other: Anything) -> bool:
        """::

            boolean = obj <= other

        True if the string form of the object is equal to or less than the
        other value.
        """
        return _cmp(self) <= other

    def __lt__(self, other: Anything) -> bool:
        """::

            boolean = obj < other

        True if the string form of the object is less than the other value.
        """
        return _cmp(self) < other

    def __ne__(self, other: Anything) -> bool:
        """::

            boolean = obj != other

        True if the string form of the object is not equal to the other value.
        """
        return _string(self) != other

    def __radd__(self, other: Anything) -> 'Pyjo.String.Unicode.object | Pyjo.String.Bytes.object':
        """::

            string = 'string' + obj

        Concatenate another string with the string form of the object, as a
        :mod:`Pyjo.String.Unicode` object, or a :mod:`Pyjo.String.Bytes` object
        for bytes.
        """
        string = _string(self)
        if not isinstance(other, type(string)) or (result := _concat(other, string)) is None:
            return NotImplemented
        return result

    def __repr__(self) -> str:
        """::

            string = repr(obj)

        Representation of the object, with its string form:
        ``Pyjo.URL.new('http://example.com')``.
        """
        string = str(self) if getattr(self, 'to_str', None) is not None else bytes(self)
        if self.__module__ == '__main__':
            return f'{self.__class__.__name__}({string!r})'
        if isinstance(self, Pyjo.Base.object):
            return f'{self.__module__}.new({string!r})'
        return f'{self.__module__}.{self.__class__.__name__}({string!r})'

    def __round__(self, ndigits: int | None = None) -> int | float:
        """::

            number = round(obj)
            number = round(obj, 2)

        ``float(obj)`` rounded, to an integer without ``ndigits``.
        """
        return round(float(self), ndigits)

    def __str__(self) -> str:
        """::

            string = str(obj)

        String form of the object, :meth:`to_str`, or the representation of
        the bytes of :meth:`to_bytes`, as ``str(b'value')`` gives it.
        """
        string = _string(self)
        return string if isinstance(string, str) else repr(string)

    def __trunc__(self) -> int:
        """::

            number = math.trunc(obj)

        ``float(obj)`` without its fraction.
        """
        return math.trunc(float(self))


# The string form: what to_str or to_bytes gives
def _string(obj: Anything) -> str | bytes:
    if (to_str := getattr(obj, 'to_str', None)) is not None:
        return str(to_str())
    if (to_bytes := getattr(obj, 'to_bytes', None)) is not None:
        return to_bytes()
    raise NotImplementedError('Method "to_bytes" or "to_str" not implemented by subclass')


# The string form for a comparison, which raises TypeError for another type, as the str or bytes does
def _cmp(obj: Anything) -> Any:
    return _string(obj)


# The concatenation of strings of the same type, None for another type
def _concat(string: str | bytes, other: Anything) -> 'Pyjo.String.Unicode.object | Pyjo.String.Bytes.object | None':
    if isinstance(other, Pyjo_String_Mixin):
        other = _string(other)
    if isinstance(string, str):
        if not isinstance(other, str):
            return None
        return Pyjo.String.Unicode.new(string + other)
    if not isinstance(other, bytes | bytearray):
        return None
    return Pyjo.String.Bytes.new(string + other)


object = Pyjo_String_Mixin
Mixin = Pyjo_String_Mixin
