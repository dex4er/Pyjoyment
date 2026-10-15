r"""
Pyjo.Exception - Exception base class
=====================================
::

    import Pyjo.Exception

    # Create exception classes
    class MyApp_X_Foo(Pyjo.Exception.object):
        pass

    class MyApp_X_Bar(Pyjo.Exception.object):
        pass

    # Throw exceptions and handle them gracefully
    from Pyjo.Exception import check
    try:
        MyApp_X_Foo.throw('Something went wrong!')
    except Exception as e:
        check(e, [
            (MyApp_X_Foo, lambda e: print(f'Foo: {e}')),
            (MyApp_X_Bar, lambda e: print(f'Bar: {e}')),
        ])

    # Generate exception classes on demand
    from Pyjo.Exception import check, throw
    try:
        throw('MyApp.X.Name', 'The name Minion is already taken')
    except Exception as e:
        check(e, [
            ('MyApp.X.Name', lambda e: print(f'Name error: {e}')),
            ('default', lambda e: print(f'Error: {e}')),
        ])

:mod:`Pyjo.Exception` is a container for exceptions with context
information. It is an :class:`Exception`, so it is raised and caught as the
exceptions of Python are.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Exception <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Exception.pm>`_
of Mojolicious 9.49.

Functions
---------
"""

import Pyjo.Base
import Pyjo.String.Mixin

from Pyjo.Util import decode

import builtins
import importlib
import os
import re
import sys
import traceback

from collections.abc import Callable
from typing import Any, NoReturn, Self, cast


type Anything = builtins.object

# A pattern of check(): "default", a class, its name or a regular expression
type Pattern = str | type[BaseException] | re.Pattern[str]


