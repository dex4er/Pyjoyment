from Pyjo.Test import *

import atexit
import importlib
import os
import signal
import socket
import subprocess
import sys
import time


# Left out from Mojolicious: TEST_HYPNOTOAD, which enables the tests, as they are quick; MOJO_REACTOR, as the tests
# run on the reactor of Pyjo.Reactor.detect()
if not hasattr(os, 'fork'):
    plan(skip_all='no os.fork')

# PyPy with its JIT on macOS: the child of a fork crashes now and then with a bus error, under load
if sys.platform == 'darwin' and getattr(sys, 'pypy_translation_info', {}).get('translation.jit'):
    plan(skip_all='PyPy with its JIT on macOS: the child of a fork crashes now and then with SIGBUS')

import Pyjo.IOLoop
import Pyjo.IOLoop.Server
import Pyjo.Server.Hot
import Pyjo.UserAgent

from Pyjo.File import curfile, tempdir


ROOT = curfile().dirname().dirname().dirname().to_str()
LIB = curfile().dirname().sibling('lib').to_str()

sys.path.insert(0, LIB)
ServerStart = importlib.import_module('ServerStart')

with subtest('Configure'):
    hot = Pyjo.Server.Hot.new()
    hot.prefork.app.config()['myserver'] = {
        'accepts': 13,
        'backlog': 43,
        'clients': 1,
        'graceful_timeout': 23,
        'heartbeat_interval': 7,
        'heartbeat_timeout': 9,
        'inactivity_timeout': 5,
        'keep_alive_timeout': 3,
        'listen': ['http://*:8081'],
        'pid_file': '/foo/bar.pid',
        'proxy': True,
        'requests': 3,
        'spare': 4,
        'trusted_proxies': ['127.0.0.0/8'],
        'upgrade_timeout': 45,
        'workers': 7,
    }
    is_ok(hot.upgrade_timeout, 180, 'right default')
    hot.configure('test')
    is_deeply_ok(hot.prefork.listen, ['http://*:8080'], 'right value')
    hot.configure('myserver')
    is_ok(hot.prefork.accepts, 13, 'right value')
    is_ok(hot.prefork.backlog, 43, 'right value')
    is_ok(hot.prefork.graceful_timeout, 23, 'right value')
    is_ok(hot.prefork.heartbeat_interval, 7, 'right value')
    is_ok(hot.prefork.heartbeat_timeout, 9, 'right value')
    is_ok(hot.prefork.inactivity_timeout, 5, 'right value')
    is_ok(hot.prefork.keep_alive_timeout, 3, 'right value')
    is_deeply_ok(hot.prefork.listen, ['http://*:8081'], 'right value')
    is_ok(hot.prefork.max_clients, 1, 'right value')
    is_ok(hot.prefork.max_requests, 3, 'right value')
    is_ok(hot.prefork.pid_file, '/foo/bar.pid', 'right value')
    ok(hot.prefork.reverse_proxy, 'reverse proxy enabled')
    is_ok(hot.prefork.spare, 4, 'right value')
    is_deeply_ok(hot.prefork.trusted_proxies, ['127.0.0.0/8'], 'right value')
    is_ok(hot.prefork.workers, 7, 'right value')
    is_ok(hot.upgrade_timeout, 45, 'right value')


def _pid(path):
    try:
        with open(path) as file:
            return file.readline().rstrip('\n')
    except OSError:
        return None


def _port(port):
    try:
        socket.create_connection(('127.0.0.1', port), 1).close()
        return True
    except OSError:
        return False


