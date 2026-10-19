import Pyjo.IOLoop
import Pyjo.Promise
import Pyjo.Server.Daemon
import Pyjo.UserAgent
import Pyjoyment

from Pyjo.Test import *

import gc
import threading


# Each thread has an event loop of its own, the singleton of the thread, as each thread of Perl has a copy of the
# interpreter with its own; the main thread keeps the singleton of the module

app = Pyjoyment.new()
app.log.level = 'fatal'
app.routes.get('/', {'text': 'thread'})

main = Pyjo.IOLoop.singleton


def in_thread(target, *args):
    # What the target returns in a thread of its own, or the exception it raises
    results = []

    def run():
        try:
            results.append((True, target(*args)))
        except BaseException as e:
            results.append((False, e))

    thread = threading.Thread(target=run)
    thread.start()
    thread.join()
    succeeded, result = results[0]
    if not succeeded:
        raise result
    return result


def daemon_in_cycle():
    daemon = Pyjo.Server.Daemon.new(app=app, listen=['http://127.0.0.1'], silent=True).start()
    daemon.cycle = daemon
    return daemon.acceptors[0]


with subtest('The singleton of the main thread'):
    ok(Pyjo.IOLoop.singleton is main, 'same singleton')
    ok(Pyjo.IOLoop.object.singleton() is main, 'same singleton of the class')

with subtest('The singleton of another thread'):

    def singletons():
        loop = Pyjo.IOLoop.singleton
        return [
            loop is not main,
            Pyjo.IOLoop.singleton is loop,
            Pyjo.IOLoop.object.singleton() is loop,
            loop.reactor is not main.reactor,
        ]

    is_deeply_ok(in_thread(singletons), [True, True, True, True], 'singleton and reactor of the thread')
    is_deeply_ok(in_thread(lambda: Pyjo.IOLoop.singleton is not main), True, 'singleton of another thread')

with subtest('The functions of the module in another thread'):

    def functions():
        got = []

        def timer(loop):
            got.append(loop is Pyjo.IOLoop.singleton and loop is not main)
            got.append(Pyjo.IOLoop.is_running())
            Pyjo.IOLoop.stop()

        Pyjo.IOLoop.timer(0.01, timer)
        Pyjo.IOLoop.start()
        got.append(Pyjo.IOLoop.is_running())
        return got

    is_deeply_ok(in_thread(functions), [True, True, False], 'timer, is_running, start and stop of the thread')
    ok(not main.is_running, 'singleton of the main thread is not running')

with subtest('Event loops of threads at the same time'):
    barrier = threading.Barrier(3, timeout=10)
    got = []

    def run(name):
        def tick(loop):
            got.append((name, Pyjo.IOLoop.is_running()))
            # All three event loops are running here
            barrier.wait()
            loop.stop()

        Pyjo.IOLoop.next_tick(tick)
        Pyjo.IOLoop.start()

    threads = [threading.Thread(target=run, args=(name,)) for name in ('a', 'b')]
    for thread in threads:
        thread.start()
    run('main')
    for thread in threads:
        thread.join()
    is_deeply_ok(sorted(got), [('a', True), ('b', True), ('main', True)], 'three event loops')

with subtest('A promise in another thread'):

    def promise():
        got = []
        Pyjo.Promise.timer(0.01, 'thread').then(got.append).wait()
        return got

    is_deeply_ok(in_thread(promise), ['thread'], 'promise of the thread')

with subtest('A server in another thread'):
    ports = []
    started = threading.Event()
    stopping = threading.Event()

    def serve():
        with Pyjo.Server.Daemon.new(app=app, listen=['http://127.0.0.1'], silent=True) as daemon:
            ports.append(daemon.start().ports()[0])
            ports.append(daemon.ioloop is Pyjo.IOLoop.singleton and daemon.ioloop is not main)
            Pyjo.IOLoop.recurring(0.01, lambda loop: stopping.is_set() and loop.stop())
            started.set()
            Pyjo.IOLoop.start()

    thread = threading.Thread(target=serve)
    thread.start()
    started.wait(10)
    try:
        with Pyjo.UserAgent.new() as ua:
            tx = ua.get(f'http://127.0.0.1:{ports[0]}/')
            is_ok(tx.res.code, 200, 'right status')
            is_ok(tx.res.text, 'thread', 'right content')
    finally:
        stopping.set()
        thread.join()
    ok(ports[1], 'server on the singleton of the thread')
    ok(not main.is_running, 'singleton of the main thread is not running')

with subtest('A finalizer in another thread cleans up in the thread of the event loop'):
    loops = []
    seen = []
    created = threading.Event()
    collected = threading.Event()

    def thread_loop():
        id = daemon_in_cycle()
        loops.append((Pyjo.IOLoop.singleton, id))

        def check(loop):
            seen.append(bool(Pyjo.IOLoop.acceptor(id)))
            loop.stop()

        # The event loop of the thread waits in a callback while the main thread collects the daemon
        def blocked(loop):
            created.set()
            collected.wait(10)
            loop.timer(0.05, check)

        Pyjo.IOLoop.next_tick(blocked)
        Pyjo.IOLoop.start()

    # The garbage collector runs only where it is called, not in the thread that allocates
    gc.disable()
    try:
        thread = threading.Thread(target=thread_loop)
        thread.start()
        created.wait(10)
        gc.collect()
        loop, id = loops.pop()
        seen.append(bool(loop.acceptor(id)))
        del loop
        collected.set()
        thread.join()
    finally:
        gc.enable()
    is_deeply_ok(seen, [True, False], 'acceptor removed by the event loop of the thread')

done_testing()
