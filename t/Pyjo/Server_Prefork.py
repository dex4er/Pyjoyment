from Pyjo.Test import *

import gc
import os
import signal
import socket
import sys
import time


# Left out from Mojolicious: TEST_PREFORK, which enables the tests, as they are quick; MOJO_REACTOR, as the tests run on
# the reactor of Pyjo.Reactor.detect()
if not hasattr(os, 'fork'):
    plan(skip_all='no os.fork')

# PyPy with its JIT on macOS: the child of a fork crashes now and then with a bus error, under load
if sys.platform == 'darwin' and getattr(sys, 'pypy_translation_info', {}).get('translation.jit'):
    plan(skip_all='PyPy with its JIT on macOS: the child of a fork crashes now and then with SIGBUS')

import Pyjo.Server.Prefork
import Pyjo.UserAgent
import Pyjoyment.HelloWorld

from Pyjo.File import curfile, path, tempdir


# Unlike Mojolicious: a server listens on a port that the system picks, which ports() gives, where the test picks one
# with generate_port, which an outgoing connection of a test that runs at the same time can take before the server
# binds it, and has a process id file of its own, where the default one, in the temporary directory of the system, is
# the one of every server that runs at the same time


with subtest('Manage and clean up PID file'):
    prefork = Pyjo.Server.Prefork.new()
    dir = tempdir()
    ok(prefork.pid_file, 'has default path')
    file = dir.child('prefork.pid')
    prefork.pid_file = file
    ok(not prefork.check_pid(), 'no process id')
    prefork.ensure_pid_file(-23)
    ok(os.path.exists(file), 'file exists')
    is_ok(path(file).slurp(), b'-23\n', 'right process id')
    ok(not prefork.check_pid(), 'no process id')
    ok(not os.path.exists(file), 'file has been cleaned up')
    prefork.ensure_pid_file(os.getpid())
    ok(os.path.exists(file), 'file exists')
    is_ok(path(file).slurp(), f'{os.getpid()}\n'.encode(), 'right process id')
    is_ok(prefork.check_pid(), os.getpid(), 'right process id')
    del prefork
    gc.collect()
    ok(not os.path.exists(file), 'file has been cleaned up')

with subtest('Bad PID file'):
    bad = curfile().sibling('does_not_exist', 'test.pid')
    prefork = Pyjo.Server.Prefork.new(pid_file=bad)
    prefork.app.log.level = 'trace'
    prefork.app.log.unsubscribe('message')
    log = ''

    def message(log_, level, *lines):
        global log
        log += lines[-1]

    cb = prefork.app.log.on('message', message)
    try:
        prefork.ensure_pid_file(os.getpid())
        err = None
    except Exception as e:
        err = str(e)
    like_ok(err, r"Can't create process id file", 'right error')
    unlike_ok(log, r'Creating process id file', 'right message')
    like_ok(log, r"Can't create process id file", 'right message')
    prefork.app.log.unsubscribe('message', cb)

