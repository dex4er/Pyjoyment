import Pyjo.UserAgent.Transactor

from Pyjo.Test import *

import json

from email import message_from_bytes, policy
from urllib.parse import parse_qs, urlsplit


t = Pyjo.UserAgent.Transactor.new()

with subtest('URL of urllib.parse'):
    tx = t.tx('GET', urlsplit('https://example.com/foo?a=b'))
    is_ok(str(tx.req.url), 'https://example.com/foo?a=b', 'right URL')
    tx = t.websocket(urlsplit('ws://example.com/echo'))
    is_ok(str(tx.req.url), 'http://example.com/echo', 'right URL')

with subtest('JSON for json'):
    tx = t.tx('POST', 'http://example.com', json={'a': ['b', 1, None]})
    is_deeply_ok(json.loads(tx.req.body), {'a': ['b', 1, None]}, 'same data')

with subtest('Form for urllib.parse'):
    tx = t.tx('POST', 'http://example.com', form={'a': ['b', 'c'], '♥': '☃'})
    is_deeply_ok(parse_qs(tx.req.body.decode()), {'a': ['b', 'c'], '♥': ['☃']}, 'same form')
    tx = t.tx('GET', 'http://example.com', form={'a': ['b', 'c'], '♥': '☃'})
    is_deeply_ok(parse_qs(str(tx.req.url.query)), {'a': ['b', 'c'], '♥': ['☃']}, 'same query')

with subtest('Multipart form for email'):
    tx = t.tx(
        'POST',
        'http://example.com',
        form={'a': 'b', 'mytext': {'content': 'lalala', 'filename': 'foo.txt', 'Content-Type': 'text/plain'}},
    )
    message = message_from_bytes(tx.req.to_bytes().split(b'\r\n', 1)[1], policy=policy.HTTP)
    parts = list(message.iter_parts())
    is_deeply_ok(
        [
            (part.get_param('name', header='content-disposition'), part.get_filename(), part.get_content())
            for part in parts
        ],
        [('a', None, 'b'), ('mytext', 'foo.txt', 'lalala')],
        'same parts',
    )

done_testing()
