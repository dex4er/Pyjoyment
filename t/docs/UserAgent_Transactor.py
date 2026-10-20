from Pyjo.File import tempdir
from Pyjo.Test import *

import io

from contextlib import redirect_stdout


with subtest('Synopsis'):
    from Pyjo.UserAgent.Transactor import Transactor

    # GET request with Accept header
    t = Transactor()
    like_ok(
        t.tx('GET', 'http://example.com', {'Accept': '*/*'}).req.to_bytes(),
        rb'^GET / HTTP/1\.1\r\nAccept: \*/\*\r\n',
        'print(...)',
    )

    # Or import the module, as in Google Python Style Guide
    import Pyjo.UserAgent.Transactor

    # GET request with Accept header
    t = Pyjo.UserAgent.Transactor.new()
    like_ok(
        t.tx('GET', 'http://example.com', {'Accept': '*/*'}).req.to_bytes(),
        rb'^GET / HTTP/1\.1\r\nAccept: \*/\*\r\n',
        'print(...)',
    )

    # POST request with form-data
    like_ok(t.tx('POST', 'example.com', form={'a': 'b'}).req.to_bytes(), rb'\r\n\r\na=b$', 'print(...)')

    # PUT request with JSON data
    like_ok(t.tx('PUT', 'example.com', json={'a': 'b'}).req.to_bytes(), rb'\r\n\r\n\{"a":"b"\}$', 'print(...)')

with subtest('Generators'):
    tx = t.tx('POST', 'http://example.com', form={'a': 'b'})
    is_ok(tx.req.body, b'a=b', 'form')
    tx = t.tx('PATCH', 'http://example.com', json={'a': 'b'})
    is_ok(tx.req.body, b'{"a":"b"}', 'json')
    tx = t.tx('PUT', 'http://example.com', multipart=['Hello', 'World!'])
    is_deeply_ok([part.asset.slurp() for part in tx.req.content.parts], [b'Hello', b'World!'], 'multipart')

with subtest('new'):
    t = Pyjo.UserAgent.Transactor.new()
    ok(t.compressed, 't')
    t = Pyjo.UserAgent.Transactor.new(compressed=False)
    ok(not t.compressed, 't.compressed')

with subtest('compressed'):
    boolean = t.compressed
    is_ok(boolean, False, 'boolean')
    t.compressed = True
    is_ok(t.compressed, True, 't.compressed')

with subtest('generators'):
    generators = t.generators
    is_deeply_ok(sorted(generators), ['form', 'json', 'multipart'], 'generators')
    t.generators = {'foo': lambda t, tx, *args, **options: ...}
    is_deeply_ok(sorted(t.generators), ['foo'], 't.generators')

with subtest('name'):
    name = t.name
    is_ok(name, 'Pyjoyment (Python)', 'name')
    t.name = 'Pyjoyment'
    is_ok(t.name, 'Pyjoyment', 't.name')

with subtest('add_generator'):
    t = Pyjo.UserAgent.Transactor.new()
    is_ok(t.add_generator('foo', lambda t, tx, *args, **options: ...), t, 't')

    def foo(t, tx, data, **options):
        tx.req.body = data

    t.add_generator('foo', foo)
    is_ok(t.tx('PUT', 'http://example.com', foo=b'bar').req.body, b'bar', 'foo')

with subtest('download'):
    import Pyjo.Transaction.HTTP

    tx = t.download(Pyjo.Transaction.HTTP.new(), tempdir().child('test.tar.gz'))
    is_ok(tx.req.method, 'GET', 'tx')

with subtest('endpoint'):
    proto, host, port = t.endpoint(Pyjo.Transaction.HTTP.new())
    is_deeply_ok((proto, host, port), ('http', None, 80), 'proto, host, port')

with subtest('peer'):
    proto, host, port = t.peer(Pyjo.Transaction.HTTP.new())
    is_deeply_ok((proto, host, port), ('http', None, 80), 'proto, host, port')