# Not in Mojolicious: script/hypnotoad is python -m Pyjo.Server.Hot, waited for, as Python warns about a process that
# nothing waits for, with its result, and its standard error captured and shown
def _hot(*args):
    result = subprocess.run(
        [sys.executable, '-m', 'Pyjo.Server.Hot', *args],
        env=dict(os.environ, PYTHONPATH=ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    sys.stderr.write(result.stderr)
    return result


with subtest('Hot deployment'):
    dir = tempdir()
    script = dir.child('myapp.py')
    log = dir.child('mojo.log')

    # Not in Mojolicious: the server is stopped when the test ends before it stops it
    def stop():
        if pid := _pid(dir.child('hot.pid')):
            try:
                os.kill(int(pid), signal.SIGTERM)
            except OSError:
                pass

    atexit.register(stop)

    # Not in Mojolicious: the server is started again on new ports when one of them is taken
    def start():
        port1 = Pyjo.IOLoop.Server.object.generate_port()
        port2 = Pyjo.IOLoop.Server.object.generate_port()
        script.spew(
            f"""
import sys
sys.path.insert(0, {LIB!r})
from Lite import app, get
import Pyjo.IOLoop

app.log.path = {log.to_str()!r}

app.config({{
    'hot': {{
        'listen': ['http://127.0.0.1:{port1}', 'http://127.0.0.1:{port2}'],
        'workers': 1
    }}
}})

app.log.level = 'trace'

get('/hello', {{'text': 'Hello Hot!'}})

graceful = False


def finish(loop):
    global graceful
    graceful = True


Pyjo.IOLoop.singleton.on('finish', finish)


def wait(c):
    def check(loop):
        if not graceful:
            return
        c.render(text='Graceful shutdown!')
        Pyjo.IOLoop.remove(id)

    id = Pyjo.IOLoop.recurring(0, check)


get('/graceful', wait)

app.start()
""".encode()
        )
        return None if ServerStart.in_use(_hot(script.to_str())) else (port1, port2)

    port1, port2 = ServerStart.retry(start)
    time.sleep(3)
    ServerStart.wait_for(lambda: _port(port2), 'the server', interval=1)
    old = _pid(dir.child('hot.pid'))
    ua = Pyjo.UserAgent.new()

    with subtest('Application is alive'):
        tx = ua.get(f'http://127.0.0.1:{port1}/hello')
        ok(tx.is_finished, 'transaction is finished')
        ok(tx.keep_alive, 'connection will be kept alive')
        ok(not tx.kept_alive, 'connection was not kept alive')
        is_ok(tx.res.code, 200, 'right status')
        is_ok(tx.res.body, b'Hello Hot!', 'right content')

        tx = ua.get(f'http://127.0.0.1:{port2}/hello')
        ok(tx.is_finished, 'transaction is finished')
        ok(tx.keep_alive, 'connection will be kept alive')
        ok(not tx.kept_alive, 'connection was not kept alive')
        is_ok(tx.res.code, 200, 'right status')
        is_ok(tx.res.body, b'Hello Hot!', 'right content')

        tx = ua.get(f'http://127.0.0.1:{port1}/hello')
        ok(tx.is_finished, 'transaction is finished')
        ok(tx.keep_alive, 'connection will be kept alive')
        ok(tx.kept_alive, 'connection was kept alive')
        is_ok(tx.res.code, 200, 'right status')
        is_ok(tx.res.body, b'Hello Hot!', 'right content')

        tx = ua.get(f'http://127.0.0.1:{port2}/hello')
        ok(tx.is_finished, 'transaction is finished')
        ok(tx.keep_alive, 'connection will be kept alive')
        ok(tx.kept_alive, 'connection was kept alive')
        is_ok(tx.res.code, 200, 'right status')
        is_ok(tx.res.body, b'Hello Hot!', 'right content')

    script.spew(
        f"""
import os
import sys
sys.path.insert(0, {LIB!r})
from Lite import app

if os.environ.get('PYJO_HOT_PID'):
    raise RuntimeError('Died')

app.start()
""".encode()
    )
    _hot(script.to_str())

    ServerStart.wait_for(
        lambda: 'Zero downtime software upgrade failed' in log.slurp().decode(), 'the failed upgrade', interval=1
    )

    with subtest('Connection did not get lost'):
        tx = ua.get(f'http://127.0.0.1:{port1}/hello')
        ok(tx.is_finished, 'transaction is finished')
        ok(tx.keep_alive, 'connection will be kept alive')
        ok(tx.kept_alive, 'connection was kept alive')
        is_ok(tx.res.code, 200, 'right status')
        is_ok(tx.res.body, b'Hello Hot!', 'right content')

        tx = ua.get(f'http://127.0.0.1:{port2}/hello')
        ok(tx.is_finished, 'transaction is finished')
        ok(tx.keep_alive, 'connection will be kept alive')
        ok(tx.kept_alive, 'connection was kept alive')
        is_ok(tx.res.code, 200, 'right status')
        is_ok(tx.res.body, b'Hello Hot!', 'right content')

    with subtest('Request that will be served after graceful shutdown has been initiated'):
        tx = ua.build_tx('GET', f'http://127.0.0.1:{port1}/graceful')
        ua.start(tx, lambda ua, tx: None)
        while not tx.req.is_finished:
            Pyjo.IOLoop.one_tick()

        script.spew(
            f"""
import os
import sys
sys.path.insert(0, {LIB!r})
from Lite import app, get

app.log.path = {log.to_str()!r}

app.config({{
    'hot': {{
        'accepts': 2,
        'inactivity_timeout': 3,
        'listen': ['http://127.0.0.1:{port1}', 'http://127.0.0.1:{port2}'],
        'requests': 1,
        'workers': 1
    }}
}})

app.log.level = 'trace'

get('/hello', lambda c: c.render(text=f'Hello World {{os.getpid()}}!'))

app.start()
""".encode()
        )
        _hot(script.to_str())

        time.sleep(1)
        ServerStart.wait_for(lambda: _pid(dir.child('hot.pid')) not in (None, old), 'the new manager', interval=1)

        while not tx.is_finished:
            Pyjo.IOLoop.one_tick()
        ok(not tx.keep_alive, 'connection will not be kept alive')
        ok(not tx.kept_alive, 'connection was not kept alive')
        is_ok(tx.res.code, 200, 'right status')
        is_ok(tx.res.body, b'Graceful shutdown!', 'right content')

    with subtest('One uncertain request that may or may not be served by the old worker'):
        tx = ua.get(f'http://127.0.0.1:{port1}/hello')
        is_ok(tx.res.code, 200, 'right status')
        tx = ua.get(f'http://127.0.0.1:{port2}/hello')
        is_ok(tx.res.code, 200, 'right status')

    with subtest('Application has been reloaded'):
        tx = ua.get(f'http://127.0.0.1:{port1}/hello')
        ok(tx.is_finished, 'transaction is finished')
        ok(not tx.keep_alive, 'connection will not be kept alive')
        ok(not tx.kept_alive, 'connection was not kept alive')
        is_ok(tx.res.code, 200, 'right status')
        first = tx.res.body
        like_ok(first, rb'Hello World \d+!', 'right content')

        tx = ua.get(f'http://127.0.0.1:{port2}/hello')
        ok(tx.is_finished, 'transaction is finished')
        ok(not tx.keep_alive, 'connection will not be kept alive')
        ok(not tx.kept_alive, 'connection was not kept alive')
        is_ok(tx.res.code, 200, 'right status')
        is_ok(tx.res.body, first, 'same content')

        tx = ua.get(f'http://127.0.0.1:{port1}/hello')
        ok(tx.is_finished, 'transaction is finished')
        ok(not tx.keep_alive, 'connection will not be kept alive')
        ok(not tx.kept_alive, 'connection was not kept alive')
        is_ok(tx.res.code, 200, 'right status')
        second = tx.res.body
        isnt_ok(first, second, 'different content')
        like_ok(second, rb'Hello World \d+!', 'right content')

        tx = ua.get(f'http://127.0.0.1:{port2}/hello')
        ok(tx.is_finished, 'transaction is finished')
        ok(not tx.keep_alive, 'connection will not be kept alive')
        ok(not tx.kept_alive, 'connection was not kept alive')
        is_ok(tx.res.code, 200, 'right status')
        is_ok(tx.res.body, second, 'same content')

    _hot(script.to_str(), '-s')
    ServerStart.wait_for(lambda: not _port(port2), 'the server to stop', interval=1)

    with subtest('Check log'):
        log = log.slurp().decode()
        like_ok(log, r'Worker \d+ started', 'right message')
        like_ok(log, r'Starting zero downtime software upgrade \(180 seconds\)', 'right message')
        like_ok(log, rf'Upgrade successful, stopping {old}', 'right message')

done_testing()
