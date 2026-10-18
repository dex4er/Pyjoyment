from Pyjo.Test import *

import socket
import struct
import threading


# A FastCGI client of a web server, in a thread of its own, as daemon.run() runs the event loop
def record(type, id, content=b''):
    padding = -len(content) % 8
    return struct.pack('>BBHHBx', 1, type, id, len(content), padding) + content + b'\0' * padding


def fastcgi(port, path, results):
    params = {'REQUEST_METHOD': 'GET', 'PATH_INFO': path, 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost'}
    pairs = b''.join(bytes([len(n), len(v)]) + n.encode() + v.encode() for n, v in params.items())
    data = record(1, 1, struct.pack('>HB5x', 1, 0)) + record(4, 1, pairs) + record(4, 1) + record(5, 1)
    with socket.create_connection(('127.0.0.1', port), timeout=10) as conn:
        conn.sendall(data)
        output = b''
        while chunk := conn.recv(65536):
            output += chunk
    stdout = b''
    while len(output) >= 8:
        _, type, _, size, padding = struct.unpack('>BBHHBx', output[:8])
        if type == 6:
            stdout += output[8 : 8 + size]
        output = output[8 + size + padding :]
    results.append(stdout)


with subtest('Synopsis'):
    import Pyjo.IOLoop
    import Pyjo.Server.Daemon

    daemon = Pyjo.Server.Daemon.new(listen=['fcgi://127.0.0.1'], silent=True)

    @daemon.unsubscribe('request').on('request')
    def request(daemon, tx):
        # Request
        method = tx.req.method
        path = tx.req.url.path

        # Response
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = f'{method} request for {path}!'.encode()

        # Resume transaction
        tx.resume()

    port = daemon.start().ports()[0]
    results = []

    # The client in a thread of its own, and the event loop stops when it is done
    worker = threading.Thread(target=fastcgi, args=(port, '/foo', results))
    worker.start()
    Pyjo.IOLoop.recurring(0.05, lambda loop: worker.is_alive() or loop.stop())
    daemon.run()
    worker.join()
    is_ok(len(results), 1, 'daemon.run()')
    like_ok(results[0], rb'^Status: 200 OK\r\n', 'status')
    like_ok(results[0], rb'\r\nContent-Type: text/plain\r\n', 'header')
    like_ok(results[0], rb'\r\n\r\nGET request for /foo!$', 'content')

with subtest('new'):
    import Pyjo.Server.FastCGI

    fcgi = Pyjo.Server.FastCGI.new(daemon, 'b8f8b6e2c6a1f5a9d0e3c4b7a2f1e0d9')
    ok(isinstance(fcgi, Pyjo.Server.FastCGI.object), 'fcgi')

with subtest('id'):
    id = fcgi.id
    is_ok(id, 'b8f8b6e2c6a1f5a9d0e3c4b7a2f1e0d9', 'id')

with subtest('read'):
    # A record of an unknown type, whose answer goes nowhere, as the connection does not exist
    fcgi.read(record(99, 0, b'?'))
    pass_ok('fcgi.read(chunk)')

with subtest('closed'):
    fcgi.closed()
    pass_ok('fcgi.closed()')

daemon.stop()

done_testing()
