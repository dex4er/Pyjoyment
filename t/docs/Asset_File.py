from Pyjo.File import tempdir
from Pyjo.Test import *

import contextlib
import io
import os


# The paths of the documentation are in a temporary directory
dir = tempdir()
home = dir.child('home', 'sri').make_path()


def documented(path):
    return dir.child(*path.strip('/').split('/')).to_str()


with subtest('Synopsis'):
    import Pyjo.Asset.File

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        # Temporary file
        file = Pyjo.Asset.File.new()
        file.add_chunk(b'foo bar baz')
        if file.contains(b'bar') >= 0:
            print('File contains "bar"')
        print(file.slurp())

        # Existing file
        home.child('foo.txt').spew(b'existing')
        file = Pyjo.Asset.File.new(path=documented('/home/sri/foo.txt'))
        file.move_to(documented('/yada.txt'))
        print(file.slurp())
    is_ok(output.getvalue(), "File contains \"bar\"\nb'foo bar baz'\nb'existing'\n", 'output')

with subtest('new'):
    file = Pyjo.Asset.File.new()
    is_ok(file.path, None, 'no path yet')
    file = Pyjo.Asset.File.new(path=documented('/home/sri/test.txt'))
    is_ok(file.path, documented('/home/sri/test.txt'), 'path')

with subtest('cleanup'):
    file = Pyjo.Asset.File.new()
    boolean = file.cleanup
    is_ok(boolean, None, 'default')
    file.cleanup = True
    is_ok(file.cleanup, True, 'set')

with subtest('path'):
    file = Pyjo.Asset.File.new()
    path = file.path
    is_ok(path, None, 'default')
    file.path = documented('/home/sri/foo.txt')
    is_ok(file.path, documented('/home/sri/foo.txt'), 'set')

with subtest('handle'):
    home.child('foo.txt').spew(b'existing')
    file = Pyjo.Asset.File.new(path=documented('/home/sri/foo.txt'))
    handle = file.handle
    is_ok(handle.read(), b'existing', 'opened on demand')
    handle.close()
    file.handle = open(documented('/home/sri/foo.txt'), 'rb')
    is_ok(file.handle.read(), b'existing', 'set')
    file.handle.close()

with subtest('tmpdir'):
    file = Pyjo.Asset.File.new()
    tmpdir = file.tmpdir
    ok(os.path.isdir(tmpdir), 'auto-detected')
    file.tmpdir = documented('/tmp')
    is_ok(file.tmpdir, documented('/tmp'), 'set')

with subtest('add_chunk'):
    file = Pyjo.Asset.File.new()
    is_ok(file.add_chunk(b'foo bar baz'), file, 'returns the file')
    is_ok(file.slurp(), b'foo bar baz', 'added')

with subtest('close'):
    file = Pyjo.Asset.File.new().add_chunk(b'foo')
    path = file.path
    file.close()
    ok(not os.path.exists(path), 'deleted')

with subtest('contains'):
    file = Pyjo.Asset.File.new().add_chunk(b'foo bar baz')
    position = file.contains(b'bar')
    is_ok(position, 4, 'position')

with subtest('get_chunk'):
    file = Pyjo.Asset.File.new().add_chunk(b'foo bar baz')
    offset, max = 4, 3
    chunk = file.get_chunk(offset)
    is_ok(chunk, b'bar baz', 'from offset')
    chunk = file.get_chunk(offset, max)
    is_ok(chunk, b'bar', 'with max')

with subtest('is_file'):
    boolean = file.is_file
    is_ok(boolean, True, 'a file')

with subtest('move_to'):
    file = Pyjo.Asset.File.new().add_chunk(b'bar')
    file = file.move_to(documented('/home/sri/bar.txt'))
    is_ok(file.path, documented('/home/sri/bar.txt'), 'moved')
    is_ok(file.cleanup, False, 'no cleanup')

with subtest('mtime'):
    mtime = file.mtime
    is_ok(mtime, os.stat(documented('/home/sri/bar.txt')).st_mtime, 'modification time')

with subtest('size'):
    size = file.size
    is_ok(size, 3, 'size')

with subtest('slurp'):
    content = file.slurp()
    is_ok(content, b'bar', 'content')

with subtest('to_file'):
    is_ok(file.to_file(), file, 'same object')

done_testing()
