import Pyjo.File

from Pyjo.File import path, tempdir
from Pyjo.Test import *

import os
import pathlib
import shutil
import tempfile
import warnings


# The temporary objects of the standard library that Pyjo.File keeps warn when they are removed with it, as tempdir()
# and tempfile() do not
warnings.filterwarnings('ignore', message='Implicitly cleaning up', category=ResourceWarning)

with subtest('An os.PathLike'):
    dir = tempdir()
    file = dir.child('test.txt')
    isa_ok(file, os.PathLike, 'file')
    is_ok(os.fspath(file), file.to_str(), 'os.fspath()')
    with open(file, 'w') as f:
        f.write('works')
    ok(os.path.isfile(file), 'os.path')
    is_ok(file.slurp(), b'works', 'written with open()')
    shutil.copy(file, dir.child('copy.txt'))
    is_ok(dir.child('copy.txt').slurp(), b'works', 'shutil')
    is_deeply_ok(sorted(os.listdir(dir)), ['copy.txt', 'test.txt'], 'os.listdir()')

with subtest('pathlib'):
    p = pathlib.Path('/home/sri/.vimrc')
    file = Pyjo.File.new(p)
    is_ok(file, '/home/sri/.vimrc', 'from pathlib.Path')
    is_ok(pathlib.Path(file), p, 'pathlib.Path() of it')
    is_ok(file.to_path(), p, 'to_path()')
    isa_ok(file.to_path(), pathlib.Path, 'to_path()')
    is_ok(path(p.parent, p.name), file, 'parts from pathlib')

with subtest('Kept as given'):
    is_ok(path('foo/bar/'), 'foo/bar/', 'unlike pathlib.Path')
    is_ok(str(pathlib.Path('foo/bar/')), 'foo/bar', 'pathlib.Path normalizes')

with subtest('Temporary files of the standard library'):
    tmp = tempfile.TemporaryDirectory()
    dir = path(tmp)
    is_ok(dir, tmp.name, 'TemporaryDirectory')
    del tmp
    ok(os.path.isdir(dir), 'kept with the object')
    named = tempfile.NamedTemporaryFile()
    file = path(named)
    is_ok(file, named.name, 'NamedTemporaryFile')
    file = tempdir().child('test.txt').spew('works')
    is_ok(file.slurp(), b'works', 'a child keeps the temporary directory')

with subtest('Context manager'):
    with tempdir() as dir:
        file = dir.child('test.txt').spew('works')
        ok(os.path.isfile(file), 'temporary directory')
    ok(not os.path.exists(dir), 'removed at the end of the block')
    ok(not os.path.exists(file), 'with its files, which a child keeps no longer')
    with Pyjo.File.tempfile() as file:
        ok(os.path.isfile(file), 'temporary file')
    ok(not os.path.exists(file), 'removed at the end of the block')
    with path(tempfile.TemporaryDirectory()) as dir:
        ok(os.path.isdir(dir), 'TemporaryDirectory')
    ok(not os.path.exists(dir), 'cleaned up at the end of the block')
    with warnings.catch_warnings(record=True) as warned:
        warnings.simplefilter('always')
        with path(tempfile.NamedTemporaryFile()) as file:
            ok(os.path.isfile(file), 'NamedTemporaryFile')
    ok(not os.path.exists(file), 'closed at the end of the block')
    is_ok(len(warned), 0, 'without a ResourceWarning')
    with path('/home/sri/.vimrc') as file:
        is_ok(file, '/home/sri/.vimrc', 'a path without a temporary file')
    is_ok(file, '/home/sri/.vimrc', 'kept')

with subtest('stat'):
    file = tempdir().child('test.txt').spew('1234')
    isa_ok(file.stat(), os.stat_result, 'os.stat_result')
    is_ok(file.stat(), os.stat(file), 'as os.stat() gives it')

done_testing()
