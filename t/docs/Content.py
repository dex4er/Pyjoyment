import Pyjo.Content.Single

from Pyjo.Test import *

import contextlib
import io
import os
import time


def output(cb):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        cb()
    return out.getvalue()


with subtest('Synopsis'):
    from Pyjo.Content import Content

    class MyContent(Content):
        def body_contains(self, chunk): ...
        @property
        def body_size(self): ...
        def get_body_chunk(self, offset): ...

    isa_ok(MyContent(), Content, 'subclass')

    # Or import the module, as in Google Python Style Guide
    import Pyjo.Content

    class MyContent(Pyjo.Content.object):
        def body_contains(self, chunk): ...
        @property
        def body_size(self): ...
        def get_body_chunk(self, offset): ...

    isa_ok(MyContent.new(), Pyjo.Content.object, 'subclass')

with subtest('body'):
    content = Pyjo.Content.Single.new()
    content.on('body', lambda content: ...)
    ok(content.has_subscribers('body'), 'subscribed')

    content = Pyjo.Content.Single.new()

    @content.on('body')
    def body(content):
        if content.headers.header('X-No-MultiPart'):
            content.auto_upgrade = False

    content.parse(b'X-No-MultiPart: 1\x0d\x0aContent-Type: multipart/mixed; boundary=foo\x0d\x0a\x0d\x0a')
    is_ok(content.auto_upgrade, False, 'no upgrade')

with subtest('drain'):
    content = Pyjo.Content.Single.new()
    content.on('drain', lambda content, offset: ...)
    ok(content.has_subscribers('drain'), 'subscribed')

    content = Pyjo.Content.Single.new().write_chunk()
    content.on('drain', lambda content, offset: content.write_chunk(str(time.time()).encode()))
    ok(content.get_body_chunk(0), 'chunk written on drain')

with subtest('read'):
    content = Pyjo.Content.Single.new()
    content.on('read', lambda content, chunk: ...)
    ok(content.has_subscribers('read'), 'subscribed')

    content = Pyjo.Content.Single.new()
    content.on('read', lambda content, chunk: print(f'Streaming: {chunk}'))
    is_ok(output(lambda: content.parse(b'Content-Length: 2\x0d\x0a\x0d\x0aHi')), "Streaming: b'Hi'\n", 'streaming')

with subtest('sse'):
    content = Pyjo.Content.Single.new()
    content.on('sse', lambda content, event: ...)
    ok(content.has_subscribers('sse'), 'subscribed')

    content = Pyjo.Content.Single.new()

    @content.on('sse')
    def sse(content, event):
        if event:
            print(f'Type: {event["type"]}, Data: {event["text"]}')
        else:
            print('SSE connection established')

    is_ok(
        output(
            lambda: content.parse(b'Content-Type: text/event-stream\x0d\x0a\x0d\x0aevent: foo\x0adata: bar\x0a\x0a')
        ),
        'SSE connection established\nType: foo, Data: bar\n',
        'events',
    )

with subtest('new'):
    content = Pyjo.Content.Single.new()
    isa_ok(content.headers, Pyjo.Headers.object, 'headers')
    content = Pyjo.Content.Single.new(headers=Pyjo.Headers.new())
    isa_ok(content.headers, Pyjo.Headers.object, 'given headers')

with subtest('auto_decompress'):
    content = Pyjo.Content.Single.new()
    boolean = content.auto_decompress
    is_ok(boolean, None, 'default')
    content.auto_decompress = True
    is_ok(content.auto_decompress, True, 'set')

with subtest('auto_relax'):
    content = Pyjo.Content.Single.new()
    boolean = content.auto_relax
    is_ok(boolean, None, 'default')
    content.auto_relax = True
    is_ok(content.auto_relax, True, 'set')

with subtest('max_buffer_size'):
    content = Pyjo.Content.Single.new()
    size = content.max_buffer_size
    is_ok(size, int(os.environ.get('PYJO_MAX_BUFFER_SIZE') or 262144), 'default')
    content.max_buffer_size = 1024
    is_ok(content.max_buffer_size, 1024, 'set')

with subtest('max_leftover_size'):
    content = Pyjo.Content.Single.new()
    size = content.max_leftover_size
    is_ok(size, int(os.environ.get('PYJO_MAX_LEFTOVER_SIZE') or 262144), 'default')
    content.max_leftover_size = 1024
    is_ok(content.max_leftover_size, 1024, 'set')

with subtest('relaxed'):
    content = Pyjo.Content.Single.new()
    boolean = content.relaxed
    is_ok(boolean, None, 'default')
    content.relaxed = True
    is_ok(content.relaxed, True, 'set')

with subtest('skip_body'):
    content = Pyjo.Content.Single.new()
    boolean = content.skip_body
    is_ok(boolean, None, 'default')
    content.skip_body = True
    is_ok(content.skip_body, True, 'set')

with subtest('headers'):
    content = Pyjo.Content.Single.new()
    headers = content.headers
    isa_ok(headers, Pyjo.Headers.object, 'default')
    content.headers = Pyjo.Headers.new()
    ok(content.headers is not headers, 'set')

with subtest('body_contains'):
    content = Pyjo.Content.Single.new()
    content.asset.add_chunk(b'foo bar baz')
    boolean = content.body_contains(b'foo bar baz')
    is_ok(boolean, True, 'contains')

with subtest('body_size'):
    size = content.body_size
    is_ok(size, 11, 'size')

with subtest('boundary'):
    content = Pyjo.Content.Single.new()
    content.headers.content_type = 'multipart/form-data; boundary=foo'
    boundary = content.boundary
    is_ok(boundary, 'foo', 'boundary')

