from Pyjo.Test import *

import importlib
import os
import re
import signal
import socket
import subprocess
import sys
import time
import warnings


# Left out from Mojolicious: TEST_MORBO, which enables the tests, as they are quick; MOJO_REACTOR, as the tests run on
# the reactor of Pyjo.Reactor.detect()
if not hasattr(os, 'fork'):
    plan(skip_all='Pyjo.Server.Reload does not support Windows')

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

sys.path.insert(0, LIB)
ServerStart = importlib.import_module('ServerStart')

dir = tempdir()
ua = Pyjo.UserAgent.new()

# Not in Mojolicious: a shorter timeout of the backend, which waits for changes as long as it, so that the test, which
# runs in CI, takes less time
os.environ['PYJO_RELOAD_TIMEOUT'] = '0.25'

with subtest('Watch for modified files'):
    subdir = dir.child('modified', 'stuff').make_path()
    file = subdir.child('test.txt').spew(b'Hello')
    reload = Pyjo.Server.Reload.new()
    reload.backend.watch = [subdir.dirname()]
    reload.backend.modified_files()
    is_deeply_ok(reload.backend.modified_files(), [], 'no files have changed')

    stat = os.stat(file)
    size, mtime = stat.st_size, stat.st_mtime
    file.spew(b'World')
    os.utime(file, (mtime + 1, mtime + 1))
    is_deeply_ok(reload.backend.modified_files(), [file.to_str()], 'file has changed')
    ok(os.stat(file).st_mtime > mtime, 'modify time has changed')
    is_ok(os.stat(file).st_size, size, 'still equal size')
    is_deeply_ok(reload.backend.modified_files(), [], 'no files have changed')

    mtime = os.stat(file).st_mtime
    file.spew(b'Hello World')
    os.utime(file, (mtime, mtime))
    is_deeply_ok(reload.backend.modified_files(), [file.to_str()], 'file has changed')
    ok(os.stat(file).st_mtime == mtime, 'modify time has not changed')
    isnt_ok(os.stat(file).st_size, size, 'size has changed')
    is_deeply_ok(reload.backend.modified_files(), [], 'no files have changed')

with subtest('Watch for new and deleted files'):
    subdir = dir.child('new').make_path()
    reload = Pyjo.Server.Reload.new()
    reload.backend.watch = [subdir]
    is_deeply_ok(reload.backend.modified_files(), [], 'no files have changed')

    new = [subdir.child(f'{name}.txt') for name in ('test', 'testing')]
    for file in new:
        file.spew(b'whatever')
    is_deeply_ok(reload.backend.modified_files(), [file.to_str() for file in new], 'two files have been created')
    is_deeply_ok(reload.backend.modified_files(), [], 'no files have changed')
    subdir.child('.hidden.txt').spew(b'whatever')
    is_deeply_ok(reload.backend.modified_files(), [], 'hidden files are ignored')

    os.unlink(new[0])
    is_deeply_ok(reload.backend.modified_files(), [new[0].to_str()], 'file has been deleted')
    is_deeply_ok(reload.backend.modified_files(), [], 'no files have changed')

with subtest('Broken symlink'):
    if not hasattr(os, 'symlink'):
        plan(skip_all='Symlink support required!')
    subdir = dir.child('symlink').make_path()
    reload = Pyjo.Server.Reload.new()
    reload.backend.watch = [subdir]
    broken = subdir.child('broken.txt')
    os.symlink(subdir.child('missing.txt'), broken)
    ok(os.path.islink(broken), 'symlink created')
    ok(not os.path.isfile(broken), 'symlink target does not exist')
    with warnings.catch_warnings(record=True) as warned:
        warnings.simplefilter('always')
        is_deeply_ok(reload.backend.modified_files(), [], 'no files have changed')
    ok(not warned, 'no warnings')


def _app(name, text, extra=''):
    return dir.child(name).spew(
        f"""
import os
import signal
import sys
import time

from Pyjoyment.Lite import app, get, hook
from Pyjo.File import path
import Pyjo.IOLoop

app.log.level = 'fatal'

{extra}

server = {{'name': 'none'}}
hook('before_server_start', lambda server_, app_: server.update(name=type(server_).__module__))

get('/hello', {{'text': {text!r}}}, 'hello')
get('/server', lambda c: c.render(text=server['name']))

app.start()
""".encode()
    )


# Not in Mojolicious: the server is killed when the test ends before it stops it
def _reload(log, *args):
    with open(log, 'ab') as handle:
        process = subprocess.Popen(
            [sys.executable, '-m', 'Pyjo.Server.Reload', *args],
            env=dict(os.environ, PYTHONPATH=ROOT),
            stdout=handle,
            stderr=subprocess.STDOUT,
        )
    reloads.append(process)
    return process


