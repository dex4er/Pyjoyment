from Pyjo.File import tempdir
from Pyjo.Test import *

import contextlib
import io


# The paths of the documentation are in a temporary directory
dir = tempdir()
dir.child('home', 'sri').make_path()


def documented(path):
    return dir.child(*path.strip('/').split('/')).to_str()


with subtest('Synopsis'):
    from Pyjo.Asset.Memory import Memory

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        mem = Memory()
        mem.add_chunk(b'foo bar baz')
        print(mem.slurp())
    is_ok(output.getvalue(), "b'foo bar baz'\n", 'output')

    # Or import the module, as in Google Python Style Guide
    import Pyjo.Asset.Memory

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        mem = Pyjo.Asset.Memory.new()
        mem.add_chunk(b'foo bar baz')
        print(mem.slurp())
    is_ok(output.getvalue(), "b'foo bar baz'\n", 'output')

with subtest('upgrade'):
    mem = Pyjo.Asset.Memory.new(auto_upgrade=True, max_memory_size=3)
    mem.on('upgrade', lambda mem, file: ...)
    ok(mem.has_subscribers('upgrade'), 'subscribed')

    mem = Pyjo.Asset.Memory.new(auto_upgrade=True, max_memory_size=3)
    mem.on('upgrade', lambda mem, file: file.set(tmpdir=documented('/tmp')))
    dir.child('tmp').make_path()
    file = mem.add_chunk(b'foo bar baz')
    is_ok(file.tmpdir, documented('/tmp'), 'tmpdir of the file')

with subtest('new'):
    mem = Pyjo.Asset.Memory.new()
    is_ok(mem.size, 0, 'empty')
    mem = Pyjo.Asset.Memory.new(max_memory_size=1024, auto_upgrade=True)
    is_ok((mem.max_memory_size, mem.auto_upgrade), (1024, True), 'attributes')

with subtest('auto_upgrade'):
    mem = Pyjo.Asset.Memory.new()
    boolean = mem.auto_upgrade
    is_ok(boolean, None, 'default')
    mem.auto_upgrade = True
    is_ok(mem.auto_upgrade, True, 'set')

with subtest('max_memory_size'):
    mem = Pyjo.Asset.Memory.new()
    size = mem.max_memory_size
    is_ok(size, 262144, 'default')
    mem.max_memory_size = 1024
    is_ok(mem.max_memory_size, 1024, 'set')

with subtest('mtime'):
    mem = Pyjo.Asset.Memory.new()
    mtime = mem.mtime
    is_ok(mtime, Pyjo.Asset.Memory.MTIME, 'default')
    mem.mtime = 1408567500
    is_ok(mem.mtime, 1408567500, 'set')

with subtest('add_chunk'):
    mem = Pyjo.Asset.Memory.new(auto_upgrade=True)
    mem = mem.add_chunk(b'foo bar baz')
    ok(not mem.is_file, 'in memory')
    file = mem.add_chunk(b'abc' * 262144)
    ok(file.is_file, 'upgraded')

with subtest('contains'):
    mem = Pyjo.Asset.Memory.new().add_chunk(b'foo bar baz')
    position = mem.contains(b'bar')
    is_ok(position, 4, 'position')

with subtest('get_chunk'):
    offset, max = 4, 3
    chunk = mem.get_chunk(offset)
    is_ok(chunk, b'bar baz', 'from offset')
    chunk = mem.get_chunk(offset, max)
    is_ok(chunk, b'bar', 'with max')

with subtest('move_to'):
    mem = mem.move_to(documented('/home/sri/foo.txt'))
    is_ok(dir.child('home', 'sri', 'foo.txt').slurp(), b'foo bar baz', 'moved')

with subtest('size'):
    size = mem.size
    is_ok(size, 11, 'size')

with subtest('slurp'):
    content = mem.slurp()
    is_ok(content, b'foo bar baz', 'content')

with subtest('to_file'):
    file = mem.to_file()
    is_ok(file.slurp(), b'foo bar baz', 'converted')

done_testing()
