import Pyjo.Prove

from Pyjo.Test import *

import ast
import asyncio
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time

from pathlib import Path


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

PASS = "from Pyjo.Test import *\n\nok(True, 'works')\n\ndone_testing()\n"


def scripts(tmp):
    # The test scripts the documented code runs
    for name, code in {
        't/a.py': PASS,
        't/b.py': PASS,
        't/test.py': PASS,
        't/Pyjo/URL.py': PASS,
        't/docs/URL.py': PASS,
    }.items():
        path = os.path.join(tmp, *name.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(code)


def shell(command, cwd, **env):
    # A `python` on PATH which is the interpreter running this test, and
    # Pyjoyment importable as if it was installed
    bindir = os.path.join(cwd, 'bin')
    os.makedirs(bindir, exist_ok=True)
    if not os.path.exists(os.path.join(bindir, 'python')):
        os.symlink(sys.executable, os.path.join(bindir, 'python'))
    env = dict(
        {k: v for k, v in os.environ.items() if k != 'PYJO_PROVE_OPTS'},
        PATH=os.pathsep.join([bindir, os.environ.get('PATH', '')]),
        PYTHONPATH=ROOT,
        **env,
    )
    p = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, env=env)
    return p.stdout, p.returncode


def run(code, **names):
    # The documented code runs in a namespace of its own, with the names it
    # uses; a top-level `await` is allowed, as in an async function
    namespace = {'asyncio': asyncio, 'os': os, 'sys': sys, **vars(Pyjo.Prove), **names}
    compiled = compile(textwrap.dedent(code), '<doc>', 'exec', flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        try:
            if coroutine := eval(compiled, namespace):
                asyncio.run(coroutine)
        except SystemExit as e:
            namespace['exit_status'] = e.code
    return namespace, out.getvalue()


with subtest('Synopsis'):
    with tempfile.TemporaryDirectory() as tmp:
        scripts(tmp)

        out, code = shell('python -m Pyjo.Prove t/Pyjo t/docs', tmp)
        like_ok(out, r'(?m)^t/Pyjo/URL\.py \.+ ok\nt/docs/URL\.py \.+ ok$', 'python -m Pyjo.Prove t/Pyjo t/docs')
        like_ok(out, r'(?m)^Files=2, Tests=2, ', 'two scripts')
        is_ok(code, 0, 'right exit status')

        out, code = shell('python -m Pyjo.Prove -r -j 4 t', tmp)
        like_ok(out, r'(?m)^Files=5, Tests=5, ', 'python -m Pyjo.Prove -r -j 4 t')
        is_ok(code, 0, 'right exit status')

        if shutil.which('pyjo-prove'):
            out, code = shell('pyjo-prove -v t/Pyjo/URL.py', tmp)
            like_ok(out, r'(?m)^ok 1 - works$', 'pyjo-prove -v t/Pyjo/URL.py')
            is_ok(code, 0, 'right exit status')
        else:
            skip('pyjo-prove is not installed', 2)

with subtest('Options'):
    with tempfile.TemporaryDirectory() as tmp:
        scripts(tmp)
        out, code = shell('python -m Pyjo.Prove -j 0 -r t', tmp)
        like_ok(out, r'(?m)^Files=5, Tests=5, ', 'python -m Pyjo.Prove -j 0 -r t')
        is_ok(code, 0, 'right exit status')

with subtest('Options of the reports'):
    with tempfile.TemporaryDirectory() as tmp:
        scripts(tmp)
        out, code = shell('python -m Pyjo.Prove --formatter junit -r t > report.xml', tmp)
        is_ok(out, '', 'python -m Pyjo.Prove --formatter junit -r t > report.xml')
        like_ok(Path(tmp, 'report.xml').read_text(), r'<testsuites errors="0" failures="0" name="Pyjo.Prove"', 'report')

        # A variable in the command is of a shell of POSIX, which the cmd.exe of Windows is not
        if sys.platform == 'win32':
            skip('no shell of POSIX on Windows', 3)
        else:
            summary = os.path.join(tmp, 'summary.md')
            out, code = shell(
                'python -m Pyjo.Prove --capture-stderr --formatter junit=report.xml \\\n'
                '    --formatter "markdown=$GITHUB_STEP_SUMMARY" -r t',
                tmp,
                GITHUB_STEP_SUMMARY=summary,
            )
            like_ok(out, r'(?m)^Files=5, Tests=5, ', 'usual output')
            like_ok(Path(tmp, 'report.xml').read_text(), r'<testsuites ', 'report')
            like_ok(Path(summary).read_text(), r'(?m)^Result: \*\*PASS\*\*$', 'summary')

with subtest('Environment'):
    # A variable before the command is of a shell of POSIX, which the cmd.exe of Windows is not
    if sys.platform == 'win32':
        skip('no shell of POSIX on Windows', 2)
    else:
        with tempfile.TemporaryDirectory() as tmp:
            scripts(tmp)
            out, code = shell("PYJO_PROVE_OPTS='-l -j 4' python -m Pyjo.Prove -r t", tmp)
            like_ok(out, r'(?m)^Files=5, Tests=5, ', "PYJO_PROVE_OPTS='-l -j 4' python -m Pyjo.Prove -r t")
            is_ok(code, 0, 'right exit status')

with subtest('Description'):
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, 't'))
        with open(os.path.join(tmp, 't', 'new.py'), 'w') as f:
            f.write(
                textwrap.dedent("""\
                    # /// script
                    # requires-python = ">=3.14"
                    # ///
                """)
                + PASS
            )
        out, code = shell('python -m Pyjo.Prove t/new.py', tmp)
        if sys.version_info >= (3, 14):
            like_ok(out, r'(?m)^t/new\.py \.+ ok$', 'runs on Python 3.14')
        else:
            like_ok(out, r'(?m)^t/new\.py \.+ skipped: requires Python >=3\.14$', 'skipped before Python 3.14')
        is_ok(code, 0, 'right exit status')

