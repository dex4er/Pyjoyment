from Pyjo.Test import *

import importlib
import importlib.util
import os
import shutil
import sys
import tempfile
import textwrap


# The servers of the dependency group "servers": uv run --only-group servers python -m Pyjo.Prove t/servers
if missing := [m for m in ('waitress',) if not importlib.util.find_spec(m)]:
    plan(skip_all=f'needs the dependency group "servers", without {", ".join(missing)}')

# The servers in processes of their own
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
Server = importlib.import_module('ServerProcess').Server

APP = """
import Pyjo.IOLoop
import Pyjo.Server.WSGI

wsgi = Pyjo.Server.WSGI.new()
wsgi.unsubscribe('request')


@wsgi.on('request')
def request(wsgi, tx):
    path = str(tx.req.url.path)

    # Chunked content
    if path == '/stream':
        tx.res.code = 200
        tx.res.content.write_chunk(b'Hello ').write_chunk(b'World!').write_chunk(b'')
        return tx.resume()

    # Content given later
    if path == '/later':
        tx.res.code = 200
        tx.res.content.write_chunk(b'Hello ')

        def more(loop):
            tx.res.content.write_chunk(b'World!').write_chunk(b'')

        Pyjo.IOLoop.timer(0.1, more)
        return tx.resume()

    # Dynamic content
    if path == '/dynamic':
        tx.res.code = 200
        tx.res.content.write(b'Hello ', lambda content, offset: content.write(b'World!').write(b''))
        return tx.resume()

    tx.res.code = 200
    tx.res.headers.content_type = 'text/plain'
    tx.res.body = f'{tx.req.method} {tx.req.url.path} {tx.req.params.to_dict()} {tx.req.body!r}'.encode()
    tx.resume()


app = wsgi.to_wsgi_app()
"""

PYTHON = sys.executable
UWSGI = shutil.which('uwsgi', path=os.path.dirname(sys.executable))
SERVERS = [
    (
        'Gunicorn',
        importlib.util.find_spec('gunicorn'),
        [PYTHON, '-m', 'gunicorn', 'app:app', '--bind', '127.0.0.1:{port}'],
    ),
    ('uWSGI', UWSGI, [UWSGI, '--http-socket', '127.0.0.1:{port}', '--module', 'app:app']),
    ('Waitress', True, [PYTHON, '-m', 'waitress', '--listen=127.0.0.1:{port}', 'app:app']),
]


with tempfile.TemporaryDirectory() as dir:
    with open(os.path.join(dir, 'app.py'), 'w') as file:
        file.write(textwrap.dedent(APP))

    for name, available, command in SERVERS:
        if not available:
            continue

        with subtest(name):
            server = Server(dir, command)
            try:
                status, headers, body = server.request('GET', '/foo?a=1')
                is_ok(status, 200, 'right status')
                is_ok(body, b"GET /foo {'a': '1'} b''", 'right content')
                is_ok(len(headers.get_all('Date') or []), 1, 'one Date header')

                type = {'Content-Type': 'application/x-www-form-urlencoded'}
                status, headers, body = server.request('POST', '/form', b'x=1&y=2', type)
                is_ok(body, b"POST /form {'x': '1', 'y': '2'} b'x=1&y=2'", 'form')

                # uWSGI with --http-socket does not read a chunked request body for the application
                status, headers, body = server.request('POST', '/chunked', iter([b'x=1', b'&y=2']), type, True)
                expected = (
                    b"POST /chunked {} b''" if name == 'uWSGI' else b"POST /chunked {'x': '1', 'y': '2'} b'x=1&y=2'"
                )
                is_ok(body, expected, 'chunked request')

                status, headers, body = server.request('GET', '/stream')
                is_ok(body, b'Hello World!', 'chunked content')

                status, headers, body = server.request('GET', '/later')
                is_ok(body, b'Hello World!', 'content given later')

                status, headers, body = server.request('GET', '/dynamic')
                is_ok(body, b'Hello World!', 'dynamic content')

                status, headers, body = server.request('HEAD', '/foo')
                is_ok(status, 200, 'HEAD request')
                is_ok(body, b'', 'no content')

                status, headers, body = server.request('GET', '/caf%C3%A9/a%20b')
                is_ok(body, b"GET /caf%C3%A9/a%20b {} b''", 'path with UTF-8')
            except Exception:
                diag(server.output())
                raise
            finally:
                server.close()

done_testing()
