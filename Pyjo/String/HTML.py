r"""
Pyjo.String.HTML - String of markup
===================================
::

    from Pyjo.String.HTML import html

    # Markup that is not escaped again
    link = html('<a href="/">Home</a>')

    # What is added to markup is escaped
    name = '<script>'
    print(html('<p>') + name + html('</p>'))

    # And what goes into it
    print(html('<p>{}</p>').format(name))
    print(html('<br>').join(['Hello', name]))

:mod:`Pyjo.String.HTML` is a :mod:`Pyjo.String.Unicode` that holds markup,
which escaping leaves as it is: :func:`Pyjo.Util.xml_escape` and anything else
that knows the ``__html__`` protocol of markupsafe, Jinja and Django. A string
that is not marked is escaped, a :mod:`Pyjo.String.Unicode` too, so that only
an explicit :func:`html` turns a string into markup.

What is added to markup, with ``+`` on either side, ``%``,
:meth:`~Pyjo_String_HTML.format`, :meth:`~Pyjo_String_HTML.format_map` or
:meth:`~Pyjo_String_HTML.join`, is escaped, unless it is markup itself, and
the result is markup. The methods of :mod:`Pyjo.String.Unicode` return markup
too, as the string has been marked explicitly; those of :class:`str` return a
:class:`str`. ::

    # "&lt;p&gt;"
    html('<p>').xml_escape()

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Inspired by ``Markup`` of `markupsafe <https://markupsafe.palletsprojects.com/>`_.

Functions
---------
"""

import Pyjo.String.Unicode
import Pyjo.Util

import builtins
import string

from collections.abc import Iterable, Mapping
from typing import Any, Self, SupportsIndex, cast


type Anything = builtins.object


class Pyjo_String_HTML(Pyjo.String.Unicode.object):
    """
    :mod:`Pyjo.String.HTML` inherits all methods from
    :mod:`Pyjo.String.Unicode` and implements the following new ones.
    """

    def __add__(self, other: Anything) -> Self:
        """::

            string = string + other

        Concatenate, escaping the other string unless it is markup.
        """
        if not isinstance(other, str) and not hasattr(other, '__html__'):
            return NotImplemented
        return self.new(str(self), _escape(other))

    def __html__(self) -> str:
        """::

            markup = string.__html__()

        The markup, as the ``__html__`` protocol gives it.
        """
        return self

    def __mod__(self, value: Anything) -> Self:
        """::

            string = string % value
            string = string % (value, value)
            string = string % {'name': value}

        Format with ``%``, escaping the values unless they are markup or
        numbers.
        """
        if isinstance(value, tuple):
            args: Any = tuple(_Escaped.of(v) for v in cast(tuple[Anything, ...], value))
        elif isinstance(value, Mapping):
            args = {k: _Escaped.of(v) for k, v in cast(Mapping[Anything, Anything], value).items()}
        else:
            args = _Escaped.of(value)
        return self.new(str(self) % args)

    def __mul__(self, value: SupportsIndex) -> Self:
        """::

            string = string * 3

        Repeat the markup.
        """
        return self.new(str(self) * value)

    def __radd__(self, other: Anything) -> Self:
        """::

            string = other + string

        Concatenate, escaping the other string unless it is markup.
        """
        if not isinstance(other, str) and not hasattr(other, '__html__'):
            return NotImplemented
        return self.new(_escape(other), str(self))

    def __rmul__(self, value: SupportsIndex) -> Self:
        """::

            string = 3 * string

        Repeat the markup.
        """
        return self.new(str(self) * value)

    def format(self, *args: Anything, **kwargs: Anything) -> Self:
        """::

            string = string.format(value, name=value)

        Format with :meth:`str.format`, escaping the fields unless they are
        markup.
        """
        return self.new(_FORMATTER.vformat(str(self), args, kwargs))

    # Any mapping that str.format_map takes, which needs only __getitem__
    def format_map(self, mapping: Any) -> Self:
        """::

            string = string.format_map({'name': value})

        Format with :meth:`str.format_map`, escaping the fields unless they
        are markup.
        """
        return self.new(_FORMATTER.vformat(str(self), (), mapping))

    def join(self, iterable: Iterable[Anything]) -> Self:
        """::

            string = string.join(['Hello', 'World'])

        Join the strings with the markup between them, escaping those that
        are not markup.
        """
        return self.new(str(self).join(map(_escape, iterable)))


def html(*parts: Anything) -> Pyjo_String_HTML:
    """::

        string = html('<p>Hello</p>')

    Construct a new :mod:`Pyjo.String.HTML` object, marking the string as
    markup.
    """
    return Pyjo_String_HTML(*parts)


# A value of the formatting with %, which gives the escaped string, as %s and %r take it; numbers go as they are
class _Escaped:
    def __init__(self, value: Anything) -> None:
        self.value = value

    def __repr__(self) -> str:
        return _escape(repr(self.value))

    def __str__(self) -> str:
        return _escape(self.value)

    @classmethod
    def of(cls, value: Anything) -> Anything:
        return value if isinstance(value, (int, float)) else cls(value)


# The formatting of str.format, which escapes the fields that are not markup after their conversion and format
class _Formatter(string.Formatter):
    def format_field(self, value: Any, format_spec: str) -> str:
        if not format_spec and hasattr(value, '__html__'):
            return value.__html__()
        return _escape(format(value, format_spec))


_FORMATTER = _Formatter()


def _escape(value: Anything) -> str:
    if (markup := getattr(value, '__html__', None)) is not None:
        return markup()
    return Pyjo.Util.xml_escape(str(value))


new = Pyjo_String_HTML.new
object = Pyjo_String_HTML
HTML = Pyjo_String_HTML