with tempfile.TemporaryDirectory() as tmp:
    scripts(tmp)
    cwd = os.getcwd()
    os.environ['PYTHONPATH'] = ROOT
    os.chdir(tmp)
    try:
        with subtest('passed'):
            names, _ = run(
                """
                ok = result.passed
                """,
                result=Pyjo.Prove.Result('t/test.py', planned=1, tests=1),
            )
            is_ok(names['ok'], True, 'ok')

        with subtest('parse'):
            names, _ = run(
                """
                result = Result('t/test.py')
                for line in output.splitlines():
                    parse(result, line)
                """,
                output='ok 1\nnot ok 2\n1..2\n',
            )
            is_ok(names['result'].tests, 2, 'result.tests')
            is_ok(names['result'].failed, [2], 'result.failed')

        with subtest('parse at'):
            names, _ = run(
                """
                result = Result('t/test.py')
                parse(result, line, at=time.monotonic())
                """,
                line='ok 1',
                time=time,
            )
            is_ok(names['result'].points[0].name, '', 'point')

        with subtest('Point.failed'):
            names, _ = run(
                """
                failed = point.failed
                """,
                point=Pyjo.Prove.Point(1, ok=False),
            )
            is_ok(names['failed'], True, 'failed')

        with subtest('Point.skipped'):
            names, _ = run(
                """
                skipped = point.skipped
                """,
                point=Pyjo.Prove.Point(1, ok=False, directive='todo'),
            )
            is_ok(names['skipped'], True, 'skipped')

        with subtest('junit'):
            results = [Pyjo.Prove.Result('t/test.py', planned=1, tests=1, points=[Pyjo.Prove.Point(1, 'works')])]
            run(
                """
                report = junit(results)
                Path('report.xml').write_text(str(report))
                """,
                results=results,
                Path=Path,
            )
            like_ok(
                Path('report.xml').read_text(),
                r'<testcase classname="t/test.py" file="t/test.py" name="1 - works"',
                'report',
            )

        with subtest('markdown'):
            names, _ = run(
                """
                summary = markdown(results, 37.2)
                summary = markdown(results, 37.2, title='Tests of Pyjo')
                """,
                results=results,
            )
            like_ok(names['summary'], r'^### Tests of Pyjo\n', 'title')
            like_ok(names['summary'], r'(?m)^\| 1 \| 1 \| 1 \| 0 \| 0 \| 37s \|$', 'numbers')

        with subtest('finish'):
            result = Pyjo.Prove.Result('t/test.py', planned=2, tests=1, exit_status=255)
            run(
                """
                finish(result)
                """,
                result=result,
            )
            is_ok(
                result.errors,
                ['Bad plan.  You planned 2 tests but ran 1.', 'Non-zero exit status: 255'],
                'result.errors',
            )

        with subtest('run_script'):
            names, _ = run("""
                result = await run_script('t/test.py', [sys.executable], dict(os.environ))
            """)
            is_ok(names['result'].passed, True, 'result.passed')
            is_ok(names['result'].exit_status, 0, 'result.exit_status')

            names, _ = run("""
                result = await run_script('t/test.py', [sys.executable], dict(os.environ), timeout=60)
            """)
            is_ok(names['result'].passed, True, 'result.passed with a timeout')
            is_ok(names['result'].timed_out, None, 'result.timed_out')

            names, _ = run("""
                result = await run_script('t/test.py', [sys.executable], dict(os.environ), capture_stderr=True)
            """)
            is_ok(names['result'].passed, True, 'result.passed with the standard error captured')
            is_deeply_ok(names['result'].stderr, [], 'result.stderr')

            names, _ = run("""
                result = await run_script('t/test.py', [sys.executable], dict(os.environ), capture_stderr=True, stderr_lines=100)
            """)
            is_ok(names['result'].passed, True, 'result.passed with a limit of the standard error')
            is_ok(names['result'].stderr_left_out, 0, 'result.stderr_left_out')

            names, out = run("""
                result = await run_script('t/test.py', [sys.executable], dict(os.environ), progress=print)
            """)
            is_ok(names['result'].passed, True, 'result.passed with the progress')
            is_ok(out.count("Result(path='t/test.py'"), 2, 'progress at the start and after the test')

            shutil.copytree('t', os.path.join('project', 't'))
            names, _ = run("""
                result = await run_script('t/test.py', [sys.executable], dict(os.environ), cwd='project')
            """)
            is_ok(names['result'].passed, True, 'result.passed in the directory')
            is_ok(names['result'].path, 't/test.py', 'result.path relative to the directory')

        with subtest('find_scripts'):
            names, _ = run("""
                scripts = find_scripts(['t'], '.py', recurse=True)
            """)
            is_ok(
                names['scripts'],
                ['t/Pyjo/URL.py', 't/a.py', 't/b.py', 't/docs/URL.py', 't/test.py'],
                'scripts',
            )

        with subtest('run'):
            names, out = run("""
                results = asyncio.run(run(['t/a.py', 't/b.py'], jobs=2))
            """)
            is_ok([r.path for r in names['results']], ['t/a.py', 't/b.py'], 'results')
            like_ok(out, r'(?m)^t/a\.py \.+ ok$', 'line for t/a.py')
            like_ok(out, r'(?m)^Result: PASS$', 'summary')

            names, out = run("""
                results = asyncio.run(run(['t/a.py', 't/b.py'], jobs=0))
            """)
            is_ok([r.path for r in names['results']], ['t/a.py', 't/b.py'], 'results with the jobs of the processors')
            like_ok(out, r'(?m)^Result: PASS$', 'summary with the jobs of the processors')

            names, out = run("""
                results = asyncio.run(run(['t/a.py', 't/b.py'], timeout=60, trap=True))
            """)
            is_ok([r.path for r in names['results']], ['t/a.py', 't/b.py'], 'results with a timeout and trap')
            like_ok(out, r'(?m)^Result: PASS$', 'summary with a timeout and trap')

            names, out = run("""
                results = asyncio.run(run(['t/a.py', 't/b.py'], jobs=2, capture_stderr=True))
            """)
            is_ok([r.path for r in names['results']], ['t/a.py', 't/b.py'], 'results with the standard error captured')
            like_ok(out, r'(?m)^Result: PASS$', 'summary with the standard error captured')

            names, out = run("""
                results = asyncio.run(run(['t/a.py', 't/b.py'], jobs=2, capture_stderr=True, stderr_lines=1000))
            """)
            is_ok(
                [r.path for r in names['results']], ['t/a.py', 't/b.py'], 'results with a limit of the standard error'
            )
            like_ok(out, r'(?m)^Result: PASS$', 'summary with a limit of the standard error')

            names, out = run("""
                results = asyncio.run(run(['t/a.py', 't/b.py'], color=False))
            """)
            is_ok([r.path for r in names['results']], ['t/a.py', 't/b.py'], 'results without colors')
            unlike_ok(out, r'\033', 'no colors')

            names, out = run("""
                results = asyncio.run(run(['t/a.py', 't/b.py'], count=False))
            """)
            is_ok([r.path for r in names['results']], ['t/a.py', 't/b.py'], 'results without the count')
            unlike_ok(out, r'\r', 'no count')

        with subtest('main'):
            names, out = run("""
                sys.exit(main(['-r', 't']))
            """)
            is_ok(names['exit_status'], 0, 'exit status')
            like_ok(out, r'(?m)^Files=5, Tests=5, ', 'summary')
    finally:
        os.chdir(cwd)

done_testing()
