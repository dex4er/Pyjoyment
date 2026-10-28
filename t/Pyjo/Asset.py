import Pyjo.Asset
import Pyjo.Asset.File
import Pyjo.Asset.Memory

from Pyjo.File import path, tempdir
from Pyjo.Test import *

import gc
import io
import os
import re


with subtest('File asset'):
    file = Pyjo.Asset.File.new()
    is_ok(file.size, 0, 'file is empty')
    is_ok(file.mtime, os.fstat(file.handle.fileno()).st_mtime, 'right mtime')
    is_ok(file.slurp(), b'', 'file is empty')
    file.add_chunk(b'abc')
    is_ok(file.contains(b'abc'), 0, '"abc" at position 0')
    is_ok(file.contains(b'bc'), 1, '"bc" at position 1')
    is_ok(file.contains(b'db'), -1, 'does not contain "db"')
    is_ok(file.size, 3, 'right size')
    is_ok(file.mtime, os.fstat(file.handle.fileno()).st_mtime, 'right mtime')
    is_ok(file.to_file(), file, 'same object')

    p = file.path
    ok(os.path.exists(p), 'temporary file exists')
    del file
    # Not in Mojolicious: PyPy frees objects only when its garbage collector runs
    gc.collect()
    ok(not os.path.exists(p), 'temporary file has been cleaned up')

with subtest('Memory asset'):
    mem = Pyjo.Asset.Memory.new()
    mem.add_chunk(b'abc')
    is_ok(mem.contains(b'abc'), 0, '"abc" at position 0')
    is_ok(mem.contains(b'bc'), 1, '"bc" at position 1')
    is_ok(mem.contains(b'db'), -1, 'does not contain "db"')
    is_ok(mem.size, 3, 'right size')
    is_ok(mem.mtime, Pyjo.Asset.Memory.MTIME, 'right mtime')
    is_ok(mem.mtime, Pyjo.Asset.Memory.new().mtime, 'same mtime')
    mtime = mem.mtime
    mem.mtime = mtime + 23
    is_ok(mem.mtime, mtime + 23, 'right mtime')

with subtest('Asset upgrade from memory to file'):
    mem = Pyjo.Asset.Memory.new()
    mem.add_chunk(b'abcdef')
    isa_ok(mem.to_file(), Pyjo.Asset.File.object, 'right class')
    is_ok(mem.to_file().slurp(), mem.slurp(), 'same content')
    file = mem.to_file()
    p = file.path
    ok(os.path.exists(p), 'file exists')
    del file
    # Not in Mojolicious: PyPy frees objects only when its garbage collector runs
    gc.collect()
    ok(not os.path.exists(p), 'file has been cleaned up')

with subtest('Empty file asset'):
    file = Pyjo.Asset.File.new()
    is_ok(file.size, 0, 'asset is empty')
    is_ok(file.get_chunk(0), b'', 'no content')
    is_ok(file.slurp(), b'', 'no content')
    is_ok(file.contains(b'a'), -1, 'does not contain "a"')

with subtest('Empty memory asset'):
    mem = Pyjo.Asset.Memory.new()
    is_ok(mem.size, 0, 'asset is empty')
    is_ok(mem.get_chunk(0), b'', 'no content')
    is_ok(mem.slurp(), b'', 'no content')
    ok(not mem.is_range, 'no range')
    is_ok(mem.contains(b'a'), -1, 'does not contain "a"')

with subtest('File asset range support (a[bcdefabc])'):
    file = Pyjo.Asset.File.new(start_range=1)
    ok(file.is_range, 'has range')
    file.add_chunk(b'abcdefabc')
    is_ok(file.contains(b'bcdef'), 0, '"bcdef" at position 0')
    is_ok(file.contains(b'cdef'), 1, '"cdef" at position 1')
    is_ok(file.contains(b'abc'), 5, '"abc" at position 5')
    is_ok(file.contains(b'db'), -1, 'does not contain "db"')

