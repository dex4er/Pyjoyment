import Pyjo.Asset.File
import Pyjo.Asset.Memory

from Pyjo.Test import *

import datetime
import io
import os
import pathlib
import shutil
import tempfile


with subtest('pathlib'):
    with tempfile.TemporaryDirectory() as dir:
        root = pathlib.Path(dir)
        file = Pyjo.Asset.File.new(path=root / 'test.file')
        is_ok(file.path, str(root / 'test.file'), 'path from a pathlib.Path')
        file.add_chunk(b'works!')
        is_ok((root / 'test.file').read_bytes(), b'works!', 'written')

        file = Pyjo.Asset.File.new(tmpdir=root)
        is_ok(file.tmpdir, str(root), 'tmpdir from a pathlib.Path')
        file.add_chunk(b'moved')
        file.move_to(root / 'moved.file')
        is_ok((root / 'moved.file').read_bytes(), b'moved', 'moved to a pathlib.Path')
        is_ok(file.path, str(root / 'moved.file'), 'new path')

        Pyjo.Asset.Memory.new().add_chunk(b'memory').move_to(root / 'memory.file')
        is_ok((root / 'memory.file').read_bytes(), b'memory', 'memory moved to a pathlib.Path')

with subtest('Context manager'):
    with Pyjo.Asset.File.new() as file:
        file.add_chunk(b'abc')
        path = file.path
        ok(os.path.exists(path), 'file exists')
    ok(not os.path.exists(path), 'file has been cleaned up at the end of the block')

    with tempfile.TemporaryDirectory() as dir:
        path = os.path.join(dir, 'keep.file')
        with Pyjo.Asset.File.new(path=path, cleanup=False) as file:
            file.add_chunk(b'abc')
        ok(os.path.exists(path), 'file without cleanup is kept')
        ok(file.handle.closed, 'handle is closed')

with subtest('Handle of the standard library'):
    file = Pyjo.Asset.File.new().add_chunk(b'foo bar baz')
    isa_ok(file.handle, io.RawIOBase, 'raw file object')
    file.handle.seek(0)
    copy = io.BytesIO()
    shutil.copyfileobj(file.handle, copy)
    is_ok(copy.getvalue(), b'foo bar baz', 'copied with shutil')
    file.close()

with subtest('mtime'):
    file = Pyjo.Asset.File.new().add_chunk(b'x')
    when = datetime.datetime.fromtimestamp(file.mtime, datetime.UTC)
    ok(abs(datetime.datetime.now(datetime.UTC) - when) < datetime.timedelta(minutes=5), 'datetime from mtime')
    file.close()
    mem = Pyjo.Asset.Memory.new()
    isa_ok(datetime.datetime.fromtimestamp(mem.mtime, datetime.UTC), datetime.datetime, 'datetime from memory mtime')

done_testing()
