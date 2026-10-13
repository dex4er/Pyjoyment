import Pyjo.Exception
import Pyjo.Reactor.Asyncio

from Pyjo.Test import *

import asyncio
import re
import socket


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

done_testing()
