from Pyjo.Test import *

import os
import socket
import ssl
import tempfile


# The documentation describes the default reactor, before Pyjo.IOLoop is loaded
os.environ.pop('PYJO_REACTOR', None)

with subtest('Synopsis'):
    import Pyjo.IOLoop.Server

    accepted = []

    # Create listen socket
    server = Pyjo.IOLoop.Server.new()
    server.on('accept', lambda server, handle: ...)
    server.on('accept', lambda server, handle: accepted.append(handle) or server.reactor.stop())
    server.listen(port=Pyjo.IOLoop.Server.object.generate_port(), address='127.0.0.1')

    # Start and stop accepting connections
    server.start()
    server.stop()
    server.start()
    client = socket.create_connection(('127.0.0.1', server.port))

    # Start reactor if necessary
    if not server.reactor.is_running:
        server.reactor.start()
    isa_ok(accepted[0], socket.socket, 'accepted')
    server.close()

with subtest('reactor'):
    import Pyjo.Reactor.Poll

    server = Pyjo.IOLoop.Server.new()
    reactor = server.reactor
    is_ok(reactor, Pyjo.IOLoop.singleton.reactor, 'default')
    poll = Pyjo.Reactor.Poll.new()
    server.reactor = poll
    is_ok(server.reactor, poll, 'set')

with subtest('generate_port'):
    port = Pyjo.IOLoop.Server.object.generate_port()
    ok(0 < port < 65536, 'free port')

with subtest('handle, is_accepting and port'):
    server = Pyjo.IOLoop.Server.new()
    server.listen(address='127.0.0.1')
    handle = server.handle
    isa_ok(handle, socket.socket, 'handle')
    boolean = server.is_accepting
    ok(not boolean, 'not accepting')
    server.start()
    ok(server.is_accepting, 'accepting')
    port = server.port
    is_ok(port, handle.getsockname()[1], 'port')
    server.close()

with subtest('listen'):
    port = Pyjo.IOLoop.Server.object.generate_port()
    server = Pyjo.IOLoop.Server.new()
    server.listen(port=port, address='127.0.0.1', backlog=128, reuse=True, single_accept=True)
    is_ok(server.port, port, 'port')
    server.close()

    with tempfile.TemporaryDirectory() as dir:
        path = os.path.join(dir, 'myapp.sock')
        server = Pyjo.IOLoop.Server.new()
        server.listen(path=path)
        is_ok(server.handle.family, socket.AF_UNIX, 'UNIX domain socket')
        server.close()

    listening = socket.create_server(('127.0.0.1', 0))
    server = Pyjo.IOLoop.Server.new()
    server.listen(fd=listening.fileno())
    is_ok(server.port, listening.getsockname()[1], 'file descriptor')
    listening.detach()
    server.close()

    server = Pyjo.IOLoop.Server.new()
    server.listen(address='127.0.0.1', tls=True)
    server.close()
    server = Pyjo.IOLoop.Server.new()
    server.listen(
        address='127.0.0.1',
        tls=True,
        tls_ca='/etc/tls/ca.crt',
        tls_cert={'mojolicious.org': '/etc/tls/mojo.crt'},
        tls_key={'mojolicious.org': '/etc/tls/mojo.key'},
        tls_context=ssl.create_default_context(ssl.Purpose.CLIENT_AUTH),
    )
    server.close()
    pass_ok('options')

with subtest('close'):
    server = Pyjo.IOLoop.Server.new()
    server.listen(address='127.0.0.1')
    reuse = f'127.0.0.1:{server.port}:{server.handle.fileno()}'
    ok(reuse in os.environ['PYJO_REUSE'], 'reusable')
    server.close()
    ok(reuse not in os.environ['PYJO_REUSE'], 'not anymore')
    is_ok(server.handle, None, 'no handle')

done_testing()
