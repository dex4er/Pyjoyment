import Pyjo.Exception
import Pyjo.Reactor.Asyncio

from Pyjo.Test import *

import asyncio
import os
import re
import socket
import subprocess
import sys


with subtest('Coroutines run in the loop of the reactor'):
    reactor = Pyjo.Reactor.Asyncio.new()
    got = []

    async def coroutine():
        got.append(asyncio.get_running_loop() is reactor.loop)
        await asyncio.sleep(0.01)
        got.append('slept')

    task = reactor.loop.create_task(coroutine())
    reactor.timer(0.05, lambda reactor: reactor.stop())
    reactor.start()
    is_deeply_ok(got, [True, 'slept'], 'task ran while the reactor did')
    ok(task.done(), 'task done')

with subtest('Callbacks see the running loop'):
    reactor = Pyjo.Reactor.Asyncio.new()
    loops = []
    reactor.next_tick(lambda reactor: loops.append(asyncio.get_running_loop()))
    reactor.start()
    is_deeply_ok(loops, [reactor.loop], 'loop of the reactor')

with subtest('Inside asyncio.run'):
    got = []

    async def main():
        reactor = Pyjo.Reactor.Asyncio.new()
        got.append(reactor.loop is asyncio.get_running_loop())
        reactor.timer(0, lambda reactor: got.append('timer'))
        reactor.next_tick(lambda reactor: got.append('next tick'))
        reactor.start()
        got.append('start returned')
        await asyncio.sleep(0.01)
        got.append(reactor.is_running)

    asyncio.run(main())
    is_deeply_ok(got, [True, 'start returned', 'timer', 'next tick', False], 'the running loop watches the events')

with subtest('Unhandled error in a loop that runs already'):
    contexts = []

    def die(reactor):
        raise Exception('Oops')

    async def main():
        asyncio.get_running_loop().set_exception_handler(lambda loop, context: contexts.append(context))
        reactor = Pyjo.Reactor.Asyncio.new()
        reactor.timer(0, die)
        await asyncio.sleep(0.01)

    asyncio.run(main())
    is_ok(len(contexts), 1, 'exception handler of asyncio')
    isa_ok(contexts[0]['exception'], Pyjo.Exception.object, 'error event')

with subtest('Unhandled error raised by start'):
    reactor = Pyjo.Reactor.Asyncio.new()

    def die(reactor):
        raise ValueError('Oops')

    reactor.timer(0, die)
    try:
        reactor.start()
    except Pyjo.Exception.object as e:
        like_ok(str(e), r'Timer failed: Oops', 'message')
        isa_ok(e.__cause__.__cause__, ValueError, 'cause of the error')
    ok(not reactor.is_running, 'not running')

with subtest('Handles and timers move to the loop that is running'):
    reactor = Pyjo.Reactor.Asyncio.new()
    got = []
    reactor.timer(0.01, lambda reactor: got.append(asyncio.get_running_loop()))
    own = reactor.loop

    async def outer():
        # the reactor moves when it is used in the running loop
        reactor.loop
        await asyncio.sleep(0.05)
        return asyncio.get_running_loop()

    running = asyncio.run(outer())
    is_deeply_ok(got, [running], 'the timer ran in the loop that was running')
    reactor.timer(0, lambda reactor: got.append('back'))
    reactor.start()
    is_ok(got[-1], 'back', 'and back in a loop of its own')
    ok(reactor.loop is own, 'the same loop of its own')

with subtest('Handles'):
    reactor = Pyjo.Reactor.Asyncio.new()
    a, b = socket.socketpair()
    reactor.io(a.fileno(), lambda reactor, writable: reactor.stop())
    reactor.start()
    ok(reactor.remove(a), 'file descriptor and socket are the same handle')
    a.close()
    throws_ok(lambda: reactor.remove(a), re.compile(r'^Handle is closed'), 'closed handle')
    b.close()

with subtest('The event loop of a reactor that exists at the exit is closed'):
    script = (
        'import Pyjo.Reactor.Asyncio\n'
        'reactor = Pyjo.Reactor.Asyncio.new()\n'
        'reactor.timer(0, lambda reactor: reactor.stop())\n'
        'reactor.start()\n'
    )
    root = os.path.join(os.path.dirname(__file__), '..', '..')
    env = {**os.environ, 'PYTHONPATH': root, 'PYTHONWARNINGS': 'always::ResourceWarning'}
    process = subprocess.run([sys.executable, '-c', script], env=env, capture_output=True, text=True, timeout=30)
    is_ok(process.returncode, 0, 'exit status')
    unlike_ok(process.stderr, r'unclosed event loop', 'no ResourceWarning')

with subtest('A reactor moves to a new loop in the child of a fork'):
    if not hasattr(os, 'fork'):
        skip('no os.fork', 3)
    else:
        script = """
import Pyjo.Reactor.Asyncio, os, socket

reactor = Pyjo.Reactor.Asyncio.new()
parent = reactor.loop
a, b = socket.socketpair()
got = []
reactor.io(a, lambda reactor, writable: (got.append(a.recv(10)), reactor.stop())).watch(a, True, False)
reactor.timer(0, lambda reactor: b.send(b'io'))
r, w = os.pipe()
pid = os.fork()
if not pid:
    reactor.start()
    os.write(w, f'{reactor.loop is not parent} {got}'.encode())
    os._exit(0)
os.close(w)
os.waitpid(pid, 0)
child = os.read(r, 100).decode()
reactor.start()
print(child, reactor.loop is parent, got)
a.close()
b.close()
"""
        root = os.path.join(os.path.dirname(__file__), '..', '..')
        env = {**os.environ, 'PYTHONPATH': root, 'PYTHONWARNINGS': 'always::ResourceWarning,error::DeprecationWarning'}
        process = subprocess.run([sys.executable, '-c', script], env=env, capture_output=True, text=True, timeout=30)
        is_ok(process.returncode, 0, 'exit status')
        is_ok(process.stdout, "True [b'io'] True [b'io']\n", 'a new loop in the child, the loop of the parent in it')
        is_ok(process.stderr, '', 'no warning')

done_testing()
