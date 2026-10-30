from Pyjo.Test import *

import atexit
import http.client
import importlib
import os
import pathlib
import signal
import socket
import subprocess
import sys
import tempfile
import time


if not hasattr(os, 'fork'):
    plan(skip_all='no os.fork')

# PyPy with its JIT on macOS: the child of a fork crashes now and then with a bus error, under load
if sys.platform == 'darwin' and getattr(sys, 'pypy_translation_info', {}).get('translation.jit'):
    plan(skip_all='PyPy with its JIT on macOS: the child of a fork crashes now and then with SIGBUS')

import Pyjo.IOLoop.Server
import Pyjo.Server.Reload.Backend.Poll


ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
LIB = os.path.join(os.path.dirname(__file__), '..', 'lib')

sys.path.insert(0, LIB)
ServerStart = importlib.import_module('ServerStart')

with subtest('Paths of pathlib and times of os.utime'), tempfile.TemporaryDirectory() as dir:
    root = pathlib.Path(dir)
    (root / 'lib').mkdir()
    file = root / 'lib' / 'MyApp.py'
    # The clock of a file system can be behind time.time() by some milliseconds, so the file is written a second
    # after the start
    time.sleep(1)
    file.write_text('pass\n')
    backend = Pyjo.Server.Reload.Backend.Poll.new(watch=[root / 'lib'], watch_timeout=0)
    is_deeply_ok(backend.modified_files(), [str(file)], 'a directory of pathlib')
    is_deeply_ok(backend.modified_files(), [], 'not changed')
    stat = file.stat()
    os.utime(file, (stat.st_atime, stat.st_mtime + 10))
    is_deeply_ok(backend.modified_files(), [str(file)], 'a later modification time')
    backend.watch = [file]
    is_deeply_ok(backend.modified_files(), [], 'a file of pathlib')

with subtest('http.client and TERM'), tempfile.TemporaryDirectory() as dir:
    app = pathlib.Path(dir, 'myapp.py')
    app.write_text(
        f"""
import sys
sys.path.insert(0, {os.path.abspath(LIB)!r})
from Pyjoyment.Lite import app, get
app.log.level = 'fatal'
get('/', {{'text': 'version 1'}})
app.start()
"""
    )

    # The server is started again on a new port when it is taken
    def start():
        port = ServerStart.port()
        process = subprocess.Popen(
            [sys.executable, '-m', 'Pyjo.Server.Reload', '-l', f'http://127.0.0.1:{port}', str(app)],
            env=dict(os.environ, PYTHONPATH=ROOT),
            stdout=subprocess.DEVNULL,
        )
        atexit.register(lambda: process.poll() is None and process.kill())
        return (port, process) if ServerStart.listening(port, process) else None

    port, process = ServerStart.retry(start)

    # The response of the worker, once there is one with the content
    def get(content):
        deadline = time.monotonic() + 20
        body = None
        while time.monotonic() < deadline:
            # The connection is closed also when the request fails, as PyPy would close it only with its garbage
            # collector
            conn = http.client.HTTPConnection('127.0.0.1', port, timeout=2)
            try:
                conn.request('GET', '/')
                body = conn.getresponse().read()
                if body == content:
                    break
            except OSError:
                pass
            finally:
                conn.close()
            time.sleep(0.1)
        return body

    is_ok(get(b'version 1'), b'version 1', 'first version')
    app.write_text(app.read_text().replace('version 1', 'version 2'))
    is_ok(get(b'version 2'), b'version 2', 'reloaded')
    process.send_signal(signal.SIGTERM)
    is_ok(process.wait(30), 0, 'stopped')
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            socket.create_connection(('127.0.0.1', port), 0.2).close()
            time.sleep(0.1)
        except OSError:
            break
    pass_ok('the port is free')

done_testing()
