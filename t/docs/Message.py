import Pyjo.Collection
import Pyjo.Content.MultiPart
import Pyjo.Content.Single
import Pyjo.Cookie.Request
import Pyjo.DOM
import Pyjo.Headers
import Pyjo.Message.Request
import Pyjo.Message.Response
import Pyjo.Parameters

from Pyjo.File import tempdir
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


FORM = b'--xYz\x0d\x0aContent-Disposition: form-data; name="foo"; filename="foo.txt"\x0d\x0a\x0d\x0abar\x0d\x0a--xYz--'
UPLOAD = (
    b'POST / HTTP/1.1\x0d\x0aContent-Type: multipart/form-data; boundary=xYz\x0d\x0a'
    + f'Content-Length: {len(FORM)}\x0d\x0a\x0d\x0a'.encode()
    + FORM
)
HTML = b'<html><head><title>Test</title></head><body><h1>One</h1><p>Two</p><h2>Three</h2><p>Four</p></body></html>'

with subtest('Synopsis'):
    from Pyjo.Message import Message

    class MyMessage(Message):
        def cookies(self, *cookies): ...
        def extract_start_line(self, buffer): ...
        def get_start_line_chunk(self, offset): ...
        @property
        def start_line_size(self): ...

    isa_ok(MyMessage(), Message, 'subclass')

    import Pyjo.Message

    class MyMessage(Pyjo.Message.object):
        def cookies(self, *cookies): ...
        def extract_start_line(self, buffer): ...
        def get_start_line_chunk(self, offset): ...
        @property
        def start_line_size(self): ...

    isa_ok(MyMessage.new(), Pyjo.Message.object, 'subclass')

with subtest('finish'):
    msg = Pyjo.Message.Response.new()
    msg.on('finish', lambda msg: ...)
    ok(msg.has_subscribers('finish'), 'subscribed')

    msg = Pyjo.Message.Response.new()
    before = time.time()
    msg.on('finish', lambda msg: msg.headers.header('X-Parser-Time', int(time.time() - before)))
    msg.parse(b'HTTP/1.1 200 OK\x0d\x0aContent-Length: 0\x0d\x0a\x0d\x0a')
    is_ok(msg.headers.header('X-Parser-Time'), '0', 'parser time')

with subtest('progress'):
    msg = Pyjo.Message.Response.new()
    msg.on('progress', lambda msg, *args: ...)
    ok(msg.has_subscribers('progress'), 'subscribed')

    msg = Pyjo.Message.Response.new()
    msg.on('progress', lambda msg, state, offset: print(f'Building "{state}" at offset {offset}'))
    msg.code = 200
    like_ok(output(lambda: msg.build_start_line()), r'^Building "start_line" at offset 0\n', 'building')

    msg = Pyjo.Message.Response.new()

    @msg.on('progress')
    def progress(msg):
        if not (length := int(msg.headers.content_length or 0)):
            return
        size = msg.content.progress
        print('Progress:', 100 if size == length else int(size / (length / 100)), '%')

    is_ok(
        output(lambda: msg.parse(b'HTTP/1.1 200 OK\x0d\x0aContent-Length: 4\x0d\x0a\x0d\x0a')),
        'Progress: 0 %\n',
        'headers',
    )
    is_ok(output(lambda: msg.parse(b'ab')), 'Progress: 50 %\n', 'parsing')
    is_ok(output(lambda: msg.parse(b'cd')), 'Progress: 100 %\n', 'parsed')

with subtest('new'):
    msg = Pyjo.Message.Request.new()
    isa_ok(msg, Pyjo.Message.object, 'request')
    msg = Pyjo.Message.Response.new(content=Pyjo.Content.MultiPart.new())
    ok(msg.content.is_multipart, 'content')

with subtest('default_charset'):
    msg = Pyjo.Message.Request.new()
    charset = msg.default_charset
    is_ok(charset, 'UTF-8', 'default')
    msg.default_charset = 'UTF-8'
    is_ok(msg.default_charset, 'UTF-8', 'set')

with subtest('max_line_size'):
    msg = Pyjo.Message.Request.new()
    size = msg.max_line_size
    is_ok(size, int(os.environ.get('PYJO_MAX_LINE_SIZE') or 8192), 'default')
    msg.max_line_size = 1024
    is_ok(msg.max_line_size, 1024, 'set')

with subtest('max_message_size'):
    msg = Pyjo.Message.Request.new()
    size = msg.max_message_size
    is_ok(size, int(os.environ.get('PYJO_MAX_MESSAGE_SIZE') or 16777216), 'default')
    msg.max_message_size = 1024
    is_ok(msg.max_message_size, 1024, 'set')

