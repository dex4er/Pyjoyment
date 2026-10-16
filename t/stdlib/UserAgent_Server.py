import Pyjo.HelloWorld
import Pyjo.IOLoop
import Pyjo.UserAgent.Server

from Pyjo.Test import *

import gc
import http.client
import socket
import threading


# A client of the standard library in a thread of its own, while the event loop of the server runs
def get(loop, url):
    results = []

    def client():
        conn = http.client.HTTPConnection(url.host, url.port, timeout=10)
        conn.request('GET', '/')
        res = conn.getresponse()
        results.append((res.status, res.read()))
        conn.close()

    worker = threading.Thread(target=client)
    worker.start()
    timer = loop.recurring(0.05, lambda loop: worker.is_alive() or loop.stop())
    loop.start()
    loop.remove(timer)
    worker.join()
    return results[0]


hello = Pyjo.HelloWorld.new()
server = Pyjo.UserAgent.Server.new(app=hello, ioloop=Pyjo.IOLoop.new())

with subtest('Blocking server on the event loop of the server'):
    is_deeply_ok(get(server.ioloop, server.url()), (200, b'Your Pyjo is working!'), 'right response')

with subtest('Non-blocking server on the singleton'):
    is_deeply_ok(get(Pyjo.IOLoop.singleton, server.nb_url()), (200, b'Your Pyjo is working!'), 'right response')

with subtest('Restart'):
    url = server.url()
    server.restart()
    # Not in Mojolicious: PyPy frees the old servers when its garbage collector runs
    gc.collect()
    ok(server.url().port != url.port, 'new port')
    is_deeply_ok(get(server.ioloop, server.url()), (200, b'Your Pyjo is working!'), 'right response')

with subtest('Restart when the system gives the same port again'):
    import Pyjo.Server.Daemon

    url, nb_url = server.url(), server.nb_url()
    server.restart()

    # The first server after the restart gets the port of the old one
    ports = Pyjo.Server.Daemon.object.ports
    calls = []

    def same_port(self):
        calls.append(True)
        return [url.port] if len(calls) == 1 else ports(self)

    Pyjo.Server.Daemon.object.ports = same_port
    try:
        new = server.url()
    finally:
        Pyjo.Server.Daemon.object.ports = ports
    gc.collect()
    ok(new.port not in (url.port, nb_url.port), 'not an old port')
    ok(server.nb_url().port not in (url.port, nb_url.port), 'not an old port for non-blocking requests')
    is_deeply_ok(get(server.ioloop, server.url()), (200, b'Your Pyjo is working!'), 'right response')

    is_deeply_ok(get(server.ioloop, server.url()), (200, b'Your Pyjo is working!'), 'right response')

with subtest('Context manager'):
    with Pyjo.UserAgent.Server.new() as server:
        port = server.url().port
        socket.create_connection(('127.0.0.1', port)).close()
    throws_ok(
        lambda: socket.create_connection(('127.0.0.1', port)), ConnectionRefusedError, 'servers closed at the end'
    )

done_testing()
