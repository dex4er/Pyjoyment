"""
Pyjo.Test - Simple writing of test scripts
==========================================
::

    from Pyjo.Test import *  # noqa

    if not have_some_feature:
        plan_skip_all(why)
    else:
        plan_tests(number_of_tests_run)

    ok(got == expected, test_name)

    is_ok(got, expected, test_name)
    isnt_ok(got, expected, test_name)

    diag("here's what went wrong")

    like_ok(got, r'expected', r_flags, test_name)
    unlike_ok(got, r'expected', r_flags, test_name)

    cmp_ok(got, '==', expected, test_name)

    is_deeply_ok(got_complex_structure, expected_complex_structure, test_name)

    if not have_some_feature:
        skip(why, how_many)
    else:
        ok(foo(), test_name)
        is_ok(foo(42), 23, test_name)

    isa_ok(obj, cls)

    pass_ok(test_name)
    fail_ok(test_name)

    done_testing()

This is a module for writing a test scripts which return theirs results as
a `Test Anything Protocol <http://testanything.org/>`_ (TAP) output.

Each test script is a separate Python program which usually is placed in `t`
subdirectory.

prove
-----

The test scripts can be started with ``prove`` command: ::

    $ PYTHONPATH=. prove --ext=py --exec=python t

You can also put the arguments in the configuration file ``.proverc``: ::

    --ext=py
    --exec=python

``prove`` requires that ``__init__.py`` files have to be also runnable scripts.
For example: ::

    if __name__ == '__main__':
        from Pyjo.Test import *  # noqa
        pass_ok('__init__')
        done_testing()

nosetests
---------

The test scripts can be started with ``nosetests`` command: ::

    $ PYTHONPATH=`pwd` nosetests --where=t --match=. --attr=test_nose

You can also put the arguments in the configuration file ``setup.cfg``: ::

    [nosetests]
    where=t
    match=.
    attr=test_nose

``nosetests`` command requires additional boilerplate code in test script: ::

    import Pyjo.Test

    class NoseTest(Pyjo.Test.NoseTest):
        script = __file__
        srcdir = '../..'

    if __name__ == '__main__':
        from Pyjo.Test import *  # noqa
        ok('main test script')
        ...

unittest
--------

The test scripts can be started with ``python -m unittest`` command: ::

    $ PYTHONPATH=. python -m unittest discover -s t -p '*.py'

``unittest`` module does not discover test script in subdirectories so it have
to be used for each subdirectory separately: ::

    $ PYTHONPATH=. python -m unittest discover -s t/subdir1 -p '*.py'
    $ PYTHONPATH=. python -m unittest discover -s t/subdir2 -p '*.py'

``unittest`` module requires additional boilerplate code in test script: ::

    import Pyjo.Test

    class UnitTest(Pyjo.Test.UnitTest):
        script = __file__

    if __name__ == '__main__':
        from Pyjo.Test import *  # noqa
        ok('main test script')
        ...

setuptools
----------

The test scripts can be started with ``python setup.py test`` command. ::

    $ python setup.py test

Additional helper script ``test.py`` is required in the source directory of
the package: ::

    #!/usr/bin/env python

    import unittest

    dirs = ['t']

    class TestSuite(unittest.TestSuite):
        def __init__(self, *args, **kwargs):
            super(TestSuite, self).__init__(*args, **kwargs)
            test_loader = unittest.defaultTestLoader
            for d in dirs:
                test_suite = test_loader.discover(d, pattern='*.py', top_level_dir='.')
                for t in test_suite:
                    self.addTest(t)

        def __iter__(self):
            return iter(self._tests)

    if __name__ == '__main__':
        unittest.main(defaultTest='TestSuite')

The ``setup.py`` script should set additional options: ::

    setup(
        packages=find_packages(exclude=['t', 't.*']),
        test_suite='test.TestSuite',
        ...
    )

Classes and functions
---------------------
"""

import os
import re
import subprocess
import sys
import traceback
import unittest


__all__ = [
    'cmp_ok',
    'done_testing',
    'diag',
    'fail_ok',
    'in_ok',
    'is_ok',
    'isa_ok',
    'is_deeply_ok',
    'isnt_ok',
    'like_ok',
    'none_ok',
    'not_in_ok',
    'ok',
    'pass_ok',
    'plan_tests',
    'plan_skip_all',
    'skip',
    'throws_ok',
    'unlike_ok',
]


