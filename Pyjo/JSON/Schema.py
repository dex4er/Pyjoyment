"""
Pyjo.JSON.Schema - JSON Schema from type hints, and its validation
==================================================================
::

    from Pyjo.JSON.Schema import Schema, z

    def weather(city: str, days: int = 3) -> dict[str, float]:
        \"\"\"Forecast of the weather.

        :param city: Name of the city.
        :param days: Number of days.
        \"\"\"

    print(Schema.parameters(weather).data)
    print(Schema.returns(weather).data)

    print(z.object(city=z.string().describe('Name of the city'), days=z.int().min(1).optional()).data)

    result = Schema.parameters(weather).validate({'city': 'Warsaw', 'days': 'three'})
    if not result:
        print(result)

    # Or import the module, as in Google Python Style Guide

    import Pyjo.JSON.Schema

    print(Pyjo.JSON.Schema.of(list[int]).data)
    print(Pyjo.JSON.Schema.new({'type': 'string'}).data)

:mod:`Pyjo.JSON.Schema` makes `JSON Schema 2020-12
<https://json-schema.org/draft/2020-12>`_ from the type hints of Python, from
the annotations of a type or of the parameters and the return value of a
function, with the descriptions of its docstring, or builds it with a chain of
methods, after `zod <https://zod.dev>`_, so that the schema of a tool of
JavaScript ports as it is. Both give an object of :mod:`Pyjo.JSON.Schema`,
which holds the schema in :attr:`~Pyjo_JSON_Schema.data`, as :mod:`Pyjo.JSON`
encodes it, and so does a schema written by hand.

The types of the type hints, and the schemas that they give:

* ``bool``, ``int``, ``float``, ``str`` and ``None`` are ``boolean``,
  ``integer``, ``number``, ``string`` and ``null``, and ``Any`` and ``object``
  are ``{}``, any value;
* ``list[T]``, ``set[T]`` and ``frozenset[T]`` are an ``array`` of ``items``,
  the sets with ``uniqueItems``, ``tuple[A, B]`` an ``array`` of
  ``prefixItems``, and ``tuple[T, ...]`` one of ``items``;
* ``dict[str, T]`` is an ``object`` of ``additionalProperties``;
* ``T | None`` and ``Optional[T]`` add ``null`` to the ``type`` of a schema
  that has only a type, and are an ``anyOf`` with ``null`` otherwise, and other
  unions are ``anyOf``;
* ``Literal`` is a ``const`` or an ``enum``, and so is an :class:`enum.Enum` of
  its values, with their ``type`` where they have one;
* a ``TypedDict`` is an ``object`` whose ``required`` are its required keys,
  closed with ``closed=True`` of :pep:`728`, and a dataclass one whose
  ``required`` are the fields without a default;
* :class:`datetime.datetime`, :class:`datetime.date`, :class:`datetime.time`,
  :class:`uuid.UUID` and :mod:`Pyjo.URL` are a ``string`` with the ``format``
  ``date-time``, ``date``, ``time``, ``uuid`` and ``uri``;
* ``Annotated[T, ...]`` adds a string as the ``description``, and the keywords
  of a :class:`dict`, as ``minimum`` and ``pattern``, or of a schema, as
  ``z.email()``, without a class of a library of validation;
* a ``type`` alias is its value, and a ``NewType`` its type.

A ``TypedDict``, a dataclass, an :class:`enum.Enum` or a ``type`` alias that is
used more than once, or a type that refers to itself, goes to ``$defs``, where
a ``$ref`` refers to it. A schema that refers to itself refers to its root with
``#``, so that the root stays an ``object``, as the ``inputSchema`` of a tool
of MCP has to be. The description of a ``TypedDict``, a dataclass or an
:class:`enum.Enum` is the first paragraph of its docstring.

A type that has no schema, as ``bytes``, a ``TypeVar`` or a class of its own,
fails with a :mod:`Pyjo.Exception` that names it and where it is. The
annotations are those that :func:`typing.get_type_hints` gives, lazy as of
:pep:`649`, or strings with ``from __future__ import annotations``, so a name
that the module of a type does not have fails too.

A schema has no ``$schema``, as the schemas of MCP and OpenAPI, whose dialect is
known. :data:`DIALECT` names it on request, with
:meth:`~Pyjo_JSON_Schema.meta`. ::

    # {'$schema': 'https://json-schema.org/draft/2020-12/schema', 'type': 'string'}
    z.string().meta({'$schema': Pyjo.JSON.Schema.DIALECT}).data

The builder is a subset of zod, what JSON Schema has, without its
transformations, refinements, coercions and the types that are inferred from a
schema. Its methods are those of zod in the names of Python, ``multiple_of``
for ``multipleOf``, and ``z`` is the class itself, so that
``z.object({...})`` reads as in JavaScript. An ``object`` is as zod gives it
for the input, which a tool gets: a property that has a ``default`` is not
required, and the properties that it does not name are not forbidden, unless
the object is strict. Where zod gives another schema of the same, the method
says so.

Validation
----------

:meth:`~Pyjo_JSON_Schema.validate` validates a value, as :mod:`Pyjo.JSON`
decodes it, with a schema of any of the three forms, and gives a
:class:`Result`, which is false if the value is not valid, with the errors of
the value, each with the JSON Pointer of the value and of the keyword. ::

    # /days: Expected integer - got string.
    print(z.object(days=z.int()).validate({'days': 'three'}))

It is the validation of JSON Schema 2020-12 with the keywords that the schema of
a tool, of a body of an API or of a configuration has:

* ``type``, ``enum`` and ``const``;
* ``minimum``, ``maximum``, ``exclusiveMinimum``, ``exclusiveMaximum`` and
  ``multipleOf`` of numbers;
* ``minLength``, ``maxLength``, ``pattern`` and ``format`` of strings;
* ``items``, ``prefixItems``, ``minItems``, ``maxItems``, ``uniqueItems``,
  ``contains``, ``minContains`` and ``maxContains`` of arrays;
* ``properties``, ``required``, ``additionalProperties``,
  ``patternProperties``, ``propertyNames``, ``minProperties``,
  ``maxProperties``, ``dependentRequired`` and ``dependentSchemas`` of
  objects;
* ``allOf``, ``anyOf``, ``oneOf``, ``not``, ``if``, ``then`` and ``else``;
* ``$ref`` to the schemas of the document, by a JSON Pointer, as to ``$defs``,
  by their ``$anchor`` and by the ``$id`` of a schema in the schema, also to
  itself, and to the schemas of the registry of
  :meth:`~Pyjo_JSON_Schema.add_schema`, which it never downloads.

The keywords of 2020-12 that it does not support, ``$dynamicRef``,
``unevaluatedItems`` and ``unevaluatedProperties``, and a ``$schema`` of
another dialect, fail with a :mod:`Pyjo.Exception`, as a ``$ref`` to a schema
that it does not have does, and a keyword that 2020-12 does not have, as
``additionalItems`` of the older drafts, is ignored, as the specification says
of a keyword that it does not know. The annotations, as ``title``,
``default`` and ``contentMediaType``, validate nothing.

The values are those of JSON: ``bool`` is not an ``integer`` nor a ``number``,
a ``float`` without a fraction is an ``integer``, ``1`` and ``1.0`` are equal
for ``enum``, ``const`` and ``uniqueItems``, ``True`` and ``1`` are not, and a
``tuple`` is an ``array``. A value that JSON does not have, as ``bytes``, a
``set``, ``nan`` or a name of a property that is not a string, is an error of
its own, whatever the schema.

``format`` is an annotation, as JSON Schema has it by default, and an
assertion with ``formats``, for the formats ``date-time``, ``date``, ``time``
and ``duration`` of RFC 3339, ``email``, ``hostname``, ``ipv4``, ``ipv6``,
``uri``, ``uri-reference``, ``uuid``, ``regex``, ``json-pointer`` and
``relative-json-pointer``. Another format, as ``idn-email``, ``iri`` or
``uri-template``, stays an annotation.

A ``pattern`` is a regular expression of ECMAScript, which is one of
:mod:`re` with these translations: ``\\d``, ``\\w`` and ``\\b`` are of ASCII,
``\\s`` is the white space of ECMAScript, ``.`` matches no line terminator,
``$`` matches only at the end, a named group is ``(?<name>...)`` and its
backreference ``\\k<name>``, ``\\p{...}`` is a general category of Unicode,
or ``ASCII``, ``Any`` and ``Assigned``, and ``\\cX``, ``\\u{...}``, ``[]``
and ``[^]`` are as ECMAScript has them. What :mod:`re` does not have, as a
lookbehind of a variable width or ``\\p{Script=...}``, and the syntax of
Python that ECMAScript does not have, as ``(?P<name>...)``, fail with a
:mod:`Pyjo.Exception`.

See also
--------

:mod:`Pyjo.JSON`, :mod:`Pyjo.JSON.Pointer`, https://mojolicious.org.

It has no counterpart in Mojolicious, it is written from the specification of
JSON Schema 2020-12, its builder is inspired by `zod <https://zod.dev>`_, and
its validation is tested with the official test suite of JSON Schema,
`JSON-Schema-Test-Suite <https://github.com/json-schema-org/JSON-Schema-Test-Suite>`_.

Classes
-------
"""

import Pyjo.Base
import Pyjo.Collection
import Pyjo.Exception
import Pyjo.JSON
import Pyjo.JSON.Pointer
import Pyjo.URL

from Pyjo.JSON import to_json
from Pyjo.Util import punycode_decode

import builtins
import collections
import contextlib
import dataclasses
import datetime
import enum
import fractions
import functools
import inspect
import ipaddress
import math
import re
import sys
import types
import typing
import unicodedata
import uuid

from collections.abc import Callable, Iterable
from typing import Any, Self, cast


type Anything = builtins.object

DIALECT = 'https://json-schema.org/draft/2020-12/schema'
"""The dialect of the schemas, JSON Schema 2020-12, as ``$schema`` names it."""

# The keywords of a constraint for each type, as min() and max() set them
_MIN = {'string': 'minLength', 'number': 'minimum', 'integer': 'minimum', 'array': 'minItems'}
_MAX = {'string': 'maxLength', 'number': 'maximum', 'integer': 'maximum', 'array': 'maxItems'}

# The qualifiers of the keys of a TypedDict, ReadOnly of Python 3.13 too
_QUALIFIERS = tuple(
    q for q in (typing.Required, typing.NotRequired, getattr(typing, 'ReadOnly', None)) if q is not None
)

# The formats of the types of the standard library
_FORMATS: dict[type, str] = {
    datetime.datetime: 'date-time',
    datetime.date: 'date',
    datetime.time: 'time',
    uuid.UUID: 'uuid',
}

# The sections of a docstring of the Google Python Style Guide
_RE_ARGS = re.compile(r'(?:Args|Arguments|Parameters|Params|Keyword Args|Keyword Arguments):')
_RE_RETURNS = re.compile(r'(?:Returns|Return|Yields):')
_RE_SECTION = re.compile(r'[A-Z][A-Za-z ]*:')
_RE_FIELD = re.compile(r':(param|parameter|arg|argument|key|keyword|returns?|type|rtype|raises?)\b([^:]*):\s*(.*)')
_RE_ITEM = re.compile(r'\*{0,2}(\w+)(?:\s*\([^)]*\))?:\s*(.*)')
_RE_RETURN_TYPE = re.compile(r'[\w.\[\], |]+:\s+(.*)')

_MISSING = builtins.object()

# The names of the classes that the class hides, as its methods int, enum and object do in the lazy annotations of
# PEP 649
type _Enum = enum.Enum


