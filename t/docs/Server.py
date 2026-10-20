import Pyjo.HelloWorld

from Pyjo.File import tempdir
from Pyjo.Test import *


with subtest('Synopsis'):
    from Pyjo.Server import Server

    class Pyjo_Server_MyServer(Server):
        def run(self):
            # Get a transaction
            tx = self.build_tx()

            # Emit "request" event
            self.emit('request', tx)

    server = Pyjo_Server_MyServer()
    server.run()
    ok(isinstance(server.app, Pyjo.HelloWorld.object), 'run')

    # Or import the module, as in Google Python Style Guide

    import Pyjo.Server

    class Pyjo_Server_MyServer(Pyjo.Server.object):
        def run(self):
            # Get a transaction
            tx = self.build_tx()

            # Emit "request" event
            self.emit('request', tx)

    server = Pyjo_Server_MyServer.new()
    server.run()
    ok(isinstance(server.app, Pyjo.HelloWorld.object), 'run')

with subtest('request'):
    import Pyjo.Transaction.HTTP

    server = Pyjo.Server.new()
    server.on('request', lambda server, tx: ...)
    is_ok(len(server.subscribers('request')), 2, 'subscribed')

    server.unsubscribe('request')

    @server.on('request')
    def request(server, tx):
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = b'Hello World!'
        tx.resume()

    tx = Pyjo.Transaction.HTTP.new()
    server.emit('request', tx)
    is_ok(tx.res.body, b'Hello World!', 'response')

with subtest('app'):
    app = server.app
    ok(isinstance(app, Pyjo.HelloWorld.object), 'app')
    server.app = Pyjo.HelloWorld.new()
    ok(server.app is not app, 'server.app')

with subtest('reverse_proxy'):
    boolean = server.reverse_proxy
    is_ok(boolean, False, 'boolean')
    server.reverse_proxy = True
    is_ok(server.reverse_proxy, True, 'server.reverse_proxy')

with subtest('trusted_proxies'):
    proxies = server.trusted_proxies
    is_deeply_ok(proxies, [], 'proxies')
    server.trusted_proxies = ['10.0.0.0/8', '127.0.0.1', '172.16.0.0/12', '192.168.0.0/16', 'fc00::/7']
    is_ok(len(server.trusted_proxies), 5, 'server.trusted_proxies')

with subtest('build_app'):
    import Pyjo.Log

    app = server.build_app('Pyjo.HelloWorld')
    ok(isinstance(app, Pyjo.HelloWorld.object), 'by name')
    log = Pyjo.Log.new()
    app = server.build_app('Pyjo.HelloWorld', log=log)
    is_ok(app.log, log, 'with arguments')
    app = server.build_app(Pyjo.HelloWorld.object)
    ok(isinstance(app, Pyjo.HelloWorld.object), 'by class')

with subtest('build_tx'):
    tx = server.build_tx()
    ok(tx.req.reverse_proxy, 'tx')

with subtest('daemonize'):
    # Not run: it forks and ends the process of the test
    ok(callable(server.daemonize), 'server.daemonize()')

with subtest('load_app'):
    tmp = tempdir()
    script = tmp.child('myapp.py').spew('import Pyjo.HelloWorld\n\nPyjo.HelloWorld.new().start()\n')
    app = server.load_app(script.to_str())
    ok(isinstance(app, Pyjo.HelloWorld.object), 'app')
    app = server.load_app(script.to_str(), log=log)
    is_ok(app.log, log, 'with arguments')

    import os

    cwd = os.getcwd()
    os.chdir(tmp)
    try:
        is_ok(Pyjo.Server.new().load_app('./myapp.py').log.level, 'error', 'print(...)')
    finally:
        os.chdir(cwd)

with subtest('new'):
    server = Pyjo.Server.new()
    is_ok(server.reverse_proxy, False, 'server')
    server = Pyjo.Server.new(reverse_proxy=True)
    is_ok(server.reverse_proxy, True, 'server')

with subtest('run'):
    throws_ok(lambda: server.run(), NotImplementedError, 'server.run()')

done_testing()
