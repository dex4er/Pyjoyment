r"""
Pyjo.Test - Writing test scripts
================================
::

    from Pyjo.Test import *

    import os

    if not os.getenv('TEST_ONLINE'):
        plan(skip_all='set TEST_ONLINE to enable this test')

    ok(got == expected, 'test name')

    is_ok(got, expected, 'test name')
    isnt_ok(got, unexpected, 'test name')
    like_ok(got, r'expected', 'test name')
    unlike_ok(got, r'unexpected', 'test name')
    cmp_ok(got, '==', expected, 'test name')
    is_deeply_ok(got_complex_structure, expected_complex_structure, 'test name')
    isa_ok(obj, cls)
    throws_ok(lambda: int('x'), ValueError, 'test name')

    with subtest('Parse'):
        is_ok(url.host, 'example.com', 'right host')

    @subtest('Format')
    def _():
        is_ok(str(url), 'http://example.com', 'right format')

    diag("here's what went wrong")
    note('what happens next')

    done_testing()

:mod:`Pyjo.Test` is a module for writing test scripts which print their results
in the `Test Anything Protocol <https://testanything.org/>`_ (TAP). It is
inspired by Perl's ``Test::More``, which the tests of Mojolicious are written
with, but it is not a port of it.

Each test script is a separate Python program, usually placed in the ``t``
directory.

Running tests
-------------

The test scripts run with :mod:`Pyjo.Prove`: ::

    $ python -m Pyjo.Prove -I . -r t

or with Perl's ``prove``, as they print standard TAP: ::

    $ PYTHONPATH=. prove --ext=py --exec=python -r t

A single script runs on its own as well: ::

    $ PYTHONPATH=. python t/Pyjo/URL.py

Plans
-----

A test script declares how many tests it runs, either up front with
:func:`plan` or at the end with :func:`done_testing`. A script that runs tests
without a plan fails.

Subtests
--------

A subtest groups tests under a name. Its tests are numbered on their own and
printed indented, and the subtest as a whole counts as one test of its parent,
which passes when all of its tests pass. :func:`subtest` works as a context
manager, as a decorator which runs the function at once, and as a function
which runs a callback: ::

    with subtest('Simple'):
        ok(True, 'first')

    @subtest('Decorated')
    def _():
        ok(True, 'second')

    subtest('Callback', lambda: ok(True, 'third'))

A subtest has an implicit :func:`done_testing`. ``plan(skip_all=...)`` skips
the rest of the subtest, and a subtest that runs no tests fails.

Exit status
-----------

The exit status of a test script is ``0`` when every test passed, the number of
failed tests (up to 254), ``254`` when tests ran without a plan, and ``255``
when the number of tests does not match the plan, when the script died with an
exception, or after :func:`bail_out`.

Functions
---------
"""

import atexit
import inspect
import os
import re
import sys

from collections.abc import Callable
from dataclasses import dataclass
from types import TracebackType
from typing import Any, NoReturn, Self, TextIO, cast, overload


__all__ = [
    'bail_out',
    'cmp_ok',
    'diag',
    'done_testing',
    'fail_ok',
    'in_ok',
    'is_deeply_ok',
    'is_ok',
    'isa_ok',
    'isnt_ok',
    'like_ok',
    'none_ok',
    'not_in_ok',
    'note',
    'ok',
    'pass_ok',
    'plan',
    'plan_skip_all',
    'plan_tests',
    'skip',
    'subtest',
    'throws_ok',
    'unlike_ok',
]


class Error(Exception):
    """
    Exception raised for a misuse of the test functions, for example planning
    twice.
    """


class SkipAll(Exception):
    """
    Exception raised by ``plan(skip_all=...)`` inside a subtest, to leave it.
    It is caught by :func:`subtest`.
    """


@dataclass
class _State:
    name: str | None = None
    depth: int = 0
    count: int = 0
    failed: int = 0
    planned: int | None = None
    done: bool = False
    skip_all: str | None = None


@dataclass
class _Step:
    kind: str | None
    idx: object
    got: object
    expected: object


