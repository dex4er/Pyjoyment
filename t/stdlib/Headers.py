import Pyjo.Headers

from Pyjo.Test import *

import http.client
import io
import os
import re
import urllib.request
import wsgiref.headers

from email.message import Message
from unittest.mock import patch


RAW = b'Content-Type: text/plain\r\nSet-Cookie: a=1\r\nSet-Cookie: b=2\r\nX-Name: caf\xe9\r\n\r\n'

with subtest('From the standard library'):
    message = http.client.parse_headers(io.BytesIO(RAW))
    headers = Pyjo.Headers.new(message)
    is_ok(headers.content_type, 'text/plain', 'from HTTPMessage')
    is_deeply_ok(headers.every_header('Set-Cookie'), ['a=1', 'b=2'], 'repeated headers')
    is_ok(Pyjo.Headers.new({'Vary': ['Accept', 'Accept-Encoding']}).vary, 'Accept, Accept-Encoding', 'from dict')
    is_ok(Pyjo.Headers.new([('Vary', 'Accept'), ('Vary', 'Accept-Encoding')]).vary, 'Accept, Accept-Encoding', 'pairs')
    is_ok(str(Pyjo.Headers.new(headers)), str(headers), 'from Pyjo.Headers')

with subtest('Characters as http.client has them'):
    message = http.client.parse_headers(io.BytesIO(RAW))
    headers = Pyjo.Headers.new().parse(RAW)
    is_ok(headers.header('X-Name'), message['X-Name'], 'ISO-8859-1, as http.client decodes it')
    is_ok(headers.header('X-Name'), 'café', 'right value')
    like_ok(headers.to_bytes(), re.compile(rb'X-Name: caf\xe9'), 'encoded back as ISO-8859-1')

with subtest('Mapping'):
    headers = Pyjo.Headers.new(http.client.parse_headers(io.BytesIO(RAW)))
    is_deeply_ok(
        dict(headers),
        {'Content-Type': 'text/plain', 'Set-Cookie': 'a=1, b=2', 'X-Name': 'café'},
        'dict(headers)',
    )
    ok('content-type' in headers, 'in, without regard to case')
    ok('X-Missing' not in headers, 'not in')
    is_ok(headers['SET-COOKIE'], 'a=1, b=2', 'headers[name]')
    is_ok(headers.get('X-Missing', 'none'), 'none', 'get with a default')
    is_ok(len(headers), 3, 'len')
    is_deeply_ok(list(headers), ['Content-Type', 'Set-Cookie', 'X-Name'], 'iter')
    request = urllib.request.Request('http://example.com', headers=headers)
    is_ok(request.get_header('Content-type'), 'text/plain', 'urllib.request.Request(headers=headers)')

with subtest('To the standard library'):
    headers = Pyjo.Headers.new(http.client.parse_headers(io.BytesIO(RAW)))
    message = headers.to_message()
    isa_ok(message, Message, 'to_message')
    is_deeply_ok(message.get_all('Set-Cookie'), ['a=1', 'b=2'], 'each value on its own')
    pairs = headers.to_list()
    is_ok(pairs.count(('Set-Cookie', 'a=1')), 1, 'to_list')
    is_deeply_ok(wsgiref.headers.Headers(pairs).get_all('Set-Cookie'), ['a=1', 'b=2'], 'wsgiref')

with subtest('Roundtrip'):
    headers = Pyjo.Headers.new(http.client.parse_headers(io.BytesIO(RAW)))
    is_deeply_ok(Pyjo.Headers.new(headers.to_message()).to_list(), headers.to_list(), 'through Message')
    is_deeply_ok(Pyjo.Headers.new(headers.to_list()).to_list(), headers.to_list(), 'through a list of pairs')

with subtest('The limits of the environment are read on first use'):
    headers = Pyjo.Headers.new()
    with patch.dict(os.environ, {'PYJO_MAX_LINE_SIZE': '1024', 'PYJO_MAX_LINES': '10'}):
        is_ok(headers.max_line_size, 1024, 'max_line_size')
        is_ok(headers.max_lines, 10, 'max_lines')
    is_ok(headers.max_line_size, 1024, 'kept')
    is_ok(Pyjo.Headers.new(max_line_size=2048).max_line_size, 2048, 'given')

done_testing()