with subtest('version'):
    msg = Pyjo.Message.Request.new()
    version = msg.version
    is_ok(version, '1.1', 'default')
    msg.version = '1.1'
    is_ok(msg.version, '1.1', 'set')

with subtest('content'):
    msg = Pyjo.Message.Request.new()
    content = msg.content
    isa_ok(content, Pyjo.Content.Single.object, 'default')
    msg.content = Pyjo.Content.Single.new()
    ok(msg.content is not content, 'set')

with subtest('body'):
    msg = Pyjo.Message.Request.new()
    data = msg.body
    is_ok(data, b'', 'no body')
    msg.body = b'Hello!'
    is_ok(msg.body, b'Hello!', 'set')

with subtest('body_params'):
    msg = Pyjo.Message.Request.new()
    msg.parse(
        b'POST / HTTP/1.1\x0d\x0aContent-Type: application/x-www-form-urlencoded\x0d\x0a'
        b'Content-Length: 7\x0d\x0a\x0d\x0afoo=bar'
    )
    params = msg.body_params
    isa_ok(params, Pyjo.Parameters.object, 'parameters')

    params = msg.body_params.to_dict()
    is_deeply_ok(params, {'foo': 'bar'}, 'names and values')

with subtest('body_size'):
    msg = Pyjo.Message.Request.new().set(body=b'Hello!')
    size = msg.body_size
    is_ok(size, 6, 'size')

with subtest('build_body'):
    msg = Pyjo.Message.Request.new().set(body=b'Hello!')
    data = msg.build_body()
    is_ok(data, b'Hello!', 'body')

with subtest('build_headers'):
    msg = Pyjo.Message.Request.new().set(body=b'Hello!')
    data = msg.build_headers()
    is_ok(data, b'Content-Length: 6\x0d\x0aHost: \x0d\x0a\x0d\x0a', 'headers')

with subtest('build_start_line'):
    msg = Pyjo.Message.Request.new()
    msg.url.parse('http://127.0.0.1/foo')
    data = msg.build_start_line()
    is_ok(data, b'GET /foo HTTP/1.1\x0d\x0a', 'start-line')

with subtest('cookie'):
    msg = Pyjo.Message.Request.new().cookies({'name': 'foo', 'value': 'bar'})
    cookie = msg.cookie('foo')
    isa_ok(cookie, Pyjo.Cookie.Request.object, 'cookie')

    is_ok(output(lambda: print(msg.cookie('foo').value)), 'bar\n', 'cookie value')

with subtest('cookies'):
    msg = Pyjo.Message.Request.new().cookies({'name': 'foo', 'value': 'bar'})
    cookies = msg.cookies()
    is_ok(len(cookies), 1, 'cookies')

with subtest('dom'):
    msg = Pyjo.Message.Response.new().set(body=HTML)
    dom = msg.dom()
    isa_ok(dom, Pyjo.DOM.object, 'DOM')
    collection = msg.dom('a[href]')
    isa_ok(collection, Pyjo.Collection.object, 'collection')

    is_ok(output(lambda: print(msg.dom('h1, h2, h3').map('text').join('\n'))), 'One\nThree\n', 'find right away')
    is_ok(output(lambda: print(msg.dom().at('title').text)), 'Test\n', 'title')
    is_ok(output(lambda: print(msg.dom().at('body').children().map('tag').uniq().join('\n'))), 'h1\np\nh2\n', 'tags')

with subtest('error'):
    msg = Pyjo.Message.Response.new()
    err = msg.error
    is_ok(err, None, 'no error')
    msg.error = {'message': 'Parser error'}
    is_deeply_ok(msg.error, {'message': 'Parser error'}, 'set')
    ok(msg.is_finished, 'finished')

    msg = Pyjo.Message.Response.new()
    msg.error = {'message': 'Connection refused'}
    is_deeply_ok(msg.error, {'message': 'Connection refused'}, 'connection error')

    msg = Pyjo.Message.Response.new()
    msg.error = {'message': 'Internal Server Error', 'code': 500}
    is_deeply_ok(msg.error, {'message': 'Internal Server Error', 'code': 500}, 'response error')

with subtest('every_cookie'):
    msg = Pyjo.Message.Request.new().cookies({'name': 'foo', 'value': 'bar'}, {'name': 'foo', 'value': 'baz'})
    cookies = msg.every_cookie('foo')
    is_ok(len(cookies), 2, 'cookies')

    is_ok(output(lambda: print(msg.every_cookie('foo')[0].value)), 'bar\n', 'first cookie value')

with subtest('every_upload'):
    msg = Pyjo.Message.Request.new()
    msg.parse(UPLOAD)
    uploads = msg.every_upload('foo')
    is_ok(len(uploads), 1, 'uploads')

    is_ok(output(lambda: print(msg.every_upload('foo')[0].asset.slurp())), "b'bar'\n", 'first upload content')