# Any: comparisons and regular expressions take whatever the tested code
# returns, str or bytes, and a mismatch is a failed test, not a type error.
type _Pattern = str | bytes | re.Pattern[Any] | tuple[str | bytes, str]

_stack: list[_State] = [_State()]
_used = False
_died = False
_bailed_out = False


def bail_out(reason: str = '') -> NoReturn:
    """::

        if not connected:
            bail_out('No database connection')

    Stop all testing at once, here and in the test harness, which shows the
    reason. The exit status is ``255``.
    """
    global _bailed_out
    _use()
    _bailed_out = True
    _print(f'Bail out!  {reason}', depth=0)
    sys.exit(255)


def cmp_ok(got: Any, operator: str, expected: Any, test_name: str | None = None) -> bool:
    """::

        # ok(got == expected)
        cmp_ok(got, '==', expected, 'this == that')

    Compare two values with a binary operator: ``==``, ``!=``, ``<``, ``<=``,
    ``>``, ``>=``, ``is``, ``is not``, ``in`` or ``not in``. The test passes if
    the comparison is true.
    """
    operators: dict[str, Callable[[Any, Any], bool]] = {
        '==': lambda a, b: a == b,
        '!=': lambda a, b: a != b,
        '<': lambda a, b: a < b,
        '<=': lambda a, b: a <= b,
        '>': lambda a, b: a > b,
        '>=': lambda a, b: a >= b,
        'is': lambda a, b: a is b,
        'is not': lambda a, b: a is not b,
        'in': lambda a, b: a in b,
        'not in': lambda a, b: a not in b,
    }
    if operator not in operators:
        raise Error(f'Unknown operator {operator!r}')
    check = operators[operator](got, expected)
    _ok(check, test_name)
    if not check:
        _diag_lines([f'    {got!r}', f'        {operator}', f'    {expected!r}'])
    return check


def diag(*messages: object) -> bool:
    """::

        if not in_ok(users, 'foo', "There's a foo user"):
            diag("Since there's no foo, check that /etc/bar is set up right")

    Print a diagnostic message to the standard error, which does not interfere
    with the test output. Returns ``False``, so a failure is preserved.
    """
    _use()
    _diag_lines(''.join(str(m) for m in messages).split('\n'))
    return False


def done_testing(how_many: int | None = None) -> bool:
    """::

        ok(True)
        done_testing()

        ok(True)
        done_testing(1)

    Issue the plan when the tests are done, instead of declaring it up front
    with :func:`plan`. The number of tests is optional; when it is given, it
    has to match the number of tests run.
    """
    _use()
    state = _current()

    if state.done:
        return fail_ok('done_testing() was already called')

    if state.planned is not None and how_many is not None and how_many != state.planned:
        fail_ok(f'planned to run {state.planned} but done_testing() expects {how_many}')

    if state.planned is None:
        state.planned = state.count if how_many is None else how_many
        _print(f'1..{state.planned}')

    state.done = True
    return _finish(state)


def fail_ok(test_name: str | None = None) -> bool:
    """::

        fail_ok('This should not happen')

    A test that always fails, the same as ``ok(False)``.
    """
    return _ok(False, test_name)


def in_ok(got: Any, elem: object, test_name: str | None = None) -> bool:
    """::

        in_ok(['foo', 'bar'], 'foo', 'foo is in the list')

    Check if the element is in the container. The same as
    ``ok(elem in got)``, with a better diagnostic message.
    """
    try:
        check = elem in got
    except TypeError:
        check = False
    _ok(check, test_name)
    if not check:
        _diag_lines([f'         got: {got!r}', f'    expected: to contain {elem!r}'])
    return check


def is_deeply_ok(got: object, expected: object, test_name: str | None = None) -> bool:
    """::

        is_deeply_ok([[1, 2], [3, [4, 5]]], [[1, 2], [3]], 'deep structure')

    Compare two data structures, walking through lists, tuples, sets and
    dicts. If they differ, the diagnostic message shows where they start
    differing.
    """
    if _is_container(got) and _is_container(expected):
        stack: list[_Step] = []
        check = _deep_check(stack, got, expected)
        _ok(check, test_name)
        if not check:
            _diag_lines(_format_stack(stack))
    else:
        check = got == expected
        _ok(check, test_name)
        if not check:
            _diag_lines([f'         got: {got!r}', f'    expected: {expected!r}'])
    return check


