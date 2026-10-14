import Pyjo.Asset.File
import Pyjo.Asset.Memory
import Pyjo.Promise
import Pyjo.Transaction
import Pyjo.Transaction.WebSocket
import Pyjo.URL
import Pyjo.UserAgent.Transactor

from Pyjo.File import tempdir
from Pyjo.Test import *
from Pyjo.Util import b64_decode, encode
from Pyjo.WebSocket import server_handshake

import os
import re

from unittest.mock import patch


# Custom content generator
t = Pyjo.UserAgent.Transactor.new()


def reverse(t, tx, content):
    tx.req.body = content[::-1].encode()


t.add_generator('reverse', reverse)

with subtest('Compression'):
    with patch.dict(os.environ, {'PYJO_GZIP': '1'}):
        t2 = Pyjo.UserAgent.Transactor.new()
        ok(t2.compressed, 'compressed')
        is_ok(t2.tx('GET', '/').req.headers.accept_encoding, 'gzip', 'right value')
        is_ok(t2.tx('GET', '/').res.content.auto_decompress, None, 'no value')

        os.environ['PYJO_GZIP'] = '0'
        t2 = Pyjo.UserAgent.Transactor.new()
        ok(not t2.compressed, 'not compressed')
        is_ok(t2.tx('GET', '/').req.headers.accept_encoding, None, 'no value')
        is_ok(t2.tx('GET', '/').res.content.auto_decompress, False, 'right value')

with subtest('Simple GET'):
    tx = t.tx('GET', 'mojolicious.org/foo.html?bar=baz')
    is_ok(str(tx.req.url.to_abs()), 'http://mojolicious.org/foo.html?bar=baz', 'right URL')
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(tx.req.headers.accept_encoding, 'gzip', 'right "Accept-Encoding" value')
    # Unlike Mojolicious: Pyjoyment names itself
    is_ok(tx.req.headers.user_agent, 'Pyjoyment (Python)', 'right "User-Agent" value')

with subtest('GET with escaped slash'):
    url = Pyjo.URL.new('http://mojolicious.org')
    url.path.parts = ['foo/bar']
    tx = t.tx('GET', url)
    is_ok(tx.req.url.to_str(), url.to_str(), 'URLs are equal')
    is_ok(tx.req.url.path.to_str(), url.path.to_str(), 'paths are equal')
    is_ok(tx.req.url.path.to_str(), 'foo%2Fbar', 'right path')
    is_ok(tx.req.method, 'GET', 'right method')

with subtest('POST with header'):
    t.name = 'MyUA 1.0'
    tx = t.tx('POST', 'https://mojolicious.org', {'DNT': 1})
    is_ok(str(tx.req.url.to_abs()), 'https://mojolicious.org', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.dnt, '1', 'right "DNT" value')
    is_ok(tx.req.headers.accept_encoding, 'gzip', 'right "Accept-Encoding" value')
    is_ok(tx.req.headers.user_agent, 'MyUA 1.0', 'right "User-Agent" value')

with subtest('POST with header and content'):
    tx = t.tx('POST', 'https://mojolicious.org', {'DNT': 1}, 'test')
    is_ok(str(tx.req.url.to_abs()), 'https://mojolicious.org', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.dnt, '1', 'right "DNT" value')
    is_ok(tx.req.body, b'test', 'right content')

with subtest('DELETE with content'):
    tx = t.tx('DELETE', 'https://mojolicious.org', 'test')
    is_ok(str(tx.req.url.to_abs()), 'https://mojolicious.org', 'right URL')
    is_ok(tx.req.method, 'DELETE', 'right method')
    is_ok(tx.req.headers.dnt, None, 'no "DNT" value')
    is_ok(tx.req.body, b'test', 'right content')

with subtest('PUT with custom content generator'):
    tx = t.tx('PUT', 'mojolicious.org', reverse='hello!')
    is_ok(str(tx.req.url.to_abs()), 'http://mojolicious.org', 'right URL')
    is_ok(tx.req.method, 'PUT', 'right method')
    is_ok(tx.req.headers.dnt, None, 'no "DNT" value')
    is_ok(tx.req.body, b'!olleh', 'right content')
    tx = t.tx('PUT', 'mojolicious.org', {'DNT': 1}, reverse='hello!')
    is_ok(str(tx.req.url.to_abs()), 'http://mojolicious.org', 'right URL')
    is_ok(tx.req.method, 'PUT', 'right method')
    is_ok(tx.req.headers.dnt, '1', 'right "DNT" value')
    is_ok(tx.req.body, b'!olleh', 'right content')

with subtest('Simple JSON POST'):
    tx = t.tx('POST', 'http://example.com/foo', json={'test': 123})
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.content_type, 'application/json', 'right "Content-Type" value')
    is_deeply_ok(tx.req.json(), {'test': 123}, 'right content')
    tx = t.tx('POST', 'http://example.com/foo', json=[1, 2, 3])
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.content_type, 'application/json', 'right "Content-Type" value')
    is_deeply_ok(tx.req.json(), [1, 2, 3], 'right content')

with subtest('JSON POST with headers'):
    tx = t.tx('POST', 'http://example.com/foo', {'DNT': 1}, json={'test': 123})
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.dnt, '1', 'right "DNT" value')
    is_ok(tx.req.headers.content_type, 'application/json', 'right "Content-Type" value')
    is_deeply_ok(tx.req.json(), {'test': 123}, 'right content')

with subtest('JSON POST with custom content type'):
    tx = t.tx('POST', 'http://example.com/foo', {'DNT': 1, 'content-type': 'application/something'}, json=[1, 2])
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.dnt, '1', 'right "DNT" value')
    is_ok(tx.req.headers.content_type, 'application/something', 'right "Content-Type" value')
    is_deeply_ok(tx.req.json(), [1, 2], 'right content')

with subtest('Simple form (POST)'):
    tx = t.tx('POST', 'http://example.com/foo', form={'test': 123})
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.content_type, 'application/x-www-form-urlencoded', 'right "Content-Type" value')
    is_ok(tx.req.body, b'test=123', 'right content')

with subtest('Simple form (GET)'):
    tx = t.tx('GET', 'http://example.com/foo', form={'test': 123})
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo?test=123', 'right URL')
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(tx.req.headers.content_type, None, 'no "Content-Type" value')
    is_ok(tx.req.body, b'', 'no content')

with subtest('Simple form with multiple values'):
    tx = t.tx('POST', 'http://example.com/foo', form={'a': [1, 2, 3], 'b': 4})
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.content_type, 'application/x-www-form-urlencoded', 'right "Content-Type" value')
    ok(not tx.is_empty, 'transaction is not empty')
    is_ok(tx.req.body, b'a=1&a=2&a=3&b=4', 'right content')

with subtest('Existing query string (lowercase HEAD)'):
    tx = t.tx('head', 'http://example.com?foo=bar', form={'baz': [1, 2]})
    is_ok(str(tx.req.url.to_abs()), 'http://example.com?foo=bar&baz=1&baz=2', 'right URL')
    is_ok(tx.req.method, 'head', 'right method')
    is_ok(tx.req.headers.content_type, None, 'no "Content-Type" value')
    ok(tx.is_empty, 'transaction is empty')
    is_ok(tx.req.body, b'', 'no content')