with subtest('Memory asset range support (a[bcdefabc])'):
    mem = Pyjo.Asset.Memory.new(start_range=1)
    ok(mem.is_range, 'has range')
    mem.add_chunk(b'abcdefabc')
    is_ok(mem.contains(b'bcdef'), 0, '"bcdef" at position 0')
    is_ok(mem.contains(b'cdef'), 1, '"cdef" at position 1')
    is_ok(mem.contains(b'abc'), 5, '"abc" at position 5')
    is_ok(mem.contains(b'db'), -1, 'does not contain "db"')

with subtest('File asset range support (ab[cdefghi]jk)'):
    file = Pyjo.Asset.File.new(start_range=2, end_range=8)
    ok(file.is_range, 'has range')
    file.add_chunk(b'abcdefghijk')
    is_ok(file.contains(b'cdefghi'), 0, '"cdefghi" at position 0')
    is_ok(file.contains(b'fghi'), 3, '"fghi" at position 3')
    is_ok(file.contains(b'f'), 3, '"f" at position 3')
    is_ok(file.contains(b'hi'), 5, '"hi" at position 5')
    is_ok(file.contains(b'db'), -1, 'does not contain "db"')
    is_ok(file.get_chunk(0), b'cdefghi', 'chunk from position 0')
    is_ok(file.get_chunk(1), b'defghi', 'chunk from position 1')
    is_ok(file.get_chunk(5), b'hi', 'chunk from position 5')
    is_ok(file.get_chunk(0, 2), b'cd', 'chunk from position 0 (2 bytes)')
    is_ok(file.get_chunk(1, 3), b'def', 'chunk from position 1 (3 bytes)')
    is_ok(file.get_chunk(5, 1), b'h', 'chunk from position 5 (1 byte)')
    is_ok(file.get_chunk(5, 3), b'hi', 'chunk from position 5 (2 byte)')

with subtest('Memory asset range support (ab[cdefghi]jk)'):
    mem = Pyjo.Asset.Memory.new(start_range=2, end_range=8)
    ok(mem.is_range, 'has range')
    mem.add_chunk(b'abcdefghijk')
    is_ok(mem.contains(b'cdefghi'), 0, '"cdefghi" at position 0')
    is_ok(mem.contains(b'fghi'), 3, '"fghi" at position 3')
    is_ok(mem.contains(b'f'), 3, '"f" at position 3')
    is_ok(mem.contains(b'hi'), 5, '"hi" at position 5')
    is_ok(mem.contains(b'ij'), -1, 'does not contain "ij"')
    is_ok(mem.contains(b'db'), -1, 'does not contain "db"')
    is_ok(mem.get_chunk(0), b'cdefghi', 'chunk from position 0')
    is_ok(mem.get_chunk(1), b'defghi', 'chunk from position 1')
    is_ok(mem.get_chunk(5), b'hi', 'chunk from position 5')
    is_ok(mem.get_chunk(0, 2), b'cd', 'chunk from position 0 (2 bytes)')
    is_ok(mem.get_chunk(1, 3), b'def', 'chunk from position 1 (3 bytes)')
    is_ok(mem.get_chunk(5, 1), b'h', 'chunk from position 5 (1 byte)')
    is_ok(mem.get_chunk(5, 3), b'hi', 'chunk from position 5 (2 byte)')

with subtest('File asset range support ([a]bcdef)'):
    file = Pyjo.Asset.File.new(end_range=0)
    file.add_chunk(b'abcdef')
    is_ok(file.get_chunk(0), b'a', 'chunk from position 0')
    is_ok(file.get_chunk(1), b'', 'chunk from position 1')

with subtest('Memory asset range support ([a]bcdef)'):
    mem = Pyjo.Asset.Memory.new(end_range=0)
    mem.add_chunk(b'abcdef')
    is_ok(mem.get_chunk(0), b'a', 'chunk from position 0')
    is_ok(mem.get_chunk(1), b'', 'chunk from position 1')

