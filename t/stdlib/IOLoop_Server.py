import Pyjo.IOLoop
import Pyjo.IOLoop.Server
import Pyjo.IOLoop.TLS

from Pyjo.Test import *

import os
import socket
import ssl
import tempfile
import threading


CA = os.path.join(os.path.dirname(Pyjo.IOLoop.TLS.CERT), 'ca.crt')


# A client of the standard library in a thread, while the loop runs
def serve(server, client):
    got = []
    server.on('accept', lambda server, handle: got.append(handle))
    server.start()
    thread = threading.Thread(target=client)
    thread.start()
    Pyjo.IOLoop.recurring(0.01, lambda loop: loop.stop() if not thread.is_alive() and got else None)
    Pyjo.IOLoop.timer(5, lambda loop: loop.stop())
    Pyjo.IOLoop.start()
    thread.join()
    Pyjo.IOLoop.reset()
    return got


with subtest('A client of the standard library'):
    server = Pyjo.IOLoop.Server.new()
    server.listen(address='127.0.0.1')

    def client():
        socket.create_connection(('127.0.0.1', server.port)).close()

    got = serve(server, client)
    isa_ok(got[0], socket.socket, 'accepted socket')
    ok(not got[0].getblocking(), 'non-blocking')
    ok(got[0].getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY), 'TCP_NODELAY')
    ok(server.handle.get_inheritable(), 'inheritable listen socket')
    server.close()

with subtest('IPv6'):
    if not socket.has_ipv6:
        skip('no IPv6', 2)
    else:
        server = Pyjo.IOLoop.Server.new()
        try:
            server.listen(address='[::1]')
        except OSError as e:
            skip(f'no IPv6 on ::1: {e}', 2)
        else:
            is_ok(server.handle.family, socket.AF_INET6, 'IPv6 socket')

            def client():
                socket.create_connection(('::1', server.port)).close()

            got = serve(server, client)
            is_ok(got[0].family, socket.AF_INET6, 'accepted')
            server.close()

with subtest('UNIX domain socket'):
    with tempfile.TemporaryDirectory() as dir:
        path = os.path.join(dir, 'test.sock')
        server = Pyjo.IOLoop.Server.new()
        server.listen(path=path)
        is_ok(server.port, None, 'no port')
        ok(f'unix:{path}:' in os.environ['PYJO_REUSE'], 'reusable')

        def client():
            s = socket.socket(socket.AF_UNIX)
            s.connect(path)
            s.close()

        got = serve(server, client)
        is_ok(got[0].family, socket.AF_UNIX, 'accepted')
        server.close()

with subtest('TLS'):
    server = Pyjo.IOLoop.Server.new()
    server.listen(address='127.0.0.1', tls=True)
    names = []

    def client():
        context = ssl.create_default_context(cafile=CA)
        with socket.create_connection(('127.0.0.1', server.port)) as s:
            with context.wrap_socket(s, server_hostname='localhost') as tls:
                names.append(tls.getpeercert()['subject'])

    got = serve(server, client)
    isa_ok(got[0], ssl.SSLSocket, 'accepted after the handshake')
    ok(names, 'the client verified the built-in certificate')
    server.close()

with subtest("Can't create listen socket"):
    taken = socket.socket()
    taken.bind(('127.0.0.1', 0))
    taken.listen()
    server = Pyjo.IOLoop.Server.new()
    try:
        server.listen(address='127.0.0.1', port=taken.getsockname()[1])
        fail_ok('listened')
    except OSError as e:
        like_ok(str(e), r"^Can't create listen socket: ", 'error with the message of Mojo')
        isa_ok(e.__cause__, OSError, 'the error of the system is the cause')
    taken.close()

done_testing()
