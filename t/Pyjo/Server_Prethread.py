import Pyjo.IOLoop
import Pyjo.Server.Prethread
import Pyjo.UserAgent
import Pyjoyment.HelloWorld

from Pyjo.File import curfile, path, tempdir
from Pyjo.Test import *

import gc
import os
import re
import signal
import socket
import threading
import time


# The tests of Pyjo.Server.Prefork for the threads of Pyjo.Server.Prethread, with the ids of the threads for the process
# ids of the workers, and the tests of what threads do otherwise; a server listens on a port that the system picks,
# which ports() gives, and has a process id file of its own


def message(log_, level, *lines):
    global log
    log += lines[-1]


def finish(prethread, graceful_):
    global graceful
    graceful = graceful_


with subtest('Manage and clean up PID file'):
    prethread = Pyjo.Server.Prethread.new()
    dir = tempdir()
    like_ok(str(prethread.pid_file), r'prethread\.pid$', 'has default path')
    file = dir.child('prethread.pid')
    prethread.pid_file = file
    ok(not prethread.check_pid(), 'no process id')
    prethread.ensure_pid_file(os.getpid())
    ok(os.path.exists(file), 'file exists')
    is_ok(path(file).slurp(), f'{os.getpid()}\n'.encode(), 'right process id')
    is_ok(prethread.check_pid(), os.getpid(), 'right process id')
    del prethread
    gc.collect()
    ok(not os.path.exists(file), 'file has been cleaned up')

with subtest('Bad PID file'):
    bad = curfile().sibling('does_not_exist', 'test.pid')
    prethread = Pyjo.Server.Prethread.new(pid_file=bad)
    prethread.app.log.level = 'trace'
    prethread.app.log.unsubscribe('message')
    log = ''
    cb = prethread.app.log.on('message', message)
    throws_ok(
        lambda: prethread.ensure_pid_file(os.getpid()), re.compile(r"Can't create process id file"), 'right error'
    )
    like_ok(log, r"Can't create process id file", 'right message')
    prethread.app.log.unsubscribe('message', cb)

with subtest('Multiple workers and graceful shutdown'):
    dir = tempdir()
    file = dir.child('prethread.pid')
    prethread = Pyjo.Server.Prethread.new(
        app=Pyjoyment.HelloWorld.new(), heartbeat_interval=0.5, listen=['http://*'], pid_file=file
    )
    prethread.unsubscribe('request')
    served = []

    @prethread.on('request')
    def request(prethread, tx):
        # The event loop of the thread of the worker
        served.append((threading.get_native_id(), Pyjo.IOLoop.singleton is not prethread_loop))
        tx.res.code = 200
        tx.res.body = b'just works!'
        tx.resume()

    prethread_loop = prethread.ioloop
    is_ok(prethread.workers, 4, 'start with four workers')
    spawn, reap = [], []
    worker = tx = graceful = None
    prethread.on('spawn', lambda prethread, id: spawn.append(id))

    @prethread.on('heartbeat')
    def heartbeat(prethread, id):
        global worker, tx
        worker = id
        if prethread.healthy < 4:
            return
        with Pyjo.UserAgent.new() as ua:
            tx = ua.get(f'http://127.0.0.1:{prethread.ports()[0]}')
        os.kill(os.getpid(), signal.SIGTERM)

    prethread.on('reap', lambda prethread, id: reap.append(id))
    prethread.on('finish', finish)
    prethread.app.log.level = 'trace'
    prethread.app.log.unsubscribe('message')
    log = ''
    cb = prethread.app.log.on('message', message)
    is_ok(prethread.healthy, 0, 'no healthy workers')
    server = []

    def before_server_start(server_, app):
        server.extend([server_.workers, app.mode])

    prethread.app.hook('before_server_start', before_server_start)
    prethread.run()
    is_deeply_ok(server, [4, 'development'], 'hook has been emitted once')
    is_ok(len(spawn), 4, 'four workers spawned')
    is_ok(len(reap), 4, 'four workers reaped')
    ok(worker in spawn, 'worker has a heartbeat')
    ok(os.getpid() not in spawn, 'workers are threads')
    ok(graceful, 'server has been stopped gracefully')
    is_deeply_ok(sorted(spawn), sorted(reap), 'same thread ids')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, b'just works!', 'right content')
    is_ok(len(served), 1, 'one request')
    ok(served[0][0] in spawn, 'served by a worker')
    ok(served[0][1], 'on the event loop of the thread')
    like_ok(log, r'Listening at', 'right message')
    like_ok(log, rf'Manager {os.getpid()} started', 'right message')
    like_ok(log, r'Creating process id file', 'right message')
    like_ok(log, rf'Worker {spawn[0]} started', 'right message')
    like_ok(log, rf'Stopping worker {spawn[0]} gracefully \(25 seconds\)', 'right message')
    like_ok(log, rf'Worker {spawn[0]} stopped', 'right message')
    like_ok(log, rf'Manager {os.getpid()} stopped', 'right message')
    prethread.app.log.unsubscribe('message', cb)
    is_deeply_ok(
        [t.name for t in threading.enumerate() if t.name.startswith('Pyjo.Server.Prethread')], [], 'no threads left'
    )

    is_ok(prethread.check_pid(), os.getpid(), 'right process id')
    pid = prethread.pid_file
    ok(os.path.exists(pid), 'process id file has been created')
    del prethread
    gc.collect()
    ok(not os.path.exists(pid), 'process id file has been removed')

