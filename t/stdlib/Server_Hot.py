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


ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
LIB = os.path.join(os.path.dirname(__file__), '..', 'lib')
ENV = dict(os.environ, PYTHONPATH=ROOT)

sys.path.insert(0, LIB)
ServerStart = importlib.import_module('ServerStart')


def application(dir, port):
    app = pathlib.Path(dir, 'myapp.py')
    app.write_text(
        f"""
import sys
sys.path.insert(0, {os.path.abspath(LIB)!r})
from Pyjoyment.Lite import app, get
app.log.level = 'fatal'
app.config(hot={{'listen': ['http://127.0.0.1:{port}'], 'workers': 1}})
get('/', lambda c: c.render(text=f'int_max_str_digits={{sys.flags.int_max_str_digits}}'))
app.start()
"""
    )
    return app


# The process id of the manager, 0 while there is none: the manager writes the file after it creates it, and a hot
# deployment removes it before the new manager creates it again
def read_pid(pid):
    try:
        return int(pid.read_text() or 0)
    except FileNotFoundError:
        return 0


# The response of the worker, once there is one
def get(port):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        # The connection is closed also when the request fails, as PyPy would close it only with its garbage collector
        conn = http.client.HTTPConnection('127.0.0.1', port, timeout=2)
        try:
            conn.request('GET', '/')
            return conn.getresponse().read()
        except OSError:
            time.sleep(0.1)
        finally:
            conn.close()
    return None


def closed(port):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            socket.create_connection(('127.0.0.1', port), 0.2).close()
            time.sleep(0.1)
        except OSError:
            return True
    return False


with subtest('pathlib, http.client and the options of the interpreter'), tempfile.TemporaryDirectory() as dir:
    # The server is started again on a new port when it is taken
    def start():
        port = ServerStart.port()
        app = application(dir, port)
        code = f"""
import pathlib
import Pyjo.Server.Hot

Pyjo.Server.Hot.new().run(pathlib.Path({str(app)!r}))
"""
        result = subprocess.run(
            [sys.executable, '-X', 'int_max_str_digits=1234', '-c', code], env=ENV, capture_output=True, text=True
        )
        return None if ServerStart.in_use(result) else (port, app, result)

    port, app, result = ServerStart.retry(start)
    pid = app.with_name('hot.pid')
    is_ok(result.returncode, 0, 'daemonized')
    atexit.register(lambda: (manager := read_pid(pid)) and os.kill(manager, signal.SIGQUIT))
    is_ok(get(port), b'int_max_str_digits=1234', 'the command line of the process with -X, run again')
    deadline = time.monotonic() + 20
    while not read_pid(pid) and time.monotonic() < deadline:
        time.sleep(0.1)
    os.kill(read_pid(pid), signal.SIGTERM)
    ok(closed(port), 'stopped gracefully')

with subtest('-t and -s'), tempfile.TemporaryDirectory() as dir:
    app = application(dir, ServerStart.port())
    result = subprocess.run(
        [sys.executable, '-m', 'Pyjo.Server.Hot', '-t', str(app)], env=ENV, capture_output=True, text=True
    )
    is_ok(result.returncode, 0, 'test')
    is_ok(result.stdout, 'Everything looks good!\n', 'application is fine')
    result = subprocess.run(
        [sys.executable, '-m', 'Pyjo.Server.Hot', '-s', str(app)], env=ENV, capture_output=True, text=True
    )
    is_ok(result.returncode, 0, 'stop')
    is_ok(result.stdout, 'Hot server not running.\n', 'not running')

# Not in Mojolicious: HUP attempts a hot deployment, where Mojo has USR2, and -s stops the server gracefully with TERM
with subtest('HUP and -s'), tempfile.TemporaryDirectory() as dir:
    # The server is started again on a new port when it is taken
    def start():
        port = ServerStart.port()
        app = application(dir, port)
        result = subprocess.run([sys.executable, '-m', 'Pyjo.Server.Hot', str(app)], env=ENV, capture_output=True)
        return None if ServerStart.in_use(result) else (port, app, result)

    port, app, result = ServerStart.retry(start)
    pid = app.with_name('hot.pid')
    atexit.register(lambda: (manager := read_pid(pid)) and os.kill(manager, signal.SIGQUIT))
    like_ok(get(port), rb'^int_max_str_digits=', 'serving')
    deadline = time.monotonic() + 20
    while not read_pid(pid) and time.monotonic() < deadline:
        time.sleep(0.1)
    old = read_pid(pid)
    os.kill(old, signal.SIGHUP)
    deadline = time.monotonic() + 30
    while read_pid(pid) in (0, old) and time.monotonic() < deadline:
        time.sleep(0.1)
    isnt_ok(read_pid(pid), old, 'new manager')
    like_ok(get(port), rb'^int_max_str_digits=', 'serving after the hot deployment')
    result = subprocess.run(
        [sys.executable, '-m', 'Pyjo.Server.Hot', '-s', str(app)], env=ENV, capture_output=True, text=True
    )
    like_ok(result.stdout, r'^Stopping Hot server \d+ gracefully\.', 'stopping')
    ok(closed(port), 'stopped gracefully')

with subtest('Foreground and TERM'), tempfile.TemporaryDirectory() as dir:
    # The server is started again on a new port when it is taken
    def start():
        port = ServerStart.port()
        app = application(dir, port)
        process = subprocess.Popen(
            [sys.executable, '-m', 'Pyjo.Server.Hot', '-f', str(app)], env=ENV, stdout=subprocess.DEVNULL
        )
        atexit.register(lambda: process.poll() is None and process.kill())
        return (port, app, process) if ServerStart.listening(port, process) else None

    port, app, process = ServerStart.retry(start)
    like_ok(get(port), rb'^int_max_str_digits=', 'serving')
    process.send_signal(signal.SIGTERM)
    is_ok(process.wait(30), 0, 'stopped')
    ok(closed(port), 'the port is free')
    ok(not app.with_name('hot.pid').exists(), 'no process id file')

done_testing()
