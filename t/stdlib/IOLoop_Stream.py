import Pyjo.IOLoop
import Pyjo.IOLoop.Server
import Pyjo.IOLoop.Stream

from Pyjo.Test import *

import os
import socket
import ssl


with subtest('A pipe'):
    r, w = os.pipe()
    reader = Pyjo.IOLoop.Stream.new(os.fdopen(r, 'rb', buffering=0))
    writer = Pyjo.IOLoop.Stream.new(os.fdopen(w, 'wb', buffering=0))
    got = []

    def read(stream, chunk):
        got.append(chunk)
        writer.close()

    reader.on('read', read)
    reader.on('close', lambda stream: Pyjo.IOLoop.stop())
    reader.start()
    writer.start()
    writer.write(b'through a pipe')
    Pyjo.IOLoop.start()
    is_deeply_ok(got, [b'through a pipe'], 'os.read and os.write')

with subtest('A closed peer'):
    a, b = socket.socketpair()
    stream = Pyjo.IOLoop.Stream.new(a)
    closed = []
    stream.on('close', lambda stream: closed.append(True) or Pyjo.IOLoop.stop())
    stream.start()
    b.close()
    Pyjo.IOLoop.start()
    is_deeply_ok(closed, [True], 'closed')
    is_ok(a.fileno(), -1, 'the socket is closed too')

with subtest('An error'):
    a, b = socket.socketpair()
    stream = Pyjo.IOLoop.Stream.new(a)
    errors = []
    stream.on('error', lambda stream, err: errors.append(err))
    stream.on('close', lambda stream: Pyjo.IOLoop.stop())
    stream.start()
    a.shutdown(socket.SHUT_RD)
    b.close()
    Pyjo.IOLoop.timer(1, lambda loop: Pyjo.IOLoop.stop())
    Pyjo.IOLoop.start()
    ok(all(isinstance(e, OSError) for e in errors), 'errors are OSError')

with subtest('TLS'):
    certs = os.path.dirname(Pyjo.IOLoop.Server.CERT)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(Pyjo.IOLoop.Server.CERT, Pyjo.IOLoop.Server.KEY)
    client_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    client_context.load_verify_locations(os.path.join(certs, 'ca.crt'))
    a, b = socket.socketpair()
    a.setblocking(False)
    b.setblocking(False)
    server = context.wrap_socket(a, server_side=True, do_handshake_on_connect=False)
    client = client_context.wrap_socket(b, server_hostname='localhost', do_handshake_on_connect=False)
    for _ in range(100):
        done = 0
        for s in (server, client):
            try:
                s.do_handshake()
                done += 1
            except (ssl.SSLWantReadError, ssl.SSLWantWriteError):
                pass
        if done == 2:
            break
    ok(done == 2, 'verified with the CA of the tests, for localhost')
    got = []
    stream = Pyjo.IOLoop.Stream.new(server)
    stream.on('read', lambda stream, chunk: got.append(chunk) or Pyjo.IOLoop.stop())
    stream.start()
    other = Pyjo.IOLoop.Stream.new(client)
    other.start()
    other.write(b'secret')
    Pyjo.IOLoop.timer(5, lambda loop: Pyjo.IOLoop.stop())
    Pyjo.IOLoop.start()
    is_deeply_ok(got, [b'secret'], 'ssl.SSLSocket')
    stream.close()
    other.close()

done_testing()
