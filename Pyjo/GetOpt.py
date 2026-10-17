"""
Pyjo.GetOpt - Command line options
==================================
::

    import Pyjo.GetOpt

    getopt = Pyjo.GetOpt.new()

    # The value goes to the result
    getopt.option('m|mode=s')

    # The values go to a list
    listen = []
    getopt.option('l|listen=s', listen)

    # A callback gets the value
    @getopt.on('i|inactivity-timeout=i')
    def timeout(name, value):
        print(f'{name}: {value}')

    opts = getopt.parse(['-m', 'production', '-l', 'http://*:8080', 'myapp.py'])
    if not opts:
        raise SystemExit('Usage: ...')
    print(opts.mode)

:mod:`Pyjo.GetOpt` extracts options from a list of command line arguments,
the way `Getopt::Long <https://metacpan.org/pod/Getopt::Long>`_ of Perl does
with the configuration that :func:`Pyjo.Util.getopt` gives it, as the
commands of Mojolicious do. It is the engine of :func:`Pyjo.Util.getopt`,
with decorators for the callbacks of the options.

An option is ``-name`` or ``--name``, with its value after it or after ``=``,
as ``--mode production``, ``--mode=production`` or ``-m production``. The
names are case sensitive and are not abbreviated, and the options of a
single letter are not bundled. The arguments that are not options stay in the
list, in their order, and ``--`` ends the options.

An unknown option, an option without its value and a value of a wrong type are
errors: their messages go to ``sys.stderr``, as warnings, the parsing goes on,
and the result is false.

Options
-------

The specification of an option is its names, separated by ``|``, and what it
takes. ::

    # A flag, True
    getopt.option('v|verbose')

    # A flag that --no-color and --nocolor negate, False
    getopt.option('color!')

    # A counter, which each -v increments
    getopt.option('v|verbose+')

    # A string, an integer or a float
    getopt.option('m|mode=s')
    getopt.option('b|backlog=i')
    getopt.option('r|ratio=f')

    # An optional value, which is "" or 0 without it
    getopt.option('p|proxy:s')

    # A list of values in the result
    getopt.option('H|header=s@')

The name of an option in the result, and the name that a callback gets, is
its first name that is longer than one letter, or its only name, with ``_``
for ``-``: ``inactivity_timeout`` for ``i|inactivity-timeout=i``.

See also
--------

:func:`Pyjo.Util.getopt`, https://mojolicious.org.

Inspired by `Getopt::Long::Parser <https://metacpan.org/pod/Getopt::Long>`_,
the object interface of Getopt::Long, which ``getopt`` of Mojo::Util
configures.

Classes
-------
"""

import Pyjo.Base
import Pyjo.Exception

from Pyjo.Util import warn

import re
import sys

from collections.abc import Callable
from typing import Any, Self, cast, overload


type Callback = Callable[[str, Any], Any]
type Target = list[Any] | Callback | None


