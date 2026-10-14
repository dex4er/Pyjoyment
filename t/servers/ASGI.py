from Pyjo.Test import *

import http.client
import importlib.util
import os
import socket
import subprocess
import sys
import tempfile
import textwrap
import time


# The servers of the dependency group "servers": uv run --only-group servers python -m Pyjo.Prove t/servers
if missing := [
    m for m in ('daphne', 'granian', 'hypercorn', 'uvicorn', 'websockets') if not importlib.util.find_spec(m)
]:
    plan(skip_all=f'needs the dependency group "servers", without {", ".join(missing)}')

from websockets.exceptions import ConnectionClosed, InvalidStatus  # noqa: E402
from websockets.sync.client import connect  # noqa: E402


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

APP = """
import Pyjo.IOLoop
import Pyjo.Server.ASGI

asgi = Pyjo.Server.ASGI.new()
asgi.unsubscribe('request')


@asgi.on('request')
def request(asgi, tx):
    path = str(tx.req.url.path)

    # WebSocket
    if tx.is_websocket:
        if path == '/reject':
            tx.res.code = 403
            return tx.resume()
        tx.on('message', lambda ws, msg: ws.finish(4000, 'Bye!') if msg == 'quit' else ws.send(f'echo: {msg}'))
        tx.res.code = 101
        return tx.resume()

    # Response given later
    if path == '/later':

        def later(loop):
            tx.res.code = 200
            tx.res.body = b'later'
            tx.resume()

        return Pyjo.IOLoop.timer(0.1, later)

    # Streaming
    if path == '/stream':
        tx.res.code = 200
        tx.res.content.write_chunk(b'Hello ')

        def more(loop):
            tx.res.content.write_chunk(b'World!').write_chunk(b'')
            tx.resume()

        Pyjo.IOLoop.timer(0.1, more)
        return tx.resume()

    tx.res.code = 200
    tx.res.headers.content_type = 'text/plain'
    tx.res.body = f'{tx.req.method} {path} {tx.req.params.to_dict()} {tx.req.body!r}'.encode()
    tx.resume()


app = asgi.to_asgi_app()
"""

LOCAL = ['--host', '127.0.0.1', '--port']
SERVERS = [
    ('uvicorn', ['uvicorn', 'app:app', '--loop', 'asyncio', '--log-level', 'warning', *LOCAL]),
    ('uvicorn on uvloop', ['uvicorn', 'app:app', '--loop', 'uvloop', '--log-level', 'warning', *LOCAL]),
    ('Hypercorn', ['hypercorn', 'app:app', '--bind']),
    ('Hypercorn on uvloop', ['hypercorn', 'app:app', '--worker-class', 'uvloop', '--bind']),
    ('Daphne', ['daphne', '-b', '127.0.0.1', 'app:app', '-p']),
    ('Granian', ['granian', '--interface', 'asgi', 'app:app', *LOCAL]),
]


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


class Server:
    def __init__(self, dir, command):
        self.port = free_port()
        port = f'127.0.0.1:{self.port}' if command[-1] == '--bind' else str(self.port)
        # The warnings of the servers and their libraries are not ours, so they are not errors there as in CI
        env = {k: v for k, v in os.environ.items() if k != 'PYTHONWARNINGS'} | {
            'PYTHONPATH': os.pathsep.join([dir, ROOT])
        }
        self.log = open(os.path.join(dir, 'server.log'), 'w+')
        self.process = subprocess.Popen(
            [sys.executable, '-m', *command, port], cwd=dir, env=env, stdout=self.log, stderr=subprocess.STDOUT
        )
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            try:
                socket.create_connection(('127.0.0.1', self.port), 0.2).close()
                return
            except OSError:
                time.sleep(0.1)
        self.close()
        raise RuntimeError(f'the server did not start: {self.output()}')

    def close(self):
        self.process.terminate()
        try:
            self.process.wait(10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()

    def output(self):
        self.log.seek(0)
        return self.log.read()

    def request(self, method, path, body=None, headers=None, chunked=False):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
        try:
            conn.request(method, path, body=body, headers=headers or {}, encode_chunked=chunked)
            res = conn.getresponse()
            return res.status, res.headers, res.read()
        finally:
            conn.close()

    def websocket(self, path):
        return connect(f'ws://127.0.0.1:{self.port}{path}', open_timeout=10, close_timeout=2)


with tempfile.TemporaryDirectory() as dir:
    with open(os.path.join(dir, 'app.py'), 'w') as file:
        file.write(textwrap.dedent(APP))

    for name, command in SERVERS:
        if 'uvloop' in name and not importlib.util.find_spec('uvloop'):
            continue

        with subtest(name):
            server = Server(dir, command)
            try:
                status, headers, body = server.request('GET', '/foo?a=1')
                is_ok(status, 200, 'right status')
                is_ok(body, b"GET /foo {'a': '1'} b''", 'right content')
                # Daphne adds no Date header, and Pyjo.Server.ASGI leaves out its own for the servers that do
                is_ok(len(headers.get_all('Date') or []), 0 if name == 'Daphne' else 1, 'one Date header at most')

                type = {'Content-Type': 'application/x-www-form-urlencoded'}
                status, headers, body = server.request('POST', '/form', b'x=1&y=2', type)
                is_ok(body, b"POST /form {'x': '1', 'y': '2'} b'x=1&y=2'", 'form')

                status, headers, body = server.request('POST', '/chunked', iter([b'x=1', b'&y=2']), type, True)
                is_ok(body, b"POST /chunked {'x': '1', 'y': '2'} b'x=1&y=2'", 'chunked request')

                status, headers, body = server.request('GET', '/later')
                is_ok(body, b'later', 'response given later')

                status, headers, body = server.request('GET', '/stream')
                is_ok(body, b'Hello World!', 'streaming')

                status, headers, body = server.request('HEAD', '/foo')
                is_ok(status, 200, 'HEAD request')
                is_ok(body, b'', 'no content')

                with server.websocket('/ws') as ws:
                    ws.send('hi')
                    is_ok(ws.recv(10), 'echo: hi', 'WebSocket message')
                    ws.send('quit')

                    # Granian does not deliver the websocket.close of the application while a receive is waiting
                    if name == 'Granian':
                        throws_ok(lambda: ws.recv(2), TimeoutError, 'close not delivered')
                    else:
                        try:
                            ws.recv(10)
                            fail_ok('closed by the application')
                        except ConnectionClosed as e:
                            is_ok(e.rcvd.code if e.rcvd else None, 4000, 'closed by the application')
                            # Daphne sends no reason with a close code
                            is_ok(e.rcvd.reason if e.rcvd else None, '' if name == 'Daphne' else 'Bye!', 'reason')

                def reject(server=server):
                    with server.websocket('/reject'):
                        pass

                throws_ok(reject, InvalidStatus, 'rejected handshake')
            except Exception:
                diag(server.output())
                raise
            finally:
                server.close()

done_testing()
