import Pyjo.IOLoop
import Pyjo.IOLoop.Datagram

from Pyjo.Test import *

import errno
import os
import re
import socket
import tempfile


def ipv6():
    try:
        with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as s:
            s.bind(('::1', 0))
        return True
    except OSError:
        return False


with subtest('Echo'):
    loop = Pyjo.IOLoop.new()
    server = Pyjo.IOLoop.Datagram.new()
    server.reactor = loop.reactor
    server.on('message', lambda server, data, peer: server.send(b'Echo: ' + data, peer))
    is_ok(server.bind(address='127.0.0.1'), server, 'bind returns the socket')
    ok(server.port, 'port')
    isa_ok(server.handle, socket.socket, 'handle')

    client = Pyjo.IOLoop.Datagram.new()
    client.reactor = loop.reactor
    is_ok(client.handle, None, 'no handle before the first datagram')
    is_ok(client.port, None, 'no port before the first datagram')
    got = []

    @client.on
    def message(client, data, peer):
        got.append((data, peer))
        loop.stop()

    client.send(b'Hello!', ('127.0.0.1', server.port))
    ok(client.port, 'bound to a random port by the first datagram')
    loop.start()
    is_deeply_ok(got, [(b'Echo: Hello!', ('127.0.0.1', server.port))], 'echo with the address of the sender')
    client.close()
    server.close()

with subtest('One datagram for every send'):
    loop = Pyjo.IOLoop.new()
    server = Pyjo.IOLoop.Datagram.new()
    server.reactor = loop.reactor
    got = []

    @server.on
    def message(server, data, peer):
        got.append(data)
        if len(got) == 10:
            loop.stop()

    server.bind(address='127.0.0.1')
    client = Pyjo.IOLoop.Datagram.new()
    client.reactor = loop.reactor
    sent = []
    for i in range(10):
        client.send(f'datagram {i}'.encode(), ('127.0.0.1', server.port), lambda client: sent.append(True))
    loop.timer(5, lambda loop: loop.stop())
    loop.start()
    is_deeply_ok(got, [f'datagram {i}'.encode() for i in range(10)], 'ten datagrams, not joined')
    is_ok(len(sent), 10, 'callback for every datagram')
    is_ok(client.bytes_waiting, 0, 'nothing waiting')
    client.close()
    server.close()

with subtest('Connect'):
    loop = Pyjo.IOLoop.new()
    server = Pyjo.IOLoop.Datagram.new()
    server.reactor = loop.reactor
    server.on('message', lambda server, data, peer: server.send(data.upper(), peer))
    server.bind(address='127.0.0.1')

    client = Pyjo.IOLoop.Datagram.new()
    client.reactor = loop.reactor
    got = []
    client.on('connect', lambda client: got.append('connect'))

    @client.on
    def message(client, data, peer):
        got.append(data)
        loop.stop()

    is_ok(client.connect(address='127.0.0.1', port=server.port), client, 'connect returns the socket')
    client.send(b'before connected')
    is_ok(client.bytes_waiting, 16, 'waiting for the connection')
    loop.start()
    is_deeply_ok(got, ['connect', b'BEFORE CONNECTED'], 'sent once connected')
    client.close()
    server.close()

with subtest('Name resolution'):
    loop = Pyjo.IOLoop.new()
    server = Pyjo.IOLoop.Datagram.new()
    server.reactor = loop.reactor
    server.on('message', lambda server, data, peer: server.send(data, peer))
    server.bind(address='127.0.0.1')

    # Bound to IPv4 first, so that localhost is resolved to an IPv4 address
    client = Pyjo.IOLoop.Datagram.new()
    client.reactor = loop.reactor
    client.bind(address='127.0.0.1')
    got = []

    @client.on
    def message(client, data, peer):
        got.append(data)
        loop.stop()

    client.send(b'by name', ('localhost', server.port))
    timer = loop.timer(5, lambda loop: loop.stop())
    loop.start()
    loop.remove(timer)
    is_deeply_ok(got, [b'by name'], 'resolved')

    errors = []

    @client.on
    def error(client, err):
        errors.append(err)
        loop.stop()

    client.send(b'nowhere', ('nonexistent.invalid', 53))
    timer = loop.timer(10, lambda loop: loop.stop())
    loop.start()
    loop.remove(timer)
    like_ok(errors[0], r"^Can't resolve", 'error of the name resolution')
    ok(client.handle, 'still open')
    client.close()
    server.close()

