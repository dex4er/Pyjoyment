import os


os.environ['PYJO_PROXY'] = '0'
# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor that Pyjo.Reactor.detect gives

import Pyjo.IOLoop
import Pyjo.IOLoop.Server
import Pyjo.IOLoop.TLS
import Pyjo.Transaction.HTTP
import Pyjo.UserAgent

from Pyjo.Test import *

import socket


if not (os.environ.get('TEST_ONLINE') or os.environ.get('TEST_ALL')):
    plan(skip_all='set TEST_ONLINE to enable this test (developer only!)')
if not Pyjo.IOLoop.TLS.object.can_tls():
    plan(skip_all='TLS support required for this test!')
# Left out from Mojolicious: Mozilla::CA, as ssl takes the certificate authorities of the system

from Pyjoyment.Lite import app, get


# TODO: the functions of ojo, when it is ported


@get('/remote_address')
def remote_address(c):
    c.render(text=c.tx.remote_address)


loop = Pyjo.IOLoop.singleton
ua = Pyjo.UserAgent.new()

with subtest('Make sure user agents dont taint the ioloop'):
    result = {}

    def cb(ua, tx):
        result.update(id=tx.connection, code=tx.res.code)
        loop.stop()

    ua.get('http://metacpan.org', cb)
    loop.start()
    ua = None
    loop.timer(0.25, lambda loop: loop.stop())
    loop.start()
    ok(not loop.stream(result['id']), 'loop not tainted')
    is_ok(result['code'], 301, 'right status')

ua = Pyjo.UserAgent.new()

with subtest('Local address'):
    ua.server.app = app
    with socket.create_connection(('mojolicious.org', 80)) as sock:
        address = sock.getsockname()[0]
    isnt_ok(address, '127.0.0.1', 'different address')
    ua.max_connections = 0
    # Unlike Mojolicious: source_address, where Mojo sets LocalAddr of socket_options
    ua.source_address = ('127.0.0.1', 0)
    tx = ua.get('/remote_address')
    ok(not ua.ioloop.stream(tx.connection), 'connection is not active')
    is_ok(tx.res.body, b'127.0.0.1', 'right address')
    ua.source_address = (address, 0)
    is_ok(ua.get('/remote_address').res.body, address.encode(), 'right address')

ua = Pyjo.UserAgent.new()
port = Pyjo.IOLoop.Server.object.generate_port()

with subtest('Connection refused'):
    tx = ua.build_tx('GET', f'http://127.0.0.1:{port}')
    ua.start(tx)
    ok(tx.is_finished, 'transaction is finished')
    ok(tx.error, 'has error')

with subtest('Connection refused (IPv4)'):
    tx = ua.build_tx('GET', f'http://127.0.0.1:{port}')
    ua.start(tx)
    ok(tx.is_finished, 'transaction is finished')
    ok(tx.error, 'has error')

with subtest('Connection refused (IPv6)'):
    tx = ua.build_tx('GET', f'http://[::1]:{port}')
    ua.start(tx)
    ok(tx.is_finished, 'transaction is finished')
    ok(tx.error, 'has error')

with subtest('Host does not exist'):
    tx = ua.build_tx('GET', 'http://cdeabcdeffoobarnonexisting.com')
    ua.start(tx)
    ok(tx.is_finished, 'transaction is finished')
    ok(tx.error, 'has error')

ua = Pyjo.UserAgent.new()

with subtest('Keep-alive'):
    ua.get('http://mojolicious.org', lambda ua, tx: Pyjo.IOLoop.singleton.stop())
    Pyjo.IOLoop.singleton.start()
    kept_alive = []

    def keep_alive(ua, tx):
        Pyjo.IOLoop.singleton.stop()
        kept_alive.append(tx.kept_alive)

    ua.get('http://mojolicious.org', keep_alive)
    Pyjo.IOLoop.singleton.start()
    ok(kept_alive[0], 'connection was kept alive')

with subtest('Nested keep-alive'):
    kept_alive = []

    def first(ua, tx):
        kept_alive.append(tx.kept_alive)

        def second(ua, tx):
            kept_alive.append(tx.kept_alive)

            def third(ua, tx):
                kept_alive.append(tx.kept_alive)
                Pyjo.IOLoop.singleton.stop()

            ua.get('http://mojolicious.org', third)

        ua.get('http://mojolicious.org', second)

    ua.get('http://mojolicious.org', first)
    Pyjo.IOLoop.singleton.start()
    is_deeply_ok(kept_alive, [True, True, True], 'connections kept alive')

