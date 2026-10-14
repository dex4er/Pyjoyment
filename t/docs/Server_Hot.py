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
import Pyjo.Server.Hot
import Pyjo.Server.Prefork

from Pyjo.File import curfile, tempdir


ROOT = curfile().dirname().dirname().dirname().to_str()
LIB = curfile().dirname().sibling('lib').to_str()
ENV = dict(os.environ, PYTHONPATH=ROOT)


# An application in a directory of its own, for its hot.pid
def application(port):
    return (
        tempdir()
        .child('myapp.py')
        .spew(
            f"""
import sys
sys.path.insert(0, {LIB!r})
from Lite import app, get
app.log.level = 'fatal'
app.config(hot={{'listen': ['http://127.0.0.1:{port}'], 'workers': 1}})
get('/', {{'text': 'Hello!'}})
app.start()
""".encode()
        )
    )


def pid(app):
    try:
        return int(app.sibling('hot.pid').slurp().strip())
    except (OSError, ValueError):
        return None


def listening(port):
    try:
        socket.create_connection(('127.0.0.1', port), 0.2).close()
        return True
    except OSError:
        return False


def wait_for(condition):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.1)
    return False


# The server of the application, stopped gracefully, and killed when the test ends before it stops it
def stop(app, port):
    os.kill(pid(app), signal.SIGQUIT)
    return wait_for(lambda: not listening(port) and not os.path.exists(app.sibling('hot.pid')))


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def kill(app):
    if manager := pid(app):
        try:
            os.kill(manager, signal.SIGTERM)
        except OSError:
            pass


def command(*args, **kwargs):
    return subprocess.run([sys.executable, *args], env=ENV, capture_output=True, text=True, **kwargs)


with subtest('Synopsis'):
    port = Pyjo.IOLoop.Server.object.generate_port()
    myapp = application(port)
    atexit.register(kill, myapp)
    code = f"""
import Pyjo.Server.Hot

hot = Pyjo.Server.Hot.new()
hot.run({myapp.to_str()!r})
"""
    result = command('-c', code)
    is_ok(result.returncode, 0, 'daemonized')
    ok(wait_for(lambda: listening(port) and pid(myapp)), 'listening')
    ok(stop(myapp, port), 'stopped')

with subtest('Description'):
    port = Pyjo.IOLoop.Server.object.generate_port()
    myapp = application(port)
    atexit.register(kill, myapp)
    result = command('-m', 'Pyjo.Server.Hot', myapp.to_str())
    is_ok(result.returncode, 0, 'python -m Pyjo.Server.Hot')
    ok(wait_for(lambda: listening(port) and pid(myapp)), 'listening')
    old = pid(myapp)
    result = command('-m', 'Pyjo.Server.Hot', myapp.to_str())
    is_ok(result.stdout, f'Starting hot deployment for Hot server {old}.\n', 'hot deployment')
    ok(wait_for(lambda: pid(myapp) not in (None, old)), 'new manager')
    ok(wait_for(lambda: not alive(old)), 'old manager stopped')
    ok(stop(myapp, port), 'stopped')

with subtest('Settings'):
    hot = Pyjo.Server.Hot.new()
    app = hot.prefork.app
    app.config(hot={'listen': ['http://*:80'], 'workers': 10})
    hot.configure('hot')
    is_deeply_ok(hot.prefork.listen, ['http://*:80'], 'listen')
    is_ok(hot.prefork.workers, 10, 'workers')

with subtest('pyjo-hot'):
    result = subprocess.run(
        [sys.executable, '-m', 'Pyjo.Server.Hot', '--help'], env=ENV, capture_output=True, text=True
    )
    is_ok(result.returncode, 0, 'help')
    like_ok(result.stdout, r'^usage: pyjo-hot ', 'usage')
    for option in ('--foreground', '--stop', '--test'):
        like_ok(result.stdout, rf'{option}', option)

with subtest('new'):
    hot = Pyjo.Server.Hot.new()
    isa_ok(hot, Pyjo.Server.Hot.object, 'hot')
    hot = Pyjo.Server.Hot.new(upgrade_timeout=15)
    is_ok(hot.upgrade_timeout, 15, 'upgrade_timeout')

with subtest('prefork'):
    prefork = hot.prefork
    isa_ok(prefork, Pyjo.Server.Prefork.object, 'default')
    is_deeply_ok(prefork.listen, ['http://*:8080'], 'listen')
    hot.prefork = Pyjo.Server.Prefork.new()
    isnt_ok(hot.prefork, prefork, 'set')

with subtest('upgrade_timeout'):
    timeout = Pyjo.Server.Hot.new().upgrade_timeout
    is_ok(timeout, 180, 'default')
    hot.upgrade_timeout = 15
    is_ok(hot.upgrade_timeout, 15, 'set')

with subtest('configure'):
    hot = Pyjo.Server.Hot.new()
    hot.prefork.app.config(hot={'upgrade_timeout': 45})
    is_ok(hot.configure('hot'), None, 'configured')
    is_ok(hot.upgrade_timeout, 45, 'from the application')

with subtest('run'):
    port = Pyjo.IOLoop.Server.object.generate_port()
    myapp = application(port)
    atexit.register(kill, myapp)
    code = """
import Pyjo.Server.Hot

hot = Pyjo.Server.Hot.new()
hot.run('myapp.py')
"""
    result = command('-c', code, cwd=myapp.dirname().to_str())
    is_ok(result.returncode, 0, 'relative path of the application')
    ok(wait_for(lambda: listening(port) and pid(myapp)), 'listening')
    ok(stop(myapp, port), 'stopped')

with subtest('main'):
    port = Pyjo.IOLoop.Server.object.generate_port()
    myapp = application(port)
    code = f"""
import Pyjo.Server.Hot

Pyjo.Server.Hot.main(['-f', {myapp.to_str()!r}])
"""
    process = subprocess.Popen([sys.executable, '-c', code], env=ENV, stdout=subprocess.DEVNULL)
    atexit.register(lambda: process.poll() is None and process.kill())
    ok(wait_for(lambda: listening(port) and pid(myapp)), 'listening')
    process.send_signal(signal.SIGTERM)
    is_ok(process.wait(30), 0, 'command line interface in the foreground')
    ok(not os.path.exists(myapp.sibling('hot.pid')), 'no process id file')

done_testing()
