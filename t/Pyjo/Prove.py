import Pyjo.Prove

from Pyjo.Test import *

import os
import signal
import subprocess
import sys
import tempfile
import textwrap
import time


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
    'sleep.py': """
        from Pyjo.Test import *
        import time
        ok(True)
        time.sleep(60)
        done_testing()
    """,
    'pid.py': """
        from Pyjo.Test import *
        import os, time
        with open('pid', 'w') as f:
            f.write(str(os.getpid()))
        ok(True)
        time.sleep(60)
        done_testing()
    """,
    'child.py': """
        from Pyjo.Test import *
        import subprocess, sys
        subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
        ok(True)
        done_testing()
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


def interrupt(*args):
    # Ctrl-C once the script that sleeps has started; SIGINT may be ignored in the process of the tests
    with tempfile.TemporaryDirectory() as tmp:
        for name in ('pass.py', 'pid.py'):
            with open(os.path.join(tmp, name), 'w') as f:
                f.write(textwrap.dedent(SCRIPTS[name]))
        env = dict(os.environ, PYTHONPATH=ROOT)
        p = subprocess.Popen(
            [sys.executable, '-m', 'Pyjo.Prove', *args, 'pass.py', 'pid.py'],
            cwd=tmp,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_DFL),
        )
        path = os.path.join(tmp, 'pid')
        deadline = time.monotonic() + 30
        while not os.path.exists(path) and time.monotonic() < deadline:
            time.sleep(0.1)
        time.sleep(0.2)
        p.send_signal(signal.SIGINT)
        out, err = p.communicate(timeout=30)
        with open(path) as f:
            pid = int(f.read())
    try:
        os.kill(pid, 0)
        alive = True
    except ProcessLookupError:
        alive = False
    return out, err, p.returncode, alive


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
    r = Pyjo.Prove.Result('test.py', tests=1, exit_status=-9, timed_out=0.5)
    Pyjo.Prove.finish(r)
    is_ok(r.errors, ['Timed out after 0.5 seconds'], 'timed out')

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

with subtest('Timeout'):
    started = time.monotonic()
    out, code = prove('--timeout', '2', 'sleep.py', 'pass.py')
    like_ok(out, r'(?m)^sleep\.py \.+ Timed out$', 'script stopped')
    like_ok(out, r'(?m)^  Timed out after 2 seconds$', 'reason in the summary')
    like_ok(out, r'(?m)^pass\.py \.+ ok$', 'next script still runs')
    is_ok(code, 1, 'right exit status')
    ok(time.monotonic() - started < 30, 'the run does not wait for the script')

    started = time.monotonic()
    out, code = prove('--timeout', '2', 'child.py')
    like_ok(out, r'(?m)^child\.py \.+ Timed out$', 'a process of the script keeps its output open')
    ok(time.monotonic() - started < 30, 'the process of the script is killed with it')

    out, code = prove('--timeout', '30', 'pass.py')
    like_ok(out, r'(?m)^pass\.py \.+ ok$', 'a script within the time')
    is_ok(code, 0, 'right exit status')

with subtest('Ctrl-C'):
    out, err, code, alive = interrupt()
    is_ok(code, -signal.SIGINT, 'dies of the signal')
    unlike_ok(out, r'Result:', 'no summary')
    unlike_ok(err, r'Traceback', 'no traceback')
    ok(not alive, 'the running script is killed')

    out, err, code, alive = interrupt('--trap')
    like_ok(out, r'(?m)^pass\.py \.+ ok$', 'finished script')
    like_ok(err, r'(?m)^Test run interrupted!$', 'interrupted')
    like_ok(out, r'(?m)^Files=1, Tests=2, ', 'summary of the finished scripts')
    like_ok(out, r'(?m)^Result: FAIL$', 'result')
    is_ok(code, 1, 'right exit status')
    ok(not alive, 'the running script is killed')

with subtest('Verbose'):
    out, code = prove('-v', 'pass.py')
    like_ok(out, r'(?m)^ok 1 - first$', 'TAP output shown')
    like_ok(out, r'(?m)^    ok 1 - deep$', 'subtest output shown')

done_testing()