def is_ok(got: object, expected: object, test_name: str | None = None) -> bool:
    """::

        is_ok(ultimate_answer(), 42, 'meaning of life')

    Compare two values with ``==``.
    """
    check = got == expected
    _ok(check, test_name)
    if not check:
        _diag_lines([f'         got: {got!r}', f'    expected: {expected!r}'])
    return check


def isa_ok(got: object, cls: type | tuple[type, ...], test_name: str | None = None) -> bool:
    """::

        obj = SomeClass()
        isa_ok(obj, SomeClass)
        isa_ok(123, (int, float))

    Check if the object is an instance of the class, or of one of the classes.
    """
    if test_name is None:
        test_name = f'An object of class {type(got).__name__!r} isa {_class_names(cls)!r}'
    check = isinstance(got, cls)
    _ok(check, test_name)
    if not check:
        _diag_lines([f'    The object of class {type(got).__name__!r} is not a {_class_names(cls)!r}'])
    return check


def isnt_ok(got: object, expected: object, test_name: str | None = None) -> bool:
    """::

        isnt_ok(foo, '', 'got some foo')

    Compare two values with ``!=``.
    """
    check = got != expected
    _ok(check, test_name)
    if not check:
        _diag_lines([f'         got: {got!r}', '    expected: anything else'])
    return check


def like_ok(got: Any, expected: _Pattern, test_name: str | None = None) -> bool:
    """::

        like_ok(got, r'expected', 'test name')
        like_ok(got, (r'expected', 'i'), 'test name')
        like_ok(got, re.compile(r'expected'), 'test name')

    Check if the value matches the regular expression. The expression can be
    compiled already, or given with flags as a tuple: ``a``, ``i``, ``m``,
    ``s`` and ``x``.
    """
    regex = _regex(expected)
    try:
        check = regex.search(got) is not None
    except TypeError:
        check = False
    _ok(check, test_name)
    if not check:
        _diag_lines([f'                  {got!r}', f"    doesn't match {regex.pattern!r}"])
    return check


def none_ok(got: object, test_name: str | None = None) -> bool:
    """::

        none_ok(req.headers.transfer_encoding, 'no "Transfer-Encoding" value')

    Check if the value is ``None``.
    """
    check = got is None
    _ok(check, test_name)
    if not check:
        _diag_lines([f'         got: {got!r}', '    expected: None'])
    return check


def not_in_ok(got: Any, elem: object, test_name: str | None = None) -> bool:
    """::

        not_in_ok(os.environ, 'DISPLAY', 'DISPLAY is not set')

    The opposite of :func:`in_ok`: check if the element is not in the
    container.
    """
    try:
        check = elem not in got
    except TypeError:
        check = False
    _ok(check, test_name)
    if not check:
        _diag_lines([f'         got: {got!r}', f'    expected: not to contain {elem!r}'])
    return check


def note(*messages: object) -> None:
    """::

        note(f'Tempfile is {tempfile}')

    Print a message to the standard output as a TAP comment, which the test
    harness hides unless asked to show it.
    """
    _use()
    for line in ''.join(str(m) for m in messages).split('\n'):
        _print(f'# {line}' if line else '#')


def ok(check: object, test_name: str | None = None) -> bool:
    """::

        ok(3**4 == 81, 'simple exponential')
        ok(isinstance(film, Film), 'set_db()')
        ok(None not in items, 'all items defined')

    The basic test: it passes if the value is true and fails otherwise.
    Returns whether the test passed.
    """
    return _ok(check, test_name)


def pass_ok(test_name: str | None = None) -> bool:
    """::

        pass_ok('step 1')

    A test that always passes, the same as ``ok(True)``.
    """
    return _ok(True, test_name)


