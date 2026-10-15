r"""
Pyjo.String.Template - Template string with escaping
====================================================
::

    from Pyjo.String.Template import t

    name = '<script>'

    # A t-string of Python 3.14
    print(t(t'<p>{name}</p>'))

    # The same on any Python
    print(t('<p>{name}</p>'))
    print(t('<p>{name}</p>', name=name))

    # A template in a template is markup
    def link_to(text, url):
        return t(t'<a href="{url}">{text}</a>')

    print(t(t'<li>{link_to(name, "/user")}</li>'))

:mod:`Pyjo.String.Template` is a template string, a t-string of
`PEP 750 <https://peps.python.org/pep-0750/>`_, which renders into
:mod:`Pyjo.String.HTML`, escaping the values that it interpolates, unless they
are markup. :func:`t` wraps a t-string of Python 3.14, and on any Python it
takes a string with the fields of :meth:`str.format`, whose values it finds as
a t-string would.

The template has the interface of :class:`string.templatelib.Template`, its
:attr:`~Pyjo_String_Template.strings`,
:attr:`~Pyjo_String_Template.interpolations` and
:attr:`~Pyjo_String_Template.values`, and it is a string, the rendered one,
as :mod:`Pyjo.String.Mixin` makes it: ``str(template)``, ``print`` and
comparisons render it. ``Interpolation`` of this module is
:class:`string.templatelib.Interpolation` on Python 3.14, and a class with
the same interface on an older Python, so that a t-string and :func:`t` have
the same interpolations. ::

    import Pyjo.String.Template

    from Pyjo.String.Template import Interpolation

    # "<p>&lt;script&gt;</p>"
    Pyjo.String.Template.new('<p>', Interpolation(name, 'name'), '</p>')

A value is rendered by its type:

* a template, of :mod:`Pyjo.String.Template` or of Python 3.14: it is rendered
  as it is, not escaped;
* markup, an object with the method ``__html__``, as :mod:`Pyjo.String.HTML`,
  ``Markup`` of markupsafe or a template: it is inserted as it is;
* ``None``: nothing;
* an iterable, as a list, a :mod:`Pyjo.Collection` or a generator, which is
  not a string, bytes or a mapping: each of its items by these rules;
* anything else: it is formatted with :func:`format` and escaped.

A conversion (``!r``, ``!s``, ``!a``) or a format specification (``:>10``)
of the field makes a string of the value, which is escaped. ::

    # "<ul><li>&lt;b&gt;</li><li>&lt;i&gt;</li></ul>"
    tags = ['<b>', '<i>']
    t(t'<ul>{[t"<li>{tag}</li>" for tag in tags]}</ul>')

A string of :func:`t` has no code, so that a string of a user cannot run any:
a field is a name, followed by ``.attribute`` and ``[key]``, as in
:meth:`str.format`, but not by an attribute that starts with ``_``, which
would reach the internals of Python. The value of the name is the keyword
argument of the name, or the variable of the caller: a local one, a global
one or a builtin, as a t-string sees them. A function sees the variables of
the functions around it only where it uses them itself, so a variable that
only the template uses is passed as a keyword argument. ::

    # "<p>&lt;b&gt;</p>"
    t('<p>{user.name}</p>', user=user)

    # "<p>&lt;b&gt;</p>"
    t('<p>{user[name]}</p>', user={'name': '<b>'})

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Inspired by `PEP 750 <https://peps.python.org/pep-0750/>`_.

Classes
-------
"""

import Pyjo.Base
import Pyjo.String.HTML
import Pyjo.String.Mixin
import Pyjo.Util

import builtins
import inspect
import re
import string
import sys

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from types import FrameType
from typing import Any, Literal, TypeGuard


type Anything = builtins.object
type Conversion = Literal['a', 'r', 's']

if sys.version_info >= (3, 14):
    from string.templatelib import Interpolation, Template

else:

    @dataclass(frozen=True, eq=False, repr=False, slots=True)
    class Interpolation[T]:
        """::

            interpolation = Interpolation(value, 'name', 'r', '>10')

        An interpolation of a template: the value, the text of the field, the
        conversion and the format specification. It is
        :class:`string.templatelib.Interpolation` on Python 3.14.
        """

        value: T
        expression: str = ''
        conversion: Conversion | None = None
        format_spec: str = ''

        def __post_init__(self) -> None:
            if self.conversion not in (None, 'a', 'r', 's'):
                raise ValueError("Interpolation() argument 'conversion' must be one of 's', 'a' or 'r'")

        def __repr__(self) -> str:
            return f'Interpolation({self.value!r}, {self.expression!r}, {self.conversion!r}, {self.format_spec!r})'


