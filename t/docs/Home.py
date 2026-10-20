from Pyjo.File import path
from Pyjo.Test import *

import contextlib
import io
import os
import sys


with subtest('Synopsis'):
    from Pyjo.Home import Home

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        # Find and manage the project root directory
        home = Home()
        home.detect()
        print(home.child('templates', 'layouts', 'default.html.ep'))
        print(f'{home}')
    cwd = path().to_abs()
    is_ok(output.getvalue(), f'{cwd.child("templates", "layouts", "default.html.ep")}\n{cwd}\n', 'printed')

    import Pyjo.Home

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        # Find and manage the project root directory
        home = Pyjo.Home.new()
        home.detect()
        print(home.child('templates', 'layouts', 'default.html.ep'))
        print(f'{home}')
    cwd = path().to_abs()
    is_ok(output.getvalue(), f'{cwd.child("templates", "layouts", "default.html.ep")}\n{cwd}\n', 'printed')

with subtest('detect'):
    home = Pyjo.Home.new('/tmp')
    home = home.detect()
    is_ok(str(home), '/tmp', 'nothing detected')

    class MyApp:
        pass

    MyApp.__module__ = 'My.App'
    module = type(sys)('My.App')
    module.__file__ = os.path.join(os.sep, 'srv', 'myapp', 'lib', 'My', 'App.py')
    sys.modules['My.App'] = module
    # The absolute path, which has the drive of the working directory on Windows
    home = home.detect(MyApp)
    is_ok(str(home), os.path.abspath(os.path.join(os.sep, 'srv', 'myapp')), 'class')
    home = Pyjo.Home.new().detect('My.App')
    is_ok(str(home), os.path.abspath(os.path.join(os.sep, 'srv', 'myapp')), 'name')
    del sys.modules['My.App']

with subtest('rel_file'):
    home = Pyjo.Home.new('/srv/myapp')
    path_ = home.rel_file('foo/bar.html')
    isa_ok(path_, Pyjo.Home.object, 'home')
    is_ok(str(path_), os.path.join(os.sep, 'srv', 'myapp', 'foo', 'bar.html'), 'relative')

done_testing()