class Pyjo_GetOpt(Pyjo.Base.object):
    """
    :mod:`Pyjo.GetOpt` inherits all methods from :mod:`Pyjo.Base` and
    implements the following new ones.
    """

    def __init__(self, *, pass_through: bool = False) -> None:
        """::

            getopt = Pyjo.GetOpt.new()
            getopt = Pyjo.GetOpt.new(pass_through=True)

        Construct a new :mod:`Pyjo.GetOpt` object. With ``pass_through``,
        unknown options and ``--`` stay in the list of arguments, without a
        warning.
        """
        self.pass_through = pass_through
        self._names: dict[str, _Option] = {}
        self._negations: set[str] = set()
        self._options: list[_Option] = []

    @overload
    def on[F: Callback](self, spec: str, cb: None = None) -> Callable[[F], F]: ...

    @overload
    def on[F: Callback](self, spec: str, cb: F) -> F: ...

    def on(self, spec: str, cb: Callback | None = None) -> Any:
        """::

            cb = getopt.on('b|backlog=i', lambda name, value: ...)

            @getopt.on('b|backlog=i')
            def backlog(name, value): ...

        Add an option whose callback gets its name and its value, as a
        decorator without the callback.
        """
        if cb is None:

            def decorator(cb: Callback) -> Callback:
                return self.on(spec, cb)

            return decorator
        self.option(spec, cb)
        return cb

    def option(self, spec: str, target: Target = None) -> Self:
        """::

            getopt = getopt.option('m|mode=s')
            getopt = getopt.option('l|listen=s', [])
            getopt = getopt.option('b|backlog=i', lambda name, value: ...)

        Add an option, whose value goes to the result, to a list or to a
        callback.
        """
        if not (m := re.fullmatch(r'([\w?-]+(?:\|[\w?-]+)*)(?:(!)|(\+)|([=:])([sif])(@)?)?', spec)):
            raise Pyjo.Exception.new(f'Error in option spec: "{spec}"')
        names = m[1].split('|')
        name = next((name for name in names if len(name) > 1), names[0]).replace('-', '_')
        kind = 'negatable' if m[2] else 'increment' if m[3] else 'value' if m[4] else 'flag'
        option = _Option(name, kind, m[5] or '', m[4] == ':', bool(m[6]), target)
        self._options.append(option)
        for name in names:
            self._names[name] = option
            if kind == 'negatable':
                self._names[f'no{name}'] = self._names[f'no-{name}'] = option
                self._negations.update((f'no{name}', f'no-{name}'))
        return self

    def parse(self, args: list[str] | None = None) -> 'Pyjo_GetOpt_Result':
        """::

            opts = getopt.parse()
            opts = getopt.parse(['--mode', 'production', 'myapp.py'])

        Extract the options from the list of arguments, which defaults to the
        ones of ``sys.argv``, and remove them from it. The result has the
        values of the options without a target, and is false after an error.
        """
        argv = sys.argv if args is None else args
        start = 1 if args is None else 0
        rest, keep = argv[start:], list[str]()
        values: dict[str, Any] = {o.name: [] if o.multi else None for o in self._options if o.target is None}
        success = True

        i = 0
        while i < len(rest):
            arg = rest[i]
            i += 1

            # The end of the options
            if arg == '--':
                keep.extend(rest[i - 1 :] if self.pass_through else rest[i:])
                break

            # An argument
            if not arg.startswith('-') or arg == '-':
                keep.append(arg)
                continue

            # An unknown option
            given, _, value = arg.lstrip('-').partition('=')
            value = value if '=' in arg else None
            if (option := self._names.get(given)) is None:
                if self.pass_through:
                    keep.append(arg)
                else:
                    warn(f'Unknown option: {given}')
                    success = False
                continue

            # A flag
            if option.kind != 'value':
                if value is not None:
                    warn(f'Option {given} does not take an argument')
                    success = False
                    continue
                if option.kind == 'increment':
                    _store(option, values, (values.get(option.name) or 0) + 1)
                else:
                    _store(option, values, given not in self._negations)
                continue

            # A value after the option, which an optional one takes only when it is not an option
            if value is None and i < len(rest) and (not option.optional or _is_value(option.type, rest[i])):
                value = rest[i]
                i += 1
            if value is None:
                if not option.optional:
                    warn(f'Option {given} requires an argument')
                    success = False
                    continue
                value = '' if option.type == 's' else '0'

            # The type of the value
            if option.type == 'i' and not re.fullmatch(r'[-+]?\d+', value):
                warn(f'Value "{value}" invalid for option {given} (integer number expected)')
                success = False
            elif option.type == 'f' and not re.fullmatch(r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?', value):
                warn(f'Value "{value}" invalid for option {given} (real number expected)')
                success = False
            else:
                _store(
                    option, values, int(value) if option.type == 'i' else float(value) if option.type == 'f' else value
                )

        argv[start:] = keep
        return Pyjo_GetOpt_Result(values, success)


class Pyjo_GetOpt_Result:
    """
    The result of :meth:`~Pyjo_GetOpt.parse`, the values of the options as
    attributes, which is false after an error.
    """

    def __init__(self, values: dict[str, Any], success: bool) -> None:
        self.__dict__.update(values)
        self._success = success

    def __bool__(self) -> bool:
        return self._success

    # The values are attributes that the specifications of the options name
    def __getattr__(self, name: str) -> Any:
        raise AttributeError(f'{type(self).__name__!r} object has no attribute {name!r}', name=name, obj=self)

    def __repr__(self) -> str:
        values = ', '.join(f'{name}={value!r}' for name, value in vars(self).items() if not name.startswith('_'))
        return f'{type(self).__name__}({values})'


class _Option:
    def __init__(self, name: str, kind: str, type: str, optional: bool, multi: bool, target: Target) -> None:
        self.kind = kind
        self.multi = multi
        self.name = name
        self.optional = optional
        self.target = target
        self.type = type


def _is_value(type: str, arg: str) -> bool:
    if type == 's':
        return not arg.startswith('-') or arg == '-'
    return re.fullmatch(r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?' if type == 'f' else r'[-+]?\d+', arg) is not None


def _store(option: _Option, values: dict[str, Any], value: Any) -> None:
    target = option.target
    if isinstance(target, list):
        cast(list[Any], target).append(value)
    elif target is not None:
        target(option.name, value)
    elif option.multi:
        values[option.name].append(value)
    else:
        values[option.name] = value


new = Pyjo_GetOpt.new
object = Pyjo_GetOpt
