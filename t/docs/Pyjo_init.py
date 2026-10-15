import Pyjo.IOLoop
import Pyjo.Server.Daemon

from Pyjo.Test import *

import contextlib
import http.client
import io
import threading


# The examples request a real host and listen on a fixed port, so a local daemon answers instead
local = Pyjo.Server.Daemon.new(ioloop=Pyjo.IOLoop.singleton, listen=['http://127.0.0.1'], silent=True)
port = local.start().ports()[0]


@contextlib.contextmanager
def output():
    with contextlib.redirect_stdout(io.StringIO()) as stdout:
        yield stdout


with subtest('Synopsis'):
    with output() as stdout:
        # HTTP/WebSocket user agent
        import Pyjo.UserAgent

        ua = Pyjo.UserAgent.new()
        ua.ioloop = Pyjo.IOLoop.singleton

        @ua.on('start')
        def start(ua, tx):
            url = tx.req.url
            url.scheme, url.host, url.port = 'http', '127.0.0.1', port
            tx.req.proxy = None

        print(ua.get('www.mojolicious.org').result.headers.server)
    is_ok(stdout.getvalue(), 'Pyjoyment (Python)\n', 'user agent')

    with output() as stdout:
        # HTML/XML DOM parser with CSS selectors
        import Pyjo.DOM

        dom = Pyjo.DOM.new('<div><b>Hello Pyjo!</b></div>')
        print(dom.at('div > b').text)
    is_ok(stdout.getvalue(), 'Hello Pyjo!\n', 'DOM')

    with output() as stdout:
        # Python-ish templates
        import Pyjo.Template

        mt = Pyjo.Template.new(vars=True)
        print(mt.render('Hello <%= what %>!', {'what': 'Pyjo'}))
    is_ok(stdout.getvalue(), 'Hello Pyjo!\n\n', 'template, with the newline at its end')

    # HTTP/WebSocket server
    import Pyjo.Server.Daemon

    daemon = Pyjo.Server.Daemon.new(listen=['http://127.0.0.1'], silent=True)

    @daemon.unsubscribe('request').on('request')
    def request(daemon, tx):
        tx.res.code = 200
        tx.res.body = b'Hello Pyjo!'
        tx.resume()

    daemon_port = daemon.start().ports()[0]
    results = []

    def client():
        conn = http.client.HTTPConnection('127.0.0.1', daemon_port, timeout=10)
        conn.request('GET', '/')
        results.append(conn.getresponse().read())
        conn.close()

    # The client in a thread of its own, and the event loop stops when it is done
    worker = threading.Thread(target=client)
    worker.start()
    id = Pyjo.IOLoop.recurring(0.05, lambda loop: worker.is_alive() or loop.stop())
    daemon.run()
    worker.join()
    Pyjo.IOLoop.remove(id)
    is_deeply_ok(results, [b'Hello Pyjo!'], 'server')

    with output() as stdout:
        # Event loop, with a tenth of a second for each second
        import Pyjo.IOLoop

        for seconds in range(1, 6):
            Pyjo.IOLoop.timer(seconds / 10, lambda loop, seconds=seconds: print(seconds))
        Pyjo.IOLoop.timer(0.6, lambda loop: loop.stop())
        Pyjo.IOLoop.start()
    is_ok(stdout.getvalue(), '1\n2\n3\n4\n5\n', 'event loop')

local.stop()

done_testing()