with subtest('Multiple workers and graceful shutdown'):
    dir = tempdir()
    file = dir.child('prefork.pid')
    # Unlike Mojolicious: the default application of Pyjo.Server is Pyjo.HelloWorld, which has no hooks, so the test
    # passes Pyjoyment.HelloWorld, the Mojo::HelloWorld of Mojo
    prefork = Pyjo.Server.Prefork.new(
        app=Pyjoyment.HelloWorld.new(), heartbeat_interval=0.5, listen=['http://*'], pid_file=file
    )
    prefork.unsubscribe('request')

    @prefork.on('request')
    def request(prefork, tx):
        tx.res.code = 200
        tx.res.body = b'just works!'
        tx.resume()

    is_ok(prefork.workers, 4, 'start with four workers')
    spawn, reap = [], []
    worker = tx = graceful = None
    prefork.on('spawn', lambda prefork, pid: spawn.append(pid))

    @prefork.on('heartbeat')
    def heartbeat(prefork, pid):
        global worker, tx
        worker = pid
        if prefork.healthy < 4:
            return
        # The user agent closes its connection, as PyPy frees it only when its garbage collector runs, which
        # the workers of a later server, forked with it, may do
        ua = Pyjo.UserAgent.new()
        tx = ua.get(f'http://127.0.0.1:{prefork.ports()[0]}')
        ua.ioloop.reset()
        # Unlike Mojolicious: TERM shuts the server down gracefully, where Mojo has QUIT
        os.kill(os.getpid(), signal.SIGTERM)

    prefork.on('reap', lambda prefork, pid: reap.append(pid))

    def finish(prefork, graceful_):
        global graceful
        graceful = graceful_

    prefork.on('finish', finish)
    prefork.app.log.level = 'trace'
    prefork.app.log.unsubscribe('message')
    log = ''
    cb = prefork.app.log.on('message', message)
    is_ok(prefork.healthy, 0, 'no healthy workers')
    server = []

    def before_server_start(server_, app):
        server.extend([server_.workers, app.mode])

    prefork.app.hook('before_server_start', before_server_start)

    # Not in Mojolicious: the end of the server, in each worker and in the manager, which writes its process id
    stopped = dir.child('stopped')

    def after_server_stop(server_, app):
        with open(stopped.to_str(), 'a') as file:
            file.write(f'{os.getpid()}\n')

    prefork.app.hook('after_server_stop', after_server_stop)
    prefork.run()
    is_deeply_ok(server, [4, 'development'], 'hook has been emitted once')
    is_deeply_ok(
        sorted(int(pid) for pid in stopped.slurp().split()),
        sorted([*spawn, os.getpid()]),
        'end in the workers and the manager',
    )
    is_ok(len(spawn), 4, 'four workers spawned')
    is_ok(len(reap), 4, 'four workers reaped')
    ok(worker in spawn, 'worker has a heartbeat')
    ok(graceful, 'server has been stopped gracefully')
    is_deeply_ok(sorted(spawn), sorted(reap), 'same process ids')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, b'just works!', 'right content')
    like_ok(log, r'Listening at', 'right message')
    like_ok(log, rf'Manager {os.getpid()} started', 'right message')
    like_ok(log, r'Creating process id file', 'right message')
    # Unlike Mojolicious: the graceful timeout defaults to 25 seconds, where Mojo has 120
    like_ok(log, rf'Stopping worker {spawn[0]} gracefully \(25 seconds\)', 'right message')
    like_ok(log, rf'Worker {spawn[0]} stopped', 'right message')
    like_ok(log, rf'Manager {os.getpid()} stopped', 'right message')
    prefork.app.log.unsubscribe('message', cb)

    is_ok(prefork.check_pid(), os.getpid(), 'right process id')
    pid = prefork.pid_file
    ok(os.path.exists(pid), 'process id file has been created')
    del prefork
    gc.collect()
    ok(not os.path.exists(pid), 'process id file has been removed')

# Not in Mojolicious: the same on Pyjo.HelloWorld, the application of pure Pyjo, whose handler answers the request of a
# worker, and whose server method the manager calls once before it starts, as Pyjoyment.HelloWorld emits its hook
with subtest('Multiple workers and graceful shutdown (Pyjo.HelloWorld)'):
    import Pyjo.HelloWorld

    server = []

    class HelloWorld(Pyjo.HelloWorld.object):
        def server(self, server_):
            server.append(server_.workers)

    dir = tempdir()
    file = dir.child('prefork.pid')
    prefork = Pyjo.Server.Prefork.new(app=HelloWorld.new(), heartbeat_interval=0.5, listen=['http://*'], pid_file=file)
    spawn, reap = [], []
    worker = tx = graceful = None
    prefork.on('spawn', lambda prefork, pid: spawn.append(pid))

    @prefork.on('heartbeat')
    def heartbeat(prefork, pid):
        global worker, tx
        worker = pid
        if prefork.healthy < 4:
            return
        ua = Pyjo.UserAgent.new()
        tx = ua.get(f'http://127.0.0.1:{prefork.ports()[0]}')
        ua.ioloop.reset()
        # Unlike Mojolicious: TERM shuts the server down gracefully, where Mojo has QUIT
        os.kill(os.getpid(), signal.SIGTERM)

    prefork.on('reap', lambda prefork, pid: reap.append(pid))
    prefork.on('finish', finish)
    prefork.run()
    is_deeply_ok(server, [4], 'server method has been called once')
    is_ok(len(spawn), 4, 'four workers spawned')
    is_ok(len(reap), 4, 'four workers reaped')
    ok(worker in spawn, 'worker has a heartbeat')
    ok(graceful, 'server has been stopped gracefully')
    is_deeply_ok(sorted(spawn), sorted(reap), 'same process ids')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, b'Your Pyjo is working!', 'right content of the application')
    del prefork
    gc.collect()