with subtest('extract_start_line'):
    msg = Pyjo.Message.Request.new()
    buffer = bytearray(b'GET / HTTP/1.1\x0d\x0aHost: localhost\x0d\x0a')
    boolean = msg.extract_start_line(buffer)
    ok(boolean, 'start-line extracted')
    is_ok(buffer, b'Host: localhost\x0d\x0a', 'buffer lost the start-line')

with subtest('finish'):
    msg = Pyjo.Message.Request.new()
    msg = msg.finish()
    ok(msg.is_finished, 'finished')

with subtest('fix_headers'):
    msg = Pyjo.Message.Request.new().set(body=b'Hello!')
    msg = msg.fix_headers()
    is_ok(msg.headers.content_length, '6', 'Content-Length')

with subtest('get_body_chunk'):
    msg = Pyjo.Message.Request.new().set(body=b'Hello!')
    offset = 1
    data = msg.get_body_chunk(offset)
    is_ok(data, b'ello!', 'chunk')

with subtest('get_header_chunk'):
    msg = Pyjo.Message.Request.new().set(body=b'Hello!')
    offset = 0
    data = msg.get_header_chunk(offset)
    is_ok(data, b'Content-Length: 6\x0d\x0aHost: \x0d\x0a\x0d\x0a', 'chunk')

with subtest('get_start_line_chunk'):
    msg = Pyjo.Message.Request.new()
    offset = 4
    data = msg.get_start_line_chunk(offset)
    is_ok(data, b'/ HTTP/1.1\x0d\x0a', 'chunk')

with subtest('header_size'):
    msg = Pyjo.Message.Request.new().set(body=b'Hello!')
    size = msg.header_size
    is_ok(size, 29, 'size')

with subtest('headers'):
    msg = Pyjo.Message.Request.new()
    headers = msg.headers
    isa_ok(headers, Pyjo.Headers.object, 'headers')

    headers = msg.content.headers
    ok(headers is msg.headers, 'longer version')

with subtest('is_finished'):
    msg = Pyjo.Message.Request.new()
    boolean = msg.is_finished
    is_ok(boolean, False, 'not finished')

with subtest('is_limit_exceeded'):
    msg = Pyjo.Message.Request.new()
    boolean = msg.is_limit_exceeded
    is_ok(boolean, False, 'not exceeded')

with subtest('json'):
    msg = Pyjo.Message.Response.new().set(body=b'{"foo": {"bar": [' + b'0, ' * 23 + b'"baz"]}}')
    value = msg.json()
    is_deeply_ok(value, {'foo': {'bar': [0] * 23 + ['baz']}}, 'JSON')
    value = msg.json('/foo/bar')
    is_deeply_ok(value, [0] * 23 + ['baz'], 'JSON Pointer')

    is_ok(output(lambda: print(msg.json()['foo']['bar'][23])), 'baz\n', 'extract value')
    is_ok(output(lambda: print(msg.json('/foo/bar/23'))), 'baz\n', 'extract value with JSON Pointer')

with subtest('parse'):
    msg = Pyjo.Message.Response.new()
    msg = msg.parse(b'HTTP/1.1 200 OK...')
    isa_ok(msg, Pyjo.Message.Response.object, 'parsed')

with subtest('save_to'):
    msg = Pyjo.Message.Response.new().set(body=b'Hello!')
    path = tempdir().child('index.html')
    msg = msg.save_to(path)
    is_ok(path.slurp(), b'Hello!', 'saved')

with subtest('start_line_size'):
    msg = Pyjo.Message.Request.new()
    size = msg.start_line_size
    is_ok(size, 16, 'size')

with subtest('text'):
    msg = Pyjo.Message.Response.new().set(body='☃'.encode())
    string = msg.text
    is_ok(string, '☃', 'decoded')

    msg = Pyjo.Message.Response.new().set(body=b'\xff')
    is_ok(msg.text, '\xff', 'characters 0-255')

with subtest('to_bytes'):
    msg = Pyjo.Message.Request.new()
    data = msg.to_bytes()
    is_ok(data, b'GET / HTTP/1.1\x0d\x0aHost: \x0d\x0a\x0d\x0a', 'message')

with subtest('upload'):
    msg = Pyjo.Message.Request.new()
    msg.parse(UPLOAD)
    upload = msg.upload('foo')
    is_ok(upload.filename, 'foo.txt', 'upload')

    is_ok(output(lambda: print(msg.upload('foo').asset.slurp())), "b'bar'\n", 'upload content')

with subtest('uploads'):
    uploads = msg.uploads()
    is_ok(len(uploads), 1, 'uploads')

    def names():
        for upload in msg.uploads():
            print(upload.name)

    is_ok(output(names), 'foo\n', 'names of all uploads')

done_testing()
