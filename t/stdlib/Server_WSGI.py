import Pyjo.IOLoop
import Pyjo.Server.WSGI

from Pyjo.Test import *

import io
import wsgiref.util
import wsgiref.validate


wsgi = Pyjo.Server.WSGI.new()
wsgi.unsubscribe('request')


@wsgi.on('request')
def request(wsgi, tx):
    path = str(tx.req.url.path)
    tx.res.code = 200
    tx.res.headers.content_type = 'text/plain'
    if path == '/stream':
        tx.res.content.write_chunk(b'Hello ')
        Pyjo.IOLoop.timer(0.05, lambda loop: tx.res.content.write_chunk(b'World!').write_chunk(b''))
    else:
        tx.res.body = f'{tx.req.method} {tx.req.url.path} {tx.req.params.to_dict()} {tx.req.body!r}'.encode()
    tx.resume()


# The application checked by the validator of PEP 3333
app = wsgiref.validate.validator(wsgi.to_wsgi_app())


def run(method='GET', path='/', body=b'', **environ):
    environ = {
        'REQUEST_METHOD': method,
        'SCRIPT_NAME': '',
        'QUERY_STRING': '',
        'PATH_INFO': path,
        'wsgi.input': io.BytesIO(body),
        **environ,
    }
    wsgiref.util.setup_testing_defaults(environ)
    got = {}

    def start_response(status, headers, exc_info=None):
        got['status'], got['headers'] = status, headers

    result = app(environ, start_response)
    try:
        got['body'] = b''.join(result)
    finally:
        result.close()
    return got


with subtest('GET request'):
    got = run('GET', '/foo', QUERY_STRING='a=1')
    is_ok(got['status'], '200 OK', 'right status')
    is_ok(got['body'], b"GET /foo {'a': '1'} b''", 'right content')

with subtest('Form'):
    got = run(
        'POST',
        '/form',
        b'x=1&y=2',
        CONTENT_TYPE='application/x-www-form-urlencoded',
        CONTENT_LENGTH='7',
    )
    is_ok(got['body'], b"POST /form {'x': '1', 'y': '2'} b'x=1&y=2'", 'read with read()')

with subtest('Request body of unknown length'):
    got = run(
        'POST',
        '/form',
        b'x=1&y=2',
        CONTENT_TYPE='application/x-www-form-urlencoded',
        HTTP_TRANSFER_ENCODING='chunked',
        **{'wsgi.input_terminated': True},
    )
    is_ok(got['body'], b"POST /form {'x': '1', 'y': '2'} b'x=1&y=2'", 'read until the end of the input')

with subtest('Chunked content given later, without hop-by-hop headers'):
    got = run('GET', '/stream')
    names = [name.lower() for name, value in got['headers']]
    ok('transfer-encoding' not in names and 'connection' not in names, 'no hop-by-hop headers')
    is_ok(got['body'], b'Hello World!', 'content without framing')

with subtest('Path of bytes as the characters 0-255'):
    got = run('GET', '/caf\xc3\xa9')
    is_ok(got['body'], b"GET /caf%C3%A9 {} b''", 'right path')

done_testing()