def plan(tests: int | None = None, skip_all: str | None = None) -> bool:
    """::

        plan(tests=3)

        if not os.getenv('TEST_ONLINE'):
            plan(skip_all='set TEST_ONLINE to enable this test')

    Declare how many tests the script is going to run, which protects against
    a premature exit, or skip all of them with a reason. In a subtest,
    ``skip_all`` skips the rest of the subtest.
    """
    _use()
    state = _current()

    if state.planned is not None or state.done:
        raise Error('You tried to plan twice')

    if skip_all is not None:
        state.skip_all = skip_all
        state.planned = 0
        state.done = True
        _print(f'1..0 # SKIP {skip_all}')
        if state.depth:
            raise SkipAll(skip_all)
        sys.exit(0)

    if tests is None:
        raise Error('plan() needs either tests or skip_all')

    state.planned = tests
    _print(f'1..{tests}')
    return True


def plan_skip_all(why: str) -> bool:
    """::

        plan_skip_all('set TEST_ONLINE to enable this test')

    The same as ``plan(skip_all=why)``.
    """
    return plan(skip_all=why)


def plan_tests(how_many: int) -> bool:
    """::

        plan_tests(3)

    The same as ``plan(tests=how_many)``.
    """
    return plan(tests=how_many)


def skip(why: str | None = None, how_many: int = 1) -> bool:
    """::

        if os.getenv('TEST_ONLINE'):
            ok(Pyjo.UserAgent.new().get('https://mojolicious.org').result.is_success, 'online request')
        else:
            skip('set TEST_ONLINE to enable this test', 1)

    Skip the given number of tests, which still count for the plan.
    """
    _use()
    state = _current()
    for _ in range(how_many):
        state.count += 1
        _print(f'ok {state.count} # skip {why}' if why is not None else f'ok {state.count} # skip')
    return True


