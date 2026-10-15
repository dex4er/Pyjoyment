from Pyjo.Test import *

import io
import os
import socket
import tempfile

from contextlib import redirect_stdout


# The documentation describes the default reactor, before Pyjo.IOLoop is loaded
os.environ.pop('PYJO_REACTOR', None)


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


port = free_port()

with subtest('Synopsis'):
    import Pyjo.IOLoop.Datagram

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        # Echo server
        server = Pyjo.IOLoop.Datagram.new()
        server.on('message', lambda server, data, peer: server.send(b'Echo: ' + data, peer))
        server.bind(address='127.0.0.1', port=port)

        # Client
        client = Pyjo.IOLoop.Datagram.new()
        client.on('message', lambda client, data, peer: print(data))
        client.on('error', lambda client, err: print(err))
        client.on('message', lambda client, data, peer: client.reactor.stop())
        client.send(b'Hello!', ('127.0.0.1', port))

        # Start reactor if necessary
        if not client.reactor.is_running:
            client.reactor.start()
    is_ok(stdout.getvalue(), "b'Echo: Hello!'\n", 'print(data)')

with subtest('Events'):
    events = []
    client.on('close', lambda datagram: events.append('close'))
    other = Pyjo.IOLoop.Datagram.new()
    other.on('connect', lambda datagram: events.append('connect') or datagram.reactor.stop())
    other.on('error', lambda datagram, err: ...)
    other.on('message', lambda datagram, data, peer: ...)
    other.connect(address='127.0.0.1', port=port)
    other.reactor.start()
    client.close()
    is_deeply_ok(events, ['connect', 'close'], 'connect and close')
    other.close()

with subtest('new'):
    datagram = Pyjo.IOLoop.Datagram.new()
    is_ok(datagram.handle, None, 'not bound')
    handle = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    handle.bind(('127.0.0.1', 0))
    datagram = Pyjo.IOLoop.Datagram.new(handle)
    is_ok(datagram.handle, handle, 'handle')
    datagram.close()

with subtest('reactor'):
    import Pyjo.Reactor.Poll

    datagram = Pyjo.IOLoop.Datagram.new()
    reactor = datagram.reactor
    is_ok(reactor, Pyjo.IOLoop.singleton.reactor, 'default')
    poll = Pyjo.Reactor.Poll.new()
    datagram.reactor = Pyjo.Reactor.Poll.new()
    datagram.reactor = poll
    is_ok(datagram.reactor, poll, 'set')

with subtest('add_membership and drop_membership'):
    datagram = Pyjo.IOLoop.Datagram.new().bind(port=free_port())
    try:
        datagram = datagram.add_membership('224.0.0.114')
    except OSError as e:
        skip(f'No multicast: {e}', 1)
    else:
        datagram = datagram.drop_membership('224.0.0.114')
        pass_ok('joined and left')
    datagram.close()

with subtest('bind'):
    datagram = Pyjo.IOLoop.Datagram.new()
    datagram = datagram.bind(port=free_port())
    ok(datagram.port, 'bound')
    datagram.close()
    datagram = Pyjo.IOLoop.Datagram.new().bind(address='127.0.0.1', ipv6_only=True, reuse=True)
    ok(datagram.port, 'options')
    datagram.close()
    with tempfile.TemporaryDirectory() as dir:
        datagram = Pyjo.IOLoop.Datagram.new().bind(path=os.path.join(dir, 'myapp.sock'))
        is_ok(datagram.port, None, 'path')
        datagram.close()

with subtest('broadcast'):
    datagram = Pyjo.IOLoop.Datagram.new().bind(address='127.0.0.1')
    boolean = datagram.broadcast
    ok(not boolean, 'default')
    datagram.broadcast = True
    ok(datagram.broadcast, 'set')

with subtest('bytes_waiting'):
    num = datagram.bytes_waiting
    is_ok(num, 0, 'nothing')

with subtest('close and close_gracefully'):
    datagram.close()
    is_ok(datagram.handle, None, 'closed')
    datagram = Pyjo.IOLoop.Datagram.new().bind(address='127.0.0.1')
    datagram.close_gracefully()
    is_ok(datagram.handle, None, 'closed gracefully')

with subtest('connect'):
    server = Pyjo.IOLoop.Datagram.new().bind(address='127.0.0.1', port=free_port())
    datagram = Pyjo.IOLoop.Datagram.new()
    datagram.on('connect', lambda datagram: datagram.reactor.stop())
    datagram = datagram.connect(address='127.0.0.1', port=server.port)
    datagram.reactor.start()
    is_ok(datagram.handle.getpeername(), ('127.0.0.1', server.port), 'connected')
    datagram.close()

with subtest('handle'):
    handle = server.handle
    isa_ok(handle, socket.socket, 'socket')

with subtest('multicast_loopback'):
    boolean = server.multicast_loopback
    ok(boolean, 'default')
    server.multicast_loopback = False
    ok(not server.multicast_loopback, 'set')

with subtest('multicast_ttl'):
    ttl = server.multicast_ttl
    is_ok(ttl, 1, 'default')
    server.multicast_ttl = 64
    is_ok(server.multicast_ttl, 64, 'set')

with subtest('port'):
    port = server.port
    ok(port, 'port')

with subtest('send'):
    got = []

    @server.on
    def message(server, data, peer):
        got.append(data)
        if len(got) == 3:
            server.reactor.stop()

    connected = Pyjo.IOLoop.Datagram.new()
    connected.connect(address='127.0.0.1', port=port)
    datagram = connected.send(b'Hello!')

    # Bound to IPv4 first, so that localhost is resolved to an IPv4 address
    datagram = Pyjo.IOLoop.Datagram.new().bind(address='127.0.0.1')
    datagram = datagram.send(b'Hello!', ('127.0.0.1', port))
    datagram = datagram.send(b'Hello!', ('localhost', port), lambda datagram: ...)
    datagram.reactor.start()
    is_deeply_ok(got, [b'Hello!', b'Hello!', b'Hello!'], 'sent')
    connected.close()
    datagram.close()
    with tempfile.TemporaryDirectory() as dir:
        path = os.path.join(dir, 'myapp.sock')
        unix = Pyjo.IOLoop.Datagram.new().bind(path=path)
        unix.on('message', lambda unix, data, peer: [got.append(data), unix.reactor.stop()])
        datagram = Pyjo.IOLoop.Datagram.new()
        datagram = datagram.send(b'Hello!', path)
        datagram.reactor.start()
        is_ok(len(got), 4, 'UNIX domain socket')
        datagram.close()
        unix.close()

with subtest('start and stop'):
    server.start()
    server.stop()
    server.start()
    pass_ok('started and stopped')

with subtest('ttl'):
    ttl = server.ttl
    ok(ttl, 'default')
    server.ttl = 64
    is_ok(server.ttl, 64, 'set')
    server.close()

done_testing()
