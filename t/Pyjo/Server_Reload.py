from Pyjo.Test import *

import atexit
import os
import signal
import socket
import subprocess
import sys
import time
import warnings


# Left out from Mojolicious: TEST_MORBO, which enables the tests, as they are quick; MOJO_REACTOR, as the tests run on
# the reactor of Pyjo.Reactor.detect()
if not hasattr(os, 'fork'):
    plan(skip_all='no os.fork')

# PyPy with its JIT on macOS: the child of a fork crashes now and then with a bus error, under load
if sys.platform == 'darwin' and getattr(sys, 'pypy_translation_info', {}).get('translation.jit'):
    plan(skip_all='PyPy with its JIT on macOS: the child of a fork crashes now and then with SIGBUS')

import Pyjo.IOLoop.Server
import Pyjo.Server.Daemon
import Pyjo.Server.Reload
import Pyjo.Server.Reload.Backend
import Pyjo.UserAgent

from Pyjo.File import curfile, tempdir


ROOT = curfile().dirname().dirname().dirname().to_str()
LIB = curfile().dirname().sibling('lib').to_str()


def _port(port):
    try:
        socket.create_connection(('127.0.0.1', port), 1).close()
        return True
    except OSError:
        return False


# Start
dir = tempdir()
script = dir.child('myapp.py')
subdir = dir.child('test', 'stuff').make_path()
reload = Pyjo.Server.Reload.new()
reload.backend.watch = [subdir, script]
is_deeply_ok(reload.backend.modified_files(), [], 'no files have changed')
started = dir.child('started1.txt')
# 'Hello Reload!' and 'Hello World!!' have the same size, as the two messages of the test of Mojolicious
script.spew(
    f"""
import sys
sys.path.insert(0, {LIB!r})
from Lite import app, get
from Pyjo.File import path
import Pyjo.IOLoop

app.log.level = 'fatal'

Pyjo.IOLoop.next_tick(lambda loop: path({started.to_str()!r}).touch())

get('/hello', {{'text': 'Hello Reload!'}})

app.start()
""".encode()
)
port = Pyjo.IOLoop.Server.object.generate_port()
server = subprocess.Popen(
    [sys.executable, '-m', 'Pyjo.Server.Reload', '-l', f'http://127.0.0.1:{port}', script.to_str()],
    env=dict(os.environ, PYTHONPATH=ROOT),
    stdout=subprocess.DEVNULL,
)
# Not in Mojolicious: the server is killed when the test ends before it stops it
atexit.register(lambda: server.poll() is None and server.kill())
while not _port(port):
    time.sleep(0.1)
ua = Pyjo.UserAgent.new()

with subtest('Basics'):
    tx = ua.get(f'http://127.0.0.1:{port}/hello')
    ok(tx.is_finished, 'transaction is finished')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, b'Hello Reload!', 'right content')

    tx = ua.get(f'http://127.0.0.1:{port}/hello')
    ok(tx.is_finished, 'transaction is finished')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, b'Hello Reload!', 'right content')

with subtest('Update script without changing size'):
    stat = os.stat(script)
    size, mtime = stat.st_size, stat.st_mtime
    started = started.sibling('started2.txt')
    script.spew(
        f"""
import sys
sys.path.insert(0, {LIB!r})
from Lite import app, get
from Pyjo.File import path
import Pyjo.IOLoop

app.log.level = 'fatal'

Pyjo.IOLoop.next_tick(lambda loop: path({started.to_str()!r}).touch())

get('/hello', {{'text': 'Hello World!!'}})

app.start()
""".encode()
    )
    is_deeply_ok(reload.backend.modified_files(), [script.to_str()], 'file has changed')
    ok(os.stat(script).st_mtime > mtime, 'modify time has changed')
    is_ok(os.stat(script).st_size, size, 'still equal size')
    while not os.path.exists(started):
        time.sleep(0.1)

    # Application has been reloaded
    tx = ua.get(f'http://127.0.0.1:{port}/hello')
    ok(tx.is_finished, 'transaction is finished')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, b'Hello World!!', 'right content')

    # Same result
    tx = ua.get(f'http://127.0.0.1:{port}/hello')
    ok(tx.is_finished, 'transaction is finished')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, b'Hello World!!', 'right content')

with subtest('Update script without changing mtime'):
    stat = os.stat(script)
    size, mtime = stat.st_size, stat.st_mtime
    is_deeply_ok(reload.backend.modified_files(), [], 'no files have changed')
    started = started.sibling('started3.txt')
    script.spew(
        f"""
import sys
sys.path.insert(0, {LIB!r})
from Lite import app, get
from Pyjo.File import path
import Pyjo.IOLoop

app.log.level = 'fatal'

Pyjo.IOLoop.next_tick(lambda loop: path({started.to_str()!r}).touch())

message = 'Failed!'


def before_server_start(server, app):
    global message
    message = 'Hello!'


app.hook('before_server_start', before_server_start)

get('/hello', lambda c: c.render(text=message))

app.start()
""".encode()
    )
    os.utime(script, (mtime, mtime))
    is_deeply_ok(reload.backend.modified_files(), [script.to_str()], 'file has changed')
    ok(os.stat(script).st_mtime == mtime, 'modify time has not changed')
    isnt_ok(os.stat(script).st_size, size, 'size has changed')
    while not os.path.exists(started):
        time.sleep(0.1)

    # Application has been reloaded again
    tx = ua.get(f'http://127.0.0.1:{port}/hello')
    ok(tx.is_finished, 'transaction is finished')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, b'Hello!', 'right content')

    # Same result
    tx = ua.get(f'http://127.0.0.1:{port}/hello')
    ok(tx.is_finished, 'transaction is finished')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, b'Hello!', 'right content')