with subtest('promisify'):
    import Pyjo.Promise

    promise = Pyjo.Promise.new()
    t.promisify(promise, Pyjo.Transaction.HTTP.new())
    results = []
    promise.then(lambda tx: results.append(tx)).wait()
    is_ok(len(results), 1, 'resolved')

with subtest('proxy_connect'):
    tx = t.proxy_connect(Pyjo.Transaction.HTTP.new())
    is_ok(tx, None, 'tx')

with subtest('redirect'):
    tx = t.redirect(Pyjo.Transaction.HTTP.new())
    is_ok(tx, None, 'tx')

with subtest('tx'):
    tx = t.tx('GET', 'example.com')
    is_ok(str(tx.req.url), 'http://example.com', 'tx')
    tx = t.tx('POST', 'http://example.com')
    is_ok(tx.req.method, 'POST', 'tx')
    tx = t.tx('GET', 'http://example.com', {'Accept': '*/*'})
    is_ok(tx.req.headers.accept, '*/*', 'tx')
    tx = t.tx('PUT', 'http://example.com', b'Content!')
    is_ok(tx.req.body, b'Content!', 'tx')
    tx = t.tx('PUT', 'http://example.com', form={'a': 'b'})
    is_ok(tx.req.body, b'a=b', 'tx')
    tx = t.tx('PUT', 'http://example.com', json={'a': 'b'})
    is_ok(tx.req.body, b'{"a":"b"}', 'tx')
    tx = t.tx('PUT', 'https://example.com', multipart=['a', 'b'])
    is_ok(len(tx.req.content.parts), 2, 'tx')
    tx = t.tx('POST', 'example.com', {'Accept': '*/*'}, b'Content!')
    is_ok(tx.req.body, b'Content!', 'tx')
    tx = t.tx('PUT', 'example.com', {'Accept': '*/*'}, form={'a': 'b'})
    is_ok(tx.req.body, b'a=b', 'tx')
    tx = t.tx('PUT', 'example.com', {'Accept': '*/*'}, json={'a': 'b'})
    is_ok(tx.req.body, b'{"a":"b"}', 'tx')
    tx = t.tx('PUT', 'example.com', {'Accept': '*/*'}, multipart=['a', 'b'])
    is_ok(len(tx.req.content.parts), 2, 'tx')

    # Generate and inspect custom GET request with DNT header and content
    with redirect_stdout(io.StringIO()) as stdout:
        print(t.tx('GET', 'example.com', {'DNT': 1}, b'Bye!').req.to_bytes())
    like_ok(stdout.getvalue(), r'DNT: 1\\r\\n.*Bye!', 'print(...)')

    # Stream response content to STDOUT
    tx = t.tx('GET', 'http://example.com')
    with redirect_stdout(io.StringIO()) as stdout:
        tx.res.content.unsubscribe('read').on('read', lambda content, chunk: print(chunk))
        tx.res.parse(b'HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nHello')
    is_ok(stdout.getvalue(), "b'Hello'\n", 'print(chunk)')

    # PUT request with content streamed from file
    import Pyjo.Asset.File

    tx = t.tx('PUT', 'http://example.com')
    tx.req.content.asset = Pyjo.Asset.File.new(path='/foo.txt')
    is_ok(tx.req.content.asset.path, '/foo.txt', 'asset')

    # POST request with "application/json" content
    tx = t.tx('POST', 'http://example.com', json={'a': 'b', 'c': [1, 2, 3]})
    is_deeply_ok(tx.req.json(), {'a': 'b', 'c': [1, 2, 3]}, 'json')

    # GET request with query parameters
    tx = t.tx('GET', 'http://example.com', form={'a': 'b'})
    is_ok(str(tx.req.url), 'http://example.com?a=b', 'query')

    # POST request with "application/x-www-form-urlencoded" content
    tx = t.tx('POST', 'http://example.com', form={'a': 'b', 'c': 'd'})
    is_ok(tx.req.body, b'a=b&c=d', 'form')

    # PUT request with Shift_JIS encoded form values
    tx = t.tx('PUT', 'example.com', form={'a': 'b'}, charset='Shift_JIS')
    is_ok(tx.req.body, b'a=b', 'charset')

    # POST request with form values sharing the same name
    tx = t.tx('POST', 'http://example.com', form={'a': ['b', 'c', 'd']})
    is_ok(tx.req.body, b'a=b&a=c&a=d', 'same name')

    # POST request with "multipart/form-data" content
    tx = t.tx('POST', 'http://example.com', form={'mytext': {'content': 'lala'}})
    is_ok(tx.req.headers.content_type, 'multipart/form-data', 'multipart/form-data')

    # POST request with multiple files sharing the same name
    tx = t.tx('POST', 'http://example.com', form={'mytext': [{'content': 'first'}, {'content': 'second'}]})
    is_ok(len(tx.req.content.parts), 2, 'files')

    # POST request with upload streamed from file
    file = tempdir().child('foo.txt').spew(b'lalala')
    tx = t.tx('POST', 'http://example.com', form={'mytext': {'file': file.to_str()}})
    is_ok(tx.req.content.parts[0].asset.slurp(), b'lalala', 'file')

    # POST request with upload streamed from asset
    import Pyjo.Asset.Memory

    asset = Pyjo.Asset.Memory.new().add_chunk(b'lalala')
    tx = t.tx('POST', 'http://example.com', form={'mytext': {'file': asset}})
    is_ok(tx.req.content.parts[0].asset, asset, 'asset')

    # POST request with form values and customized upload (filename and header)
    tx = t.tx(
        'POST',
        'http://example.com',
        form={
            'a': 'b',
            'c': 'd',
            'mytext': {'content': 'lalala', 'filename': 'foo.txt', 'Content-Type': 'text/plain'},
        },
    )
    is_ok(tx.req.upload('mytext').filename, 'foo.txt', 'filename')
    is_ok(tx.req.upload('mytext').headers.content_type, 'text/plain', 'header')

    # Force "multipart/form-data"
    headers = {'Content-Type': 'multipart/form-data'}
    tx = t.tx('POST', 'example.com', headers, form={'a': 'b'})
    is_ok(tx.req.param('a'), 'b', 'forced')

    # POST request with multipart content ("foo" and "bar")
    tx = t.tx('POST', 'http://example.com', multipart=['foo', 'bar'])
    is_deeply_ok([part.asset.slurp() for part in tx.req.content.parts], [b'foo', b'bar'], 'multipart')

    # POST request with multipart content streamed from file
    tx = t.tx('POST', 'http://example.com', multipart=[{'file': file.to_str()}])
    ok(tx.req.content.parts[0].asset.is_file, 'file')

    # PUT request with multipart content streamed from asset
    headers = {'Content-Type': 'multipart/custom'}
    asset = Pyjo.Asset.Memory.new().add_chunk(b'lalala')
    tx = t.tx('PUT', 'http://example.com', headers, multipart=[{'file': asset}])
    is_ok(tx.req.headers.content_type, 'multipart/custom', 'custom')

    # POST request with multipart content and custom headers
    tx = t.tx(
        'POST',
        'http://example.com',
        multipart=[
            {'content': 'Hello', 'Content-Type': 'text/plain', 'Content-Language': 'en-US'},
            {'content': 'World!', 'Content-Type': 'text/plain', 'Content-Language': 'en-US'},
        ],
    )
    is_deeply_ok([part.headers.content_language for part in tx.req.content.parts], ['en-US', 'en-US'], 'custom headers')

with subtest('upgrade'):
    tx = t.upgrade(Pyjo.Transaction.HTTP.new())
    is_ok(tx, None, 'tx')

with subtest('websocket'):
    tx = t.websocket('ws://example.com')
    is_ok(tx.req.headers.upgrade, 'websocket', 'tx')
    tx = t.websocket('ws://example.com', {'DNT': 1}, ['v1.proto'])
    is_ok(tx.req.headers.sec_websocket_protocol, 'v1.proto', 'tx')

done_testing()
