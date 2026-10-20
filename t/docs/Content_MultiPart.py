import Pyjo.Content.Single

from Pyjo.Test import *

import contextlib
import io
import re


with subtest('Synopsis'):
    from Pyjo.Content.MultiPart import MultiPart

    multi = MultiPart()
    multi.parse(b'Content-Type: multipart/mixed; boundary=---foobar')
    # The parts of the documentation, once the rest of the content has been parsed
    body = b''.join(b'-----foobar\x0d\x0a\x0d\x0a%d\x0d\x0a' % i for i in range(5)) + b'-----foobar--'
    multi.parse(b'\x0d\x0aContent-Length: %d\x0d\x0a\x0d\x0a' % len(body) + body)
    single = multi.parts[4]
    is_ok(single.asset.slurp(), b'4', 'fifth part')

    # Or import the module, as in Google Python Style Guide

    import Pyjo.Content.MultiPart

    multi = Pyjo.Content.MultiPart.new()
    multi.parse(b'Content-Type: multipart/mixed; boundary=---foobar')
    # The parts of the documentation, once the rest of the content has been parsed
    body = b''.join(b'-----foobar\x0d\x0a\x0d\x0a%d\x0d\x0a' % i for i in range(5)) + b'-----foobar--'
    multi.parse(b'\x0d\x0aContent-Length: %d\x0d\x0a\x0d\x0a' % len(body) + body)
    single = multi.parts[4]
    is_ok(single.asset.slurp(), b'4', 'fifth part')

with subtest('part'):
    multi = Pyjo.Content.MultiPart.new()
    multi.on('part', lambda multi, single: ...)
    ok(multi.has_subscribers('part'), 'subscribed')

    multi = Pyjo.Content.MultiPart.new()

    @multi.on('part')
    def part(multi, single):
        @single.on('body')
        def body(single):
            if m := re.search(r'name="([^"]+)"', single.headers.content_disposition or ''):
                print(f'Field: {m[1]}')

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        body = b'--x\x0d\x0aContent-Disposition: form-data; name="foo"\x0d\x0a\x0d\x0abar\x0d\x0a--x--'
        multi.parse(
            b'Content-Type: multipart/form-data; boundary=x\x0d\x0aContent-Length: %d\x0d\x0a\x0d\x0a' % len(body)
            + body
        )
    is_ok(out.getvalue(), 'Field: foo\n', 'field')

with subtest('new'):
    multi = Pyjo.Content.MultiPart.new()
    is_ok(multi.parts, [], 'no parts')
    multi = Pyjo.Content.MultiPart.new(parts=[Pyjo.Content.Single.new()])
    is_ok(len(multi.parts), 1, 'one part')

with subtest('parts'):
    multi = Pyjo.Content.MultiPart.new()
    parts = multi.parts
    is_ok(parts, [], 'default')
    multi.parts = [Pyjo.Content.Single.new()]
    is_ok(len(multi.parts), 1, 'set')

with subtest('body_contains'):
    multi.parts[0].asset.add_chunk(b'foobarbaz')
    boolean = multi.body_contains(b'foobarbaz')
    is_ok(boolean, True, 'contains')

with subtest('body_size'):
    size = multi.body_size
    body, offset = b'', 0
    while chunk := multi.get_body_chunk(offset):
        body += chunk
        offset += len(chunk)
    is_ok(size, len(body), 'size of the whole body')

with subtest('build_boundary'):
    multi = Pyjo.Content.MultiPart.new()
    boundary = multi.build_boundary()
    is_ok(multi.headers.content_type, f'multipart/mixed; boundary={boundary}', 'added to the header')

with subtest('clone'):
    clone = multi.clone()
    is_ok(clone.parts, multi.parts, 'same parts')

with subtest('get_body_chunk'):
    chunk = multi.get_body_chunk(0)
    is_ok(chunk, b'--' + boundary.encode() + b'\x0d\x0a', 'first boundary')

with subtest('is_multipart'):
    boolean = multi.is_multipart
    is_ok(boolean, True, 'multipart')

done_testing()