class _stringmethod[S]:
    """A modifier of a string that the class has too, for a new string, as ``z.email()`` of zod."""

    def __init__(self, func: Callable[[S], S]) -> None:
        self.func = func
        self.__doc__ = func.__doc__

    def __get__(self, obj: S | None, objtype: Any = None) -> Callable[[], S]:
        def bound() -> S:
            return self.func(obj if obj is not None else objtype.string())

        bound.__doc__ = self.__doc__
        return bound


class Pyjo_JSON_Schema(Pyjo.Base.object):
    """
    :mod:`Pyjo.JSON.Schema` inherits all methods from :mod:`Pyjo.Base` and
    implements the following new ones.
    """

    _keywords: dict[str, Any] | bool
    _optional: bool
    _lazy: '_Lazy | None'
    _data: dict[str, Any] | bool | None
    _schemas: 'dict[str, Pyjo_JSON_Schema | dict[str, Any] | bool]'
    _index: '_Index | None'

    def __init__(self, data: dict[str, Any] | bool | None = None) -> None:
        """::

            schema = Pyjo.JSON.Schema.new()
            schema = Pyjo.JSON.Schema.new({'type': 'string', 'minLength': 1})

        Build new :mod:`Pyjo.JSON.Schema` object, of a schema written by hand,
        which can hold other objects of :mod:`Pyjo.JSON.Schema`, or of any value
        without arguments.
        """
        self._keywords = {} if data is None else data
        self._optional = False
        self._lazy = None
        self._data = None
        self._schemas = {}
        self._index = None

        self.name: str | None = None
        """::

            name = schema.name
            schema.name = 'Category'

        The name of the schema in ``$defs``, where it goes when a schema holds
        it more than once, as the name of its type, or ``Schema`` and a number
        without a name.
        """

    def __json__(self) -> dict[str, Any] | bool:
        """::

            data = schema.__json__()

        The schema as :mod:`Pyjo.JSON` encodes it, :attr:`data`.
        """
        return self.data

    def __repr__(self) -> str:
        return f'{type(self).__module__}.{type(self).__qualname__}({self.data!r})'

    @property
    def data(self) -> dict[str, Any] | bool:
        """::

            data = schema.data

        The schema as a :class:`dict`, with ``$defs`` for the types that are used
        more than once or refer to themselves, or ``True`` or ``False`` for a
        schema of any value or of none. ::

            # {'type': 'array', 'items': {'type': 'integer'}}
            Pyjo.JSON.Schema.of(list[int]).data
        """
        if self._data is None:
            self._data = _Emitter(self).emit()
        return self._data

    @property
    def is_optional(self) -> bool:
        """::

            boolean = schema.is_optional

        True if the schema is of a property that an object does not require, as
        :meth:`optional` and :meth:`default` make it.
        """
        return self._optional

    @property
    def is_lazy(self) -> bool:
        """::

            boolean = schema.is_lazy

        True if the schema is the one that a function gives, as :meth:`lazy`
        makes it.
        """
        return self._lazy is not None

    @property
    def keywords(self) -> dict[str, Any] | bool:
        """::

            keywords = schema.keywords

        The keywords of the schema, which can hold other objects of
        :mod:`Pyjo.JSON.Schema`, as :attr:`data` has them without them.
        """
        return self._keywords

    def resolve(self) -> 'Pyjo_JSON_Schema':
        """::

            schema = schema.resolve()

        The schema that the function of a lazy schema gives, or the schema
        itself.
        """
        return self._lazy.resolve(self) if self._lazy is not None else self

    # Types

    @classmethod
    def of(cls, tp: Any) -> Self:
        """::

            schema = Pyjo.JSON.Schema.of(list[int])
            schema = Pyjo.JSON.Schema.of(Point)

        The schema of a type of the type hints, or the schema itself, or a schema
        written by hand as a :class:`dict`. ::

            # {'type': ['string', 'null']}
            Pyjo.JSON.Schema.of(str | None).data

            # {'type': 'object', 'additionalProperties': {'type': 'number'}}
            Pyjo.JSON.Schema.of(dict[str, float]).data
        """
        return cast(Self, _Compiler(cls).compile(tp, ''))

    @classmethod
    def parameters(cls, function: Callable[..., Any], skip: int = 0) -> Self:
        """::

            schema = Pyjo.JSON.Schema.parameters(tool)
            schema = Pyjo.JSON.Schema.parameters(tool, skip=1)

        The schema of the parameters of a function, as the ``inputSchema`` of a
        tool, an ``object`` whose ``properties`` are the parameters, with the
        ones without a default ``required``, and the first paragraph of its
        docstring as its ``description``. The description of a parameter is the
        one of the field ``:param x:`` of its docstring, in reStructuredText, or
        of the section ``Args:`` of the Google Python Style Guide.

        ``skip`` leaves out the first parameters, as the context or the
        controller that a tool or an action gets before its arguments; ``self``
        of a bound method is already gone. ``**kwargs: T`` gives the
        ``additionalProperties`` of the schema of ``T``, and without it the
        object has no other properties. A parameter without an annotation is of
        any value. ``*args`` and a parameter that is only positional fail, as an
        object of JSON has no members without a name. ::

            def weather(c, city: str, days: int = 3):
                \"\"\"Forecast of the weather.

                Args:
                    city: Name of the city.
                \"\"\"

            # {'type': 'object', 'description': 'Forecast of the weather.',
            #  'properties': {'city': {'type': 'string', 'description': 'Name of the city.'},
            #                 'days': {'type': 'integer', 'default': 3}},
            #  'required': ['city'], 'additionalProperties': False}
            Pyjo.JSON.Schema.parameters(weather, skip=1).data
        """
        return cast(Self, _Compiler(cls).parameters(function, skip))

    @classmethod
    def returns(cls, function: Callable[..., Any]) -> Self | None:
        """::

            schema = Pyjo.JSON.Schema.returns(tool)

        The schema of the return value of a function, as the ``outputSchema`` of
        a tool, with the description of the field ``:returns:`` of its
        docstring, or of its section ``Returns:``, or ``None`` for a function
        without the annotation of its return value. ::

            def forecast(city: str) -> list[float]:
                \"\"\"Temperatures.

                :returns: One for each day.
                \"\"\"

            # {'type': 'array', 'items': {'type': 'number'}, 'description': 'One for each day.'}
            Pyjo.JSON.Schema.returns(forecast).data
        """
        return cast(Self | None, _Compiler(cls).returns(function))

    # Builder

    @classmethod
    def string(cls) -> Self:
        """::

            schema = z.string()

        The schema of a string. ::

            # {'type': 'string', 'minLength': 1, 'maxLength': 5}
            z.string().min(1).max(5).data
        """
        return cls({'type': 'string'})

    @classmethod
    def number(cls) -> Self:
        """::

            schema = z.number()

        The schema of a number. ::

            # {'type': 'number', 'exclusiveMinimum': 0}
            z.number().gt(0).data
        """
        return cls({'type': 'number'})

    @classmethod
    def boolean(cls) -> Self:
        """::

            schema = z.boolean()

        The schema of ``true`` or ``false``.
        """
        return cls({'type': 'boolean'})

    @classmethod
    def null(cls) -> Self:
        """::

            schema = z.null()

        The schema of ``null``.
        """
        return cls({'type': 'null'})

    @classmethod
    def literal(cls, value: Any) -> Self:
        """::

            schema = z.literal('celsius')
            schema = z.literal(['celsius', 'fahrenheit'])

        The schema of a value, as ``const``, or of one of a list of values, as
        ``enum``, with their ``type`` where they have one. ::

            # {'type': 'string', 'const': 'celsius'}
            z.literal('celsius').data
        """
        values = cast(list[Any], value) if isinstance(value, (list, tuple)) else [value]
        return cls(_literal(values))

    @classmethod
    def union(cls, options: Iterable[Any]) -> Self:
        """::

            schema = z.union([z.string(), z.int()])

        The schema of a value of one of the options, as ``anyOf``.
        """
        return cls({'anyOf': [cls.of(option) for option in options]})

    @classmethod
    def array(cls, element: Any = None) -> Self:
        """::

            schema = z.array(z.string())

        The schema of an array of elements, of any value without them. ::

            # {'type': 'array', 'items': {'type': 'string'}, 'minItems': 1}
            z.array(z.string()).nonempty().data
        """
        keywords: dict[str, Any] = {'type': 'array'}
        if element is not None:
            keywords['items'] = cls.of(element)
        return cls(keywords)

    @classmethod
    def tuple(cls, elements: Iterable[Any], rest: Any = None) -> Self:
        """::

            schema = z.tuple([z.string(), z.int()])
            schema = z.tuple([z.string()], z.int())

        The schema of an array of the elements, each of its own, and of the
        elements of ``rest`` after them, if any. zod also gives ``items: false``
        to a tuple without ``rest``, which ``maxItems`` already says. ::

            # {'type': 'array', 'prefixItems': [{'type': 'string'}, {'type': 'integer'}],
            #  'minItems': 2, 'maxItems': 2}
            z.tuple([z.string(), z.int()]).data
        """
        prefix = [cls.of(element) for element in elements]
        keywords: dict[str, Any] = {'type': 'array', 'prefixItems': prefix, 'minItems': len(prefix)}
        if rest is None:
            keywords['maxItems'] = len(prefix)
        else:
            keywords['items'] = cls.of(rest)
        return cls(keywords)

    @classmethod
    def record(cls, key: Any, value: Any = None) -> Self:
        """::

            schema = z.record(z.string(), z.int())
            schema = z.record(z.int())

        The schema of an object whose properties are all of a value, with the
        schema of their names where it is not any string. zod also gives
        ``propertyNames: {'type': 'string'}``, which every name of JSON is. ::

            # {'type': 'object', 'additionalProperties': {'type': 'integer'}}
            z.record(z.string(), z.int()).data
        """
        if value is None:
            key, value = None, key
        keywords: dict[str, Any] = {'type': 'object', 'additionalProperties': cls.of(value)}
        if key is not None:
            names = cls.of(key)
            if names._keywords != {'type': 'string'}:
                keywords['propertyNames'] = names
        return cls(keywords)

    @classmethod
    def strict_object(cls, shape: dict[str, Any] | None = None, /, **kwargs: Any) -> Self:
        """::

            schema = z.strict_object({'city': z.string()})

        The schema of an object without other properties, :meth:`object` and
        :meth:`strict`.
        """
        return cls.object(shape, **kwargs).strict()

    @classmethod
    def loose_object(cls, shape: dict[str, Any] | None = None, /, **kwargs: Any) -> Self:
        """::

            schema = z.loose_object({'city': z.string()})

        The schema of an object that allows other properties, :meth:`object` and
        :meth:`loose`.
        """
        return cls.object(shape, **kwargs).loose()

    @classmethod
    def lazy(cls, getter: Callable[[], Any]) -> Self:
        """::

            schema = z.lazy(lambda: category)

        The schema that a function gives when :attr:`data` is made, so that a
        schema can refer to itself, or to another one that is made after it. ::

            category = z.object(name=z.string(), subcategories=z.array(z.lazy(lambda: category)))

            # {'type': 'object',
            #  'properties': {'name': {'type': 'string'},
            #                 'subcategories': {'type': 'array', 'items': {'$ref': '#'}}},
            #  'required': ['name', 'subcategories']}
            category.data
        """
        schema = cls({})
        schema._lazy = _Lazy(getter)
        return schema

    # Modifiers

    def min(self, value: float) -> Self:
        """::

            schema = schema.min(1)

        The least length of a string, the least value of a number, or the least
        number of elements of an array, as ``minLength``, ``minimum`` and
        ``minItems``.
        """
        return self._constraint(_MIN, value, 'min')

    def max(self, value: float) -> Self:
        """::

            schema = schema.max(5)

        The greatest length of a string, the greatest value of a number, or the
        greatest number of elements of an array, as ``maxLength``, ``maximum``
        and ``maxItems``.
        """
        return self._constraint(_MAX, value, 'max')

    def gte(self, value: float) -> Self:
        """::

            schema = schema.gte(1)

        The same as :meth:`min`.
        """
        return self.min(value)

    def lte(self, value: float) -> Self:
        """::

            schema = schema.lte(5)

        The same as :meth:`max`.
        """
        return self.max(value)

    def length(self, value: builtins.int) -> Self:
        """::

            schema = schema.length(3)

        The length of a string, or the number of elements of an array.
        """
        return self.min(value).max(value)

    def nonempty(self) -> Self:
        """::

            schema = schema.nonempty()

        A string or an array that is not empty, :meth:`min` of 1.
        """
        return self.min(1)

    def gt(self, value: float) -> Self:
        """::

            schema = schema.gt(0)

        A number greater than the value, ``exclusiveMinimum``.
        """
        return self._number('exclusiveMinimum', value, 'gt')

    def lt(self, value: float) -> Self:
        """::

            schema = schema.lt(10)

        A number less than the value, ``exclusiveMaximum``.
        """
        return self._number('exclusiveMaximum', value, 'lt')

    def multiple_of(self, value: float) -> Self:
        """::

            schema = schema.multiple_of(2)

        A number that is a multiple of the value, ``multipleOf``.
        """
        return self._number('multipleOf', value, 'multiple_of')

    def regex(self, pattern: str | re.Pattern[str]) -> Self:
        """::

            schema = schema.regex(r'^[a-z]+$')
            schema = schema.regex(re.compile(r'^[a-z]+$'))

        A string that matches a regular expression, ``pattern``, which JSON
        Schema has in the syntax of ECMAScript.
        """
        return self._string('pattern', pattern.pattern if isinstance(pattern, re.Pattern) else pattern, 'regex')

    @_stringmethod
    def email(self) -> 'Pyjo_JSON_Schema':
        """::

            schema = z.email()
            schema = z.string().email()

        A string of the format ``email``. zod also gives the ``pattern`` of its
        own regular expression.
        """
        return self._string('format', 'email', 'email')

    @_stringmethod
    def url(self) -> 'Pyjo_JSON_Schema':
        """::

            schema = z.url()
            schema = z.string().url()

        A string of the format ``uri``.
        """
        return self._string('format', 'uri', 'url')

    @_stringmethod
    def uuid(self) -> 'Pyjo_JSON_Schema':
        """::

            schema = z.uuid()
            schema = z.string().uuid()

        A string of the format ``uuid``. zod also gives the ``pattern`` of its
        own regular expression.
        """
        return self._string('format', 'uuid', 'uuid')

    def datetime(self) -> Self:
        """::

            schema = schema.datetime()

        A string of the format ``date-time``, as ``z.iso.datetime()``. zod also
        gives the ``pattern`` of its own regular expression.
        """
        return self._string('format', 'date-time', 'datetime')

    def date(self) -> Self:
        """::

            schema = schema.date()

        A string of the format ``date``, as ``z.iso.date()``.
        """
        return self._string('format', 'date', 'date')

    def time(self) -> Self:
        """::

            schema = schema.time()

        A string of the format ``time``, as ``z.iso.time()``. zod gives only the
        ``pattern`` of its own regular expression.
        """
        return self._string('format', 'time', 'time')

    def strict(self) -> Self:
        """::

            schema = schema.strict()

        An object without other properties, ``additionalProperties: false``.
        """
        return self._object(False, 'strict')

    def loose(self) -> Self:
        """::

            schema = schema.loose()

        An object that allows other properties, ``additionalProperties: {}``.
        """
        return self._object({}, 'loose')

    def passthrough(self) -> Self:
        """::

            schema = schema.passthrough()

        The same as :meth:`loose`.
        """
        return self.loose()

    def optional(self) -> Self:
        """::

            schema = schema.optional()

        The schema of a property that an object does not require. ::

            # {'type': 'object', 'properties': {'days': {'type': 'integer'}}}
            z.object(days=z.int().optional()).data
        """
        schema = self._copy()
        schema._optional = True
        return schema

    def nullable(self) -> Self:
        """::

            schema = schema.nullable()

        The schema of the value or of ``null``, in its ``type`` where the
        schema has only a type, and in ``anyOf`` otherwise. ::

            # {'type': ['string', 'null']}
            z.string().nullable().data
        """
        schema = type(self)(_nullable(self))
        schema._optional = self._optional
        return schema

    def nullish(self) -> Self:
        """::

            schema = schema.nullish()

        :meth:`nullable` and :meth:`optional`.
        """
        return self.nullable().optional()

    def default(self, value: Any) -> Self:
        """::

            schema = schema.default(3)

        The value of a property that is not given, ``default``, which an object
        does not require, as zod has it for the input.
        """
        return self.meta(default=value).optional()

    def describe(self, description: str) -> Self:
        """::

            schema = schema.describe('Name of the city')

        The description of the value, ``description``.
        """
        return self.meta(description=description)

    def meta(self, keywords: dict[str, Any] | None = None, /, **kwargs: Any) -> Self:
        """::

            schema = schema.meta({'$schema': Pyjo.JSON.Schema.DIALECT})
            schema = schema.meta(title='City', examples=['Warsaw'])

        Other keywords of the schema. zod keeps them as the metadata of the
        schema too.
        """
        schema = self._copy()
        schema._keywords = {**cast(dict[str, Any], schema._keywords), **(keywords or {}), **kwargs}
        return schema

    # Validation

    def add_schema(self, schema: 'Pyjo_JSON_Schema | dict[str, Any] | bool', uri: str | None = None) -> Self:
        """::

            schema = schema.add_schema({'$id': 'https://example.com/address', 'type': 'object'})
            schema = schema.add_schema(z.string(), 'https://example.com/name')

        Add a schema to the registry of the schema, under its ``$id`` or the
        URI, where a ``$ref`` of the schema finds it, and its ``$id`` and
        ``$anchor`` too.
        """
        if uri is None:
            data = schema.data if isinstance(schema, Pyjo_JSON_Schema) else schema
            uri = data.get('$id') if isinstance(data, dict) else None
            if not isinstance(uri, str):
                raise Pyjo.Exception.new('JSON Schema has no $id of the schema to add')
        self._schemas[_uri('', uri)[0]] = schema
        self._index = None
        return self

    def parse(self, value: Any, formats: bool = False) -> Any:
        """::

            value = schema.parse({'city': 'Warsaw'})

        The value, if the schema validates it, as :meth:`validate` does, or a
        :mod:`Pyjo.Exception` with the errors, one in each line.
        """
        result = self.validate(value, formats)
        if not result:
            raise Pyjo.Exception.new(str(result))
        return value

    def validate(self, value: Any, formats: bool = False) -> 'Result':
        """::

            result = schema.validate({'city': 'Warsaw'})
            result = schema.validate({'date': '2026-10-23'}, formats=True)

        Validate a value, as :mod:`Pyjo.JSON` decodes it, and return a
        :class:`Result`, which is true if the value is valid, with the
        :class:`Error` objects of the value otherwise. ``format`` is an
        annotation, as JSON Schema has it by default, and an assertion with
        ``formats``. ::

            # "/days: Expected integer - got string."
            str(z.object(days=z.int()).validate({'days': 'three'}))
        """
        if self._index is None:
            self._index = _Index(self.data, self._schemas)
        return Result(_Validator(self._index, formats).validate(value))

    # Internals

    def _copy(self) -> Self:
        if isinstance(self._keywords, bool):
            raise Pyjo.Exception.new(f'JSON Schema {self._keywords} has no keywords')
        schema = type(self)(dict(self._keywords))
        schema._optional = self._optional
        schema._lazy = self._lazy
        schema._schemas = dict(self._schemas)
        return schema

    def _types(self) -> list[str]:
        types = self._keywords.get('type') if isinstance(self._keywords, dict) else None
        return [types] if isinstance(types, str) else [t for t in cast(list[str], types or []) if t != 'null']

    def _constraint(self, keywords: dict[str, str], value: float, method: str) -> Self:
        for t in self._types():
            if t in keywords:
                return self.meta({keywords[t]: value})
        raise Pyjo.Exception.new(f'JSON Schema has no {method} for {self._kind()}')

    def _number(self, keyword: str, value: float, method: str) -> Self:
        if not {'number', 'integer'} & set(self._types()):
            raise Pyjo.Exception.new(f'JSON Schema has no {method} for {self._kind()}')
        return self.meta({keyword: value})

    def _string(self, keyword: str, value: str, method: str) -> Self:
        if 'string' not in self._types():
            raise Pyjo.Exception.new(f'JSON Schema has no {method} for {self._kind()}')
        return self.meta({keyword: value})

    def _object(self, additional: Any, method: str) -> Self:
        if 'object' not in self._types():
            raise Pyjo.Exception.new(f'JSON Schema has no {method} for {self._kind()}')
        return self.meta(additionalProperties=additional)

    def _kind(self) -> str:
        types = self._types()
        return f'the type {types[0]}' if types else 'a schema without a type'

    # The names of builtins, last, as they hide them in the class

    @classmethod
    def any(cls) -> Self:
        """::

            schema = z.any()

        The schema of any value, ``{}``.
        """
        return cls({})

    @classmethod
    def int(cls) -> Self:
        """::

            schema = z.int()

        The schema of an integer. zod also gives the least and the greatest
        safe integer of JavaScript as its ``minimum`` and ``maximum``, which an
        integer of Python does not have. ::

            # {'type': 'integer', 'minimum': 1, 'maximum': 7}
            z.int().min(1).max(7).data
        """
        return cls({'type': 'integer'})

    @classmethod
    def enum(cls, values: Iterable[Any] | type[_Enum]) -> Self:
        """::

            schema = z.enum(['celsius', 'fahrenheit'])
            schema = z.enum(Unit)

        The schema of one of the values, or of the values of an
        :class:`enum.Enum`, as ``enum``, with their ``type`` where they have
        one. ::

            # {'type': 'string', 'enum': ['celsius', 'fahrenheit']}
            z.enum(['celsius', 'fahrenheit']).data
        """
        if isinstance(values, type):
            return cls(_literal([member.value for member in values], True))
        return cls(_literal(builtins.list(values), True))

    @classmethod
    def object(cls, shape: dict[str, Any] | None = None, /, **kwargs: Any) -> Self:
        """::

            schema = z.object({'city': z.string(), 'days': z.int().optional()})
            schema = z.object(city=z.string(), days=z.int().optional())

        The schema of an object of the properties, which it requires, but the
        optional ones, as :meth:`optional` and :meth:`default` make them. A
        name that is a keyword of Python, or not a name of Python, goes in the
        :class:`dict`. zod also gives ``additionalProperties: false`` for the
        output, and this is the schema of the input, which a tool gets. ::

            # {'type': 'object', 'properties': {'class': {'type': 'string'}}, 'required': ['class']}
            z.object({'class': z.string()}).data
        """
        properties = {name: cls.of(value) for name, value in {**(shape or {}), **kwargs}.items()}
        keywords: dict[str, Any] = {'type': 'object', 'properties': properties}
        required = [name for name, value in properties.items() if not value._optional]
        if required:
            keywords['required'] = required
        return cls(keywords)

    iso: '_ISO'
    """::

        schema = z.iso.datetime()
        schema = z.iso.date()
        schema = z.iso.time()

    The schemas of the strings of the formats ``date-time``, ``date`` and
    ``time``, as :meth:`datetime`, :meth:`date` and :meth:`time` of a string.
    """