ua = Pyjo.UserAgent.new()

with subtest('Custom non-keep-alive request'):
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.method = 'GET'
    tx.req.url.parse('http://metacpan.org')
    tx.req.headers.connection = 'close'
    ua.start(tx)
    ok(tx.is_finished, 'transaction is finished')
    is_ok(tx.res.code, 301, 'right status')
    like_ok(tx.res.headers.connection, r'(?i)close', 'right "Connection" header')

# TODO: the subtest "One-liner", when ojo is ported

with subtest('Simple request'):
    tx = ua.get('metacpan.org')
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(str(tx.req.url), 'http://metacpan.org', 'right url')
    is_ok(tx.res.code, 301, 'right status')

with subtest('Simple keep-alive requests'):
    tx = ua.get('https://www.wikipedia.org')
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(str(tx.req.url), 'https://www.wikipedia.org', 'right url')
    is_ok(tx.req.body, b'', 'no content')
    is_ok(tx.res.code, 200, 'right status')
    ok(tx.keep_alive, 'connection will be kept alive')
    ok(not tx.kept_alive, 'connection was not kept alive')
    tx = ua.get('https://www.wikipedia.org')
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(str(tx.req.url), 'https://www.wikipedia.org', 'right url')
    is_ok(tx.res.code, 200, 'right status')
    ok(tx.keep_alive, 'connection will be kept alive')
    ok(tx.kept_alive, 'connection was kept alive')
    tx = ua.get('https://www.wikipedia.org')
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(str(tx.req.url), 'https://www.wikipedia.org', 'right url')
    is_ok(tx.res.code, 200, 'right status')
    ok(tx.keep_alive, 'connection will be kept alive')
    ok(tx.kept_alive, 'connection was kept alive')

with subtest('Simple HTTPS request'):
    tx = ua.get('https://metacpan.org')
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(str(tx.req.url), 'https://metacpan.org', 'right url')
    is_ok(tx.res.code, 200, 'right status')

ua = Pyjo.UserAgent.new()

with subtest('Simple keep-alive form POST'):
    tx = ua.post('https://metacpan.org/search', form={'q': 'mojolicious'})
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(str(tx.req.url), 'https://metacpan.org/search', 'right url')
    is_ok(tx.req.headers.content_length, '13', 'right content length')
    is_ok(tx.req.body, b'q=mojolicious', 'right content')
    like_ok(tx.res.body, rb'Mojolicious', 'right content')
    is_ok(tx.res.code, 200, 'right status')
    ok(tx.keep_alive, 'connection will be kept alive')
    tx = ua.post('https://metacpan.org/search', form={'q': 'mojolicious'})
    is_ok(tx.req.method, 'POST', 'right method')
    is_ok(str(tx.req.url), 'https://metacpan.org/search', 'right url')
    is_ok(tx.req.headers.content_length, '13', 'right content length')
    is_ok(tx.req.body, b'q=mojolicious', 'right content')
    like_ok(tx.res.body, rb'Mojolicious', 'right content')
    is_ok(tx.res.code, 200, 'right status')
    ok(tx.kept_alive, 'connection was kept alive')
    ok(tx.local_address, 'has local address')
    ok(tx.local_port > 0, 'has local port')
    ok(tx.original_remote_address, 'has original remote address')
    ok(tx.remote_address, 'has remote address')
    ok(tx.remote_port > 0, 'has remote port')

with subtest('Simple request with redirect'):
    ua.max_redirects = 3
    tx = ua.get('http://wikipedia.org/wiki/Perl')
    ua.max_redirects = 0
    is_ok(tx.req.method, 'GET', 'right method')
    is_ok(str(tx.req.url), 'https://en.wikipedia.org/wiki/Perl', 'right url')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.previous.req.method, 'GET', 'right method')
    is_ok(str(tx.previous.req.url), 'https://www.wikipedia.org/wiki/Perl', 'right url')
    is_ok(tx.previous.res.code, 301, 'right status')
    is_ok(tx.redirects()[-1].req.method, 'GET', 'right method')
    is_ok(str(tx.redirects()[-1].req.url), 'https://www.wikipedia.org/wiki/Perl', 'right url')
    is_ok(tx.redirects()[-1].res.code, 301, 'right status')

with subtest('Connect timeout (non-routable address)'):
    ua.connect_timeout = 0.5
    tx = ua.get('192.0.2.1')
    ok(tx.is_finished, 'transaction is finished')
    is_ok(tx.error['message'], 'Connect timeout', 'right error')
    ua.connect_timeout = 3

done_testing()