done = False
failed = 0
test = 0
tests = 0


def cmp_ok(got, operator, expected, test_name=None):
    """::

        # ok(got == expected)
        cmp_ok(got, '==', expected, 'this == that')

    Compare two arguments using binary Python operator (``==``, ``>=``,
    ``>``, ``<=``, ``<`` or ``!=``). The test passes if the comparison
    is true and fails otherwise.
    """
    if test_name is None:
        test_name = f'An object {type(got)}'
    test_name = f'{test_name} {operator} {repr(expected)}'
    methods = {
        '==': lambda a, b: a == b,
        '>=': lambda a, b: a >= b,
        '>': lambda a, b: a > b,
        '<=': lambda a, b: a <= b,
        '<': lambda a, b: a < b,
        '!=': lambda a, b: a != b,
    }
    check = methods[operator](got, expected)
    _ok(check, test_name)
    if not check:
        diag(f'    {repr(got)}\n        {operator}\n    {repr(expected)}\n')
    return check


def diag(*args):
    """::

        if not in_ok(users, 'foo', "There's a foo user"):
            diag("Since there's no foo, check that /etc/bar is set up right")

    Print a diagnostic message which is guaranteed not to interfere with test
    output.

    Returns false, so as to preserve failure.
    """
    _print('# ' + '\n# '.join(''.join(args).split('\n')), file=sys.stderr)
    return False


def done_testing(how_many=None):
    """::

        plan(1)
        ok(True)
        done_testing(1)

    Issue the plan when it's done running tests. It fails when plan doesn't
    match this one in :func:`plan`. The plan is optional and any number of
    tests is accepted if plan is ``None``.
    """
    global done, failed, test, tests

    if done:
        fail_ok('done_testing() was already called')
        return

    if tests and how_many:
        fail_ok(f'planned to run {tests} but done_testing() expects {how_many}')
        return

    if not tests:
        tests = test
        _print(f'1..{tests}')

    if not tests:
        diag('No tests run!')
        failed = 255

    if failed:
        sys.exit(failed)

    done = True
    return True


def fail_ok(test_name=None):
    """::

        fail_ok("This should not happen")

    The synonym for ``ok(False)``.
    """
    return _ok(False, test_name)


def in_ok(got, elem, test_name=None):
    """::

        in_ok(['foo', 'bar'], 'foo', "foo is in list")

    Check if element exists in given object. The same as ``ok(elem in got)``,
    but with more meaningful diagnostic message.
    """
    if test_name is None:
        test_name = f'an object {type(got)}'
    test_name = f'{repr(elem)} is in {test_name}'
    try:
        check = elem in got
    except TypeError:
        check = False
    _ok(check, test_name)
    if not check:
        diag(f'         got: {repr(got)}')
    return check


def is_deeply_ok(got, expected, test_name=None):
    """::

        is_deeply_ok([[1,2], [3, [4,5]]], [[1,2], [3]], "deep structure")

    Do a deep comparison walking each data structure to see if they are
    equivalent. If the two structures are different, it will display the place
    where they start differing.
    """
    test_name = f'{test_name} is {repr(expected)}'
    if isinstance(got, (list, tuple, set, dict)) and isinstance(expected, (list, tuple, set, dict)):
        stack = []
        check = _deep_check(stack, got, expected)
        _ok(check, test_name)
        if not check:
            diag(_format_stack(stack))
    else:
        check = got == expected
        _ok(check, test_name)
        if not check:
            diag(f'         got: {repr(got)}\n    expected: {repr(expected)}')
    return check


def is_ok(got, expected, test_name=None):
    """::

        is_ok(ultimate_answer(), 42, "Meaning of Life")

    Compare two arguments with '==' operator.
    """
    if test_name is None:
        test_name = f'An object {type(got)}'
    test_name = f'{test_name} is {repr(expected)}'
    check = got == expected
    _ok(check, test_name)
    if not check:
        diag(f'         got: {repr(got)}\n    expected: {repr(expected)}\n')
    return check


