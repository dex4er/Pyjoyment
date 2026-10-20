import Pyjo.File
import Pyjoyment
import Pyjoyment.Command.Author.generate.pyproject

from Pyjo.Test import *

import contextlib
import io
import os
import tomllib


cwd = Pyjo.File.path()

with subtest('Synopsis'):
    application = Pyjoyment.new()
    pyproject = Pyjoyment.Command.Author.generate.pyproject.new(app=application)
    like_ok(
        pyproject.usage,
        r'^Usage: APPLICATION generate pyproject \[OPTIONS\]\n\n  \./myapp\.py generate pyproject\n',
        'usage',
    )

with subtest('Description'):
    application = Pyjoyment.new()
    pyproject = Pyjoyment.Command.Author.generate.pyproject.new(app=application)
    tmp = Pyjo.File.tempdir()
    dir = tmp.child('my_app').make_path()
    os.chdir(dir)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            pyproject.run()
    finally:
        os.chdir(cwd)
    project = tomllib.loads(dir.child('pyproject.toml').slurp().decode())
    is_ok(project['project']['name'], 'my_app', 'name of the current directory')
    like_ok(project['project']['dependencies'][0], r'^Pyjoyment', 'dependencies')
    ok('build-system' not in project, 'no build system')
    ok('tool' not in project, 'no testpaths of pytest without t')
    ok('dependency-groups' not in project, 'no pytest without t')
    dir = tmp.child('my_tested_app').make_path()
    dir.child('t').make_path()
    os.chdir(dir)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            pyproject.run()
    finally:
        os.chdir(cwd)
    project = tomllib.loads(dir.child('pyproject.toml').slurp().decode())
    is_deeply_ok(project['tool']['pytest']['ini_options']['testpaths'], ['t'], 'testpaths of pytest with t')
    is_deeply_ok(project['tool']['pytest']['ini_options']['pythonpath'], ['.'], 'pythonpath of pytest with t')
    is_deeply_ok(project['dependency-groups']['dev'], ['pytest>=9', 'pytest-xdist>=3'], 'pytest in the group dev')

with subtest('Attributes'):
    pyproject = Pyjoyment.Command.Author.generate.pyproject.new()
    is_ok(pyproject.description, 'Generate "pyproject.toml"', 'description')
    like_ok(pyproject.usage, r'generate pyproject', 'usage')

done_testing()
