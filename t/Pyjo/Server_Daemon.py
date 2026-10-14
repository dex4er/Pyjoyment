import os


os.environ['PYJO_NO_TLS'] = '1'
# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor that Pyjo.Reactor.detect gives

import Pyjo.IOLoop
import Pyjo.Server
import Pyjo.Server.Daemon
import Pyjo.Transaction.HTTP

from Pyjo.File import tempdir
from Pyjo.Test import *

import gc
import importlib
import re
import sys

from unittest.mock import patch


# The minimal Mojolicious::Lite of the tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
Lite = importlib.import_module('Lite')
Mojolicious = Lite.Mojolicious


class TestApp(Mojolicious):
    def handler(self, tx):
        tx.res.code = 200
        tx.res.body = b'Hello TestApp!'
        tx.resume()


# TODO: the subtest "Minimal application", which needs Pyjo.UserAgent, when it is ported

with subtest('Timeouts'):
    with patch.dict(os.environ):
        os.environ.pop('PYJO_INACTIVITY_TIMEOUT', None)
        os.environ.pop('PYJO_KEEP_ALIVE_TIMEOUT', None)
        is_ok(Pyjo.Server.Daemon.new().inactivity_timeout, 30, 'right value')
        os.environ['PYJO_INACTIVITY_TIMEOUT'] = '25'
        is_ok(Pyjo.Server.Daemon.new().inactivity_timeout, 25, 'right value')
        os.environ['PYJO_INACTIVITY_TIMEOUT'] = '0'
        is_ok(Pyjo.Server.Daemon.new().inactivity_timeout, 0, 'right value')
        is_ok(Pyjo.Server.Daemon.new().keep_alive_timeout, 5, 'right value')
        os.environ['PYJO_KEEP_ALIVE_TIMEOUT'] = '25'
        is_ok(Pyjo.Server.Daemon.new().keep_alive_timeout, 25, 'right value')
        os.environ['PYJO_KEEP_ALIVE_TIMEOUT'] = '0'
        is_ok(Pyjo.Server.Daemon.new().keep_alive_timeout, 0, 'right value')

with subtest('Listen'):
    with patch.dict(os.environ):
        os.environ.pop('PYJO_LISTEN', None)
        is_deeply_ok(Pyjo.Server.Daemon.new().listen, ['http://*:3000'], 'right value')
        os.environ['PYJO_LISTEN'] = 'http://127.0.0.1:8080'
        is_deeply_ok(Pyjo.Server.Daemon.new().listen, ['http://127.0.0.1:8080'], 'right value')
        os.environ['PYJO_LISTEN'] = 'http://*:80,https://*:443'
        is_deeply_ok(Pyjo.Server.Daemon.new().listen, ['http://*:80', 'https://*:443'], 'right value')

with subtest('Reverse proxy'):
    ok(not Pyjo.Server.Daemon.new().reverse_proxy, 'no reverse proxy')
    with patch.dict(os.environ, {'PYJO_REVERSE_PROXY': '1'}):
        ok(Pyjo.Server.Daemon.new().reverse_proxy, 'reverse proxy')

with subtest('Config'):
    app = Mojolicious()
    is_ok(app.config('foo'), None, 'no value')
    is_deeply_ok(app.config(foo='bar').config(), {'foo': 'bar'}, 'right value')
    is_ok(app.config('foo'), 'bar', 'right value')
    del app.config()['foo']
    is_ok(app.config('foo'), None, 'no value')
    app.config(foo='bar', baz='yada')
    is_ok(app.config({'test': 23}).config()['test'], 23, 'right value')
    is_deeply_ok(app.config(), {'foo': 'bar', 'baz': 'yada', 'test': 23}, 'right value')

# Not in Mojolicious: the scripts and modules that Mojo has in t/mojo/lib, written into a temporary directory
tmp = tempdir()
tmp.child('myapp.py').spew('import sys\n\nfrom Lite import app\n\napp.config(script=sys.argv[0])\n\napp.start()\n')
tmp.child('A.py').spew('class A:\n    pass\n')
tmp.child('LoaderException.py').spew('class LoaderException:\n    def new(self):\n        pass\n\n\nfoo = {\n')

with subtest('Loading'):
    daemon = Pyjo.Server.Daemon.new()
    path = tmp.child('myapp.py')
    is_ok(type(daemon.load_app(path)).__qualname__, 'Lite', 'right reference')
    is_ok(daemon.app.config('script'), path.to_abs().to_str(), 'right script name')
    is_ok(type(daemon.build_app(f'{__name__}.TestApp')).__qualname__, 'TestApp', 'right reference')
    is_ok(type(daemon.app).__qualname__, 'TestApp', 'right reference')

with subtest('Load broken app'):
    throws_ok(
        lambda: Pyjo.Server.Daemon.new().load_app(tmp.child('A.py')),
        re.compile(r'did not return an application object'),
        'right error',
    )
    try:
        Pyjo.Server.Daemon.new().load_app(tmp.child('LoaderException.py'))
        err = ''
    except Exception as e:
        err = str(e)
    # Unlike Mojolicious: the message of Python for the syntax error
    like_ok(err, r"'\{' was never closed", 'right error')
    like_ok(err, r"^Can't load application", 'right error')

