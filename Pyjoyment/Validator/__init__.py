r"""
Pyjoyment.Validator - Validate values
=====================================
::

    from Pyjoyment.Validator import Validator

    validator = Validator()
    v = validator.validation()
    v.input = {'foo': 'bar'}
    v.required('foo').like(re.compile(r'ar$'))
    print(v.param('foo'))

    # Or import the module, as in Google Python Style Guide
    import Pyjoyment.Validator

    validator = Pyjoyment.Validator.new()
    v = validator.validation()
    v.input = {'foo': 'bar'}
    v.required('foo').like(re.compile(r'ar$'))
    print(v.param('foo'))

:mod:`Pyjoyment.Validator` validates values for :mod:`Pyjoyment`.

Checks
------

These validation checks are available by default.

equal_to ::

    v = v.equal_to('foo')

String value needs to be equal to the value of another field.

in ::

    v = v.one_of('foo', 'bar', 'baz')

String value needs to match one of the values in the list. ``in`` is a
keyword of Python, so the method of the check is ``one_of``, and ``in_`` is
its alias.

like ::

    v = v.like(re.compile(r'^[A-Z]'))

String value needs to match the regular expression.

num ::

    v = v.num()
    v = v.num(2, 5)
    v = v.num(-3, 7)
    v = v.num(2, None)
    v = v.num(None, 5)

String value needs to be a non-fractional number (positive or negative) and if
provided in the given range.

size ::

    v = v.size(2, 5)
    v = v.size(2, None)
    v = v.size(None, 5)

String value length or size of :mod:`Pyjo.Upload` object in bytes needs to be
between these two values.

upload ::

    v = v.upload()

Value needs to be a :mod:`Pyjo.Upload` object, representing a file upload.

Filters
-------

These filters are available by default.

comma_separated ::

    v = v.optional('foo', 'comma_separated')

Split string of comma separated values into separate values.

not_empty ::

    v = v.optional('foo', 'not_empty')

Remove empty string values and treat them as if they had not been submitted.

trim ::

    v = v.optional('foo', 'trim')

Trim whitespace characters from both ends of string value with
:func:`Pyjo.Util.trim`.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Validator <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Validator.pm>`_
of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.Base
import Pyjo.String.Unicode
import Pyjo.Upload
import Pyjoyment.Validator.Validation

from Pyjo.Util import trim

import builtins
import re

from collections.abc import Callable
from typing import Any, Self, overload


type Anything = builtins.object

# A check gets the validation, the name and a value of the field, and the arguments of the check, and returns a true
# value when the value fails
type Check = Callable[..., Any]

# A filter gets the validation, the name and a value of the field, and returns the value, or a tuple of several values
type Filter = Callable[..., Any]


class Pyjoyment_Validator(Pyjo.Base.object):
    """
    :mod:`Pyjoyment.Validator` inherits all methods from :mod:`Pyjo.Base` and
    implements the following new ones.
    """

    def __init__(self) -> None:
        """::

            validator = Pyjoyment.Validator.new()

        Construct a new :mod:`Pyjoyment.Validator` object.
        """
        self.checks: dict[str, Check] = {}
        """::

            checks = validator.checks
            validator.checks = {'size': lambda v, name, value, *args: ...}

        Registered validation checks, by default only ``equal_to``, ``in``,
        ``like``, ``num``, ``size`` and ``upload`` are already defined.
        """

        self.filters: dict[str, Filter] = {'comma_separated': _comma_separated, 'not_empty': _not_empty, 'trim': _trim}
        """::

            filters = validator.filters
            validator.filters = {'trim': lambda v, name, value: ...}

        Registered filters, by default only ``comma_separated``,
        ``not_empty`` and ``trim`` are already defined.
        """

        self.add_check('equal_to', _equal_to)
        self.add_check('in', _in)
        self.add_check('like', _like)
        self.add_check('num', _num)
        self.add_check('size', _size)
        self.add_check('upload', _upload)

    @overload
    def add_check[F: Check](self, name: str, cb: None = None) -> Callable[[F], F]: ...

    @overload
    def add_check(self, name: str, cb: Check) -> Self: ...

    def add_check(self, name: str, cb: Check | None = None) -> Any:
        """::

            validator = validator.add_check('size', lambda v, name, value, *args: ...)

            @validator.add_check('size')
            def size(v, name, value, *args): ...

        Register a validation check. ::

            @validator.add_check('foo')
            def foo(v, name, value, *args):
                ...
                return None
        """
        if cb is None:

            def decorator(cb: Check) -> Check:
                self.add_check(name, cb)
                return cb

            return decorator

        # Unlike Mojolicious: Mojo registers the check as a method of Mojolicious::Validator::Validation with
        # Mojo::DynamicMethods, Python looks it up in the checks of the validator when a method is not found
        self.checks[name] = cb
        return self

    @overload
    def add_filter[F: Filter](self, name: str, cb: None = None) -> Callable[[F], F]: ...

    @overload
    def add_filter(self, name: str, cb: Filter) -> Self: ...

    def add_filter(self, name: str, cb: Filter | None = None) -> Any:
        """::

            validator = validator.add_filter('trim', lambda v, name, value: ...)

            @validator.add_filter('trim')
            def trim(v, name, value): ...

        Register a new filter. ::

            @validator.add_filter('foo')
            def foo(v, name, value):
                ...
                return value
        """
        if cb is None:

            def decorator(cb: Filter) -> Filter:
                self.add_filter(name, cb)
                return cb

            return decorator
        self.filters[name] = cb
        return self

    def validation(self) -> 'Pyjoyment.Validator.Validation.object':
        """::

            v = validator.validation()

        Build :mod:`Pyjoyment.Validator.Validation` object to perform
        validations. ::

            v = validator.validation()
            v.input = {'foo': 'bar'}
            v.required('foo').size(1, 5)
            print(v.param('foo'))
        """
        return Pyjoyment.Validator.Validation.new(validator=self)


def _comma_separated(v: Anything, name: str, value: Anything) -> tuple[str, ...] | None:
    if value is None:
        return None
    return tuple(str(part) for part in Pyjo.String.Unicode.new(str(value)).split(r'\s*,\s*', -1))


def _equal_to(v: 'Pyjoyment.Validator.Validation.object', name: str, value: Anything, to: str) -> bool:
    if (other := v.input.get(to)) is None:
        return True
    return str(value) != str(other)


def _in(v: Anything, name: str, value: Anything, *values: Anything) -> bool:
    return not any(str(value) == str(item) for item in values)


def _like(v: Anything, name: str, value: Anything, regex: str | re.Pattern[str]) -> bool:
    return not re.search(regex, str(value))


def _not_empty(v: Anything, name: str, value: Anything) -> Anything:
    return value if value is not None and len(str(value)) else ()


def _num(v: Anything, name: str, value: Anything, min: int | None = None, max: int | None = None) -> bool:
    if not re.search(r'^-?[0-9]+$', string := str(value)):
        return True
    number = int(string)
    return min is not None and min > number or max is not None and max < number


def _size(v: Anything, name: str, value: Anything, min: int | None = None, max: int | None = None) -> bool:
    length = value.size if isinstance(value, Pyjo.Upload.object) else len(str(value))
    return (min is not None and length < min) or (max is not None and length > max)


def _trim(v: Anything, name: str, value: Anything) -> str | None:
    return trim(str(value)) if value is not None else None


def _upload(v: Anything, name: str, value: Anything) -> bool:
    return not isinstance(value, Pyjo.Upload.object)


new = Pyjoyment_Validator.new
object = Pyjoyment_Validator
Validator = Pyjoyment_Validator
