import Pyjo.Promise
import Pyjo.Test.Pyjo
import Pyjo.Transaction.HTTP

from Pyjo.Test import *

import os


with subtest('Synopsis'):
    from Pyjo.App.ASGI import ASGI

    async def hello(scope, receive, send):
        await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/plain')]})
        await send({'type': 'http.response.body', 'body': b'Hello World!'})

    app = ASGI(app=hello)
    Pyjo.Test.Pyjo.new(app).get_ok('/').status_is(200).content_is('Hello World!')
    app.close()

    # Or import the module, as in Google Python Style Guide

    import Pyjo.App.ASGI

    app = Pyjo.App.ASGI.new(app=hello)

    # Mount it in an application of Pyjoyment
    import Pyjoyment

    pyjoyment = Pyjoyment.new()
    pyjoyment.log.level = 'fatal'
    pyjoyment.plugin('Mount', {'/hello': app})
    Pyjo.Test.Pyjo.new(pyjoyment).get_ok('/hello').status_is(200).content_is('Hello World!')
    app.close()

with subtest('Ping'):
    import Pyjo.App.ASGI
    import Pyjo.IOLoop
    import Pyjo.Transaction

    from Pyjo.WebSocket import WS_PING

    # Ping the WebSockets every 20 seconds, of the transaction or of the controller of a route
    class KeepAlive(Pyjo.App.ASGI.object):
        interval = 20

        def handler(self, tx):
            ws = tx if isinstance(tx, Pyjo.Transaction.object) else tx.tx
            if ws.is_websocket:
                ping = (1, 0, 0, 0, WS_PING, b'')
                timer = Pyjo.IOLoop.recurring(self.interval, lambda loop: ws.established and ws.send(ping))
                ws.on('finish', lambda ws, code, reason: Pyjo.IOLoop.remove(timer))
            super().handler(tx)

    async def quiet(scope, receive, send):
        await receive()
        await send({'type': 'websocket.accept'})
        await receive()

    application = quiet
    app = KeepAlive.new(app=application)
    ok(isinstance(app, KeepAlive), 'right class')
    app.interval = 0.05

    # The WebSocket outlives the inactivity timeout of the server
    os.environ['PYJO_INACTIVITY_TIMEOUT'] = '0.3'
    try:
        t = Pyjo.Test.Pyjo.new(app)
        frames = []
        t.websocket_ok('/').tx.on('frame', lambda ws, frame: frames.append(frame[4]))
        Pyjo.IOLoop.timer(0.6, lambda loop: loop.stop())
        Pyjo.IOLoop.start()
    finally:
        del os.environ['PYJO_INACTIVITY_TIMEOUT']
    ok(len(frames) > 2, 'pings')
    is_deeply_ok(set(frames), {WS_PING}, 'only pings')
    t.finish_ok().finished_ok(1005)
    app.close()

with subtest('app'):
    app = Pyjo.App.ASGI.new()
    application = app.app
    is_ok(application, None, 'no application')
    app.app = hello
    ok(app.app is hello, 'application')

with subtest('new'):
    application = hello
    app = Pyjo.App.ASGI.new(app=application)
    ok(app.app is hello, 'application')

with subtest('handler'):
    app = Pyjo.App.ASGI.new(app=hello)
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.method = 'GET'
    tx.req.url.parse('/')
    resumed = Pyjo.Promise.new(lambda resolve, reject: tx.once('resume', lambda tx: resolve(tx.res.code)))
    app.handler(tx)
    codes = []
    resumed.then(codes.append).wait()
    is_deeply_ok(codes, [200], 'handled')
    app.close()

done_testing()