class Error(Pyjo.Base.object):
    """
    An error of a value, which :meth:`~Pyjo_JSON_Schema.validate` gives, with
    where it is in the value and in the schema. ::

        # "/days: Expected integer - got string."
        str(error)
    """

    def __init__(self, path: str = '', keyword_path: str = '', message: str = '') -> None:
        self.path = path
        """::

            path = error.path

        The JSON Pointer of the value in the validated value, as
        :mod:`Pyjo.JSON.Pointer` takes it, or of the missing property of
        ``required``.
        """

        self.keyword_path = keyword_path
        """::

            keyword_path = error.keyword_path

        The JSON Pointer of the keyword in the schema, through the ``$ref``
        that the validation follows, as ``/properties/days/type``.
        """

        self.message = message
        """::

            message = error.message

        What is wrong with the value.
        """

        self._expected: list[str] | None = None

    def __json__(self) -> dict[str, str]:
        """::

            data = error.__json__()

        The error as :mod:`Pyjo.JSON` encodes it, with ``path``,
        ``keyword_path`` and ``message``.
        """
        return {'path': self.path, 'keyword_path': self.keyword_path, 'message': self.message}

    def __repr__(self) -> str:
        return f'{type(self).__module__}.{type(self).__qualname__}({self.__json__()!r})'

    def __str__(self) -> str:
        """::

            string = str(error)

        The path, with ``/`` for the whole value, and the message.
        """
        return f'{self.path or "/"}: {self.message}'


