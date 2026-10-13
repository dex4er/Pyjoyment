from Pyjo.Test import *

import os
import shutil
import subprocess
import sys
import tempfile
import textwrap


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def run(code, setup='', after='done_testing()', env=None):
    # The documented code runs as a test script of its own, after the setup,
    # which defines the names it uses, and before `after`, which ends it
    script = '\n'.join(['from Pyjo.Test import *', textwrap.dedent(setup), textwrap.dedent(code), after, ''])
    env = {k: v for k, v in os.environ.items() if k != 'TEST_ONLINE'} | {'PYTHONPATH': ROOT} | (env or {})
    p = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True, env=env)
    return p.stdout, p.stderr, p.returncode


def shell(command, cwd):
    # A `python` on PATH which is the interpreter running this test
    bindir = os.path.join(cwd, 'bin')
    os.makedirs(bindir, exist_ok=True)
    if not os.path.exists(os.path.join(bindir, 'python')):
        os.symlink(sys.executable, os.path.join(bindir, 'python'))
    env = dict(os.environ, PATH=os.pathsep.join([bindir, os.environ.get('PATH', '')]))
    env.pop('PYTHONPATH', None)
    p = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, env=env)
    return p.stdout, p.returncode


SYNOPSIS_SETUP = """
    import Pyjo.URL

    class Cls:
        pass

    got, expected, unexpected = 'expected', 'expected', 'unexpected'
    got_complex_structure = expected_complex_structure = {'a': [1, 2]}
    obj, cls = Cls(), Cls
    url = Pyjo.URL.new('http://example.com')
"""

SYNOPSIS = """
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
"""

with subtest('Synopsis'):
    out, err, code = run(SYNOPSIS, setup=SYNOPSIS_SETUP, after='', env={'TEST_ONLINE': '1'})
    is_ok(
        out,
        'ok 1 - test name\n'
        'ok 2 - test name\n'
        'ok 3 - test name\n'
        'ok 4 - test name\n'
        'ok 5 - test name\n'
        'ok 6 - test name\n'
        'ok 7 - test name\n'
        "ok 8 - An object of class 'Cls' isa 'Cls'\n"
        'ok 9 - test name\n'
        '# Subtest: Parse\n'
        '    ok 1 - right host\n'
        '    1..1\n'
        'ok 10 - Parse\n'
        '# Subtest: Format\n'
        '    ok 1 - right format\n'
        '    1..1\n'
        'ok 11 - Format\n'
        '# what happens next\n'
        '1..11\n',
        'all tests pass',
    )
    is_ok(err, "# here's what went wrong\n", 'diagnostic message')
    is_ok(code, 0, 'right exit status')

    out, err, code = run(SYNOPSIS, setup=SYNOPSIS_SETUP, after='')
    is_ok(out, '1..0 # SKIP set TEST_ONLINE to enable this test\n', 'skipped without TEST_ONLINE')
    is_ok(code, 0, 'right exit status')

with subtest('Running tests'):
    with tempfile.TemporaryDirectory() as tmp:
        os.symlink(os.path.join(ROOT, 'Pyjo'), os.path.join(tmp, 'Pyjo'))
        os.makedirs(os.path.join(tmp, 't', 'Pyjo'))
        with open(os.path.join(tmp, 't', 'Pyjo', 'URL.py'), 'w') as f:
            f.write("from Pyjo.Test import *\n\nok(True, 'works')\n\ndone_testing()\n")

        out, code = shell('python -m Pyjo.Prove -I . -r t', tmp)
        like_ok(out, r'(?m)^t/Pyjo/URL\.py \.+ ok$', 'python -m Pyjo.Prove -I . -r t')
        is_ok(code, 0, 'right exit status')

        if shutil.which('prove'):
            out, code = shell('PYTHONPATH=. prove --ext=py --exec=python -r t', tmp)
            like_ok(out, r'(?m)^t/Pyjo/URL\.py \.+ ok$', 'PYTHONPATH=. prove --ext=py --exec=python -r t')
            is_ok(code, 0, 'right exit status')
        else:
            skip('Perl prove is not installed', 2)

        out, code = shell('PYTHONPATH=. python t/Pyjo/URL.py', tmp)
        is_ok(out, 'ok 1 - works\n1..1\n', 'PYTHONPATH=. python t/Pyjo/URL.py')
        is_ok(code, 0, 'right exit status')

