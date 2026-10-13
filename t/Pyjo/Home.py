import Pyjo.Home

from Pyjo.File import curfile, path
from Pyjo.Test import *

import contextlib
import os
import sys
import types


# local $INC{'My/Class.pm'}: a module that is loaded from the file
@contextlib.contextmanager
def module(name, file):
    sys.modules[name] = types.ModuleType(name)
    sys.modules[name].__file__ = file
    try:
        yield
    finally:
        del sys.modules[name]


with subtest('ENV detection'):
    fake = path().to_abs().child('does_not_exist')
    os.environ['PYJO_HOME'] = fake.to_str()
    home = Pyjo.Home.new().detect()
    is_deeply_ok(home.to_array(), fake.to_array(), 'right path detected')
    del os.environ['PYJO_HOME']

with subtest('Specific class detection'):
    fake = path().to_abs().child('does_not_exist_2')
    with module('My.Class', fake.child('My', 'Class.py').to_str()):
        home = Pyjo.Home.new().detect('My.Class')
        is_deeply_ok(home.to_array(), fake.to_array(), 'right path detected')

with subtest('Specific class detection (with "lib")'):
    fake = path().to_abs().child('does_not_exist_3')
    with module('My.Class', fake.child('lib', 'My', 'Class.py').to_str()):
        home = Pyjo.Home.new().detect('My.Class')
        is_deeply_ok(home.to_array(), fake.to_array(), 'right path detected')

with subtest('Specific class detection (with "blib/lib")'):
    fake = path().to_abs().child('does_not_exist_3')
    with module('My.Class', fake.child('blib', 'lib', 'My', 'Class.py').to_str()):
        home = Pyjo.Home.new().detect('My.Class')
        is_deeply_ok(home.to_array(), fake.to_array(), 'right path detected')

with subtest('Specific class detection (relative)'):
    with module('My.Class', path('My', 'Class.py').to_str()):
        home = Pyjo.Home.new().detect('My.Class')
        is_deeply_ok(home.to_array(), path().to_array(), 'right path detected')

with subtest('Specific class detection (relative "blib/lib")'):
    with module('My.Class', path('blib', 'lib', 'My', 'Class.py').to_str()):
        home = Pyjo.Home.new().detect('My.Class')
        is_deeply_ok(home.to_array(), path().to_array(), 'right path detected')

with subtest('Current working directory'):
    home = Pyjo.Home.new().detect()
    is_deeply_ok(home.to_array(), path().to_abs().to_array(), 'right path detected')

with subtest('Path generation'):
    home = Pyjo.Home.new(curfile().dirname())
    path_ = curfile().dirname()
    is_ok(str(home.rel_file('foo.txt')), str(path_.child('foo.txt')), 'right path')
    is_ok(str(home.rel_file('foo/bar.txt')), str(path_.child('foo', 'bar.txt')), 'right path')
    is_ok(home.rel_file('foo/bar.txt').basename(), 'bar.txt', 'right result')

done_testing()