reloads = []


def _alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _port(port):
    try:
        socket.create_connection(('127.0.0.1', port), 1).close()
        return True
    except OSError:
        return False


def _stop(process, port, sig=signal.SIGINT):
    process.send_signal(sig)
    is_ok(process.wait(60), 0, 'reload exited cleanly')
    ok(not _port(port), 'all server processes have been stopped')


def _wait_until(cb, timeout=30):
    deadline = time.monotonic() + timeout
    while not cb() and time.monotonic() < deadline:
        time.sleep(0.1)
    return cb()


# Retry until the expected response arrives (the listen socket stays open between restarts)
def _wait_for(port, text):
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        tx = ua.get(f'http://127.0.0.1:{port}/hello')
        if (tx.res.body or b'') == text.encode():
            return True
        time.sleep(0.1)
    return False


def _slurp(file):
    return file.slurp().decode() if os.path.exists(file) else ''


with subtest('Default command (daemon)'):
    script = _app('daemon.py', 'Hello Reload!')
    port = ServerStart.port()
    log = dir.child('daemon.log')
    process = _reload(log, '-v', '-l', f'http://127.0.0.1:{port}', script.to_str())
    ok(_wait_for(port, 'Hello Reload!'), 'server has been started')
    ok(_wait_for(port, 'Hello Reload!'), 'same result')

    _app('daemon.py', 'Hello World!')
    ok(_wait_for(port, 'Hello World!'), 'server has been restarted')
    like_ok(_slurp(log), r'File ".*daemon\.py" changed, restarting', 'right message')
    is_ok(ua.get(f'http://127.0.0.1:{port}/server').res.body, b'Pyjo.Server.Daemon', 'right server')

    _app(
        'daemon.py',
        'Failed!',
        "hook('before_server_start', lambda server, app: app.routes.find('hello').to(text='Hook!'))",
    )
    ok(_wait_for(port, 'Hook!'), 'server has been restarted again')

    _stop(process, port)

with subtest('Prefork command with arguments'):
    script = _app('prefork.py', 'Hello Prefork!')
    port = ServerStart.port()
    process = _reload(dir.child('prefork.log'), '-l', f'http://127.0.0.1:{port}', script.to_str(), 'prefork', '-w', '2')
    ok(_wait_for(port, 'Hello Prefork!'), 'server has been started')

    _app('prefork.py', 'Hello Again!')
    ok(_wait_for(port, 'Hello Again!'), 'server has been restarted')
    is_ok(ua.get(f'http://127.0.0.1:{port}/server').res.body, b'Pyjo.Server.Prefork', 'right server')

    _stop(process, port)

with subtest('Recover from broken application'):
    script = _app('broken.py', 'Hello!')
    port = ServerStart.port()
    log = dir.child('broken.log')
    process = _reload(log, '-l', f'http://127.0.0.1:{port}', script.to_str())
    ok(_wait_for(port, 'Hello!'), 'server has been started')

    script.spew(b"from Pyjoyment.Lite import app, get\nget('/hello', {'text': 'Broken!'}\napp.start()\n")
    _wait_until(lambda: 'SyntaxError' in _slurp(log))
    like_ok(_slurp(log), r'SyntaxError', 'application is broken')

    _app('broken.py', 'Fixed!')
    ok(_wait_for(port, 'Fixed!'), 'server has been restarted after fixing the application')

    _stop(process, port)

with subtest('Kill server that does not stop'):
    # Unlike Mojolicious: the server ignores QUIT too, which stops it immediately
    extra = (
        'Pyjo.IOLoop.next_tick(lambda loop: '
        '(signal.signal(signal.SIGTERM, signal.SIG_IGN), signal.signal(signal.SIGQUIT, signal.SIG_IGN)))'
    )
    script = _app('stuck.py', 'Stuck!', extra)
    port = ServerStart.port()
    process = _reload(dir.child('stuck.log'), '-l', f'http://127.0.0.1:{port}', script.to_str())
    ok(_wait_for(port, 'Stuck!'), 'server has been started')

    start = time.monotonic()
    _app('stuck.py', 'Unstuck!', extra)
    ok(_wait_for(port, 'Unstuck!'), 'server has been killed and restarted')
    ok(time.monotonic() - start >= 4, 'server got time to stop')

    _stop(process, port)