with subtest('One worker and immediate shutdown'):
    prefork = Pyjo.Server.Prefork.new(
        accepts=500, heartbeat_interval=0.5, listen=['http://*'], pid_file=tempdir().child('prefork.pid'), workers=1
    )
    spawn, reap = [], []
    tx = graceful = None
    prefork.unsubscribe('request')

    @prefork.on('request')
    def request(prefork, tx):
        tx.res.code = 200
        tx.res.body = b'works too!'
        tx.resume()

    prefork.on('spawn', lambda prefork, pid: spawn.append(pid))

    @prefork.once('heartbeat')
    def heartbeat(prefork, pid):
        global tx
        ua = Pyjo.UserAgent.new()
        tx = ua.get(f'http://127.0.0.1:{prefork.ports()[0]}')
        ua.ioloop.reset()
        # Unlike Mojolicious: QUIT shuts the server down immediately, where Mojo has TERM
        os.kill(os.getpid(), signal.SIGQUIT)

    prefork.on('reap', lambda prefork, pid: reap.append(pid))
    prefork.on('finish', finish)
    prefork.run()
    is_ok(prefork.ioloop.max_accepts, 500, 'right value')
    is_ok(len(spawn), 1, 'one worker spawned')
    is_ok(len(reap), 1, 'one worker reaped')
    ok(not graceful, 'server has been stopped immediately')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, b'works too!', 'right content')

# Not in Mojolicious: a worker that gets TERM before it has its handler stops, where Mojo's serves on
with subtest('TERM right after the fork'):
    prefork = Pyjo.Server.Prefork.new(
        heartbeat_interval=0.5, listen=['http://127.0.0.1'], pid_file=tempdir().child('prefork.pid'), workers=1
    )
    spawn, reap, heartbeats = [], [], []

    @prefork.on('spawn')
    def quit(prefork, pid):
        if not len(spawn):
            os.kill(pid, signal.SIGTERM)
        spawn.append(pid)

    @prefork.on('heartbeat')
    def count(prefork, pid):
        heartbeats.append(pid)
        if len(heartbeats) > 4:
            os.kill(os.getpid(), signal.SIGINT)

    prefork.on('reap', lambda prefork, pid: reap.append(pid))
    prefork.run()
    ok(heartbeats.count(spawn[0]) < 5, 'first worker has stopped')
    is_ok(reap[0], spawn[0], 'first worker reaped')


# Not in Mojolicious: a second INT, as of Ctrl-C pressed twice, shuts the server down immediately after a graceful
# shutdown, and a second TERM does not
with subtest('Second INT and TERM'):

    def second_signal(second):
        prefork = Pyjo.Server.Prefork.new(
            heartbeat_interval=0.5, listen=['http://127.0.0.1'], pid_file=tempdir().child('prefork.pid'), workers=1
        )
        prefork.unsubscribe('request')

        # A request that keeps the worker from stopping gracefully
        @prefork.on('request')
        def request(prefork, tx):
            pass

        finished, connections, signalled = [], [], []
        prefork.on('finish', lambda prefork, graceful: finished.append(graceful))

        @prefork.once('heartbeat')
        def heartbeat(prefork, pid):
            connections.append(connection := socket.create_connection(('127.0.0.1', prefork.ports()[0])))
            connection.sendall(b'GET / HTTP/1.1\r\nHost: x\r\n\r\n')
            signalled.append(time.monotonic())
            os.kill(os.getpid(), signal.SIGINT)

            # The second signal once the manager has handled the first, as Python handles two of the same signal that
            # come before its handler runs once
            @prefork.once('finish')
            def again(prefork, graceful):
                os.kill(os.getpid(), second)

        prefork.graceful_timeout = 2
        prefork.run()
        for connection in connections:
            connection.close()
        # The time since the first signal, without the start of the workers
        return finished, time.monotonic() - signalled[0]

    finished, elapsed = second_signal(signal.SIGTERM)
    is_deeply_ok(finished, [True], 'a second TERM does nothing')
    finished, elapsed = second_signal(signal.SIGINT)
    is_deeply_ok(finished, [True, False], 'a second INT shuts the server down immediately')
    ok(elapsed < 2, 'stopped before the graceful timeout')

# Not in Mojolicious: the manager and the workers close their copies of the listen sockets when the server stops
# gracefully, so that a new connection is refused, while a request in progress keeps the worker
with subtest('A new connection while it stops gracefully'):
    prefork = Pyjo.Server.Prefork.new(
        heartbeat_interval=0.5, listen=['http://127.0.0.1'], pid_file=tempdir().child('prefork.pid'), workers=1
    )
    prefork.graceful_timeout = 5
    prefork.unsubscribe('request')

    # A request that keeps the worker from stopping gracefully
    @prefork.on('request')
    def request(prefork, tx):
        pass

    connections, refused, finished = [], [], []

    @prefork.once('heartbeat')
    def heartbeat(prefork, pid):
        port = prefork.ports()[0]
        connections.append(connection := socket.create_connection(('127.0.0.1', port)))
        connection.sendall(b'GET / HTTP/1.1\r\nHost: x\r\n\r\n')
        os.kill(os.getpid(), signal.SIGTERM)

        # A new connection each time the manager waits, until one is refused
        @prefork.on('wait')
        def wait(prefork):
            if refused:
                return
            try:
                socket.create_connection(('127.0.0.1', port), timeout=1).close()
            # A connection that comes while the socket closes is reset, as a refused one is
            except (ConnectionRefusedError, ConnectionResetError):
                refused.append(time.monotonic())

    prefork.on('finish', lambda prefork, graceful: finished.append(time.monotonic()))
    prefork.run()
    for connection in connections:
        connection.close()
    ok(refused, 'a new connection is refused')
    ok(refused and refused[0] - finished[0] < 3, 'refused before the graceful timeout')

