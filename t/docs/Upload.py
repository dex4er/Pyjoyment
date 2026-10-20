import Pyjo.Asset.Memory
import Pyjo.Headers

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
    from Pyjo.Upload import Upload

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        upload = Upload()
        # An upload has its asset and its filename once it has been parsed
        upload.set(asset=Pyjo.Asset.Memory.new().add_chunk(b'foo'), filename='foo.txt')
        print(upload.filename)
        upload.move_to(documented('/home/sri/foo.txt'))
    is_ok(out.getvalue(), 'foo.txt\n', 'output')
    is_ok(dir.child('home', 'sri', 'foo.txt').slurp(), b'foo', 'moved')

    # Or import the module, as in Google Python Style Guide

    import Pyjo.Upload

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        upload = Pyjo.Upload.new()
        # An upload has its asset and its filename once it has been parsed
        upload.set(asset=Pyjo.Asset.Memory.new().add_chunk(b'foo'), filename='foo.txt')
        print(upload.filename)
        upload.move_to(documented('/home/sri/foo.txt'))
    is_ok(out.getvalue(), 'foo.txt\n', 'output')
    is_ok(dir.child('home', 'sri', 'foo.txt').slurp(), b'foo', 'moved')

with subtest('new'):
    upload = Pyjo.Upload.new()
    is_ok(upload.asset, None, 'no asset')
    upload = Pyjo.Upload.new(name='foo', filename='foo.txt', asset=Pyjo.Asset.Memory.new())
    is_ok((upload.name, upload.filename), ('foo', 'foo.txt'), 'attributes')

with subtest('asset'):
    asset = upload.asset
    isa_ok(asset, Pyjo.Asset.Memory.object, 'asset')
    upload.asset = Pyjo.Asset.Memory.new().add_chunk(b'bar')
    is_ok(upload.asset.slurp(), b'bar', 'set')

with subtest('filename'):
    filename = upload.filename
    is_ok(filename, 'foo.txt', 'filename')
    upload.filename = 'foo.txt'
    is_ok(upload.filename, 'foo.txt', 'set')

with subtest('headers'):
    headers = upload.headers
    is_ok(headers, None, 'default')
    upload.headers = Pyjo.Headers.new()
    isa_ok(upload.headers, Pyjo.Headers.object, 'set')

with subtest('name'):
    name = upload.name
    is_ok(name, 'foo', 'name')
    upload.name = 'foo'
    is_ok(upload.name, 'foo', 'set')

with subtest('move_to'):
    upload = upload.move_to(documented('/home/sri/foo.txt'))
    is_ok(dir.child('home', 'sri', 'foo.txt').slurp(), b'bar', 'moved')

with subtest('size'):
    size = upload.size
    is_ok(size, 3, 'size')

with subtest('slurp'):
    content = upload.slurp()
    is_ok(content, b'bar', 'content')

done_testing()