with subtest('Stop subprocesses'):
    file = dir.child('subprocess.pid')
    extra = f"""
pid = os.fork()
if not pid:
    time.sleep(1000)
    os._exit(0)
path({file.to_str()!r}).spew(str(pid))
"""
    script = _app('subprocess_app.py', 'Hello!', extra)
    port = ServerStart.port()
    process = _reload(dir.child('subprocess.log'), '-l', f'http://127.0.0.1:{port}', script.to_str())
    ok(_wait_for(port, 'Hello!'), 'server has been started')
    ok(child := int(_slurp(file) or 0), 'subprocess has been started')
    ok(_alive(child), 'subprocess is running')

    _stop(process, port)
    ok(_wait_until(lambda: not _alive(child)), 'subprocess has been stopped')

with subtest('Exec commands'):
    file = dir.child('exec.txt')
    cmd = dir.child('exec_cmd.py').spew(
        f"""
import os, time
pid = os.fork()
if not pid:
    time.sleep(1000)
    os._exit(0)
with open({file.to_str()!r}, 'w') as handle:
    handle.write(f'{{os.getpid()}} {{pid}} {{os.environ["PYJO_MODE"]}}')
time.sleep(1000)
""".encode()
    )
    script = _app('exec_app.py', 'Hello Exec!')
    port = ServerStart.port()
    log = dir.child('exec.log')
    exec = ['-x', f'"{sys.executable}" "{cmd}"', '-x', f'"{sys.executable}" -c "raise SystemExit(3)"']
    process = _reload(log, '-l', f'http://127.0.0.1:{port}', *exec, script.to_str())
    ok(_wait_for(port, 'Hello Exec!'), 'server has been started')
    ok(_wait_until(lambda: _slurp(file)), 'command has been started')
    command, child, mode = _slurp(file).split()
    command, child = int(command), int(child)
    is_ok(mode, 'development', 'right mode')
    ok(_alive(command), 'command is running')
    ok(_alive(child), 'subprocess of command is running')
    ok(
        _wait_until(lambda: re.search(r'Command ".+SystemExit\(3\)"" exited with status 3\.', _slurp(log))),
        'right message',
    )

    _app('exec_app.py', 'Hello Again!')
    ok(_wait_for(port, 'Hello Again!'), 'server has been restarted')
    ok(_alive(command), 'command has not been restarted')
    is_ok(int(_slurp(file).split()[0]), command, 'command has only been started once')

    _stop(process, port)
    ok(_wait_until(lambda: not _alive(command)), 'command has been stopped')
    ok(_wait_until(lambda: not _alive(child)), 'subprocess of command has been stopped')
    unlike_ok(_slurp(log), r'exec_cmd\.py"" (?:exited|was killed)', 'no message for commands stopped by reload')

with subtest('Exec commands that misbehave'):
    file = dir.child('stuck_exec.txt')
    stuck = dir.child('stuck_exec.py').spew(
        f"""
import os, signal, time
signal.signal(signal.SIGTERM, signal.SIG_IGN)
with open({file.to_str()!r}, 'w') as handle:
    handle.write(f'{{os.getpid()}} {{os.environ["PYJO_MODE"]}}')
time.sleep(1000)
""".encode()
    )
    killed = dir.child('killed_exec.py').spew(b'import os, signal, time\nos.kill(os.getpid(), signal.SIGKILL)\n')
    missing = dir.child('missing_exec')
    script = _app('stuck_exec_app.py', 'Hello Stuck!', "get('/mode', lambda c: c.render(text=app.mode))")
    port = ServerStart.port()
    log = dir.child('stuck_exec.log')
    exec = ['-x', f'{sys.executable} {stuck}', '-x', f'{sys.executable} {killed}', '-x', missing.to_str()]
    process = _reload(log, '-m', 'testing', '-l', f'http://127.0.0.1:{port}', *exec, script.to_str())
    ok(_wait_for(port, 'Hello Stuck!'), 'server has been started')
    is_ok(ua.get(f'http://127.0.0.1:{port}/mode').res.body, b'testing', 'right application mode')
    ok(_wait_until(lambda: _slurp(file)), 'command has been started')
    command, mode = _slurp(file).split()
    command = int(command)
    is_ok(mode, 'testing', 'same mode for command')
    ok(
        _wait_until(lambda: re.search(r'Command ".+killed_exec\.py" was killed by signal 9\.', _slurp(log))),
        'right message',
    )
    ok(
        _wait_until(lambda: re.search(r'Command ".+missing_exec" exited with status 1\.', _slurp(log))),
        'right message',
    )
    like_ok(_slurp(log), r'Can\'t exec ".+missing_exec"', 'right error')
    ok(_alive(command), 'command is still running')

    start = time.monotonic()
    _stop(process, port)
    ok(time.monotonic() - start >= 4, 'command got time to stop')
    ok(not _alive(command), 'command has been killed')
    unlike_ok(_slurp(log), r'stuck_exec\.py" (?:exited|was killed)', 'no message for commands stopped by reload')

