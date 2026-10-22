import Pyjo.Home
import Pyjo.Log
import Pyjo.Server
import Pyjo.Transaction.HTTP
import Pyjo.UserAgent

from Pyjo.Test import *


with subtest('Synopsis'):
    from Pyjo.App import App

    class MyApp(App):
        # All the complexities of CGI, WSGI, ASGI, HTTP and WebSockets get
        # reduced to a single method call!
        def handler(self, tx):
            # Resume transaction at the end of the block
            with tx:
                # Request
                method = tx.req.method
                path = tx.req.url.path

                # Response
                tx.res.code = 200
                tx.res.headers.content_type = 'text/plain'
                tx.res.body = f'{method} request for {path}!'.encode()

    ua = Pyjo.UserAgent.new()
    ua.server.app = MyApp()
    is_ok(ua.get('/foo').res.text, 'GET request for /foo!', 'handler')

    # Or import the module, as in Google Python Style Guide

    import Pyjo.App

    class MyApp(Pyjo.App.object):
        # All the complexities of CGI, WSGI, ASGI, HTTP and WebSockets get
        # reduced to a single method call!
        def handler(self, tx):
            # Resume transaction at the end of the block
            with tx:
                # Request
                method = tx.req.method
                path = tx.req.url.path

                # Response
                tx.res.code = 200
                tx.res.headers.content_type = 'text/plain'
                tx.res.body = f'{method} request for {path}!'.encode()

    ua = Pyjo.UserAgent.new()
    ua.server.app = MyApp.new()
    is_ok(ua.get('/foo').res.text, 'GET request for /foo!', 'handler')

with subtest('new'):
    app = MyApp.new()
    app = MyApp.new(moniker='foo_bar')
    is_ok(app.moniker, 'foo_bar', 'keyword argument')
    app = MyApp.new({'moniker': 'foo_bar'})
    is_ok(app.moniker, 'foo_bar', 'dict')

with subtest('home'):
    app = MyApp.new()
    home = app.home
    isa_ok(home, Pyjo.Home.object, 'default')
    app.home = Pyjo.Home.new()

    # Portably generate path relative to home directory
    path = app.home.child('data', 'important.txt')
    like_ok(path.to_str(), r'data[/\\]important\.txt$', 'path')

with subtest('log'):
    app = MyApp.new()
    log = app.log
    isa_ok(log, Pyjo.Log.object, 'default')
    app.log = Pyjo.Log.new()

    # Log debug message
    with app.log.capture('debug') as messages:
        app.log.debug('It works')
    like_ok(str(messages), r'It works', 'logged')

with subtest('moniker'):
    app = MyApp.new()
    moniker = app.moniker
    is_ok(moniker, 'my_app', 'default')
    app.moniker = 'foo_bar'
    is_ok(app.moniker, 'foo_bar', 'set')

with subtest('ua'):
    app = MyApp.new()
    ua = app.ua
    isa_ok(ua, Pyjo.UserAgent.object, 'default')
    app.ua = Pyjo.UserAgent.new()
    # The example of a blocking request needs the network, so it is not run

with subtest('build_tx'):
    tx = MyApp.new().build_tx()
    isa_ok(tx, Pyjo.Transaction.HTTP.object, 'transaction')

with subtest('close'):
    import Pyjo.App

    app = Pyjo.App.new()
    before = app.ua.server.url().port
    app.close()
    isnt_ok(app.ua.server.url().port, before, 'a new server when it is used again')
    app.close()


with subtest('config'):
    app = MyApp.new()
    hash = app.config()
    is_deeply_ok(hash, {}, 'empty')
    app = app.config({'foo': 'bar', 'baz': 23})
    app = app.config(foo='bar', baz=23)
    foo = app.config('foo')
    is_ok(foo, 'bar', 'value')

    # Remove value
    foo = app.config().pop('foo')

    # Assign multiple values at once
    app.config(foo='test', bar=23)
    is_deeply_ok(app.config(), {'baz': 23, 'foo': 'test', 'bar': 23}, 'values')

with subtest('handler'):
    tx = Pyjo.Transaction.HTTP.new()
    MyApp.new().handler(tx)
    is_ok(tx.res.code, 200, 'handled')
    throws_ok(lambda: Pyjo.App.new().handler(tx), NotImplementedError, 'meant to be overloaded')

with subtest('server'):
    is_ok(MyApp.new().server(Pyjo.Server.new()), None, 'nothing by default')

with subtest('server_stopped'):
    promise = MyApp.new().server_stopped(Pyjo.Server.new())
    is_ok(promise, None, 'nothing by default')

with subtest('start'):
    app = MyApp.new()
    app = app.start()
    isa_ok(app, MyApp, 'started')

done_testing()
