import Pyjo.IOLoop
import Pyjo.IOLoop.TLS
import Pyjo.Reactor.Asyncio

from Pyjo.Test import *

import os
import socket
import ssl


CA = os.path.join(os.path.dirname(Pyjo.IOLoop.TLS.CERT), 'ca.crt')

# The asyncio reactor, whatever PYJO_REACTOR says
Pyjo.IOLoop.singleton.reactor = Pyjo.Reactor.Asyncio.new()


# The handles of the negotiations, closed at the end
handles = []


def negotiate(server_options, client_options):
    a, b = socket.socketpair()
    a.setblocking(False)
    b.setblocking(False)
    got = {'server': None, 'client': None, 'errors': [], 'done': 0}

    # Wait until both sides are done, upgraded or failed
    def finish():
        got['done'] += 1
        if got['done'] == 2:
            Pyjo.IOLoop.stop()

    def upgrade(side):
        def cb(tls, handle):
            got[side] = handle
            handles.append(handle)
            finish()

        return cb

    def error(tls, err):
        got['errors'].append(err)
        finish()

    server = Pyjo.IOLoop.TLS.new(a)
    server.on('upgrade', upgrade('server'))
    server.on('error', error)
    server.negotiate(server=True, **server_options)
    client = Pyjo.IOLoop.TLS.new(b)
    client.on('upgrade', upgrade('client'))
    client.on('error', error)
    client.negotiate(**client_options)
    timer = Pyjo.IOLoop.timer(5, lambda loop: Pyjo.IOLoop.stop())
    Pyjo.IOLoop.start()
    Pyjo.IOLoop.remove(timer)
    return got


with subtest('Verified with the CA of the tests'):
    got = negotiate({}, {'address': 'localhost', 'tls_ca': CA})
    isa_ok(got['client'], ssl.SSLSocket, 'localhost')
    is_ok(got['client'].server_hostname, 'localhost', 'name for SNI')
    got = negotiate({}, {'address': '127.0.0.1', 'tls_ca': CA})
    isa_ok(got['client'], ssl.SSLSocket, '127.0.0.1')

with subtest('Not verified'):
    got = negotiate({}, {'address': 'example.com', 'tls_ca': CA})
    isa_ok(got['errors'][0], ssl.SSLCertVerificationError, 'wrong name')
    got = negotiate({}, {'address': 'localhost'})
    isa_ok(got['errors'][0], ssl.SSLCertVerificationError, 'not with the default CAs')

with subtest('Client certificate'):
    got = negotiate({'tls_ca': CA}, {'address': 'localhost', 'tls_ca': CA})
    ok(len(got['errors']), 'required by the server with a CA')
    got = negotiate(
        {'tls_ca': CA},
        {'address': 'localhost', 'tls_ca': CA, 'tls_cert': Pyjo.IOLoop.TLS.CERT, 'tls_key': Pyjo.IOLoop.TLS.KEY},
    )
    # The certificate of the server is for servers only; a certificate of a client comes with the tests of the client
    like_ok(
        str(got['errors'][0]), r'unsuitable certificate purpose', 'the certificate of a server is not one of a client'
    )

with subtest('SNI'):
    got = negotiate(
        {'tls_cert': {'localhost': Pyjo.IOLoop.TLS.CERT}, 'tls_key': {'localhost': Pyjo.IOLoop.TLS.KEY}},
        {'address': 'localhost', 'tls_ca': CA},
    )
    isa_ok(got['client'], ssl.SSLSocket, 'certificate of the name')

with subtest('ALPN with contexts'):
    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_context.load_cert_chain(Pyjo.IOLoop.TLS.CERT, Pyjo.IOLoop.TLS.KEY)
    server_context.set_alpn_protocols(['foo', 'bar', 'baz'])
    client_context = ssl.create_default_context(cafile=CA)
    client_context.set_alpn_protocols(['baz', 'bar'])
    got = negotiate({'tls_context': server_context}, {'address': 'localhost', 'tls_context': client_context})
    # OpenSSL chooses by the order of the server, IO::Socket::SSL of Mojo's tests by the order of the client
    is_ok(got['server'].selected_alpn_protocol(), 'bar', 'right protocol')
    is_ok(got['client'].selected_alpn_protocol(), 'bar', 'right protocol')

for handle in handles:
    handle.close()

done_testing()