with subtest('Exec commands can tell when reload is gone'):
    file = dir.child('stdin_exec.txt')
    cmd = dir.child('stdin_exec.py').spew(
        f"""
import sys
with open({file.to_str()!r}, 'w') as handle:
    handle.write('started')
input = sys.stdin.read()
with open({file.to_str()!r}, 'w') as handle:
    handle.write('stdin closed')
""".encode()
    )
    script = _app('stdin_exec_app.py', 'Hello Stdin!', "get('/pid', lambda c: c.render(text=str(os.getpid())))")
    port = ServerStart.port()
    process = _reload(
        dir.child('stdin_exec.log'), '-l', f'http://127.0.0.1:{port}', '-x', f'{sys.executable} {cmd}', script.to_str()
    )
    ok(_wait_for(port, 'Hello Stdin!'), 'server has been started')
    ok(_wait_until(lambda: _slurp(file)), 'command has been started')
    time.sleep(0.5)
    is_ok(_slurp(file), 'started', 'command is still waiting for input')

    server = int(ua.get(f'http://127.0.0.1:{port}/pid').res.body)
    process.kill()
    is_ok(process.wait(30), -signal.SIGKILL, 'reload has been killed')
    ok(_wait_until(lambda: _slurp(file) == 'stdin closed'), 'command noticed that reload is gone')

    # The server does not use STDIN and needs to be cleaned up manually
    os.killpg(server, signal.SIGKILL)
    ok(_wait_until(lambda: not _port(port)), 'server has been stopped')

# Unlike Mojolicious: HUP restarts the server, as it reloads the other servers of Pyjoyment, where Mojo stops on it, in
# its subtest "Stop on SIGHUP (terminal closed)"
with subtest('Restart on SIGHUP'):
    file = dir.child('hup_exec.txt')
    cmd = dir.child('hup_exec.py').spew(
        f"import os, time\nopen({file.to_str()!r}, 'w').write(str(os.getpid()))\ntime.sleep(1000)\n".encode()
    )
    script = _app('hup_app.py', 'Hello HUP!', "get('/pid', lambda c: c.render(text=str(os.getpid())))")
    port = ServerStart.port()
    process = _reload(
        dir.child('hup.log'), '-l', f'http://127.0.0.1:{port}', '-x', f'{sys.executable} {cmd}', script.to_str()
    )
    ok(_wait_for(port, 'Hello HUP!'), 'server has been started')
    ok(_wait_until(lambda: _slurp(file)), 'command has been started')
    command = int(_slurp(file))
    server = ua.get(f'http://127.0.0.1:{port}/pid').res.body

    process.send_signal(signal.SIGHUP)
    ok(
        _wait_until(lambda: ua.get(f'http://127.0.0.1:{port}/pid').res.body not in (server, None)),
        'server has been restarted',
    )
    ok(_alive(command), 'command is still running')

    _stop(process, port)
    ok(_wait_until(lambda: not _alive(command)), 'command has been stopped')

with subtest('Wrong arguments'):
    result = subprocess.run(
        [sys.executable, '-m', 'Pyjo.Server.Reload'], env=dict(os.environ, PYTHONPATH=ROOT), capture_output=True
    )
    like_ok(result.stderr.decode(), r'Usage: pyjo-reload', 'usage message')
    isnt_ok(result.returncode, 0, 'failed')

    result = subprocess.run(
        [sys.executable, '-m', 'Pyjo.Server.Reload', './myapp.py', '-l', 'http://127.0.0.1:3000'],
        env=dict(os.environ, PYTHONPATH=ROOT),
        capture_output=True,
    )
    like_ok(
        result.stderr.decode(),
        r'pyjo-reload options need to come before the application, e\.g\. "pyjo-reload -l \.\.\. \./myapp\.py"',
        'right error',
    )
    isnt_ok(result.returncode, 0, 'failed')

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
        plan(skip_all='SO_REUSEPORT support required!')
    port = Pyjo.IOLoop.Server.object.generate_port()
    # Not in Mojolicious: the daemon is closed where the test is done with it, as Perl frees it, as PyPy frees it later,
    # and the next daemon would reuse its listen socket of PYJO_REUSE
    with Pyjo.Server.Daemon.new(listen=[f'http://127.0.0.1:{port}'], silent=True).start() as daemon:
        ok(
            not daemon.ioloop.acceptor(daemon.acceptors[0]).handle.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT),
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

for reload_ in reloads:
    if reload_.poll() is None:
        reload_.kill()
        reload_.wait()

done_testing()
