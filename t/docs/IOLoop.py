from Pyjo.Test import *

import contextlib
import io
import os
import socket
import subprocess
import sys


# The documentation describes the default reactor
os.environ.pop('PYJO_REACTOR', None)


def free_port():
    with socket.create_server(('127.0.0.1', 0)) as s:
        return s.getsockname()[1]


with subtest('Synopsis'):
    port = free_port()
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        import Pyjo.IOLoop

        # Listen on port 3000
        @Pyjo.IOLoop.server(port=port)
        def server(loop, stream, id):
            @stream.on
            def read(stream, chunk):
                # Process input chunk
                print(chunk)

                # Write response
                stream.write(b'HTTP/1.1 200 OK')

        # Connect to port 3000
        @Pyjo.IOLoop.client(port=port)
        def id(loop, err, stream):
            @stream.on
            def read(stream, chunk):
                # Process input
                print(f'Input: {chunk}')
                loop.stop()

            # Write request
            stream.write(b'GET / HTTP/1.1\x0d\x0a\x0d\x0a')

        # Add a timer
        Pyjo.IOLoop.timer(5, lambda loop: loop.remove(id))

        # Start event loop if necessary
        if not Pyjo.IOLoop.is_running():
            Pyjo.IOLoop.start()
    is_ok(output.getvalue(), "b'GET / HTTP/1.1\\r\\n\\r\\n'\nInput: b'HTTP/1.1 200 OK'\n", 'request and response')
    Pyjo.IOLoop.reset()

with subtest('Decorators'):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):

        @Pyjo.IOLoop.timer(0.01)
        def id(loop):
            print('Timeout!')

        Pyjo.IOLoop.start()
    is_ok(output.getvalue(), 'Timeout!\n', 'timer')
    isa_ok(id, str, 'decorated name is the id')

with subtest('Events'):
    loop = Pyjo.IOLoop.new()
    loop.on('finish', lambda loop: ...)
    loop.on('reset', lambda loop: ...)
    ok(loop.has_subscribers('finish'), 'finish')
    ok(loop.has_subscribers('reset'), 'reset')

with subtest('Debugging'):
    env = dict(os.environ, PYJO_IOLOOP_DEBUG='1')
    env.pop('PYJO_REACTOR', None)
    result = subprocess.run([sys.executable, '-c', 'import Pyjo.IOLoop'], env=env, capture_output=True, text=True)
    is_ok(result.stderr, '-- Reactor initialized (Pyjo.Reactor.Asyncio)\n', 'diagnostics')

with subtest('max_accepts and max_connections'):
    loop = Pyjo.IOLoop.new()
    max = loop.max_accepts
    is_ok(max, 0, 'default')
    loop.max_accepts = 1000
    is_ok(loop.max_accepts, 1000, 'set')
    max = loop.max_connections
    is_ok(max, 1000, 'default')
    loop.max_connections = 100
    is_ok(loop.max_connections, 100, 'set')

with subtest('reactor'):
    import Pyjo.Reactor.Asyncio

    loop = Pyjo.IOLoop.new()
    reactor = loop.reactor
    isa_ok(reactor, Pyjo.Reactor.Asyncio.object, 'default')
    loop.reactor = Pyjo.Reactor.Asyncio.new()
    isnt_ok(loop.reactor, reactor, 'set')

    handle, peer = socket.socketpair()
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        # Watch if handle becomes readable or writable
        Pyjo.IOLoop.singleton.reactor.io(
            handle, lambda reactor, writable: print('Handle is writable' if writable else 'Handle is readable')
        )

        # Change to watching only if handle becomes writable
        Pyjo.IOLoop.singleton.reactor.watch(handle, False, True)
        Pyjo.IOLoop.one_tick()

        # Remove handle again
        Pyjo.IOLoop.singleton.reactor.remove(handle)
    is_ok(output.getvalue(), 'Handle is writable\n', 'watched')
    handle.close()
    peer.close()

with subtest('acceptor'):
    import Pyjo.IOLoop.Server

    loop = Pyjo.IOLoop.new()
    listening = Pyjo.IOLoop.Server.new()
    listening.listen(address='127.0.0.1')
    id = loop.acceptor(listening)
    server = loop.acceptor(id)
    isa_ok(server, Pyjo.IOLoop.Server.object, 'acceptor')
    is_ok(Pyjo.IOLoop.acceptor(id), None, 'not of the singleton')
    loop.reset()

with subtest('client and server'):
    loop = Pyjo.IOLoop.new()
    got = []

    # Listen on random port
    id = loop.server(lambda loop, stream, id: got.append('accepted'), address='127.0.0.1')
    port = loop.acceptor(id).port

    def cb(loop, err, stream):
        got.append('connected')
        loop.stop()

    id = loop.client(cb, address='127.0.0.1', port=port)
    loop.start()
    ok('connected' in got, 'connected')
    isa_ok(id, str, 'id')

    @loop.client(address='127.0.0.1', port=port)
    def id2(loop, err, stream):
        loop.stop()

    loop.start()
    isa_ok(id2, str, 'decorator')

