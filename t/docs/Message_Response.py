import Pyjo.Cookie.Response
import Pyjo.Message.Response

from Pyjo.Test import *

import contextlib
import io
import os
import re


def output(cb):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        cb()
    return out.getvalue()


with subtest('Synopsis'):

    def parse():
        import Pyjo.Message.Response

        # Parse
        res = Pyjo.Message.Response.new()
        res.parse(b'HTTP/1.0 200 OK\x0d\x0a')
        res.parse(b'Content-Length: 12\x0d\x0a')
        res.parse(b'Content-Type: text/plain\x0d\x0a\x0d\x0a')
        res.parse(b'Hello World!')
        print(res.code)
        print(res.headers.content_type)
        print(res.body)

    is_ok(output(parse), "200\ntext/plain\nb'Hello World!'\n", 'parse')

    def build():
        import Pyjo.Message.Response

        # Build
        res = Pyjo.Message.Response.new()
        res.code = 200
        res.headers.content_type = 'text/plain'
        res.body = b'Hello World!'
        print(res.to_bytes())

    like_ok(
        output(build),
        re.compile(
            r"^b'HTTP/1\.1 200 OK\\r\\nContent-Length: 12\\r\\nContent-Type: text/plain\\r\\n"
            r"Date: .+ GMT\\r\\n\\r\\nHello World!'\n$"
        ),
        'build',
    )

with subtest('new'):
    res = Pyjo.Message.Response.new()
    is_ok(res.code, None, 'default')
    res = Pyjo.Message.Response.new(code=200, message='OK')
    is_ok(res.code, 200, 'code')
    is_ok(res.message, 'OK', 'message')

with subtest('code'):
    res = Pyjo.Message.Response.new()
    code = res.code
    is_ok(code, None, 'default')
    res.code = 200
    is_ok(res.code, 200, 'set')

with subtest('message'):
    res = Pyjo.Message.Response.new()
    message = res.message
    is_ok(message, None, 'default')
    res.message = 'OK'
    is_ok(res.message, 'OK', 'set')

with subtest('max_message_size'):
    res = Pyjo.Message.Response.new()
    size = res.max_message_size
    is_ok(size, int(os.environ.get('PYJO_MAX_MESSAGE_SIZE') or 2147483648), 'default')
    res.max_message_size = 1024
    is_ok(res.max_message_size, 1024, 'set')

with subtest('cookies'):
    res = Pyjo.Message.Response.new()
    cookies = res.cookies()
    is_deeply_ok(cookies, [], 'no cookies')
    res = res.cookies(Pyjo.Cookie.Response.new(name='foo', value='bar'))
    res = res.cookies({'name': 'bar', 'value': 'baz'})
    is_deeply_ok(res.headers.every_header('Set-Cookie'), ['foo=bar', 'bar=baz'], 'added')

    def names():
        for cookie in res.cookies():
            print(cookie.name)

    is_ok(output(names), 'foo\nbar\n', 'names of all cookies')

with subtest('default_message'):
    res = Pyjo.Message.Response.new()
    message = res.default_message()
    is_ok(message, 'Not Found', 'default')
    message = res.default_message(418)
    is_ok(message, "I'm a teapot", 'code')

with subtest('extract_start_line'):
    res = Pyjo.Message.Response.new()
    buffer = bytearray(b'HTTP/1.1 200 OK\x0d\x0a')
    boolean = res.extract_start_line(buffer)
    ok(boolean, 'status-line extracted')
    is_ok(buffer, b'', 'buffer lost the status-line')

with subtest('fix_headers'):
    res = Pyjo.Message.Response.new()
    res = res.fix_headers()
    ok(res.headers.date, 'Date')

with subtest('get_start_line_chunk'):
    res = Pyjo.Message.Response.new()
    offset = 0
    data = res.get_start_line_chunk(offset)
    is_ok(data, b'HTTP/1.1 404 Not Found\x0d\x0a', 'chunk')

with subtest('is_client_error'):
    res = Pyjo.Message.Response.new(code=404)
    boolean = res.is_client_error
    is_ok(boolean, True, '4xx')

with subtest('is_empty'):
    res = Pyjo.Message.Response.new(code=204)
    boolean = res.is_empty
    is_ok(boolean, True, 'no content')

with subtest('is_error'):
    res = Pyjo.Message.Response.new(code=500)
    boolean = res.is_error
    is_ok(boolean, True, '5xx')

with subtest('is_info'):
    res = Pyjo.Message.Response.new(code=100)
    boolean = res.is_info
    is_ok(boolean, True, '1xx')

with subtest('is_redirect'):
    res = Pyjo.Message.Response.new(code=302)
    boolean = res.is_redirect
    is_ok(boolean, True, '3xx')

with subtest('is_server_error'):
    res = Pyjo.Message.Response.new(code=503)
    boolean = res.is_server_error
    is_ok(boolean, True, '5xx')

with subtest('is_success'):
    res = Pyjo.Message.Response.new(code=200)
    boolean = res.is_success
    is_ok(boolean, True, '2xx')

with subtest('start_line_size'):
    res = Pyjo.Message.Response.new()
    size = res.start_line_size
    is_ok(size, 24, 'size')

done_testing()
