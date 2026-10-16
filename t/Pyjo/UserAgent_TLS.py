# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor that Pyjo.Reactor.detect gives

import Pyjo.IOLoop
import Pyjo.IOLoop.TLS
import Pyjo.Server.Daemon
import Pyjo.UserAgent

from Pyjo.Test import *
from Pyjoyment.Lite import app, get

import os
import ssl

from unittest.mock import patch


# Left out from Mojolicious: plan skip_all unless TEST_TLS, as the ssl module comes with Python
if not Pyjo.IOLoop.TLS.object.can_tls():
    plan(skip_all='TLS support required for this test!')

# The certificates of the tests
certs = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'certs')


def cert(name):
    return os.path.join(certs, name)


# Silence
app.log.level = 'fatal'

get('/', {'text': 'works!'})

with subtest('Web server with valid certificates'):
    daemon = Pyjo.Server.Daemon.new(app=app, ioloop=Pyjo.IOLoop.singleton, silent=True)
    listen = (
        'https://127.0.0.1'
        + f'?cert={cert("server.crt")}'
        + f'&key={cert("server.key")}'
        + f'&ca={cert("ca.crt")}&verify=0x03'
    )
    daemon.listen = [listen]
    port = daemon.start().ports()[0]

    with subtest('No certificate'):
        ua = Pyjo.UserAgent.new(ioloop=Pyjo.IOLoop.singleton)
        tx = ua.get(f'https://127.0.0.1:{port}')
        ok(tx.error, 'has error')
        tx = ua.get(f'https://127.0.0.1:{port}')
        ok(tx.error, 'has error')
        ua.ca = cert('ca.crt')
        tx = ua.get(f'https://127.0.0.1:{port}')
        ok(tx.error, 'has error')
        tx = ua.get(f'https://127.0.0.1:{port}')
        ok(tx.error, 'has error')

    with subtest('Valid certificates'):
        ua = Pyjo.UserAgent.new(ioloop=Pyjo.IOLoop.singleton)
        ua.ca, ua.cert, ua.key = cert('ca.crt'), cert('client.crt'), cert('client.key')
        tx = ua.get(f'https://127.0.0.1:{port}')
        ok(not tx.error, 'no error')
        is_ok(tx.res.code, 200, 'right status')
        is_ok(tx.res.body, b'works!', 'right content')

    with subtest('Valid certificates (env)'):
        env = {
            'PYJO_CA_FILE': cert('ca.crt'),
            'PYJO_CERT_FILE': cert('client.crt'),
            'PYJO_KEY_FILE': cert('client.key'),
            'PYJO_INSECURE': '0',
        }
        with patch.dict(os.environ, env):
            # Unlike Mojolicious: the user agent reads the environment when it is made, where Mojo reads it on first use
            ua = Pyjo.UserAgent.new(ioloop=Pyjo.IOLoop.singleton)
            tx = ua.get(f'https://127.0.0.1:{port}')
        is_ok(ua.ca, cert('ca.crt'), 'right path')
        is_ok(ua.cert, cert('client.crt'), 'right path')
        is_ok(ua.key, cert('client.key'), 'right path')
        is_ok(ua.insecure, False, 'secure')
        ok(not tx.error, 'no error')
        is_ok(tx.res.code, 200, 'right status')
        is_ok(tx.res.body, b'works!', 'right content')

    with subtest('Invalid certificate'):
        ua = Pyjo.UserAgent.new(ioloop=Pyjo.IOLoop.singleton)
        ua.cert, ua.key = cert('bad.crt'), cert('bad.key')
        tx = ua.get(f'https://127.0.0.1:{port}')
        ok(tx.error, 'has error')

    daemon.stop()

with subtest('Web server with valid certificates and no verification'):
    daemon = Pyjo.Server.Daemon.new(app=app, ioloop=Pyjo.IOLoop.singleton, silent=True)
    # Unlike Mojolicious: TLSv1_2 and a cipher of it that the client of Python offers, where Mojo uses TLSv1 and
    # AES256-SHA, as OpenSSL 3 disables TLSv1 and Python deprecates it
    listen = (
        'https://127.0.0.1'
        + f'?cert={cert("server.crt")}'
        + f'&key={cert("server.key")}'
        + f'&ca={cert("ca.crt")}'
        + '&ciphers=ECDHE-RSA-AES256-GCM-SHA384:ALL'
        + '&verify=0x00'
        + '&version=TLSv1_2'
    )
    daemon.listen = [listen]
    port = daemon.start().ports()[0]

    # Invalid certificate
    ua = Pyjo.UserAgent.new(ioloop=Pyjo.IOLoop.singleton)
    ua.cert, ua.key = cert('bad.crt'), cert('bad.key')
    tx = ua.get(f'https://127.0.0.1:{port}')
    ok(tx.error, 'has error')
    ua = Pyjo.UserAgent.new(ioloop=ua.ioloop, insecure=True)
    ua.cert, ua.key = cert('bad.crt'), cert('bad.key')
    tx = ua.get(f'https://127.0.0.1:{port}')
    ok(not tx.error, 'no error')
    is_ok(
        ua.ioloop.stream(tx.connection).handle.cipher()[0],
        'ECDHE-RSA-AES256-GCM-SHA384',
        'ECDHE-RSA-AES256-GCM-SHA384 has been negotiated',
    )
    is_ok(ua.ioloop.stream(tx.connection).handle.version(), 'TLSv1.2', 'TLSv1.2 has been negotiated')
    daemon.stop()

with subtest('Client side TLS options'):
    daemon = Pyjo.Server.Daemon.new(app=app, ioloop=Pyjo.IOLoop.singleton, silent=True)
    # Unlike Mojolicious: TLSv1_2, where Mojo uses TLSv1_1, as OpenSSL 3 disables it and Python deprecates it
    daemon.listen = ['https://127.0.0.1/?version=TLSv1_2']
    port = daemon.start().ports()[0]

    with subtest('(Not) setting verification mode'):
        ua = Pyjo.UserAgent.new(ioloop=Pyjo.IOLoop.singleton)
        tx = ua.get(f'https://127.0.0.1:{port}')
        like_ok(tx.error['message'], r'certificate verify failed', 'has error')

        ua = Pyjo.UserAgent.new(ioloop=Pyjo.IOLoop.singleton)
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        ua.tls_context = context
        tx = ua.get(f'https://127.0.0.1:{port}')
        ok(not tx.error, 'no error')

    with subtest('Setting acceptable protocol version'):
        ua = Pyjo.UserAgent.new(ioloop=Pyjo.IOLoop.singleton)
        # Unlike Mojolicious: TLSv1_3 for a server of TLSv1_2, where Mojo has TLSv1_2 for TLSv1_1
        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        ua.tls_context = context
        tx = ua.get(f'https://127.0.0.1:{port}')
        # Unlike Mojolicious: the message of OpenSSL, where IO::Socket::SSL says "wrong ssl version"
        like_ok(tx.error['message'], r'(?i)protocol version|unsupported protocol', 'has error')

    daemon.stop()

done_testing()
