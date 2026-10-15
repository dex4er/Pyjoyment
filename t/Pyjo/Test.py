from Pyjo.Test import *

import os
import re
import subprocess
import sys
import tempfile
import textwrap


def run(code):
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as script:
        script.write(textwrap.dedent(code))
    try:
        p = subprocess.run([sys.executable, script.name], capture_output=True, text=True, env=os.environ)
    finally:
        os.unlink(script.name)
    stderr = re.sub(r'(?m)^(\s*#   at ).*( line \d+\.)$', r'\1SCRIPT\2', p.stderr)
    return p.stdout, stderr, p.returncode


with subtest('Passing tests with done_testing'):
    out, err, code = run("""
        from Pyjo.Test import *
        ok(True, 'first')
        ok(1)
        done_testing()
    """)
    is_ok(out, 'ok 1 - first\nok 2\n1..2\n', 'right output')
    is_ok(err, '', 'no diagnostics')
    is_ok(code, 0, 'right exit status')

with subtest('Plan up front'):
    out, err, code = run("""
        from Pyjo.Test import *
        plan(tests=2)
        pass_ok('first')
        pass_ok('second')
    """)
    is_ok(out, '1..2\nok 1 - first\nok 2 - second\n', 'right output')
    is_ok(code, 0, 'right exit status')

with subtest('Failure'):
    out, err, code = run("""
        from Pyjo.Test import *
        is_ok(1, 1, 'same')
        is_ok(1, 2, 'different')
        done_testing()
    """)
    is_ok(out, 'ok 1 - same\nnot ok 2 - different\n1..2\n', 'right output')
    is_ok(
        err,
        "#   Failed test 'different'\n"
        '#   at SCRIPT line 4.\n'
        '#          got: 1\n'
        '#     expected: 2\n'
        '# Looks like you failed 1 test of 2.\n',
        'right diagnostics',
    )
    is_ok(code, 1, 'exit status is the number of failures')

with subtest('Fewer tests than planned'):
    out, err, code = run("""
        from Pyjo.Test import *
        plan(tests=3)
        ok(True)
    """)
    is_ok(out, '1..3\nok 1\n', 'right output')
    is_ok(err, '# Looks like you planned 3 tests but ran 1.\n', 'right diagnostics')
    is_ok(code, 255, 'right exit status')

with subtest('No plan'):
    out, err, code = run("""
        from Pyjo.Test import *
        ok(True)
    """)
    like_ok(err, r'no plan was declared', 'right diagnostics')
    is_ok(code, 254, 'right exit status')

with subtest('Skip all'):
    out, err, code = run("""
        from Pyjo.Test import *
        plan(skip_all='not now')
        ok(False)
    """)
    is_ok(out, '1..0 # SKIP not now\n', 'right output')
    is_ok(code, 0, 'right exit status')

with subtest('Import only'):
    out, err, code = run("""
        import Pyjo.Test
    """)
    is_ok(out + err, '', 'no output')
    is_ok(code, 0, 'right exit status')

with subtest('Subtests'):
    out, err, code = run("""
        from Pyjo.Test import *

        ok(1, 'first')

        with subtest('Parse'):
            is_ok(1, 1, 'right one')

            @subtest('Nested')
            def _():
                ok(1, 'deep')

            ok(1)

        @subtest('Skipped')
        def _():
            plan(skip_all='not now')

        subtest('Empty', lambda: None)
        done_testing()
    """)
    is_ok(
        out,
        'ok 1 - first\n'
        '# Subtest: Parse\n'
        '    ok 1 - right one\n'
        '    # Subtest: Nested\n'
        '        ok 1 - deep\n'
        '        1..1\n'
        '    ok 2 - Nested\n'
        '    ok 3\n'
        '    1..3\n'
        'ok 2 - Parse\n'
        '# Subtest: Skipped\n'
        '    1..0 # SKIP not now\n'
        'ok 3 # skip not now\n'
        '# Subtest: Empty\n'
        '    1..0\n'
        '    # No tests run!\n'
        'not ok 4 - No tests run for subtest "Empty"\n'
        '1..4\n',
        'same output as Test::More',
    )
    is_ok(code, 1, 'empty subtest fails')

with subtest('Failing subtest'):
    out, err, code = run("""
        from Pyjo.Test import *
        with subtest('Inner'):
            ok(True, 'good')
            ok(False, 'bad')
        done_testing()
    """)
    is_ok(
        out,
        '# Subtest: Inner\n    ok 1 - good\n    not ok 2 - bad\n    1..2\nnot ok 1 - Inner\n1..1\n',
        'right output',
    )
    is_ok(
        err,
        "    #   Failed test 'bad'\n"
        '    #   at SCRIPT line 5.\n'
        '    # Looks like you failed 1 test of 2.\n'
        "#   Failed test 'Inner'\n"
        '#   at SCRIPT line 3.\n'
        '# Looks like you failed 1 test of 1.\n',
        'diagnostics are indented like the subtest',
    )
    is_ok(code, 1, 'right exit status')

