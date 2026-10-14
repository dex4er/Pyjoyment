import Pyjo.Message.Request
import Pyjo.Transaction.HTTP

from Pyjo.Test import *

import contextlib
import io


def output(cb):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        cb()
    return out.getvalue()


with subtest('Synopsis'):

    def client():
        import Pyjo.Transaction.HTTP

        # Client
        tx = Pyjo.Transaction.HTTP.new()
        tx.req.method = 'GET'
        tx.req.url.parse('http://example.com')
        tx.req.headers.accept = 'application/json'
        print(tx.res.code)
        print(tx.res.headers.content_type)
        print(tx.res.body)
        print(tx.remote_address)

    is_ok(output(client), "None\nNone\nb''\nNone\n", 'client')

    def server():
        import Pyjo.Transaction.HTTP

        # Server
        tx = Pyjo.Transaction.HTTP.new()
        print(tx.req.method)
        print(tx.req.url.to_abs())
        print(tx.req.headers.accept)
        print(tx.remote_address)
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = b'Hello World!'

    is_ok(output(server), 'GET\n\nNone\nNone\n', 'server')

with subtest('request'):
    tx = Pyjo.Transaction.HTTP.new()
    tx.on('request', lambda tx: ...)
    ok(tx.has_subscribers('request'), 'subscribed')

    tx = Pyjo.Transaction.HTTP.new()
    tx.on('request', lambda tx: tx.res.headers.header('X-Bender', 'Bite my shiny metal ass!'))
    tx.server_read(b'GET / HTTP/1.1\x0d\x0a\x0d\x0a')
    is_ok(tx.res.headers.header('X-Bender'), 'Bite my shiny metal ass!', 'request handled')

with subtest('resume'):
    tx = Pyjo.Transaction.HTTP.new()
    tx.on('resume', lambda tx: ...)
    ok(tx.has_subscribers('resume'), 'subscribed')

with subtest('unexpected'):
    tx = Pyjo.Transaction.HTTP.new()
    tx.on('unexpected', lambda tx, res: ...)
    ok(tx.has_subscribers('unexpected'), 'subscribed')

    tx = Pyjo.Transaction.HTTP.new()
    tx.on('unexpected', lambda tx, res: tx.res.on('finish', lambda res: print('Follow-up response is finished.')))
    is_ok(
        output(lambda: tx.client_read(b'HTTP/1.1 100 Continue\x0d\x0a\x0d\x0aHTTP/1.1 204 No Content\x0d\x0a\x0d\x0a')),
        'Follow-up response is finished.\n',
        'unexpected response',
    )

with subtest('new'):
    tx = Pyjo.Transaction.HTTP.new()
    isa_ok(tx, Pyjo.Transaction.HTTP.object, 'transaction')
    tx = Pyjo.Transaction.HTTP.new(req=Pyjo.Message.Request.new())
    isa_ok(tx.req, Pyjo.Message.Request.object, 'request')

with subtest('previous'):
    tx = Pyjo.Transaction.HTTP.new()
    previous = tx.previous
    is_ok(previous, None, 'default')
    tx.previous = Pyjo.Transaction.HTTP.new()
    isa_ok(tx.previous, Pyjo.Transaction.HTTP.object, 'set')

    tx.previous.req.url.parse('/second')
    tx.previous.previous = Pyjo.Transaction.HTTP.new()
    tx.previous.previous.req.url.parse('/first')
    is_ok(output(lambda: print(tx.previous.previous.req.url.path)), '/first\n', 'first request')
    is_ok(output(lambda: print(tx.previous.req.url.path)), '/second\n', 'second request')

with subtest('client_read'):
    tx = Pyjo.Transaction.HTTP.new()
    tx.client_read(b'HTTP/1.1 200 OK\x0d\x0aContent-Length: 0\x0d\x0a\x0d\x0a')
    ok(tx.is_finished, 'response read')

with subtest('client_write'):
    tx = Pyjo.Transaction.HTTP.new()
    data = tx.client_write()
    is_ok(data, b'GET / HTTP/1.1\x0d\x0aHost: \x0d\x0a\x0d\x0a', 'request written')

with subtest('is_empty'):
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.method = 'HEAD'
    boolean = tx.is_empty
    is_ok(boolean, True, 'HEAD request')

with subtest('keep_alive'):
    tx = Pyjo.Transaction.HTTP.new()
    boolean = tx.keep_alive
    is_ok(boolean, True, 'HTTP/1.1')

with subtest('redirects'):
    tx = Pyjo.Transaction.HTTP.new(previous=Pyjo.Transaction.HTTP.new(previous=Pyjo.Transaction.HTTP.new()))
    tx.previous.req.url.parse('/second')
    tx.previous.previous.req.url.parse('/first')
    redirects = tx.redirects()
    is_ok(len(redirects), 2, 'two previous transactions')

    def paths():
        # Paths of all previous requests
        for previous in tx.redirects():
            print(previous.req.url.path)

    is_ok(output(paths), '/first\n/second\n', 'paths')

with subtest('resume'):
    tx = Pyjo.Transaction.HTTP.new()
    resumed = []
    tx.on('resume', lambda tx: resumed.append(True))
    tx = tx.resume()
    is_deeply_ok(resumed, [True], 'resumed')

with subtest('server_read'):
    tx = Pyjo.Transaction.HTTP.new()
    tx.server_read(b'GET / HTTP/1.1\x0d\x0a\x0d\x0a')
    ok(tx.req.is_finished, 'request read')

with subtest('server_write'):
    tx = Pyjo.Transaction.HTTP.new()
    tx.res.code = 200
    tx.res.headers.date = 'Sun, 17 Aug 2008 16:27:35 GMT'
    data = tx.resume().server_write()
    is_ok(
        data,
        b'HTTP/1.1 200 OK\x0d\x0aContent-Length: 0\x0d\x0aDate: Sun, 17 Aug 2008 16:27:35 GMT\x0d\x0a\x0d\x0a',
        'written',
    )

done_testing()
