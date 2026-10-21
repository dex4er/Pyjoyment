import Pyjo.Promise
import Pyjo.Test.Pyjo
import Pyjo.Transaction.HTTP

from Pyjo.Test import *


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
