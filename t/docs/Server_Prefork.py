from Pyjo.Test import *

import contextlib
import http.client
import importlib
import io
import os
import signal
import subprocess
import sys


if not hasattr(os, 'fork'):
    plan(skip_all='no os.fork')

# PyPy with its JIT on macOS: the child of a fork crashes now and then with a bus error, under load
if sys.platform == 'darwin' and getattr(sys, 'pypy_translation_info', {}).get('translation.jit'):
    plan(skip_all='PyPy with its JIT on macOS: the child of a fork crashes now and then with SIGBUS')

import Pyjo.IOLoop.Server
import Pyjo.Server.Prefork

from Pyjo.File import tempdir


ROOT = os.path.join(os.path.dirname(__file__), '..', '..')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
ServerStart = importlib.import_module('ServerStart')


# A server in a process of its own, with the code for a port, which answers once its port accepts connections, started
# again on a new port when it is taken
def server(code):
    def start():
        port = ServerStart.port()
        process = subprocess.Popen(
            [sys.executable, '-c', code(port)], env=dict(os.environ, PYTHONPATH=ROOT), stdout=subprocess.PIPE, text=True
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
    pid_file = tempdir().child('prefork.pid')
    port, process = server(
        lambda port: (
            f"""
from Pyjo.Server.Prefork import Prefork

prefork = Prefork(listen=['http://*:{port}'])
prefork.pid_file = {str(pid_file)!r}
prefork.workers = 2


@prefork.unsubscribe('request').on('request')
def request(prefork, tx):
    # Request
    method = tx.req.method
    path = tx.req.url.path

    # Response
    tx.res.code = 200
    tx.res.headers.content_type = 'text/plain'
    tx.res.body = f'{{method}} request for {{path}}!'.encode()

    # Resume transaction
    tx.resume()


prefork.run()
"""
        )
    )
    is_ok(get(port, '/foo'), b'GET request for /foo!', 'served by a worker')
    process.send_signal(signal.SIGTERM)
    is_ok(process.wait(30), 0, 'stopped gracefully')
    like_ok(process.stdout.read(), rf'Web application available at http://127.0.0.1:{port}', 'listening')
    process.stdout.close()

    # Or import the module, as in Google Python Style Guide

    pid_file = tempdir().child('prefork.pid')
    port, process = server(
        lambda port: (
            f"""
import Pyjo.Server.Prefork

prefork = Pyjo.Server.Prefork.new(listen=['http://*:{port}'])
prefork.pid_file = {str(pid_file)!r}
prefork.workers = 2


@prefork.unsubscribe('request').on('request')
def request(prefork, tx):
    # Request
    method = tx.req.method
    path = tx.req.url.path

    # Response
    tx.res.code = 200
    tx.res.headers.content_type = 'text/plain'
    tx.res.body = f'{{method}} request for {{path}}!'.encode()

    # Resume transaction
    tx.resume()


prefork.run()
"""
        )
    )
    is_ok(get(port, '/foo'), b'GET request for /foo!', 'served by a worker')
    process.send_signal(signal.SIGTERM)
    is_ok(process.wait(30), 0, 'stopped gracefully')
    like_ok(process.stdout.read(), rf'Web application available at http://127.0.0.1:{port}', 'listening')
    process.stdout.close()


# A server that stops after the first heartbeat, with the events of the documentation
def once(prefork):
    @prefork.once('heartbeat')
    def heartbeat(prefork, pid):
        os.kill(os.getpid(), signal.SIGTERM)

    prefork.app.log.level = 'fatal'
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        prefork.run()
    return output.getvalue()


def new(**kwargs):
    port = ServerStart.port()
    return Pyjo.Server.Prefork.new(
        heartbeat_interval=0.1,
        listen=[f'http://127.0.0.1:{port}'],
        pid_file=tempdir().child('prefork.pid'),
        silent=True,
        workers=1,
        **kwargs,
    )


with subtest('finish'):
    prefork = new()
    prefork.on('finish', lambda prefork, graceful: ...)
    prefork.on('finish', lambda prefork, graceful: print('Graceful server shutdown' if graceful else 'Server shutdown'))
    is_ok(once(prefork), 'Graceful server shutdown\n', 'emitted')

with subtest('heartbeat'):
    prefork = new()
    prefork.on('heartbeat', lambda prefork, pid: ...)
    prefork.on('heartbeat', lambda prefork, pid: print(f'Worker {pid} has a heartbeat'))
    like_ok(once(prefork), r'^Worker \d+ has a heartbeat\n', 'emitted')

with subtest('reap'):
    prefork = new()
    prefork.on('reap', lambda prefork, pid: ...)
    prefork.on('reap', lambda prefork, pid: print(f'Worker {pid} stopped'))
    like_ok(once(prefork), r'^Worker \d+ stopped\n$', 'emitted')

with subtest('spawn'):
    prefork = new()
    prefork.on('spawn', lambda prefork, pid: ...)
    prefork.on('spawn', lambda prefork, pid: print(f'Worker {pid} started'))
    like_ok(once(prefork), r'^Worker \d+ started\n$', 'emitted')

with subtest('wait'):
    prefork = new()
    prefork.on('wait', lambda prefork: ...)
    prefork.on('wait', lambda prefork: print(f'Waiting for heartbeat messages from {prefork.workers} workers'))
    like_ok(once(prefork), r'^Waiting for heartbeat messages from 1 workers\n', 'emitted')

with subtest('new'):
    prefork = Pyjo.Server.Prefork.new()
    isa_ok(prefork, Pyjo.Server.Prefork.object, 'prefork')
    prefork = Pyjo.Server.Prefork.new(listen=['http://*:8080'], workers=10)
    is_ok(prefork.workers, 10, 'workers')

with subtest('accepts'):
    accepts = prefork.accepts
    is_ok(accepts, 10000, 'default')
    prefork.accepts = 100
    is_ok(prefork.accepts, 100, 'set')

with subtest('cleanup'):
    boolean = prefork.cleanup
    is_ok(boolean, True, 'default')
    prefork.cleanup = False
    is_ok(prefork.cleanup, False, 'set')

with subtest('graceful_timeout'):
    timeout = prefork.graceful_timeout
    is_ok(timeout, 25, 'default')
    prefork.graceful_timeout = 15
    is_ok(prefork.graceful_timeout, 15, 'set')

with subtest('heartbeat_interval'):
    interval = prefork.heartbeat_interval
    is_ok(interval, 5, 'default')
    prefork.heartbeat_interval = 3
    is_ok(prefork.heartbeat_interval, 3, 'set')

with subtest('heartbeat_timeout'):
    timeout = prefork.heartbeat_timeout
    is_ok(timeout, 50, 'default')
    prefork.heartbeat_timeout = 2
    is_ok(prefork.heartbeat_timeout, 2, 'set')

with subtest('pid_file'):
    import tempfile

    file = prefork.pid_file
    is_ok(file, os.path.join(tempfile.gettempdir(), 'prefork.pid'), 'default')
    prefork.pid_file = '/tmp/prefork.pid'
    is_ok(prefork.pid_file, '/tmp/prefork.pid', 'set')

with subtest('spare'):
    spare = prefork.spare
    is_ok(spare, 2, 'default')
    prefork.spare = 4
    is_ok(prefork.spare, 4, 'set')

with subtest('workers'):
    workers = prefork.workers
    is_ok(workers, 10, 'given')
    prefork.workers = 10
    is_ok(prefork.workers, 10, 'set')

with subtest('check_pid'):
    prefork = new()
    pid = prefork.check_pid()
    is_ok(pid, None, 'no process id file')
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        if not prefork.check_pid():
            print('Server is not running')
    is_ok(output.getvalue(), 'Server is not running\n', 'not running')

with subtest('ensure_pid_file'):
    prefork.ensure_pid_file(os.getpid())
    is_ok(prefork.check_pid(), os.getpid(), 'created')

with subtest('healthy'):
    healthy = prefork.healthy
    is_ok(healthy, 0, 'no workers')

with subtest('run'):
    once(prefork)
    pass_ok('run until a signal')

done_testing()
