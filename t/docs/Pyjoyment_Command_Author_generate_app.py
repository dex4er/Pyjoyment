import Pyjo.File
import Pyjoyment
import Pyjoyment.Command.Author.generate.app

from Pyjo.Test import *

import contextlib
import io
import os
import subprocess
import sys


# The modules of the checkout for the generated application, which runs in a process of its own
root = Pyjo.File.path(__file__).to_abs().dirname().dirname().dirname().to_str()
env = {**os.environ, 'PYTHONPATH': os.pathsep.join([root, *filter(None, [os.environ.get('PYTHONPATH')])])}
cwd = Pyjo.File.path()


def python(*args, dir):
    return subprocess.run([sys.executable, *args], cwd=dir, env=env, capture_output=True, text=True)


with subtest('Synopsis'):
    application = Pyjoyment.new()
    app = Pyjoyment.Command.Author.generate.app.new(app=application)
    like_ok(app.usage, r'^Usage: APPLICATION generate app \[OPTIONS\] \[NAME\]\n\n  pyjo generate app\n', 'usage')
    tmp = Pyjo.File.tempdir()
    os.chdir(tmp)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            app.run()
            app.run('TestApp')
            app.run('My.TestApp')
    finally:
        os.chdir(cwd)
    ok(os.path.isfile(tmp.child('my_app', 'MyApp', '__init__.py').to_str()), 'pyjo generate app')
    ok(os.path.isfile(tmp.child('test_app', 'TestApp', '__init__.py').to_str()), 'pyjo generate app TestApp')
    ok(
        os.path.isfile(tmp.child('my_test_app', 'My', 'TestApp', '__init__.py').to_str()),
        'pyjo generate app My.TestApp',
    )

    # Not in Mojolicious: the class under the name of its module, unless it has it already
    module = tmp.child('my_test_app', 'My', 'TestApp', '__init__.py').slurp('UTF-8')
    like_ok(module, r'\nTestApp = My_TestApp\n', 'application class under the name of its module')
    unlike_ok(tmp.child('my_app', 'MyApp', '__init__.py').slurp('UTF-8'), r'\nMyApp = ', 'named after its module')
    controller = tmp.child('my_app', 'MyApp', 'Controller', 'Example.py').slurp('UTF-8')
    like_ok(controller, r'\nExample = MyApp_Controller_Example\n', 'controller class under the name of its module')

with subtest('Description'):
    application = Pyjoyment.new()
    app = Pyjoyment.Command.Author.generate.app.new(app=application)
    tmp = Pyjo.File.tempdir()
    os.chdir(tmp)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            app.run()
    finally:
        os.chdir(cwd)
    dir = tmp.child('my_app').to_str()
    like_ok(tmp.child('my_app', 'pyproject.toml').slurp().decode(), r'dependencies = \["Pyjoyment', 'dependencies')
    result = python('-m', 'MyApp', 'get', '/', dir=dir)
    like_ok(result.stdout, r'<h2>Welcome to the Pyjoyment real-time web framework!</h2>', 'python -m MyApp')
    result = python('-m', 'MyApp', 'eval', '-v', 'app.home', dir=dir)
    # Both real, as a temporary directory of Windows may have the short names of 8.3, as C:\Users\RUNNER~1
    is_ok(Pyjo.File.path(result.stdout.strip()).realpath().to_str(), Pyjo.File.path(dir).realpath().to_str(), 'home')
    result = python('-m', 'Pyjo.Prove', '-l', '-r', 't', dir=dir)
    like_ok(result.stdout, r'Result: PASS', 'python -m Pyjo.Prove -l -r t')

with subtest('Attributes'):
    app = Pyjoyment.Command.Author.generate.app.new()
    is_ok(app.description, 'Generate Pyjoyment application directory structure', 'description')
    like_ok(app.usage, r'generate app', 'usage')

done_testing()
