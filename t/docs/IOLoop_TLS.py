from Pyjo.Test import *

import os
import socket
import ssl


# The documentation describes the default reactor, before Pyjo.IOLoop is loaded
os.environ.pop('PYJO_REACTOR', None)

certs = os.path.join(os.path.dirname(__file__), '..', '..', 'Pyjo', 'IOLoop', 'certs')

with subtest('Synopsis'):
    import Pyjo.IOLoop.TLS

    old_handle, peer = socket.socketpair()
    old_handle.setblocking(False)
    peer.setblocking(False)
    upgraded = []

    # Negotiate TLS
    tls = Pyjo.IOLoop.TLS.new(old_handle)
    tls.on('upgrade', lambda tls, new_handle: ...)
    tls.on('error', lambda tls, err: ...)
    tls.on('upgrade', lambda tls, new_handle: upgraded.append(new_handle) or tls.reactor.stop())
    tls.negotiate(server=True)

    client = Pyjo.IOLoop.TLS.new(peer)
    client.on('upgrade', lambda tls, handle: ...)
    client.on('upgrade', lambda tls, handle: upgraded.append(handle))
    client.negotiate(address='localhost', tls_ca=os.path.join(certs, 'ca.crt'))

    # Start reactor if necessary
    if not tls.reactor.is_running:
        tls.reactor.start()
    isa_ok(upgraded[0], ssl.SSLSocket, 'upgraded')
    for handle in upgraded:
        handle.close()

with subtest('reactor'):
    import Pyjo.Reactor.Poll

    tls = Pyjo.IOLoop.TLS.new()
    reactor = tls.reactor
    is_ok(reactor, Pyjo.IOLoop.singleton.reactor, 'default')
    poll = Pyjo.Reactor.Poll.new()
    tls.reactor = poll
    is_ok(tls.reactor, poll, 'set')

with subtest('can_tls'):
    boolean = Pyjo.IOLoop.TLS.object.can_tls()
    ok(boolean, 'TLS support')

with subtest('negotiate'):
    errors = []
    pair = socket.socketpair()
    tls = Pyjo.IOLoop.TLS.new(pair[0])
    tls.on('error', lambda tls, err: errors.append(err))
    tls.negotiate(server=True)
    pair2 = socket.socketpair()
    tls2 = Pyjo.IOLoop.TLS.new(pair2[0])
    tls2.on('error', lambda tls, err: errors.append(err))
    tls2.negotiate(tls_ca='/etc/tls/ca.crt')
    pair3 = socket.socketpair()
    tls3 = Pyjo.IOLoop.TLS.new(pair3[0])
    tls3.on('error', lambda tls, err: errors.append(err))
    tls3.negotiate(address='mojolicious.org', tls_context=ssl.create_default_context())
    is_deeply_ok(errors, [], 'started')
    Pyjo.IOLoop.reset()
    del tls, tls2, tls3
    for sockets in (pair, pair2, pair3):
        for sock in sockets:
            sock.close()

with subtest('new'):
    handle, peer = socket.socketpair()
    tls = Pyjo.IOLoop.TLS.new(handle)
    isa_ok(tls, Pyjo.IOLoop.TLS.object, 'new')
    handle.close()
    peer.close()

done_testing()
