import Pyjo.File

from Pyjo.Test import *

import importlib.metadata
import importlib.util
import os
import subprocess
import sys
import textwrap
import tomllib


if importlib.util.find_spec('pytest') is None:
    plan(skip_all='pytest is required, as of the dependency group "pytest"')

root = Pyjo.File.curfile().dirname().dirname().dirname()

# The plugin of the entry point where Pyjoyment is installed, as uv installs it, or of the checkout otherwise
entry_point = any(e.value == 'Pyjo.Test.pytest_plugin' for e in importlib.metadata.entry_points(group='pytest11'))
plugin = [] if entry_point else ['-p', 'Pyjo.Test.pytest_plugin']

env = dict(os.environ)
env['PYTHONPATH'] = os.pathsep.join([root.to_str(), *filter(None, [env.get('PYTHONPATH')])])

tmp = Pyjo.File.tempdir()


def pytest(dir, *args):
    p = subprocess.run(
        [
            sys.executable,
            '-m',
            'pytest',
            '-p',
            'no:cacheprovider',
            '-o',
            'console_output_style=classic',
            *plugin,
            *args,
        ],
        cwd=dir.to_str(),
        env=env,
        capture_output=True,
        text=True,
    )
    return p.stdout.replace('\\', '/'), p.returncode


def spew(path, content):
    path.dirname().make_path()
    path.spew(textwrap.dedent(content))


# The project of generate app, as in the synopsis
subprocess.run(
    [sys.executable, '-m', 'Pyjoyment', 'generate', 'app'], cwd=tmp.to_str(), env=env, capture_output=True, check=True
)
project = tmp.child('my_app')

with subtest('Synopsis'):
    out, code = pytest(project)
    like_ok(out, r'(?m)^testpaths: t$', 'testpaths of generate app')
    generated = tomllib.loads(project.child('pyproject.toml').slurp().decode())
    is_deeply_ok(generated['dependency-groups']['dev'], ['pytest>=9', 'pytest-xdist>=3'], 'pytest in the group dev')
    is_deeply_ok(generated['tool']['pytest']['ini_options'], {'testpaths': ['t'], 'pythonpath': ['.']}, 'ini options')
    like_ok(out, r'(?m)^t/basic\.py \.$', 'pytest')
    is_ok(code, 0, 'right exit status')

    out, code = pytest(project, '-v', 't/basic.py')
    like_ok(out, r'(?m)^t/basic\.py PASSED\b', 'pytest -v t/basic.py')
    is_ok(code, 0, 'right exit status')

    pyproject = project.child('pyproject.toml')
    pyproject.spew(pyproject.slurp().decode().replace('testpaths = ["t"]', 'testpaths = ["t", "tests"]'))
    spew(
        project.child('tests', 'conftest.py'),
        """\
        import pytest


        @pytest.fixture
        def app():
            return 'MyApp'
        """,
    )
    spew(
        project.child('tests', 'test_basic.py'),
        """\
        def test_index(t):
            t.get_ok('/').status_is(200).content_like(r'Pyjoyment')
        """,
    )
    out, code = pytest(project)
    like_ok(out, r'(?m)^testpaths: t, tests$', 'testpaths of the synopsis')
    like_ok(out, r'(?m)^t/basic\.py \.$', 'test script')
    like_ok(out, r'(?m)^tests/test_basic\.py \.$', 'test of pytest')
    is_ok(code, 0, 'right exit status')

with subtest('Ini options'):
    pyproject.spew(pyproject.slurp().decode() + 'pyjo_prove_paths = ["t", "xt"]\npyjo_prove_timeout = "60"\n')
    spew(
        project.child('xt', 'author.py'),
        """\
        from Pyjo.Test import *

        ok(True, 'an author test')

        done_testing()
        """,
    )
    out, code = pytest(project, 't', 'xt')
    like_ok(out, r'(?m)^t/basic\.py \.$', 'test script of t')
    like_ok(out, r'(?m)^xt/author\.py \.$', 'test script of xt')
    is_ok(code, 0, 'right exit status')

with subtest('Fixtures'):
    lite = tmp.child('lite')
    spew(lite.child('pyproject.toml'), '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n')
    spew(
        lite.child('myapp.py'),
        """\
        from Pyjoyment.Lite import *

        get('/', lambda c: c.render(text='Hello'))

        app.start()
        """,
    )
    spew(
        lite.child('tests', 'conftest.py'),
        """\
        import pytest

        import Pyjo.File


        @pytest.fixture
        def app():
            return Pyjo.File.curfile().dirname().sibling('myapp.py')
        """,
    )
    spew(
        lite.child('tests', 'test_index.py'),
        """\
        def test_index(t):
            t.get_ok('/').status_is(200)
        """,
    )
    out, code = pytest(lite)
    like_ok(out, r'(?m)^tests/test_index\.py \.$', 'test with the fixture t')
    is_ok(code, 0, 'right exit status')

done_testing()