def isa_ok(got, cls, test_name=None):
    """::

        obj = SomeClass()
        isa_ok(obj, SomeClass)
        isa_ok(123, (int, float,))

    Check if object is an instance of class or one of the classes.
    """
    if test_name is None:
        test_name = f'An object {type(got)}'
    test_name = f'{test_name} is object {cls}'
    check = isinstance(got, cls)
    _ok(check, test_name)
    return check


def isnt_ok(got, expected, test_name=None):
    """::

        isnt(foo, '', "Got some foo")

    Compare two arguments with '!=' operator.
    """
    if test_name is None:
        test_name = f'An object {type(got)}'
    test_name = f'{test_name} is {repr(expected)}'
    check = got != expected
    _ok(check, test_name)
    if not check:
        diag(f'         got: {repr(got)}\n    expected: anything else\n')
    return check


_type_regex = type(re.compile(''))


def like_ok(got, expected, test_name=None):
    """::

        like_ok(got, 'expected', test_name)
        like_ok(got, ('expected', 'i'), test_name)
        like_ok(got, re.compile('expected'), test_name)

    Check if value matches against the regex. The regex can be already
    compiled as a :mod:re object.

    The regex can compiled with additional flags: ``d``, ``i``,
    ``m``, ``s``, ``u`` and ``x`` as a second element of list or tuple.
    """
    FLAGS = {
        'd': re.DEBUG,
        'i': re.IGNORECASE,
        'l': re.LOCALE,
        'm': re.MULTILINE,
        's': re.DOTALL,
        'u': re.UNICODE,
        'x': re.VERBOSE,
    }
    if isinstance(expected, _type_regex):
        regex = expected
        regex_repr = f're.compile({repr(regex.pattern)}, {regex.flags})'
    else:
        re_flags = 0
        if isinstance(expected, (list, tuple)) and len(expected) > 1:
            for c in expected[1]:
                re_flags |= FLAGS[c]
            expected = expected[0]
        regex = re.compile(expected, re_flags)
        regex_repr = f're.compile({repr(expected)}, {re_flags})'
    if test_name is None:
        test_name = f'An object {type(got)}'
    test_name = f'{test_name} matches {regex_repr}'
    try:
        check = bool(regex.search(got))
    except:
        check = False
    _ok(check, test_name)
    if not check:
        diag(f"                {repr(got)}\n  doesn't match {regex}\n")
    return check


def none_ok(got, test_name=None):
    """::

        none_ok(req.headers.transfer_encoding, "no Transfer-Encoding value")

    Check if value is ``None``.
    """
    if test_name is None:
        test_name = f'An object {type(got)} is None'
    else:
        test_name = f'{test_name} is None'
    check = got is None
    _ok(check, test_name)
    return check


def not_in_ok(got, elem, test_name=None):
    """::

        import os
        not_in_ok(os.environ, 'DISPLAY', "DISPLAY is not set")

    The same as :func:`in_ok`, only it checks if element does not exists in
    given object.
    """
    if test_name is None:
        test_name = f'an object {type(got)}'
    test_name = f'{repr(elem)} is not in {test_name}'
    try:
        check = elem not in got
    except TypeError:
        check = False
    _ok(check, test_name)
    if not check:
        diag(f'         got: {repr(got)}')
    return check


def ok(check, test_name=None):
    """::

        ok(exp(9) == 81, "simple exponential")
        ok(isinstance('db_Main', Film), "set_db()")
        ok(p.tests == 4, "saw tests")
        ok(None not in items, "all items defined")

    This simply evaluates any expression and uses that to determine if the
    test succeeded or failed. A true expression passes, a false one fails.
    """
    return _ok(check, test_name)


def pass_ok(test_name=None):
    """::

        pass_ok("Step 1")

    The synonym for ``ok(True)``.
    """
    return _ok(True, test_name)


def plan_tests(how_many):
    """::

        hosts = ['pyjoyment.net', 'pypi.python.org']
        plan_tests(len(hosts))
        for host in hosts:
            ok(check_if_available(host))

    Declare how many tests script is going to run to protect against
    premature failure.

    The plan can be also issued when it's done running tests.
    Then :func:`done_testing` function should be used instead.
    """
    global done, failed, test, tests
    tests = how_many
    _print(f'1..{tests}')
    return True


