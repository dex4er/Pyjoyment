from Pyjo.Test import *

import gc
import os
import signal
import sys


# Left out from Mojolicious: TEST_PREFORK, which enables the tests, as they are quick; MOJO_REACTOR, as the tests run on
# the reactor of Pyjo.Reactor.detect()
if not hasattr(os, 'fork'):
    plan(skip_all='no os.fork')

# PyPy with its JIT on macOS: the child of a fork crashes now and then with a bus error, under load
if sys.platform == 'darwin' and getattr(sys, 'pypy_translation_info', {}).get('translation.jit'):
    plan(skip_all='PyPy with its JIT on macOS: the child of a fork crashes now and then with SIGBUS')

import Pyjo.IOLoop.Server
import Pyjo.Server.Prefork
import Pyjo.UserAgent

from Pyjo.File import curfile, path, tempdir

import importlib


# The minimal Mojolicious::Lite of the tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
Lite = importlib.import_module('Lite')


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
    port = Pyjo.IOLoop.Server.object.generate_port()
    # TODO: the default application, when Pyjo.HelloWorld is an application of Pyjoyment with hooks
    prefork = Pyjo.Server.Prefork.new(app=Lite.app, heartbeat_interval=0.5, listen=[f'http://*:{port}'], pid_file=file)
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
        tx = Pyjo.UserAgent.new().get(f'http://127.0.0.1:{port}')
        os.kill(os.getpid(), signal.SIGQUIT)

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
    prefork.run()
    is_deeply_ok(server, [4, 'development'], 'hook has been emitted once')
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
    like_ok(log, rf'Stopping worker {spawn[0]} gracefully \(120 seconds\)', 'right message')
    like_ok(log, rf'Worker {spawn[0]} stopped', 'right message')
    like_ok(log, rf'Manager {os.getpid()} stopped', 'right message')
    prefork.app.log.unsubscribe('message', cb)

    is_ok(prefork.check_pid(), os.getpid(), 'right process id')
    pid = prefork.pid_file
    ok(os.path.exists(pid), 'process id file has been created')
    del prefork
    gc.collect()
    ok(not os.path.exists(pid), 'process id file has been removed')

with subtest('One worker and immediate shutdown'):
    port = Pyjo.IOLoop.Server.object.generate_port()
    prefork = Pyjo.Server.Prefork.new(accepts=500, heartbeat_interval=0.5, listen=[f'http://*:{port}'], workers=1)
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
        tx = Pyjo.UserAgent.new().get(f'http://127.0.0.1:{port}')
        os.kill(os.getpid(), signal.SIGTERM)

    prefork.on('reap', lambda prefork, pid: reap.append(pid))
    prefork.on('finish', finish)
    prefork.run()
    is_ok(prefork.ioloop.max_accepts, 500, 'right value')
    is_ok(len(spawn), 1, 'one worker spawned')
    is_ok(len(reap), 1, 'one worker reaped')
    ok(not graceful, 'server has been stopped immediately')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, b'works too!', 'right content')

# Not in Mojolicious: a worker that gets QUIT before it has its handler stops, where Mojo's serves on
with subtest('QUIT right after the fork'):
    port = Pyjo.IOLoop.Server.object.generate_port()
    prefork = Pyjo.Server.Prefork.new(heartbeat_interval=0.5, listen=[f'http://127.0.0.1:{port}'], workers=1)
    spawn, reap, heartbeats = [], [], []

    @prefork.on('spawn')
    def quit(prefork, pid):
        if not len(spawn):
            os.kill(pid, signal.SIGQUIT)
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

done_testing()
