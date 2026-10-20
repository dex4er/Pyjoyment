import Pyjo.Server.Prethread

from Pyjo.File import tempdir
from Pyjo.Test import *

import contextlib
import http.client
import importlib
import io
import os
import signal
import subprocess
import sys
import tempfile


ROOT = os.path.join(os.path.dirname(__file__), '..', '..')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
ServerStart = importlib.import_module('ServerStart')


# A server in a process of its own, with the code for a port, which answers once its port accepts connections, started
# again on a new port when it is taken
def server(code):
    def start():
        port = ServerStart.port()
        # A group of its own on Windows, which Ctrl-Break reaches
        process = subprocess.Popen(
            [sys.executable, '-c', code(port)],
            env=dict(os.environ, PYTHONPATH=ROOT),
            stdout=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0,
        )
        if ServerStart.listening(port, process):
            return port, process
        process.stdout.close()
        return None

    return ServerStart.retry(start)


def get(port, path):
    conn = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
    conn.request('GET', path)
    body = conn.getresponse().read()
    conn.close()
    return body


with subtest('Synopsis'):
    pid_file = tempdir().child('prethread.pid')
    port, process = server(
        lambda port: (
            f"""
import Pyjo.Server.Prethread

prethread = Pyjo.Server.Prethread.new(listen=['http://*:{port}'])
prethread.pid_file = {str(pid_file)!r}
prethread.workers = 2


@prethread.unsubscribe('request').on('request')
def request(prethread, tx):
    # Request
    method = tx.req.method
    path = tx.req.url.path

    # Response
    tx.res.code = 200
    tx.res.headers.content_type = 'text/plain'
    tx.res.body = f'{{method}} request for {{path}}!'.encode()

    # Resume transaction
    tx.resume()


prethread.run()
"""
        )
    )
    is_ok(get(port, '/foo'), b'GET request for /foo!', 'served by a worker')
    # TERM of Windows terminates the process, and Ctrl-Break stops the server, immediately
    process.send_signal(signal.CTRL_BREAK_EVENT if sys.platform == 'win32' else signal.SIGTERM)
    is_ok(process.wait(30), 0, 'stopped gracefully')
    like_ok(process.stdout.read(), rf'Web application available at http://127.0.0.1:{port}', 'listening')
    process.stdout.close()

with subtest('Events'):
    prethread = Pyjo.Server.Prethread.new(
        heartbeat_interval=0.1,
        listen=['http://127.0.0.1'],
        pid_file=tempdir().child('prethread.pid'),
        silent=True,
        workers=1,
    )
    prethread.on('spawn', lambda prethread, id: print(f'Worker {id} started'))

    @prethread.once('heartbeat')
    def heartbeat(prethread, id):
        signal.raise_signal(signal.SIGTERM)

    prethread.app.log.level = 'fatal'
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        prethread.run()
    like_ok(output.getvalue(), r'^Worker \d+ started\n$', 'emitted with the id of the thread')
    isnt_ok(output.getvalue(), f'Worker {os.getpid()} started\n', 'not the process id')

with subtest('new'):
    prethread = Pyjo.Server.Prethread.new()
    isa_ok(prethread, Pyjo.Server.Prethread.object, 'prethread')
    prethread = Pyjo.Server.Prethread.new(listen=['http://*:8080'], workers=10)
    is_ok(prethread.workers, 10, 'workers')
    is_ok(prethread.pid_file, os.path.join(tempfile.gettempdir(), 'prethread.pid'), 'default of pid_file')

done_testing()
