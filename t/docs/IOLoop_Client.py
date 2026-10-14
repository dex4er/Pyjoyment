from Pyjo.Test import *

import os
import socket
import ssl


# The documentation describes the default reactor, before Pyjo.IOLoop is loaded
os.environ.pop('PYJO_REACTOR', None)

listening = socket.create_server(('127.0.0.1', 0))
listening.setblocking(False)
port = listening.getsockname()[1]

with subtest('Synopsis'):
    import Pyjo.IOLoop.Client

    connected = []

    # Create socket connection
    client = Pyjo.IOLoop.Client.new()
    client.on('connect', lambda client, handle: ...)
    client.on('error', lambda client, err: ...)
    client.on('connect', lambda client, handle: connected.append(handle) or client.reactor.stop())
    client.connect(address='127.0.0.1', port=port)

    # Start reactor if necessary
    if not client.reactor.is_running:
        client.reactor.start()
    isa_ok(connected[0], socket.socket, 'connected')

with subtest('reactor'):
    import Pyjo.Reactor.Poll

    client = Pyjo.IOLoop.Client.new()
    reactor = client.reactor
    is_ok(reactor, Pyjo.IOLoop.singleton.reactor, 'default')
    poll = Pyjo.Reactor.Poll.new()
    client = Pyjo.IOLoop.Client.new(reactor=poll)
    is_ok(client.reactor, poll, 'given')
    client.reactor = Pyjo.IOLoop.singleton.reactor
    is_ok(client.reactor, Pyjo.IOLoop.singleton.reactor, 'set')

with subtest('can_nnr and can_socks'):
    boolean = Pyjo.IOLoop.Client.object.can_nnr()
    ok(boolean, 'name resolution in a thread')
    boolean = Pyjo.IOLoop.Client.object.can_socks()
    ok(boolean, 'SOCKS5')

with subtest('connect'):
    errors = []

    def stop(client, *args):
        client.reactor.stop()

    client = Pyjo.IOLoop.Client.new()
    client.on('connect', stop)
    client.on('error', lambda client, err: errors.append(err) or stop(client))
    client.connect(address='127.0.0.1', port=port)
    client.reactor.start()

    handle = socket.create_connection(('127.0.0.1', port))
    client = Pyjo.IOLoop.Client.new()
    client.on('connect', stop)
    client.connect(handle=handle)
    client.reactor.start()

    client = Pyjo.IOLoop.Client.new()
    client.on('connect', stop)
    client.on('error', lambda client, err: errors.append(err) or stop(client))
    client.connect(address='localhost', port=port, source_address=('127.0.0.1', 0), timeout=15)
    client.reactor.start()
    is_deeply_ok(errors, [], 'connected')

    client = Pyjo.IOLoop.Client.new()
    client.connect(
        address='localhost',
        port=port,
        socks_address='127.0.0.1',
        socks_pass='secr3t',
        socks_port=9050,
        socks_user='sri',
        tls=True,
        tls_ca='/etc/tls/ca.crt',
        tls_cert='/etc/tls/client.crt',
        tls_key='/etc/tls/client.key',
        tls_hostname='mojolicious.org',
        tls_context=ssl.create_default_context(),
    )
    client.close()
    pass_ok('options')

with subtest('close'):
    client = Pyjo.IOLoop.Client.new()
    client.connect(address='127.0.0.1', port=port)
    client.close()
    pass_ok('closed')

listening.close()

done_testing()