with subtest('Subtests'):
    out, err, code = run("""
        with subtest('Simple'):
            ok(True, 'first')

        @subtest('Decorated')
        def _():
            ok(True, 'second')

        subtest('Callback', lambda: ok(True, 'third'))
    """)
    is_ok(
        out,
        '# Subtest: Simple\n'
        '    ok 1 - first\n'
        '    1..1\n'
        'ok 1 - Simple\n'
        '# Subtest: Decorated\n'
        '    ok 1 - second\n'
        '    1..1\n'
        'ok 2 - Decorated\n'
        '# Subtest: Callback\n'
        '    ok 1 - third\n'
        '    1..1\n'
        'ok 3 - Callback\n'
        '1..3\n',
        'three subtests',
    )
    is_ok(code, 0, 'right exit status')

with subtest('bail_out'):
    out, err, code = run(
        """
        if not connected:
            bail_out('No database connection')
        """,
        setup='connected = False',
    )
    is_ok(out, 'Bail out!  No database connection\n', 'bailed out')
    is_ok(code, 255, 'right exit status')

with subtest('cmp_ok'):
    out, err, code = run(
        """
        # ok(got == expected)
        cmp_ok(got, '==', expected, 'this == that')
        """,
        setup='got, expected = 42, 42',
    )
    is_ok(out, 'ok 1 - this == that\n1..1\n', 'passed')

with subtest('diag'):
    out, err, code = run(
        """
        if not in_ok(users, 'foo', "There's a foo user"):
            diag("Since there's no foo, check that /etc/bar is set up right")
        """,
        setup="users = ['bar']",
    )
    is_ok(out, "not ok 1 - There's a foo user\n1..1\n", 'failed')
    like_ok(err, r"(?m)^# Since there's no foo, check that /etc/bar is set up right$", 'diagnostic message')
    is_ok(code, 1, 'right exit status')

with subtest('done_testing'):
    out, err, code = run(
        """
        ok(True)
        done_testing()
        """,
        after='',
    )
    is_ok(out, 'ok 1\n1..1\n', 'without a number')
    out, err, code = run(
        """
        ok(True)
        done_testing(1)
        """,
        after='',
    )
    is_ok(out, 'ok 1\n1..1\n', 'with a number')
    is_ok(code, 0, 'right exit status')

with subtest('fail_ok'):
    out, err, code = run("""
        fail_ok('This should not happen')
    """)
    is_ok(out, 'not ok 1 - This should not happen\n1..1\n', 'failed')
    is_ok(code, 1, 'right exit status')

with subtest('in_ok'):
    out, err, code = run("""
        in_ok(['foo', 'bar'], 'foo', 'foo is in the list')
    """)
    is_ok(out, 'ok 1 - foo is in the list\n1..1\n', 'passed')

with subtest('is_deeply_ok'):
    out, err, code = run("""
        is_deeply_ok([[1, 2], [3, [4, 5]]], [[1, 2], [3]], 'deep structure')
    """)
    is_ok(out, 'not ok 1 - deep structure\n1..1\n', 'failed')
    like_ok(
        err,
        r'(?m)^#     Structures begin differing at:\n'
        r'#          got\[1\]\[1\] = \[4, 5\]\n'
        r'#     expected\[1\]\[1\] = Does not exist$',
        'where the structures differ',
    )

with subtest('is_ok'):
    out, err, code = run(
        """
        is_ok(ultimate_answer(), 42, 'meaning of life')
        """,
        setup="""
        def ultimate_answer():
            return 42
        """,
    )
    is_ok(out, 'ok 1 - meaning of life\n1..1\n', 'passed')

with subtest('isa_ok'):
    out, err, code = run(
        """
        obj = SomeClass()
        isa_ok(obj, SomeClass)
        isa_ok(123, (int, float))
        """,
        setup="""
        class SomeClass:
            pass
        """,
    )
    is_ok(
        out,
        "ok 1 - An object of class 'SomeClass' isa 'SomeClass'\n"
        "ok 2 - An object of class 'int' isa 'int, float'\n"
        '1..2\n',
        'passed',
    )

with subtest('isnt_ok'):
    out, err, code = run(
        """
        isnt_ok(foo, '', 'got some foo')
        """,
        setup="foo = 'foo'",
    )
    is_ok(out, 'ok 1 - got some foo\n1..1\n', 'passed')

with subtest('like_ok'):
    out, err, code = run(
        """
        like_ok(got, r'expected', 'test name')
        like_ok(got, (r'expected', 'i'), 'test name')
        like_ok(got, re.compile(r'expected'), 'test name')
        """,
        setup="""
        import re

        got = 'the expected value'
        """,
    )
    is_ok(out, 'ok 1 - test name\nok 2 - test name\nok 3 - test name\n1..3\n', 'passed')

with subtest('none_ok'):
    out, err, code = run(
        """
        none_ok(req.headers.transfer_encoding, 'no "Transfer-Encoding" value')
        """,
        setup="""
        import Pyjo.Message.Request

        req = Pyjo.Message.Request.new()
        """,
    )
    is_ok(out, 'ok 1 - no "Transfer-Encoding" value\n1..1\n', 'passed')