class Subtest:
    """
    A subtest, returned by :func:`subtest` without a callback. It is a context
    manager and a decorator; after it ends, :attr:`passed` tells whether all
    of its tests passed.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.passed: bool | None = None

    def __call__[F: Callable[[], object]](self, fn: F) -> F:
        with self:
            fn()
        return fn

    def __enter__(self) -> Self:
        _use()
        _print(f'# Subtest: {self.name}')
        _stack.append(_State(self.name, _current().depth + 1))
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> bool:
        state = _current()

        if exc_type is not None and issubclass(exc_type, SystemExit):
            _stack.pop()
            return False

        if exc_type is not None and issubclass(exc_type, SkipAll):
            _stack.pop()
            self.passed = True
            skip(state.skip_all)
            return True

        name = self.name
        if exc_type is not None:
            if state.planned is None:
                state.planned = state.count
                _print(f'1..{state.planned}')
            self.passed = False
        elif state.count == 0 and state.planned is None and not state.done:
            _print('1..0')
            _diag_lines(['No tests run!'], stream=sys.stdout)
            name = f'No tests run for subtest "{self.name}"'
            self.passed = False
        elif state.done:
            self.passed = _passed(state)
        else:
            state.done = True
            if state.planned is None:
                state.planned = state.count
                _print(f'1..{state.planned}')
            self.passed = _finish(state)

        _stack.pop()
        _ok(self.passed, name)
        return False


@overload
def subtest(name: str, fn: None = None) -> Subtest: ...


@overload
def subtest(name: str, fn: Callable[[], object]) -> bool: ...


def subtest(name: str, fn: Callable[[], object] | None = None) -> Subtest | bool:
    """::

        with subtest('Parse'):
            ok(True)

        @subtest('Parse')
        def _():
            ok(True)

        passed = subtest('Parse', lambda: ok(True))

    Run a group of tests as a single test of the parent. Without a callback it
    returns a :class:`Subtest`, which works as a context manager and as a
    decorator; with a callback it runs it at once and returns whether the
    subtest passed.
    """
    test = Subtest(name)
    if fn is None:
        return test
    test(fn)
    return bool(test.passed)


def throws_ok(
    cb: Callable[[], object], expected: type[BaseException] | str | re.Pattern[str], test_name: str | None = None
) -> bool:
    """::

        throws_ok(lambda: [1, 2, 3][3], IndexError, 'no more elements')
        throws_ok(lambda: int('x'), "invalid literal for int() with base 10: 'x'", 'right message')
        throws_ok(lambda: int('x'), re.compile(r'invalid literal'), 'right message')

    Check if the callback raises an exception: of the given class, with the
    given message, or with a message matching the regular expression.
    """
    got = None
    check = False

    # The expected class, also one that is not an Exception, as SystemExit, but no other BaseException
    catch = (Exception, expected) if isinstance(expected, type) else Exception
    try:
        cb()
    except catch as e:
        if isinstance(expected, type):
            got = type(e).__name__
            check = isinstance(e, expected)
        elif isinstance(expected, re.Pattern):
            got = str(e)
            check = bool(expected.search(got))
        else:
            got = str(e)
            check = got == expected

    if isinstance(expected, type):
        expected = expected.__name__
    elif isinstance(expected, re.Pattern):
        expected = f'a message matching {expected.pattern!r}'

    _ok(check, test_name)
    if not check:
        _diag_lines([f'         got: {got if got is not None else "no exception"}', f'    expected: {expected}'])
    return check


def unlike_ok(got: Any, expected: _Pattern, test_name: str | None = None) -> bool:
    """::

        unlike_ok(got, r'unexpected', 'test name')

    The opposite of :func:`like_ok`: check if the value does not match the
    regular expression.
    """
    regex = _regex(expected)
    try:
        check = regex.search(got) is None
    except TypeError:
        check = True
    _ok(check, test_name)
    if not check:
        _diag_lines([f'                  {got!r}', f'          matches {regex.pattern!r}'])
    return check


class _DoesNotExist:
    def __repr__(self) -> str:
        return 'Does not exist'


_DOES_NOT_EXIST = _DoesNotExist()

_FLAGS: dict[str, re.RegexFlag] = {
    'a': re.ASCII,
    'i': re.IGNORECASE,
    'm': re.MULTILINE,
    's': re.DOTALL,
    'x': re.VERBOSE,
}


def _at_exit() -> None:
    if not _used:
        return

    state = _stack[0]

    if _bailed_out:
        code = 255
    elif state.skip_all is not None:
        code = 0
    elif _died:
        _diag_lines([f'Looks like your test exited with 255 just after {state.count}.'], depth=0)
        code = 255
    elif state.planned is None:
        _diag_lines(['Tests were run but no plan was declared and done_testing() was not seen.'], depth=0)
        code = 254
    else:
        if not state.done:
            _finish(state)
        if state.count != state.planned:
            code = 255
        else:
            code = min(state.failed, 254)

    if code:
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(code)


def _class_names(cls: type | tuple[type, ...]) -> str:
    if isinstance(cls, tuple):
        return ', '.join(c.__name__ for c in cls)
    return cls.__name__


def _caller() -> str | None:
    frame = inspect.currentframe()
    while frame is not None and frame.f_code.co_filename == __file__:
        frame = frame.f_back
    if frame is None:
        return None
    return f'{frame.f_code.co_filename} line {frame.f_lineno}'


def _current() -> _State:
    return _stack[-1]


def _deep_check(stack: list[_Step], e1: object, e2: object) -> bool:
    step = _Step(None, None, e1, e2)

    if e1 is e2:
        return True

    if isinstance(e1, list) and isinstance(e2, list):
        return _eq_sequence(stack, 'list', cast(list[object], e1), cast(list[object], e2))

    if isinstance(e1, tuple) and isinstance(e2, tuple):
        return _eq_sequence(stack, 'tuple', cast(tuple[object, ...], e1), cast(tuple[object, ...], e2))

    if isinstance(e1, set) and isinstance(e2, set):
        return _eq_sequence(
            stack, 'set', sorted(cast(set[object], e1), key=repr), sorted(cast(set[object], e2), key=repr)
        )

    if isinstance(e1, dict) and isinstance(e2, dict):
        return _eq_dict(stack, cast(dict[object, object], e1), cast(dict[object, object], e2))

    if e1 is not None and e2 is not None and e1 == e2:
        return True

    stack.append(step)
    return False


def _diag_lines(lines: list[str], stream: TextIO | None = None, depth: int | None = None) -> None:
    _print(*[f'# {line}' if line else '#' for line in lines], stream=stream or sys.stderr, depth=depth)


def _eq_dict(stack: list[_Step], h1: dict[object, object], h2: dict[object, object]) -> bool:
    for k in sorted(set(h1) | set(h2), key=repr):
        e1 = h1.get(k, _DOES_NOT_EXIST)
        e2 = h2.get(k, _DOES_NOT_EXIST)
        stack.append(_Step('dict', k, e1, e2))
        if not _deep_check(stack, e1, e2):
            return False
        stack.pop()
    return True


def _eq_sequence(
    stack: list[_Step], kind: str, a1: list[object] | tuple[object, ...], a2: list[object] | tuple[object, ...]
) -> bool:
    for i in range(max(len(a1), len(a2))):
        e1 = a1[i] if i < len(a1) else _DOES_NOT_EXIST
        e2 = a2[i] if i < len(a2) else _DOES_NOT_EXIST
        stack.append(_Step(kind, i, e1, e2))
        if not _deep_check(stack, e1, e2):
            return False
        stack.pop()
    return True


def _except_hook(exc_type: type[BaseException], exc_value: BaseException, traceback: TracebackType | None) -> None:
    global _died
    _died = True
    _original_except_hook(exc_type, exc_value, traceback)


def _finish(state: _State) -> bool:
    if state.skip_all is None:
        if state.count != state.planned:
            _diag_lines([f'Looks like you planned {_tests(state.planned)} but ran {state.count}.'])
        elif state.failed:
            _diag_lines([f'Looks like you failed {_tests(state.failed)} of {state.count}.'])
        elif not state.count:
            _diag_lines(['No tests run!'])
    return _passed(state)


def _format_stack(stack: list[_Step]) -> list[str]:
    path = ''
    for step in stack:
        if step.kind in ('list', 'tuple', 'dict'):
            path += f'[{step.idx!r}]'
        elif step.kind == 'set':
            path = f'sorted({path or "x"})[{step.idx!r}]'

    got, expected = stack[-1].got, stack[-1].expected
    return [
        '    Structures begin differing at:',
        f'         got{path} = {got!r}',
        f'    expected{path} = {expected!r}',
    ]


def _is_container(value: object) -> bool:
    return isinstance(value, (list, tuple, set, dict))


def _ok(check: object, test_name: str | None = None) -> bool:
    _use()
    state = _current()
    state.count += 1
    check = bool(check)

    line = f'ok {state.count}' if check else f'not ok {state.count}'
    if test_name is not None:
        if str(test_name).isdigit():
            _diag_lines(
                [
                    f"    You named your test '{test_name}'.  You shouldn't use numbers for your test names.",
                    '    Very confusing.',
                ]
            )
        line += ' - ' + str(test_name).replace('#', '\\#')
    _print(line)

    if not check:
        state.failed += 1
        where = _caller()
        failed = f"  Failed test '{test_name}'" if test_name is not None else '  Failed test'
        _diag_lines([failed, f'  at {where}.'] if where else [failed])

    return check


def _passed(state: _State) -> bool:
    if state.skip_all is not None:
        return True
    return state.count == state.planned and not state.failed and state.count > 0


def _print(*lines: str, stream: TextIO | None = None, depth: int | None = None) -> None:
    stream = stream or sys.stdout
    if stream is None:
        return
    indent = '    ' * (_current().depth if depth is None else depth)
    text = ''.join(f'{indent}{line}\n' for line in lines)
    encoding = getattr(stream, 'encoding', None)
    if not encoding or encoding.lower().replace('-', '') != 'utf8':
        text = text.encode('ascii', 'backslashreplace').decode('ascii')
    if stream is sys.stderr:
        sys.stdout.flush()
    stream.write(text)
    stream.flush()


def _regex(expected: _Pattern) -> re.Pattern[Any]:
    if isinstance(expected, re.Pattern):
        return expected
    flags = 0
    if isinstance(expected, (list, tuple)):
        expected, letters = expected
        for letter in letters:
            flags |= _FLAGS[letter]
    return re.compile(expected, flags)


def _tests(n: int | None) -> str:
    return f'{n} test' if n == 1 else f'{n} tests'


def _use() -> None:
    global _used
    _used = True


_original_except_hook = sys.excepthook
sys.excepthook = _except_hook
atexit.register(_at_exit)