class Pyjo_Exception(Exception, Pyjo.Base.object, Pyjo.String.Mixin.object):
    """
    :mod:`Pyjo.Exception` inherits all methods from :class:`Exception`,
    :mod:`Pyjo.Base` and :mod:`Pyjo.String.Mixin` and implements the following
    new ones.
    """

    def __init__(self, message: Anything = None) -> None:
        """::

            e = Pyjo.Exception.new()
            e = Pyjo.Exception.new('Died at test.py line 3.')
            e = Pyjo.Exception.new(ValueError('Something went wrong!'))

        Construct a new :mod:`Pyjo.Exception` object and assign
        :attr:`message` if necessary. An exception of Python gives its message
        and the :attr:`frames` of its traceback.
        """
        self.frames: list[traceback.FrameSummary] = []
        """::

            frames = e.frames
            e.frames = [frame1, frame2]

        Stack trace if available, as a list of
        :class:`traceback.FrameSummary`, the most recent first. ::

            # Extract information from the last frame
            filename, lineno, name, line = e.frames[-1]
        """

        self.line: list[int | str] = []
        """::

            line = e.line
            e.line = [3, 'raise Exception()']

        The line where the exception occurred if available.
        """

        self.lines_after: list[list[int | str]] = []
        """::

            lines = e.lines_after
            e.lines_after = [[4, 'print(foo)'], [5, 'print(bar)']]

        Lines after the line where the exception occurred if available.
        """

        self.lines_before: list[list[int | str]] = []
        """::

            lines = e.lines_before
            e.lines_before = [[1, 'foo = 23'], [2, 'bar = 24']]

        Lines before the line where the exception occurred if available.
        """

        self.message: str = 'Exception!'
        """::

            msg = e.message
            e.message = 'Died at test.py line 3.'

        Exception message, defaults to ``Exception!``.
        """

        self._verbose: bool | None = None

        # Not in Mojolicious: an exception of Python
        if isinstance(message, BaseException):
            self.message = str(message)
            if message.__traceback__ is not None:
                self.frames = list(reversed(traceback.extract_tb(message.__traceback__)))
        elif message is not None:
            self.message = str(message)

        super().__init__(self.message)

    @property
    def verbose(self) -> bool:
        """::

            boolean = e.verbose
            e.verbose = boolean

        Show more information with :meth:`to_str`, such as :attr:`frames`,
        defaults to the value of the ``PYJO_EXCEPTION_VERBOSE`` environment
        variable.
        """
        if self._verbose is None:
            self._verbose = bool(os.environ.get('PYJO_EXCEPTION_VERBOSE'))
        return self._verbose

    @verbose.setter
    def verbose(self, value: bool) -> None:
        self._verbose = value

    def __bool__(self) -> bool:
        """::

            boolean = bool(e)

        Always true.
        """
        return True

    def __str__(self) -> str:
        """::

            string = str(e)

        Alias for :meth:`to_str`.
        """
        return self.to_str()

    def inspect(self, *sources: str) -> Self:
        """::

            e = e.inspect()
            e = e.inspect(source1, source2)

        Inspect :attr:`message`, :attr:`frames` and optional additional sources
        to fill :attr:`lines_before`, :attr:`line` and :attr:`lines_after` with
        context information.
        """
        if len(self.line):
            return self

        # Extract file and line from message
        files = [(m[1], int(m[2])) for m in re.finditer(r'at\s+(.+?)\s+line\s+(\d+)', self.message)][::-1]

        # Extract file and line from stack trace
        if len(self.frames) and (zero := self.frames[0]).lineno is not None:
            files.append((zero.filename, zero.lineno))

        # Search for context in files
        for file, num in files:
            try:
                with open(file, 'rb') as handle:
                    data = handle.read()
            except OSError:
                continue
            self._context(num, [re.findall(rb'[^\n]*\n|[^\n]+$', data)])
            return self

        # Search for context in sources
        if len(sources) and len(files):
            self._context(files[-1][1], [_split(s) for s in sources])

        return self

    @classmethod
    def throw(cls, message: Anything = None) -> NoReturn:
        """::

            Pyjo.Exception.object.throw('Something went wrong!')

        Throw exception from the current execution context. ::

            # Longer version
            raise Pyjo.Exception.new('Something went wrong!').trace()
        """
        raise cls.new(message).trace(2)

    # Renamed from Mojolicious: to_string
    def to_str(self) -> str:
        """::

            string = e.to_str()

        Render exception. Note that the output format may change as more
        features are added, only the error message at the beginning is
        guaranteed not to be modified to allow regex matching.
        """
        string = self.message

        frames = self.frames
        if not string.endswith('\n'):
            string += f' at {frames[0].filename} line {frames[0].lineno}.\n' if len(frames) else '\n'
        if not self.verbose:
            return string

        line = self.line
        if len(line):
            string += 'Context:\n'
            string += ''.join(f'  {n[0]}: {n[1]}\n' for n in self.lines_before)
            string += f'  {line[0]}: {line[1]}\n'
            string += ''.join(f'  {n[0]}: {n[1]}\n' for n in self.lines_after)

        if len(frames):
            string += 'Traceback (most recent call first):\n'
            string += ''.join(f'  File "{f.filename}", line {f.lineno}, in "{f.name}"\n' for f in frames)

        return string

    def trace(self, start: int = 1) -> Self:
        """::

            e = e.trace()
            e = e.trace(skip)

        Generate stack trace and store all :attr:`frames`, defaults to skipping
        ``1`` call frame. ::

            # Skip 3 call frames
            e.trace(3)

            # Skip no call frames
            e.trace(0)
        """
        try:
            frame = sys._getframe(start)  # pyright: ignore[reportPrivateUsage]
        except ValueError:
            self.frames = []
        else:
            self.frames = list(reversed(traceback.extract_stack(frame)))
        return self

    # Left out from Mojolicious: with_roles, as Pyjoyment has no roles

    def _context(self, num: int, sources: list[list[bytes]] | list[list[str]]) -> None:

        # Line
        if not 0 <= num - 1 < len(sources[0]):
            return
        self.line = [num]
        for s in sources:
            self.line.append(_line(s[num - 1]))

        # Before
        for i in range(2, 7):
            if (previous := num - i) < 0:
                break
            self.lines_before.insert(0, [previous + 1, *(_line(s[previous]) for s in sources)])

        # After
        for i in range(5):
            if (following := num + i) < 0 or following >= len(sources[0]):
                continue
            self.lines_after.append([following + 1, *(_line(s[following]) for s in sources)])