# Left out from Mojolicious: the subtest "Load app using module_true", a feature of Perl 5.38

with subtest('Load missing application class'):
    throws_ok(
        lambda: Pyjo.Server.Daemon.new().build_app('Pyjo.DoesNotExist'),
        re.compile(r'^Can\'t find application class "Pyjo\.DoesNotExist" in sys\.path'),
        'right error',
    )

with subtest('Invalid listen location'):
    throws_ok(
        lambda: Pyjo.Server.Daemon.new(listen=['fail']).start(),
        re.compile(r'Invalid listen location'),
        'right error',
    )

with subtest('Transaction'):
    app = Mojolicious()
    isa_ok(app.build_tx(), Pyjo.Transaction.HTTP.object, 'right transaction')

app = Mojolicious()

# TODO: the subtest "Moniker", the routes of the application and the subtests from "Normal request" to "Timeout",
# which need Pyjo.UserAgent, when it is ported

with subtest('Pipelined'):
    daemon = Pyjo.Server.Daemon.new(listen=['http://127.0.0.1'], silent=True)
    port = daemon.start().ports()[0]
    # Unlike Mojolicious: the moniker of Pyjo.HelloWorld
    is_ok(daemon.app.moniker, 'pyjo-hello_world', 'right moniker')
    buffer = b''

    @Pyjo.IOLoop.client(port=port)
    def id(loop, err, stream):
        @stream.on('read')
        def read(stream, chunk):
            global buffer
            buffer += chunk
            buffer, count = re.subn(rb' is working!.*is working!$', b'', buffer, flags=re.S)
            if count:
                Pyjo.IOLoop.remove(id)
                Pyjo.IOLoop.stop()

        stream.write(
            b'GET /pipeline1/ HTTP/1.1\x0d\x0a'
            b'Content-Length: 0\x0d\x0a\x0d\x0a'
            b'GET /pipeline2/ HTTP/1.1\x0d\x0a'
            b'Content-Length: 0\x0d\x0a\x0d\x0a'
        )

    Pyjo.IOLoop.start()
    # Unlike Mojolicious: Pyjo.HelloWorld answers "Your Pyjo is working!"
    like_ok(buffer, rb'Pyjo$', 'transactions were pipelined')

with subtest('Throttling'):
    daemon = Pyjo.Server.Daemon.new(app=app, listen=['http://127.0.0.1'], max_clients=23, silent=True)
    is_ok(len(daemon.acceptors), 0, 'no active acceptors')
    is_ok(len(daemon.start().start().acceptors), 1, 'one active acceptor')
    is_ok(daemon.ioloop.max_connections, 23, 'right value')
    id = daemon.acceptors[0]
    ok(Pyjo.IOLoop.acceptor(id), 'acceptor has been added')
    is_ok(len(daemon.stop().acceptors), 0, 'no active acceptors')
    ok(not Pyjo.IOLoop.acceptor(id), 'acceptor has been removed')
    is_ok(len(daemon.start().acceptors), 1, 'one active acceptor')
    id = daemon.acceptors[0]
    ok(Pyjo.IOLoop.acceptor(id), 'acceptor has been added')
    del daemon
    # Not in Mojolicious: PyPy frees the daemon when its garbage collector runs
    gc.collect()
    ok(not Pyjo.IOLoop.acceptor(id), 'acceptor has been removed')

with subtest('Single-accept and connection limit'):
    loop = Pyjo.IOLoop.new()
    daemon = Pyjo.Server.Daemon.new(
        app=app, ioloop=loop, listen=['http://127.0.0.1?single_accept=1'], max_clients=2, silent=True
    ).start()
    acceptor = loop.acceptor(daemon.acceptors[0])
    accepting = []

    @acceptor.on('accept')
    def accept(acceptor, handle):
        def tick(loop):
            accepting.append(acceptor.is_accepting)
            if len(accepting) == 2:
                loop.stop()

        loop.next_tick(tick)

    for _ in range(2):
        loop.client(lambda loop, err, stream: None, port=acceptor.port)
    loop.start()
    ok(accepting[0], 'accepting connections')
    ok(not accepting[1], 'connection limit reached')

# TODO: the subtests "Request limit" and "File descriptor", which need Pyjo.UserAgent, when it is ported

with subtest('No TLS support'):
    # Unlike Mojolicious: the message of Pyjo.IOLoop.Server, where Mojo names IO::Socket::SSL
    throws_ok(
        lambda: Pyjo.Server.Daemon.new(listen=['https://127.0.0.1'], silent=True).start(),
        re.compile(r'TLS support is disabled'),
        'right error',
    )

with subtest('Abstract methods'):
    throws_ok(
        lambda: Pyjo.Server.new().run(),
        re.compile(r'Method "run" not implemented by subclass'),
        'right error',
    )

done_testing()
