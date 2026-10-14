import Pyjo.HelloWorld
import Pyjo.IOLoop
import Pyjo.UserAgent.Server

from Pyjo.Test import *

import gc
import http.client
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

done_testing()