with subtest('Huge file asset'):
    file = Pyjo.Asset.File.new()
    ok(not file.is_range, 'no range')
    file.add_chunk(b'a' * 131072)
    file.add_chunk(b'b')
    file.add_chunk(b'c' * 131072)
    file.add_chunk(b'ddd')
    is_ok(file.contains(b'a'), 0, '"a" at position 0')
    is_ok(file.contains(b'b'), 131072, '"b" at position 131072')
    is_ok(file.contains(b'c'), 131073, '"c" at position 131073')
    is_ok(file.contains(b'abc'), 131071, '"abc" at position 131071')
    is_ok(file.contains(b'ccdd'), 262143, '"ccdd" at position 262143')
    is_ok(file.contains(b'dd'), 262145, '"dd" at position 262145')
    is_ok(file.contains(b'ddd'), 262145, '"ddd" at position 262145')
    is_ok(file.contains(b'e'), -1, 'does not contain "e"')
    is_ok(file.contains(b'a' * 131072), 0, '"a" x 131072 at position 0')
    is_ok(file.contains(b'c' * 131072), 131073, '"c" x 131072 at position 131073')
    is_ok(file.contains(b'b' + (b'c' * 131072) + b'ddd'), 131072, '"b" . ("c" x 131072) . "ddd" at position 131072')

with subtest('Huge file asset with range'):
    file = Pyjo.Asset.File.new(start_range=1, end_range=262146)
    file.add_chunk(b'a' * 131072)
    file.add_chunk(b'b')
    file.add_chunk(b'c' * 131072)
    file.add_chunk(b'ddd')
    is_ok(file.contains(b'a'), 0, '"a" at position 0')
    is_ok(file.contains(b'b'), 131071, '"b" at position 131071')
    is_ok(file.contains(b'c'), 131072, '"c" at position 131072')
    is_ok(file.contains(b'abc'), 131070, '"abc" at position 131070')
    is_ok(file.contains(b'ccdd'), 262142, '"ccdd" at position 262142')
    is_ok(file.contains(b'dd'), 262144, '"dd" at position 262144')
    is_ok(file.contains(b'ddd'), -1, 'does not contain "ddd"')
    is_ok(file.contains(b'b' + (b'c' * 131072) + b'ddd'), -1, 'does not contain "b" . ("c" x 131072) . "ddd"')

with subtest('Move memory asset to file'):
    mem = Pyjo.Asset.Memory.new().add_chunk(b'abc')
    tmp = Pyjo.Asset.File.new().add_chunk(b'x')
    p = tmp.path
    ok(os.path.exists(p), 'file exists')
    del tmp
    # Not in Mojolicious: PyPy frees objects only when its garbage collector runs
    gc.collect()
    ok(not os.path.exists(p), 'file has been cleaned up')
    is_ok(mem.move_to(p).slurp(), b'abc', 'right content')
    ok(os.path.exists(p), 'file exists')
    os.unlink(p)
    pass_ok('unlinked file')
    ok(not os.path.exists(p), 'file has been cleaned up')
    is_ok(Pyjo.Asset.Memory.new().move_to(p).slurp(), b'', 'no content')
    ok(os.path.exists(p), 'file exists')
    os.unlink(p)
    pass_ok('unlinked file')
    ok(not os.path.exists(p), 'file has been cleaned up')

