import Pyjo.Content.MultiPart
import Pyjo.Content.Single
import Pyjo.Cookie.Request
import Pyjo.Message
import Pyjo.Message.Request
import Pyjo.Upload
import Pyjo.URL

from Pyjo.File import tempdir
from Pyjo.Test import *
from Pyjo.Util import encode, gzip

import os
import re
import time


# Renamed from Mojolicious: to_string of a message is to_bytes

with subtest('Defaults'):
    req = Pyjo.Message.Request.new()
    is_ok(req.max_message_size, 16777216, 'right default')

with subtest('Request ID'):
    id = Pyjo.Message.Request.new().request_id
    ok(len(id) >= 8, 'at least 8 characters')
    id2 = Pyjo.Message.Request.new().request_id
    ok(len(id) >= 8, 'at least 8 characters')
    isnt_ok(id, id2, 'different id')

with subtest('Parse HTTP 1.1 message with huge "Cookie" header exceeding all limits'):
    req = Pyjo.Message.Request.new()
    finished = None
    req.max_message_size = req.headers.max_line_size
    huge = b'a=b; ' * req.max_message_size

    @req.on('finish')
    def finish(req, *args):
        global finished
        finished = req.is_finished

    ok(not req.is_limit_exceeded, 'limit is not exceeded')
    req.parse(b'PUT /upload HTTP/1.1\x0d\x0aCookie: ' + huge + b'\x0d\x0a')
    ok(req.is_limit_exceeded, 'limit is exceeded')
    req.parse(b'Content-Length: 0\x0d\x0a\x0d\x0a')
    ok(finished, 'finish event has been emitted')
    ok(req.is_finished, 'request is finished')
    is_ok(req.content.leftovers(), b'', 'no leftovers')
    is_ok(req.error['message'], 'Maximum message size exceeded', 'right error')
    ok(req.is_limit_exceeded, 'limit is exceeded')
    is_ok(req.method, 'PUT', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/upload', 'right URL')
    is_ok(req.cookie('a'), None, 'no value')

with subtest('Parse HTTP 1.1 message with huge "Cookie" header exceeding line limit'):
    req = Pyjo.Message.Request.new()
    is_ok(req.headers.max_line_size, 8192, 'right size')
    is_ok(req.headers.max_lines, 100, 'right number')
    req.parse(b'GET / HTTP/1.1\x0d\x0a')
    req.parse(b'Cookie: ' + b'a=b; ' * 131072 + b'\x0d\x0a')
    req.parse(b'Content-Length: 0\x0d\x0a\x0d\x0a')
    ok(req.is_finished, 'request is finished')
    is_ok(req.error['message'], 'Maximum header size exceeded', 'right error')
    ok(req.is_limit_exceeded, 'limit is exceeded')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/', 'right URL')
    is_ok(req.cookie('a'), None, 'no value')
    is_ok(req.body, b'', 'no content')

with subtest('Parse HTTP 1.1 message with huge "Cookie" header exceeding line limit (alternative)'):
    req = Pyjo.Message.Request.new()
    req.parse(b'GET / HTTP/1.1\x0d\x0a')
    req.parse(
        b'Content-Length: 4\x0d\x0aCookie: ' + b'a=b; ' * 131072 + b'\x0d\x0a' + b'X-Test: 23\x0d\x0a\x0d\x0aabcd'
    )
    ok(req.is_finished, 'request is finished')
    is_ok(req.error['message'], 'Maximum header size exceeded', 'right error')
    ok(req.is_limit_exceeded, 'limit is exceeded')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/', 'right URL')
    is_ok(req.cookie('a'), None, 'no value')
    is_ok(req.body, b'', 'no content')

with subtest('Parse HTTP 1.1 message with content exceeding line limit'):
    req = Pyjo.Message.Request.new()
    is_ok(req.max_message_size, 16777216, 'right size')
    req.parse(b'GET / HTTP/1.1\x0d\x0a')
    req.parse(b'Content-Length: 655360\x0d\x0a\x0d\x0a' + b'a=b; ' * 131072)
    ok(req.is_finished, 'request is finished')
    is_ok(req.error, None, 'no error')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/', 'right URL')
    is_ok(req.body, b'a=b; ' * 131072, 'right content')

with subtest('Parse broken start-line'):
    req = Pyjo.Message.Request.new()
    req.parse(b'12345\x0d\x0a')
    ok(req.is_finished, 'request is finished')
    is_ok(req.error['message'], 'Bad request start-line', 'right error')
    ok(not req.is_limit_exceeded, 'limit is not exceeded')

with subtest('Parse broken HTTP 1.1 message with header exceeding line limit'):
    req = Pyjo.Message.Request.new()
    req.parse(b'GET / HTTP/1.1\x0d\x0a')
    req.parse(b'Content-Length: 0\x0d\x0a')
    ok(not req.is_limit_exceeded, 'limit is not exceeded')
    req.parse(b'Foo: ' + b'a' * 8192)
    ok(req.is_finished, 'request is finished')
    is_ok(req.error['message'], 'Maximum header size exceeded', 'right error')
    ok(req.is_limit_exceeded, 'limit is exceeded')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/', 'right URL')
    is_ok(req.headers.header('Foo'), None, 'no "Foo" value')
    is_ok(req.body, b'', 'no content')

with subtest('Parse broken HTTP 1.1 message with start-line exceeding line limit'):
    req = Pyjo.Message.Request.new()
    is_ok(req.max_line_size, 8192, 'right size')
    is_ok(req.headers.max_lines, 100, 'right number')
    req.parse(b'GET /' + b'abcd' * 131072 + b' HTTP/1.1')
    ok(req.is_finished, 'request is finished')
    is_ok(req.error['message'], 'Maximum start-line size exceeded', 'right error')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '', 'no URL')
    is_ok(req.cookie('a'), None, 'no value')
    is_ok(req.body, b'', 'no content')

with subtest('Parse broken HTTP 1.1 message with start-line exceeding line limit (alternative)'):
    req = Pyjo.Message.Request.new()
    req.parse(b'GET /')
    req.parse(b'abcd' * 131072)
    ok(req.is_finished, 'request is finished')
    is_ok(req.error['message'], 'Maximum start-line size exceeded', 'right error')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '', 'no URL')
    is_ok(req.cookie('a'), None, 'no value')
    is_ok(req.body, b'', 'no content')

with subtest('Parse pipelined HTTP 1.1 messages exceeding leftover limit'):
    req = Pyjo.Message.Request.new()
    is_ok(req.content.max_leftover_size, 262144, 'right size')
    req.parse(b'GET /one HTTP/1.1\x0d\x0a')
    req.parse(b'Content-Length: 120000\x0d\x0a\x0d\x0a' + b'a' * 120000)
    ok(req.is_finished, 'request is finished')
    is_ok(req.content.leftovers(), b'', 'no leftovers')
    req.parse(b'GET /two HTTP/1.1\x0d\x0a')
    req.parse(b'Content-Length: 120000\x0d\x0a\x0d\x0a' + b'b' * 120000)
    is_ok(len(req.content.leftovers()), 120045, 'right size')
    req.parse(b'GET /three HTTP/1.1\x0d\x0a')
    req.parse(b'Content-Length: 120000\x0d\x0a\x0d\x0a' + b'c' * 120000)
    is_ok(len(req.content.leftovers()), 240092, 'right size')
    req.parse(b'GET /four HTTP/1.1\x0d\x0a')
    req.parse(b'Content-Length: 120000\x0d\x0a\x0d\x0a' + b'd' * 120000)
    is_ok(len(req.content.leftovers()), 360138, 'right size')
    req.parse(b'GET /five HTTP/1.1\x0d\x0a')
    req.parse(b'Content-Length: 120000\x0d\x0a\x0d\x0a' + b'e' * 120000)
    is_ok(len(req.content.leftovers()), 360138, 'right size')
    is_ok(req.error, None, 'no error')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/one', 'right URL')
    is_ok(req.body, b'a' * 120000, 'right content')

with subtest('Parse pipelined HTTP 1.1 messages exceeding leftover limit (chunked)'):
    req = Pyjo.Message.Request.new()
    req.parse(b'GET /one HTTP/1.1\x0d\x0a')
    req.parse(b'Transfer-Encoding: chunked\x0d\x0a\x0d\x0a')
    req.parse(b'ea60\x0d\x0a')
    req.parse(b'a' * 60000)
    req.parse(b'\x0d\x0aea60\x0d\x0a')
    req.parse(b'a' * 60000)
    req.parse(b'\x0d\x0a0\x0d\x0a\x0d\x0a')
    ok(req.is_finished, 'request is finished')
    is_ok(req.content.leftovers(), b'', 'no leftovers')
    req.parse(b'GET /two HTTP/1.1\x0d\x0a')
    req.parse(b'Content-Length: 120000\x0d\x0a\x0d\x0a' + b'b' * 120000)
    is_ok(len(req.content.leftovers()), 120045, 'right size')
    req.parse(b'GET /three HTTP/1.1\x0d\x0a')
    req.parse(b'Content-Length: 120000\x0d\x0a\x0d\x0a' + b'c' * 120000)
    is_ok(len(req.content.leftovers()), 240092, 'right size')
    req.parse(b'GET /four HTTP/1.1\x0d\x0a')
    req.parse(b'Content-Length: 120000\x0d\x0a\x0d\x0a' + b'd' * 120000)
    is_ok(len(req.content.leftovers()), 360138, 'right size')
    req.parse(b'GET /five HTTP/1.1\x0d\x0a')
    req.parse(b'Content-Length: 120000\x0d\x0a\x0d\x0a' + b'e' * 120000)
    is_ok(len(req.content.leftovers()), 360138, 'right size')
    is_ok(req.error, None, 'no error')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/one', 'right URL')
    is_ok(req.body, b'a' * 120000, 'right content')

with subtest('Parse HTTP 1.1 start-line, no headers and body'):
    req = Pyjo.Message.Request.new()
    req.parse(b'GET / HTTP/1.1\x0d\x0a\x0d\x0a')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/', 'right URL')

with subtest('Parse HTTP 1.1 start-line, no headers and body (small chunks)'):
    req = Pyjo.Message.Request.new()
    req.parse(b'G')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'E')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'T')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b' ')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'/')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b' ')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'H')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'T')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'T')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'P')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'/')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'1')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'.')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'1')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'\x0d')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'\x0a')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'\x0d')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'\x0a')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/', 'right URL')

with subtest('Parse pipelined HTTP 1.1 start-line, no headers and body'):
    req = Pyjo.Message.Request.new()
    req.parse(b'GET / HTTP/1.1\x0d\x0a\x0d\x0aGET / HTTP/1.1\x0d\x0a\x0d\x0a')
    ok(req.is_finished, 'request is finished')
    is_ok(req.content.leftovers(), b'GET / HTTP/1.1\x0d\x0a\x0d\x0a', 'second request in leftovers')

with subtest('Parse HTTP 1.1 start-line, no headers and body with leading CRLFs'):
    req = Pyjo.Message.Request.new()
    req.parse(b'\x0d\x0a GET / HTTP/1.1\x0d\x0a\x0d\x0a')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/', 'right URL')

with subtest('Parse WebSocket handshake request'):
    req = Pyjo.Message.Request.new()
    req.parse(b'GET /demo HTTP/1.1\x0d\x0a')
    req.parse(b'Host: example.com\x0d\x0a')
    req.parse(b'Connection: Upgrade\x0d\x0a')
    req.parse(b'Sec-WebSocket-Key: abcdef=\x0d\x0a')
    req.parse(b'Sec-WebSocket-Protocol: sample\x0d\x0a')
    req.parse(b'Upgrade: websocket\x0d\x0a\x0d\x0a')
    ok(req.is_finished, 'request is finished')
    ok(req.is_handshake, 'request is WebSocket handshake')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/demo', 'right URL')
    is_ok(req.headers.host, 'example.com', 'right "Host" value')
    is_ok(req.headers.connection, 'Upgrade', 'right "Connection" value')
    is_ok(req.headers.sec_websocket_protocol, 'sample', 'right "Sec-WebSocket-Protocol" value')
    is_ok(req.headers.upgrade, 'websocket', 'right "Upgrade" value')
    is_ok(req.headers.sec_websocket_key, 'abcdef=', 'right "Sec-WebSocket-Key" value')
    is_ok(req.body, b'', 'no content')

with subtest('Parse HTTP 1.0 start-line and headers, no body'):
    req = Pyjo.Message.Request.new()
    req.parse(b'GET /foo/bar/baz.html HTTP/1.0\x0d\x0a')
    req.parse(b'Content-Type: text/plain;charset=UTF-8\x0d\x0a')
    req.parse(b'Content-Length: 0\x0d\x0a\x0d\x0a')
    ok(req.is_finished, 'request is finished')
    ok(not req.is_handshake, 'request is not a WebSocket handshake')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.0', 'right version')
    is_ok(req.url, '/foo/bar/baz.html', 'right URL')
    is_ok(req.headers.content_type, 'text/plain;charset=UTF-8', 'right "Content-Type" value')
    is_ok(req.headers.content_length, '0', 'right "Content-Length" value')
    is_ok(req.content.charset, 'UTF-8', 'right charset')