with subtest('UTF-8 query'):
    tx = t.tx('GET', 'http://example.com/foo', form={'a': '☃', 'b': '♥'})
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo?a=%E2%98%83&b=%E2%99%A5', 'right URL')
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(tx.req.headers.content_type, None, 'no "Content-Type" value')
    is_ok(tx.req.body, b'', 'no content')

with subtest('UTF-8 form'):
    tx = t.tx('POST', 'http://example.com/foo', form={'♥': '☃'})
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.content_type, 'application/x-www-form-urlencoded', 'right "Content-Type" value')
    is_ok(tx.req.body, b'%E2%99%A5=%E2%98%83', 'right content')
    is_ok(tx.req.param('♥'), '☃', 'right value')

with subtest('UTF-8 form with header and custom content type'):
    tx = t.tx(
        'POST',
        'http://example.com/foo',
        {'Accept': '*/*', 'Content-Type': 'application/mojo-form'},
        form={'♥': '☃', 'nothing': None},
    )
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.content_type, 'application/mojo-form', 'right "Content-Type" value')
    is_ok(tx.req.headers.accept, '*/*', 'right "Accept" value')
    is_ok(tx.req.body, b'%E2%99%A5=%E2%98%83', 'right content')

with subtest('Form (shift_jis)'):
    tx = t.tx('POST', 'http://example.com/foo', form={'やった': 'やった'}, charset='shift_jis')
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.content_type, 'application/x-www-form-urlencoded', 'right "Content-Type" value')
    is_ok(tx.req.body, b'%82%E2%82%C1%82%BD=%82%E2%82%C1%82%BD', 'right content')
    tx.req.default_charset = 'shift_jis'
    is_ok(tx.req.param('やった'), 'やった', 'right value')

with subtest('UTF-8 multipart form'):
    tx = t.tx(
        'POST', 'http://example.com/foo', {'Content-Type': 'multipart/form-data'}, form={'♥': '☃', 'nothing': None}
    )
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.content_type, 'multipart/form-data', 'right "Content-Type" value')
    like_ok(
        tx.req.content.parts[0].headers.content_disposition,
        f'"{re.escape(encode("UTF-8", "♥").decode("latin-1"))}"',
        'right "Content-Disposition" value',
    )
    is_ok(tx.req.content.parts[0].asset.slurp(), encode('UTF-8', '☃'), 'right part')
    ok(not tx.req.content.parts[0].asset.is_file, 'stored in memory')
    ok(not tx.req.content.parts[0].asset.auto_upgrade, 'no upgrade')
    is_ok(len(tx.req.content.parts), 1, 'no more parts')
    is_ok(tx.req.param('♥'), '☃', 'right value')

with subtest('Multipart form (shift_jis)'):
    tx = t.tx(
        'POST',
        'http://example.com/foo',
        {'Content-Type': 'multipart/form-data'},
        form={'やった': 'やった'},
        charset='shift_jis',
    )
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.content_type, 'multipart/form-data', 'right "Content-Type" value')
    like_ok(
        tx.req.content.parts[0].headers.content_disposition,
        f'"{re.escape(encode("shift_jis", "やった").decode("latin-1"))}"',
        'right "Content-Disposition" value',
    )
    is_ok(tx.req.content.parts[0].asset.slurp(), encode('shift_jis', 'やった'), 'right part')
    ok(not tx.req.content.parts[0].asset.is_file, 'stored in memory')
    ok(not tx.req.content.parts[0].asset.auto_upgrade, 'no upgrade')
    is_ok(len(tx.req.content.parts), 1, 'no more parts')
    tx.req.default_charset = 'shift_jis'
    is_ok(tx.req.param('やった'), 'やった', 'right value')

with subtest('Multipart form with multiple values'):
    tx = t.tx('POST', 'http://example.com/foo', {'Content-Type': 'multipart/form-data'}, form={'a': [1, 2, 3], 'b': 4})
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.content_type, 'multipart/form-data', 'right "Content-Type" value')
    like_ok(tx.req.content.parts[0].headers.content_disposition, r'"a"', 'right "Content-Disposition" value')
    is_ok(tx.req.content.parts[0].asset.slurp(), b'1', 'right part')
    like_ok(tx.req.content.parts[1].headers.content_disposition, r'"a"', 'right "Content-Disposition" value')
    is_ok(tx.req.content.parts[1].asset.slurp(), b'2', 'right part')
    like_ok(tx.req.content.parts[2].headers.content_disposition, r'"a"', 'right "Content-Disposition" value')
    is_ok(tx.req.content.parts[2].asset.slurp(), b'3', 'right part')
    like_ok(tx.req.content.parts[3].headers.content_disposition, r'"b"', 'right "Content-Disposition" value')
    is_ok(tx.req.content.parts[3].asset.slurp(), b'4', 'right part')
    is_ok(len(tx.req.content.parts), 4, 'no more parts')
    is_deeply_ok(tx.req.every_param('a'), ['1', '2', '3'], 'right values')
    is_ok(tx.req.param('b'), '4', 'right value')

with subtest('Multipart form with real file and custom header'):
    tx = t.tx('POST', 'http://example.com/foo', form={'mytext': {'file': __file__, 'DNT': 1}})
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.content_type, 'multipart/form-data', 'right "Content-Type" value')
    like_ok(tx.req.content.parts[0].headers.content_disposition, r'"mytext"', 'right "Content-Disposition" value')
    like_ok(
        tx.req.content.parts[0].headers.content_disposition,
        r'"UserAgent_Transactor.py"',
        'right "Content-Disposition" value',
    )
    like_ok(tx.req.content.parts[0].asset.slurp(), rb'mytext', 'right part')
    ok(tx.req.content.parts[0].asset.is_file, 'stored in file')
    ok(not tx.req.content.parts[0].headers.header('file'), 'no "file" header')
    is_ok(tx.req.content.parts[0].headers.dnt, '1', 'right "DNT" header')
    is_ok(len(tx.req.content.parts), 1, 'no more parts')

with subtest('Multipart form with custom Content-Disposition header'):
    tx = t.tx(
        'POST',
        'http://example.com/foo',
        form={'mytext': {'file': __file__, 'Content-Disposition': 'form-data; name="works"'}},
    )
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.content_type, 'multipart/form-data', 'right "Content-Type" value')
    unlike_ok(
        tx.req.content.parts[0].headers.content_disposition,
        r'"UserAgent_Transactor.py"',
        'different "Content-Disposition" value',
    )
    is_ok(
        tx.req.content.parts[0].headers.content_disposition,
        'form-data; name="works"',
        'right "Content-Disposition" value',
    )
    like_ok(tx.req.content.parts[0].asset.slurp(), rb'mytext', 'right part')
    ok(tx.req.content.parts[0].asset.is_file, 'stored in file')
    ok(not tx.req.content.parts[0].headers.header('file'), 'no "file" header')
    is_ok(len(tx.req.content.parts), 1, 'no more parts')

with subtest('Multipart form with asset and custom content type'):
    tx = t.tx(
        'POST',
        'http://example.com/foo',
        {'Content-Type': 'multipart/mojo-form'},
        form={'mytext': {'file': Pyjo.Asset.File.new(path=__file__)}},
    )
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.content_type, 'multipart/mojo-form', 'right "Content-Type" value')
    like_ok(tx.req.content.parts[0].headers.content_disposition, r'"mytext"', 'right "Content-Disposition" value')
    like_ok(
        tx.req.content.parts[0].headers.content_disposition,
        r'"UserAgent_Transactor.py"',
        'right "Content-Disposition" value',
    )
    like_ok(tx.req.content.parts[0].asset.slurp(), rb'mytext', 'right part')
    ok(tx.req.content.parts[0].asset.is_file, 'stored in file')
    is_ok(len(tx.req.content.parts), 1, 'no more parts')

