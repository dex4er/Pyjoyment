from Pyjo.Test import *

import http.server
import importlib
import os
import shutil
import sys
import tempfile
import textwrap


# The servers of the dependency group "servers": uv run --only-group servers python -m Pyjo.Prove t/servers
PYTHON = sys.executable
UWSGI = shutil.which('uwsgi', path=os.path.dirname(sys.executable))
# Python 3.15 has no CGI server of its own any more, and for root, http.server runs the script as nobody, who cannot
# read the temporary directory
HTTP_SERVER = hasattr(http.server, 'CGIHTTPRequestHandler') and hasattr(os, 'geteuid') and os.geteuid() != 0
if not UWSGI:
    plan(skip_all='needs the dependency group "servers", without uwsgi')

# The servers in processes of their own
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
Server = importlib.import_module('ServerProcess').Server

# A CGI script runs as a program of its own, with the Python of the tests
APP = f"""#!{PYTHON}
import Pyjo.IOLoop
import Pyjo.Server.CGI

cgi = Pyjo.Server.CGI.new()
cgi.unsubscribe('request')


@cgi.on('request')
def request(cgi, tx):
    path = str(tx.req.url.path)

    # Status
    if path == 'created':
        tx.res.code = 201
        return tx.resume()

    # Chunked content
    if path == 'stream':
        tx.res.code = 200
        tx.res.content.write_chunk(b'Hello ').write_chunk(b'World!').write_chunk(b'')
        return tx.resume()

    # Content given later
    if path == 'later':
        tx.res.code = 200
        tx.res.content.write_chunk(b'Hello ')

        def more(loop):
            tx.res.content.write_chunk(b'World!').write_chunk(b'')

        Pyjo.IOLoop.timer(0.1, more)
        return tx.resume()

    # Dynamic content
    if path == 'dynamic':
        tx.res.code = 200
        tx.res.content.write(b'Hello ', lambda content, offset: content.write(b'World!').write(b''))
        return tx.resume()

    tx.res.code = 200
    tx.res.headers.content_type = 'text/plain'
    url = tx.req.url
    tx.res.body = f'{{tx.req.method}} {{url.base.path}} {{url.path}} {{tx.req.params.to_dict()}} {{tx.req.body!r}}'.encode()
    tx.resume()


cgi.run()
"""

SERVERS = [
    ('http.server', HTTP_SERVER, [PYTHON, '-m', 'http.server', '--cgi', '--bind', '127.0.0.1', '{port}']),
    (
        'uWSGI',
        UWSGI,
        [UWSGI, '--http-socket', '127.0.0.1:{port}', '--http-socket-modifier1', '9', '--cgi', '/cgi-bin={dir}/cgi-bin'],
    ),
]


with tempfile.TemporaryDirectory() as dir:
    os.mkdir(os.path.join(dir, 'cgi-bin'))
    script = os.path.join(dir, 'cgi-bin', 'app.py')
    with open(script, 'w') as file:
        file.write(textwrap.dedent(APP))
    os.chmod(script, 0o755)

    for name, available, command in SERVERS:
        if not available:
            continue

        with subtest(name):
            server = Server(dir, [arg.replace('{dir}', dir) for arg in command])
            try:
                status, headers, body = server.request('GET', '/cgi-bin/app.py/foo?a=1')
                is_ok(status, 200, 'right status')
                is_ok(body, b"GET /cgi-bin/app.py/ foo {'a': '1'} b''", 'right content')
                # http.server sends the output of the script as it is, after a status line and headers of its own
                if name == 'http.server':
                    is_ok(headers.get_all('Status'), ['200 OK'], 'Status header of the script')
                    is_ok(len(headers.get_all('Date') or []), 2, 'Date headers of the server and of the script')
                else:
                    is_ok(headers.get_all('Status'), None, 'no Status header')
                    is_ok(len(headers.get_all('Date') or []), 1, 'one Date header')

                # http.server always sends 200
                status, headers, body = server.request('GET', '/cgi-bin/app.py/created')
                is_ok(status, 200 if name == 'http.server' else 201, 'status of the script')

                type = {'Content-Type': 'application/x-www-form-urlencoded'}
                status, headers, body = server.request('POST', '/cgi-bin/app.py/form', b'x=1&y=2', type)
                is_ok(body, b"POST /cgi-bin/app.py/ form {'x': '1', 'y': '2'} b'x=1&y=2'", 'form')

                status, headers, body = server.request('GET', '/cgi-bin/app.py/stream')
                is_ok(body, b'Hello World!', 'chunked content')

                status, headers, body = server.request('GET', '/cgi-bin/app.py/later')
                is_ok(body, b'Hello World!', 'content given later')

                status, headers, body = server.request('GET', '/cgi-bin/app.py/dynamic')
                is_ok(body, b'Hello World!', 'dynamic content')

                status, headers, body = server.request('HEAD', '/cgi-bin/app.py/foo')
                is_ok(status, 200, 'HEAD request')
                is_ok(body, b'', 'no content')

                status, headers, body = server.request('GET', '/cgi-bin/app.py/caf%C3%A9/a%20b')
                is_ok(body, b"GET /cgi-bin/app.py/ caf%C3%A9/a%20b {} b''", 'path with UTF-8')

                # A chunked request has no CONTENT_LENGTH: http.server passes no request body to the script, and
                # uWSGI does not answer, which holds its only worker, so this request is the last one
                def chunked(server=server, type=type, timeout=10):
                    return server.request(
                        'POST', '/cgi-bin/app.py/chunked', iter([b'x=1', b'&y=2']), type, True, timeout
                    )

                if name == 'uWSGI':
                    throws_ok(lambda: chunked(timeout=2), TimeoutError, 'chunked request not answered')
                else:
                    status, headers, body = chunked()
                    is_ok(body, b"POST /cgi-bin/app.py/ chunked {} b''", 'chunked request without body')
            except Exception:
                diag(server.output())
                raise
            finally:
                server.close()

done_testing()