class Pyjo_String_Template(Pyjo.Base.object, Pyjo.String.Mixin.object):
    """::

        template = Pyjo.String.Template.new('<p>', Interpolation(name, 'name'), '</p>')

    A template of strings and interpolations, as
    :class:`string.templatelib.Template` makes it.
    :mod:`Pyjo.String.Template` inherits all methods from
    :mod:`Pyjo.String.Mixin` and implements the following new ones.
    """

    def __init__(self, *args: str | Interpolation[Any]) -> None:
        strings = ['']
        interpolations: list[Interpolation[Any]] = []
        for arg in args:
            match arg:
                case str():
                    strings[-1] += str(arg)
                case Interpolation():
                    interpolations.append(arg)
                    strings.append('')
                case _:
                    raise TypeError(
                        f"Template.__init__ *args need to be of type 'str' or 'Interpolation', got {type(arg).__name__}"
                    )
        self._strings = tuple(strings)
        self._interpolations = tuple(interpolations)

    def __add__(self, other: Anything) -> Any:
        """::

            template = template + other

        Concatenate two templates into a template, or the rendered template
        with a string into :mod:`Pyjo.String.HTML`, escaping the string unless
        it is markup.
        """
        if _is_template(other):
            return self.new(*self, *other)
        if isinstance(other, str) or hasattr(other, '__html__'):
            return self.render() + other
        return NotImplemented

    def __html__(self) -> str:
        """::

            markup = template.__html__()

        The rendered template, as the ``__html__`` protocol gives it.
        """
        return str(self.render())

    def __iter__(self) -> Iterator[str | Interpolation[Any]]:
        """::

            for item in template:
                ...

        The strings that are not empty and the interpolations, in their
        order.
        """
        for s, interpolation in zip(self._strings, self._interpolations, strict=False):
            if s:
                yield s
            yield interpolation
        if self._strings[-1]:
            yield self._strings[-1]

    def __radd__(self, other: Anything) -> Any:
        """::

            template = other + template

        Concatenate two templates into a template, or a string with the
        rendered template into :mod:`Pyjo.String.HTML`, escaping the string
        unless it is markup.
        """
        if _is_template(other):
            return self.new(*other, *self)
        if isinstance(other, str) or hasattr(other, '__html__'):
            return self.render().__radd__(other)
        return NotImplemented

    def __repr__(self) -> str:
        """::

            string = repr(template)

        The template as the code that makes it.
        """
        return f'{self.__module__}.new({", ".join(map(repr, self))})'

    @property
    def interpolations(self) -> tuple[Interpolation[Any], ...]:
        """::

            interpolations = template.interpolations

        The interpolations of the template.
        """
        return self._interpolations

    def render(self) -> Pyjo.String.HTML.object:
        """::

            string = template.render()

        Render the template into :mod:`Pyjo.String.HTML`.
        """
        return Pyjo.String.HTML.new(_render(self._strings, self._interpolations))

    @property
    def strings(self) -> tuple[str, ...]:
        """::

            strings = template.strings

        The strings of the template, one more than the interpolations: the
        one before each of them and the one at the end, which can be empty.
        """
        return self._strings

    def to_str(self) -> Pyjo.String.HTML.object:
        """::

            string = template.to_str()

        The rendered template, as :meth:`render` gives it.
        """
        return self.render()

    @property
    def values(self) -> tuple[Any, ...]:
        """::

            values = template.values

        The values of the interpolations.
        """
        return tuple(i.value for i in self._interpolations)


def t(template: Anything, /, **values: Anything) -> Pyjo_String_Template:
    """::

        template = t(t'<p>{name}</p>')
        template = t('<p>{name}</p>')
        template = t('<p>{name}</p>', name=name)

    Construct a new :mod:`Pyjo.String.Template` object from a t-string of
    Python 3.14, or from a string with the fields of :meth:`str.format`, whose
    values are the keyword arguments, or the variables of the caller.
    """
    if isinstance(template, str):
        frame = inspect.currentframe()
        try:
            return Pyjo_String_Template(*_parse(str(template), values, frame and frame.f_back))
        finally:
            del frame
    if values:
        raise TypeError('t() takes keyword arguments only with a string')
    if isinstance(template, Pyjo_String_Template):
        return template
    if _is_template(template):
        return Pyjo_String_Template(*template)
    raise TypeError(f't() takes a string or a template, not {type(template).__name__}')