with subtest('charset'):
    content = Pyjo.Content.Single.new()
    content.headers.content_type = 'text/plain; charset=UTF-8'
    charset = content.charset
    is_ok(charset, 'UTF-8', 'charset')

with subtest('clone'):
    clone = content.clone()
    is_ok(clone.headers.content_type, 'text/plain; charset=UTF-8', 'cloned')
    is_ok(content.write().clone(), None, 'dynamic content')

with subtest('generate_body_chunk'):
    content = Pyjo.Content.Single.new().write(b'Hi!')
    chunk = content.generate_body_chunk(0)
    is_ok(chunk, b'Hi!', 'generated')

with subtest('get_body_chunk'):
    content = Pyjo.Content.Single.new()
    content.asset.add_chunk(b'Hello')
    chunk = content.get_body_chunk(0)
    is_ok(chunk, b'Hello', 'chunk')

with subtest('get_header_chunk'):
    content = Pyjo.Content.Single.new()
    content.headers.content_type = 'text/plain'
    chunk = content.get_header_chunk(13)
    is_ok(chunk, b' text/plain\x0d\x0a\x0d\x0a', 'chunk of the headers')

with subtest('header_size'):
    size = content.header_size
    is_ok(size, 28, 'size')

with subtest('headers_contain'):
    boolean = content.headers_contain(b'text/plain')
    is_ok(boolean, True, 'contains')

with subtest('is_chunked'):
    content = Pyjo.Content.Single.new()
    content.headers.transfer_encoding = 'chunked'
    boolean = content.is_chunked
    is_ok(boolean, True, 'chunked')

with subtest('is_compressed'):
    content = Pyjo.Content.Single.new()
    content.headers.content_encoding = 'gzip'
    boolean = content.is_compressed
    is_ok(boolean, True, 'compressed')

with subtest('is_dynamic'):
    content = Pyjo.Content.Single.new().write()
    boolean = content.is_dynamic
    is_ok(boolean, True, 'dynamic')

with subtest('is_finished'):
    content = Pyjo.Content.Single.new().parse(b'Content-Length: 0\x0d\x0a\x0d\x0a')
    boolean = content.is_finished
    is_ok(boolean, True, 'finished')

with subtest('is_limit_exceeded'):
    boolean = content.is_limit_exceeded
    is_ok(boolean, False, 'not exceeded')

with subtest('is_multipart'):
    boolean = content.is_multipart
    is_ok(boolean, False, 'not multipart')

with subtest('is_parsing_body'):
    content = Pyjo.Content.Single.new().parse(b'Content-Length: 2\x0d\x0a\x0d\x0aH')
    boolean = content.is_parsing_body
    is_ok(boolean, True, 'parsing body')

with subtest('is_sse'):
    content = Pyjo.Content.Single.new()
    content.headers.content_type = 'text/event-stream'
    boolean = content.is_sse
    is_ok(boolean, True, 'SSE')

with subtest('leftovers'):
    content = Pyjo.Content.Single.new().parse(b'Content-Length: 2\x0d\x0a\x0d\x0aHi!')
    data = content.leftovers()
    is_ok(data, b'!', 'leftovers')

with subtest('parse'):
    content = Pyjo.Content.Single.new()
    content = content.parse(b'Content-Length: 12\x0d\x0a\x0d\x0aHello World!')
    is_ok(content.asset.slurp(), b'Hello World!', 'parsed')

with subtest('parse_body'):
    content = Pyjo.Content.Single.new()
    content = content.parse_body(b'Hi!')
    is_ok(content.leftovers(), b'Hi!', 'parsed body without a length')

with subtest('progress'):
    size = content.progress
    is_ok(size, 3, 'progress')

with subtest('write'):
    content = Pyjo.Content.Single.new()
    chunk = b'Hello!'
    content = content.write()
    content = content.write(b'')
    content = Pyjo.Content.Single.new().write(chunk)
    content = Pyjo.Content.Single.new().write(chunk, lambda content, offset: ...)
    ok(content.is_dynamic, 'dynamic')

    # Make sure previous chunk of data has been written before continuing
    content = Pyjo.Content.Single.new()
    content.write(b'He', lambda content, offset: content.write(b'llo!', lambda content, offset: content.write(b'')))
    body, offset = b'', 0
    while chunk := content.get_body_chunk(offset):
        body += chunk
        offset += len(chunk)
    is_ok(body, b'Hello!', 'written in order')

with subtest('write_chunk'):
    content = Pyjo.Content.Single.new()
    chunk = b'Hello!'
    content = content.write_chunk()
    content = content.write_chunk(b'')
    content = Pyjo.Content.Single.new().write_chunk(chunk)
    content = Pyjo.Content.Single.new().write_chunk(chunk, lambda content, offset: ...)
    ok(content.is_chunked, 'chunked')

    # Make sure previous chunk of data has been written before continuing
    content = Pyjo.Content.Single.new()
    content.write_chunk(
        b'He', lambda content, offset: content.write_chunk(b'llo!', lambda content, offset: content.write_chunk(b''))
    )
    body, offset = b'', 0
    while chunk := content.get_body_chunk(offset):
        body += chunk
        offset += len(chunk)
    is_ok(body, b'2\x0d\x0aHe\x0d\x0a4\x0d\x0allo!\x0d\x0a0\x0d\x0a\x0d\x0a', 'written in order')

with subtest('write_sse'):
    content = Pyjo.Content.Single.new()
    event = {'type': 'foo', 'text': 'bar'}
    content = content.write_sse()
    content = content.write_sse(event)
    content = content.write_sse(event, lambda content, offset: ...)
    is_ok(content.headers.content_type, 'text/event-stream', 'SSE')

done_testing()
