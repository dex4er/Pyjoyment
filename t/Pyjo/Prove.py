import Pyjo.Prove

from Pyjo.Test import *

import os
import subprocess
import sys
import tempfile
import textwrap


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

SCRIPTS = {
    'pass.py': """
        from Pyjo.Test import *
        ok(True, 'first')
        with subtest('Nested'):
            ok(True, 'deep')
        done_testing()
    """,
    'fail.py': """
        from Pyjo.Test import *
        ok(True)
        ok(False)
        ok(False)
        done_testing()
    """,
    'skip.py': """
        from Pyjo.Test import *
        plan(skip_all='not now')
    """,
    'noplan.py': """
        from Pyjo.Test import *
        ok(True)
    """,
    'badplan.py': """
        from Pyjo.Test import *
        plan(tests=3)
        ok(True)
    """,
    'die.py': """
        from Pyjo.Test import *
        ok(True)
        raise RuntimeError('boom')
    """,
    'bail.py': """
        from Pyjo.Test import *
        bail_out('no database')
    """,
}


def prove(*args, scripts=SCRIPTS):
    with tempfile.TemporaryDirectory() as tmp:
        for name, code in scripts.items():
            path = os.path.join(tmp, *name.split('/'))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                f.write(textwrap.dedent(code))
        env = dict(os.environ, PYTHONPATH=ROOT)
        p = subprocess.run(
            [sys.executable, '-m', 'Pyjo.Prove', *args], cwd=tmp, env=env, capture_output=True, text=True
        )
    return p.stdout, p.returncode


def result(lines):
    r = Pyjo.Prove.Result('test.py')
    for line in textwrap.dedent(lines).strip('\n').split('\n'):
        Pyjo.Prove.parse(r, line)
    Pyjo.Prove.finish(r)
    return r


with subtest('Parse a passing script'):
    r = result("""
        TAP version 14
        ok 1 - first
        # Subtest: Nested
            ok 1 - deep
            not ok 2 - ignored, belongs to the subtest
            1..2
        ok 2 - Nested
        ok 3 # SKIP no network
        not ok 4 # TODO not done yet
        1..4
    """)
    is_ok(r.planned, 4, 'right plan')
    is_ok(r.tests, 4, 'right number of tests')
    is_ok(r.failed, [], 'no failures')
    is_ok(r.skipped, 1, 'one skipped')
    is_ok(r.errors, [], 'no errors')
    ok(r.passed, 'passed')

with subtest('Parse failures'):
    r = result("""
        ok 1
        not ok 2 - bad
        ok 3 # TODO unexpectedly fixed
        1..3
    """)
    is_ok(r.failed, [2], 'right failures')
    is_ok(r.todo_passed, [3], 'TODO test passed')
    ok(not r.passed, 'failed')

with subtest('Parse a skipped script'):
    r = result('1..0 # SKIP not now')
    is_ok(r.skip_all, 'not now', 'right reason')
    ok(r.passed, 'passed')

with subtest('Parse errors'):
    is_ok(result('ok 1').errors, ['No plan found in TAP output'], 'no plan')
    is_ok(result('1..2\nok 1').errors, ['Bad plan.  You planned 2 tests but ran 1.'], 'fewer tests than planned')
    is_ok(
        result('ok 1\nok 3\n1..2').errors,
        ['Tests out of sequence.  Found (3) but expected (2)'],
        'out of sequence',
    )
    is_ok(result('1..1\nok 1\n1..1').errors, ['More than one plan found in TAP output'], 'two plans')
    is_ok(result('Bail out!  broken').bail_out, 'broken', 'bail out')
    is_ok(result('ok 1 - a \\# b # SKIP why').skipped, 1, 'escaped hash in the description')

with subtest('Find scripts'):
    with tempfile.TemporaryDirectory() as tmp:
        for name in ('b.py', 'a.py', 'notes.txt', 'sub/c.py'):
            path = os.path.join(tmp, *name.split('/'))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, 'w').close()
        found = Pyjo.Prove.find_scripts([tmp], '.py', recurse=False)
        is_ok([os.path.relpath(p, tmp) for p in found], ['a.py', 'b.py'], 'sorted, not recursive')
        found = Pyjo.Prove.find_scripts([tmp], '.py', recurse=True)
        is_ok([os.path.relpath(p, tmp) for p in found], ['a.py', 'b.py', os.path.join('sub', 'c.py')], 'recursive')

with subtest('Run passing and skipped scripts'):
    out, code = prove('pass.py', 'skip.py')
    like_ok(out, r'(?m)^pass\.py \.+ ok$', 'passing script')
    like_ok(out, r'(?m)^skip\.py \.+ skipped: not now$', 'skipped script')
    like_ok(out, r'(?m)^All tests successful\.$', 'summary')
    like_ok(out, r'(?m)^Files=2, Tests=2, \d+ wallclock secs$', 'counts')
    like_ok(out, r'(?m)^Result: PASS$', 'result')
    is_ok(code, 0, 'right exit status')

with subtest('Run failing scripts'):
    out, code = prove('fail.py', 'noplan.py', 'badplan.py', 'die.py')
    like_ok(out, r'(?m)^fail\.py \.+ Failed 2/3 subtests$', 'failures')
    like_ok(out, r'(?m)^  Failed tests:  2, 3$', 'failed test numbers')
    like_ok(out, r'(?m)^  No plan found in TAP output$', 'no plan')
    like_ok(out, r'(?m)^  Bad plan\.  You planned 3 tests but ran 1\.$', 'bad plan')
    like_ok(out, r'(?m)^  Non-zero exit status: 255$', 'died')
    like_ok(out, r'(?m)^Result: FAIL$', 'result')
    is_ok(code, 1, 'right exit status')

with subtest('Bail out stops the run'):
    out, code = prove('bail.py', 'pass.py')
    like_ok(out, r'(?m)^bail\.py \.+ Bailout called\.  Further testing stopped:  no database$', 'bail out')
    unlike_ok(out, r'pass\.py', 'next script not run')
    is_ok(code, 1, 'right exit status')

with subtest('Directories, recursion and parallel jobs'):
    scripts = {'t/a.py': SCRIPTS['pass.py'], 't/sub/b.py': SCRIPTS['pass.py'], 't/sub/c.py': SCRIPTS['skip.py']}
    out, code = prove(scripts=scripts)
    like_ok(out, r'(?m)^Files=1, ', 'only the top directory of t by default')
    out, code = prove('-r', '-j', '3', scripts=scripts)
    like_ok(out, r'(?m)^Files=3, Tests=4, ', 'recursive, in parallel')
    is_ok(code, 0, 'right exit status')

with subtest('Verbose'):
    out, code = prove('-v', 'pass.py')
    like_ok(out, r'(?m)^ok 1 - first$', 'TAP output shown')
    like_ok(out, r'(?m)^    ok 1 - deep$', 'subtest output shown')

done_testing()