with subtest('Multipart form with in-memory content'):
    tx = t.tx('POST', 'http://example.com/foo', form={'mytext': {'content': 'lalala'}})
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.content_type, 'multipart/form-data', 'right "Content-Type" value')
    like_ok(tx.req.content.parts[0].headers.content_disposition, r'mytext', 'right "Content-Disposition" value')
    ok(not tx.req.content.parts[0].headers.header('content'), 'no "content" header')
    is_ok(tx.req.content.parts[0].asset.slurp(), b'lalala', 'right part')
    ok(not tx.req.content.parts[0].asset.is_file, 'stored in memory')
    ok(not tx.req.content.parts[0].asset.auto_upgrade, 'no upgrade')
    is_ok(len(tx.req.content.parts), 1, 'no more parts')

with subtest('Multipart form with filename ("0")'):
    tx = t.tx('POST', 'http://example.com/foo', form={'0': {'content': 'whatever', 'filename': '0'}})
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.content_type, 'multipart/form-data', 'right "Content-Type" value')
    like_ok(tx.req.content.parts[0].headers.content_disposition, r'0', 'right "Content-Disposition" value')
    ok(not tx.req.content.parts[0].headers.header('filename'), 'no "filename" header')
    is_ok(tx.req.content.parts[0].asset.slurp(), b'whatever', 'right part')
    is_ok(len(tx.req.content.parts), 1, 'no more parts')
    is_ok(tx.req.upload('0').filename, '0', 'right filename')
    is_ok(tx.req.upload('0').size, 8, 'right size')
    is_ok(tx.req.upload('0').slurp(), b'whatever', 'right content')

with subtest('Multipart form with asset and filename (UTF-8)'):
    snowman = encode('UTF-8', '☃').decode('latin-1')
    tx = t.tx(
        'POST',
        'http://example.com/foo',
        form={'"☃"': {'file': Pyjo.Asset.Memory.new().add_chunk(b'snowman'), 'filename': '"☃".jpg'}},
    )
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.content_type, 'multipart/form-data', 'right "Content-Type" value')
    like_ok(tx.req.content.parts[0].headers.content_disposition, snowman, 'right "Content-Disposition" value')
    is_ok(tx.req.content.parts[0].asset.slurp(), b'snowman', 'right part')
    is_ok(len(tx.req.content.parts), 1, 'no more parts')
    is_ok(tx.req.upload('%22☃%22').filename, '%22☃%22.jpg', 'right filename')
    is_ok(tx.req.upload('%22☃%22').size, 7, 'right size')
    is_ok(tx.req.upload('%22☃%22').slurp(), b'snowman', 'right content')

with subtest('Multipart form with multiple uploads sharing the same name'):
    tx = t.tx(
        'POST',
        'http://example.com/foo',
        form={'mytext': [{'content': 'just', 'filename': 'one.txt'}, {'content': 'works', 'filename': 'two.txt'}]},
    )
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.content_type, 'multipart/form-data', 'right "Content-Type" value')
    like_ok(tx.req.content.parts[0].headers.content_disposition, r'mytext', 'right "Content-Disposition" value')
    like_ok(tx.req.content.parts[0].headers.content_disposition, r'one\.txt', 'right "Content-Disposition" value')
    is_ok(tx.req.content.parts[0].asset.slurp(), b'just', 'right part')
    like_ok(tx.req.content.parts[1].headers.content_disposition, r'mytext', 'right "Content-Disposition" value')
    like_ok(tx.req.content.parts[1].headers.content_disposition, r'two\.txt', 'right "Content-Disposition" value')
    is_ok(tx.req.content.parts[1].asset.slurp(), b'works', 'right part')
    is_ok(len(tx.req.content.parts), 2, 'no more parts')

with subtest('Multipart request (long)'):
    tx = t.tx('POST', 'http://example.com/foo', multipart=[{'content': 'just'}, {'content': 'works'}])
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.content_type, None, 'no "Content-Type" value')
    is_ok(tx.req.content.parts[0].headers.content_disposition, None, 'no "Content-Disposition" value')
    is_ok(tx.req.content.parts[0].asset.slurp(), b'just', 'right part')
    is_ok(tx.req.content.parts[1].headers.content_disposition, None, 'no "Content-Disposition" value')
    is_ok(tx.req.content.parts[1].asset.slurp(), b'works', 'right part')
    is_ok(len(tx.req.content.parts), 2, 'no more parts')

with subtest('Multipart request (short)'):
    tx = t.tx('POST', 'http://example.com/foo', multipart=['just', 'works'])
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.content_type, None, 'no "Content-Type" value')
    is_ok(tx.req.content.parts[0].headers.content_disposition, None, 'no "Content-Disposition" value')
    is_ok(tx.req.content.parts[0].asset.slurp(), b'just', 'right part')
    is_ok(tx.req.content.parts[1].headers.content_disposition, None, 'no "Content-Disposition" value')
    is_ok(tx.req.content.parts[1].asset.slurp(), b'works', 'right part')
    is_ok(len(tx.req.content.parts), 2, 'no more parts')

with subtest('Multipart request with asset'):
    tx = t.tx('POST', 'http://example.com/foo', multipart=[{'file': Pyjo.Asset.Memory.new().add_chunk(b'snowman')}])
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.content_type, None, 'no "Content-Type" value')
    is_ok(tx.req.content.parts[0].headers.content_disposition, None, 'no "Content-Disposition" value')
    is_ok(tx.req.content.parts[0].asset.slurp(), b'snowman', 'right part')
    is_ok(len(tx.req.content.parts), 1, 'no more parts')

with subtest('Multipart request with real file and custom header'):
    tx = t.tx('POST', 'http://example.com/foo', multipart=[{'file': __file__, 'DNT': 1}])
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/foo', 'right URL')
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(tx.req.headers.content_type, None, 'no "Content-Type" value')
    like_ok(tx.req.content.parts[0].asset.slurp(), rb'mytext', 'right part')
    ok(tx.req.content.parts[0].asset.is_file, 'stored in file')
    is_ok(tx.req.content.parts[0].headers.header('file'), None, 'no "file" header')
    is_ok(tx.req.content.parts[0].headers.content_disposition, None, 'no "Content-Disposition" value')
    is_ok(tx.req.content.parts[0].headers.dnt, '1', 'right "DNT" header')
    is_ok(len(tx.req.content.parts), 1, 'no more parts')

with subtest('Simple endpoint'):
    tx = t.tx('GET', 'mojolicious.org')
    is_ok(t.endpoint(tx)[0], 'http', 'right scheme')
    is_ok(t.endpoint(tx)[1], 'mojolicious.org', 'right host')
    is_ok(t.endpoint(tx)[2], 80, 'right port')

with subtest('Simple endpoint with proxy'):
    tx = t.tx('GET', 'http://mojolicious.org')
    tx.req.proxy = Pyjo.URL.new('http://127.0.0.1:3000')
    is_ok(t.endpoint(tx)[0], 'http', 'right scheme')
    is_ok(t.endpoint(tx)[1], '127.0.0.1', 'right host')
    is_ok(t.endpoint(tx)[2], 3000, 'right port')

