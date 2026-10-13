from Pyjo.Test import *

import os
import socket


# The documentation describes the default reactor, before Pyjo.IOLoop is loaded
os.environ.pop('PYJO_REACTOR', None)

handle, peer = socket.socketpair()

with subtest('Synopsis'):
    import Pyjo.IOLoop.Stream

    got = []

    # Create stream
    stream = Pyjo.IOLoop.Stream.new(handle)
    stream.on('read', lambda stream, chunk: ...)
    stream.on('close', lambda stream: ...)
    stream.on('error', lambda stream, err: ...)
    stream.on('read', lambda stream, chunk: got.append(chunk) or stream.reactor.stop())

    # Start and stop watching for new data
    stream.start()
    stream.stop()
    stream.start()
    peer.sendall(b'data')

    # Start reactor if necessary
    if not stream.reactor.is_running:
        stream.reactor.start()
    is_deeply_ok(got, [b'data'], 'read')

with subtest('Events'):
    events = []
    stream.on('drain', lambda stream: events.append('drain'))
    stream.on('write', lambda stream, chunk: events.append(chunk))
    stream.on('timeout', lambda stream: ...)
    stream.write(b'out', lambda stream: stream.reactor.stop())
    stream.reactor.start()
    is_deeply_ok(events, [b'out', 'drain'], 'write and drain')
    is_ok(peer.recv(3), b'out', 'written')
    stream.unsubscribe('drain')

with subtest('high_water_mark'):
    size = stream.high_water_mark
    is_ok(size, 1048576, 'default')
    stream.high_water_mark = 1024
    is_ok(stream.high_water_mark, 1024, 'set')

with subtest('reactor'):
    import Pyjo.Reactor.Poll

    reactor = stream.reactor
    is_ok(reactor, Pyjo.IOLoop.singleton.reactor, 'default')
    poll = Pyjo.Reactor.Poll.new()
    other = Pyjo.IOLoop.Stream.new()
    other.reactor = poll
    is_ok(other.reactor, poll, 'set')

with subtest('bytes_read, bytes_waiting and bytes_written'):
    num = stream.bytes_read
    is_ok(num, 4, 'read')
    num = stream.bytes_waiting
    is_ok(num, 0, 'waiting')
    num = stream.bytes_written
    is_ok(num, 3, 'written')

with subtest('can_write, is_readable and is_writing'):
    boolean = stream.can_write
    ok(boolean, 'can write')
    boolean = stream.is_readable
    ok(not boolean, 'not readable')
    boolean = stream.is_writing
    ok(not boolean, 'not writing')

with subtest('handle, steal_handle and timeout'):
    handle = stream.handle
    isa_ok(handle, socket.socket, 'handle')
    timeout = stream.timeout
    is_ok(timeout, 15, 'default')
    stream.timeout = 45
    is_ok(stream.timeout, 45, 'set')
    handle = stream.steal_handle()
    is_ok(stream.handle, None, 'stolen')
    stream = Pyjo.IOLoop.Stream.new(handle)

with subtest('write'):
    stream.start()
    stream = stream.write(b'chunk')
    stream = stream.write(b'chunk', lambda stream: stream.reactor.stop())
    stream.reactor.start()
    is_ok(stream.bytes_written, 10, 'written')

with subtest('close and close_gracefully'):
    closed = []
    stream.on('close', lambda stream: closed.append(True))
    stream.close_gracefully()
    is_deeply_ok(closed, [True], 'closed')
    stream.close()
    is_deeply_ok(closed, [True], 'closed once')

done_testing()