with subtest('Subtest with its own plan and done_testing'):
    out, err, code = run("""
        from Pyjo.Test import *
        with subtest('Planned'):
            plan(tests=1)
            ok(True)
        with subtest('Done'):
            ok(True)
            done_testing(1)
        done_testing()
    """)
    is_ok(
        out,
        '# Subtest: Planned\n    1..1\n    ok 1\nok 1 - Planned\n'
        '# Subtest: Done\n    ok 1\n    1..1\nok 2 - Done\n1..2\n',
        'right output',
    )
    is_ok(code, 0, 'right exit status')

with subtest('Callback returns the result'):
    out, err, code = run("""
        from Pyjo.Test import *
        print('#', subtest('Good', lambda: ok(True)))
        print('#', subtest('Bad', lambda: ok(False)))
        done_testing()
    """)
    like_ok(out, r'# True\n', 'passed subtest returns True')
    like_ok(out, r'# False\n', 'failed subtest returns False')

with subtest('Exception'):
    out, err, code = run("""
        from Pyjo.Test import *
        ok(True)
        raise RuntimeError('boom')
    """)
    like_ok(err, r'RuntimeError: boom', 'traceback')
    like_ok(err, r'# Looks like your test exited with 255 just after 1\.', 'right diagnostics')
    is_ok(code, 255, 'right exit status')

with subtest('Exception in a subtest'):
    out, err, code = run("""
        from Pyjo.Test import *
        with subtest('Dies'):
            ok(True)
            raise RuntimeError('boom')
    """)
    is_ok(out, '# Subtest: Dies\n    ok 1\n    1..1\nnot ok 1 - Dies\n', 'subtest fails')
    is_ok(code, 255, 'right exit status')

with subtest('Bail out'):
    out, err, code = run("""
        from Pyjo.Test import *
        with subtest('Inner'):
            bail_out('no database')
        ok(True)
    """)
    is_ok(out, '# Subtest: Inner\nBail out!  no database\n', 'right output')
    is_ok(code, 255, 'right exit status')

with subtest('Skip, note and diag'):
    out, err, code = run("""
        from Pyjo.Test import *
        skip('no network', 2)
        note('a note')
        diag('a diag')
        done_testing()
    """)
    is_ok(out, 'ok 1 # skip no network\nok 2 # skip no network\n# a note\n1..2\n', 'right output')
    is_ok(err, '# a diag\n', 'diag goes to the standard error')

with subtest('Test names'):
    out, err, code = run("""
        from Pyjo.Test import *
        ok(True, 'a # in the name')
        isa_ok(1, int)
        done_testing()
    """)
    is_ok(out, "ok 1 - a \\# in the name\nok 2 - An object of class 'int' isa 'int'\n1..2\n", 'right names')

with subtest('Assertions'):
    out, err, code = run("""
        import re
        import sys
        from Pyjo.Test import *
        like_ok('Hello', ('hello', 'i'), 'like with flags')
        unlike_ok('Hello', r'bye', 'unlike')
        cmp_ok(2, '>', 1, 'cmp_ok')
        cmp_ok(None, 'is', None, 'cmp_ok is')
        in_ok([1, 2], 1, 'in_ok')
        not_in_ok([1, 2], 3, 'not_in_ok')
        none_ok(None, 'none_ok')
        is_deeply_ok({'a': [1, (2, 3)]}, {'a': [1, (2, 3)]}, 'is_deeply_ok')
        throws_ok(lambda: int('x'), ValueError, 'throws_ok class')
        throws_ok(lambda: int('x'), re.compile(r'invalid literal'), 'throws_ok regex')
        throws_ok(lambda: [][0], 'list index out of range', 'throws_ok message')
        throws_ok(lambda: sys.exit('bye'), SystemExit, 'throws_ok class that is not an Exception')
        isnt_ok(1, 2, 'isnt_ok')
        done_testing()
    """)
    is_ok(err, '', 'no diagnostics')
    is_ok(code, 0, 'all assertions pass')

with subtest('Deep structure differences'):
    out, err, code = run("""
        from Pyjo.Test import *
        is_deeply_ok({'a': [1, 2]}, {'a': [1, 3]}, 'differ')
        done_testing()
    """)
    like_ok(
        err,
        r"#     Structures begin differing at:\n#          got\['a'\]\[1\] = 2\n#     expected\['a'\]\[1\] = 3\n",
        'right diagnostics',
    )
    is_ok(code, 1, 'right exit status')

done_testing()
