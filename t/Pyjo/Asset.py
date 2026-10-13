if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import Pyjo.Asset.File
    import Pyjo.Asset.Memory

    import os
    import tempfile

    from Pyjo.Util import getenv, setenv, steady_time

    from t.lib.Value import Value

    # File asset
    with Pyjo.Asset.File.new() as asset_file:
        is_ok(asset_file.size, 0, 'file is empty')
        is_ok(asset_file.mtime, os.fstat(asset_file.handle.fileno()).st_mtime, 'right mtime')
        is_ok(asset_file.slurp(), b'', 'file is empty')
        asset_file.add_chunk(b'abc')
        is_ok(asset_file.contains(b'abc'), 0, '"abc" at position 0')
        is_ok(asset_file.contains(b'bc'), 1, '"bc" at position 1')
        is_ok(asset_file.contains(b'db'), -1, 'does not contain "db"')
        is_ok(asset_file.size, 3, 'right size')
        is_ok(asset_file.mtime, os.fstat(asset_file.handle.fileno()).st_mtime, 'right mtime')

        # Cleanup
        path = asset_file.path
        ok(os.path.exists(path), 'temporary file exists')

    ok(not os.path.exists(path), 'temporary file has been cleaned up')

    # Memory asset
    with Pyjo.Asset.Memory.new() as asset_mem:
        asset_mem.add_chunk(b'abc')
        is_ok(asset_mem.contains(b'abc'), 0, '"abc" at position 0')
        is_ok(asset_mem.contains(b'bc'), 1, '"bc" at position 1')
        is_ok(asset_mem.contains(b'db'), -1, 'does not contain "db"')
        is_ok(asset_mem.size, 3, 'right size')
        ok(asset_mem.mtime > (steady_time() - 100), 'right mtime')
        is_ok(asset_mem.mtime, Pyjo.Asset.Memory.new().mtime, 'same mtime')
        mtime = asset_mem.mtime
        is_ok(asset_mem.set(mtime=mtime + 23).mtime, mtime + 23, 'right mtime')

    # Empty file asset
    with Pyjo.Asset.File.new() as asset_file:
        is_ok(asset_file.size, 0, 'asset is empty')
        is_ok(asset_file.get_chunk(0), b'', 'no content')
        is_ok(asset_file.slurp(), b'', 'no content')
        is_ok(asset_file.contains(b'a'), -1, 'does not contain "a"')

    # Empty memory asset
    with Pyjo.Asset.Memory.new() as asset_mem:
        is_ok(asset_mem.size, 0, 'asset is empty')
        is_ok(asset_mem.get_chunk(0), b'', 'no content')
        is_ok(asset_mem.slurp(), b'', 'no content')
        ok(not asset_mem.is_range, 'no range')
        is_ok(asset_mem.contains(b'a'), -1, 'does not contain "a"')

    # File asset range support (a[bcdefabc])
    with Pyjo.Asset.File.new(start_range=1) as asset_file:
        ok(asset_file.is_range, 'has range')
        asset_file.add_chunk(b'abcdefabc')
        is_ok(asset_file.contains(b'bcdef'), 0, '"bcdef" at position 0')
        is_ok(asset_file.contains(b'cdef'), 1, '"cdef" at position 1')
        is_ok(asset_file.contains(b'abc'), 5, '"abc" at position 5')
        is_ok(asset_file.contains(b'db'), -1, 'does not contain "db"')

    # Memory asset range support (a[bcdefabc])
    with Pyjo.Asset.Memory.new(start_range=1) as asset_mem:
        ok(asset_mem.is_range, 'has range')
        asset_mem.add_chunk(b'abcdefabc')
        is_ok(asset_mem.contains(b'bcdef'), 0, '"bcdef" at position 0')
        is_ok(asset_mem.contains(b'cdef'), 1, '"cdef" at position 1')
        is_ok(asset_mem.contains(b'abc'), 5, '"abc" at position 5')
        is_ok(asset_mem.contains(b'db'), -1, 'does not contain "db"')

    # File asset range support (ab[cdefghi]jk)
    with Pyjo.Asset.File.new(start_range=2, end_range=8) as asset_file:
        ok(asset_file.is_range, 'has range')
        asset_file.add_chunk(b'abcdefghijk')
        is_ok(asset_file.contains(b'cdefghi'), 0, '"cdefghi" at position 0')
        is_ok(asset_file.contains(b'fghi'), 3, '"fghi" at position 3')
        is_ok(asset_file.contains(b'f'), 3, '"f" at position 3')
        is_ok(asset_file.contains(b'hi'), 5, '"hi" at position 5')
        is_ok(asset_mem.contains(b'ij'), -1, 'does not contain "ij"')
        is_ok(asset_file.contains(b'db'), -1, 'does not contain "db"')
        is_ok(asset_file.get_chunk(0), b'cdefghi', 'chunk from position 0')
        is_ok(asset_file.get_chunk(1), b'defghi', 'chunk from position 1')
        is_ok(asset_file.get_chunk(5), b'hi', 'chunk from position 5')
        is_ok(asset_file.get_chunk(0, 2), b'cd', 'chunk from position 0 (2 bytes)')
        is_ok(asset_file.get_chunk(1, 3), b'def', 'chunk from position 1 (3 bytes)')
        is_ok(asset_file.get_chunk(5, 1), b'h', 'chunk from position 5 (1 byte)')
        is_ok(asset_file.get_chunk(5, 3), b'hi', 'chunk from position 5 (2 byte)')

    # Memory asset range support (ab[cdefghi]jk)
    with Pyjo.Asset.Memory.new(start_range=2, end_range=8) as asset_mem:
        ok(asset_mem.is_range, 'has range')
        asset_mem.add_chunk(b'abcdefghijk')
        is_ok(asset_mem.contains(b'cdefghi'), 0, '"cdefghi" at position 0')
        is_ok(asset_mem.contains(b'fghi'), 3, '"fghi" at position 3')
        is_ok(asset_mem.contains(b'f'), 3, '"f" at position 3')
        is_ok(asset_mem.contains(b'hi'), 5, '"hi" at position 5')
        is_ok(asset_mem.contains(b'ij'), -1, 'does not contain "ij"')
        is_ok(asset_mem.contains(b'db'), -1, 'does not contain "db"')
        is_ok(asset_mem.get_chunk(0), b'cdefghi', 'chunk from position 0')
        is_ok(asset_mem.get_chunk(1), b'defghi', 'chunk from position 1')
        is_ok(asset_mem.get_chunk(5), b'hi', 'chunk from position 5')
        is_ok(asset_mem.get_chunk(0, 2), b'cd', 'chunk from position 0 (2 bytes)')
        is_ok(asset_mem.get_chunk(1, 3), b'def', 'chunk from position 1 (3 bytes)')
        is_ok(asset_mem.get_chunk(5, 1), b'h', 'chunk from position 5 (1 byte)')
        is_ok(asset_mem.get_chunk(5, 3), b'hi', 'chunk from position 5 (2 byte)')

    # Huge file asset
    with Pyjo.Asset.File.new() as asset_file:
        ok(not asset_file.is_range, 'no range')
        asset_file.add_chunk(b'a' * 131072)
        asset_file.add_chunk(b'b')
        asset_file.add_chunk(b'c' * 131072)
        asset_file.add_chunk(b'ddd')
        is_ok(asset_file.contains(b'a'), 0, '"a" at position 0')
        is_ok(asset_file.contains(b'b'), 131072, '"b" at position 131072')
        is_ok(asset_file.contains(b'c'), 131073, '"c" at position 131073')
        is_ok(asset_file.contains(b'abc'), 131071, '"abc" at position 131071')
        is_ok(asset_file.contains(b'ccdd'), 262143, '"ccdd" at position 262143')
        is_ok(asset_file.contains(b'dd'), 262145, '"dd" at position 262145')
        is_ok(asset_file.contains(b'ddd'), 262145, '"ddd" at position 262145')
        is_ok(asset_file.contains(b'e'), -1, 'does not contain "e"')
        is_ok(asset_file.contains(b'a' * 131072), 0, '"a" * 131072 at position 0')
        is_ok(asset_file.contains(b'c' * 131072), 131073, '"c" * 131072 at position 131073')
        is_ok(
            asset_file.contains(b'b' + (b'c' * 131072) + b'ddd'),
            131072,
            '"b" + ("c" * 131072) . "ddd" at position 131072',
        )

    # Huge file asset with range
    with Pyjo.Asset.File.new(start_range=1, end_range=262146) as asset_file:
        asset_file.add_chunk(b'a' * 131072)
        asset_file.add_chunk(b'b')
        asset_file.add_chunk(b'c' * 131072)
        asset_file.add_chunk(b'ddd')
        is_ok(asset_file.contains(b'a'), 0, '"a" at position 0')
        is_ok(asset_file.contains(b'b'), 131071, '"b" at position 131071')
        is_ok(asset_file.contains(b'c'), 131072, '"c" at position 131072')
        is_ok(asset_file.contains(b'abc'), 131070, '"abc" at position 131070')
        is_ok(asset_file.contains(b'ccdd'), 262142, '"ccdd" at position 262142')
        is_ok(asset_file.contains(b'dd'), 262144, '"dd" at position 262144')
        is_ok(asset_file.contains(b'ddd'), -1, 'does not contain "ddd"')
        is_ok(asset_file.contains(b'b' + (b'c' * 131072) + b'ddd'), -1, 'does not contain "b" + ("c" * 131072) + "ddd"')

    # Move memory asset to file
    asset_mem = Pyjo.Asset.Memory.new().add_chunk(b'abc')
    with Pyjo.Asset.File.new().add_chunk(b'x') as tmp:
        path = tmp.path
        ok(os.path.exists(path), 'file exists')
    ok(not os.path.exists(path), 'file has been cleaned up')
    is_ok(asset_mem.move_to(path).slurp(), b'abc', 'right content')
    ok(os.path.exists(path), 'file exists')
    os.unlink(path)
    ok(not os.path.exists(path), 'file has been cleaned up')
    is_ok(Pyjo.Asset.Memory.new().move_to(path).slurp(), b'', 'no content')
    ok(os.path.exists(path), 'file exists')
    os.unlink(path)
    ok(not os.path.exists(path), 'file has been cleaned up')

    # Move file asset to file
    with Pyjo.Asset.File.new() as asset_file:
        asset_file.add_chunk(b'bcd')
        with Pyjo.Asset.File.new() as tmp:
            tmp.add_chunk(b'x')
            isnt_ok(asset_file.path, tmp.path, 'different paths')
            path = tmp.path
            ok(os.path.exists(path), 'file exists')
        ok(not os.path.exists(path), 'file has been cleaned up')
        is_ok(asset_file.move_to(path).slurp(), b'bcd', 'right content')
    ok(os.path.exists(path), 'file exists')
    os.unlink(path)
    ok(not os.path.exists(path), 'file has been cleaned up')
    is_ok(Pyjo.Asset.File.new().move_to(path).slurp(), b'', 'no content')
    ok(os.path.exists(path), 'file exists')
    os.unlink(path)
    ok(not os.path.exists(path), 'file has been cleaned up')

    # Upgrade
    asset = Pyjo.Asset.Memory.new(max_memory_size=5, auto_upgrade=True)
    upgrade = Value(0)
    asset.on('upgrade', lambda asset_mem, asset_file: upgrade.inc())
    asset = asset.add_chunk(b'lala')
    ok(not upgrade.get(), 'upgrade event has not been emitted')
    ok(not asset.is_file, 'stored in memory')
    asset = asset.add_chunk(b'lala')
    is_ok(upgrade.get(), 1, 'upgrade event has been emitted once')
    ok(asset.is_file, 'stored in file')
    asset = asset.add_chunk(b'lala')
    is_ok(upgrade.get(), 1, 'upgrade event was not emitted again')
    ok(asset.is_file, 'stored in file')
    is_ok(asset.slurp(), b'lalalalalala', 'right content')
    ok(asset.cleanup, 'file will be cleaned up')
    asset.close()
    asset = Pyjo.Asset.Memory.new(max_memory_size=5)
    asset = asset.add_chunk(b'lala')
    ok(not asset.is_file, 'stored in memory')
    asset = asset.add_chunk(b'lala')
    ok(not asset.is_file, 'stored in memory')
    asset.close()

    # Temporary directory
    mojo_tmpdir = getenv('PYJO_TMPDIR')
    tmpdir = tempfile.mkdtemp()
    setenv('PYJO_TMPDIR', tmpdir)
    with Pyjo.Asset.File.new() as asset_file:
        is_ok(asset_file.tmpdir, tmpdir, 'same directory')
        asset_file.add_chunk(b'works!')
        is_ok(asset_file.slurp(), b'works!', 'right content')
        is_ok(os.path.dirname(asset_file.path), tmpdir, 'same directory')
    os.rmdir(tmpdir)
    setenv('PYJO_TMPDIR', mojo_tmpdir)

    # Custom temporary file
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, 'test.file')
    with Pyjo.Asset.File.new(path=path) as asset_file:
        is_ok(asset_file.path, path, 'right path')
        ok(not os.path.exists(path), 'file still does not exist')
        asset_file.add_chunk(b'works!')
        ok(os.path.exists(path), 'file exists')
        is_ok(asset_file.slurp(), b'works!', 'right content')
        is_ok(os.path.dirname(asset_file.path), tmpdir, 'same directory')
    ok(not os.path.exists(path), 'file has been cleaned up')
    os.rmdir(tmpdir)

    # Temporary file without cleanup
    with Pyjo.Asset.File.new(cleanup=False).add_chunk(b'test') as asset_file:
        ok(asset_file.is_file, 'stored in file')
        is_ok(asset_file.slurp(), b'test', 'right content')
        is_ok(asset_file.size, 4, 'right size')
        is_ok(asset_file.mtime, os.fstat(asset_file.handle.fileno()).st_mtime, 'right mtime')
        is_ok(asset_file.contains(b'es'), 1, '"es" at position 1')
        path = asset_file.path
    ok(os.path.exists(path), 'file exists')
    os.unlink(path)
    ok(not os.path.exists(path), 'file has been cleaned up')

    # Abstract methods
    throws_ok(lambda: Pyjo.Asset.new().add_chunk(), 'Method "add_chunk" not implemented by subclass', 'right error')
    throws_ok(lambda: Pyjo.Asset.new().contains(), 'Method "contains" not implemented by subclass', 'right error')
    throws_ok(lambda: Pyjo.Asset.new().get_chunk(), 'Method "get_chunk" not implemented by subclass', 'right error')
    throws_ok(lambda: Pyjo.Asset.new().move_to(), 'Method "move_to" not implemented by subclass', 'right error')
    throws_ok(lambda: Pyjo.Asset.new().mtime, 'Method "mtime" not implemented by subclass', 'right error')
    throws_ok(lambda: Pyjo.Asset.new().size, 'Method "size" not implemented by subclass', 'right error')
    throws_ok(lambda: Pyjo.Asset.new().slurp(), 'Method "slurp" not implemented by subclass', 'right error')

    done_testing()