with subtest('Simple endpoint with deactivated proxy'):
    tx = t.tx('GET', 'http://mojolicious.org')
    tx.req.via_proxy = False
    tx.req.proxy = Pyjo.URL.new('http://127.0.0.1:3000')
    is_ok(t.endpoint(tx)[0], 'http', 'right scheme')
    is_ok(t.endpoint(tx)[1], 'mojolicious.org', 'right host')
    is_ok(t.endpoint(tx)[2], 80, 'right port')

with subtest('Simple endpoint with SOCKS proxy'):
    tx = t.tx('GET', 'http://mojolicious.org')
    tx.req.proxy = Pyjo.URL.new('socks://127.0.0.1:3000')
    is_ok(t.endpoint(tx)[0], 'http', 'right scheme')
    is_ok(t.endpoint(tx)[1], 'mojolicious.org', 'right host')
    is_ok(t.endpoint(tx)[2], 80, 'right port')

with subtest('Simple WebSocket endpoint with proxy'):
    tx = t.websocket('ws://mojolicious.org')
    tx.req.proxy = Pyjo.URL.new('http://127.0.0.1:3000')
    is_ok(t.endpoint(tx)[0], 'http', 'right scheme')
    is_ok(t.endpoint(tx)[1], 'mojolicious.org', 'right host')
    is_ok(t.endpoint(tx)[2], 80, 'right port')

with subtest('HTTPS endpoint'):
    tx = t.tx('GET', 'HTTPS://mojolicious.org')
    is_ok(t.endpoint(tx)[0], 'https', 'right scheme')
    is_ok(t.endpoint(tx)[1], 'mojolicious.org', 'right host')
    is_ok(t.endpoint(tx)[2], 443, 'right port')

with subtest('HTTPS endpoint with proxy'):
    tx = t.tx('GET', 'https://mojolicious.org')
    tx.req.proxy = Pyjo.URL.new('http://127.0.0.1:3000')
    is_ok(t.endpoint(tx)[0], 'https', 'right scheme')
    is_ok(t.endpoint(tx)[1], 'mojolicious.org', 'right host')
    is_ok(t.endpoint(tx)[2], 443, 'right port')

with subtest('HTTPS endpoint with SOCKS proxy'):
    tx = t.tx('GET', 'https://mojolicious.org')
    tx.req.proxy = Pyjo.URL.new('socks://127.0.0.1:3000')
    is_ok(t.endpoint(tx)[0], 'https', 'right scheme')
    is_ok(t.endpoint(tx)[1], 'mojolicious.org', 'right host')
    is_ok(t.endpoint(tx)[2], 443, 'right port')

with subtest('TLS WebSocket endpoint with proxy'):
    tx = t.websocket('WSS://mojolicious.org')
    tx.req.proxy = Pyjo.URL.new('http://127.0.0.1:3000')
    is_ok(t.endpoint(tx)[0], 'https', 'right scheme')
    is_ok(t.endpoint(tx)[1], 'mojolicious.org', 'right host')
    is_ok(t.endpoint(tx)[2], 443, 'right port')

with subtest('Simple peer'):
    tx = t.tx('GET', 'mojolicious.org')
    is_ok(t.peer(tx)[0], 'http', 'right scheme')
    is_ok(t.peer(tx)[1], 'mojolicious.org', 'right host')
    is_ok(t.peer(tx)[2], 80, 'right port')

with subtest('Simple peer with proxy'):
    tx = t.tx('GET', 'http://mojolicious.org')
    tx.req.proxy = Pyjo.URL.new('http://127.0.0.1:3000')
    is_ok(t.peer(tx)[0], 'http', 'right scheme')
    is_ok(t.peer(tx)[1], '127.0.0.1', 'right host')
    is_ok(t.peer(tx)[2], 3000, 'right port')

with subtest('Simple peer with deactivated proxy'):
    tx = t.tx('GET', 'http://mojolicious.org')
    tx.req.via_proxy = False
    tx.req.proxy = Pyjo.URL.new('http://127.0.0.1:3000')
    is_ok(t.peer(tx)[0], 'http', 'right scheme')
    is_ok(t.peer(tx)[1], 'mojolicious.org', 'right host')
    is_ok(t.peer(tx)[2], 80, 'right port')

with subtest('Simple peer with SOCKS proxy'):
    tx = t.tx('GET', 'http://mojolicious.org')
    tx.req.proxy = Pyjo.URL.new('socks://127.0.0.1:3000')
    is_ok(t.peer(tx)[0], 'socks', 'right scheme')
    is_ok(t.peer(tx)[1], '127.0.0.1', 'right host')
    is_ok(t.peer(tx)[2], 3000, 'right port')

with subtest('Simple peer with proxy (no port)'):
    tx = t.tx('GET', 'http://mojolicious.org')
    tx.req.proxy = Pyjo.URL.new('http://127.0.0.1')
    is_ok(t.peer(tx)[0], 'http', 'right scheme')
    is_ok(t.peer(tx)[1], '127.0.0.1', 'right host')
    is_ok(t.peer(tx)[2], 80, 'right port')

with subtest('Simple peer with HTTPS proxy (no port)'):
    tx = t.tx('GET', 'http://mojolicious.org')
    tx.req.proxy = Pyjo.URL.new('HTTPS://127.0.0.1')
    is_ok(t.peer(tx)[0], 'https', 'right scheme')
    is_ok(t.peer(tx)[1], '127.0.0.1', 'right host')
    is_ok(t.peer(tx)[2], 443, 'right port')

with subtest('Simple WebSocket peer with proxy'):
    tx = t.websocket('ws://mojolicious.org')
    tx.req.proxy = Pyjo.URL.new('http://127.0.0.1:3000')
    is_ok(t.peer(tx)[0], 'http', 'right scheme')
    is_ok(t.peer(tx)[1], '127.0.0.1', 'right host')
    is_ok(t.peer(tx)[2], 3000, 'right port')

with subtest('HTTPS peer'):
    tx = t.tx('GET', 'https://mojolicious.org')
    is_ok(t.peer(tx)[0], 'https', 'right scheme')
    is_ok(t.peer(tx)[1], 'mojolicious.org', 'right host')
    is_ok(t.peer(tx)[2], 443, 'right port')

with subtest('HTTPS peer with proxy'):
    tx = t.tx('GET', 'https://mojolicious.org')
    tx.req.proxy = Pyjo.URL.new('http://127.0.0.1:3000')
    is_ok(t.peer(tx)[0], 'http', 'right scheme')
    is_ok(t.peer(tx)[1], '127.0.0.1', 'right host')
    is_ok(t.peer(tx)[2], 3000, 'right port')

with subtest('HTTPS peer with SOCKS proxy'):
    tx = t.tx('GET', 'https://mojolicious.org')
    tx.req.proxy = Pyjo.URL.new('socks://127.0.0.1:3000')
    is_ok(t.peer(tx)[0], 'socks', 'right scheme')
    is_ok(t.peer(tx)[1], '127.0.0.1', 'right host')
    is_ok(t.peer(tx)[2], 3000, 'right port')

