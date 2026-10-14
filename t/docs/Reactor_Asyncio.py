from Pyjo.Test import *

import asyncio
import contextlib
import io
import socket


with subtest('Synopsis'):
    first, peer = socket.socketpair()
    second, other = socket.socketpair()
    fd = second.fileno()
    other.sendall(b'x')

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        import Pyjo.Reactor.Asyncio

        # Watch if handle becomes readable or writable
        reactor = Pyjo.Reactor.Asyncio.new()
        reactor.io(
            first,
            lambda reactor, writable: print('First handle is writable' if writable else 'First handle is readable'),
        )

        # Change to watching only if handle becomes writable
        reactor.watch(first, False, True)

        # Watch a file descriptor if it becomes readable
        reactor.io(
            fd,
            lambda reactor, writable: print('Second handle is writable' if writable else 'Second handle is readable'),
        ).watch(fd, True, False)

        # Add a timer
        def timeout(reactor):
            reactor.remove(first)
            reactor.remove(fd)
            print('Timeout!')

        reactor.timer(0.05, timeout)

        # Start reactor if necessary
        if not reactor.is_running:
            reactor.start()
    lines = output.getvalue().splitlines()
    ok('First handle is writable' in lines, 'first handle')
    ok('Second handle is readable' in lines, 'second handle')
    is_ok(lines[-1], 'Timeout!', 'timeout')
    ok('First handle is readable' not in lines, 'not readable')
    for sock in (first, peer, second, other):
        sock.close()

with subtest('new'):
    reactor = Pyjo.Reactor.Asyncio.new()
    isa_ok(reactor.loop, asyncio.AbstractEventLoop, 'own loop')
    loop = asyncio.new_event_loop()
    reactor = Pyjo.Reactor.Asyncio.new(loop=loop)
    is_ok(reactor.loop, loop, 'given loop')
    loop.close()

with subtest('again'):
    reactor = Pyjo.Reactor.Asyncio.new()
    id = reactor.timer(10, lambda reactor: None)
    reactor.again(id)
    reactor.again(id, 0.5)
    ok(reactor.remove(id), 'restarted timer')

with subtest('io'):
    handle, peer = socket.socketpair()
    reactor = Pyjo.Reactor.Asyncio.new()
    events = []

    # Callback will be executed twice if handle becomes readable and writable
    reactor.io(handle, lambda reactor, writable: print('Handle is writable' if writable else 'Handle is readable'))
    reactor.io(handle, lambda reactor, writable: events.append(writable) or reactor.stop())
    peer.sendall(b'x')
    reactor.start()
    ok(len(events), 'event')
    reactor.remove(handle)
    handle.close()
    peer.close()

with subtest('next_tick and one_tick'):
    reactor = Pyjo.Reactor.Asyncio.new()
    none = reactor.next_tick(lambda reactor: None)
    is_ok(none, None, 'always None')

    # Don't block longer than 0.5 seconds
    id = reactor.timer(0.5, lambda reactor: None)
    reactor.one_tick()
    reactor.remove(id)
    pass_ok('one tick')

with subtest('recurring, timer, remove and stop'):
    reactor = Pyjo.Reactor.Asyncio.new()
    id = reactor.recurring(0.25, lambda reactor: None)
    boolean = reactor.remove(id)
    ok(boolean, 'removed')
    id = reactor.timer(0.5, lambda reactor: reactor.stop())
    reactor.start()
    ok(not reactor.remove(id), 'fired')

with subtest('reset'):
    reactor = Pyjo.Reactor.Asyncio.new()
    reactor.timer(10, lambda reactor: None)
    reactor.reset()
    reactor.start()
    pass_ok('nothing to watch')

with subtest('awaitable and coroutine'):
    import Pyjo.IOLoop
    import Pyjo.Promise

    reactor = Pyjo.Reactor.Asyncio.new()
    loop = Pyjo.IOLoop.new(reactor=reactor)
    promise = Pyjo.Promise.new().set(ioloop=loop).timer(0.01, 'done')
    future = reactor.awaitable(promise)
    isa_ok(future, asyncio.Future, 'future of the loop')

    async def coro():
        await asyncio.sleep(0)
        return await promise

    got = []
    reactor.run_coroutine(coro(), got.append, got.append)
    Pyjo.Promise.new().set(ioloop=loop).timer(0.05).wait()
    is_deeply_ok(got, ['done'], 'task of the loop')

with subtest('future'):
    reactor = Pyjo.Reactor.Asyncio.new()
    future = reactor.future()
    isa_ok(future, asyncio.Future, 'future of the loop')
    ok(future.get_loop() is reactor.loop, 'right loop')

with subtest('watch'):
    handle, peer = socket.socketpair()
    reactor = Pyjo.Reactor.Asyncio.new()
    reactor.io(handle, lambda reactor, writable: None)

    # Watch only for readable events
    reactor.watch(handle, True, False)

    # Watch only for writable events
    reactor.watch(handle, False, True)

    # Watch for readable and writable events
    reactor.watch(handle, True, True)

    # Pause watching for events
    reactor.watch(handle, False, False)
    ok(reactor.remove(handle), 'watched')
    handle.close()
    peer.close()

done_testing()
