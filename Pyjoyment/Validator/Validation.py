"""
Pyjoyment.Validator.Validation - Perform validations
====================================================
::

    import Pyjoyment.Validator
    import Pyjoyment.Validator.Validation

    validator = Pyjoyment.Validator.new()
    v = Pyjoyment.Validator.Validation.new(validator=validator)
    v.input = {'foo': 'bar'}
    v.required('foo').one_of('bar', 'baz')
    print(v.param('foo'))

:mod:`Pyjoyment.Validator.Validation` performs :mod:`Pyjoyment.Validator`
validation checks.

Checks
------

In addition to the attributes and methods below, you can also call validation
checks provided by :attr:`~Pyjoyment_Validator_Validation.validator` on
:mod:`Pyjoyment.Validator.Validation` objects, similar to
:meth:`~Pyjoyment_Validator_Validation.check`. ::

    # Call validation checks
    v.required('foo').size(2, 5).like(re.compile(r'^[A-Z]'))
    v.optional('bar').equal_to('foo')
    v.optional('baz').one_of('test', '123')

    # Longer version
    v.required('foo').check('size', 2, 5).check('like', re.compile(r'^[A-Z]'))

A check with the name of a keyword of Python, as ``in``, is also a method
with the name followed by an underscore, as ``in_``.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Validator::Validation
<https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Validator/Validation.pm>`_ of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.Base

from Pyjo.Util import secure_compare

import builtins
import functools
import keyword
import re
import sys

from typing import TYPE_CHECKING, Any, Self, cast, overload


if TYPE_CHECKING:
    import Pyjoyment.Validator


type Anything = builtins.object

# Renamed from Mojolicious: the check "in" is the method one_of, as "in" is a keyword of Python
_RENAMED = {'one_of': 'in'}


class Pyjoyment_Validator_Validation(Pyjo.Base.object):
    """
    :mod:`Pyjoyment.Validator.Validation` inherits all methods from
    :mod:`Pyjo.Base` and implements the following new ones.
    """

    def __init__(
        self,
        *,
        csrf_token: str | None = None,
        input: dict[str, Any] | None = None,
        output: dict[str, Any] | None = None,
        topic: str | None = None,
        validator: 'Pyjoyment.Validator.object | None' = None,
    ) -> None:
        """::

            v = Pyjoyment.Validator.Validation.new(validator=Pyjoyment.Validator.new())

        Construct a new :mod:`Pyjoyment.Validator.Validation` object.
        """
        self.csrf_token = csrf_token
        """::

            token = v.csrf_token
            v.csrf_token = 'fa6a08...'

        CSRF token.
        """

        self.input: dict[str, Any] = input if input is not None else {}
        """::

            input = v.input
            v.input = {'foo': 'bar', 'baz': [123, 'yada']}

        Data to be validated.
        """

        self.output: dict[str, Any] = output if output is not None else {}
        """::

            output = v.output
            v.output = {'foo': 'bar', 'baz': [123, 'yada']}

        Validated data.
        """

        self.topic = topic
        """::

            topic = v.topic
            v.topic = 'foo'

        Name of field currently being validated.
        """

        self.validator = validator
        """::

            validator = v.validator
            v.validator = Pyjoyment.Validator.new()

        :mod:`Pyjoyment.Validator` object this validation belongs to.
        """

        self._error: dict[str, list[Any]] = {}

    # Unlike Mojolicious: Mojo registers the checks with Mojo::DynamicMethods, Python looks them up in the checks of
    # the validator when a method is not found
    def __getattr__(self, name: str) -> Any:
        validator: Any = vars(self).get('validator')
        if not name.startswith('_') and validator is not None:
            check = _RENAMED.get(name, name)
            if check.endswith('_') and keyword.iskeyword(check[:-1]):
                check = check[:-1]
            if check in validator.checks:
                return functools.partial(self.check, check)
        package = f'{type(self).__module__}.{type(self).__qualname__}'

        # The location of the caller, which croak adds to the message
        caller = sys._getframe(1)  # pyright: ignore[reportPrivateUsage]
        at = f'at {caller.f_code.co_filename} line {caller.f_lineno}'
        raise AttributeError(
            f'Can\'t locate object method "{name}" via package "{package}" {at}.\n', name=name, obj=self
        )

    @property
    def failed(self) -> list[str]:
        """::

            names = v.failed

        Return a list with all names for values that failed validation. ::

            # Names of all values that failed
            for name in v.failed:
                print(name)
        """
        return sorted(self._error)

    @property
    def has_data(self) -> bool:
        """::

            boolean = v.has_data

        Check if :attr:`input` is available for validation.
        """
        return bool(self.input)

    @property
    def passed(self) -> list[str]:
        """::

            names = v.passed

        Return a list with all names for values that passed validation. ::

            # Names of all values that passed
            for name in v.passed:
                print(name)
        """
        return sorted(self.output)

    def check(self, check: str, /, *args: Any) -> Self:
        """::

            v = v.check('size', 2, 7)

        Perform validation check on all values of the current :attr:`topic`,
        no more checks will be performed on them after the first one failed.
        All checks from :mod:`Pyjoyment.Validator` are supported.
        """
        if not self.is_valid():
            return self

        assert self.validator is not None
        cb = self.validator.checks[check]
        name = self.topic
        assert name is not None
        for value in _list(self.output[name]):
            if not (result := cb(self, name, value, *args)):
                continue
            return self.error(name, [check, result, *args])

        return self

    def csrf_protect(self) -> Self:
        """::

            v = v.csrf_protect()

        Validate ``csrf_token`` and protect from cross-site request forgery.
        Tokens are masked with a random value to protect against BREACH
        attacks.
        """
        token = self.input.get('csrf_token')
        if not _csrf_valid(token, self.csrf_token):
            self.error('csrf_token', ['csrf_protect'])
        return self

    @overload
    def error(self, name: str, /) -> list[Any] | None: ...

    @overload
    def error(self, name: str, value: list[Any], /) -> Self: ...

    def error(self, name: str, /, *args: list[Any]) -> list[Any] | None | Self:
        """::

            err = v.error('foo')
            v = v.error('foo', ['custom_check'])
            v = v.error('foo', [check, result, *args])

        Get or set details for failed validation check, at any given time
        there can only be one per field. ::

            # Details about failed validation
            check, result, *args = v.error('foo')

            # Force validation to fail for a field without performing a check
            v.error('foo', ['some_made_up_check_name'])
        """
        if not args:
            return self._error.get(name)
        self._error[name] = args[0]
        self.output.pop(name, None)
        return self

    def every_param(self, name: str | None = None) -> list[Any]:
        """::

            values = v.every_param()
            values = v.every_param('foo')

        Similar to :meth:`param`, but returns all values sharing the same name
        as a list. ::

            # Get first value
            first = v.every_param('foo')[0]
        """
        if (key := name if name is not None else self.topic) is None or (value := self.output.get(key)) is None:
            return []
        return _list(value)

    def has_error(self, name: str | None = None) -> bool:
        """::

            boolean = v.has_error()
            boolean = v.has_error('foo')

        Check if validation resulted in errors, defaults to checking all
        fields.
        """
        # Unlike Mojolicious: a field named "0" is checked, where Mojo checks all the fields, as "0" is false in Perl
        return name in self._error if name is not None else bool(self._error)

    def is_valid(self, name: str | None = None) -> bool:
        """::

            boolean = v.is_valid()
            boolean = v.is_valid('foo')

        Check if validation was successful and field has a value, defaults to
        checking the current :attr:`topic`.
        """
        return (name if name is not None else self.topic) in self.output

    def optional(self, name: str, /, *filters: str) -> Self:
        """::

            v = v.optional('foo')
            v = v.optional('foo', *filters)

        Change validation :attr:`topic` and apply filters. All filters from
        :mod:`Pyjoyment.Validator` are supported. ::

            # Trim value and check size
            v.optional('user', 'trim').size(1, 15)
        """
        self.topic = name
        if (input := self.input.get(name)) is None:
            return self

        values = _list(input)
        assert self.validator is not None
        for cb in [self.validator.filters[f] for f in filters]:
            values = [item for value in values for item in _values(cb(self, name, value))]
        if values and all(value is not None for value in values):
            self.output[name] = values if len(values) > 1 else values[0]

        return self

    def param(self, name: str | None = None) -> Any:
        """::

            value = v.param()
            value = v.param('foo')

        Access validated values, defaults to the current :attr:`topic`. If
        there are multiple values sharing the same name, and you want to
        access more than just the last one, you can use :meth:`every_param`.
        ::

            # Get value right away
            user = v.optional('user').size(1, 15).param()
        """
        values = self.every_param(name)
        return values[-1] if values else None

    def required(self, name: str, /, *filters: str) -> Self:
        """::

            v = v.required('foo')
            v = v.required('foo', *filters)

        Change validation :attr:`topic`, apply filters, and make sure a value
        is present. All filters from :mod:`Pyjoyment.Validator` are supported.
        ::

            # Trim value and check size
            v.required('user', 'trim').size(1, 15)
        """
        if self.optional(name, *filters).is_valid():
            return self
        return self.error(name, ['required'])


def _csrf_valid(token: Anything, csrf: str | None) -> bool:
    if not isinstance(token, str) or not re.search(r'^[0-9a-f]{80}$', token):
        return False

    # Unmask token to protect against BREACH attacks
    mask = bytes.fromhex(token[:40])
    masked = bytes.fromhex(token[40:])
    return secure_compare(bytes(a ^ b for a, b in zip(mask, masked, strict=True)).hex(), csrf or '')


# The values of a field, which are several for a list
def _list(value: Any) -> list[Any]:
    return list(cast(list[Any], value)) if isinstance(value, list) else [value]


# The values that a filter returns, which are several for a tuple
def _values(result: Any) -> tuple[Any, ...]:
    return cast(tuple[Any, ...], result) if isinstance(result, tuple) else (result,)


new = Pyjoyment_Validator_Validation.new
object = Pyjoyment_Validator_Validation
Validation = Pyjoyment_Validator_Validation