with subtest('Move file asset to file'):
    file = Pyjo.Asset.File.new()
    file.add_chunk(b'bcd')
    tmp = Pyjo.Asset.File.new()
    tmp.add_chunk(b'x')
    isnt_ok(file.path, tmp.path, 'different paths')
    p = tmp.path
    ok(os.path.exists(p), 'file exists')
    del tmp
    # Not in Mojolicious: PyPy frees objects only when its garbage collector runs
    gc.collect()
    ok(not os.path.exists(p), 'file has been cleaned up')
    is_ok(file.move_to(p).slurp(), b'bcd', 'right content')
    del file
    # Not in Mojolicious: PyPy frees objects only when its garbage collector runs
    gc.collect()
    ok(os.path.exists(p), 'file exists')
    os.unlink(p)
    pass_ok('unlinked file')
    ok(not os.path.exists(p), 'file has been cleaned up')
    is_ok(Pyjo.Asset.File.new().move_to(p).slurp(), b'', 'no content')
    ok(os.path.exists(p), 'file exists')
    os.unlink(p)
    pass_ok('unlinked file')
    ok(not os.path.exists(p), 'file has been cleaned up')

with subtest('Upgrade'):
    asset = Pyjo.Asset.Memory.new(max_memory_size=5, auto_upgrade=True)
    upgrade = 0

    def upgraded(mem, file):
        global upgrade
        upgrade += 1

    asset.on('upgrade', upgraded)
    asset = asset.add_chunk(b'lala')
    ok(not upgrade, 'upgrade event has not been emitted')
    ok(not asset.is_file, 'stored in memory')
    asset = asset.add_chunk(b'lala')
    is_ok(upgrade, 1, 'upgrade event has been emitted once')
    ok(asset.is_file, 'stored in file')
    asset = asset.add_chunk(b'lala')
    is_ok(upgrade, 1, 'upgrade event was not emitted again')
    ok(asset.is_file, 'stored in file')
    is_ok(asset.slurp(), b'lalalalalala', 'right content')
    ok(asset.cleanup, 'file will be cleaned up')
    asset = Pyjo.Asset.Memory.new(max_memory_size=5)
    asset = asset.add_chunk(b'lala')
    ok(not asset.is_file, 'stored in memory')
    asset = asset.add_chunk(b'lala')
    ok(not asset.is_file, 'stored in memory')

with subtest('Change temporary directory during upgrade'):
    tmpdir = tempdir()
    mem = Pyjo.Asset.Memory.new(auto_upgrade=True, max_memory_size=10)
    mem.on('upgrade', lambda mem, file: file.set(tmpdir=tmpdir))
    file = mem.add_chunk(b'aaaaaaaaaaa')
    ok(file.is_file, 'stored in file')
    is_ok(file.slurp(), b'aaaaaaaaaaa', 'right content')
    is_ok(path(file.path).dirname(), tmpdir, 'right directory')

with subtest('Temporary directory'):
    tmpdir = tempdir()
    os.environ['PYJO_TMPDIR'] = str(tmpdir)
    try:
        file = Pyjo.Asset.File.new()
        is_ok(file.tmpdir, tmpdir, 'same directory')
        file.add_chunk(b'works!')
        is_ok(file.slurp(), b'works!', 'right content')
        is_ok(path(file.path).dirname(), tmpdir, 'same directory')
    finally:
        del os.environ['PYJO_TMPDIR']

with subtest('Custom temporary file'):
    tmpdir = tempdir()
    p = tmpdir.child('test.file')
    ok(not os.path.exists(p), 'file does not exist')
    file = Pyjo.Asset.File.new(path=p)
    is_ok(file.path, p, 'right path')
    ok(not os.path.exists(p), 'file still does not exist')
    file.add_chunk(b'works!')
    ok(os.path.exists(p), 'file exists')
    is_ok(file.slurp(), b'works!', 'right content')
    del file
    # Not in Mojolicious: PyPy frees objects only when its garbage collector runs
    gc.collect()
    ok(not os.path.exists(p), 'file has been cleaned up')

