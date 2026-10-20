import Pyjo.Asset.File
import Pyjo.Asset.Memory

from Pyjo.Test import *

import contextlib
import io
import re


with subtest('Synopsis'):
    from Pyjo.Content.Single import Single

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        single = Single()
        single.parse(b'Content-Length: 12\x0d\x0a\x0d\x0aHello World!')
        print(single.headers.content_length)
    is_ok(out.getvalue(), '12\n', 'output')

    # Or import the module, as in Google Python Style Guide
    import Pyjo.Content.Single

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        single = Pyjo.Content.Single.new()
        single.parse(b'Content-Length: 12\x0d\x0a\x0d\x0aHello World!')
        print(single.headers.content_length)
    is_ok(out.getvalue(), '12\n', 'output')

with subtest('upgrade'):
    single = Pyjo.Content.Single.new()
    single.on('upgrade', lambda single, multi: ...)
    ok(single.has_subscribers('upgrade'), 'subscribed')

    single = Pyjo.Content.Single.new()

    @single.on('upgrade')
    def upgrade(single, multi):
        if m := re.search(r'multipart/([^;]+)', multi.headers.content_type, re.I):
            print(f'Multipart: {m[1]}')

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        single.parse(b'Content-Type: multipart/form-data; boundary=foo\x0d\x0a\x0d\x0a')
    is_ok(out.getvalue(), 'Multipart: form-data\n', 'upgraded')

with subtest('new'):
    single = Pyjo.Content.Single.new()
    isa_ok(single.asset, Pyjo.Asset.Memory.object, 'default asset')
    single = Pyjo.Content.Single.new(asset=Pyjo.Asset.File.new())
    isa_ok(single.asset, Pyjo.Asset.File.object, 'given asset')

with subtest('auto_upgrade'):
    single = Pyjo.Content.Single.new()
    boolean = single.auto_upgrade
    is_ok(boolean, True, 'default')
    single.auto_upgrade = False
    is_ok(single.auto_upgrade, False, 'set')

with subtest('asset'):
    single = Pyjo.Content.Single.new()
    asset = single.asset
    is_ok(asset.auto_upgrade, True, 'default with auto_upgrade')
    single.asset = Pyjo.Asset.Memory.new()
    isnt_ok(single.asset.auto_upgrade, True, 'set')

with subtest('body_contains'):
    single = Pyjo.Content.Single.new()
    single.asset.add_chunk(b'1234567')
    boolean = single.body_contains(b'1234567')
    is_ok(boolean, True, 'contains')

with subtest('body_size'):
    size = single.body_size
    is_ok(size, 7, 'size')

with subtest('clone'):
    clone = single.clone()
    is_ok(clone.asset, single.asset, 'same asset')

with subtest('get_body_chunk'):
    chunk = single.get_body_chunk(0)
    is_ok(chunk, b'1234567', 'chunk')

with subtest('parse'):
    single = Pyjo.Content.Single.new()
    single = single.parse(b'Content-Length: 12\x0d\x0a\x0d\x0aHello World!')
    is_ok(single.asset.slurp(), b'Hello World!', 'parsed')
    multi = Pyjo.Content.Single.new().parse(b'Content-Type: multipart/form-data\x0d\x0a\x0d\x0a')
    isa_ok(multi, Pyjo.Content.Single.object, 'no boundary, no upgrade')

done_testing()