with subtest('not_in_ok'):
    out, err, code = run(
        """
        not_in_ok(os.environ, 'DISPLAY', 'DISPLAY is not set')
        """,
        setup="""
        import os

        os.environ.pop('DISPLAY', None)
        """,
    )
    is_ok(out, 'ok 1 - DISPLAY is not set\n1..1\n', 'passed')

with subtest('note'):
    out, err, code = run(
        """
        note(f'Tempfile is {tempfile}')
        """,
        setup="tempfile = '/tmp/test.txt'",
        after='pass_ok()\ndone_testing()',
    )
    is_ok(out, '# Tempfile is /tmp/test.txt\nok 1\n1..1\n', 'TAP comment')

with subtest('ok'):
    out, err, code = run(
        """
        ok(3**4 == 81, 'simple exponential')
        ok(isinstance(film, Film), 'set_db()')
        ok(None not in items, 'all items defined')
        """,
        setup="""
        class Film:
            pass

        film = Film()
        items = [1, 2, 3]
        """,
    )
    is_ok(out, 'ok 1 - simple exponential\nok 2 - set_db()\nok 3 - all items defined\n1..3\n', 'passed')

with subtest('pass_ok'):
    out, err, code = run("""
        pass_ok('step 1')
    """)
    is_ok(out, 'ok 1 - step 1\n1..1\n', 'passed')

with subtest('plan'):
    out, err, code = run(
        """
        plan(tests=3)
        """,
        after='ok(True)\nok(True)\nok(True)',
    )
    is_ok(out, '1..3\nok 1\nok 2\nok 3\n', 'planned')
    is_ok(code, 0, 'right exit status')
    out, err, code = run(
        """
        if not os.getenv('TEST_ONLINE'):
            plan(skip_all='set TEST_ONLINE to enable this test')
        """,
        setup='import os',
        after='',
    )
    is_ok(out, '1..0 # SKIP set TEST_ONLINE to enable this test\n', 'skipped')
    is_ok(code, 0, 'right exit status')

with subtest('plan_skip_all'):
    out, err, code = run(
        """
        plan_skip_all('set TEST_ONLINE to enable this test')
        """,
        after='',
    )
    is_ok(out, '1..0 # SKIP set TEST_ONLINE to enable this test\n', 'skipped')
    is_ok(code, 0, 'right exit status')

with subtest('plan_tests'):
    out, err, code = run(
        """
        plan_tests(3)
        """,
        after='ok(True)\nok(True)\nok(True)',
    )
    is_ok(out, '1..3\nok 1\nok 2\nok 3\n', 'planned')
    is_ok(code, 0, 'right exit status')

with subtest('skip'):
    out, err, code = run(
        """
        if os.getenv('TEST_ONLINE'):
            ok(Pyjo.UserAgent.new().get('https://mojolicious.org').success, 'online request')
        else:
            skip('set TEST_ONLINE to enable this test', 1)
        """,
        setup="""
        import Pyjo.UserAgent

        import os
        """,
    )
    is_ok(out, 'ok 1 # skip set TEST_ONLINE to enable this test\n1..1\n', 'skipped')
    is_ok(code, 0, 'right exit status')

with subtest('subtest'):
    out, err, code = run(
        """
        with subtest('Parse'):
            ok(True)

        @subtest('Parse')
        def _():
            ok(True)

        passed = subtest('Parse', lambda: ok(True))
        """,
        after="is_ok(passed, True, 'passed')\ndone_testing()",
    )
    is_ok(
        out,
        ''.join(f'# Subtest: Parse\n    ok 1\n    1..1\nok {i} - Parse\n' for i in (1, 2, 3)) + 'ok 4 - passed\n1..4\n',
        'three subtests',
    )

with subtest('throws_ok'):
    out, err, code = run(
        """
        throws_ok(lambda: [1, 2, 3][3], IndexError, 'no more elements')
        throws_ok(lambda: int('x'), "invalid literal for int() with base 10: 'x'", 'right message')
        throws_ok(lambda: int('x'), re.compile(r'invalid literal'), 'right message')
        """,
        setup='import re',
    )
    is_ok(out, 'ok 1 - no more elements\nok 2 - right message\nok 3 - right message\n1..3\n', 'passed')

with subtest('unlike_ok'):
    out, err, code = run(
        """
        unlike_ok(got, r'unexpected', 'test name')
        """,
        setup="got = 'the expected value'",
    )
    is_ok(out, 'ok 1 - test name\n1..1\n', 'passed')

done_testing()