with subtest('Watch for deleted files'):
    local = Pyjo.Server.Reload.new()
    local.backend.watch = [dir]
    local.backend.modified_files()
    tmp_file = dir.child('tmp_file.txt')
    tmp_file.spew(b'some data')
    is_deeply_ok(local.backend.modified_files(), [tmp_file.to_str()], 'file was created')
    is_deeply_ok(local.backend.modified_files(), [], 'no files changed')
    os.unlink(tmp_file)
    is_deeply_ok(local.backend.modified_files(), [tmp_file.to_str()], 'file was deleted')
    is_deeply_ok(local.backend.modified_files(), [], 'no files changed')

with subtest('New file(s)'):
    is_deeply_ok(reload.backend.modified_files(), [], 'directory has not changed')
    new = [subdir.child(f'{name}.txt') for name in ('test', 'testing')]
    for file in new:
        file.spew(b'whatever')
    is_deeply_ok(reload.backend.modified_files(), [file.to_str() for file in new], 'two files have changed')
    subdir.child('.hidden.txt').spew(b'whatever')
    is_deeply_ok(reload.backend.modified_files(), [], 'directory has not changed again')

with subtest('Broken symlink'):
    if not hasattr(os, 'symlink'):
        skip('Symlink support required!', 5)
    else:
        missing = subdir.child('missing.txt')
        broken = subdir.child('broken.txt')
        os.symlink(missing, broken)
        ok(os.path.islink(broken), 'symlink created')
        ok(not os.path.isfile(broken), 'symlink target does not exist')
        with warnings.catch_warnings(record=True) as warned:
            warnings.simplefilter('always')
            is_deeply_ok(reload.backend.modified_files(), [], 'directory has not changed')
        ok(not warned, 'no warnings')

# Stop
server.send_signal(signal.SIGINT)
while _port(port):
    time.sleep(0.1)
server.wait(30)

with subtest('Custom backend'):
    # The backend of t/mojo/lib, in the namespace of a temporary directory, which Pyjo.Server.Reload.Backend extends in
    # a process of its own, as the namespace is extended where the package is imported
    lib = tempdir()
    lib.child('Pyjo', 'Server', 'Reload', 'Backend').make_path().child('TestBackend.py').spew(b"""
import Pyjo.Server.Reload.Backend


class Pyjo_Server_Reload_Backend_TestBackend(Pyjo.Server.Reload.Backend.object):
    def modified_files(self):
        return ['always_changed']


new = Pyjo_Server_Reload_Backend_TestBackend.new
object = Pyjo_Server_Reload_Backend_TestBackend
""")
    code = """
import Pyjo.Server.Reload, Pyjo.Server.Reload.Backend

test_reload = Pyjo.Server.Reload.new()
print(isinstance(test_reload.backend, Pyjo.Server.Reload.Backend.object))
print(type(test_reload.backend).__module__)
print(test_reload.backend.modified_files())
print(test_reload.backend.watch_timeout)
"""
    env = dict(
        os.environ,
        PYTHONPATH=os.pathsep.join([ROOT, lib.to_str()]),
        PYJO_RELOAD_BACKEND='TestBackend',
        PYJO_RELOAD_TIMEOUT='2',
    )
    result = subprocess.run([sys.executable, '-c', code], env=env, capture_output=True, text=True)
    lines = result.stdout.splitlines()
    is_ok(lines[0], 'True', 'right backend')
    is_ok(lines[1], 'Pyjo.Server.Reload.Backend.TestBackend', 'right backend')
    is_ok(lines[2], "['always_changed']", 'always changes')
    is_ok(lines[3], '2.0', 'right timeout')

with subtest('SO_REUSEPORT'):
    if not hasattr(socket, 'SO_REUSEPORT'):
        skip('SO_REUSEPORT support required!', 2)
    else:
        port = Pyjo.IOLoop.Server.object.generate_port()
        # Not in Mojolicious: the daemon is closed where the test is done with it, as Perl frees it, as PyPy frees it
        # later, and the next daemon would reuse its listen socket of PYJO_REUSE
        with Pyjo.Server.Daemon.new(listen=[f'http://127.0.0.1:{port}'], silent=True).start() as daemon:
            ok(
                not daemon.ioloop.acceptor(daemon.acceptors[0]).handle.getsockopt(
                    socket.SOL_SOCKET, socket.SO_REUSEPORT
                ),
                'no SO_REUSEPORT socket option',
            )
        daemon = Pyjo.Server.Daemon.new(listen=[f'http://127.0.0.1:{port}?reuse=1'], silent=True)
        daemon.start()
        ok(
            daemon.ioloop.acceptor(daemon.acceptors[0]).handle.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT),
            'SO_REUSEPORT socket option',
        )

with subtest('Abstract methods'):
    throws_ok(
        lambda: Pyjo.Server.Reload.Backend.new().modified_files(),
        'Method "modified_files" not implemented by subclass',
        'right error',
    )

done_testing()