with subtest('TLS WebSocket peer with proxy'):
    tx = t.websocket('wss://mojolicious.org')
    tx.req.proxy = Pyjo.URL.new('http://127.0.0.1:3000')
    is_ok(t.peer(tx)[0], 'http', 'right scheme')
    is_ok(t.peer(tx)[1], '127.0.0.1', 'right host')
    is_ok(t.peer(tx)[2], 3000, 'right port')

with subtest('WebSocket handshake'):
    tx = t.websocket('ws://127.0.0.1:3000/echo')
    ok(not tx.is_websocket, 'not a WebSocket')
    is_ok(str(tx.req.url.to_abs()), 'http://127.0.0.1:3000/echo', 'right URL')
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(tx.req.headers.connection, 'Upgrade', 'right "Connection" value')
    is_ok(len(b64_decode(tx.req.headers.sec_websocket_key)), 16, '16 byte "Sec-WebSocket-Key" value')
    ok(not tx.req.headers.sec_websocket_protocol, 'no "Sec-WebSocket-Protocol" header')
    ok(tx.req.headers.sec_websocket_version, 'has "Sec-WebSocket-Version" value')
    is_ok(tx.req.headers.upgrade, 'websocket', 'right "Upgrade" value')
    is_ok(t.upgrade(tx), None, 'not upgraded')
    server_handshake(tx)
    tx.res.code = 101
    tx = t.upgrade(tx)
    ok(tx.is_websocket, 'is a WebSocket')

with subtest('WebSocket handshake with header'):
    tx = t.websocket('wss://127.0.0.1:3000/echo', {'DNT': 1})
    is_ok(str(tx.req.url.to_abs()), 'https://127.0.0.1:3000/echo', 'right URL')
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(tx.req.headers.dnt, '1', 'right "DNT" value')
    is_ok(tx.req.headers.connection, 'Upgrade', 'right "Connection" value')
    is_ok(len(b64_decode(tx.req.headers.sec_websocket_key)), 16, '16 byte "Sec-WebSocket-Key" value')
    ok(not tx.req.headers.sec_websocket_protocol, 'no "Sec-WebSocket-Protocol" header')
    ok(tx.req.headers.sec_websocket_version, 'has "Sec-WebSocket-Version" value')
    is_ok(tx.req.headers.upgrade, 'websocket', 'right "Upgrade" value')

with subtest('WebSocket handshake with protocol'):
    tx = t.websocket('wss://127.0.0.1:3000/echo', ['foo'])
    is_ok(str(tx.req.url.to_abs()), 'https://127.0.0.1:3000/echo', 'right URL')
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(tx.req.headers.connection, 'Upgrade', 'right "Connection" value')
    is_ok(len(b64_decode(tx.req.headers.sec_websocket_key)), 16, '16 byte "Sec-WebSocket-Key" value')
    is_ok(tx.req.headers.sec_websocket_protocol, 'foo', 'right "Sec-WebSocket-Protocol" value')
    ok(tx.req.headers.sec_websocket_version, 'has "Sec-WebSocket-Version" value')
    is_ok(tx.req.headers.upgrade, 'websocket', 'right "Upgrade" value')

with subtest('WebSocket handshake with header and protocols'):
    tx = t.websocket('wss://127.0.0.1:3000/echo', {'DNT': 1}, ['v1.bar.example.com', 'foo', 'v2.baz.example.com'])
    is_ok(str(tx.req.url.to_abs()), 'https://127.0.0.1:3000/echo', 'right URL')
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(tx.req.headers.dnt, '1', 'right "DNT" value')
    is_ok(tx.req.headers.connection, 'Upgrade', 'right "Connection" value')
    is_ok(len(b64_decode(tx.req.headers.sec_websocket_key)), 16, '16 byte "Sec-WebSocket-Key" value')
    is_ok(
        tx.req.headers.sec_websocket_protocol,
        'v1.bar.example.com, foo, v2.baz.example.com',
        'right "Sec-WebSocket-Protocol" value',
    )
    ok(tx.req.headers.sec_websocket_version, 'has "Sec-WebSocket-Version" value')
    is_ok(tx.req.headers.upgrade, 'websocket', 'right "Upgrade" value')

with subtest('WebSocket handshake with UNIX domain socket'):
    tx = t.websocket('ws+unix://%2Ftmp%2Fmyapp.sock/echo', {'DNT': 1})
    is_ok(str(tx.req.url.to_abs()), 'http+unix://%2Ftmp%2Fmyapp.sock/echo', 'right URL')
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(tx.req.headers.dnt, '1', 'right "DNT" value')
    is_ok(tx.req.headers.connection, 'Upgrade', 'right "Connection" value')
    is_ok(len(b64_decode(tx.req.headers.sec_websocket_key)), 16, '16 byte "Sec-WebSocket-Key" value')
    ok(not tx.req.headers.sec_websocket_protocol, 'no "Sec-WebSocket-Protocol" header')
    ok(tx.req.headers.sec_websocket_version, 'has "Sec-WebSocket-Version" value')
    is_ok(tx.req.headers.upgrade, 'websocket', 'right "Upgrade" value')

with subtest('Proxy CONNECT'):
    tx = t.tx('GET', 'HTTPS://sri:secr3t@mojolicious.org')
    tx.req.proxy = Pyjo.URL.new('http://sri:secr3t@127.0.0.1:3000')
    ok(not tx.req.headers.authorization, 'no "Authorization" header')
    ok(not tx.req.headers.proxy_authorization, 'no "Proxy-Authorization" header')
    tx.req.fix_headers()
    is_ok(tx.req.headers.authorization, 'Basic c3JpOnNlY3IzdA==', 'right "Authorization" header')
    is_ok(tx.req.headers.proxy_authorization, 'Basic c3JpOnNlY3IzdA==', 'right "Proxy-Authorization" header')
    tx = t.proxy_connect(tx)
    is_ok(tx.req.method, 'CONNECT', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'https://mojolicious.org', 'right URL')
    is_ok(str(tx.req.proxy.to_abs()), 'http://127.0.0.1:3000', 'right proxy URL')
    ok(not tx.req.headers.authorization, 'no "Authorization" header')
    ok(not tx.req.headers.proxy_authorization, 'no "Proxy-Authorization" header')
    ok(not tx.req.headers.host, 'no "Host" header')
    tx.req.fix_headers()
    ok(not tx.req.headers.authorization, 'no "Authorization" header')
    is_ok(tx.req.headers.proxy_authorization, 'Basic c3JpOnNlY3IzdA==', 'right "Proxy-Authorization" header')
    is_ok(tx.req.headers.host, 'mojolicious.org', 'right "Host" header')
    is_ok(t.proxy_connect(tx), None, 'already a CONNECT request')
    tx.req.method = 'Connect'
    is_ok(t.proxy_connect(tx), None, 'already a CONNECT request')
    tx = t.tx('GET', 'https://mojolicious.org')
    tx.req.proxy = Pyjo.URL.new('socks://127.0.0.1:3000')
    is_ok(t.proxy_connect(tx), None, 'using a SOCKS proxy')
    tx = t.tx('GET', 'https://mojolicious.org')
    ok(tx.req.via_proxy, 'proxy use is enabled by default')
    tx.req.via_proxy = False
    tx.req.proxy = Pyjo.URL.new('http://127.0.0.1:3000')
    is_ok(t.proxy_connect(tx), None, 'proxy use is disabled')

