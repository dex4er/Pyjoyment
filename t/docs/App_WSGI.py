import Pyjo.Promise
import Pyjo.Test.Pyjo
import Pyjo.Transaction.HTTP

from Pyjo.Test import *


with subtest('Synopsis'):
    from Pyjo.App.WSGI import WSGI

    def hello(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [b'Hello World!']

    app = WSGI(app=hello)
    Pyjo.Test.Pyjo.new(app).get_ok('/').status_is(200).content_is('Hello World!')
    app.close()

    # Or import the module, as in Google Python Style Guide

    import Pyjo.App.WSGI

    app = Pyjo.App.WSGI.new(app=hello)

    # Mount it in an application of Pyjoyment
    import Pyjoyment

    pyjoyment = Pyjoyment.new()
    pyjoyment.log.level = 'fatal'
    pyjoyment.plugin('Mount', {'/hello': app})
    Pyjo.Test.Pyjo.new(pyjoyment).get_ok('/hello').status_is(200).content_is('Hello World!')
    app.close()

with subtest('app'):
    app = Pyjo.App.WSGI.new()
    application = app.app
    is_ok(application, None, 'no application')
    app.app = hello
    ok(app.app is hello, 'application')

with subtest('threads'):
    app = Pyjo.App.WSGI.new()
    threads = app.threads
    is_ok(threads, 4, 'default')
    app.threads = 10
    is_ok(app.threads, 10, 'threads')

with subtest('new'):
    application = hello
    app = Pyjo.App.WSGI.new(app=application)
    ok(app.app is hello, 'application')
    app = Pyjo.App.WSGI.new(app=application, threads=10)
    is_ok(app.threads, 10, 'threads')

with subtest('close'):
    app = Pyjo.App.WSGI.new(app=hello)
    Pyjo.Test.Pyjo.new(app).get_ok('/').status_is(200)
    app.close()
    Pyjo.Test.Pyjo.new(app).get_ok('/').status_is(200).content_is('Hello World!')
    app.close()

with subtest('handler'):
    app = Pyjo.App.WSGI.new(app=hello)
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