with subtest('Temporary file without cleanup'):
    file = Pyjo.Asset.File.new(cleanup=False).add_chunk(b'test')
    ok(file.is_file, 'stored in file')
    is_ok(file.slurp(), b'test', 'right content')
    is_ok(file.size, 4, 'right size')
    is_ok(file.mtime, os.fstat(file.handle.fileno()).st_mtime, 'right mtime')
    is_ok(file.contains(b'es'), 1, '"es" at position 1')
    p = file.path
    del file
    # Not in Mojolicious: PyPy frees objects only when its garbage collector runs
    gc.collect()
    ok(os.path.exists(p), 'file exists')
    os.unlink(p)
    pass_ok('unlinked file')
    ok(not os.path.exists(p), 'file has been cleaned up')

with subtest('Incomplete write'):
    # local *IO::Handle::syswrite = sub { $! = 0; 2 }, as a handle that writes two bytes
    class ShortWrite(io.FileIO):
        def write(self, b):
            return 2

    tmpdir = tempdir()
    file = Pyjo.Asset.File.new(handle=ShortWrite(tmpdir.child('short').to_str(), 'a+b'))
    throws_ok(lambda: file.add_chunk(b'test'), re.compile(r"Can't write to asset: .*"), 'right error')
    file.handle.close()

with subtest('Forked process'):
    if not hasattr(os, 'fork'):
        plan(skip_all='Real fork is required!')
    else:
        file = Pyjo.Asset.File.new().add_chunk(b'Fork test!')
        p = file.path
        ok(os.path.exists(p), 'file exists')
        is_ok(file.slurp(), b'Fork test!', 'right content')
        pid = os.fork()
        if not pid:
            # exit 0, which frees the file in the child process too
            file.close()
            os._exit(0)
        os.waitpid(pid, 0)
        ok(os.path.exists(p), 'file still exists')
        is_ok(file.slurp(), b'Fork test!', 'right content')
        del file
        # Not in Mojolicious: PyPy frees objects only when its garbage collector runs
        gc.collect()
        ok(not os.path.exists(p), 'file has been cleaned up')

with subtest('Upgrade with missing temporary directory'):
    tmpdir = tempdir()
    os.environ['PYJO_TMPDIR'] = tmpdir.child('does_not_exist').to_str()
    try:
        mem = Pyjo.Asset.Memory.new(max_memory_size=10, auto_upgrade=True)
        mem.add_chunk(b'abcdef')
        # Unlike Mojolicious: the error of the system, not the message of File::Temp, "does not exist"
        throws_ok(lambda: mem.add_chunk(b'ghijkl'), re.compile(r'No such file or directory'), 'right error')
        is_ok(mem.slurp(), b'abcdef', 'no memory leak')
        throws_ok(lambda: mem.add_chunk(b'g'), re.compile(r'Asset has been upgraded and is now frozen'), 'right error')
        is_ok(mem.slurp(), b'abcdef', 'asset is frozen')
    finally:
        del os.environ['PYJO_TMPDIR']

with subtest('Abstract methods'):
    asset = Pyjo.Asset.new()
    throws_ok(
        lambda: asset.add_chunk(b''), re.compile(r'Method "add_chunk" not implemented by subclass'), 'right error'
    )
    throws_ok(lambda: asset.contains(b''), re.compile(r'Method "contains" not implemented by subclass'), 'right error')
    throws_ok(lambda: asset.get_chunk(0), re.compile(r'Method "get_chunk" not implemented by subclass'), 'right error')
    throws_ok(lambda: asset.move_to(''), re.compile(r'Method "move_to" not implemented by subclass'), 'right error')
    throws_ok(lambda: asset.mtime, re.compile(r'Method "mtime" not implemented by subclass'), 'right error')
    throws_ok(lambda: asset.size, re.compile(r'Method "size" not implemented by subclass'), 'right error')
    throws_ok(lambda: asset.slurp(), re.compile(r'Method "slurp" not implemented by subclass'), 'right error')
    throws_ok(lambda: asset.to_file(), re.compile(r'Method "to_file" not implemented by subclass'), 'right error')

done_testing()