with subtest('Simple 301 redirect'):
    tx = t.tx('POST', 'http://mojolicious.org/foo', {'Accept': 'application/json'})
    tx.res.code = 301
    tx.res.headers.location = 'http://example.com/bar'
    is_ok(tx.req.headers.accept, 'application/json', 'right "Accept" value')
    is_ok(tx.req.body, b'', 'no content')
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/bar', 'right URL')
    is_ok(tx.req.headers.user_agent, 'MyUA 1.0', 'right "User-Agent" value')
    is_ok(tx.req.headers.accept, 'application/json', 'right "Accept" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.body, b'', 'no content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('301 redirect with content'):
    tx = t.tx('POST', 'http://mojolicious.org/foo', {'Accept': '*/*'}, 'whatever')
    tx.res.code = 301
    tx.res.headers.location = 'http://example.com/bar'
    is_ok(tx.req.headers.accept, '*/*', 'right "Accept" value')
    is_ok(tx.req.body, b'whatever', 'right content')
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/bar', 'right URL')
    is_ok(tx.req.headers.accept, '*/*', 'right "Accept" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.body, b'', 'no content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('301 redirect with content (DELETE)'):
    tx = t.tx('DELETE', 'http://mojolicious.org/foo', {'Accept': '*/*'}, 'whatever')
    tx.res.code = 301
    tx.res.headers.location = 'http://example.com/bar'
    is_ok(tx.req.headers.accept, '*/*', 'right "Accept" value')
    is_ok(tx.req.body, b'whatever', 'right content')
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'DELETE', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/bar', 'right URL')
    is_ok(tx.req.headers.accept, '*/*', 'right "Accept" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.body, b'', 'no content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('Simple 302 redirect'):
    tx = t.tx('POST', 'http://mojolicious.org/foo', {'Accept': 'application/json'})
    tx.res.code = 302
    tx.res.headers.location = 'http://example.com/bar'
    is_ok(tx.req.headers.accept, 'application/json', 'right "Accept" value')
    is_ok(tx.req.body, b'', 'no content')
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/bar', 'right URL')
    is_ok(tx.req.headers.accept, 'application/json', 'right "Accept" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.body, b'', 'no content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('302 redirect (lowercase HEAD)'):
    tx = t.tx('head', 'http://mojolicious.org/foo')
    tx.res.code = 302
    tx.res.headers.location = 'http://example.com/bar'
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'HEAD', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/bar', 'right URL')
    is_ok(tx.req.headers.accept, None, 'no "Accept" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.body, b'', 'no content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('302 redirect (dynamic)'):
    tx = t.tx('POST', 'http://mojolicious.org/foo')
    tx.res.code = 302
    tx.res.headers.location = 'http://example.com/bar'
    tx.req.content.write_chunk(b'whatever', lambda content: content.finish())
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/bar', 'right URL')
    is_ok(tx.req.headers.accept, None, 'no "Accept" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.body, b'', 'no content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('302 redirect with content'):
    tx = t.tx('POST', 'http://mojolicious.org/foo', {'Accept': '*/*'}, 'whatever')
    tx.req.fix_headers().headers.content_type = 'text/plain'
    tx.res.code = 302
    tx.res.headers.location = 'http://example.com/bar'
    is_ok(tx.req.headers.accept, '*/*', 'right "Accept" value')
    is_ok(tx.req.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(tx.req.headers.content_length, '8', 'right "Content-Length" value')
    is_ok(tx.req.body, b'whatever', 'right content')
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/bar', 'right URL')
    is_ok(tx.req.headers.accept, '*/*', 'right "Accept" value')
    is_ok(tx.req.headers.content_type, None, 'no "Content-Type" value')
    is_ok(tx.req.headers.content_length, None, 'no "Content-Length" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.body, b'', 'no content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('Simple 303 redirect'):
    tx = t.tx('POST', 'http://mojolicious.org/foo', {'Accept': 'application/json'})
    tx.res.code = 303
    tx.res.headers.location = 'http://example.com/bar'
    is_ok(tx.req.headers.accept, 'application/json', 'right "Accept" value')
    is_ok(tx.req.body, b'', 'no content')
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/bar', 'right URL')
    is_ok(tx.req.headers.accept, 'application/json', 'right "Accept" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.body, b'', 'no content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('303 redirect (dynamic)'):
    tx = t.tx('PUT', 'http://mojolicious.org/foo')
    tx.res.code = 303
    tx.res.headers.location = 'http://example.com/bar'
    tx.req.content.write_chunk(b'whatever', lambda content: content.finish())
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/bar', 'right URL')
    is_ok(tx.req.headers.accept, None, 'no "Accept" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.body, b'', 'no content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('303 redirect (additional headers)'):
    tx = t.tx(
        'POST',
        'http://mojolicious.org/foo',
        {'Accept': 'application/json', 'Authorization': 'one', 'Cookie': 'two', 'Host': 'three', 'Referer': 'four'},
    )
    tx.res.code = 303
    tx.res.headers.location = 'http://example.com/bar'
    is_ok(tx.req.headers.accept, 'application/json', 'right "Accept" value')
    is_ok(tx.req.headers.authorization, 'one', 'right "Authorization" value')
    is_ok(tx.req.headers.cookie, 'two', 'right "Cookie" value')
    is_ok(tx.req.headers.host, 'three', 'right "Host" value')
    is_ok(tx.req.headers.referrer, 'four', 'right "Referer" value')
    is_ok(tx.req.body, b'', 'no content')
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/bar', 'right URL')
    is_ok(tx.req.headers.accept, 'application/json', 'right "Accept" value')
    is_ok(tx.req.headers.authorization, None, 'no "Authorization" value')
    is_ok(tx.req.headers.cookie, None, 'no "Cookie" value')
    is_ok(tx.req.headers.host, None, 'no "Host" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.headers.referrer, None, 'no "Referer" value')
    is_ok(tx.req.body, b'', 'no content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('Simple 307 redirect'):
    tx = t.tx('POST', 'http://mojolicious.org/foo', {'Accept': 'application/json'})
    tx.res.code = 307
    tx.res.headers.location = 'http://example.com/bar'
    is_ok(tx.req.headers.accept, 'application/json', 'right "Accept" value')
    is_ok(tx.req.body, b'', 'no content')
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/bar', 'right URL')
    is_ok(tx.req.headers.accept, 'application/json', 'right "Accept" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.body, b'', 'no content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('307 redirect with content'):
    tx = t.tx('POST', 'http://mojolicious.org/foo', {'Accept': '*/*'}, 'whatever')
    tx.res.code = 307
    tx.res.headers.location = 'http://example.com/bar'
    is_ok(tx.req.headers.accept, '*/*', 'right "Accept" value')
    is_ok(tx.req.body, b'whatever', 'right content')
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/bar', 'right URL')
    is_ok(tx.req.headers.accept, '*/*', 'right "Accept" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.body, b'whatever', 'right content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('307 redirect (dynamic)'):
    tx = t.tx('POST', 'http://mojolicious.org/foo')
    tx.res.code = 307
    tx.res.headers.location = 'http://example.com/bar'
    tx.req.content.write_chunk(b'whatever', lambda content: content.finish())
    is_ok(t.redirect(tx), None, 'unsupported redirect')

with subtest('307 redirect (additional headers)'):
    tx = t.tx(
        'POST',
        'http://mojolicious.org/foo',
        {'Accept': 'application/json', 'Authorization': 'one', 'Cookie': 'two', 'Host': 'three', 'Referer': 'four'},
    )
    tx.res.code = 307
    tx.res.headers.location = 'http://example.com/bar'
    is_ok(tx.req.headers.accept, 'application/json', 'right "Accept" value')
    is_ok(tx.req.headers.authorization, 'one', 'right "Authorization" value')
    is_ok(tx.req.headers.cookie, 'two', 'right "Cookie" value')
    is_ok(tx.req.headers.host, 'three', 'right "Host" value')
    is_ok(tx.req.headers.referrer, 'four', 'right "Referer" value')
    is_ok(tx.req.body, b'', 'no content')
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/bar', 'right URL')
    is_ok(tx.req.headers.accept, 'application/json', 'right "Accept" value')
    is_ok(tx.req.headers.authorization, None, 'no "Authorization" value')
    is_ok(tx.req.headers.cookie, None, 'no "Cookie" value')
    is_ok(tx.req.headers.host, None, 'no "Host" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.headers.referrer, None, 'no "Referer" value')
    is_ok(tx.req.body, b'', 'no content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('Simple 308 redirect'):
    tx = t.tx('POST', 'http://mojolicious.org/foo', {'Accept': 'application/json'})
    tx.res.code = 308
    tx.res.headers.location = 'http://example.com/bar'
    is_ok(tx.req.headers.accept, 'application/json', 'right "Accept" value')
    is_ok(tx.req.body, b'', 'no content')
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/bar', 'right URL')
    is_ok(tx.req.headers.accept, 'application/json', 'right "Accept" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.body, b'', 'no content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('308 redirect with content'):
    tx = t.tx('POST', 'http://mojolicious.org/foo', {'Accept': '*/*'}, 'whatever')
    tx.res.code = 308
    tx.res.headers.location = 'https://example.com/bar'
    is_ok(tx.req.headers.accept, '*/*', 'right "Accept" value')
    is_ok(tx.req.body, b'whatever', 'right content')
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'https://example.com/bar', 'right URL')
    is_ok(tx.req.headers.accept, '*/*', 'right "Accept" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.body, b'whatever', 'right content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('308 redirect (dynamic)'):
    tx = t.tx('POST', 'http://mojolicious.org/foo')
    tx.res.code = 308
    tx.res.headers.location = 'http://example.com/bar'
    tx.req.content.write_chunk(b'whatever', lambda content: content.finish())
    is_ok(t.redirect(tx), None, 'unsupported redirect')

with subtest('QUERY 301 redirect with content'):
    tx = t.tx('QUERY', 'http://mojolicious.org/foo', {'Accept': '*/*'}, 'whatever')
    tx.res.code = 301
    tx.res.headers.location = 'http://example.com/bar'
    is_ok(tx.req.headers.accept, '*/*', 'right "Accept" value')
    is_ok(tx.req.body, b'whatever', 'right content')
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'QUERY', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/bar', 'right URL')
    is_ok(tx.req.headers.accept, '*/*', 'right "Accept" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.body, b'whatever', 'right content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('QUERY 302 redirect with content'):
    tx = t.tx('QUERY', 'http://mojolicious.org/foo', {'Accept': '*/*'}, 'whatever')
    tx.res.code = 302
    tx.res.headers.location = 'http://example.com/bar'
    is_ok(tx.req.headers.accept, '*/*', 'right "Accept" value')
    is_ok(tx.req.body, b'whatever', 'right content')
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'QUERY', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/bar', 'right URL')
    is_ok(tx.req.headers.accept, '*/*', 'right "Accept" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.body, b'whatever', 'right content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('QUERY 303 redirect with content'):
    tx = t.tx('QUERY', 'http://mojolicious.org/foo', {'Accept': '*/*'}, 'whatever')
    tx.res.code = 303
    tx.res.headers.location = 'http://example.com/bar'
    is_ok(tx.req.headers.accept, '*/*', 'right "Accept" value')
    is_ok(tx.req.body, b'whatever', 'right content')
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/bar', 'right URL')
    is_ok(tx.req.headers.accept, '*/*', 'right "Accept" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.body, b'', 'no content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('QUERY 307 redirect with content'):
    tx = t.tx('QUERY', 'http://mojolicious.org/foo', {'Accept': '*/*'}, 'whatever')
    tx.res.code = 307
    tx.res.headers.location = 'http://example.com/bar'
    is_ok(tx.req.headers.accept, '*/*', 'right "Accept" value')
    is_ok(tx.req.body, b'whatever', 'right content')
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'QUERY', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/bar', 'right URL')
    is_ok(tx.req.headers.accept, '*/*', 'right "Accept" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.body, b'whatever', 'right content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('309 redirect (unsupported)'):
    tx = t.tx('POST', 'http://mojolicious.org/foo', {'Accept': 'application/json'})
    tx.res.code = 309
    tx.res.headers.location = 'http://example.com/bar'
    is_ok(tx.req.headers.accept, 'application/json', 'right "Accept" value')
    is_ok(tx.req.body, b'', 'no content')
    is_ok(t.redirect(tx), None, 'unsupported redirect')

with subtest('302 redirect with bad location'):
    tx = t.tx('GET', 'http://mojolicious.org/foo')
    tx.res.code = 302
    tx.res.headers.location = 'data:image/png;base64,helloworld123'
    is_ok(t.redirect(tx), None, 'unsupported redirect')
    tx = t.tx('GET', 'http://mojolicious.org/foo')
    tx.res.code = 302
    tx.res.headers.location = 'http:'
    is_ok(t.redirect(tx), None, 'unsupported redirect')

with subtest('302 redirect with multiple locations'):
    tx = t.tx('GET', 'http://mojolicious.org/foo')
    tx.res.code = 302
    tx.res.headers.add('Location', 'http://example.com/1.html')
    tx.res.headers.add('Location', 'http://example.com/2.html')
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/1.html', 'right URL')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.body, b'', 'no content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('302 redirect (relative path and query)'):
    tx = t.tx('POST', 'http://mojolicious.org/foo/bar?a=b', {'Accept': 'application/json'})
    tx.res.code = 302
    tx.res.headers.location = 'baz?f%23oo=bar'
    is_ok(tx.req.headers.accept, 'application/json', 'right "Accept" value')
    is_ok(tx.req.body, b'', 'no content')
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://mojolicious.org/foo/baz?f%23oo=bar', 'right URL')
    is_ok(str(tx.req.url.query), 'f%23oo=bar', 'right query')
    is_ok(tx.req.headers.accept, 'application/json', 'right "Accept" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.body, b'', 'no content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('302 redirect (absolute path and query)'):
    tx = t.tx('POST', 'http://mojolicious.org/foo/bar?a=b', {'Accept': 'application/json'})
    tx.res.code = 302
    tx.res.headers.location = '/baz?f%23oo=bar'
    is_ok(tx.req.headers.accept, 'application/json', 'right "Accept" value')
    is_ok(tx.req.body, b'', 'no content')
    tx = t.redirect(tx)
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://mojolicious.org/baz?f%23oo=bar', 'right URL')
    is_ok(str(tx.req.url.query), 'f%23oo=bar', 'right query')
    is_ok(tx.req.headers.accept, 'application/json', 'right "Accept" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.body, b'', 'no content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')

with subtest('302 redirect for CONNECT request'):
    tx = t.tx('CONNECT', 'http://mojolicious.org')
    tx.res.code = 302
    tx.res.headers.location = 'http://example.com/bar'
    is_ok(t.redirect(tx), None, 'unsupported redirect')

with subtest('301 redirect without compression'):
    t2 = Pyjo.UserAgent.Transactor.new(compressed=False)
    tx = t2.tx('POST', 'http://mojolicious.org/foo', {'Accept': 'application/json'})
    tx.res.code = 301
    tx.res.headers.location = 'http://example.com/bar'
    is_ok(tx.res.content.auto_decompress, False, 'right value')
    tx = t2.redirect(tx)
    is_ok(tx.res.content.auto_decompress, False, 'right value')
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(str(tx.req.url.to_abs()), 'http://example.com/bar', 'right URL')
    # Unlike Mojolicious: Pyjoyment names itself
    is_ok(tx.req.headers.user_agent, 'Pyjoyment (Python)', 'right "User-Agent" value')
    is_ok(tx.req.headers.accept, 'application/json', 'right "Accept" value')
    is_ok(tx.req.headers.location, None, 'no "Location" value')
    is_ok(tx.req.body, b'', 'no content')
    is_ok(tx.res.code, None, 'no status')
    is_ok(tx.res.headers.location, None, 'no "Location" value')


with subtest('Download'):
    dir = tempdir()
    no_file = dir.child('no_file')
    small_file = dir.child('small_file').spew(b'x')
    large_file = dir.child('large_file').spew(b'xxxxxxxxxxx')
    correct_file = dir.child('correct_file').spew(b'xxxxxxxxxx')
    t2 = Pyjo.UserAgent.Transactor.new()

    with subtest('Partial file exists'):
        head = t2.tx('HEAD', 'http://mojolicious.org/release.tar.gz')
        head.res.headers.content_length = '10'
        head.res.headers.accept_ranges = 'bytes'
        tx = t2.download(head, small_file)
        is_ok(tx.req.method, 'GET', 'right method')
        is_ok(str(tx.req.url.to_abs()), 'http://mojolicious.org/release.tar.gz', 'right URL')
        is_ok(tx.req.headers.range, 'bytes=1-10', 'right "Range" value')

    with subtest('Partial file exists (with headers)'):
        head = t2.tx('HEAD', 'http://mojolicious.org/release.tar.gz', {'Accept': 'application/json'})
        head.res.headers.content_length = '10'
        head.res.headers.accept_ranges = 'bytes'
        tx = t2.download(head, small_file)
        is_ok(tx.req.method, 'GET', 'right method')
        is_ok(str(tx.req.url.to_abs()), 'http://mojolicious.org/release.tar.gz', 'right URL')
        is_ok(tx.req.headers.range, 'bytes=1-10', 'right "Range" value')
        is_ok(tx.req.headers.accept, 'application/json', 'right "Accept" value')

    with subtest('Failed HEAD request'):
        head = t2.tx('HEAD', 'http://mojolicious.org/release.tar.gz')
        head.res.error = {'message': 'Failed to connect'}
        tx = t2.download(head, no_file)
        is_ok(tx.error['message'], 'Failed to connect', 'right error')

    with subtest('Empty HEAD response'):
        head = t2.tx('HEAD', 'http://mojolicious.org/release.tar.gz')
        tx = t2.download(head, no_file)
        is_ok(tx.req.method, 'GET', 'right method')
        is_ok(str(tx.req.url.to_abs()), 'http://mojolicious.org/release.tar.gz', 'right URL')
        is_ok(tx.req.headers.range, None, 'no "Range" value')

    with subtest('Empty HEAD response (file exists)'):
        head = t2.tx('HEAD', 'http://mojolicious.org/release.tar.gz')
        tx = t2.download(head, small_file)
        is_ok(tx.error['message'], 'Unknown file size', 'right error')

    with subtest('Target file does not exist'):
        head = t2.tx('HEAD', 'http://mojolicious.org/release.tar.gz')
        head.res.headers.content_length = '10'
        tx = t2.download(head, no_file)
        is_ok(tx.req.method, 'GET', 'right method')
        is_ok(str(tx.req.url.to_abs()), 'http://mojolicious.org/release.tar.gz', 'right URL')
        is_ok(tx.req.headers.range, None, 'no "Range" value')

    with subtest('Partial file exists (unsupported server)'):
        head = t2.tx('HEAD', 'http://mojolicious.org/release.tar.gz')
        head.res.headers.content_length = '10'
        tx = t2.download(head, small_file)
        is_ok(tx.error['message'], 'Server does not support partial requests', 'right error')

    with subtest('Partial file exists (larger than download)'):
        head = t2.tx('HEAD', 'http://mojolicious.org/release.tar.gz')
        head.res.headers.content_length = '10'
        head.res.headers.accept_ranges = 'bytes'
        tx = t2.download(head, large_file)
        is_ok(tx.error['message'], 'File size mismatch', 'right error')

    with subtest('Download already finished'):
        head = t2.tx('HEAD', 'http://mojolicious.org/release.tar.gz')
        head.res.headers.content_length = '10'
        head.res.headers.accept_ranges = 'bytes'
        tx = t2.download(head, correct_file)
        is_ok(tx.error['message'], 'Download complete', 'right error')

with subtest('Promisify'):
    promise = Pyjo.Promise.new()
    results, errors = [], []
    promise.then(lambda *args: results.extend(args), lambda *args: errors.extend(args))
    tx = t.tx('GET', '/')
    t.promisify(promise, tx)
    promise.wait()
    is_deeply_ok(results, [tx], 'promise resolved')
    is_deeply_ok(errors, [], 'promise not rejected')
    promise = Pyjo.Promise.new()
    results[:], errors[:] = [], []
    promise.then(lambda *args: results.extend(args), lambda *args: errors.extend(args))
    tx = t.websocket('/')
    t.promisify(promise, tx)
    promise.wait()
    is_deeply_ok(results, [], 'promise not resolved')
    is_deeply_ok(errors, ['WebSocket handshake failed'], 'promise rejected')
    promise = Pyjo.Promise.new()
    results[:], errors[:] = [], []
    promise.then(lambda *args: results.extend(args), lambda *args: errors.extend(args))
    tx = t.tx('GET', '/')
    tx.res.error = {'message': 'Premature connection close'}
    t.promisify(promise, tx)
    promise.wait()
    is_deeply_ok(results, [], 'promise not resolved')
    is_deeply_ok(errors, ['Premature connection close'], 'promise rejected')

with subtest('Abstract methods'):
    throws_ok(
        lambda: Pyjo.Transaction.new().client_read(b''),
        re.compile(r'Method "client_read" not implemented by subclass'),
        'right error',
    )
    throws_ok(
        lambda: Pyjo.Transaction.new().client_write(),
        re.compile(r'Method "client_write" not implemented by subclass'),
        'right error',
    )
    throws_ok(
        lambda: Pyjo.Transaction.new().server_read(b''),
        re.compile(r'Method "server_read" not implemented by subclass'),
        'right error',
    )
    throws_ok(
        lambda: Pyjo.Transaction.new().server_write(),
        re.compile(r'Method "server_write" not implemented by subclass'),
        'right error',
    )

done_testing()
