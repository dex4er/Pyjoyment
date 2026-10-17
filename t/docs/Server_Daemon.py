from Pyjo.Test import *

import http.client
import io
import threading

from contextlib import redirect_stdout


with subtest('Synopsis'):
    import Pyjo.IOLoop
    import Pyjo.Server.Daemon

    daemon = Pyjo.Server.Daemon.new(listen=['http://127.0.0.1'], silent=True)

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

    def client():
        conn = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
        conn.request('GET', '/foo')
        results.append(conn.getresponse().read())
        conn.close()

    # The client in a thread of its own, and the event loop stops when it is done
    worker = threading.Thread(target=client)
    worker.start()
    Pyjo.IOLoop.recurring(0.05, lambda loop: worker.is_alive() or loop.stop())
    daemon.run()
    worker.join()
    is_deeply_ok(results, [b'GET request for /foo!'], 'daemon.run()')

with subtest('context manager'):
    with Pyjo.Server.Daemon.new(listen=['http://127.0.0.1'], silent=True) as daemon:
        id = daemon.start().acceptors[0]
        ok(Pyjo.IOLoop.acceptor(id), 'listening')
    ok(not Pyjo.IOLoop.acceptor(id), 'not listening any more')

with subtest('new'):
    daemon = Pyjo.Server.Daemon.new()
    is_deeply_ok(daemon.listen, ['http://*:3000'], 'daemon')
    daemon = Pyjo.Server.Daemon.new(listen=['http://*:8080'], silent=True)
    is_ok(daemon.silent, True, 'daemon.silent')

with subtest('acceptors'):
    daemon = Pyjo.Server.Daemon.new(listen=['http://127.0.0.1'], silent=True)
    acceptors = daemon.acceptors
    is_deeply_ok(acceptors, [], 'acceptors')
    daemon.acceptors = ['6be0c140ef00a389c5d039536b56d139']
    is_deeply_ok(daemon.acceptors, ['6be0c140ef00a389c5d039536b56d139'], 'daemon.acceptors')
    daemon.acceptors = []

    # Check port
    daemon.start()
    port = daemon.ioloop.acceptor(daemon.acceptors[0]).port
    ok(port > 0, 'port')
    daemon.stop()

with subtest('backlog'):
    backlog = daemon.backlog
    is_ok(backlog, None, 'backlog')
    daemon.backlog = 128
    is_ok(daemon.backlog, 128, 'daemon.backlog')

with subtest('inactivity_timeout'):
    timeout = daemon.inactivity_timeout
    is_ok(timeout, 30, 'timeout')
    daemon.inactivity_timeout = 5
    is_ok(daemon.inactivity_timeout, 5, 'daemon.inactivity_timeout')

with subtest('ioloop'):
    loop = daemon.ioloop
    is_ok(loop, Pyjo.IOLoop.singleton, 'loop')
    daemon.ioloop = Pyjo.IOLoop.new()
    ok(daemon.ioloop is not loop, 'daemon.ioloop')

with subtest('keep_alive_timeout'):
    timeout = daemon.keep_alive_timeout
    is_ok(timeout, 5, 'timeout')
    daemon.keep_alive_timeout = 10
    is_ok(daemon.keep_alive_timeout, 10, 'daemon.keep_alive_timeout')

