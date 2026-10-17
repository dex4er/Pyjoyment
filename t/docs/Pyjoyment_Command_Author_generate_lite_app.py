import Pyjo.File
import Pyjoyment
import Pyjoyment.Command.Author.generate.lite_app

from Pyjo.Test import *

import contextlib
import io
import os
import subprocess
import sys


# The modules of the checkout for the generated application, which runs in a process of its own
root = Pyjo.File.path(__file__).to_abs().dirname().dirname().dirname().to_str()
env = {**os.environ, 'PYTHONPATH': os.pathsep.join([root, *filter(None, [os.environ.get('PYTHONPATH')])])}
env.pop('PYJO_EXE', None)
cwd = Pyjo.File.path()

with subtest('Synopsis'):
    application = Pyjoyment.new()
    app = Pyjoyment.Command.Author.generate.lite_app.new(app=application)
    like_ok(
        app.usage, r'^Usage: APPLICATION generate lite-app \[OPTIONS\] \[NAME\]\n\n  pyjo generate lite-app\n', 'usage'
    )
    tmp = Pyjo.File.tempdir()
    os.chdir(tmp)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            app.run()
            app.run('foo.py')
    finally:
        os.chdir(cwd)
    ok(os.path.isfile(tmp.child('myapp.py').to_str()), 'pyjo generate lite-app')
    ok(os.path.isfile(tmp.child('foo.py').to_str()), 'pyjo generate lite-app foo.py')
    ok(os.access(tmp.child('foo.py').to_str(), os.X_OK), 'executable')

with subtest('Description'):
    application = Pyjoyment.new()
    app = Pyjoyment.Command.Author.generate.lite_app.new(app=application)
    tmp = Pyjo.File.tempdir()
    os.chdir(tmp)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            app.run('foo.py')
    finally:
        os.chdir(cwd)
    result = subprocess.run(
        [sys.executable, 'foo.py', 'get', '/'], cwd=tmp.to_str(), env=env, capture_output=True, text=True
    )
    like_ok(result.stdout, r'<h1>Welcome to the Pyjoyment real-time web framework!</h1>', 'fully functional')

with subtest('Attributes'):
    app = Pyjoyment.Command.Author.generate.lite_app.new()
    is_ok(app.description, 'Generate Pyjoyment.Lite application', 'description')
    like_ok(app.usage, r'generate lite-app', 'usage')

done_testing()