# Not in Mojolicious: the delay of a graceful shutdown, which the manager tells the workers with USR1, while they
# serve as before and readiness fails, and the listen sockets are closed after it
with subtest('Shutdown delay'):
    import Pyjoyment

    import http.client

    app = Pyjoyment.new()
    app.log.level = 'fatal'
    app.plugin('Health')
    app.routes.get('/wait').to(cb=lambda c: c.render_later())
    prefork = Pyjo.Server.Prefork.new(
        app=app,
        heartbeat_interval=0.5,
        listen=['http://127.0.0.1'],
        pid_file=tempdir().child('prefork.pid'),
        shutdown_delay=1,
        workers=1,
    )
    prefork.graceful_timeout = 2

    def get(port, path):
        connection = http.client.HTTPConnection('127.0.0.1', port, timeout=2)
        try:
            connection.request('GET', path)
            return connection.getresponse().status
        finally:
            connection.close()

    connections, codes, refused, finished, started = [], {'livez': [], 'readyz': []}, [], [], []
    waits = []

    @prefork.once('heartbeat')
    def heartbeat(prefork, id):
        port = prefork.ports()[0]
        # A request that keeps the worker from stopping gracefully
        connections.append(connection := socket.create_connection(('127.0.0.1', port)))
        connection.sendall(b'GET /wait HTTP/1.1\r\nHost: x\r\n\r\n')
        started.append(time.monotonic())
        os.kill(os.getpid(), signal.SIGTERM)

        # The probes during the delay, and a new connection after it, each time the manager waits
        @prefork.on('wait')
        def wait(prefork):
            elapsed = time.monotonic() - started[0]
            if elapsed < 0.8:
                for path in codes:
                    codes[path].append(get(port, f'/{path}'))
            elif elapsed > 1.2:
                waits.append(elapsed)
                if refused:
                    return
                try:
                    socket.create_connection(('127.0.0.1', port), timeout=1).close()
                # A connection that comes while the socket closes is reset, as a refused one is
                except (ConnectionRefusedError, ConnectionResetError):
                    refused.append(elapsed)

    prefork.on('finish', lambda prefork, graceful: finished.append(time.monotonic()))
    prefork.run()
    for connection in connections:
        connection.close()
    ok(codes['livez'] and set(codes['livez']) == {200}, 'served during the delay')
    ok(503 in codes['readyz'], 'not ready during the delay')
    ok(finished and finished[0] - started[0] >= 1, 'graceful shutdown after the delay')
    ok(len(waits) < 50, f'the manager waits as before after the delay ({len(waits)} times)')
    ok(refused, 'a new connection is refused after the delay')

# Not in Mojolicious: HUP restarts the workers gracefully, or emits the event "reload"
with subtest('HUP'):
    prefork = Pyjo.Server.Prefork.new(
        heartbeat_interval=0.5, listen=['http://127.0.0.1'], pid_file=tempdir().child('prefork.pid'), workers=1
    )
    spawn, reap = [], []
    prefork.on('spawn', lambda prefork, pid: spawn.append(pid))

    @prefork.on('reap')
    def reaped(prefork, pid):
        reap.append(pid)
        os.kill(os.getpid(), signal.SIGTERM)

    prefork.once('heartbeat', lambda prefork, pid: os.kill(os.getpid(), signal.SIGHUP))
    prefork.run()
    ok(len(spawn) >= 2, 'worker restarted')
    is_ok(reap[0], spawn[0], 'first worker stopped')

    prefork = Pyjo.Server.Prefork.new(
        heartbeat_interval=0.5, listen=['http://127.0.0.1'], pid_file=tempdir().child('prefork.pid'), workers=1
    )
    reloads = []

    @prefork.on('reload')
    def reload(prefork):
        reloads.append(True)
        os.kill(os.getpid(), signal.SIGTERM)

    prefork.once('heartbeat', lambda prefork, pid: os.kill(os.getpid(), signal.SIGHUP))
    prefork.run()
    is_deeply_ok(reloads, [True], 'event emitted')

done_testing()