class Result:
    """
    The result of :meth:`~Pyjo_JSON_Schema.validate`, which is true if the
    value is valid, as the assertions of :mod:`Pyjo.Test` are. ::

        result = schema.validate(value)
        if not result:
            for error in result.errors:
                print(error.path, error.message)
    """

    def __init__(self, errors: Iterable[Error] = ()) -> None:
        self.errors: Pyjo.Collection.object[Error] = Pyjo.Collection.new(*errors)
        """::

            errors = result.errors

        The :class:`Error` objects of the value, in a :mod:`Pyjo.Collection`,
        empty if the value is valid.
        """

    def __bool__(self) -> bool:
        """::

            boolean = bool(result)

        The value of :attr:`is_valid`.
        """
        return self.is_valid

    def __json__(self) -> dict[str, Any]:
        """::

            data = result.__json__()

        The result as :mod:`Pyjo.JSON` encodes it, ``valid`` and the ``errors``.
        """
        return {'valid': self.is_valid, 'errors': [error.__json__() for error in self.errors]}

    def __repr__(self) -> str:
        return f'<{type(self).__module__}.{type(self).__qualname__} is_valid={self.is_valid}>'

    def __str__(self) -> str:
        """::

            string = str(result)

        The errors, one in each line, or an empty string if the value is
        valid.
        """
        return '\n'.join(str(error) for error in self.errors)

    @property
    def is_valid(self) -> bool:
        """::

            boolean = result.is_valid

        True if the value is valid, without errors.
        """
        return not len(self.errors)


class _Lazy:
    """The function of a lazy schema, and the schema that it gives, which the copies of the lazy schema share, so that
    they refer to the same schema."""

    def __init__(self, getter: Callable[[], Any]) -> None:
        self.getter = getter
        self.target: Pyjo_JSON_Schema | None = None

    def resolve(self, schema: Pyjo_JSON_Schema) -> Pyjo_JSON_Schema:
        if self.target is None:
            self.target = schema.of(self.getter())
        return self.target


class _ISO:
    def __get__(self, obj: Anything, objtype: type[Pyjo_JSON_Schema]) -> Self:
        self._cls = objtype
        return self

    def datetime(self) -> Pyjo_JSON_Schema:
        return self._cls.string().datetime()

    def date(self) -> Pyjo_JSON_Schema:
        return self._cls.string().date()

    def time(self) -> Pyjo_JSON_Schema:
        return self._cls.string().time()


Pyjo_JSON_Schema.iso = _ISO()


class _Compiler:
    """The schemas of the types of the type hints, the same object for the same type in one schema."""

    def __init__(self, cls: type[Pyjo_JSON_Schema]) -> None:
        self.cls = cls
        self.done: dict[Any, Pyjo_JSON_Schema] = {}
        self.doing: set[Any] = set()

    def parameters(self, function: Callable[..., Any], skip: int) -> Pyjo_JSON_Schema:
        signature, hints = _signature(function)
        description, params, _ = _docstring(function)
        properties: dict[str, Pyjo_JSON_Schema] = {}
        required: list[str] = []
        additional: Any = False
        for param in builtins.list(signature.parameters.values())[skip:]:
            where = f' in the parameter {param.name}'
            if param.kind is param.VAR_POSITIONAL:
                raise Pyjo.Exception.new(f'JSON Schema has no positional members for the parameter {param.name}')
            if param.kind is param.POSITIONAL_ONLY:
                raise Pyjo.Exception.new(f'JSON Schema has no positional members for the parameter {param.name}')
            schema = self.compile(hints.get(param.name, Any), where)
            if param.kind is param.VAR_KEYWORD:
                additional = schema
                continue
            if param.name in params:
                schema = schema.describe(params[param.name])
            if param.default is param.empty:
                required.append(param.name)
            elif (value := _json_value(param.default)) is not _MISSING:
                schema = schema.meta(default=value)
            properties[param.name] = schema
        keywords: dict[str, Any] = {'type': 'object'}
        if description:
            keywords['description'] = description
        keywords['properties'] = properties
        if required:
            keywords['required'] = required
        keywords['additionalProperties'] = additional
        return self.cls(keywords)

    def returns(self, function: Callable[..., Any]) -> Pyjo_JSON_Schema | None:
        _, hints = _signature(function)
        if 'return' not in hints:
            return None
        schema = self.compile(hints['return'], ' in the return value')
        _, _, description = _docstring(function)
        return schema.describe(description) if description else schema

    def compile(self, tp: Any, where: str) -> Pyjo_JSON_Schema:
        cls = self.cls
        if isinstance(tp, Pyjo_JSON_Schema):
            return tp
        if isinstance(tp, (dict, bool)):
            return cls.new(cast(dict[str, Any] | bool, tp))
        if tp is None or tp is type(None):
            return cls.null()
        if tp is Any or tp is builtins.object:
            return cls.any()
        if tp is bool:
            return cls.boolean()
        if tp is builtins.int:
            return cls.int()
        if tp is float:
            return cls.number()
        if tp is str:
            return cls.string()
        if isinstance(tp, type) and tp in _FORMATS:
            return cls.string().meta(format=_FORMATS[tp])
        if isinstance(tp, type) and issubclass(tp, Pyjo.URL.object):
            return cls.string().url()

        origin, args = typing.get_origin(tp), typing.get_args(tp)
        if origin is typing.Annotated:
            return self.annotated(args[0], args[1:], where)
        if origin in (typing.Union, types.UnionType):
            return self.union(args, where)
        if origin is typing.Literal:
            return cls(_literal(builtins.list(args)))
        if origin is not None and origin in _QUALIFIERS:
            return self.compile(args[0], where)
        if tp in (list, set, frozenset, builtins.tuple) or origin in (list, set, frozenset):
            schema = cls.array(self.compile(args[0], where) if args else None)
            return schema.meta(uniqueItems=True) if set in (tp, origin) or frozenset in (tp, origin) else schema
        if origin is builtins.tuple:
            if len(args) == 2 and args[1] is Ellipsis:
                return cls.array(self.compile(args[0], where))
            return cls.tuple([self.compile(arg, where) for arg in args if arg != ()])
        if tp is dict:
            return cls({'type': 'object'})
        if origin is dict:
            if args[0] is not str:
                raise Pyjo.Exception.new(f'JSON Schema has no names of {_name(args[0])}{where}')
            return cls.record(self.compile(args[1], where))
        if isinstance(tp, typing.TypeAliasType):
            return self.named(tp, where, lambda: self.compile(tp.__value__, where))
        if isinstance(tp, typing.NewType):
            return self.compile(tp.__supertype__, where)
        if isinstance(tp, type) and issubclass(tp, enum.Enum):
            return self.named(tp, where, lambda: self.enumeration(tp))
        if typing.is_typeddict(cast(Any, tp)):
            return self.named(tp, where, lambda: self.typeddict(tp, where))
        if isinstance(tp, type) and dataclasses.is_dataclass(tp):
            return self.named(tp, where, lambda: self.dataclass(tp, where))
        raise Pyjo.Exception.new(f'JSON Schema does not support {_name(tp)}{where}')

    def named(self, tp: Any, where: str, make: Callable[[], Pyjo_JSON_Schema]) -> Pyjo_JSON_Schema:
        # A type that is in the making refers to itself, the same type again is the same object, which goes to $defs
        if tp in self.done:
            return self.done[tp]
        if tp in self.doing:
            return self.cls.lazy(lambda: self.done[tp])
        self.doing.add(tp)
        try:
            schema = make()
        finally:
            self.doing.discard(tp)
        schema.name = tp.__name__
        self.done[tp] = schema
        return schema

    def annotated(self, tp: Any, metadata: tuple[Any, ...], where: str) -> Pyjo_JSON_Schema:
        keywords: dict[str, Any] = {}
        for value in metadata:
            if isinstance(value, str):
                keywords['description'] = value
            elif isinstance(value, dict):
                keywords.update(cast(dict[str, Any], value))
            elif isinstance(value, Pyjo_JSON_Schema) and isinstance(value.keywords, dict):
                keywords.update(value.keywords)
        schema = self.compile(tp, where)
        return schema.meta(keywords) if keywords else schema

    def union(self, args: tuple[Any, ...], where: str) -> Pyjo_JSON_Schema:
        options = [arg for arg in args if arg is not None and arg is not type(None)]
        schemas = [self.compile(arg, where) for arg in options]
        if len(schemas) == 1:
            return schemas[0].nullable() if len(options) < len(args) else schemas[0]
        if len(options) < len(args):
            schemas.append(self.cls.null())
        return self.cls({'anyOf': schemas})

    def enumeration(self, tp: type[enum.Enum]) -> Pyjo_JSON_Schema:
        schema = self.cls.enum(tp)
        description = _description(tp)
        return schema.describe(description) if description else schema

    def typeddict(self, tp: Any, where: str) -> Pyjo_JSON_Schema:
        hints = _hints(tp, f' of {_name(tp)}')
        required = cast(frozenset[str], tp.__required_keys__)
        properties = {name: self.compile(hint, f' in the key {name} of {_name(tp)}') for name, hint in hints.items()}
        keywords = self.object(tp, properties, [name for name in hints if name in required])
        if getattr(tp, '__closed__', None):
            keywords['additionalProperties'] = False
        extra = getattr(tp, '__extra_items__', None)
        if extra is not None and getattr(extra, '__name__', None) != 'NoExtraItems':
            keywords['additionalProperties'] = self.compile(extra, f' in the extra items of {_name(tp)}')
        return self.cls(keywords)

    def dataclass(self, tp: type[Any], where: str) -> Pyjo_JSON_Schema:
        hints = _hints(tp, f' of {_name(tp)}')
        properties: dict[str, Pyjo_JSON_Schema] = {}
        required: list[str] = []
        for field in dataclasses.fields(tp):
            if not field.init:
                continue
            schema = self.compile(hints.get(field.name, Any), f' in the field {field.name} of {_name(tp)}')
            if field.default is dataclasses.MISSING and field.default_factory is dataclasses.MISSING:
                required.append(field.name)
            elif (value := _json_value(field.default)) is not _MISSING:
                schema = schema.meta(default=value)
            properties[field.name] = schema
        return self.cls(self.object(tp, properties, required))

    def object(self, tp: Any, properties: dict[str, Pyjo_JSON_Schema], required: list[str]) -> dict[str, Any]:
        keywords: dict[str, Any] = {'type': 'object'}
        description = _description(tp)
        if description:
            keywords['description'] = description
        keywords['properties'] = properties
        if required:
            keywords['required'] = required
        return keywords


