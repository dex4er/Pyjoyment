import Pyjo.Prove

from Pyjo.Test import *

import os
import re
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
    'stderr.py': """
        from Pyjo.Test import *
        import sys
        print('first warning', file=sys.stderr)
        ok(True)
        print('second warning', file=sys.stderr)
        done_testing()
    """,
    'directives.py': """
        print('ok 1', 'not ok 2 # TODO later', 'ok 3 # TODO fixed', 'ok 4 # SKIP why', '1..4', sep='\\n')
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
    out, err, code = prove_stderr(*args, scripts=scripts)
    return out, code


def prove_stderr(*args, scripts=SCRIPTS):
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
    return p.stdout, p.stderr, p.returncode


def prove_tty(*args, env=None, scripts=SCRIPTS):
    # The output to a terminal, where the terminal turns a newline into a carriage return and a newline
    with tempfile.TemporaryDirectory() as tmp:
        for name, code in scripts.items():
            with open(os.path.join(tmp, name), 'w') as f:
                f.write(textwrap.dedent(code))
        env = (
            {k: v for k, v in os.environ.items() if k != 'NO_COLOR'}
            | {'TERM': 'xterm', 'PYTHONPATH': ROOT}
            | (env or {})
        )
        master, slave = os.openpty()
        p = subprocess.Popen(
            [sys.executable, '-m', 'Pyjo.Prove', *args], cwd=tmp, env=env, stdout=slave, stderr=subprocess.DEVNULL
        )
        os.close(slave)
        out = b''
        try:
            while chunk := os.read(master, 4096):
                out += chunk
        except OSError:
            # Linux reports the end of the output of a terminal as EIO
            pass
        os.close(master)
        p.wait()
    return out.decode().replace('\r\n', '\n'), p.returncode


def colored(code, text):
    return re.escape(f'\033[{code}m{text}\033[0m')


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

with subtest('Scripts that require a version of Python'):

    def requires(specifier):
        return f"""
            # /// script
            # requires-python = "{specifier}"
            # ///
            from Pyjo.Test import *
            ok(True)
            done_testing()
        """

    version = '.'.join(map(str, sys.version_info[:3]))
    minor = '.'.join(map(str, sys.version_info[:2]))
    scripts = {
        'newer.py': requires('>=99'),
        'older.py': requires('<3'),
        'this.py': requires(f'=={version}'),
        'wildcard.py': requires(f'=={minor}.*'),
        'not_wildcard.py': requires(f'!={minor}.*'),
        'compatible.py': requires(f'~={minor}'),
        'range.py': requires(f'>={minor}, <99'),
        'out_of_range.py': requires(f'>={minor}, <3'),
        'syntax.py': """
            # /// script
            # requires-python = ">=99"
            # ///
            this is not Python
        """,
        'other_block.py': """
            # /// pyproject
            # requires-python = ">=99"
            # ///
            from Pyjo.Test import *
            ok(True)
            done_testing()
        """,
        'invalid.py': requires('3.12'),
        'invalid_wildcard.py': requires('>=3.*'),
        'invalid_toml.py': """
            # /// script
            # requires-python = >=3
            # ///
        """,
    }
    out, code = prove(*scripts, scripts=scripts)
    like_ok(out, r'(?m)^newer\.py \.+ skipped: requires Python >=99$', 'newer Python')
    like_ok(out, r'(?m)^older\.py \.+ skipped: requires Python <3$', 'older Python')
    like_ok(out, r'(?m)^this\.py \.+ ok$', 'this version')
    like_ok(out, r'(?m)^wildcard\.py \.+ ok$', 'wildcard')
    like_ok(out, r'(?m)^not_wildcard\.py \.+ skipped: ', 'excluded wildcard')
    like_ok(out, r'(?m)^compatible\.py \.+ ok$', 'compatible release')
    like_ok(out, r'(?m)^range\.py \.+ ok$', 'range')
    like_ok(out, r'(?m)^out_of_range\.py \.+ skipped: ', 'out of range')
    like_ok(out, r'(?m)^syntax\.py \.+ skipped: requires Python >=99$', 'not compiled')
    like_ok(out, r'(?m)^other_block\.py \.+ ok$', 'other block')
    like_ok(out, r'(?m)^invalid\.py \.+ Dubious$', 'invalid specifier')
    like_ok(out, r'(?m)^  Invalid script metadata: Invalid requires-python: 3\.12$', 'invalid specifier reported')
    like_ok(out, r'(?m)^invalid_wildcard\.py \.+ Dubious$', 'invalid wildcard')
    like_ok(out, r'(?m)^invalid_toml\.py \.+ Dubious$', 'invalid TOML')
    is_ok(code, 1, 'right exit status')

    scripts = {'newer.py': requires('>=99'), 'this.py': requires(f'=={version}')}
    out, code = prove('--exec', f'{sys.executable} -X utf8', *scripts, scripts=scripts)
    like_ok(out, r'(?m)^newer\.py \.+ skipped: requires Python >=99$', 'newer Python of the command')
    like_ok(out, r'(?m)^this\.py \.+ ok$', 'this version of the command')
    is_ok(code, 0, 'right exit status')

    scripts = {'unknown.py': requires('>=99')}
    out, code = prove('--exec', 'sh', *scripts, scripts=scripts)
    like_ok(out, r'(?m)^unknown\.py \.+ Dubious$', 'run when the version of the command is unknown')

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

with subtest('Capture the standard error'):
    out, err, code = prove_stderr('stderr.py', 'pass.py')
    like_ok(err, r'(?m)^first warning$', 'standard error passes through by default')
    unlike_ok(err, r'stderr\.py: ', 'without the name of the script')

    out, err, code = prove_stderr('-j', '2', '--capture-stderr', 'stderr.py', 'pass.py')
    like_ok(out, r'(?m)^stderr\.py \.+ ok$', 'script passes')
    is_ok(err, 'stderr.py: first warning\nstderr.py: second warning\n', 'after the name of the script, in order')
    is_ok(code, 0, 'right exit status')

    out, err, code = prove_stderr('--capture-stderr', '--timeout', '2', 'child.py')
    like_ok(out, r'(?m)^child\.py \.+ Timed out$', 'a process of the script keeps its output open')

with subtest('Run without tests'):
    out, code = prove('skip.py')
    like_ok(out, r'(?m)^All tests successful\.$', 'summary')
    like_ok(out, r'(?m)^Files=1, Tests=0, ', 'counts')
    like_ok(out, r'(?m)^Result: NOTESTS$', 'result')
    is_ok(code, 0, 'right exit status')

with subtest('Colors'):
    out, err, code = prove_stderr('-j', '2', '--capture-stderr', 'pass.py', 'fail.py', 'stderr.py')
    unlike_ok(out, r'\033', 'no colors when the output is not a terminal')
    unlike_ok(err, r'\033', 'no colors when the standard error is not a terminal')

    out, err, code = prove_stderr('--color', '--capture-stderr', 'pass.py', 'skip.py', 'stderr.py', 'directives.py')
    like_ok(out, rf'(?m)^pass\.py \.+ {colored(32, "ok")}$', 'green ok')
    like_ok(out, rf'(?m)^skip\.py \.+ {colored(33, "skipped: not now")}$', 'yellow skipped')
    like_ok(out, rf'(?m)^{colored(32, "All tests successful.")}$', 'green summary')
    like_ok(out, rf'(?m)^{colored(33, "directives.py: TODO passed:  3")}$', 'yellow TODO passed')
    like_ok(out, rf'(?m)^Result: {colored(32, "PASS")}$', 'green PASS')
    like_ok(err, rf'(?m)^{colored(31, "stderr.py: first warning")}$', 'red standard error')
    is_ok(code, 0, 'right exit status')

    out, code = prove('--color', 'fail.py', 'die.py', 'bail.py')
    like_ok(out, rf'(?m)^fail\.py \.+ {colored(31, "Failed 2/3 subtests")}$', 'red failure')
    like_ok(out, rf'(?m)^die\.py \.+ {colored(31, "Dubious")}$', 'red dubious')
    like_ok(out, rf'(?m)^bail\.py \.+ {colored(31, "Bailout called.  Further testing stopped:  no database")}$', 'red')
    like_ok(out, rf'(?m)^  {colored(31, "Failed tests:  2, 3")}$', 'red failed tests')
    like_ok(out, rf'(?m)^  {colored(31, "Non-zero exit status: 255")}$', 'red error')
    like_ok(out, rf'(?m)^  {colored(31, "Bail out:  no database")}$', 'red bail out')
    like_ok(out, rf'(?m)^Result: {colored(31, "FAIL")}$', 'red FAIL')

    out, code = prove('--color', '--timeout', '2', 'sleep.py')
    like_ok(out, rf'(?m)^sleep\.py \.+ {colored(31, "Timed out")}$', 'red timeout')

    out, code = prove('--color', 'skip.py')
    like_ok(out, rf'(?m)^Result: {colored(33, "NOTESTS")}$', 'yellow NOTESTS')

    out, code = prove('--color', '-v', 'fail.py', 'directives.py')
    like_ok(out, r'(?m)^ok 1$', 'passed test point as it is')
    like_ok(out, rf'(?m)^{colored(31, "not ok 2")}$', 'red failed test point')
    like_ok(out, rf'(?m)^{colored(33, "not ok 2 # TODO later")}$', 'yellow TODO test point')
    like_ok(out, rf'(?m)^{colored(33, "ok 4 # SKIP why")}$', 'yellow skipped test point')

    out, code = prove('--color', '-v', '-j', '2', 'fail.py', 'pass.py')
    like_ok(out, rf'(?m)^{colored(31, "not ok 2")}$', 'red failed test point of parallel jobs')

    out, code = prove('--color', '--no-color', 'pass.py')
    unlike_ok(out, r'\033', 'no colors with --no-color')
    out, code = prove('-c', 'pass.py')
    like_ok(out, rf'(?m)^pass\.py \.+ {colored(32, "ok")}$', 'colors with -c')
    out, code = prove('--color', '--nocolor', 'pass.py')
    unlike_ok(out, r'\033', 'no colors with --nocolor')

with subtest('Colors on a terminal'):
    if not hasattr(os, 'openpty'):
        skip('no terminal', 5)
    else:
        out, code = prove_tty('pass.py')
        like_ok(out, rf'(?m)^pass\.py \.+ {colored(32, "ok")}$', 'colors by default')
        out, code = prove_tty('--no-color', 'pass.py')
        unlike_ok(out, r'\033', 'no colors with --no-color')
        out, code = prove_tty('pass.py', env={'NO_COLOR': '1'})
        unlike_ok(out, r'\033', 'no colors with NO_COLOR')
        out, code = prove_tty('--color', 'pass.py', env={'NO_COLOR': '1'})
        like_ok(out, rf'(?m)^pass\.py \.+ {colored(32, "ok")}$', '--color over NO_COLOR')
        out, code = prove_tty('pass.py', env={'TERM': 'dumb'})
        unlike_ok(out, r'\033', 'no colors on a dumb terminal')

with subtest('Verbose'):
    out, code = prove('-v', 'pass.py')
    like_ok(out, r'(?m)^ok 1 - first$', 'TAP output shown')
    like_ok(out, r'(?m)^    ok 1 - deep$', 'subtest output shown')

done_testing()
