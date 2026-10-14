import Pyjo.IOLoop
import Pyjo.IOLoop.Server
import Pyjo.Promise

from Pyjo.Test import *

import socket


# Unlike Mojolicious: plan skip_all unless TEST_IPV6, the test runs where ::1 works
try:
    with socket.create_server(('::1', 0), family=socket.AF_INET6):
        pass
except OSError as e:
    plan(skip_all=f'IPv6 is not available: {e}')

with subtest('IPv6 roundtrip'):
    server = client = b''
    promise = Pyjo.Promise.new()

    def server_cb(loop, stream, id):
        def read(stream, chunk):
            global server
            server += chunk

        stream.write(b'test', lambda stream: stream.write(b'321'))
        stream.on('close', lambda stream: promise.resolve())
        stream.on('read', read)

    id = Pyjo.IOLoop.server(server_cb, address='[::1]')
    port = Pyjo.IOLoop.acceptor(id).port
    promise2 = Pyjo.Promise.new()

    def client_cb(loop, err, stream):
        def read(stream, chunk):
            global client
            client += chunk

        stream.write(b'tset', lambda stream: stream.write(b'123'))
        stream.on('close', lambda stream: promise2.resolve())
        stream.on('read', read)
        stream.timeout = 0.5

    Pyjo.IOLoop.client(client_cb, address='[::1]', port=port)
    Pyjo.Promise.all(promise, promise2).wait()
    is_ok(server, b'tset123', 'right content')
    is_ok(client, b'test321', 'right content')

done_testing()