with subtest('Multiple workers and graceful shutdown (Pyjo.HelloWorld)'):
    import Pyjo.HelloWorld

    server = []

    class HelloWorld(Pyjo.HelloWorld.object):
        def server(self, server_):
            server.append(server_.workers)

    prethread = Pyjo.Server.Prethread.new(
        app=HelloWorld.new(), heartbeat_interval=0.5, listen=['http://*'], pid_file=tempdir().child('prethread.pid')
    )
    spawn, reap = [], []
    tx = None

    @prethread.on('heartbeat')
    def heartbeat(prethread, id):
        global tx
        if prethread.healthy < 4:
            return
        with Pyjo.UserAgent.new() as ua:
            tx = ua.get(f'http://127.0.0.1:{prethread.ports()[0]}')
        os.kill(os.getpid(), signal.SIGTERM)

    prethread.on('spawn', lambda prethread, id: spawn.append(id))
    prethread.on('reap', lambda prethread, id: reap.append(id))
    prethread.run()
    is_deeply_ok(server, [4], 'server method has been called once')
    is_deeply_ok(sorted(spawn), sorted(reap), 'four workers spawned and reaped')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, b'Your Pyjo is working!', 'right content of the application')

with subtest('One worker and immediate shutdown'):
    prethread = Pyjo.Server.Prethread.new(
        accepts=500,
        heartbeat_interval=0.5,
        listen=['http://*'],
        pid_file=tempdir().child('prethread.pid'),
        workers=1,
    )
    spawn, reap, accepts = [], [], []
    tx = graceful = None
    prethread.unsubscribe('request')

    @prethread.on('request')
    def request(prethread, tx):
        accepts.append(Pyjo.IOLoop.singleton.max_accepts)
        tx.res.code = 200
        tx.res.body = b'works too!'
        tx.resume()

    prethread.on('spawn', lambda prethread, id: spawn.append(id))

    @prethread.once('heartbeat')
    def heartbeat(prethread, id):
        global tx
        with Pyjo.UserAgent.new() as ua:
            tx = ua.get(f'http://127.0.0.1:{prethread.ports()[0]}')
        os.kill(os.getpid(), signal.SIGQUIT)

    prethread.on('reap', lambda prethread, id: reap.append(id))
    prethread.on('finish', finish)
    prethread.run()
    is_deeply_ok(accepts, [500], 'right value')
    is_ok(len(spawn), 1, 'one worker spawned')
    is_ok(len(reap), 1, 'one worker reaped')
    ok(not graceful, 'server has been stopped immediately')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, b'works too!', 'right content')

with subtest('UNIX domain socket'):
    dir = tempdir()
    sock = dir.child('prethread.sock').to_str()
    prethread = Pyjo.Server.Prethread.new(
        listen=[f'http+unix://{sock.replace("/", "%2F")}'], pid_file=dir.child('prethread.pid'), workers=2
    )
    prethread.unsubscribe('request')

    @prethread.on('request')
    def request(prethread, tx):
        tx.res.code = 200
        tx.res.body = b'unix'
        tx.resume()

    tx = None

    @prethread.on('heartbeat')
    def heartbeat(prethread, id):
        global tx
        if prethread.healthy < 2:
            return
        with Pyjo.UserAgent.new() as ua:
            tx = ua.get(f'http+unix://{sock.replace("/", "%2F")}/')
        os.kill(os.getpid(), signal.SIGTERM)

    prethread.heartbeat_interval = 0.5
    prethread.run()
    is_ok(tx.res.body, b'unix', 'right content')
    ok(os.path.exists(sock), 'socket is still there')