def plan_skip_all(why):
    """::

        import os
        if not os.getenv('TEST_ONLINE'):
            plan_skip_all("set TEST_ONLINE to enable this test")

    Completely skip an entire testing script.
    """
    global done, failed, test, tests
    if tests:
        print('# You tried to plan twice', file=sys.stderr)
        exit()
    else:
        _print(f'1..0 # SKIP {why}')
        done = True
        test = 255
        exit()


def skip(why=None, how_many=1):
    """::

        plan_tests(1)
        if os.getenv('TEST_ONLINE'):
            ok(Pyjo.UserAgent.new().get('https://mojolicious.org').success, "online request")
        else:
            skip("set TEST_ONLINE to enable this test", 1)

    Declare how many tests might be skipped so tests run will match up with
    the plan.
    """
    global test
    if why is not None:
        message = 'skip ' + why
    else:
        message = 'skip'
    for _ in range(how_many):
        test += 1
        _print(f'ok {test} # {message}')
    return True


def throws_ok(cb, expected, test_name=None):
    """::

        elements = [1, 2, 3]
        throws_ok(lambda: elements[3], IndexError, 'no more elements')

    Check if callback (function or lambda) throws a proper exception.
    """
    got = None
    check = False

    if isinstance(expected, type) and issubclass(expected, Exception):
        if test_name is None:
            test_name = f'Raised {expected.__name__}'
        else:
            test_name = f'{test_name} raised {expected.__name__}'

        try:
            cb()
        except expected:
            check = True
        except Exception as e:
            got = e.__class__.__name__

        expected = expected.__name__

    else:
        if test_name is None:
            test_name = f"Raised '{expected}'"
        else:
            test_name = f"{test_name} raised '{expected}'"

        try:
            cb()
        except Exception as e:
            got = str(e)
            check = got == expected

    _ok(check, test_name)
    if not check:
        diag(f'         got: {got if got is not None else None}\n    expected: {expected}\n')
    return check


def unlike_ok(got, expected, test_name=None):
    """::

        unlike_ok(got, 'expected', test_name)
        unlike_ok(got, ('expected', 'i'), test_name)
        unlike_ok(got, re.compile('expected'), test_name)

    The same as :func:`like_ok`, only it checks if value does not match the
    given pattern.
    """
    FLAGS = {
        'd': re.DEBUG,
        'i': re.IGNORECASE,
        'l': re.LOCALE,
        'm': re.MULTILINE,
        's': re.DOTALL,
        'u': re.UNICODE,
        'x': re.VERBOSE,
    }
    if isinstance(expected, _type_regex):
        regex = expected
        regex_repr = f're.compile({repr(regex.pattern)}, {regex.flags})'
    else:
        re_flags = 0
        if isinstance(expected, (list, tuple)) and len(expected) > 1:
            for c in expected[1]:
                re_flags |= FLAGS[c]
            expected = expected[0]
        regex = re.compile(expected, re_flags)
        regex_repr = f're.compile({repr(expected)}, {re_flags})'
    if test_name is None:
        test_name = f'An object {type(got)}'
    test_name = f'{test_name} matches {regex_repr}'
    try:
        check = not regex.search(got)
    except:
        check = True
    _ok(check, test_name)
    if not check:
        diag(f'                {repr(got)}\n        matches {repr(expected)}\n')
    return check


def _deep_check(stack, e1, e2):
    if e1 is None or e2 is None:
        if e1 is None and e2 is None:
            return True
        else:
            stack.append({'vals': [e1, e2]})
            return False

    if id(e1) == id(e2):
        return True

    if e1 == e2:
        return True

    if isinstance(e1, list) and isinstance(e2, list):
        return _eq_array(stack, 'list', e1, e2)

    if isinstance(e1, tuple) and isinstance(e2, tuple):
        return _eq_array(stack, 'tuple', e1, e2)

    if isinstance(e1, set) and isinstance(e2, set):
        return _eq_array(stack, 'set', sorted(e1), sorted(e2))

    if isinstance(e1, dict) and isinstance(e2, dict):
        return _eq_hash(stack, 'dict', e1, e2)

    stack.append({'vals': [e1, e2]})
    return False


