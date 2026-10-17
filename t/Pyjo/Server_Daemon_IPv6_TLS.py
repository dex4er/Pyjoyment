# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

import Pyjo.IOLoop
import Pyjo.IOLoop.TLS
import Pyjo.Server.Daemon
import Pyjo.UserAgent

from Pyjo.File import curfile
from Pyjo.Test import *
from Pyjoyment.Lite import app, get

import socket
import ssl
import sys


sys.path.insert(0, curfile().sibling('..', 'lib').to_str())

import TestConnectProxy  # noqa: E402  # pyright: ignore[reportMissingImports]


# Unlike Mojolicious: plan skip_all unless TEST_IPV6, the test runs where ::1 works
try:
    with socket.create_server(('::1', 0), family=socket.AF_INET6):
        pass
except OSError as e:
    plan(skip_all=f'IPv6 is not available: {e}')

# Left out from Mojolicious: plan skip_all unless TEST_TLS, as the ssl module comes with Python
if not Pyjo.IOLoop.TLS.object.can_tls():
    plan(skip_all='TLS support required for this test!')

# Renamed from Mojolicious: the certificates of the tests are in t/certs, as t/certs/README.md makes them, where Mojo
# has them in t/mojo/certs; mojo_server is the one of the host mojolicious.org, where Mojo has domain for example.com
certs = curfile().sibling('..', 'certs')

# Silence
app.log.level = 'fatal'

get('/', {'text': 'works!'})

# IPv6 and TLS
daemon = Pyjo.Server.Daemon.new(app=app, listen=['https://[::1]'], silent=True)
port = daemon.start().ports()[0]
ua = Pyjo.UserAgent.new(ioloop=Pyjo.IOLoop.singleton, insecure=True)
tx = ua.get(f'https://[::1]:{port}/')
is_ok(tx.res.code, 200, 'right status')
is_ok(tx.res.body, b'works!', 'right content')

with subtest('IPv6, TLS, SNI and a proxy'):
    if not ssl.HAS_SNI:
        plan(skip_all='SNI support required!')
    daemon = Pyjo.Server.Daemon.new(app=app, silent=True)
    # Unlike Mojolicious: the default certificate is server of t/certs, as a client sends no SNI for an IP address, and
    # the built-in certificate of Pyjo has a CA of its own, where the CA of the tests of Mojo signs its built-in one
    listen = (
        'https://[::1]'
        f'?cert={certs.child("server.crt")}'
        f'&key={certs.child("server.key")}'
        f'&127.0.0.1_cert={certs.child("server.crt")}'
        f'&127.0.0.1_key={certs.child("server.key")}'
        f'&mojolicious.org_cert={certs.child("mojo_server.crt")}'
        f'&mojolicious.org_key={certs.child("mojo_server.key")}'
    )
    daemon.listen = [listen]
    forward = daemon.start().ports()[0]
    id = TestConnectProxy.proxy({'address': '[::1]'}, {'address': '[::1]', 'port': forward})
    proxy = Pyjo.IOLoop.acceptor(id).port
    ua = Pyjo.UserAgent.new(ioloop=Pyjo.IOLoop.singleton, ca=certs.child('ca.crt').to_str())
    ua.proxy.https = f'http://[::1]:{proxy}'
    tx = ua.get('https://mojolicious.org/')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, b'works!', 'right content')
    ok(not tx.error, 'no error')
    tx = ua.get('https://127.0.0.1/')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, b'works!', 'right content')
    ok(not tx.error, 'no error')
    tx = ua.get('https://has.no.cert/')
    like_ok(tx.error['message'], r'name', 'right error')

done_testing()