with subtest('is_running'):
    boolean = Pyjo.IOLoop.is_running()
    ok(not boolean, 'module')
    boolean = Pyjo.IOLoop.new().is_running
    ok(not boolean, 'loop')

with subtest('next_tick'):
    got = []
    none = Pyjo.IOLoop.next_tick(lambda loop: got.append('module'))
    is_ok(none, None, 'always None')
    loop = Pyjo.IOLoop.new()
    none = loop.next_tick(lambda loop: got.append('loop'))
    loop.start()

    # Perform operation on next reactor tick
    Pyjo.IOLoop.next_tick(lambda loop: ...)
    Pyjo.IOLoop.start()
    is_deeply_ok(got, ['loop', 'module'], 'ticks')

with subtest('one_tick'):
    # Don't block longer than 0.5 seconds
    id = Pyjo.IOLoop.timer(0.5, lambda loop: None)
    Pyjo.IOLoop.one_tick()
    Pyjo.IOLoop.remove(id)
    pass_ok('one tick')

with subtest('recurring and timer'):
    loop = Pyjo.IOLoop.new()
    ids = [
        Pyjo.IOLoop.recurring(3, lambda loop: ...),
        loop.recurring(0, lambda loop: ...),
        loop.recurring(0.25, lambda loop: ...),
        Pyjo.IOLoop.timer(3, lambda loop: ...),
        loop.timer(0, lambda loop: ...),
        loop.timer(0.25, lambda loop: ...),
    ]

    # Perform operation every 5 seconds
    ids.append(Pyjo.IOLoop.recurring(5, lambda loop: ...))

    # Perform operation in 5 seconds
    ids.append(Pyjo.IOLoop.timer(5, lambda loop: ...))
    ok(all(isinstance(id, str) for id in ids), 'ids')
    Pyjo.IOLoop.reset()
    loop.reset()

with subtest('remove and reset'):
    loop = Pyjo.IOLoop.new()
    id = Pyjo.IOLoop.timer(10, lambda loop: None)
    Pyjo.IOLoop.remove(id)
    id = loop.timer(10, lambda loop: None)
    loop.remove(id)
    Pyjo.IOLoop.reset()
    loop.reset()
    loop.reset(freeze=True)
    pass_ok('removed and reset')

with subtest('singleton'):
    loop = Pyjo.IOLoop.object.singleton()
    is_ok(loop, Pyjo.IOLoop.singleton, 'singleton')

    # Many methods also allow you to take shortcuts
    Pyjo.IOLoop.timer(0.01, lambda loop: Pyjo.IOLoop.stop())
    Pyjo.IOLoop.start()

    # Restart active timer
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        id = Pyjo.IOLoop.timer(0.01, lambda loop: print('Timeout!'))
        Pyjo.IOLoop.singleton.reactor.again(id)
        Pyjo.IOLoop.start()
    is_ok(output.getvalue(), 'Timeout!\n', 'restarted')

    handle, peer = socket.socketpair()
    fd = handle.fileno()
    peer.sendall(b'x')
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        # Watch a file descriptor if it becomes readable
        Pyjo.IOLoop.singleton.reactor.io(
            fd, lambda reactor, writable: print('Handle is writable' if writable else 'Handle is readable')
        ).watch(fd, True, False)
        Pyjo.IOLoop.one_tick()
    Pyjo.IOLoop.singleton.reactor.remove(fd)
    is_ok(output.getvalue(), 'Handle is readable\n', 'watched')
    handle.close()
    peer.close()

with subtest('start and stop'):
    Pyjo.IOLoop.timer(0.01, lambda loop: Pyjo.IOLoop.stop())

    # Start event loop only if it is not running already
    if not Pyjo.IOLoop.is_running():
        Pyjo.IOLoop.start()
    loop = Pyjo.IOLoop.new()
    loop.timer(0.01, lambda loop: loop.stop())
    loop.start()
    pass_ok('stopped')

with subtest('stop_gracefully'):
    loop = Pyjo.IOLoop.new()
    loop.next_tick(lambda loop: loop.stop_gracefully())
    loop.start()
    Pyjo.IOLoop.next_tick(lambda loop: Pyjo.IOLoop.stop_gracefully())
    Pyjo.IOLoop.start()
    Pyjo.IOLoop.reset()
    pass_ok('stopped gracefully')

with subtest('stream'):
    import Pyjo.IOLoop.Stream

    handle, peer = socket.socketpair()
    loop = Pyjo.IOLoop.new()
    id = loop.stream(Pyjo.IOLoop.Stream.new(handle))
    stream = loop.stream(id)
    isa_ok(stream, Pyjo.IOLoop.Stream.object, 'stream')

    # Increase inactivity timeout for connection to 300 seconds
    loop.stream(id).timeout = 300
    is_ok(loop.stream(id).timeout, 300, 'timeout')
    loop.reset()
    peer.close()

done_testing()
