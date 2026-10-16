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


def shell(command, cwd):
    # A `python` on PATH which is the interpreter running this test, and
    # Pyjoyment importable as if it was installed
    bindir = os.path.join(cwd, 'bin')
    os.makedirs(bindir, exist_ok=True)
    if not os.path.exists(os.path.join(bindir, 'python')):
        os.symlink(sys.executable, os.path.join(bindir, 'python'))
    env = dict(os.environ, PATH=os.pathsep.join([bindir, os.environ.get('PATH', '')]), PYTHONPATH=ROOT)
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

        with subtest('find_scripts'):
            names, _ = run("""
                scripts = find_scripts(['t'], '.py', recurse=True)
            """)
            is_ok(
                names['scripts'],
                [os.path.join('t', *p.split('/')) for p in ('Pyjo/URL.py', 'a.py', 'b.py', 'docs/URL.py', 'test.py')],
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
                results = asyncio.run(run(['t/a.py', 't/b.py'], timeout=60, trap=True))
            """)
            is_ok([r.path for r in names['results']], ['t/a.py', 't/b.py'], 'results with a timeout and trap')
            like_ok(out, r'(?m)^Result: PASS$', 'summary with a timeout and trap')

            names, out = run("""
                results = asyncio.run(run(['t/a.py', 't/b.py'], jobs=2, capture_stderr=True))
            """)
            is_ok([r.path for r in names['results']], ['t/a.py', 't/b.py'], 'results with the standard error captured')
            like_ok(out, r'(?m)^Result: PASS$', 'summary with the standard error captured')

        with subtest('main'):
            names, out = run("""
                sys.exit(main(['-r', 't']))
            """)
            is_ok(names['exit_status'], 0, 'exit status')
            like_ok(out, r'(?m)^Files=5, Tests=5, ', 'summary')
    finally:
        os.chdir(cwd)

done_testing()