with subtest('Second INT and TERM'):

    def second_signal(second):
        prethread = Pyjo.Server.Prethread.new(
            heartbeat_interval=0.5, listen=['http://127.0.0.1'], pid_file=tempdir().child('prethread.pid'), workers=1
        )
        prethread.unsubscribe('request')

        # A request that keeps the worker from stopping gracefully
        @prethread.on('request')
        def request(prethread, tx):
            pass

        finished, connections = [], []
        prethread.on('finish', lambda prethread, graceful: finished.append(graceful))

        @prethread.once('heartbeat')
        def heartbeat(prethread, id):
            connections.append(connection := socket.create_connection(('127.0.0.1', prethread.ports()[0])))
            connection.sendall(b'GET / HTTP/1.1\r\nHost: x\r\n\r\n')
            os.kill(os.getpid(), signal.SIGINT)

            @prethread.once('wait')
            def again(prethread):
                os.kill(os.getpid(), second)

        prethread.graceful_timeout = 2
        started = time.monotonic()
        prethread.run()
        for connection in connections:
            connection.close()
        return finished, time.monotonic() - started

    finished, elapsed = second_signal(signal.SIGTERM)
    is_deeply_ok(finished, [True], 'a second TERM does nothing')
    finished, elapsed = second_signal(signal.SIGINT)
    is_deeply_ok(finished, [True, False], 'a second INT shuts the server down immediately')
    ok(elapsed < 2, 'stopped before the graceful timeout')

with subtest('HUP'):
    prethread = Pyjo.Server.Prethread.new(
        heartbeat_interval=0.5, listen=['http://127.0.0.1'], pid_file=tempdir().child('prethread.pid'), workers=1
    )
    spawn, reap = [], []
    prethread.on('spawn', lambda prethread, id: spawn.append(id))

    @prethread.on('reap')
    def reaped(prethread, id):
        reap.append(id)
        os.kill(os.getpid(), signal.SIGTERM)

    prethread.once('heartbeat', lambda prethread, id: os.kill(os.getpid(), signal.SIGHUP))
    prethread.run()
    ok(len(spawn) >= 2, 'worker restarted')
    is_ok(reap[0], spawn[0], 'first worker stopped')

    prethread = Pyjo.Server.Prethread.new(
        heartbeat_interval=0.5, listen=['http://127.0.0.1'], pid_file=tempdir().child('prethread.pid'), workers=1
    )
    reloads = []

    @prethread.on('reload')
    def reload(prethread):
        reloads.append(True)
        os.kill(os.getpid(), signal.SIGTERM)

    prethread.once('heartbeat', lambda prethread, id: os.kill(os.getpid(), signal.SIGHUP))
    prethread.run()
    is_deeply_ok(reloads, [True], 'event emitted')

with subtest('A worker that does not stop is left'):
    prethread = Pyjo.Server.Prethread.new(
        graceful_timeout=0.5,
        heartbeat_interval=0.2,
        listen=['http://127.0.0.1'],
        pid_file=tempdir().child('prethread.pid'),
        workers=1,
    )
    prethread.unsubscribe('request')
    release = threading.Event()

    # A request that blocks the event loop of the worker
    @prethread.on('request')
    def request(prethread, tx):
        release.wait(30)

    prethread.app.log.level = 'trace'
    prethread.app.log.unsubscribe('message')
    log = ''
    cb = prethread.app.log.on('message', message)
    connections = []

    @prethread.once('heartbeat')
    def heartbeat(prethread, id):
        connections.append(connection := socket.create_connection(('127.0.0.1', prethread.ports()[0])))
        connection.sendall(b'GET / HTTP/1.1\r\nHost: x\r\n\r\n')
        prethread.once('wait', lambda prethread: os.kill(os.getpid(), signal.SIGTERM))

    started = time.monotonic()
    prethread.run()
    elapsed = time.monotonic() - started
    release.set()
    for connection in connections:
        connection.close()
    prethread.app.log.unsubscribe('message', cb)
    ok(elapsed < 10, 'manager stopped')
    like_ok(log, r'Worker \d+ does not stop, leaving it', 'right message')

with subtest('The manager leaves the children of the application'):
    prethread = Pyjo.Server.Prethread.new(
        heartbeat_interval=0.5, listen=['http://127.0.0.1'], pid_file=tempdir().child('prethread.pid'), workers=1
    )
    handler = signal.getsignal(signal.SIGCHLD)
    handlers = []

    @prethread.once('heartbeat')
    def heartbeat(prethread, id):
        handlers.append(signal.getsignal(signal.SIGCHLD))
        os.kill(os.getpid(), signal.SIGTERM)

    prethread.run()
    is_deeply_ok(handlers, [handler], 'no handler of CHLD')

done_testing()