class _Emitter:
    """The data of a schema, with $defs for the named schemas used again and the ones that refer to themselves."""

    def __init__(self, root: Pyjo_JSON_Schema) -> None:
        self.root = root
        self.targets: dict[builtins.int, Pyjo_JSON_Schema] = {}
        self.counts: collections.Counter[builtins.int] = collections.Counter()
        self.recursive: set[builtins.int] = set()
        self.needed: set[builtins.int] = set()
        self.names: dict[builtins.int, str] = {}
        self.defs: dict[str, Any] = {}

    def emit(self) -> dict[str, Any] | bool:
        root = self.resolve(self.root)
        self.count(root, [])
        self.needed = self.recursive | {
            key for key, count in self.counts.items() if count > 1 and self.targets[key].name is not None
        }
        self.needed.discard(id(root))
        data = self.keywords(root)
        if self.root is not root:
            data = self.merge(data, self.keywords(self.root))
        if self.defs and isinstance(data, dict):
            data['$defs'] = self.defs
        return data

    def resolve(self, schema: Pyjo_JSON_Schema) -> Pyjo_JSON_Schema:
        seen: set[builtins.int] = set()
        target = schema
        while target.is_lazy:
            if id(target) in seen:
                raise Pyjo.Exception.new('JSON Schema of a lazy schema that gives itself')
            seen.add(id(target))
            target = target.resolve()
        self.targets[id(target)] = target
        return target

    def count(self, value: Any, stack: list[builtins.int]) -> None:
        if isinstance(value, Pyjo_JSON_Schema):
            target = self.resolve(value)
            key = id(target)
            if key in stack:
                self.recursive.add(key)
                return
            self.counts[key] += 1
            if self.counts[key] == 1:
                stack.append(key)
                self.count(target.keywords, stack)
                stack.pop()
        elif isinstance(value, dict):
            for item in cast(dict[str, Any], value).values():
                self.count(item, stack)
        elif isinstance(value, (list, builtins.tuple)):
            for item in cast(list[Any], value):
                self.count(item, stack)

    def value(self, value: Any) -> Any:
        if isinstance(value, Pyjo_JSON_Schema):
            target = self.resolve(value)
            key = id(target)
            own = self.keywords(value) if value is not target else {}
            if key == id(self.resolve(self.root)):
                return self.merge({'$ref': '#'}, own)
            if key in self.needed:
                return self.merge({'$ref': f'#/$defs/{self.define(target)}'}, own)
            return self.merge(self.keywords(target), own)
        if isinstance(value, dict):
            return {name: self.value(item) for name, item in cast(dict[str, Any], value).items()}
        if isinstance(value, (list, builtins.tuple)):
            return [self.value(item) for item in cast(list[Any], value)]
        return value

    def keywords(self, schema: Pyjo_JSON_Schema) -> dict[str, Any] | bool:
        if isinstance(schema.keywords, bool):
            return schema.keywords
        return {name: self.value(item) for name, item in schema.keywords.items()}

    def define(self, target: Pyjo_JSON_Schema) -> str:
        key = id(target)
        if key not in self.names:
            base = target.name or 'Schema'
            name, n = base, 1
            while name in self.defs or name in self.names.values():
                n += 1
                name = f'{base}{n}'
            self.names[key] = name
            self.defs[name] = {}
            self.defs[name] = self.keywords(target)
        return self.names[key]

    def merge(self, data: dict[str, Any] | bool, own: dict[str, Any] | bool) -> dict[str, Any] | bool:
        if isinstance(own, bool) or not own:
            return data
        if isinstance(data, bool):
            return own if data else {**own, 'not': {}}
        return {**data, **own}


class _Index:
    """The schemas by their URI, of $id, $anchor and the registry, with the base URI of each schema."""

    def __init__(
        self, root: dict[str, Any] | bool, schemas: dict[str, Pyjo_JSON_Schema | dict[str, Any] | bool]
    ) -> None:
        self.resources: dict[str, dict[str, Any] | bool] = {}
        self.anchors: dict[str, dict[str, Any]] = {}
        self.bases: dict[builtins.int, str] = {}
        self.schemas = dict(schemas)
        self.keep: list[Any] = []
        self.patterns: dict[str, re.Pattern[str]] = {}
        self.root = root
        self.add(root, '')

    def add(self, schema: Pyjo_JSON_Schema | dict[str, Any] | bool, uri: str) -> None:
        data = schema.data if isinstance(schema, Pyjo_JSON_Schema) else schema
        # The ids of the schemas are the keys of the bases, so the schemas stay
        self.keep.append(data)
        self.resources[uri] = data
        self.walk(data, uri, '')

    def walk(self, schema: Any, base: str, where: str) -> None:
        if isinstance(schema, bool):
            return
        if not isinstance(schema, dict):
            raise Pyjo.Exception.new(f'JSON Schema has no schema in {where or "/"}')
        schema = cast(dict[str, Any], schema)
        dialect = schema.get('$schema')
        if dialect is not None and (not isinstance(dialect, str) or dialect.rstrip('#') != DIALECT):
            raise Pyjo.Exception.new(f'JSON Schema does not support the dialect {dialect}')
        for keyword in _UNSUPPORTED:
            if keyword in schema:
                raise Pyjo.Exception.new(f'JSON Schema does not support {keyword} in {where or "/"}')
        if isinstance(schema.get('$id'), str):
            base = _uri(base, schema['$id'])[0]
            self.resources.setdefault(base, schema)
        for keyword in ('$anchor', '$dynamicAnchor'):
            if isinstance(schema.get(keyword), str):
                self.anchors[f'{base}#{schema[keyword]}'] = schema
        self.bases[id(schema)] = base
        for keyword, value in schema.items():
            if keyword in _SCHEMA:
                self.walk(value, base, f'{where}/{keyword}')
            elif keyword in _SCHEMAS and isinstance(value, dict):
                for name, item in cast(dict[str, Any], value).items():
                    self.walk(item, base, f'{where}/{keyword}/{_escape(name)}')
            elif keyword in _SCHEMA_LISTS and isinstance(value, list):
                for i, item in enumerate(cast(list[Any], value)):
                    self.walk(item, base, f'{where}/{keyword}/{i}')
            elif keyword in _SCHEMAS or keyword in _SCHEMA_LISTS:
                raise Pyjo.Exception.new(f'JSON Schema has no schemas in {where}/{keyword}')

    def pattern(self, source: str) -> re.Pattern[str]:
        # The regular expressions of the schemas, which are compiled once for the schema
        pattern = self.patterns.get(source)
        if pattern is None:
            pattern = self.patterns[source] = _regex(source)
        return pattern

    def resolve(self, base: str, ref: str, where: str) -> tuple[dict[str, Any] | bool, str]:
        uri, fragment = _uri(base, ref)
        if uri not in self.resources and uri in self.schemas:
            self.add(self.schemas.pop(uri), uri)
        if uri not in self.resources:
            # An embedded resource of a schema of the registry, which has to be indexed to be found, of the schemas
            # that the validation supports
            while self.schemas:
                key, schema = self.schemas.popitem()
                with contextlib.suppress(Pyjo.Exception.object):
                    self.add(schema, key)
        target: Any = None
        if fragment.startswith('/') or not fragment:
            pointer = Pyjo.JSON.Pointer.new(self.resources.get(uri))
            if uri in self.resources and pointer.contains(fragment):
                target = pointer.get(fragment)
        else:
            target = self.anchors.get(f'{uri}#{fragment}')
        if not isinstance(target, (dict, bool)):
            raise Pyjo.Exception.new(f'JSON Schema has no schema of the $ref {ref} in {where}')
        found = cast(dict[str, Any] | bool, target)
        return found, self.bases.get(id(found), uri)


@dataclasses.dataclass(slots=True)
class _At:
    """A value and a schema whose keywords validate it, with the JSON Pointers of the value and of the keyword."""

    value: Any
    kind: str
    schema: dict[str, Any]
    base: str
    path: str
    where: str
    errors: list[Error]

    def error(self, message: str, path: str | None = None, where: str | None = None) -> Error:
        error = Error(self.path if path is None else path, self.where if where is None else where, message)
        self.errors.append(error)
        return error

    def child(self, name: Any) -> str:
        return f'{self.path}/{_escape(name)}'


