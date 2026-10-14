from Pyjo.Test import *

import atexit
import os
import signal
import socket
import subprocess
import sys
import time


if not hasattr(os, 'fork'):
    plan(skip_all='no os.fork')

# PyPy with its JIT on macOS: the child of a fork crashes now and then with a bus error, under load
if sys.platform == 'darwin' and getattr(sys, 'pypy_translation_info', {}).get('translation.jit'):
    plan(skip_all='PyPy with its JIT on macOS: the child of a fork crashes now and then with SIGBUS')

import Pyjo.IOLoop.Server
import Pyjo.Server.Daemon
import Pyjo.Server.Reload
import Pyjo.Server.Reload.Backend.Poll

from Pyjo.File import curfile, tempdir


ROOT = curfile().dirname().dirname().dirname().to_str()
LIB = curfile().dirname().sibling('lib').to_str()

dir = tempdir()
myapp = dir.child('myapp.py').spew(
    f"""
import sys
sys.path.insert(0, {LIB!r})
from Lite import app, get
app.log.level = 'fatal'
get('/', {{'text': 'Hello!'}})
app.start()
""".encode()
)


# A server in a process of its own, until its port accepts connections, killed when the test ends before it stops it
def server(args, port):
    process = subprocess.Popen(
        [sys.executable, *args], env=dict(os.environ, PYTHONPATH=ROOT), stdout=subprocess.PIPE, text=True
    )
    atexit.register(lambda: process.poll() is None and process.kill())
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            socket.create_connection(('127.0.0.1', port), 0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    return process


def stop(process):
    process.send_signal(signal.SIGINT)
    status = process.wait(30)
    output = process.stdout.read()
    process.stdout.close()
    return status, output


with subtest('Synopsis'):
    port = Pyjo.IOLoop.Server.object.generate_port()
    code = f"""
import Pyjo.Server.Reload

reload = Pyjo.Server.Reload.new()
reload.daemon.listen = ['http://127.0.0.1:{port}']
reload.run({myapp.to_str()!r})
"""
    status, output = stop(server(['-c', code], port))
    is_ok(status, 0, 'stopped')
    like_ok(output, rf'Web application available at http://127.0.0.1:{port}', 'listening')

with subtest('Description'):
    port = Pyjo.IOLoop.Server.object.generate_port()
    process = server(['-m', 'Pyjo.Server.Reload', '-l', f'http://127.0.0.1:{port}', myapp.to_str()], port)
    status, output = stop(process)
    is_ok(status, 0, 'python -m Pyjo.Server.Reload')
    like_ok(output, rf'Web application available at http://127.0.0.1:{port}', 'listening')

with subtest('pyjo-reload'):
    result = subprocess.run(
        [sys.executable, '-m', 'Pyjo.Server.Reload', '--help'],
        env=dict(os.environ, PYTHONPATH=ROOT),
        capture_output=True,
        text=True,
    )
    is_ok(result.returncode, 0, 'help')
    like_ok(result.stdout, r'^usage: pyjo-reload ', 'usage')
    for option in ('--backend', '--listen', '--mode', '--verbose', '--watch'):
        like_ok(result.stdout, rf'{option}', option)

with subtest('new'):
    reload = Pyjo.Server.Reload.new()
    isa_ok(reload, Pyjo.Server.Reload.object, 'reload')
    reload = Pyjo.Server.Reload.new(silent=False)
    is_ok(reload.silent, False, 'silent')

with subtest('backend'):
    backend = reload.backend
    isa_ok(backend, Pyjo.Server.Reload.Backend.Poll.object, 'default')
    reload.backend = Pyjo.Server.Reload.Backend.Poll.new()
    isnt_ok(reload.backend, backend, 'set')

with subtest('daemon'):
    daemon = reload.daemon
    isa_ok(daemon, Pyjo.Server.Daemon.object, 'default')
    reload.daemon = Pyjo.Server.Daemon.new()
    isnt_ok(reload.daemon, daemon, 'set')

with subtest('silent'):
    boolean = Pyjo.Server.Reload.new().silent
    is_ok(boolean, True, 'default')
    reload.silent = False
    is_ok(reload.silent, False, 'set')

with subtest('run'):
    port = Pyjo.IOLoop.Server.object.generate_port()
    code = f"""
import Pyjo.Server.Reload

reload = Pyjo.Server.Reload.new()
reload.daemon.listen = ['http://127.0.0.1:{port}']
reload.run('myapp.py')
"""
    process = subprocess.Popen(
        [sys.executable, '-c', code],
        cwd=dir.to_str(),
        env=dict(os.environ, PYTHONPATH=ROOT),
        stdout=subprocess.PIPE,
        text=True,
    )
    atexit.register(lambda: process.poll() is None and process.kill())
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            socket.create_connection(('127.0.0.1', port), 0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    status, output = stop(process)
    is_ok(status, 0, 'relative path of the application')

with subtest('main'):
    port = Pyjo.IOLoop.Server.object.generate_port()
    code = f"""
import Pyjo.Server.Reload

Pyjo.Server.Reload.main(['-l', 'http://127.0.0.1:{port}', {myapp.to_str()!r}])
"""
    status, output = stop(server(['-c', code], port))
    is_ok(status, 0, 'command line interface')

done_testing()