with subtest('An address of another family than the socket'):
    loop = Pyjo.IOLoop.new()
    datagram = Pyjo.IOLoop.Datagram.new()
    datagram.reactor = loop.reactor
    datagram.bind(address='127.0.0.1')
    errors = []

    @datagram.on
    def error(datagram, err):
        errors.append(err)
        loop.stop()

    datagram.send(b'IPv6', ('::1', 53))
    loop.timer(5, lambda loop: loop.stop())
    loop.start()
    is_ok(len(errors), 1, 'an error')
    is_ok(datagram.bytes_waiting, 0, 'not waiting')
    datagram.close()

with subtest('A datagram that cannot be sent'):
    datagram = Pyjo.IOLoop.Datagram.new().bind(address='0.0.0.0')
    errors = []
    sent = []
    datagram.on('error', lambda datagram, err: errors.append(err))

    # A broadcast without the socket option
    datagram.send(b'broadcast', ('255.255.255.255', 9), lambda datagram: sent.append(True))
    isa_ok(errors[0], PermissionError, 'error')
    is_deeply_ok(sent, [], 'not sent')
    is_ok(datagram.bytes_waiting, 0, 'not waiting')
    ok(datagram.handle, 'still open')
    datagram.close()

with subtest('IPv6'):
    if not ipv6():
        skip('IPv6 is not available', 1)
    else:
        loop = Pyjo.IOLoop.new()
        server = Pyjo.IOLoop.Datagram.new()
        server.reactor = loop.reactor
        server.on('message', lambda server, data, peer: server.send(data, peer))
        server.bind(address='[::1]')
        client = Pyjo.IOLoop.Datagram.new()
        client.reactor = loop.reactor
        got = []

        @client.on
        def message(client, data, peer):
            got.append((data, peer[0]))
            loop.stop()

        client.send(b'IPv6', ('::1', server.port))
        loop.start()
        is_deeply_ok(got, [(b'IPv6', '::1')], 'echo')
        client.close()
        server.close()

with subtest('UNIX domain datagram socket'):
    if not hasattr(socket, 'AF_UNIX'):
        skip('UNIX domain sockets are not available', 2)
    else:
        with tempfile.TemporaryDirectory() as dir:
            path = os.path.join(dir, 'server.sock')
            loop = Pyjo.IOLoop.new()
            server = Pyjo.IOLoop.Datagram.new()
            server.reactor = loop.reactor
            server.on('message', lambda server, data, peer: server.send(data.upper(), peer))
            server.bind(path=path)
            is_ok(server.port, None, 'no port')

            client = Pyjo.IOLoop.Datagram.new()
            client.reactor = loop.reactor
            client.bind(path=os.path.join(dir, 'client.sock'))
            got = []

            @client.on
            def message(client, data, peer):
                got.append((data, peer))
                loop.stop()

            client.send(b'unix', path)
            loop.start()
            is_deeply_ok(got, [(b'UNIX', path)], 'echo')
            client.close()
            server.close()

with subtest('Close'):
    loop = Pyjo.IOLoop.new()
    datagram = Pyjo.IOLoop.Datagram.new()
    datagram.reactor = loop.reactor
    closed = []
    datagram.on('close', lambda datagram: closed.append(True))
    datagram.close()
    is_deeply_ok(closed, [], 'no close event before the socket is bound')
    datagram.bind(address='127.0.0.1')
    datagram.close()
    datagram.close()
    is_deeply_ok(closed, [True], 'one close event')
    is_ok(datagram.handle, None, 'no handle')

    # Gracefully, once the datagrams have been sent
    receiver = Pyjo.IOLoop.Datagram.new()
    receiver.reactor = loop.reactor
    receiver.bind(address='127.0.0.1')
    got = []
    receiver.on('message', lambda receiver, data, peer: got.append(data))
    datagram = Pyjo.IOLoop.Datagram.new()
    datagram.reactor = loop.reactor
    datagram.on('close', lambda datagram: loop.timer(0.1, lambda loop: loop.stop()))
    datagram.send(b'last', ('127.0.0.1', receiver.port))
    datagram.close_gracefully()
    loop.start()
    is_deeply_ok(got, [b'last'], 'sent before the close')
    is_ok(datagram.handle, None, 'closed')
    receiver.close()