class _Validator:
    """The evaluation of a value against a schema, which collects the errors."""

    def __init__(self, index: _Index, formats: bool) -> None:
        self.index = index
        self.formats = formats
        self.stack: set[tuple[builtins.int, str]] = set()

    def validate(self, value: Any) -> list[Error]:
        errors: list[Error] = []
        _json_errors(value, '', errors)
        if not errors:
            self.evaluate(value, self.index.root, '', '', '', errors)
        return errors

    def evaluate(
        self, value: Any, schema: dict[str, Any] | bool, base: str, path: str, where: str, errors: list[Error]
    ) -> None:
        if schema is True:
            return
        if schema is False:
            errors.append(Error(path, where, 'Not allowed.'))
            return
        key = (id(schema), path)
        if key in self.stack:
            raise Pyjo.Exception.new(f'JSON Schema refers to itself in {where} without a value of its own')
        self.stack.add(key)
        try:
            at = _At(value, _instance_type(value), schema, self.index.bases.get(id(schema), base), path, where, errors)
            for keyword, argument in schema.items():
                check = _KEYWORDS.get(keyword)
                if check is not None:
                    at.where = f'{where}/{keyword}'
                    check(self, at, argument)
        finally:
            self.stack.discard(key)

    def errors(
        self, value: Any, schema: Any, at: _At, path: str | None = None, where: str | None = None
    ) -> list[Error]:
        errors: list[Error] = []
        self.evaluate(
            value, schema, at.base, at.path if path is None else path, at.where if where is None else where, errors
        )
        return errors

    def apply(self, value: Any, schema: Any, at: _At, path: str | None = None, where: str | None = None) -> None:
        self.evaluate(
            value, schema, at.base, at.path if path is None else path, at.where if where is None else where, at.errors
        )

    # Types

    def type(self, at: _At, argument: Any) -> None:
        types = [argument] if isinstance(argument, str) else cast(list[str], argument)
        if at.kind not in types and not (at.kind == 'integer' and 'number' in types):
            error = at.error(f'Expected {" or ".join(types)} - got {_type_name(at.value)}.')
            error._expected = types  # pyright: ignore[reportPrivateUsage]

    def enum(self, at: _At, argument: Any) -> None:
        if _canonical(at.value) not in [_canonical(item) for item in cast(list[Any], argument)]:
            at.error(f'Not in enum: {", ".join(to_json(item) for item in argument)}.')

    def const(self, at: _At, argument: Any) -> None:
        if _canonical(at.value) != _canonical(argument):
            at.error(f'Not the const: {to_json(argument)}.')

    # Numbers

    def minimum(self, at: _At, argument: Any) -> None:
        if at.kind in _NUMBERS and at.value < argument:
            at.error(f'Less than the minimum {to_json(argument)}.')

    def maximum(self, at: _At, argument: Any) -> None:
        if at.kind in _NUMBERS and at.value > argument:
            at.error(f'Greater than the maximum {to_json(argument)}.')

    def exclusive_minimum(self, at: _At, argument: Any) -> None:
        if at.kind in _NUMBERS and at.value <= argument:
            at.error(f'Not greater than the exclusive minimum {to_json(argument)}.')

    def exclusive_maximum(self, at: _At, argument: Any) -> None:
        if at.kind in _NUMBERS and at.value >= argument:
            at.error(f'Not less than the exclusive maximum {to_json(argument)}.')

    def multiple_of(self, at: _At, argument: Any) -> None:
        if at.kind in _NUMBERS and (_fraction(at.value) / _fraction(argument)).denominator != 1:
            at.error(f'Not a multiple of {to_json(argument)}.')

    # Strings

    def min_length(self, at: _At, argument: Any) -> None:
        if at.kind == 'string' and len(at.value) < argument:
            at.error(f'Shorter than {to_json(argument)} characters.')

    def max_length(self, at: _At, argument: Any) -> None:
        if at.kind == 'string' and len(at.value) > argument:
            at.error(f'Longer than {to_json(argument)} characters.')

    def pattern(self, at: _At, argument: Any) -> None:
        if at.kind == 'string' and not self.index.pattern(argument).search(at.value):
            at.error(f'Does not match the pattern {argument}.')

    def format(self, at: _At, argument: Any) -> None:
        check = _FORMAT_CHECKS.get(argument)
        if self.formats and at.kind == 'string' and check is not None and not check(at.value):
            at.error(f'Does not match the format {argument}.')

    # Arrays

    def items(self, at: _At, argument: Any) -> None:
        if at.kind == 'array':
            start = len(cast(list[Any], at.schema.get('prefixItems', [])))
            for i, item in enumerate(at.value[start:], start):
                self.apply(item, argument, at, at.child(i))

    def prefix_items(self, at: _At, argument: Any) -> None:
        if at.kind == 'array':
            for i, (item, schema) in enumerate(zip(at.value, argument, strict=False)):
                self.apply(item, schema, at, at.child(i), f'{at.where}/{i}')

    def min_items(self, at: _At, argument: Any) -> None:
        if at.kind == 'array' and len(at.value) < argument:
            at.error(f'Fewer than {to_json(argument)} items.')

    def max_items(self, at: _At, argument: Any) -> None:
        if at.kind == 'array' and len(at.value) > argument:
            at.error(f'More than {to_json(argument)} items.')

    def unique_items(self, at: _At, argument: Any) -> None:
        if at.kind == 'array' and argument is True:
            seen: dict[Any, builtins.int] = {}
            for i, item in enumerate(at.value):
                first = seen.setdefault(_canonical(item), i)
                if first != i:
                    at.error(f'Items {first} and {i} are equal.')
                    return

    def contains(self, at: _At, argument: Any) -> None:
        if at.kind != 'array':
            return
        count = sum(not self.errors(item, argument, at, at.child(i)) for i, item in enumerate(at.value))
        least, most = at.schema.get('minContains', 1), at.schema.get('maxContains')
        parent = at.where.rpartition('/')[0]
        if count < least and 'minContains' in at.schema:
            at.error(f'Fewer than {to_json(least)} items match the schema of contains.', where=f'{parent}/minContains')
        elif count < least:
            at.error('No item matches the schema of contains.')
        if most is not None and count > most:
            at.error(f'More than {to_json(most)} items match the schema of contains.', where=f'{parent}/maxContains')

    # Objects

    def properties(self, at: _At, argument: Any) -> None:
        if at.kind == 'object':
            for name, schema in cast(dict[str, Any], argument).items():
                if name in at.value:
                    self.apply(at.value[name], schema, at, at.child(name), f'{at.where}/{_escape(name)}')

    def pattern_properties(self, at: _At, argument: Any) -> None:
        if at.kind == 'object':
            for pattern, schema in cast(dict[str, Any], argument).items():
                for name, item in cast(dict[str, Any], at.value).items():
                    if self.index.pattern(pattern).search(name):
                        self.apply(item, schema, at, at.child(name), f'{at.where}/{_escape(pattern)}')

    def additional_properties(self, at: _At, argument: Any) -> None:
        if at.kind != 'object':
            return
        properties = cast(dict[str, Any], at.schema.get('properties', {}))
        patterns = [
            self.index.pattern(pattern) for pattern in cast(dict[str, Any], at.schema.get('patternProperties', {}))
        ]
        for name, item in cast(dict[str, Any], at.value).items():
            if name in properties or any(pattern.search(name) for pattern in patterns):
                continue
            if argument is False:
                at.error('Property not allowed.', at.child(name))
            else:
                self.apply(item, argument, at, at.child(name))

    def property_names(self, at: _At, argument: Any) -> None:
        if at.kind == 'object':
            for name in at.value:
                self.apply(name, argument, at, at.child(name))

    def required(self, at: _At, argument: Any) -> None:
        if at.kind == 'object':
            for name in cast(list[str], argument):
                if name not in at.value:
                    at.error('Missing property.', at.child(name))

    def min_properties(self, at: _At, argument: Any) -> None:
        if at.kind == 'object' and len(at.value) < argument:
            at.error(f'Fewer than {to_json(argument)} properties.')

    def max_properties(self, at: _At, argument: Any) -> None:
        if at.kind == 'object' and len(at.value) > argument:
            at.error(f'More than {to_json(argument)} properties.')

    def dependent_required(self, at: _At, argument: Any) -> None:
        if at.kind == 'object':
            for name, names in cast(dict[str, list[str]], argument).items():
                for required in names if name in at.value else []:
                    if required not in at.value:
                        message = f'Missing property, which {to_json(name)} requires.'
                        at.error(message, at.child(required), f'{at.where}/{_escape(name)}')

    def dependent_schemas(self, at: _At, argument: Any) -> None:
        if at.kind == 'object':
            for name, schema in cast(dict[str, Any], argument).items():
                if name in at.value:
                    self.apply(at.value, schema, at, where=f'{at.where}/{_escape(name)}')

    # Combinations

    def all_of(self, at: _At, argument: Any) -> None:
        for i, schema in enumerate(cast(list[Any], argument)):
            self.apply(at.value, schema, at, where=f'{at.where}/{i}')

    def any_of(self, at: _At, argument: Any) -> None:
        failures: list[list[Error]] = []
        for i, schema in enumerate(cast(list[Any], argument)):
            failure = self.errors(at.value, schema, at, where=f'{at.where}/{i}')
            if not failure:
                return
            failures.append(failure)
        at.errors.extend(_mismatch(at, failures))

    def one_of(self, at: _At, argument: Any) -> None:
        failures: list[list[Error]] = []
        valid: list[str] = []
        for i, schema in enumerate(cast(list[Any], argument)):
            failure = self.errors(at.value, schema, at, where=f'{at.where}/{i}')
            if failure:
                failures.append(failure)
            else:
                valid.append(str(i))
        if len(valid) > 1:
            at.error(f'Matches more than one schema of oneOf: {", ".join(valid)}.')
        elif not valid:
            at.errors.extend(_mismatch(at, failures))

    def not_(self, at: _At, argument: Any) -> None:
        if not self.errors(at.value, argument, at):
            at.error('Matches the schema of not.')

    def if_(self, at: _At, argument: Any) -> None:
        keyword = 'else' if self.errors(at.value, argument, at) else 'then'
        if keyword in at.schema:
            self.apply(at.value, at.schema[keyword], at, where=f'{at.where.rpartition("/")[0]}/{keyword}')

    # References

    def ref(self, at: _At, argument: Any) -> None:
        target, base = self.index.resolve(at.base, argument, at.where)
        self.evaluate(at.value, target, base, at.path, at.where, at.errors)

    def unsupported(self, at: _At, argument: Any) -> None:
        raise Pyjo.Exception.new(f'JSON Schema does not support {at.where.rpartition("/")[2]} in {at.where}')


type _Check = Callable[[_Validator, _At, Any], None]

# The keywords of the validation, and the ones of 2020-12 that it does not support, which a schema refers to through
# a $ref of a JSON Pointer too
_KEYWORDS: dict[str, _Check] = {
    'type': _Validator.type,
    'enum': _Validator.enum,
    'const': _Validator.const,
    'minimum': _Validator.minimum,
    'maximum': _Validator.maximum,
    'exclusiveMinimum': _Validator.exclusive_minimum,
    'exclusiveMaximum': _Validator.exclusive_maximum,
    'multipleOf': _Validator.multiple_of,
    'minLength': _Validator.min_length,
    'maxLength': _Validator.max_length,
    'pattern': _Validator.pattern,
    'format': _Validator.format,
    'items': _Validator.items,
    'prefixItems': _Validator.prefix_items,
    'minItems': _Validator.min_items,
    'maxItems': _Validator.max_items,
    'uniqueItems': _Validator.unique_items,
    'contains': _Validator.contains,
    'properties': _Validator.properties,
    'patternProperties': _Validator.pattern_properties,
    'additionalProperties': _Validator.additional_properties,
    'propertyNames': _Validator.property_names,
    'required': _Validator.required,
    'minProperties': _Validator.min_properties,
    'maxProperties': _Validator.max_properties,
    'dependentRequired': _Validator.dependent_required,
    'dependentSchemas': _Validator.dependent_schemas,
    'allOf': _Validator.all_of,
    'anyOf': _Validator.any_of,
    'oneOf': _Validator.one_of,
    'not': _Validator.not_,
    'if': _Validator.if_,
    '$ref': _Validator.ref,
    '$dynamicRef': _Validator.unsupported,
    'unevaluatedItems': _Validator.unsupported,
    'unevaluatedProperties': _Validator.unsupported,
}

# The types of the numbers, and the keywords of 2020-12 that the validation does not support
_NUMBERS = ('integer', 'number')
_UNSUPPORTED = ('$dynamicRef', 'unevaluatedItems', 'unevaluatedProperties')

# The keywords of a schema, of an object of schemas and of an array of schemas
_SCHEMA = (
    'additionalProperties',
    'contains',
    'contentSchema',
    'else',
    'if',
    'items',
    'not',
    'propertyNames',
    'then',
)
_SCHEMAS = ('$defs', 'dependentSchemas', 'patternProperties', 'properties')
_SCHEMA_LISTS = ('allOf', 'anyOf', 'oneOf', 'prefixItems')


def _mismatch(at: _At, failures: list[list[Error]]) -> list[Error]:
    # The errors of the schemas of anyOf or oneOf of the type of the value, or one of the types that they expect
    def expected(failure: list[Error]) -> list[str] | None:
        for error in failure:
            if error._expected is not None and error.path == at.path:  # pyright: ignore[reportPrivateUsage]
                return error._expected  # pyright: ignore[reportPrivateUsage]
        return None

    errors = [error for failure in failures if expected(failure) is None for error in failure]
    if errors:
        return errors
    types = list(dict.fromkeys(t for failure in failures for t in expected(failure) or []))
    error = Error(at.path, at.where, f'Expected {" or ".join(types)} - got {_type_name(at.value)}.')
    error._expected = types  # pyright: ignore[reportPrivateUsage]
    return [error]