with subtest('listen'):
    listen = daemon.listen
    is_deeply_ok(listen, ['http://127.0.0.1'], 'listen')
    daemon.listen = ['https://127.0.0.1:8080']
    is_deeply_ok(daemon.listen, ['https://127.0.0.1:8080'], 'daemon.listen')

    # Listen on all IPv4 interfaces
    daemon.listen = ['http://*:3000']

    # Listen on all IPv4 and IPv6 interfaces
    daemon.listen = ['http://[::]:3000']

    # Listen on IPv6 interface
    daemon.listen = ['http://[::1]:4000']

    # Listen on IPv4 and IPv6 interfaces
    daemon.listen = ['http://127.0.0.1:3000', 'http://[::1]:3000']

    # Listen on UNIX domain socket "/tmp/myapp.sock" (percent encoded slash)
    daemon.listen = ['http+unix://%2Ftmp%2Fmyapp.sock']

    # File descriptor, as used by systemd
    daemon.listen = ['http://127.0.0.1?fd=3']

    # Allow multiple servers to use the same port (SO_REUSEPORT)
    daemon.listen = ['http://*:8080?reuse=1']

    # Listen on two ports with HTTP and HTTPS at the same time
    daemon.listen = ['http://*:3000', 'https://*:4000']

    # Location of a URL object
    import Pyjo.URL

    daemon.listen = [Pyjo.URL.new().set(scheme='http', host='127.0.0.1', port=3000)]
    is_ok(str(daemon.listen[0]), 'http://127.0.0.1:3000', 'URL object')

    # Use a custom certificate and key
    daemon.listen = ['https://*:3000?cert=/x/server.crt&key=/y/server.key']

    # Domain specific certificates and keys (SNI)
    daemon.listen = ['https://*:3000?example.com_cert=/x/my.crt&example.com_key=/y/my.key']

    # Or even a custom certificate authority
    daemon.listen = ['https://*:3000?cert=/x/server.crt&key=/y/server.key&ca=/z/ca.crt']
    is_ok(len(daemon.listen), 1, 'locations')

with subtest('max_clients'):
    max = daemon.max_clients
    is_ok(max, None, 'max')
    daemon.max_clients = 100
    is_ok(daemon.max_clients, 100, 'daemon.max_clients')

with subtest('max_requests'):
    max = daemon.max_requests
    is_ok(max, 100, 'max')
    daemon.max_requests = 250
    is_ok(daemon.max_requests, 250, 'daemon.max_requests')

with subtest('silent'):
    boolean = daemon.silent
    is_ok(boolean, True, 'boolean')
    daemon.silent = boolean
    is_ok(daemon.silent, True, 'daemon.silent')

with subtest('ports'):
    daemon = Pyjo.Server.Daemon.new(listen=['http://127.0.0.1', 'http://127.0.0.1'], silent=True).start()
    ports = daemon.ports()
    is_ok(len(ports), 2, 'ports')

    # All ports
    with redirect_stdout(io.StringIO()) as stdout:
        for port in daemon.ports():
            print(port)
    is_ok(stdout.getvalue(), ''.join(f'{port}\n' for port in ports), 'print(port)')
    daemon.stop()

with subtest('run'):
    daemon = Pyjo.Server.Daemon.new(listen=['http://127.0.0.1'], silent=True)
    Pyjo.IOLoop.timer(0, lambda loop: loop.stop())
    daemon.run()
    ok(len(daemon.acceptors), 'daemon.run()')
    daemon.stop()

with subtest('start'):
    daemon = Pyjo.Server.Daemon.new(silent=True)
    is_ok(daemon.listen, ['http://*:3000'], 'daemon')

    # Listen on random port
    daemon.listen = ['http://127.0.0.1']
    port = daemon.start().ports()[0]
    ok(port > 0, 'port')
    daemon.stop()

    # Run multiple web servers concurrently
    daemon1 = Pyjo.Server.Daemon.new(listen=['http://127.0.0.1'], silent=True).start()
    daemon2 = Pyjo.Server.Daemon.new(listen=['http://127.0.0.1'], silent=True).start()
    Pyjo.IOLoop.timer(0, lambda loop: loop.stop())
    if not Pyjo.IOLoop.is_running():
        Pyjo.IOLoop.start()
    ok(daemon1.ports()[0] != daemon2.ports()[0], 'two servers')
    daemon1.stop()
    daemon2.stop()

with subtest('stop'):
    daemon = Pyjo.Server.Daemon.new(listen=['http://127.0.0.1'], silent=True).start()
    is_ok(daemon.stop(), daemon, 'daemon')
    is_deeply_ok(daemon.acceptors, [], 'not accepting')

done_testing()