def _eq_array(stack, t, a1, a2):
    if a1 == a2:
        return True

    check = True
    for i in range(max(len(a1), len(a2))):
        if i < len(a1):
            e1 = a1[i]
        else:
            e1 = DoesNotExist

        if i < len(a2):
            e2 = a2[i]
        else:
            e2 = DoesNotExist

        stack.append({'type': t, 'idx': i, 'vals': [e1, e2]})
        check = _deep_check(stack, e1, e2)
        if check:
            stack.pop()
        else:
            break

    return check


def _eq_hash(stack, t, h1, h2):
    if h1 == h2:
        return True

    check = True
    if len(h1) > len(h2):
        bigger = h1
    else:
        bigger = h2

    for k in sorted(bigger):
        if k in h1:
            e1 = h1[k]
        else:
            e1 = DoesNotExist

        if k in h2:
            e2 = h2[k]
        else:
            e2 = DoesNotExist

        stack.append({'type': t, 'idx': k, 'vals': [e1, e2]})
        check = _deep_check(stack, e1, e2)
        if check:
            stack.pop()
        else:
            break

    return check


def _format_stack(stack):
    vname = '$FOO'

    for entry in stack:
        t = entry.get('type', '')
        idx = entry.get('idx', 0)
        if t == 'list' or t == 'tuple' or t == 'dict':
            vname += f'[{repr(idx)}]'
        elif t == 'set':
            vname = f'sorted({vname})[{repr(idx)}]'

    vals = stack[-1]['vals']
    vnames = ['     ' + re.sub(r'\$FOO', 'got', vname), re.sub(r'\$FOO', 'expected', vname)]

    out = 'Structures begin differing at:\n'
    for idx in range(len(vals)):
        val = vals[idx]
        if val is None:
            val = 'None'
        elif val is DoesNotExist:
            val = 'Does not exist'
        else:
            val = repr(val)
        vals[idx] = val

    out += f'{vnames[0]} = {vals[0]}\n'
    out += f'{vnames[1]} = {vals[1]}\n'

    out = '    ' + '\n    '.join(out.split('\n'))

    return out


def _ok(check, test_name=None):
    global failed, test

    test += 1

    if not check:
        message = 'not '
        failed += 1
    else:
        message = ''

    message += f'ok {test}'

    if test_name is not None:
        if isinstance(test_name, int) or f'{test_name}'.isdigit():
            diag(
                f"    You named your test '{test_name}'.  You shouldn't use numbers for your test names.\n    Very confusing."
            )
        message += f' - {test_name}'

    _print(message)

    if not check:
        if test_name is not None:
            diag(f"  Failed test '{test_name}'")
        else:
            diag('  Failed test')
        diag(''.join(traceback.format_stack()[:-2]))

    return check


def _print(*args, **kwargs):
    output = kwargs.get('file', sys.stdout)
    string = ' '.join(args) + '\n'
    encoding = sys.stdout.encoding
    if not encoding or encoding.lower() != 'utf-8':
        string = string.encode('ascii', 'backslashreplace').decode('ascii')
    output.write(string)
    output.flush()


def _run(script=__file__, srcdir='.'):
    python_path = os.getenv('PYTHONPATH', '')
    if python_path and python_path != '.':
        python_path = srcdir + ':' + python_path
    else:
        python_path = srcdir
    os.putenv('PYTHONPATH', python_path)
    p = subprocess.Popen([sys.executable, script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, stderr = p.communicate()
    if p.returncode:
        raise Error(stderr)


class DoesNotExist:
    pass


class Error(Exception):
    """
    Exception raised if test script could not be started.
    """

    pass


class Guard:
    def __del__(self):
        global failed, done, tests
        if test and not tests and not done:
            print('# Tests were run but no plan was declared and done_testing() was not seen.', file=sys.stderr)

        if not done:
            if not failed:
                failed = 255 - test
            try:
                os._exit(failed)
            except:
                pass


_guard = Guard()


class NoseTest:
    """
    :mod:`Pyjo.Test` wrapper for ``nosetests`` command.
    """

    script = __file__
    srcdir = '.'

    def test_nose(self):
        _run(self.script, self.srcdir)


class UnitTest(unittest.TestCase):
    """
    :mod:`Pyjo.Test` wrapper for ``python -m unittest`` command.
    """

    script = __file__
    srcdir = '.'

    def test_unit(self):
        _run(self.script, self.srcdir)