def _json_errors(value: Any, path: str, errors: list[Error]) -> None:
    # The values that JSON does not have, which no schema validates
    if isinstance(value, dict):
        for name, item in cast(dict[Any, Any], value).items():
            if not isinstance(name, str):
                errors.append(Error(path, '', f'Not a JSON value: the name {name!r}.'))
            else:
                _json_errors(item, f'{path}/{_escape(name)}', errors)
    elif isinstance(value, (list, builtins.tuple)):
        for i, item in enumerate(cast(list[Any], value)):
            _json_errors(item, f'{path}/{i}', errors)
    elif isinstance(value, float) and not math.isfinite(value):
        errors.append(Error(path, '', f'Not a JSON value: {value!r}.'))
    elif not (value is None or isinstance(value, (bool, builtins.int, float, str))):
        errors.append(Error(path, '', f'Not a JSON value: {type(value).__name__}.'))


def _instance_type(value: Any) -> str:
    if isinstance(value, float):
        return 'integer' if value.is_integer() else 'number'
    return _type_name(value)


def _type_name(value: Any) -> str:
    return _json_type(value) or ('object' if isinstance(value, dict) else 'array')


def _canonical(value: Any) -> Any:
    # A value that is equal to another one as JSON has it: 1 and 1.0 are, True and 1 are not
    if isinstance(value, bool) or value is None:
        return ('literal', value)
    if isinstance(value, (builtins.int, float)):
        return ('number', value)
    if isinstance(value, dict):
        return ('object', frozenset((name, _canonical(item)) for name, item in cast(dict[str, Any], value).items()))
    if isinstance(value, (list, builtins.tuple)):
        return ('array', builtins.tuple(_canonical(item) for item in cast(list[Any], value)))
    return ('string', value)


def _fraction(number: float) -> fractions.Fraction:
    # The number as JSON writes it, so that 0.0075 is a multiple of 0.0001
    return fractions.Fraction(number) if isinstance(number, builtins.int) else fractions.Fraction(repr(number))


def _escape(name: Any) -> str:
    return str(name).replace('~', '~0').replace('/', '~1')


def _uri(base: str, ref: str) -> tuple[str, str]:
    # The URI of a reference without its fragment, and the fragment, decoded
    url = Pyjo.URL.new(ref).to_abs(Pyjo.URL.new(base))
    fragment = url.fragment or ''
    url.fragment = None
    return url.to_str(), fragment


# The classes of ECMAScript, ASCII but the white space, as ranges of code points
_ECMA_CLASSES: dict[str, list[builtins.tuple[builtins.int, builtins.int]]] = {
    'd': [(0x30, 0x39)],
    'w': [(0x30, 0x39), (0x41, 0x5A), (0x5F, 0x5F), (0x61, 0x7A)],
    's': [
        (0x09, 0x0D),
        (0x20, 0x20),
        (0xA0, 0xA0),
        (0x1680, 0x1680),
        (0x2000, 0x200A),
        (0x2028, 0x2029),
        (0x202F, 0x202F),
        (0x205F, 0x205F),
        (0x3000, 0x3000),
        (0xFEFF, 0xFEFF),
    ],
}


def _ranges(ranges: list[builtins.tuple[builtins.int, builtins.int]], negate: bool) -> str:
    if negate:
        ranges = _complement(ranges)
    return ''.join(f'\\U{low:08x}' if low == high else f'\\U{low:08x}-\\U{high:08x}' for low, high in ranges)


# The groups of ECMAScript, with the modifiers of ES2025
_RE_ECMA_GROUP = re.compile(r'\(\?(?:[:=!]|<[=!]|[ims]*(?:-[ims]*)?:)')

# The general categories of Unicode, by their aliases, which \p of ECMAScript takes
_CATEGORIES = {
    'C': 'C Other',
    'Cc': 'Cc Control cntrl',
    'Cf': 'Cf Format',
    'Cn': 'Cn Unassigned',
    'Co': 'Co Private_Use',
    'Cs': 'Cs Surrogate',
    'L': 'L Letter',
    'LC': 'LC Cased_Letter',
    'Ll': 'Ll Lowercase_Letter',
    'Lm': 'Lm Modifier_Letter',
    'Lo': 'Lo Other_Letter',
    'Lt': 'Lt Titlecase_Letter',
    'Lu': 'Lu Uppercase_Letter',
    'M': 'M Mark Combining_Mark',
    'Mc': 'Mc Spacing_Mark',
    'Me': 'Me Enclosing_Mark',
    'Mn': 'Mn Nonspacing_Mark',
    'N': 'N Number',
    'Nd': 'Nd Decimal_Number digit',
    'Nl': 'Nl Letter_Number',
    'No': 'No Other_Number',
    'P': 'P Punctuation punct',
    'Pc': 'Pc Connector_Punctuation',
    'Pd': 'Pd Dash_Punctuation',
    'Pe': 'Pe Close_Punctuation',
    'Pf': 'Pf Final_Punctuation',
    'Pi': 'Pi Initial_Punctuation',
    'Po': 'Po Other_Punctuation',
    'Ps': 'Ps Open_Punctuation',
    'S': 'S Symbol',
    'Sc': 'Sc Currency_Symbol',
    'Sk': 'Sk Modifier_Symbol',
    'Sm': 'Sm Math_Symbol',
    'So': 'So Other_Symbol',
    'Z': 'Z Separator',
    'Zl': 'Zl Line_Separator',
    'Zp': 'Zp Paragraph_Separator',
    'Zs': 'Zs Space_Separator',
}
_CATEGORY_ALIASES = {alias: category for category, aliases in _CATEGORIES.items() for alias in aliases.split()}


@functools.cache
def _category_ranges() -> dict[str, list[builtins.tuple[builtins.int, builtins.int]]]:
    # The ranges of the code points of each general category of unicodedata, once a pattern has \p
    ranges: dict[str, list[builtins.tuple[builtins.int, builtins.int]]] = {}
    start, current = 0, unicodedata.category('\0')
    for code in range(1, sys.maxunicode + 2):
        category = unicodedata.category(chr(code)) if code <= sys.maxunicode else ''
        if category != current:
            ranges.setdefault(current, []).append((start, code - 1))
            start, current = code, category
    return ranges


def _property(source: str, name: str) -> list[builtins.tuple[builtins.int, builtins.int]]:
    # The code points of a property of \p, a general category or ASCII, Any and Assigned
    name = name.removeprefix('General_Category=').removeprefix('gc=')
    if name in ('ASCII', 'Any'):
        return [(0, 0x7F if name == 'ASCII' else sys.maxunicode)]
    category = 'Cn' if name == 'Assigned' else _CATEGORY_ALIASES.get(name)
    if category is None:
        raise Pyjo.Exception.new(f'JSON Schema does not support the pattern {source}: the property {name}')
    ranges = sorted(
        r
        for c, rs in _category_ranges().items()
        if c == category or (len(category) == 1 and c[0] == category) or (category == 'LC' and c in ('Ll', 'Lt', 'Lu'))
        for r in rs
    )
    if name == 'Assigned':
        return _complement(ranges)
    return ranges


def _complement(
    ranges: list[builtins.tuple[builtins.int, builtins.int]],
) -> list[builtins.tuple[builtins.int, builtins.int]]:
    complement: list[builtins.tuple[builtins.int, builtins.int]] = []
    start = 0
    for low, high in ranges:
        if low > start:
            complement.append((start, low - 1))
        start = high + 1
    return [*complement, (start, sys.maxunicode)] if start <= sys.maxunicode else complement


def _regex(source: str) -> re.Pattern[str]:
    # A regular expression of ECMAScript as one of Python: \d, \w and \b are ASCII, \s has the white space of
    # ECMAScript, . matches no line terminator, $ only the end, and the named groups have the syntax of Python
    out: list[str] = []
    i, in_class = 0, False
    while i < len(source):
        c = source[i]
        if c == '\\' and i + 1 < len(source):
            e = source[i + 1]
            i += 2
            if e in 'dDsSwW' or (e in 'pP' and source.startswith('{', i) and '}' in source[i:]):
                if e in 'pP':
                    end = source.index('}', i)
                    ranges = _ranges(_property(source, source[i + 1 : end]), e == 'P')
                    i = end + 1
                else:
                    ranges = _ranges(_ECMA_CLASSES[e.lower()], e.isupper())
                out.append(ranges if in_class else f'[{ranges}]')
            elif e in 'bB' and not in_class:
                out.append(f'(?a:\\{e})')
            elif e == 'k' and source.startswith('<', i) and '>' in source[i:]:
                end = source.index('>', i)
                out.append(f'(?P={source[i + 1 : end]})')
                i = end + 1
            elif e == 'c' and i < len(source) and source[i].isascii() and source[i].isalpha():
                out.append(f'\\x{ord(source[i]) % 32:02x}')
                i += 1
            elif e == 'u' and source.startswith('{', i) and '}' in source[i:]:
                end = source.index('}', i)
                out.append(f'\\U{builtins.int(source[i + 1 : end], 16):08x}')
                i = end + 1
            elif e.isascii() and e.isalpha() and e not in 'bBcdDfknpPrsStuvwWx':
                raise Pyjo.Exception.new(f'JSON Schema does not support the pattern {source}: \\{e} of Python')
            else:
                out.append(c + e)
            continue
        if in_class:
            if c == ']':
                in_class = False
            out.append(f'\\{c}' if c in '[&~|' else c)
        elif source.startswith('[]', i):
            out.append('(?!)')
            i += 1
        elif source.startswith('[^]', i):
            out.append('[\\s\\S]')
            i += 2
        elif c == '[':
            in_class = True
            out.append('[^' if source.startswith('[^', i) else '[')
            i += 1 if source.startswith('[^', i) else 0
        elif c == '.':
            out.append('[^\\n\\r\\u2028\\u2029]')
        elif c == '$':
            out.append('\\Z')
        elif source.startswith('(?<', i) and not source.startswith(('(?<=', '(?<!'), i):
            out.append('(?P<')
            i += 2
        elif source.startswith('(?', i) and not _RE_ECMA_GROUP.match(source, i):
            raise Pyjo.Exception.new(f'JSON Schema does not support the pattern {source}: a group of Python')
        else:
            out.append(c)
        i += 1
    try:
        return re.compile(''.join(out))
    except re.error as e:
        raise Pyjo.Exception.new(f'JSON Schema does not support the pattern {source}: {e}') from None