with subtest('Parse HTTP 1.0 start-line and headers, no body (missing Content-Length)'):
    req = Pyjo.Message.Request.new()
    req.parse(b'GET /foo/bar/baz.html HTTP/1.0\x0d\x0a')
    req.parse(b'Content-Type: text/plain\x0d\x0a\x0d\x0a')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.0', 'right version')
    is_ok(req.url, '/foo/bar/baz.html', 'right URL')
    is_ok(req.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(req.headers.content_length, None, 'no "Content-Length" value')

with subtest('Parse full HTTP 1.0 request (file storage)'):
    os.environ['PYJO_MAX_MEMORY_SIZE'] = '12'
    try:
        req = Pyjo.Message.Request.new()
        upgrade = size = None

        @req.content.asset.on('upgrade')
        def upgrade_cb(mem, file):
            global upgrade, size
            upgrade = file.is_file
            size = file.size

        is_ok(req.content.asset.max_memory_size, 12, 'right size')
        is_ok(req.content.progress, 0, 'right progress')
        req.parse(b'GET /foo/bar/baz.html?fo')
        is_ok(req.content.progress, 0, 'right progress')
        req.parse(b'o=13 HTTP/1.0\x0d\x0aContent')
        req.parse(b'-Type: text/')
        is_ok(req.content.progress, 0, 'right progress')
        req.parse(b'plain\x0d\x0aContent-Length: 27\x0d\x0a\x0d\x0aHell')
        is_ok(req.content.progress, 4, 'right progress')
        ok(not req.content.asset.is_file, 'stored in memory')
        ok(not upgrade, 'upgrade event has not been emitted')
        req.parse(b'o World!\n')
        ok(upgrade, 'upgrade event has been emitted')
        is_ok(size, 0, 'file had no content yet')
        is_ok(req.content.asset.size, 13, 'file has content')
        is_ok(req.content.progress, 13, 'right progress')
        ok(req.content.asset.is_file, 'stored in file')
        req.parse(b'1234\nlalalala\n')
        is_ok(req.content.progress, 27, 'right progress')
        ok(req.content.asset.is_file, 'stored in file')
        ok(req.is_finished, 'request is finished')
        is_ok(req.method, 'GET', 'right method')
        is_ok(req.version, '1.0', 'right version')
        is_ok(req.url, '/foo/bar/baz.html?foo=13', 'right URL')
        is_ok(req.headers.content_type, 'text/plain', 'right "Content-Type" value')
        is_ok(req.headers.content_length, '27', 'right "Content-Length" value')
    finally:
        del os.environ['PYJO_MAX_MEMORY_SIZE']

with subtest('Parse HTTP 1.0 start-line and headers, no body (missing Content-Length)'):
    req = Pyjo.Message.Request.new()
    req.parse(b'GET /foo/bar/baz.html HTTP/1.0\x0d\x0a')
    req.parse(b'Content-Type: text/plain\x0d\x0a')
    req.parse(b'Connection: Close\x0d\x0a\x0d\x0a')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.0', 'right version')
    is_ok(req.url, '/foo/bar/baz.html', 'right URL')
    is_ok(req.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(req.headers.content_length, None, 'no "Content-Length" value')

with subtest('Parse HTTP 1.0 start-line (with line size limit)'):
    os.environ['PYJO_MAX_LINE_SIZE'] = '5'
    try:
        req = Pyjo.Message.Request.new()
        limit = None

        @req.on('finish')
        def finish(req, *args):
            global limit
            limit = req.is_limit_exceeded

        ok(not req.is_limit_exceeded, 'limit is not exceeded')
        is_ok(req.headers.max_line_size, 5, 'right size')
        req.parse(b'GET /foo/bar/baz.html HTTP/1')
        ok(req.is_finished, 'request is finished')
        is_ok(req.error['message'], 'Maximum start-line size exceeded', 'right error')
        ok(req.is_limit_exceeded, 'limit is exceeded')
        ok(limit, 'limit is exceeded')
        req.error = {'message': 'Nothing important.'}
        is_ok(req.error['message'], 'Nothing important.', 'right error')
        ok(req.is_limit_exceeded, 'limit is still exceeded')
    finally:
        del os.environ['PYJO_MAX_LINE_SIZE']

with subtest('Parse HTTP 1.0 start-line and headers (with line size limit)'):
    os.environ['PYJO_MAX_LINE_SIZE'] = '20'
    try:
        req = Pyjo.Message.Request.new()
        is_ok(req.max_line_size, 20, 'right size')
        req.parse(b'GET / HTTP/1.0\x0d\x0a')
        req.parse(b'Content-Type: text/plain\x0d\x0a')
        ok(req.is_finished, 'request is finished')
        is_ok(req.error['message'], 'Maximum header size exceeded', 'right error')
        ok(req.is_limit_exceeded, 'limit is exceeded')
    finally:
        del os.environ['PYJO_MAX_LINE_SIZE']

with subtest('Parse HTTP 1.0 start-line (with message size limit)'):
    os.environ['PYJO_MAX_MESSAGE_SIZE'] = '5'
    try:
        req = Pyjo.Message.Request.new()
        limit = None

        @req.on('finish')
        def finish(req, *args):
            global limit
            limit = req.is_limit_exceeded

        is_ok(req.max_message_size, 5, 'right size')
        req.parse(b'GET /foo/bar/baz.html HTTP/1')
        ok(req.is_finished, 'request is finished')
        is_ok(req.error['message'], 'Maximum message size exceeded', 'right error')
        ok(req.is_limit_exceeded, 'limit is exceeded')
        ok(limit, 'limit is exceeded')
    finally:
        del os.environ['PYJO_MAX_MESSAGE_SIZE']

with subtest('Parse HTTP 1.0 start-line and headers (with message size limit)'):
    os.environ['PYJO_MAX_MESSAGE_SIZE'] = '20'
    try:
        req = Pyjo.Message.Request.new()
        req.parse(b'GET / HTTP/1.0\x0d\x0a')
        req.parse(b'Content-Type: text/plain\x0d\x0a')
        ok(req.is_finished, 'request is finished')
        is_ok(req.error['message'], 'Maximum message size exceeded', 'right error')
        ok(req.is_limit_exceeded, 'limit is exceeded')
    finally:
        del os.environ['PYJO_MAX_MESSAGE_SIZE']

with subtest('Parse HTTP 1.0 start-line, headers and body (with message size limit)'):
    os.environ['PYJO_MAX_MESSAGE_SIZE'] = '50'
    try:
        req = Pyjo.Message.Request.new()
        req.parse(b'GET / HTTP/1.0\x0d\x0a')
        req.parse(b'Content-Length: 24\x0d\x0a\x0d\x0a')
        req.parse(b'Hello World!')
        req.parse(b'Hello World!')
        ok(req.is_finished, 'request is finished')
        is_ok(req.error['message'], 'Maximum message size exceeded', 'right error')
        ok(req.is_limit_exceeded, 'limit is exceeded')
    finally:
        del os.environ['PYJO_MAX_MESSAGE_SIZE']

with subtest('Parse HTTP 1.1 message with headers exceeding line limit'):
    os.environ['PYJO_MAX_LINES'] = '5'
    try:
        req = Pyjo.Message.Request.new()
        is_ok(req.headers.max_lines, 5, 'right number')
        req.parse(b'GET / HTTP/1.1\x0d\x0a')
        req.parse(b'A: a\x0d\x0aB: b\x0d\x0aC: c\x0d\x0aD: d\x0d\x0a')
        ok(not req.is_limit_exceeded, 'limit is not exceeded')
        req.parse(b'D: d\x0d\x0a\x0d\x0a')
        ok(req.is_finished, 'request is finished')
        is_ok(req.error['message'], 'Maximum header size exceeded', 'right error')
        ok(req.is_limit_exceeded, 'limit is exceeded')
        is_ok(req.method, 'GET', 'right method')
        is_ok(req.version, '1.1', 'right version')
        is_ok(req.url, '/', 'right URL')
    finally:
        del os.environ['PYJO_MAX_LINES']

with subtest('Parse full HTTP 1.0 request (solitary LF)'):
    req = Pyjo.Message.Request.new()
    body = b''

    @req.content.on('read')
    def read(content, chunk):
        global body
        body += chunk

    req.parse(b'GET /foo/bar/baz.html?fo')
    req.parse(b'o=13 HTTP/1.0\x0aContent')
    req.parse(b'-Type: text/')
    req.parse(b'plain\x0aContent-Length: 27\x0a\x0aH')
    req.parse(b'ello World!\n1234\nlalalala\n')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.0', 'right version')
    is_ok(req.url, '/foo/bar/baz.html?foo=13', 'right URL')
    is_ok(req.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(req.headers.content_length, '27', 'right "Content-Length" value')
    is_ok(req.body, b'Hello World!\n1234\nlalalala\n', 'right content')
    is_ok(body, b'Hello World!\n1234\nlalalala\n', 'right content')

with subtest('Parse full HTTP 1.0 request (no scheme and empty elements in path)'):
    req = Pyjo.Message.Request.new()
    req.parse(b'GET //foo/bar//baz.html?fo')
    req.parse(b'o=13 HTTP/1.0\x0d\x0aContent')
    req.parse(b'-Type: text/')
    req.parse(b'plain\x0d\x0aContent-Length: 27\x0d\x0a\x0d\x0aHell')
    req.parse(b'o World!\n1234\nlalalala\n')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.0', 'right version')
    is_ok(req.url.host, None, 'no host')
    is_ok(req.url.path, '//foo/bar//baz.html', 'right path')
    is_ok(req.url, '//foo/bar//baz.html?foo=13', 'right URL')
    is_ok(req.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(req.headers.content_length, '27', 'right "Content-Length" value')
    is_ok(req.headers.host, None, '"Host" value is not defined')

    req.fix_headers()
    is_ok(req.url.host, None, 'still no URL host')
    is_ok(req.headers.host, '', '"Host" value is fixed')

with subtest('Parse full HTTP 1.0 request (behind reverse proxy)'):
    req = Pyjo.Message.Request.new()
    req.parse(b'GET /foo/bar/baz.html?fo')
    req.parse(b'o=13 HTTP/1.0\x0d\x0aContent')
    req.parse(b'-Type: text/')
    req.parse(b'plain\x0d\x0aContent-Length: 27\x0d\x0a')
    req.parse(b'Host: mojolicious.org\x0d\x0a')
    req.parse(b'X-Forwarded-For: 192.168.2.1, 127.0.0.1\x0d\x0a\x0d\x0a')
    req.parse(b'Hello World!\n1234\nlalalala\n')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.0', 'right version')
    is_ok(req.url, '/foo/bar/baz.html?foo=13', 'right URL')
    is_ok(req.url.to_abs(), 'http://mojolicious.org/foo/bar/baz.html?foo=13', 'right absolute URL')
    is_ok(req.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(req.headers.content_length, '27', 'right "Content-Length" value')

with subtest('Parse full HTTP 1.0 request with zero chunk'):
    req = Pyjo.Message.Request.new()
    finished = None

    @req.on('finish')
    def finish(req, *args):
        global finished
        finished = req.is_finished

    req.parse(b'GET /foo/bar/baz.html?fo')
    req.parse(b'o=13 HTTP/1.0\x0d\x0aContent')
    req.parse(b'-Type: text/')
    req.parse(b'plain\x0d\x0aContent-Length: 27\x0d\x0a\x0d\x0aHell')
    req.parse(b'o World!\n123')
    req.parse(b'0')
    req.parse(b'\nlalalala\n')
    ok(finished, 'finish event has been emitted')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.0', 'right version')
    is_ok(req.url, '/foo/bar/baz.html?foo=13', 'right URL')
    is_ok(req.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(req.headers.content_length, '27', 'right "Content-Length" value')

with subtest('Parse full HTTP 1.0 request with UTF-8 form input'):
    req = Pyjo.Message.Request.new()
    req.parse(b'GET /foo/bar/baz.html?fo')
    req.parse(b'o=13 HTTP/1.0\x0d\x0aContent')
    req.parse(b'-Type: application/')
    req.parse(b'x-www-form-urlencoded\x0d\x0aContent-Length: 14')
    req.parse(b'\x0d\x0a\x0d\x0a')
    req.parse(b'name=%E2%98%83')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.0', 'right version')
    is_ok(req.url, '/foo/bar/baz.html?foo=13', 'right URL')
    is_ok(req.headers.content_type, 'application/x-www-form-urlencoded', 'right "Content-Type" value')
    is_ok(req.headers.content_length, '14', 'right "Content-Length" value')
    is_ok(req.param('name'), '☃', 'right value')

with subtest('Parse HTTP 1.1 gzip compressed request (no decompression)'):
    compressed = gzip(uncompressed := b'abc' * 1000)
    req = Pyjo.Message.Request.new()
    req.parse(b'POST /foo HTTP/1.1\x0d\x0a')
    req.parse(b'Content-Type: text/plain\x0d\x0a')
    req.parse(f'Content-Length: {len(compressed)}\x0d\x0a'.encode())
    req.parse(b'Content-Encoding: GZip\x0d\x0a\x0d\x0a')
    ok(req.content.is_compressed, 'content is compressed')
    req.parse(compressed)
    ok(req.content.is_compressed, 'content is still compressed')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo', 'right URL')
    is_ok(req.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(req.headers.content_length, str(len(compressed)), 'right "Content-Length" value')
    is_ok(req.body, compressed, 'right content')

with subtest('Parse HTTP 1.1 chunked request'):
    req = Pyjo.Message.Request.new()
    is_ok(req.content.progress, 0, 'right progress')
    req.parse(b'POST /foo/bar/baz.html?foo=13 HTTP/1.1\x0d\x0a')
    is_ok(req.content.progress, 0, 'right progress')
    req.parse(b'Content-Type: text/plain\x0d\x0a')
    req.parse(b'Transfer-Encoding: chunked\x0d\x0a\x0d\x0a')
    is_ok(req.content.progress, 0, 'right progress')
    req.parse(b'4\x0d\x0a')
    is_ok(req.content.progress, 3, 'right progress')
    req.parse(b'abcd\x0d\x0a')
    is_ok(req.content.progress, 9, 'right progress')
    req.parse(b'9\x0d\x0a')
    is_ok(req.content.progress, 12, 'right progress')
    req.parse(b'abcdefghi\x0d\x0a')
    is_ok(req.content.progress, 23, 'right progress')
    req.parse(b'0\x0d\x0a\x0d\x0a')
    is_ok(req.content.progress, 28, 'right progress')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar/baz.html?foo=13', 'right URL')
    is_ok(req.headers.content_length, '13', 'right "Content-Length" value')
    is_ok(req.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(req.content.asset.size, 13, 'right size')
    is_ok(req.content.asset.slurp(), b'abcdabcdefghi', 'right content')

with subtest('Parse HTTP 1.1 chunked request with callbacks'):
    req = Pyjo.Message.Request.new()
    progress = buffer = finish = ''
    buffer = b''

    @req.on('progress')
    def progress_cb(self, *args):
        global progress
        if self.content.is_parsing_body:
            progress = progress or self.url.path

    @req.content.unsubscribe('read').on('read')
    def read(content, chunk):
        global buffer
        buffer += chunk

    @req.on('finish')
    def finish_cb(req):
        global finish
        finish += str(req.url.query)

    req.parse(b'POST /foo/bar/baz.html?foo=13 HTTP/1.1\x0d\x0a')
    is_ok(progress, '', 'no progress')
    req.parse(b'Content-Type: text/plain\x0d\x0a')
    is_ok(progress, '', 'no progress')
    req.parse(b'Transfer-Encoding: chunked\x0d\x0a\x0d\x0a')
    is_ok(progress, '/foo/bar/baz.html', 'made progress')
    req.parse(b'4\x0d\x0a')
    req.parse(b'abcd\x0d\x0a')
    req.parse(b'9\x0d\x0a')
    req.parse(b'abcdefghi\x0d\x0a')
    is_ok(finish, '', 'not finished yet')
    req.parse(b'0\x0d\x0a\x0d\x0a')
    is_ok(finish, 'foo=13', 'finished')
    is_ok(progress, '/foo/bar/baz.html', 'made progress')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar/baz.html?foo=13', 'right URL')
    is_ok(req.headers.content_length, '13', 'right "Content-Length" value')
    is_ok(req.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(buffer, b'abcdabcdefghi', 'right content')

with subtest('Parse HTTP 1.1 "application/x-www-form-urlencoded"'):
    req = Pyjo.Message.Request.new()
    req.parse(b'POST /foo/bar/baz.html?foo=13 HTTP/1.1\x0d\x0a')
    req.parse(b'Content-Length: 25\x0d\x0a')
    req.parse(b'Content-Type: application/x-www-form-urlencoded\x0d\x0a')
    req.parse(b'\x0d\x0afoo=bar&+tset=23+&foo=bar')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar/baz.html?foo=13', 'right URL')
    is_ok(req.headers.content_type, 'application/x-www-form-urlencoded', 'right "Content-Type" value')
    is_ok(req.content.asset.size, 25, 'right size')
    is_ok(req.content.asset.slurp(), b'foo=bar&+tset=23+&foo=bar', 'right content')
    is_deeply_ok(req.body_params.to_dict()['foo'], ['bar', 'bar'], 'right values')
    is_ok(req.body_params.to_dict()[' tset'], '23 ', 'right value')
    is_ok(req.body_params, 'foo=bar&+tset=23+&foo=bar', 'right parameters')
    is_deeply_ok(req.params.to_dict()['foo'], ['bar', 'bar', '13'], 'right values')
    is_deeply_ok(req.every_param('foo'), ['bar', 'bar', '13'], 'right values')
    is_ok(req.param(' tset'), '23 ', 'right value')
    req.param('set', 'single')
    is_ok(req.param('set'), 'single', 'setting single param works')
    req.param('multi', 1, 2, 3)
    is_deeply_ok(req.every_param('multi'), ['1', '2', '3'], 'setting multiple value param works')
    is_ok(req.param('test23'), None, 'no value')

with subtest('Parse HTTP 1.1 chunked request with trailing headers'):
    req = Pyjo.Message.Request.new()
    req.parse(b'POST /foo/bar/baz.html?foo=13&bar=23 HTTP/1.1\x0d\x0a')
    req.parse(b'Content-Type: text/plain\x0d\x0a')
    req.parse(b'Transfer-Encoding: whatever\x0d\x0a')
    req.parse(b'Trailer: X-Trailer1; X-Trailer2\x0d\x0a\x0d\x0a')
    req.parse(b'4\x0d\x0a')
    req.parse(b'abcd\x0d\x0a')
    req.parse(b'9\x0d\x0a')
    req.parse(b'abcdefghi\x0d\x0a')
    req.parse(b'0\x0d\x0a')
    req.parse(b'X-Trailer1: test\x0d\x0a')
    req.parse(b'X-Trailer2: 123\x0d\x0a\x0d\x0a')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar/baz.html?foo=13&bar=23', 'right URL')
    is_ok(req.query_params, 'foo=13&bar=23', 'right parameters')
    is_ok(req.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(req.headers.header('X-Trailer1'), 'test', 'right "X-Trailer1" value')
    is_ok(req.headers.header('X-Trailer2'), '123', 'right "X-Trailer2" value')
    is_ok(req.headers.content_length, '13', 'right "Content-Length" value')
    is_ok(req.content.asset.size, 13, 'right size')
    is_ok(req.content.asset.slurp(), b'abcdabcdefghi', 'right content')

with subtest('Parse HTTP 1.1 chunked request with trailing headers (different variation)'):
    req = Pyjo.Message.Request.new()
    req.parse(b'POST /foo/bar/baz.html?foo=13&bar=23 HTTP/1.1\x0d\x0a')
    req.parse(b'Content-Type: text/plain\x0d\x0aTransfer-Enc')
    req.parse(b'oding: chunked\x0d\x0a')
    req.parse(b'Trailer: X-Trailer\x0d\x0a\x0d\x0a')
    req.parse(b'4\x0d\x0a')
    req.parse(b'abcd\x0d\x0a')
    req.parse(b'9\x0d\x0a')
    req.parse(b'abcdefghi\x0d\x0a')
    req.parse(b'0\x0d\x0aX-Trailer: 777\x0d\x0a\x0d\x0aLEFTOVER')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar/baz.html?foo=13&bar=23', 'right URL')
    is_ok(req.query_params, 'foo=13&bar=23', 'right parameters')
    ok(req.headers.transfer_encoding is None, 'no "Transfer-Encoding" value')
    is_ok(req.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(req.headers.header('X-Trailer'), '777', 'right "X-Trailer" value')
    is_ok(req.headers.content_length, '13', 'right "Content-Length" value')
    is_ok(req.content.asset.size, 13, 'right size')
    is_ok(req.content.asset.slurp(), b'abcdabcdefghi', 'right content')

with subtest('Parse HTTP 1.1 chunked request with trailing headers (different variation)'):
    req = Pyjo.Message.Request.new()
    req.parse(b'POST /foo/bar/baz.html?foo=13&bar=23 HTTP/1.1\x0d\x0a')
    req.parse(b'Content-Type: text/plain\x0d\x0a')
    req.parse(b'Transfer-Encoding: chunked\x0d\x0a')
    req.parse(b'Trailer: X-Trailer1; X-Trailer2\x0d\x0a\x0d\x0a')
    req.parse(b'4\x0d\x0a')
    req.parse(b'abcd\x0d\x0a')
    req.parse(b'9\x0d\x0a')
    req.parse(b'abcdefghi\x0d\x0a')
    req.parse(b'0\x0d\x0aX-Trailer1: test\x0d\x0aX-Trailer2: 123\x0d\x0a\x0d\x0a')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar/baz.html?foo=13&bar=23', 'right URL')
    is_ok(req.query_params, 'foo=13&bar=23', 'right parameters')
    is_ok(req.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(req.headers.header('X-Trailer1'), 'test', 'right "X-Trailer1" value')
    is_ok(req.headers.header('X-Trailer2'), '123', 'right "X-Trailer2" value')
    is_ok(req.headers.content_length, '13', 'right "Content-Length" value')
    is_ok(req.content.asset.size, 13, 'right size')
    is_ok(req.content.asset.slurp(), b'abcdabcdefghi', 'right content')

with subtest('Parse HTTP 1.1 chunked request with trailing headers (no Trailer header)'):
    req = Pyjo.Message.Request.new()
    req.parse(b'POST /foo/bar/baz.html?foo=13&bar=23 HTTP/1.1\x0d\x0a')
    req.parse(b'Content-Type: text/plain\x0d\x0a')
    req.parse(b'Transfer-Encoding: chunked\x0d\x0a\x0d\x0a')
    req.parse(b'4\x0d\x0a')
    req.parse(b'abcd\x0d\x0a')
    req.parse(b'9\x0d\x0a')
    req.parse(b'abcdefghi\x0d\x0a')
    req.parse(b'0\x0d\x0aX-Trailer1: test\x0d\x0aX-Trailer2: 123\x0d\x0a\x0d\x0a')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar/baz.html?foo=13&bar=23', 'right URL')
    is_ok(req.query_params, 'foo=13&bar=23', 'right parameters')
    is_ok(req.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(req.headers.header('X-Trailer1'), 'test', 'right "X-Trailer1" value')
    is_ok(req.headers.header('X-Trailer2'), '123', 'right "X-Trailer2" value')
    is_ok(req.headers.content_length, '13', 'right "Content-Length" value')
    is_ok(req.content.asset.size, 13, 'right size')
    is_ok(req.content.asset.slurp(), b'abcdabcdefghi', 'right content')

with subtest('Parse HTTP 1.1 multipart request'):
    req = Pyjo.Message.Request.new()
    is_ok(req.content.progress, 0, 'right progress')
    req.parse(b'GET /foo/bar/baz.html?foo13 HTTP/1.1\x0d\x0a')
    is_ok(req.content.progress, 0, 'right progress')
    req.parse(b'Content-Length: 416\x0d\x0a')
    req.parse(b'Content-Type: multipart/form-data; bo')
    is_ok(req.content.progress, 0, 'right progress')
    req.parse(b'undary=----------0xKhTmLbOuNdArY\x0d\x0a\x0d\x0a')
    is_ok(req.content.progress, 0, 'right progress')
    req.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    is_ok(req.content.progress, 31, 'right progress')
    req.parse(b'Content-Disposition: form-data; name="text1"\x0d\x0a')
    req.parse(b'\x0d\x0ahallo welt test123\n')
    req.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    req.parse(b'Content-Disposition: form-data; name="text2"\x0d\x0a')
    req.parse(b'\x0d\x0a\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    req.parse(b'Content-Disposition: form-data;name="upload";file')
    req.parse(b'name="hello.pl"\x0d\x0a')
    req.parse(b'Content-Type: application/octet-stream\x0d\x0a\x0d\x0a')
    req.parse(b'#!/usr/bin/perl\n\n')
    req.parse(b'use strict;\n')
    req.parse(b'use warnings;\n\n')
    req.parse(b'print "Hello World :)\\n"\n')
    req.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY--')
    is_ok(req.content.progress, 416, 'right progress')
    ok(req.is_finished, 'request is finished')
    ok(req.content.is_multipart, 'multipart content')
    is_ok(req.body, b'', 'no content')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar/baz.html?foo13', 'right URL')
    is_ok(req.query_params, 'foo13', 'right parameters')
    is_ok(
        req.headers.content_type,
        'multipart/form-data; boundary=----------0xKhTmLbOuNdArY',
        'right "Content-Type" value',
    )
    is_ok(req.headers.content_length, '416', 'right "Content-Length" value')
    ok(not req.content.parts[0].is_multipart, 'no multipart content')
    ok(not req.content.parts[1].is_multipart, 'no multipart content')
    ok(not req.content.parts[2].is_multipart, 'no multipart content')
    ok(not req.content.parts[0].asset.is_file, 'stored in memory')
    is_ok(req.content.parts[0].asset.slurp(), b'hallo welt test123\n', 'right content')
    is_ok(req.body_params.to_dict()['text1'], 'hallo welt test123\n', 'right value')
    is_ok(req.body_params.to_dict()['text2'], '', 'right value')
    is_ok(req.upload('upload').filename, 'hello.pl', 'right filename')
    ok(not req.upload('upload').asset.is_file, 'stored in memory')
    is_ok(req.upload('upload').asset.size, 69, 'right size')
    dir = tempdir()
    file = dir.child(f'PYJO_TMP.{int(time.time())}.txt')
    is_ok(req.upload('upload').move_to(file).filename, 'hello.pl', 'right filename')
    ok(os.unlink(file) is None, 'unlinked file')
    is_ok(req.content.boundary, '----------0xKhTmLbOuNdArY', 'right boundary')

with subtest('Parse HTTP 1.1 multipart request (too big for memory)'):
    req = Pyjo.Message.Request.new()

    @req.content.on('body')
    def body(single):
        @single.on('upgrade')
        def upgrade(single, multi):
            @multi.on('part')
            def part(multi, part):
                part.asset.max_memory_size = 5

    req.parse(b'GET /foo/bar/baz.html?foo13 HTTP/1.1\x0d\x0a')
    req.parse(b'Content-Length: 562\x0d\x0a')
    req.parse(b'Content-Type: multipart/form-data; bo')
    req.parse(b'undary=----------0xKhTmLbOuNdArY\x0d\x0a\x0d\x0a')
    req.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    req.parse(b'Content-Disposition: form-data; name="text1"\x0d\x0a')
    req.parse(b'\x0d\x0ahallo welt test123\n')
    req.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    req.parse(b'Content-Disposition: form-data; name="text2"\x0d\x0a')
    req.parse(b'\x0d\x0a\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    req.parse(b'Content-Disposition: form-data; name="upload"; file')
    req.parse(b'name="hello.pl"\x0d\x0a')
    req.parse(b'Content-Type: application/octet-stream\x0d\x0a\x0d\x0a')
    req.parse(b'#!/usr/bin/perl\n\n')
    req.parse(b'use strict;\n')
    req.parse(b'use warnings;\n\n')
    req.parse(b'print "Hello World :)\\n"\n')
    req.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    req.parse(b'Content-Disposition: form-data; name="upload"; filename')
    req.parse(b'="bye.txt"\x0d\x0a')
    req.parse(b'Content-Type: application/octet-stream\x0d\x0a\x0d\x0a')
    req.parse(b'Bye!\x0d\x0a------------0xKhTmLbOuNdArY--')
    ok(req.is_finished, 'request is finished')
    ok(req.content.is_multipart, 'multipart content')
    is_ok(req.body, b'', 'no content')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar/baz.html?foo13', 'right URL')
    is_ok(req.query_params, 'foo13', 'right parameters')
    is_ok(
        req.headers.content_type,
        'multipart/form-data; boundary=----------0xKhTmLbOuNdArY',
        'right "Content-Type" value',
    )
    is_ok(req.headers.content_length, '562', 'right "Content-Length" value')
    ok(not req.content.parts[0].is_multipart, 'no multipart content')
    ok(not req.content.parts[1].is_multipart, 'no multipart content')
    ok(not req.content.parts[2].is_multipart, 'no multipart content')
    ok(req.content.parts[0].asset.is_file, 'stored in file')
    is_ok(req.content.parts[0].asset.slurp(), b'hallo welt test123\n', 'right content')
    is_ok(req.body_params.to_dict()['text1'], 'hallo welt test123\n', 'right value')
    is_ok(req.body_params.to_dict()['text2'], '', 'right value')
    is_ok(req.upload('upload').filename, 'bye.txt', 'right filename')
    is_ok(req.upload('upload').asset.size, 4, 'right size')
    is_ok(req.every_upload('upload')[0].filename, 'hello.pl', 'right filename')
    ok(req.every_upload('upload')[0].asset.is_file, 'stored in file')
    is_ok(req.every_upload('upload')[0].asset.size, 69, 'right size')
    is_ok(req.every_upload('upload')[1].filename, 'bye.txt', 'right filename')
    ok(not req.every_upload('upload')[1].asset.is_file, 'stored in memory')
    is_ok(req.every_upload('upload')[1].asset.size, 4, 'right size')

with subtest('Parse HTTP 1.1 multipart request (with callbacks and stream)'):
    req = Pyjo.Message.Request.new()
    stream = b''

    @req.content.on('body')
    def body(single):
        @single.on('upgrade')
        def upgrade(single, multi):
            @multi.on('part')
            def part(multi, part):
                @part.on('body')
                def body(part):
                    if not re.search(r'hello\.pl', part.headers.content_disposition):
                        return

                    @part.on('read')
                    def read(part, chunk):
                        global stream
                        stream += chunk

    req.parse(b'GET /foo/bar/baz.html?foo13 HTTP/1.1\x0d\x0a')
    req.parse(b'Content-Length: 418\x0d\x0a')
    req.parse(b'Content-Type: multipart/form-data; bo')
    req.parse(b'undary=----------0xKhTmLbOuNdArY\x0d\x0a\x0d\x0a')
    req.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    req.parse(b'Content-Disposition: form-data; name="text1"\x0d\x0a')
    req.parse(b'\x0d\x0ahallo welt test123\n')
    req.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    req.parse(b'Content-Disposition: form-data; name="text2"\x0d\x0a')
    req.parse(b'\x0d\x0a\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    req.parse(b'Content-Disposition: form-data; name="upload"; file')
    req.parse(b'name="hello.pl"\x0d\x0a')
    req.parse(b'Content-Type: application/octet-stream\x0d\x0a\x0d\x0a')
    is_ok(stream, b'', 'no content')
    req.parse(b'#!/usr/bin/perl\n\n')
    is_ok(stream, b'', 'no content')
    req.parse(b'use strict;\n')
    is_ok(stream, b'', 'no content')
    req.parse(b'use warnings;\n\n')
    is_ok(stream, b'#!/usr/bin/', 'right content')
    req.parse(b'print "Hello World :)\\n"\n')
    is_ok(stream, b'#!/usr/bin/perl\n\nuse strict;\nuse war', 'right content')
    req.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY--')
    ok(req.is_finished, 'request is finished')
    ok(req.content.is_multipart, 'multipart content')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar/baz.html?foo13', 'right URL')
    is_ok(req.query_params, 'foo13', 'right parameters')
    is_ok(
        req.headers.content_type,
        'multipart/form-data; boundary=----------0xKhTmLbOuNdArY',
        'right "Content-Type" value',
    )
    is_ok(req.headers.content_length, '418', 'right "Content-Length" value')
    ok(not req.content.parts[0].is_multipart, 'no multipart content')
    ok(not req.content.parts[1].is_multipart, 'no multipart content')
    ok(not req.content.parts[2].is_multipart, 'no multipart content')
    is_ok(req.content.parts[0].asset.slurp(), b'hallo welt test123\n', 'right content')
    is_ok(req.body_params.to_dict()['text1'], 'hallo welt test123\n', 'right value')
    is_ok(req.body_params.to_dict()['text2'], '', 'right value')
    is_ok(
        stream,
        b'#!/usr/bin/perl\n\n' + b'use strict;\n' + b'use warnings;\n\n' + b'print "Hello World :)\\n"\n',
        'right content',
    )

with subtest('Parse HTTP 1.1 multipart request (without upgrade)'):
    req = Pyjo.Message.Request.new()
    req.content.auto_upgrade = 0
    req.parse(b'GET /foo/bar/baz.html?foo13 HTTP/1.1\x0d\x0a')
    req.parse(b'Content-Length: 418\x0d\x0a')
    req.parse(b'Content-Type: multipart/form-data; bo')
    req.parse(b'undary=----------0xKhTmLbOuNdArY\x0d\x0a\x0d\x0a')
    req.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    req.parse(b'Content-Disposition: form-data; name="text1"\x0d\x0a')
    req.parse(b'\x0d\x0ahallo welt test123\n')
    req.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    req.parse(b'Content-Disposition: form-data; name="text2"\x0d\x0a')
    req.parse(b'\x0d\x0a\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    req.parse(b'Content-Disposition: form-data; name="upload"; file')
    req.parse(b'name="hello.pl"\x0d\x0a')
    req.parse(b'Content-Type: application/octet-stream\x0d\x0a\x0d\x0a')
    req.parse(b'#!/usr/bin/perl\n\n')
    req.parse(b'use strict;\n')
    req.parse(b'use warnings;\n\n')
    req.parse(b'print "Hello World :)\\n"\n')
    req.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY--')
    ok(req.is_finished, 'request is finished')
    ok(not req.content.is_multipart, 'no multipart content')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar/baz.html?foo13', 'right URL')
    is_ok(req.query_params, 'foo13', 'right parameters')
    is_ok(
        req.headers.content_type,
        'multipart/form-data; boundary=----------0xKhTmLbOuNdArY',
        'right "Content-Type" value',
    )
    is_ok(req.headers.content_length, '418', 'right "Content-Length" value')
    ok(not req.content.is_multipart, 'no multipart content')
    like_ok(req.content.asset.slurp(), rb'------------0xKhTmLbOuNdArY--$', 'right content')

with subtest('Parse HTTP 1.1 multipart request with "0" filename'):
    req = Pyjo.Message.Request.new()
    req.parse(b'GET /foo/bar/baz.html?foo13 HTTP/1.1\x0d\x0a')
    req.parse(b'Content-Length: 410\x0d\x0a')
    req.parse(b'Content-Type: multipart/form-data; bo')
    req.parse(b'undary=----------0xKhTmLbOuNdArY\x0d\x0a\x0d\x0a')
    req.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    req.parse(b'Content-Disposition: form-data; name="text1"\x0d\x0a')
    req.parse(b'\x0d\x0ahallo welt test123\n')
    req.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    req.parse(b'Content-Disposition: form-data; name="text2"\x0d\x0a')
    req.parse(b'\x0d\x0a\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    req.parse(b'Content-Disposition: form-data; name="upload"; file')
    req.parse(b'name="0"\x0d\x0a')
    req.parse(b'Content-Type: application/octet-stream\x0d\x0a\x0d\x0a')
    req.parse(b'#!/usr/bin/perl\n\n')
    req.parse(b'use strict;\n')
    req.parse(b'use warnings;\n\n')
    req.parse(b'print "Hello World :)\\n"\n')
    req.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY--')
    ok(req.is_finished, 'request is finished')
    ok(req.content.is_multipart, 'no multipart content')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar/baz.html?foo13', 'right URL')
    is_ok(req.query_params, 'foo13', 'right parameters')
    is_ok(
        req.headers.content_type,
        'multipart/form-data; boundary=----------0xKhTmLbOuNdArY',
        'right "Content-Type" value',
    )
    is_ok(req.headers.content_length, '410', 'right "Content-Length" value')
    ok(not req.content.parts[0].is_multipart, 'no multipart content')
    ok(not req.content.parts[1].is_multipart, 'no multipart content')
    ok(not req.content.parts[2].is_multipart, 'no multipart content')
    is_ok(req.content.parts[0].asset.slurp(), b'hallo welt test123\n', 'right content')
    is_ok(req.body_params.to_dict()['text1'], 'hallo welt test123\n', 'right value')
    is_ok(req.body_params.to_dict()['text2'], '', 'right value')
    is_ok(req.body_params.to_dict().get('upload'), None, 'not a body parameter')
    is_ok(req.upload('upload').filename, '0', 'right filename')
    ok(not req.upload('upload').asset.is_file, 'stored in memory')
    is_ok(req.upload('upload').asset.size, 69, 'right size')

with subtest('Parse HTTP 1.1 multipart request with missing name'):
    req = Pyjo.Message.Request.new()
    is_ok(req.content.progress, 0, 'right progress')
    req.parse(b'GET /foo/bar.html HTTP/1.1\x0d\x0a')
    is_ok(req.content.progress, 0, 'right progress')
    req.parse(b'Content-Length: 115\x0d\x0a')
    req.parse(b'Content-Type: multipart/form-data; bo')
    is_ok(req.content.progress, 0, 'right progress')
    req.parse(b'undary=----------0xKhTmLbOuNdArY\x0d\x0a\x0d\x0a')
    is_ok(req.content.progress, 0, 'right progress')
    req.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    is_ok(req.content.progress, 31, 'right progress')
    req.parse(b'Content-Disposition: form-data\x0d\x0a')
    req.parse(b'\x0d\x0afield with no name\n')
    req.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY--')
    is_ok(req.content.progress, 115, 'right progress')
    ok(req.is_finished, 'request is finished')
    ok(req.content.is_multipart, 'multipart content')
    is_ok(req.body, b'', 'no content')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar.html', 'right URL')
    is_ok(
        req.headers.content_type,
        'multipart/form-data; boundary=----------0xKhTmLbOuNdArY',
        'right "Content-Type" value',
    )
    is_ok(req.headers.content_length, '115', 'right "Content-Length" value')
    is_deeply_ok(req.params.pairs, [], 'no multipart parameter')
    is_ok(req.content.boundary, '----------0xKhTmLbOuNdArY', 'right boundary')

with subtest('Parse full HTTP 1.1 proxy request with basic authentication'):
    req = Pyjo.Message.Request.new()
    req.parse(b'GET http://127.0.0.1/foo/bar#baz HTTP/1.1\x0d\x0a')
    req.parse(b'Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==\x0d\x0a')
    req.parse(b'Host: 127.0.0.1\x0d\x0a')
    req.parse(b'Proxy-Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==\x0d\x0a')
    req.parse(b'Content-Length: 13\x0d\x0a\x0d\x0a')
    req.parse(b'Hello World!\n')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url.base, 'http://127.0.0.1', 'right base URL')
    is_ok(req.url.base.userinfo, 'Aladdin:open sesame', 'right base userinfo')
    is_ok(req.url, 'http://127.0.0.1/foo/bar', 'right URL')
    is_ok(req.proxy.userinfo, 'Aladdin:open sesame', 'right proxy userinfo')

with subtest('Parse full HTTP 1.1 proxy connect request with basic authentication'):
    req = Pyjo.Message.Request.new()
    req.parse(b'CONNECT 127.0.0.1:3000 HTTP/1.1\x0d\x0a')
    req.parse(b'Host: 127.0.0.1:3000\x0d\x0a')
    req.parse(b'Proxy-Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==\x0d\x0a')
    req.parse(b'Content-Length: 0\x0d\x0a\x0d\x0a')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'CONNECT', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '//127.0.0.1:3000', 'right URL')
    is_ok(req.url.host, '127.0.0.1', 'right host')
    is_ok(req.url.port, 3000, 'right port')
    is_ok(req.proxy.userinfo, 'Aladdin:open sesame', 'right proxy userinfo')

with subtest('Build minimal HTTP 1.1 request'):
    req = Pyjo.Message.Request.new()
    req.method = 'GET'
    req.url.parse('http://127.0.0.1/')
    req = Pyjo.Message.Request.new().parse(req.to_bytes())
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/', 'right URL')
    is_ok(req.url.to_abs(), 'http://127.0.0.1/', 'right absolute URL')
    is_ok(req.headers.host, '127.0.0.1', 'right "Host" value')

with subtest('Build HTTP 1.1 start-line and header'):
    req = Pyjo.Message.Request.new()
    req.method = 'GET'
    req.url.parse('http://127.0.0.1/foo/bar')
    req.headers.expect = '100-continue'
    req = Pyjo.Message.Request.new().parse(req.to_bytes())
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar', 'right URL')
    is_ok(req.url.to_abs(), 'http://127.0.0.1/foo/bar', 'right absolute URL')
    is_ok(req.headers.expect, '100-continue', 'right "Expect" value')
    is_ok(req.headers.host, '127.0.0.1', 'right "Host" value')

with subtest('Build HTTP 1.1 start-line and header (with clone)'):
    req = Pyjo.Message.Request.new()
    req.method = 'GET'
    req.url.parse('http://127.0.0.1/foo/bar')
    req.headers.expect = '100-continue'
    clone = req.clone()
    req = Pyjo.Message.Request.new().parse(req.to_bytes())
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar', 'right URL')
    is_ok(req.url.to_abs(), 'http://127.0.0.1/foo/bar', 'right absolute URL')
    is_ok(req.headers.expect, '100-continue', 'right "Expect" value')
    is_ok(req.headers.host, '127.0.0.1', 'right "Host" value')
    clone = Pyjo.Message.Request.new().parse(clone.to_bytes())
    ok(clone.is_finished, 'request is finished')
    is_ok(clone.method, 'GET', 'right method')
    is_ok(clone.version, '1.1', 'right version')
    is_ok(clone.url, '/foo/bar', 'right URL')
    is_ok(clone.url.to_abs(), 'http://127.0.0.1/foo/bar', 'right absolute URL')
    is_ok(clone.headers.expect, '100-continue', 'right "Expect" value')
    is_ok(clone.headers.host, '127.0.0.1', 'right "Host" value')

with subtest('Build HTTP 1.1 start-line and header (with clone and changes)'):
    req = Pyjo.Message.Request.new()
    req.method = 'GET'
    req.url.parse('http://127.0.0.1/foo/bar')
    req.headers.expect = '100-continue'
    clone = req.clone()
    clone.method = 'POST'
    clone.headers.expect = 'nothing'
    clone.version = '1.2'
    clone.url.path.parts.append('baz')
    req = Pyjo.Message.Request.new().parse(req.to_bytes())
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar', 'right URL')
    is_ok(req.url.to_abs(), 'http://127.0.0.1/foo/bar', 'right absolute URL')
    is_ok(req.headers.expect, '100-continue', 'right "Expect" value')
    is_ok(req.headers.host, '127.0.0.1', 'right "Host" value')
    clone = Pyjo.Message.Request.new().parse(clone.to_bytes())
    ok(clone.is_finished, 'request is finished')
    is_ok(clone.method, 'POST', 'right method')
    is_ok(clone.version, '1.2', 'right version')
    is_ok(clone.url, '/foo/bar/baz', 'right URL')
    is_ok(clone.url.to_abs(), 'http://127.0.0.1/foo/bar/baz', 'right absolute URL')
    is_ok(clone.headers.expect, 'nothing', 'right "Expect" value')
    is_ok(clone.headers.host, '127.0.0.1', 'right "Host" value')

with subtest('Build full HTTP 1.1 request'):
    req = Pyjo.Message.Request.new()
    finished = None

    @req.on('finish')
    def finish(req, *args):
        global finished
        finished = req.is_finished

    req.method = 'get'
    req.url.parse('http://127.0.0.1/foo/bar')
    req.headers.expect = '100-continue'
    req.body = b'Hello World!\n'
    req = Pyjo.Message.Request.new().parse(req.to_bytes())
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar', 'right URL')
    is_ok(req.url.to_abs(), 'http://127.0.0.1/foo/bar', 'right absolute URL')
    is_ok(req.headers.expect, '100-continue', 'right "Expect" value')
    is_ok(req.headers.host, '127.0.0.1', 'right "Host" value')
    is_ok(req.headers.content_length, '13', 'right "Content-Length" value')
    is_ok(req.body, b'Hello World!\n', 'right content')
    ok(finished, 'finish event has been emitted')
    ok(req.is_finished, 'request is finished')

with subtest('Build HTTP 1.1 request parts with progress'):
    req = Pyjo.Message.Request.new()
    state = None
    finished = None
    progress = 0

    @req.on('finish')
    def finish(req, *args):
        global finished
        finished = req.is_finished

    @req.on('progress')
    def progress_cb(req, part, offset):
        global state, progress
        state = part
        progress += offset

    req.method = 'get'
    req.url.parse('http://127.0.0.1/foo/bar')
    req.headers.expect = '100-continue'
    req.body = b'Hello World!\n'
    ok(not state, 'no state')
    ok(not progress, 'no progress')
    ok(not finished, 'not finished')
    ok(req.build_start_line(), 'built start-line')
    is_ok(state, 'start_line', 'made progress on start_line')
    ok(progress, 'made progress')
    progress = 0
    ok(not finished, 'not finished')
    ok(req.build_headers(), 'built headers')
    is_ok(state, 'headers', 'made progress on headers')
    ok(progress, 'made progress')
    progress = 0
    ok(not finished, 'not finished')
    ok(req.build_body(), 'built body')
    is_ok(state, 'body', 'made progress on headers')
    ok(progress, 'made progress')
    ok(finished, 'finished')

with subtest('Build full HTTP 1.1 request (with clone)'):
    req = Pyjo.Message.Request.new()
    finished = None

    @req.on('finish')
    def finish(req, *args):
        global finished
        finished = req.is_finished

    req.method = 'get'
    req.url.parse('http://127.0.0.1/foo/bar')
    req.headers.expect = '100-continue'
    req.body = b'Hello World!\n'
    clone = req.clone()
    req = Pyjo.Message.Request.new().parse(req.to_bytes())
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar', 'right URL')
    is_ok(req.url.to_abs(), 'http://127.0.0.1/foo/bar', 'right absolute URL')
    is_ok(req.headers.expect, '100-continue', 'right "Expect" value')
    is_ok(req.headers.host, '127.0.0.1', 'right "Host" value')
    is_ok(req.headers.content_length, '13', 'right "Content-Length" value')
    is_ok(req.body, b'Hello World!\n', 'right content')
    ok(finished, 'finish event has been emitted')
    ok(req.is_finished, 'request is finished')
    finished = None
    clone = Pyjo.Message.Request.new().parse(clone.to_bytes())
    ok(clone.is_finished, 'request is finished')
    is_ok(clone.method, 'GET', 'right method')
    is_ok(clone.version, '1.1', 'right version')
    is_ok(clone.url, '/foo/bar', 'right URL')
    is_ok(clone.url.to_abs(), 'http://127.0.0.1/foo/bar', 'right absolute URL')
    is_ok(clone.headers.expect, '100-continue', 'right "Expect" value')
    is_ok(clone.headers.host, '127.0.0.1', 'right "Host" value')
    is_ok(clone.headers.content_length, '13', 'right "Content-Length" value')
    is_ok(clone.body, b'Hello World!\n', 'right content')
    ok(not finished, 'finish event has been emitted')
    ok(clone.is_finished, 'request is finished')

with subtest('Build full HTTP 1.1 request (roundtrip)'):
    req = Pyjo.Message.Request.new()
    req.method = 'GET'
    req.url.parse('http://127.0.0.1/foo/bar')
    req.headers.expect = '100-continue'
    req.body = b'Hello World!\n'
    req = Pyjo.Message.Request.new().parse(req.to_bytes())
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar', 'right URL')
    is_ok(req.url.to_abs(), 'http://127.0.0.1/foo/bar', 'right absolute URL')
    is_ok(req.headers.expect, '100-continue', 'right "Expect" value')
    is_ok(req.headers.host, '127.0.0.1', 'right "Host" value')
    is_ok(req.headers.content_length, '13', 'right "Content-Length" value')
    is_ok(req.body, b'Hello World!\n', 'right content')
    req2 = Pyjo.Message.Request.new().parse(req.to_bytes())
    is_ok(req.content.leftovers(), b'', 'no leftovers')
    is_ok(req.error, None, 'no error')
    is_ok(req2.content.leftovers(), b'', 'no leftovers')
    is_ok(req2.error, None, 'no error')
    ok(req2.is_finished, 'request is finished')
    is_ok(req2.method, 'GET', 'right method')
    is_ok(req2.version, '1.1', 'right version')
    is_ok(req2.url, '/foo/bar', 'right URL')
    is_ok(req2.url.to_abs(), 'http://127.0.0.1/foo/bar', 'right absolute URL')
    is_ok(req2.headers.expect, '100-continue', 'right "Expect" value')
    is_ok(req2.headers.host, '127.0.0.1', 'right "Host" value')
    is_ok(req.headers.content_length, '13', 'right "Content-Length" value')
    is_ok(req.body, b'Hello World!\n', 'right content')

with subtest('Build HTTP 1.1 request body'):
    req = Pyjo.Message.Request.new()
    finished = None

    @req.on('finish')
    def finish(req, *args):
        global finished
        finished = req.is_finished

    req.method = 'get'
    req.url.parse('http://127.0.0.1/foo/bar')
    req.headers.expect = '100-continue'
    req.body = b'Hello World!\n'
    i = 0
    while chunk := req.get_body_chunk(i):
        i += len(chunk)
    ok(finished, 'finish event has been emitted')
    ok(req.is_finished, 'request is finished')

with subtest('Build HTTP 1.1 POST request without body'):
    req = Pyjo.Message.Request.new()
    req.method = 'POST'
    req.url.parse('http://127.0.0.1/foo/bar')
    req = Pyjo.Message.Request.new().parse(req.to_bytes())
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar', 'right URL')
    is_ok(req.url.to_abs(), 'http://127.0.0.1/foo/bar', 'right absolute URL')
    is_ok(req.headers.host, '127.0.0.1', 'right "Host" value')
    is_ok(req.headers.content_length, '0', 'right "Content-Length" value')
    is_ok(req.body, b'', 'no content')
    ok(req.is_finished, 'request is finished')

with subtest('Build WebSocket handshake request'):
    req = Pyjo.Message.Request.new()
    finished = None

    @req.on('finish')
    def finish(req, *args):
        global finished
        finished = req.is_finished

    req.method = 'GET'
    req.url.parse('http://example.com/demo')
    req.headers.host = 'example.com'
    req.headers.connection = 'Upgrade'
    req.headers.sec_websocket_accept = 'abcdef='
    req.headers.sec_websocket_protocol = 'sample'
    req.headers.upgrade = 'websocket'
    req = Pyjo.Message.Request.new().parse(req.to_bytes())
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/demo', 'right URL')
    is_ok(req.url.to_abs(), 'http://example.com/demo', 'right absolute URL')
    is_ok(req.headers.connection, 'Upgrade', 'right "Connection" value')
    is_ok(req.headers.upgrade, 'websocket', 'right "Upgrade" value')
    is_ok(req.headers.host, 'example.com', 'right "Host" value')
    is_ok(req.headers.content_length, None, 'no "Content-Length" value')
    is_ok(req.headers.sec_websocket_accept, 'abcdef=', 'right "Sec-WebSocket-Key" value')
    is_ok(req.headers.sec_websocket_protocol, 'sample', 'right "Sec-WebSocket-Protocol" value')
    is_ok(req.body, b'', 'no content')
    ok(finished, 'finish event has been emitted')
    ok(req.is_finished, 'request is finished')

with subtest('Build WebSocket handshake request (with clone)'):
    req = Pyjo.Message.Request.new()
    req.method = 'GET'
    req.url.parse('http://example.com/demo')
    req.headers.host = 'example.com'
    req.headers.connection = 'Upgrade'
    req.headers.sec_websocket_accept = 'abcdef='
    req.headers.sec_websocket_protocol = 'sample'
    req.headers.upgrade = 'websocket'
    clone = req.clone()
    req = Pyjo.Message.Request.new().parse(req.to_bytes())
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/demo', 'right URL')
    is_ok(req.url.to_abs(), 'http://example.com/demo', 'right absolute URL')
    is_ok(req.headers.connection, 'Upgrade', 'right "Connection" value')
    is_ok(req.headers.upgrade, 'websocket', 'right "Upgrade" value')
    is_ok(req.headers.host, 'example.com', 'right "Host" value')
    is_ok(req.headers.content_length, None, 'no "Content-Length" value')
    is_ok(req.headers.sec_websocket_accept, 'abcdef=', 'right "Sec-WebSocket-Key" value')
    is_ok(req.headers.sec_websocket_protocol, 'sample', 'right "Sec-WebSocket-Protocol" value')
    is_ok(req.body, b'', 'no content')
    ok(req.is_finished, 'request is finished')
    clone = Pyjo.Message.Request.new().parse(clone.to_bytes())
    ok(clone.is_finished, 'request is finished')
    is_ok(clone.method, 'GET', 'right method')
    is_ok(clone.version, '1.1', 'right version')
    is_ok(clone.url, '/demo', 'right URL')
    is_ok(clone.url.to_abs(), 'http://example.com/demo', 'right absolute URL')
    is_ok(clone.headers.connection, 'Upgrade', 'right "Connection" value')
    is_ok(clone.headers.upgrade, 'websocket', 'right "Upgrade" value')
    is_ok(clone.headers.host, 'example.com', 'right "Host" value')
    is_ok(req.headers.content_length, None, 'no "Content-Length" value')
    is_ok(clone.headers.sec_websocket_accept, 'abcdef=', 'right "Sec-WebSocket-Key" value')
    is_ok(clone.headers.sec_websocket_protocol, 'sample', 'right "Sec-WebSocket-Protocol" value')
    is_ok(clone.body, b'', 'no content')
    ok(clone.is_finished, 'request is finished')

with subtest('Build WebSocket handshake proxy request'):
    req = Pyjo.Message.Request.new()
    finished = None

    @req.on('finish')
    def finish(req, *args):
        global finished
        finished = req.is_finished

    req.method = 'GET'
    req.url.parse('http://example.com/demo')
    req.headers.host = 'example.com'
    req.headers.connection = 'Upgrade'
    req.headers.sec_websocket_accept = 'abcdef='
    req.headers.sec_websocket_protocol = 'sample'
    req.headers.upgrade = 'websocket'
    req.proxy = Pyjo.URL.new('http://127.0.0.2:8080')
    req = Pyjo.Message.Request.new().parse(req.to_bytes())
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/demo', 'right URL')
    is_ok(req.url.to_abs(), 'http://example.com/demo', 'right absolute URL')
    is_ok(req.headers.connection, 'Upgrade', 'right "Connection" value')
    is_ok(req.headers.upgrade, 'websocket', 'right "Upgrade" value')
    is_ok(req.headers.host, 'example.com', 'right "Host" value')
    is_ok(req.headers.content_length, None, 'no "Content-Length" value')
    is_ok(req.headers.sec_websocket_accept, 'abcdef=', 'right "Sec-WebSocket-Key" value')
    is_ok(req.headers.sec_websocket_protocol, 'sample', 'right "Sec-WebSocket-Protocol" value')
    is_ok(req.body, b'', 'no content')
    ok(finished, 'finish event has been emitted')
    ok(req.is_finished, 'request is finished')

with subtest('Build full HTTP 1.1 proxy request'):
    req = Pyjo.Message.Request.new()
    req.method = 'GET'
    req.url.parse('http://127.0.0.1/foo/bar')
    req.headers.expect = '100-continue'
    req.body = b'Hello World!\n'
    req.proxy = Pyjo.URL.new('http://127.0.0.2:8080')
    req = Pyjo.Message.Request.new().parse(req.to_bytes())
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, 'http://127.0.0.1/foo/bar', 'right URL')
    is_ok(req.url.to_abs(), 'http://127.0.0.1/foo/bar', 'right absolute URL')
    is_ok(req.headers.expect, '100-continue', 'right "Expect" value')
    is_ok(req.headers.host, '127.0.0.1', 'right "Host" value')
    is_ok(req.headers.content_length, '13', 'right "Content-Length" value')
    is_ok(req.body, b'Hello World!\n', 'right content')

with subtest('Build full HTTP 1.1 proxy request (proxy disabled)'):
    req = Pyjo.Message.Request.new()
    req.method = 'GET'
    req.url.parse('http://127.0.0.1/foo/bar')
    req.body = b'Hello World!\n'
    req.set(via_proxy=False).proxy = Pyjo.URL.new('http://127.0.0.2:8080')
    req = Pyjo.Message.Request.new().parse(req.to_bytes())
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar', 'right URL')
    is_ok(req.url.to_abs(), 'http://127.0.0.1/foo/bar', 'right absolute URL')
    is_ok(req.headers.host, '127.0.0.1', 'right "Host" value')
    is_ok(req.headers.content_length, '13', 'right "Content-Length" value')
    is_ok(req.body, b'Hello World!\n', 'right content')

with subtest('Build full HTTP 1.1 proxy request (HTTPS)'):
    req = Pyjo.Message.Request.new()
    req.method = 'GET'
    req.url.parse('https://127.0.0.1/foo/bar')
    req.headers.expect = '100-continue'
    req.body = b'Hello World!\n'
    req.proxy = Pyjo.URL.new('http://127.0.0.2:8080')
    req = Pyjo.Message.Request.new().parse(req.to_bytes())
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar', 'right URL')
    is_ok(req.url.to_abs(), 'http://127.0.0.1/foo/bar', 'right absolute URL')
    is_ok(req.headers.expect, '100-continue', 'right "Expect" value')
    is_ok(req.headers.host, '127.0.0.1', 'right "Host" value')
    is_ok(req.headers.content_length, '13', 'right "Content-Length" value')
    is_ok(req.body, b'Hello World!\n', 'right content')

with subtest('Build full HTTP 1.1 proxy request with basic authentication'):
    req = Pyjo.Message.Request.new()
    req.method = 'GET'
    req.url.parse('http://Aladdin:open%20sesame@127.0.0.1/foo/bar')
    req.headers.expect = '100-continue'
    req.body = b'Hello World!\n'
    req.proxy = Pyjo.URL.new('http://Aladdin:open%20sesame@127.0.0.2:8080')
    req = Pyjo.Message.Request.new().parse(req.to_bytes())
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, 'http://127.0.0.1/foo/bar', 'right URL')
    is_ok(req.url.to_abs(), 'http://127.0.0.1/foo/bar', 'right absolute URL')
    is_ok(req.proxy.userinfo, 'Aladdin:open sesame', 'right proxy userinfo')
    is_ok(req.headers.authorization, 'Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==', 'right "Authorization" value')
    is_ok(req.headers.expect, '100-continue', 'right "Expect" value')
    is_ok(req.headers.host, '127.0.0.1', 'right "Host" value')
    is_ok(req.headers.proxy_authorization, 'Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==', 'right "Proxy-Authorization" value')
    is_ok(req.headers.content_length, '13', 'right "Content-Length" value')
    is_ok(req.body, b'Hello World!\n', 'right content')

with subtest('Build full HTTP 1.1 proxy request with basic authentication (and clone)'):
    req = Pyjo.Message.Request.new()
    req.method = 'GET'
    req.url.parse('http://Aladdin:open%20sesame@127.0.0.1/foo/bar')
    req.headers.expect = '100-continue'
    req.body = b'Hello World!\n'
    req.proxy = Pyjo.URL.new('http://Aladdin:open%20sesame@127.0.0.2:8080')
    clone = req.clone()
    req = Pyjo.Message.Request.new().parse(req.to_bytes())
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, 'http://127.0.0.1/foo/bar', 'right URL')
    is_ok(req.url.to_abs(), 'http://127.0.0.1/foo/bar', 'right absolute URL')
    is_ok(req.proxy.userinfo, 'Aladdin:open sesame', 'right proxy userinfo')
    is_ok(req.headers.authorization, 'Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==', 'right "Authorization" value')
    is_ok(req.headers.expect, '100-continue', 'right "Expect" value')
    is_ok(req.headers.host, '127.0.0.1', 'right "Host" value')
    is_ok(req.headers.proxy_authorization, 'Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==', 'right "Proxy-Authorization" value')
    is_ok(req.headers.content_length, '13', 'right "Content-Length" value')
    is_ok(req.body, b'Hello World!\n', 'right content')
    clone = Pyjo.Message.Request.new().parse(clone.to_bytes())
    ok(clone.is_finished, 'request is finished')
    is_ok(clone.method, 'GET', 'right method')
    is_ok(clone.version, '1.1', 'right version')
    is_ok(clone.url, 'http://127.0.0.1/foo/bar', 'right URL')
    is_ok(clone.url.to_abs(), 'http://127.0.0.1/foo/bar', 'right absolute URL')
    is_ok(clone.proxy.userinfo, 'Aladdin:open sesame', 'right proxy userinfo')
    is_ok(clone.headers.authorization, 'Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==', 'right "Authorization" value')
    is_ok(clone.headers.expect, '100-continue', 'right "Expect" value')
    is_ok(clone.headers.host, '127.0.0.1', 'right "Host" value')
    is_ok(clone.headers.proxy_authorization, 'Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==', 'right "Proxy-Authorization" value')
    is_ok(clone.headers.content_length, '13', 'right "Content-Length" value')
    is_ok(clone.body, b'Hello World!\n', 'right content')

with subtest('Build full HTTP 1.1 proxy connect request with basic authentication'):
    req = Pyjo.Message.Request.new()
    req.method = 'CONNECT'
    req.url.parse('http://Aladdin:open%20sesame@bücher.ch:3000/foo/bar')
    req.proxy = Pyjo.URL.new('http://Aladdin:open%20sesame@127.0.0.2:8080')
    req = Pyjo.Message.Request.new().parse(req.to_bytes())
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'CONNECT', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '//xn--bcher-kva.ch:3000', 'right URL')
    is_ok(req.url.host, 'xn--bcher-kva.ch', 'right host')
    is_ok(req.url.port, 3000, 'right port')
    is_ok(req.url.to_abs(), 'http://xn--bcher-kva.ch:3000', 'right absolute URL')
    is_ok(req.proxy.userinfo, 'Aladdin:open sesame', 'right proxy userinfo')
    is_ok(req.headers.authorization, 'Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==', 'right "Authorization" value')
    is_ok(req.headers.host, 'xn--bcher-kva.ch:3000', 'right "Host" value')
    is_ok(req.headers.proxy_authorization, 'Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==', 'right "Proxy-Authorization" value')

with subtest('Build HTTP 1.1 multipart request'):
    req = Pyjo.Message.Request.new()
    req.method = 'GET'
    req.url.parse('http://127.0.0.1/foo/bar')
    req.content = Pyjo.Content.MultiPart.new()
    req.headers.content_type = 'multipart/mixed; boundary=7am1X'
    req.content.parts.append(Pyjo.Content.Single.new())
    req.content.parts[-1].asset.add_chunk(b'Hallo Welt lalalala!')
    content = Pyjo.Content.Single.new()
    content.asset.add_chunk(b'lala\nfoobar\nperl rocks\n')
    content.headers.content_type = 'text/plain'
    req.content.parts.append(content)
    req = Pyjo.Message.Request.new().parse(req.to_bytes())
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar', 'right URL')
    is_ok(req.url.to_abs(), 'http://127.0.0.1/foo/bar', 'right absolute URL')
    is_ok(req.headers.host, '127.0.0.1', 'right "Host" value')
    is_ok(req.headers.content_length, '106', 'right "Content-Length" value')
    is_ok(req.headers.content_type, 'multipart/mixed; boundary=7am1X', 'right "Content-Type" value')
    is_ok(req.content.parts[0].asset.slurp(), b'Hallo Welt lalalala!', 'right content')
    is_ok(req.content.parts[1].headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(req.content.parts[1].asset.slurp(), b'lala\nfoobar\nperl rocks\n', 'right content')

with subtest('Build HTTP 1.1 multipart request (with clone)'):
    req = Pyjo.Message.Request.new()
    req.method = 'GET'
    req.url.parse('http://127.0.0.1/foo/bar')
    req.content = Pyjo.Content.MultiPart.new()
    req.headers.content_type = 'multipart/mixed; boundary=7am1X'
    req.content.parts.append(Pyjo.Content.Single.new())
    req.content.parts[-1].asset.add_chunk(b'Hallo Welt lalalala!')
    content = Pyjo.Content.Single.new()
    content.asset.add_chunk(b'lala\nfoobar\nperl rocks\n')
    content.headers.content_type = 'text/plain'
    req.content.parts.append(content)
    clone = req.clone()
    req = Pyjo.Message.Request.new().parse(req.to_bytes())
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar', 'right URL')
    is_ok(req.url.to_abs(), 'http://127.0.0.1/foo/bar', 'right absolute URL')
    is_ok(req.headers.host, '127.0.0.1', 'right "Host" value')
    is_ok(req.headers.content_length, '106', 'right "Content-Length" value')
    is_ok(req.headers.content_type, 'multipart/mixed; boundary=7am1X', 'right "Content-Type" value')
    is_ok(req.content.parts[0].asset.slurp(), b'Hallo Welt lalalala!', 'right content')
    is_ok(req.content.parts[1].headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(req.content.parts[1].asset.slurp(), b'lala\nfoobar\nperl rocks\n', 'right content')
    clone = Pyjo.Message.Request.new().parse(clone.to_bytes())
    ok(clone.is_finished, 'request is finished')
    is_ok(clone.method, 'GET', 'right method')
    is_ok(clone.version, '1.1', 'right version')
    is_ok(clone.url, '/foo/bar', 'right URL')
    is_ok(clone.url.to_abs(), 'http://127.0.0.1/foo/bar', 'right absolute URL')
    is_ok(clone.headers.host, '127.0.0.1', 'right "Host" value')
    is_ok(clone.headers.content_length, '106', 'right "Content-Length" value')
    is_ok(clone.headers.content_type, 'multipart/mixed; boundary=7am1X', 'right "Content-Type" value')
    is_ok(clone.content.parts[0].asset.slurp(), b'Hallo Welt lalalala!', 'right content')
    is_ok(clone.content.parts[1].headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(clone.content.parts[1].asset.slurp(), b'lala\nfoobar\nperl rocks\n', 'right content')

with subtest('Build HTTP 1.1 chunked request'):
    req = Pyjo.Message.Request.new()
    req.method = 'GET'
    req.url.parse('http://127.0.0.1:8080/foo/bar')
    req.headers.transfer_encoding = 'chunked'
    counter = None

    @req.on('progress')
    def progress_cb(req, *args):
        global counter
        counter = (counter or 0) + 1

    def drain(content, *args):
        def drain2(self, *args):
            self.write_chunk(b'')

        content.write_chunk(b'hello world2!\n\n', drain2)

    req.content.write_chunk(b'hello world!', drain)
    is_ok(req.clone(), None, 'dynamic requests cannot be cloned')
    req = Pyjo.Message.Request.new().parse(req.to_bytes())
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo/bar', 'right URL')
    is_ok(req.url.to_abs(), 'http://127.0.0.1:8080/foo/bar', 'right absolute URL')
    is_ok(req.headers.host, '127.0.0.1:8080', 'right "Host" value')
    is_ok(req.headers.transfer_encoding, None, 'no "Transfer-Encoding" value')
    is_ok(req.body, b'hello world!hello world2!\n\n', 'right content')
    ok(counter, 'right counter')

with subtest('Build HTTP 1.1 chunked request'):
    req = Pyjo.Message.Request.new()
    req.method = 'GET'
    req.url.parse('http://127.0.0.1')
    req.content.write_chunk(b'hello world!')
    req.content.write_chunk(b'hello world2!\n\n')
    req.content.write_chunk(b'')
    is_ok(req.clone(), None, 'dynamic requests cannot be cloned')
    req = Pyjo.Message.Request.new().parse(req.to_bytes())
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/', 'right URL')
    is_ok(req.url.to_abs(), 'http://127.0.0.1/', 'right absolute URL')
    is_ok(req.headers.host, '127.0.0.1', 'right "Host" value')
    is_ok(req.headers.transfer_encoding, None, 'no "Transfer-Encoding" value')
    is_ok(req.body, b'hello world!hello world2!\n\n', 'right content')

with subtest('Build full HTTP 1.1 request with cookies'):
    req = Pyjo.Message.Request.new()
    req.method = 'GET'
    req.url.parse('http://127.0.0.1/foo/bar?0')
    req.headers.expect = '100-continue'
    req.cookies({'name': 'foo', 'value': 'bar'}, {'name': 'bar', 'value': 'baz'})
    req.cookies(Pyjo.Cookie.Request.new(name='baz', value='yada'))
    req.body = b'Hello World!\n'
    ok(not not req.to_bytes(), 'message built')
    req2 = Pyjo.Message.Request.new()
    req2.parse(req.to_bytes())
    ok(req2.is_finished, 'request is finished')
    is_ok(req2.method, 'GET', 'right method')
    is_ok(req2.version, '1.1', 'right version')
    is_ok(req2.headers.expect, '100-continue', 'right "Expect" value')
    is_ok(req2.headers.host, '127.0.0.1', 'right "Host" value')
    is_ok(req2.headers.content_length, '13', 'right "Content-Length" value')
    is_ok(req2.headers.cookie, 'foo=bar; bar=baz; baz=yada', 'right "Cookie" value')
    is_ok(req2.url, '/foo/bar?0', 'right URL')
    is_ok(req2.url.to_abs(), 'http://127.0.0.1/foo/bar?0', 'right absolute URL')
    ok(req2.cookie('foo') is not None, 'cookie "foo" exists')
    ok(req2.cookie('bar') is not None, 'cookie "bar" exists')
    ok(req2.cookie('baz') is not None, 'cookie "baz" exists')
    ok(req2.cookie('yada') is None, 'cookie "yada" does not exist')
    is_ok(req2.cookie('foo').value, 'bar', 'right value')
    is_ok(req2.cookie('bar').value, 'baz', 'right value')
    is_ok(req2.cookie('baz').value, 'yada', 'right value')
    is_ok(req2.body, b'Hello World!\n', 'right content')

with subtest('Build HTTP 1.1 request with cookies sharing the same name'):
    req = Pyjo.Message.Request.new()
    req.method = 'GET'
    req.url.parse('http://127.0.0.1/foo/bar')
    req.cookies(
        {'name': 'foo', 'value': 'bar'},
        {'name': 'foo', 'value': 'baz'},
        {'name': 'foo', 'value': 'yada'},
        {'name': 'bar', 'value': 'foo'},
    )
    req2 = Pyjo.Message.Request.new()
    req2.parse(req.to_bytes())
    ok(req2.is_finished, 'request is finished')
    is_ok(req2.method, 'GET', 'right method')
    is_ok(req2.version, '1.1', 'right version')
    is_ok(req2.headers.host, '127.0.0.1', 'right "Host" value')
    is_ok(req2.headers.cookie, 'foo=bar; foo=baz; foo=yada; bar=foo', 'right "Cookie" value')
    is_ok(req2.url, '/foo/bar', 'right URL')
    is_ok(req2.url.to_abs(), 'http://127.0.0.1/foo/bar', 'right absolute URL')
    is_deeply_ok([c.value for c in req2.every_cookie('foo')], ['bar', 'baz', 'yada'], 'right values')
    is_deeply_ok([c.value for c in req2.every_cookie('bar')], ['foo'], 'right values')

with subtest('Parse full HTTP 1.0 request with cookies and progress callback'):
    req = Pyjo.Message.Request.new()
    counter = 0

    @req.on('progress')
    def progress_cb(req, *args):
        global counter
        counter += 1

    is_ok(counter, 0, 'right count')
    ok(not req.content.is_parsing_body, 'is not parsing body')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'GET /foo/bar/baz.html?fo')
    is_ok(counter, 1, 'right count')
    ok(not req.content.is_parsing_body, 'is not parsing body')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'o=13 HTTP/1.0\x0d\x0aContent')
    is_ok(counter, 2, 'right count')
    ok(not req.content.is_parsing_body, 'is not parsing body')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'-Type: text/')
    is_ok(counter, 3, 'right count')
    ok(not req.content.is_parsing_body, 'is not parsing body')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'plain\x0d\x0a')
    is_ok(counter, 4, 'right count')
    ok(not req.content.is_parsing_body, 'is not parsing body')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'Cookie: foo=bar; bar=baz')
    is_ok(counter, 5, 'right count')
    ok(not req.content.is_parsing_body, 'is not parsing body')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'\x0d\x0a')
    is_ok(counter, 6, 'right count')
    ok(not req.content.is_parsing_body, 'is not parsing body')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'Content-Length: 27\x0d\x0a\x0d\x0aHell')
    is_ok(counter, 7, 'right count')
    ok(req.content.is_parsing_body, 'is parsing body')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'o World!\n1234\nlalalala\n')
    is_ok(counter, 8, 'right count')
    ok(not req.content.is_parsing_body, 'is not parsing body')
    ok(req.is_finished, 'request is finished')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.0', 'right version')
    is_ok(req.url, '/foo/bar/baz.html?foo=13', 'right URL')
    is_ok(req.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(req.headers.content_length, '27', 'right "Content-Length" value')
    cookies = req.cookies()
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[1].name, 'bar', 'right name')
    is_ok(cookies[1].value, 'baz', 'right value')

with subtest('Parse and clone multipart/form-data request (changing size)'):
    req = Pyjo.Message.Request.new()
    req.parse(b'POST /example/testform_handler HTTP/1.1\x0d\x0a')
    req.parse(b'User-Agent: Mozilla/5.0\x0d\x0a')
    req.parse(b'Content-Type: multipart/form-data; ')
    req.parse(b'boundary=----WebKitFormBoundaryi5BnD9J9zoTMiSuP\x0d\x0a')
    req.parse(b'Content-Length: 318\x0d\x0aConnection: keep-alive\x0d\x0a')
    req.parse(b'Host: 127.0.0.1:3000\x0d\x0a\x0d\x0a')
    req.parse(b'------WebKitFormBoundaryi5BnD9J9zoTMiSuP\x0d\x0a')
    req.parse(b'Content-Disposition: form-data; name="Vorname"\x0a')
    req.parse(b'\x0d\x0aT\x0d\x0a------WebKitFormBoundaryi5BnD9J9zoTMiSuP\x0d')
    req.parse(b'\x0aContent-Disposition: form-data; name="Zuname"\x0a')
    req.parse(b'\x0d\x0a\x0d\x0a------WebKitFormBoundaryi5BnD9J9zoTMiSuP\x0d')
    req.parse(b'\x0aContent-Disposition: form-data; name="Text"\x0a')
    req.parse(b'\x0d\x0a\x0d\x0a------WebKitFormBoundaryi5BnD9J9zoTMiSuP--')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/example/testform_handler', 'right URL')
    is_ok(req.headers.content_length, '318', 'right "Content-Length" value')
    is_ok(req.param('Vorname'), 'T', 'right value')
    is_ok(req.param('Zuname'), '', 'right value')
    is_ok(req.param('Text'), '', 'right value')
    is_ok(req.content.parts[0].asset.slurp(), b'T', 'right content')
    is_ok(req.content.leftovers(), b'', 'no leftovers')
    req = Pyjo.Message.Request.new().parse(req.clone().to_bytes())
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/example/testform_handler', 'right URL')
    is_ok(req.headers.content_length, '323', 'right "Content-Length" value')
    is_ok(req.param('Vorname'), 'T', 'right value')
    is_ok(req.param('Zuname'), '', 'right value')
    is_ok(req.param('Text'), '', 'right value')
    is_ok(req.content.parts[0].asset.slurp(), b'T', 'right content')
    is_ok(req.content.leftovers(), b'', 'no leftovers')
    is_ok(req.content.get_body_chunk(322), b'\x0a', 'right chunk')
    is_ok(req.content.get_body_chunk(321), b'\x0d\x0a', 'right chunk')
    is_ok(req.content.get_body_chunk(320), b'-\x0d\x0a', 'right chunk')

with subtest('Parse multipart/form-data request with charset'):
    req = Pyjo.Message.Request.new()
    is_ok(req.default_charset, 'UTF-8', 'default charset is UTF-8')
    yatta = 'やった'
    yatta_sjis = encode('Shift_JIS', yatta)
    multipart = (
        b'------1234567890\x0d\x0a'
        + b'Content-Disposition: form-data; name="'
        + yatta_sjis
        + b'"\x0d\x0a\x0d\x0a'
        + yatta_sjis
        + b'\x0d\x0a------1234567890--'
    )
    req.parse(
        b'POST /example/yatta HTTP/1.1\x0d\x0a'
        + b'User-Agent: Mozilla/5.0\x0d\x0a'
        + b'Content-Type: multipart/form-data; charset=Shift_JIS; '
        + b'boundary=----1234567890\x0d\x0a'
        + f'Content-Length: {len(multipart)}\x0d\x0a'.encode()
        + b'Connection: keep-alive\x0d\x0a'
        + b'Host: 127.0.0.1:3000\x0d\x0a\x0d\x0a'
        + multipart
    )
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/example/yatta', 'right URL')
    is_ok(req.param(yatta), yatta, 'right value')
    is_ok(req.content.parts[0].asset.slurp(), yatta_sjis, 'right content')

with subtest('WebKit multipart/form-data request'):
    req = Pyjo.Message.Request.new()
    req.parse(b'POST /example/testform_handler HTTP/1.1\x0d\x0a')
    req.parse(b'User-Agent: Mozilla/5.0\x0d\x0a')
    req.parse(b'Content-Type: multipart/form-data; ')
    req.parse(b'boundary=----WebKitFormBoundaryi5BnD9J9zoTMiSuP\x0d\x0a')
    req.parse(b'Content-Length: 323\x0d\x0aConnection: keep-alive\x0d\x0a')
    req.parse(b'Host: 127.0.0.1:3000\x0d\x0a\x0d\x0a')
    req.parse(b'------WebKitFormBoundaryi5BnD9J9zoTMiSuP\x0d\x0a')
    req.parse(b'Content-Disposition: form-data; name="Vorname"\x0d\x0a')
    req.parse(b'\x0d\x0aT\x0d\x0a------WebKitFormBoundaryi5BnD9J9zoTMiSuP\x0d')
    req.parse(b'\x0aContent-Disposition: form-data; name="Zuname"\x0d\x0a')
    req.parse(b'\x0d\x0a\x0d\x0a------WebKitFormBoundaryi5BnD9J9zoTMiSuP\x0d')
    req.parse(b'\x0aContent-Disposition: form-data; name="Text"\x0d\x0a')
    req.parse(b'\x0d\x0a\x0d\x0a------WebKitFormBoundaryi5BnD9J9zoTMiSuP-')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'-')
    ok(not req.is_finished, 'request is not finished')
    req.parse(b'\x0d\x0a')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/example/testform_handler', 'right URL')
    is_ok(req.param('Vorname'), 'T', 'right value')
    is_ok(req.param('Zuname'), '', 'right value')
    is_ok(req.param('Text'), '', 'right value')
    is_ok(req.content.parts[0].asset.slurp(), b'T', 'right content')

with subtest('Chrome 35 multipart/form-data request (with quotation marks)'):
    req = Pyjo.Message.Request.new()
    req.parse(b'POST / HTTP/1.1\x0d\x0a')
    req.parse(b'Host: 127.0.0.1:3000\x0d\x0a')
    req.parse(b'Connection: keep-alive\x0d\x0a')
    req.parse(b'Content-Length: 180\x0d\x0a')
    req.parse(b'Accept: text/html,application/xhtml+xml,application/xml;q=')
    req.parse(b'0.9,image/webp,*/*;q=0.8\x0d\x0a')
    req.parse(b'Origin: http://127.0.0.1:3000\x0d\x0a')
    req.parse(b'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_0) App')
    req.parse(b'leWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari')
    req.parse(b'/537.36\x0d\x0a')
    req.parse(b'Content-Type: multipart/form-data; boundary=----WebKitFormBoun')
    req.parse(b'daryMTelhBLWA9N3KXAR\x0d\x0a')
    req.parse(b'Referer: http://127.0.0.1:3000/\x0d\x0a')
    req.parse(b'Accept-Encoding: gzip,deflate,sdch\x0d\x0a')
    req.parse(b'Accept-Language: en-US,en;q=0.8\x0d\x0a\x0d\x0a')
    req.parse(b'------WebKitFormBoundaryMTelhBLWA9N3KXAR\x0d\x0a')
    req.parse(b'Content-Disposition: form-data; na')
    req.parse(rb'me="foo \%22bar%22 baz\"; filename="fo\%22o%22.txt\"')
    req.parse(b'\x0d\x0a\x0d\x0atest\x0d\x0a')
    req.parse(b'------WebKitFormBoundaryMTelhBLWA9N3KXAR--\x0d\x0a')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/', 'right URL')
    is_ok(req.upload('foo \\%22bar%22 baz\\').filename, 'fo\\%22o%22.txt\\', 'right filename')
    is_ok(req.upload('foo \\%22bar%22 baz\\').slurp(), b'test', 'right content')

with subtest('Firefox 24 multipart/form-data request (with quotation marks)'):
    req = Pyjo.Message.Request.new()
    req.parse(b'POST / HTTP/1.1\x0d\x0a')
    req.parse(b'Host: 127.0.0.1:3000\x0d\x0a')
    req.parse(b'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:24.')
    req.parse(b'0) Gecko/20100101 Firefox/24.0\x0d\x0a')
    req.parse(b'Accept: text/html,application/xhtml+xml,application/xml;q=0.9')
    req.parse(b',*/*;q=0.8\x0d\x0a')
    req.parse(b'Accept-Language: de-de,de;q=0.8,en-us;q=0.5,en;q=0.3\x0d\x0a')
    req.parse(b'Accept-Encoding: gzip, deflate\x0d\x0a')
    req.parse(b'Referer: http://127.0.0.1:3000/\x0d\x0a')
    req.parse(b'Connection: keep-alive\x0d\x0a')
    req.parse(b'Content-Type: multipart/form-data; boundary=-----------------')
    req.parse(b'----------20773201241877674789807986058\x0d\x0a')
    req.parse(b'Content-Length: 212\x0d\x0a\x0d\x0a')
    req.parse(b'-----------------------------2077320124187767478980')
    req.parse(b'7986058\x0d\x0aContent-Disposition: form-data; na')
    req.parse(b'me="foo \\\\"bar\\" baz"; filename="fo\\\\"o\\".txt"')
    req.parse(b'\x0d\x0a\x0d\x0atest\x0d\x0a')
    req.parse(b'-----------------------------2077320124187767')
    req.parse(b'4789807986058--\x0d\x0a')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/', 'right URL')
    is_ok(req.upload(r'foo \\"bar\" baz').filename, 'fo\\\\"o\\".txt', 'right filename')
    is_ok(req.upload(r'foo \\"bar\" baz').slurp(), b'test', 'right content')

with subtest('Chrome 5 multipart/form-data request (UTF-8)'):
    req = Pyjo.Message.Request.new()
    fname, sname, sex, avatar, submit = (
        encode('UTF-8', x) for x in ('Иван', 'Иванов', 'мужской', 'аватар.jpg', 'Сохранить')
    )
    chrome = (
        b'------WebKitFormBoundaryYGjwdkpB6ZLCZQbX\x0d\x0a'
        + b'Content-Disposition: form-data; name="fname"\x0d\x0a\x0d\x0a'
        + fname
        + b'\x0d\x0a------WebKitFormBoundaryYGjwdkpB6ZLCZQbX\x0d\x0a'
        + b'Content-Disposition: form-data; name="sname"\x0d\x0a\x0d\x0a'
        + sname
        + b'\x0d\x0a------WebKitFormBoundaryYGjwdkpB6ZLCZQbX\x0d\x0a'
        + b'Content-Disposition: form-data; name="sex"\x0d\x0a\x0d\x0a'
        + sex
        + b'\x0d\x0a------WebKitFormBoundaryYGjwdkpB6ZLCZQbX\x0d\x0a'
        + b'Content-Disposition: form-data; name="bdate"\x0d\x0a\x0d\x0a'
        + b'16.02.1987\x0d\x0a------WebKitFormBoundaryYGjwdkpB6ZLCZQbX\x0d\x0a'
        + b'Content-Disposition: form-data; name="phone"\x0d\x0a\x0d\x0a'
        + b'1234567890\x0d\x0a------WebKitFormBoundaryYGjwdkpB6ZLCZQbX\x0d\x0a'
        + b'Content-Disposition: form-data; name="avatar"; filename="'
        + avatar
        + b'"'
        + b'\x0d\x0aContent-Type: image/jpeg\x0d\x0a\x0d\x0a1234'
        + b'\x0d\x0a------WebKitFormBoundaryYGjwdkpB6ZLCZQbX\x0d\x0a'
        + b'Content-Disposition: form-data; name="submit"\x0d\x0a\x0d\x0a'
        + submit
        + b'\x0d\x0a------WebKitFormBoundaryYGjwdkpB6ZLCZQbX--'
    )
    req.parse(
        b'POST / HTTP/1.0\x0d\x0a'
        + b'Host: 127.0.0.1:10002\x0d\x0a'
        + b'Connection: close\x0d\x0a'
        + b'User-Agent: Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/5'
        + b'32.9 (KHTML, like Gecko) Chrome/5.0.307.11 Safari/532.9\x0d\x0a'
        + b'Referer: http://example.org/\x0d\x0a'
        + f'Content-Length: {len(chrome)}\x0d\x0a'.encode()
        + b'Cache-Control: max-age=0\x0d\x0a'
        + b'Origin: http://example.org\x0d\x0a'
        + b'Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryY'
        + b'GjwdkpB6ZLCZQbX\x0d\x0a'
        + b'Accept: application/xml,application/xhtml+xml,text/html;q=0.9,text/'
        + b'plain;q=0.8,image/png,*/*;q=0.5\x0d\x0a'
        + b'Accept-Encoding: gzip,deflate,sdch\x0d\x0a'
        + b'Cookie: mojolicious=BAcIMTIzNDU2NzgECAgIAwIAAAAXDGFsZXgudm9yb25vdgQ'
        + b'AAAB1c2VyBp6FjksAAAAABwAAAGV4cGlyZXM=--1641adddfe885276cda0deb7475f'
        + b'153a\x0d\x0a'
        + b'Accept-Language: ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4\x0d\x0a'
        + b'Accept-Charset: windows-1251,utf-8;q=0.7,*;q=0.3\x0d\x0a\x0d\x0a'
        + chrome
    )
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.version, '1.0', 'right version')
    is_ok(req.url, '/', 'right URL')
    is_ok(
        req.cookie('mojolicious').value,
        'BAcIMTIzNDU2NzgECAgIAwIAAAAXDGFsZXgudm9yb25vdgQAAAB1c2VyBp6FjksAAAAABwA'
        + 'AAGV4cGlyZXM=--1641adddfe885276cda0deb7475f153a',
        'right value',
    )
    like_ok(req.headers.content_type, r'multipart/form-data', 'right "Content-Type" value')
    is_ok(req.param('fname'), 'Иван', 'right value')
    is_ok(req.param('sname'), 'Иванов', 'right value')
    is_ok(req.param('sex'), 'мужской', 'right value')
    is_ok(req.param('bdate'), '16.02.1987', 'right value')
    is_ok(req.param('phone'), '1234567890', 'right value')
    is_ok(req.param('submit'), 'Сохранить', 'right value')
    upload = req.upload('avatar')
    is_ok(isinstance(upload, Pyjo.Upload.object), True, 'right upload')
    is_ok(upload.headers.content_type, 'image/jpeg', 'right "Content-Type" value')
    is_ok(upload.filename, 'аватар.jpg', 'right filename')
    is_ok(upload.size, 4, 'right size')
    is_ok(upload.slurp(), b'1234', 'right content')
    is_ok(req.content.parts[0].asset.slurp(), fname, 'right content')

with subtest('Firefox 3.5.8 multipart/form-data request (UTF-8)'):
    req = Pyjo.Message.Request.new()
    fname, sname, sex, avatar, submit = (
        encode('UTF-8', x) for x in ('Иван', 'Иванов', 'мужской', 'аватар.jpg', 'Сохранить')
    )
    firefox = (
        b'-----------------------------213090722714721300002030499922\x0d\x0a'
        + b'Content-Disposition: form-data; name="fname"\x0d\x0a\x0d\x0a'
        + fname
        + b'\x0d\x0a'
        + b'-----------------------------213090722714721300002030499922\x0d\x0a'
        + b'Content-Disposition: form-data; name="sname"\x0d\x0a\x0d\x0a'
        + sname
        + b'\x0d\x0a'
        + b'-----------------------------213090722714721300002030499922\x0d\x0a'
        + b'Content-Disposition: form-data; name="sex"\x0d\x0a\x0d\x0a'
        + sex
        + b'\x0d\x0a'
        + b'-----------------------------213090722714721300002030499922\x0d\x0a'
        + b'Content-Disposition: form-data; name="bdate"\x0d\x0a\x0d\x0a'
        + b'16.02.1987\x0d\x0a'
        + b'-----------------------------213090722714721300002030499922\x0d\x0a'
        + b'Content-Disposition: form-data; name="phone"\x0d\x0a\x0d\x0a'
        + b'1234567890\x0d\x0a'
        + b'-----------------------------213090722714721300002030499922\x0d\x0a'
        + b'Content-Disposition: form-data; name="avatar"; filename="'
        + avatar
        + b'"'
        + b'\x0d\x0aContent-Type: image/jpeg\x0d\x0a\x0d\x0a1234\x0d\x0a'
        + b'-----------------------------213090722714721300002030499922\x0d\x0a'
        + b'Content-Disposition: form-data; name="submit"\x0d\x0a\x0d\x0a'
        + submit
        + b'\x0d\x0a'
        + b'-----------------------------213090722714721300002030499922--'
    )
    req.parse(
        b'POST / HTTP/1.0\x0d\x0a'
        + b'Host: 127.0.0.1:10002\x0d\x0a'
        + b'Connection: close\x0d\x0a'
        + b'User-Agent: Mozilla/5.0 (X11; U; Linux x86_64; ru; rv:1.9.1.8) Geck'
        + b'o/20100214 Ubuntu/9.10 (karmic) Firefox/3.5.8\x0d\x0a'
        + b'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q'
        + b'=0.8\x0d\x0a'
        + b'Accept-Language: ru,en-us;q=0.7,en;q=0.3\x0d\x0a'
        + b'Accept-Encoding: gzip,deflate\x0d\x0a'
        + b'Accept-Charset: windows-1251,utf-8;q=0.7,*;q=0.7\x0d\x0a'
        + b'Referer: http://example.org/\x0d\x0a'
        + b'Cookie: mojolicious=BAcIMTIzNDU2NzgECAgIAwIAAAAXDGFsZXgudm9yb25vdgQ'
        + b'AAAB1c2VyBiWFjksAAAAABwAAAGV4cGlyZXM=--cd933a37999e0fa8d7804205e891'
        + b'93a7\x0d\x0a'
        + b'Content-Type: multipart/form-data; boundary=-----------------------'
        + b'----213090722714721300002030499922\x0d\x0a'
        + f'Content-Length: {len(firefox)}\x0d\x0a\x0d\x0a'.encode()
        + firefox
    )
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.version, '1.0', 'right version')
    is_ok(req.url, '/', 'right URL')
    is_ok(
        req.cookie('mojolicious').value,
        'BAcIMTIzNDU2NzgECAgIAwIAAAAXDGFsZXgudm9yb25vdgQAAAB1c2VyBiWFjksAAAAABwA'
        + 'AAGV4cGlyZXM=--cd933a37999e0fa8d7804205e89193a7',
        'right value',
    )
    like_ok(req.headers.content_type, r'multipart/form-data', 'right "Content-Type" value')
    is_ok(req.param('fname'), 'Иван', 'right value')
    is_ok(req.param('sname'), 'Иванов', 'right value')
    is_ok(req.param('sex'), 'мужской', 'right value')
    is_ok(req.param('bdate'), '16.02.1987', 'right value')
    is_ok(req.param('phone'), '1234567890', 'right value')
    is_ok(req.param('submit'), 'Сохранить', 'right value')
    upload = req.upload('avatar')
    is_ok(isinstance(upload, Pyjo.Upload.object), True, 'right upload')
    is_ok(upload.headers.content_type, 'image/jpeg', 'right "Content-Type" value')
    is_ok(upload.filename, 'аватар.jpg', 'right filename')
    is_ok(upload.size, 4, 'right size')
    is_ok(upload.slurp(), b'1234', 'right content')
    is_ok(req.content.parts[0].asset.slurp(), fname, 'right content')

with subtest('Opera 9.8 multipart/form-data request (UTF-8)'):
    req = Pyjo.Message.Request.new()
    fname, sname, sex, avatar, submit = (
        encode('UTF-8', x) for x in ('Иван', 'Иванов', 'мужской', 'аватар.jpg', 'Сохранить')
    )
    opera = (
        b'------------IWq9cR9mYYG668xwSn56f0\x0d\x0a'
        + b'Content-Disposition: form-data; name="fname"\x0d\x0a\x0d\x0a'
        + fname
        + b'\x0d\x0a------------IWq9cR9mYYG668xwSn56f0\x0d\x0a'
        + b'Content-Disposition: form-data; name="sname"\x0d\x0a\x0d\x0a'
        + sname
        + b'\x0d\x0a------------IWq9cR9mYYG668xwSn56f0\x0d\x0a'
        + b'Content-Disposition: form-data; name="sex"\x0d\x0a\x0d\x0a'
        + sex
        + b'\x0d\x0a------------IWq9cR9mYYG668xwSn56f0\x0d\x0a'
        + b'Content-Disposition: form-data; name="bdate"\x0d\x0a\x0d\x0a'
        + b'16.02.1987\x0d\x0a------------IWq9cR9mYYG668xwSn56f0\x0d\x0a'
        + b'Content-Disposition: form-data; name="phone"\x0d\x0a\x0d\x0a'
        + b'1234567890\x0d\x0a------------IWq9cR9mYYG668xwSn56f0\x0d\x0a'
        + b'Content-Disposition: form-data; name="avatar"; filename="'
        + avatar
        + b'"'
        + b'\x0d\x0aContent-Type: image/jpeg\x0d\x0a\x0d\x0a'
        + b'1234\x0d\x0a------------IWq9cR9mYYG668xwSn56f0\x0d\x0a'
        + b'Content-Disposition: form-data; name="submit"\x0d\x0a\x0d\x0a'
        + submit
        + b'\x0d\x0a------------IWq9cR9mYYG668xwSn56f0--'
    )
    req.parse(
        b'POST / HTTP/1.0\x0d\x0a'
        + b'Host: 127.0.0.1:10002\x0d\x0a'
        + b'Connection: close\x0d\x0a'
        + b'User-Agent: Opera/9.80 (X11; Linux x86_64; U; ru) Presto/2.2.15 Ver'
        + b'sion/10.10\x0d\x0a'
        + b'Accept: text/html, application/xml;q=0.9, application/xhtml+xml, im'
        + b'age/png, image/jpeg, image/gif, image/x-xbitmap, */*;q=0.1\x0d\x0a'
        + b'Accept-Language: ru-RU,ru;q=0.9,en;q=0.8\x0d\x0a'
        + b'Accept-Charset: iso-8859-1, utf-8, utf-16, *;q=0.1\x0d\x0a'
        + b'Accept-Encoding: deflate, gzip, x-gzip, identity, *;q=0\x0d\x0a'
        + b'Referer: http://example.org/\x0d\x0a'
        + b'Cookie: mojolicious=BAcIMTIzNDU2NzgECAgIAwIAAAAXDGFsZXgudm9yb25vdgQ'
        + b'AAAB1c2VyBhaIjksAAAAABwAAAGV4cGlyZXM=--78a58a94f98ae5b75a489be1189f'
        + b'2672\x0d\x0a'
        + b'Cookie2: $Version=1\x0d\x0a'
        + b'TE: deflate, gzip, chunked, identity, trailers\x0d\x0a'
        + f'Content-Length: {len(opera)}\x0d\x0a'.encode()
        + b'Content-Type: multipart/form-data; boundary=----------IWq9cR9mYYG66'
        + b'8xwSn56f0\x0d\x0a\x0d\x0a'
        + opera
    )
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.version, '1.0', 'right version')
    is_ok(req.url, '/', 'right URL')
    is_ok(
        req.cookie('mojolicious').value,
        'BAcIMTIzNDU2NzgECAgIAwIAAAAXDGFsZXgudm9yb25vdgQAAAB1c2VyBhaIjksAAAAABwA'
        + 'AAGV4cGlyZXM=--78a58a94f98ae5b75a489be1189f2672',
        'right value',
    )
    like_ok(req.headers.content_type, r'multipart/form-data', 'right "Content-Type" value')
    is_ok(req.param('fname'), 'Иван', 'right value')
    is_ok(req.param('sname'), 'Иванов', 'right value')
    is_ok(req.param('sex'), 'мужской', 'right value')
    is_ok(req.param('bdate'), '16.02.1987', 'right value')
    is_ok(req.param('phone'), '1234567890', 'right value')
    is_ok(req.param('submit'), 'Сохранить', 'right value')
    upload = req.upload('avatar')
    is_ok(isinstance(upload, Pyjo.Upload.object), True, 'right upload')
    is_ok(upload.headers.content_type, 'image/jpeg', 'right "Content-Type" value')
    is_ok(upload.filename, 'аватар.jpg', 'right filename')
    is_ok(upload.size, 4, 'right size')
    is_ok(upload.slurp(), b'1234', 'right content')
    is_ok(req.content.parts[0].asset.slurp(), fname, 'right content')

with subtest('Firefox 14 multipart/form-data request (UTF-8)'):
    req = Pyjo.Message.Request.new()
    name, filename = (encode('UTF-8', x) for x in ('☃', 'foo bär ☃.txt'))
    firefox = (
        b'-----------------------------1264369278903768281481663536\x0d\x0a'
        + b'Content-Disposition: form-data; name="'
        + name
        + b'"; filename="'
        + filename
        + b'"'
        + b'\x0d\x0aContent-Type: text/plain\x0d\x0a\x0d\x0atest 123\x0d\x0a'
        + b'-----------------------------1264369278903768281481663536--'
    )
    req.parse(b'POST /foo HTTP/1.1\x0d\x0a')
    req.parse(b'Host: 127.0.0.1:3000\x0d\x0a')
    req.parse(b'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv')
    req.parse(b':14.0) Gecko/20100101 Firefox/14.0.1\x0d\x0a')
    req.parse(b'Accept: text/html,application/xhtml+xml,application/xml;')
    req.parse(b'q=0.9,*/*;q=0.8\x0d\x0a')
    req.parse(b'Accept-Language: en-us,en;q=0.5\x0d\x0a')
    req.parse(b'Accept-Encoding: gzip, deflate\x0d\x0a')
    req.parse(b'Connection: keep-alive\x0d\x0a')
    req.parse(b'Referer: http://127.0.0.1:3000/\x0d\x0a')
    req.parse(b'Content-Type: multipart/form-data;')
    req.parse(b'boundary=---------------------------126436927890376828148')
    req.parse(b'1663536\x0d\x0a')
    req.parse(f'Content-Length: {len(firefox)}\x0d\x0a\x0d\x0a'.encode())
    req.parse(firefox)
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/foo', 'right URL')
    like_ok(req.headers.content_type, r'multipart/form-data', 'right "Content-Type" value')
    is_ok(req.upload('☃').name, '☃', 'right name')
    is_ok(req.upload('☃').filename, 'foo bär ☃.txt', 'right filename')
    is_ok(req.upload('☃').headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(req.upload('☃').asset.size, 8, 'right size')
    is_ok(req.upload('☃').asset.slurp(), b'test 123', 'right content')

with subtest('Parse "~" in URL'):
    req = Pyjo.Message.Request.new()
    req.parse(b'GET /~foobar/ HTTP/1.1\x0d\x0a\x0d\x0a')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/~foobar/', 'right URL')

with subtest('Parse ":" in URL'):
    req = Pyjo.Message.Request.new()
    req.parse(b'GET /perldoc?Mojo::Message::Request HTTP/1.1\x0d\x0a\x0d\x0a')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, '/perldoc?Mojo::Message::Request', 'right URL')
    is_ok(req.url.query.pairs[0][0], 'Mojo::Message::Request', 'right value')

with subtest('Parse lots of special characters in URL'):
    req = Pyjo.Message.Request.new()
    req.parse(b"GET /09azAZ!$%&'()*+,-./:;=?@[\\]^_`{|}~\xc3\x9f#abc ")
    req.parse(b'HTTP/1.1\x0d\x0a\x0d\x0a')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url, "/09azAZ!$%&'()*+,-./:;=?@%5B%5C%5D%5E_%60%7B%7C%7D~%C3%83%C2%9F", 'right URL')

with subtest('Abstract methods'):
    throws_ok(
        lambda: Pyjo.Message.new().cookies(), re.compile(r'Method "cookies" not implemented by subclass'), 'right error'
    )
    throws_ok(
        lambda: Pyjo.Message.new().extract_start_line(bytearray()),
        re.compile(r'Method "extract_start_line" not implemented by subclass'),
        'right error',
    )
    throws_ok(
        lambda: Pyjo.Message.new().get_start_line_chunk(0),
        re.compile(r'Method "get_start_line_chunk" not implemented by subclass'),
        'right error',
    )
    throws_ok(
        lambda: Pyjo.Message.new().start_line_size,
        re.compile(r'Method "start_line_size" not implemented by subclass'),
        'right error',
    )

done_testing()
