import Pyjo.IOLoop
import Pyjo.IOLoop.TLS
import Pyjo.Promise

from Pyjo.Test import *
from Pyjo.Util import warn

import socket
import ssl


# Left out from Mojolicious: plan skip_all unless TEST_TLS, as the ssl module comes with Python, and unless can_tls


# Unlike Mojolicious: tls_options => {SSL_verify_mode => 0x00} is a context that does not verify
def unverified():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


with subtest('Built-in certificate'):
    client_sock, server_sock = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    client_sock.setblocking(False)
    server_sock.setblocking(False)
    promise = Pyjo.Promise.new()
    promise2 = Pyjo.Promise.new()
    server = Pyjo.IOLoop.TLS.new(server_sock)
    server.once('upgrade', lambda tls, handle: promise.resolve(handle))
    server.once('error', lambda tls, err: warn(str(err)))
    server.negotiate(server=True)
    client = Pyjo.IOLoop.TLS.new(client_sock)
    client.once('upgrade', lambda tls, handle: promise2.resolve(handle))
    client.once('error', lambda tls, err: warn(str(err)))
    client.negotiate(tls_context=unverified())
    results = []
    Pyjo.Promise.all(promise, promise2).then(lambda *values: results.extend(v[0] for v in values)).wait()
    server_result, client_result = results
    isa_ok(client_result, ssl.SSLSocket, 'right class')
    isa_ok(server_result, ssl.SSLSocket, 'right class')
    server_result.close()
    client_result.close()

with subtest('Built-in certificate (custom event loop and cipher)'):
    loop = Pyjo.IOLoop.new()
    client_sock2, server_sock2 = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    client_sock2.setblocking(False)
    server_sock2.setblocking(False)
    promise = Pyjo.Promise.new().set(ioloop=loop)
    promise2 = Pyjo.Promise.new().set(ioloop=loop)
    server = Pyjo.IOLoop.TLS.new(server_sock2).set(reactor=loop.reactor)
    server.once('upgrade', lambda tls, handle: promise.resolve(handle))
    server.once('error', lambda tls, err: warn(str(err)))
    # Unlike Mojolicious: tls_options => {SSL_cipher_list => 'AES256-SHA:ALL'} is a context with the ciphers
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(Pyjo.IOLoop.TLS.CERT, Pyjo.IOLoop.TLS.KEY)
    context.set_ciphers('AES256-SHA:ALL')
    server.negotiate(server=True, tls_context=context)
    client = Pyjo.IOLoop.TLS.new(client_sock2).set(reactor=loop.reactor)
    client.once('upgrade', lambda tls, handle: promise2.resolve(handle))
    client.once('error', lambda tls, err: warn(str(err)))
    client.negotiate(tls_context=unverified())
    results = []
    Pyjo.Promise.all(promise, promise2).then(lambda *values: results.extend(v[0] for v in values)).wait()
    server_result, client_result = results
    isa_ok(client_result, ssl.SSLSocket, 'right class')
    isa_ok(server_result, ssl.SSLSocket, 'right class')
    expect = 'TLS_AES_256_GCM_SHA384' if server_result.version() == 'TLSv1.3' else 'AES256-SHA'
    is_ok(client_result.cipher()[0], expect, f'{expect} has been negotiated')
    is_ok(server_result.cipher()[0], expect, f'{expect} has been negotiated')
    server_result.close()
    client_result.close()

done_testing()