def check(
    err: Anything, spec: list[tuple[Pattern | list[Pattern] | tuple[Pattern, ...], Callable[[Any], Anything]]]
) -> bool | None:
    """::

        boolean = check(err, [(MyApp_X_Foo, lambda e: ...)])

    Process exceptions by dispatching them to handlers with one or more
    matching conditions. Exceptions that could not be handled will be raised
    again automatically. ::

        # Handle various types of exceptions
        try:
            dangerous_code()
        except Exception as e:
            check(e, [
                (MyApp_X_Foo, lambda e: print(f'Foo: {e}')),
                (re.compile(r'^Could not open'), lambda e: print(f'Open error: {e}')),
                ('default', lambda e: print(f'Something went wrong: {e}')),
            ])

    Matching conditions can be classes, or their names, for checks with
    :func:`isinstance` on exception objects, or regular expressions to match
    string exceptions and stringified exception objects. The matching
    exception will be the argument passed to the callback. ::

        # Catch MyApp_X_Foo object or a specific string exception
        try:
            dangerous_code()
        except Exception as e:
            check(e, [
                (MyApp_X_Foo, lambda e: print(f'Foo: {e}')),
                (re.compile(r'^Could not open'), lambda e: print(f'Open error: {e}')),
            ])

    A list can be used to share the same handler with multiple conditions, of
    which only one needs to match. And since exception handlers are just
    callbacks, they can also throw their own exceptions. ::

        # Handle MyApp_X_Foo and MyApp_X_Bar the same
        try:
            dangerous_code()
        except Exception as e:
            check(e, [
                ([MyApp_X_Foo, MyApp_X_Bar], lambda e: Pyjo.Exception.object.throw(f'Foo/Bar: {e}')),
            ])

    There is currently only one keyword you can use to set special handlers.
    The ``default`` handler is used when no other handler matched. ::

        # Use "default" to catch everything
        try:
            dangerous_code()
        except Exception as e:
            check(e, [
                ('default', lambda e: print(f'Error: {e}')),
            ])
    """
    if not err:
        return None

    # The spec is checked as Mojo checks it, for the caller without type hints
    pairs = cast(Anything, spec)
    if not isinstance(pairs, list) or not all(
        isinstance(p, tuple) and len(cast(tuple[Any, ...], p)) == 2 for p in cast(list[Any], pairs)
    ):
        # Unlike Mojolicious: Mojo asks for an array reference
        raise TypeError('List of pattern/handler pairs required to dispatch exceptions')

    default = handler = None
    is_obj, string = not isinstance(err, str), str(err)
    for checks, cb in spec:
        if checks == 'default':
            default = cb
            continue

        for c in checks if isinstance(checks, (list, tuple)) else [checks]:
            is_re = isinstance(c, re.Pattern)
            if is_obj and not is_re and _isa(err, c):
                handler = cb
                break
            if is_re and c.search(string):
                handler = cb
                break
        if handler is not None:
            break

    # Rethrow if no handler could be found
    if (handler := handler or default) is None:
        raise err if isinstance(err, BaseException) else Pyjo_Exception(err)
    handler(err)

    return True


def throw(first: Anything, *rest: Anything) -> NoReturn:
    """::

        throw('Something went wrong!')
        throw('MyApp.X.Foo', 'Something went wrong!')
        throw(MyApp_X_Foo, 'Something went wrong!')

    Raise a :mod:`Pyjo.Exception`, if the class does not exist yet, one is
    created as a :mod:`Pyjo.Exception` subclass on demand. ``raise_`` is an
    alias, the name of Mojolicious with an underscore.
    """
    # Renamed from Mojolicious: raise, a keyword of Python
    name, err = (first, rest[0]) if len(rest) else (Pyjo_Exception, first)
    cls = _class(name) if isinstance(name, str) else name
    if not (isinstance(cls, type) and issubclass(cls, Pyjo_Exception)):
        raise TypeError(f'{_name(name)} is not a Pyjo.Exception subclass')
    raise cls.new(err).trace(2)


# The name of Mojolicious, with an underscore as raise is a keyword of Python
raise_ = throw


# Mojo makes the class with eval
def _class(name: str) -> Anything:
    if name in _CLASSES:
        return _CLASSES[name]

    # The longest prefix that is a module, and the rest its attributes
    parts = name.split('.')
    for i in range(len(parts) - 1, 0, -1):
        try:
            found: Anything = importlib.import_module('.'.join(parts[:i]))
        except ImportError:
            continue
        try:
            for attr in parts[i:]:
                found = getattr(found, attr)
        except AttributeError:
            break
        return found

    module, _, qualname = name.rpartition('.')
    cls = type(qualname, (Pyjo_Exception,), {'__module__': module or __name__, '__qualname__': qualname})
    _CLASSES[name] = cls
    return cls


_CLASSES: dict[str, type[Pyjo_Exception]] = {}


def _isa(err: Anything, cls: Pattern) -> bool:
    if isinstance(cls, type):
        return isinstance(err, cls)
    return any(cls in (c.__qualname__, f'{c.__module__}.{c.__qualname__}') for c in type(err).__mro__)


def _line(line: bytes | str) -> str:
    if isinstance(line, bytes):
        decoded = decode('UTF-8', line)
        line = decoded if decoded is not None else line.decode('latin-1')
    return line[:-1] if line.endswith('\n') else line


def _name(cls: Anything) -> str:
    if isinstance(cls, type):
        return f'{cls.__module__}.{cls.__qualname__}'
    return str(cls)


# Perl's split /\n/, which drops the empty lines at the end
def _split(source: str) -> list[str]:
    lines = source.split('\n')
    while len(lines) and lines[-1] == '':
        lines.pop()
    return lines


new = Pyjo_Exception.new
object = Pyjo_Exception