with subtest('Bind errors'):
    datagram = Pyjo.IOLoop.Datagram.new().bind(address='127.0.0.1')
    other = Pyjo.IOLoop.Datagram.new()
    throws_ok(
        lambda: other.bind(address='127.0.0.1', port=datagram.port),
        re.compile(r"^Can't bind datagram socket: "),
        'port in use',
    )
    is_ok(other.handle, None, 'no handle')
    datagram.close()

    first = Pyjo.IOLoop.Datagram.new().bind(address='127.0.0.1', reuse=True)
    second = Pyjo.IOLoop.Datagram.new().bind(address='127.0.0.1', port=first.port, reuse=True)
    is_ok(second.port, first.port, 'same port with reuse')
    first.close()
    second.close()

with subtest('Socket options'):
    datagram = Pyjo.IOLoop.Datagram.new()
    throws_ok(lambda: datagram.broadcast, OSError, 'not bound')
    datagram.bind(address='127.0.0.1')
    ok(not datagram.broadcast, 'no broadcast')
    datagram.broadcast = True
    ok(datagram.broadcast, 'broadcast')
    datagram.ttl = 42
    is_ok(datagram.ttl, 42, 'ttl')
    datagram.multicast_ttl = 3
    is_ok(datagram.multicast_ttl, 3, 'multicast_ttl')
    datagram.multicast_loopback = False
    ok(not datagram.multicast_loopback, 'no multicast_loopback')
    datagram.close()

with subtest('Multicast'):
    loop = Pyjo.IOLoop.new()
    receiver = Pyjo.IOLoop.Datagram.new()
    receiver.reactor = loop.reactor
    receiver.bind(address='0.0.0.0', reuse=True)
    try:
        is_ok(receiver.add_membership('239.255.42.99', '127.0.0.1'), receiver, 'add_membership returns the socket')
    except OSError as e:
        skip(f'No multicast on the loopback interface: {e}', 3)
    else:
        got = []

        @receiver.on
        def message(receiver, data, peer):
            got.append(data)
            loop.stop()

        sender = Pyjo.IOLoop.Datagram.new()
        sender.reactor = loop.reactor
        sender.bind(address='127.0.0.1')
        sender.handle.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton('127.0.0.1'))
        sender.send(b'multicast', ('239.255.42.99', receiver.port))
        loop.timer(2, lambda loop: loop.stop())
        loop.start()
        is_deeply_ok(got, [b'multicast'], 'received')
        is_ok(receiver.drop_membership('239.255.42.99', '127.0.0.1'), receiver, 'drop_membership returns the socket')
        sender.close()
    receiver.close()

with subtest('Errors of a connected socket'):
    loop = Pyjo.IOLoop.new()

    # A port that nothing listens on
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
    client = Pyjo.IOLoop.Datagram.new()
    client.reactor = loop.reactor
    errors = []

    @client.on
    def error(client, err):
        errors.append(err)
        loop.stop()

    client.on('connect', lambda client: client.send(b'nobody'))
    client.connect(address='127.0.0.1', port=port)
    loop.timer(2, lambda loop: loop.stop())
    loop.start()
    isa_ok(errors[0], ConnectionRefusedError, 'refused')
    is_ok(errors[0].errno, errno.ECONNREFUSED, 'right errno')
    ok(client.handle, 'still open')
    client.close()

with subtest('Event loop'):
    loop = Pyjo.IOLoop.new()
    got = []

    @loop.datagram(address='127.0.0.1')
    def id(loop, datagram, id):
        datagram.on('message', lambda datagram, data, peer: datagram.send(data.upper(), peer))

    isa_ok(id, str, 'the decorated name is the id')
    datagram = loop.stream(id)
    isa_ok(datagram, Pyjo.IOLoop.Datagram.object, 'the socket of the id')
    is_ok(datagram.reactor, loop.reactor, 'the reactor of the loop')

    def connected(loop, client, id):
        client.on('message', lambda client, data, peer: [got.append(data), loop.stop()])
        client.on('connect', lambda client: client.send(b'loop'))
        client.connect(address='127.0.0.1', port=datagram.port)

    client = loop.datagram(cb=connected)
    is_ok(loop.stream(client).handle, None, 'not bound without options')
    loop.start()
    is_deeply_ok(got, [b'LOOP'], 'echo')

    closed = []
    datagram.on('close', lambda datagram: closed.append(True))
    loop.remove(id)
    is_deeply_ok(closed, [True], 'removed')
    is_ok(loop.stream(id), None, 'gone')
    loop.reset()
    is_ok(loop.stream(client), None, 'reset')

done_testing()
