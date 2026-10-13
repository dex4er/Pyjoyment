import Pyjo.Home

from Pyjo.File import tempdir
from Pyjo.Test import *

import importlib
import os
import pathlib
import sys


dir = tempdir()
root = pathlib.Path(dir.to_str()).resolve()
for package in ('flat_app', 'src/src_app', 'lib/lib_app'):
    (root / package).mkdir(parents=True)
    (root / package / '__init__.py').write_text('class App:\n    pass\n')
    (root / package / 'controller.py').write_text('class Controller:\n    pass\n')
sys.path[:0] = [str(root), str(root / 'src'), str(root / 'lib')]

with subtest('A package'):
    module = importlib.import_module('flat_app')
    is_ok(str(Pyjo.Home.new().detect(module)), str(root), 'module')
    is_ok(str(Pyjo.Home.new().detect(module.App)), str(root), 'class')
    is_ok(str(Pyjo.Home.new().detect('flat_app')), str(root), 'name')
    is_ok(str(Pyjo.Home.new().detect('flat_app.App')), str(root), 'name of the class')

with subtest('A module of a package'):
    module = importlib.import_module('flat_app.controller')
    is_ok(str(Pyjo.Home.new().detect(module.Controller)), str(root), 'class')
    is_ok(str(Pyjo.Home.new().detect('flat_app.controller.Controller')), str(root), 'name of the class')

with subtest('src and lib layouts'):
    is_ok(str(Pyjo.Home.new().detect(importlib.import_module('src_app'))), str(root), 'src')
    is_ok(str(Pyjo.Home.new().detect(importlib.import_module('lib_app'))), str(root), 'lib')

with subtest('Not loaded'):
    home = Pyjo.Home.new(root)
    is_ok(str(home.detect('not_loaded_app')), str(root), 'unchanged')
    is_ok(str(home.detect(sys)), str(root), 'module without a file')

with subtest('The environment comes first'):
    os.environ['PYJO_HOME'] = str(root / 'elsewhere')
    is_ok(str(Pyjo.Home.new().detect('flat_app')), str(root / 'elsewhere'), 'PYJO_HOME')
    del os.environ['PYJO_HOME']

with subtest('A path'):
    home = Pyjo.Home.new(root)
    is_ok(os.fspath(home), str(root), 'os.fspath')
    is_ok(pathlib.Path(home.rel_file('templates/index.html')), root / 'templates' / 'index.html', 'pathlib')

done_testing()