RE_FIELD = re.compile(r'\s*([^\W\d]\w*)((?:\.[^\W\d]\w*|\[[^\]]+\])*)\s*')
RE_ITEM = re.compile(r'\.(\w+)|\[([^\]]+)\]')

_FORMATTER = string.Formatter()


def _convert(value: Anything, conversion: str | None) -> Anything:
    if conversion == 'r':
        return repr(value)
    if conversion == 's':
        return str(value)
    if conversion == 'a':
        return ascii(value)
    return value


def _is_template(value: Anything) -> TypeGuard[Iterable[str | Interpolation[Any]]]:
    if isinstance(value, Pyjo_String_Template):
        return True
    if sys.version_info >= (3, 14):
        return isinstance(value, Template)
    return False


def _iterable(value: Anything) -> bool:
    return isinstance(value, Iterable) and not isinstance(
        value, (str, bytes, bytearray, Mapping, Pyjo.String.Mixin.object)
    )


def _lookup(field: str, values: Mapping[str, Anything], frame: FrameType | None) -> Any:
    if (m := RE_FIELD.fullmatch(field)) is None:
        if not field.strip() or field.strip().isdigit():
            raise ValueError(f'Field {field!r} is positional, t() takes names only')
        raise ValueError(
            f'Field {field!r} is not a name with attributes and keys, pass its value as a keyword argument instead'
        )
    name, rest = m.groups()
    value: Any
    if name in values:
        value = values[name]
    elif frame is None:
        raise NameError(f'name {name!r} is not defined', name=name)
    elif name in frame.f_locals:
        value = frame.f_locals[name]
    elif name in frame.f_globals:
        value = frame.f_globals[name]
    elif name in frame.f_builtins:
        value = frame.f_builtins[name]
    else:
        raise NameError(f'name {name!r} is not defined', name=name)
    for item in RE_ITEM.finditer(rest):
        attr, key = item.groups()
        if attr is not None:
            if attr.startswith('_'):
                raise ValueError(f'Field {field!r} has an attribute that starts with "_"')
            value = getattr(value, attr)
        else:
            value = value[int(key) if key.isdigit() else key]
    return value


def _parse(source: str, values: Mapping[str, Anything], frame: FrameType | None) -> Iterator[str | Interpolation[Any]]:
    try:
        for text, field, spec, conversion in _FORMATTER.parse(source):
            yield text
            if field is None:
                continue
            format_spec = spec or ''
            expression = field
            if field.rstrip().endswith('='):
                # The text of the field is kept and its value is the repr, as with "=" of a t-string
                expression = field.rstrip()[:-1]
                yield field
                if conversion is None and not format_spec:
                    conversion = 'r'
            if conversion not in (None, 'a', 'r', 's'):
                raise ValueError(f'Field {field!r} has an unknown conversion {conversion!r}')
            value = _lookup(expression, values, frame)
            if '{' in format_spec:
                format_spec = ''.join(_spec(format_spec, values, frame))
            yield Interpolation(value, expression, conversion, format_spec)
    finally:
        del frame


def _render(strings: tuple[str, ...], interpolations: tuple[Interpolation[Any], ...]) -> str:
    parts = [strings[0]]
    for interpolation, s in zip(interpolations, strings[1:], strict=True):
        parts.append(_value(interpolation.value, interpolation.conversion, interpolation.format_spec))
        parts.append(s)
    return ''.join(parts)


# A format specification with fields, which give strings as they are, as in a t-string
def _spec(format_spec: str, values: Mapping[str, Anything], frame: FrameType | None) -> Iterator[str]:
    for text, field, spec, conversion in _FORMATTER.parse(format_spec):
        yield text
        if field is not None:
            if '{' in (spec := spec or ''):
                raise ValueError('Max string recursion exceeded')
            yield format(_convert(_lookup(field, values, frame), conversion), spec)


def _value(value: Any, conversion: str | None, format_spec: str) -> str:
    if conversion or format_spec:
        return Pyjo.Util.xml_escape(format(_convert(value, conversion), format_spec))
    if isinstance(value, Pyjo_String_Template):
        return _render(value.strings, value.interpolations)
    if sys.version_info >= (3, 14) and isinstance(value, Template):
        return _render(value.strings, value.interpolations)
    if (markup := getattr(value, '__html__', None)) is not None:
        return markup()
    if value is None:
        return ''
    if _iterable(value):
        return ''.join(_value(v, None, '') for v in value)
    return Pyjo.Util.xml_escape(format(value, ''))


new = Pyjo_String_Template.new
object = Pyjo_String_Template