# The formats of RFC 3339, of RFC 3986 and the others, which validate a string
_RE_DATE = re.compile(r'([0-9]{4})-([0-9]{2})-([0-9]{2})')
_RE_TIME = re.compile(r'([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.[0-9]+)?(?:[Zz]|([+-])([0-9]{2}):([0-9]{2}))')
_RE_DURATION = re.compile(
    r'P(?:[0-9]+W|(?:[0-9]+Y(?:[0-9]+M(?:[0-9]+D)?)?|[0-9]+M(?:[0-9]+D)?|[0-9]+D)(?:T(?:{0}))?|T(?:{0}))'.format(
        r'[0-9]+H(?:[0-9]+M(?:[0-9]+S)?)?|[0-9]+M(?:[0-9]+S)?|[0-9]+S'
    )
)
_RE_EMAIL_LOCAL = re.compile(
    r'''[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x20\x21\x23-\x5b\x5d-\x7e]|\\[\x20-\x7e])*"'''
)
_RE_HOSTNAME_LABEL = re.compile(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?')
_RE_IPV4 = re.compile(
    r'(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])'
)
_RE_JSON_POINTER = re.compile(r'(?:/(?:[^~/]|~[01])*)*')
_RE_RELATIVE_JSON_POINTER = re.compile(r'(?:0|[1-9][0-9]*)(?:#|(?:/(?:[^~/]|~[01])*)*)')
_RE_UUID = re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')

_URI_PCHAR = r"(?:[A-Za-z0-9\-._~!$&'()*+,;=:@]|%[0-9A-Fa-f]{2})"
_URI_SEGMENT_NC = r"(?:[A-Za-z0-9\-._~!$&'()*+,;=@]|%[0-9A-Fa-f]{2})"
_URI_AUTHORITY = (
    r"//(?:(?:[A-Za-z0-9\-._~!$&'()*+,;=:]|%[0-9A-Fa-f]{2})*@)?"
    r"(?:\[(?P<ip>[^\]]*)\]|(?:[A-Za-z0-9\-._~!$&'()*+,;=]|%[0-9A-Fa-f]{2})*)(?::[0-9]*)?"
)
_URI_ABSOLUTE = rf'/(?:{_URI_PCHAR}+(?:/{_URI_PCHAR}*)*)?'
_URI_END = rf'(?:\?(?:{_URI_PCHAR}|[/?])*)?(?:#(?:{_URI_PCHAR}|[/?])*)?'
_URI = (
    rf'[A-Za-z][A-Za-z0-9+\-.]*:(?:{_URI_AUTHORITY}(?:/{_URI_PCHAR}*)*|{_URI_ABSOLUTE}'
    rf'|{_URI_PCHAR}+(?:/{_URI_PCHAR}*)*)?{_URI_END}'
)
_RE_URI = re.compile(_URI)
_RE_URI_REFERENCE = re.compile(
    rf'{_URI}|(?:{_URI_AUTHORITY.replace("(?P<ip>", "(?P<relative_ip>")}(?:/{_URI_PCHAR}*)*|{_URI_ABSOLUTE}'
    rf'|{_URI_SEGMENT_NC}+(?:/{_URI_PCHAR}*)*)?{_URI_END}'
)


def _date(year: str, month: str, day: str) -> bool:
    try:
        datetime.date(builtins.int(year), builtins.int(month), builtins.int(day))
    except ValueError:
        return False
    return True


def _time(value: str) -> bool:
    match = _RE_TIME.fullmatch(value)
    if match is None:
        return False
    hour, minute, second, sign, offset_hour, offset_minute = match.groups('0')
    if builtins.int(hour) > 23 or builtins.int(minute) > 59 or builtins.int(second) > 60:
        return False
    if builtins.int(offset_hour) > 23 or builtins.int(offset_minute) > 59:
        return False
    if second == '60':
        # A leap second is the last second of a day of UTC
        offset = (builtins.int(offset_hour) * 60 + builtins.int(offset_minute)) * (-1 if sign == '-' else 1)
        return (builtins.int(hour) * 60 + builtins.int(minute) - offset) % 1440 == 23 * 60 + 59
    return True


def _format_date(value: str) -> bool:
    match = _RE_DATE.fullmatch(value)
    return match is not None and _date(*match.groups())


def _format_date_time(value: str) -> bool:
    match = _RE_DATE.match(value)
    return match is not None and value[10:11] in ('T', 't') and _date(*match.groups()) and _time(value[11:])


def _format_email(value: str) -> bool:
    local, at, domain = value.rpartition('@')
    if not at or _RE_EMAIL_LOCAL.fullmatch(local) is None:
        return False
    if domain[:6].lower() == '[ipv6:' and domain.endswith(']'):
        return _format_ipv6(domain[6:-1])
    if domain.startswith('[') and domain.endswith(']'):
        return _RE_IPV4.fullmatch(domain[1:-1]) is not None
    return _format_hostname(domain)


def _format_hostname(value: str) -> bool:
    labels = value.split('.')
    return len(value) <= 253 and all(_RE_HOSTNAME_LABEL.fullmatch(label) and _punycode(label) for label in labels)


def _punycode(label: str) -> bool:
    # An A-label of IDNA is Punycode
    if label[:4].lower() != 'xn--':
        return True
    try:
        punycode_decode(label[4:])
    except UnicodeError:
        return False
    return True


def _format_ipv6(value: str) -> bool:
    if not value.isascii() or '%' in value:
        return False
    try:
        ipaddress.IPv6Address(value)
    except ValueError:
        return False
    return True


def _format_regex(value: str) -> bool:
    try:
        _regex(value)
    except Pyjo.Exception.object:
        return False
    return True


def _format_uri(regex: re.Pattern[str]) -> Callable[[str], bool]:
    def check(value: str) -> bool:
        match = regex.fullmatch(value)
        if match is None:
            return False
        ip = match.groupdict().get('ip') or match.groupdict().get('relative_ip')
        return (
            ip is None
            or _format_ipv6(ip)
            or re.fullmatch(r"[vV][0-9A-Fa-f]+\.[A-Za-z0-9\-._~!$&'()*+,;=:]+", ip) is not None
        )

    return check


_FORMAT_CHECKS: dict[str, Callable[[str], bool]] = {
    'date': _format_date,
    'date-time': _format_date_time,
    'duration': lambda value: _RE_DURATION.fullmatch(value) is not None,
    'email': _format_email,
    'hostname': _format_hostname,
    'ipv4': lambda value: _RE_IPV4.fullmatch(value) is not None,
    'ipv6': _format_ipv6,
    'json-pointer': lambda value: _RE_JSON_POINTER.fullmatch(value) is not None,
    'regex': _format_regex,
    'relative-json-pointer': lambda value: _RE_RELATIVE_JSON_POINTER.fullmatch(value) is not None,
    'time': _time,
    'uri': _format_uri(_RE_URI),
    'uri-reference': _format_uri(_RE_URI_REFERENCE),
    'uuid': lambda value: _RE_UUID.fullmatch(value) is not None,
}


def _literal(values: list[Any], enumeration: bool = False) -> dict[str, Any]:
    keywords: dict[str, Any] = {}
    types = {_json_type(value) for value in values}
    if len(types) == 1 and None not in types:
        keywords['type'] = types.pop()
    if len(values) == 1 and not enumeration:
        keywords['const'] = _json_value(values[0])
    else:
        keywords['enum'] = [_json_value(value) for value in values]
    return keywords


def _nullable(schema: Pyjo_JSON_Schema) -> dict[str, Any]:
    keywords = schema.keywords
    if not schema.is_lazy and isinstance(keywords, dict) and builtins.list(keywords) == ['type']:
        types = keywords['type']
        if isinstance(types, str):
            return {'type': [types, 'null']}
        return {'type': [*cast(list[str], types), 'null']} if 'null' not in types else {'type': types}
    return {'anyOf': [schema, {'type': 'null'}]}


def _json_type(value: Any) -> str | None:
    if isinstance(value, enum.Enum):
        value = value.value
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return 'boolean'
    if isinstance(value, builtins.int):
        return 'integer'
    if isinstance(value, float):
        return 'number'
    if isinstance(value, str):
        return 'string'
    return None


def _json_value(value: Any) -> Any:
    # A default or a literal as JSON has it, or _MISSING for one that it has not
    if isinstance(value, enum.Enum):
        value = value.value
    if value is None or isinstance(value, (bool, builtins.int, float, str)):
        return value
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (list, builtins.tuple)):
        items = [_json_value(item) for item in cast(list[Any], value)]
        return _MISSING if _MISSING in items else items
    if isinstance(value, dict):
        items = {name: _json_value(item) for name, item in cast(dict[Any, Any], value).items()}
        if _MISSING in items.values() or not all(isinstance(name, str) for name in items):
            return _MISSING
        return items
    return _MISSING


def _name(tp: Any) -> str:
    if isinstance(tp, type):
        return tp.__name__ if tp.__module__ == 'builtins' else f'{tp.__module__}.{tp.__qualname__}'
    return repr(tp)


def _hints(obj: Any, where: str) -> dict[str, Any]:
    try:
        return typing.get_type_hints(obj, include_extras=True)
    except NameError as e:
        raise Pyjo.Exception.new(f'JSON Schema{where}: {e}') from e


def _signature(function: Callable[..., Any]) -> tuple[inspect.Signature, dict[str, Any]]:
    target: Any = function
    # The annotations of a class are those of its method __init__, and of another callable object of __call__
    if isinstance(target, type):
        target = target.__init__
    elif not (inspect.isfunction(target) or inspect.ismethod(target)):
        target = target.__call__
    return inspect.signature(function), _hints(
        target, f' of the function {getattr(function, "__qualname__", function)}'
    )


def _description(tp: Any) -> str | None:
    if not isinstance(tp, type):
        return None
    name, doc = tp.__name__, tp.__dict__.get('__doc__')
    # A docstring of its own, not the one that dataclasses makes of the signature, a descriptor on Python 3.15
    if not isinstance(doc, str) or not doc:
        return None
    if dataclasses.is_dataclass(tp) and re.fullmatch(re.escape(name) + r'\(.*\)', doc, re.S):
        return None
    return _docstringto_json(inspect.cleandoc(doc))[0]


def _docstring(function: Callable[..., Any]) -> tuple[str | None, dict[str, str], str | None]:
    return _docstringto_json(inspect.getdoc(function) or '')


def _docstringto_json(doc: str) -> tuple[str | None, dict[str, str], str | None]:
    # The first paragraph, and the descriptions of the parameters and of the return value, in the fields of
    # reStructuredText or in the sections of the Google Python Style Guide, each with the lines that continue it
    lines = doc.splitlines()
    paragraph: list[str] = []
    for line in lines:
        if not line.strip() or _RE_FIELD.match(line) or _RE_ARGS.fullmatch(line) or _RE_SECTION.fullmatch(line):
            break
        paragraph.append(line.strip())

    params: dict[str, list[str]] = {}
    returns: list[str] = []
    current: list[str] | None = None
    section: str | None = None
    indent = item = 0
    for line in lines:
        text = line.strip()
        depth = len(line) - len(line.lstrip())
        if not text:
            continue
        if section is not None and depth <= indent:
            section = current = None
        if section == 'args':
            match = _RE_ITEM.fullmatch(text)
            if match and (current is None or depth <= item):
                item, current = depth, [match.group(2)]
                params[match.group(1)] = current
            elif current is not None:
                current.append(text)
        elif section == 'returns':
            match = _RE_RETURN_TYPE.fullmatch(text)
            returns.append(match.group(1) if match and not returns else text)
        elif _RE_ARGS.fullmatch(text):
            section, indent, current = 'args', depth, None
        elif _RE_RETURNS.fullmatch(text):
            section, indent, current = 'returns', depth, None
        elif _RE_SECTION.fullmatch(text):
            section, indent, current = 'other', depth, None
        elif match := _RE_FIELD.match(text):
            kind, name, rest = match.groups()
            if kind in ('return', 'returns'):
                current = returns
                returns.append(rest)
            elif kind in ('type', 'rtype', 'raise', 'raises') or not name.split():
                current = None
            else:
                current = [rest]
                params[name.split()[-1]] = current
        elif current is not None and depth > 0:
            current.append(text)
        else:
            current = None

    descriptions = {name: ' '.join(text).strip() for name, text in params.items()}
    return (
        ' '.join(paragraph) or None,
        {name: text for name, text in descriptions.items() if text},
        ' '.join(returns).strip() or None,
    )


new = Pyjo_JSON_Schema.new
object = Pyjo_JSON_Schema
Schema = Pyjo_JSON_Schema

of = Pyjo_JSON_Schema.of
parameters = Pyjo_JSON_Schema.parameters
returns = Pyjo_JSON_Schema.returns

# The builder of schemas, the class itself, as z of zod
z = Pyjo_JSON_Schema
