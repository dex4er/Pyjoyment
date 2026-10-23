import Pyjo.App
import Pyjo.HelloWorld
import Pyjo.Home
import Pyjo.Log
import Pyjo.Server
import Pyjo.Transaction.HTTP
import Pyjo.UserAgent
import Pyjoyment
import Pyjoyment.HelloWorld

from Pyjo.Test import *

import os


class MyApp(Pyjo.App.object):
    def handler(self, tx):
        tx.res.code = 200
        tx.res.body = f'{tx.req.method} request for {tx.req.url.path}!'.encode()
        tx.resume()


with subtest('Defaults'):
    level = os.environ.pop('PYJO_LOG_LEVEL', None)
    try:
        app = MyApp.new()
        isa_ok(app.log, Pyjo.Log.object, 'log')
        is_ok(app.log.level, 'trace', 'all messages')
    finally:
        if level is not None:
            os.environ['PYJO_LOG_LEVEL'] = level
    isa_ok(app.home, Pyjo.Home.object, 'home')
    isa_ok(app.ua, Pyjo.UserAgent.object, 'user agent')
    is_ok(app.moniker, 'my_app', 'moniker of a class in a script')
    is_deeply_ok(app.config(), {}, 'no configuration')
    isa_ok(app.build_tx(), Pyjo.Transaction.HTTP.object, 'transaction')
    is_ok(app.server(Pyjo.Server.new()), None, 'nothing to do before the server starts')

with subtest('Log level from the environment'):
    level = os.environ.get('PYJO_LOG_LEVEL')
    os.environ['PYJO_LOG_LEVEL'] = 'fatal'
    try:
        is_ok(MyApp.new().log.level, 'fatal', 'PYJO_LOG_LEVEL')
        is_ok(Pyjoyment.new().log.level, 'fatal', 'as Pyjoyment has it')
    finally:
        if level is None:
            del os.environ['PYJO_LOG_LEVEL']
        else:
            os.environ['PYJO_LOG_LEVEL'] = level

with subtest('Attributes'):
    log = Pyjo.Log.new()
    app = MyApp.new(log=log, moniker='foo_bar')
    is_ok(app.log, log, 'log')
    is_ok(app.moniker, 'foo_bar', 'moniker')
    app = MyApp.new({'moniker': 'baz'})
    is_ok(app.moniker, 'baz', 'moniker from a dict')

with subtest('Arguments of the server'):
    Pyjo.Server.args_override = {'moniker': 'override'}
    try:
        is_ok(MyApp.new(moniker='foo').moniker, 'override', 'overridden')
    finally:
        Pyjo.Server.args_override = {}

with subtest('Moniker of a module'):
    is_ok(Pyjo.HelloWorld.new().moniker, 'pyjo-hello_world', 'module that names its object')
    is_ok(Pyjoyment.new().moniker, 'pyjoyment', 'package')
    is_ok(Pyjoyment.HelloWorld.new().moniker, 'pyjoyment-hello_world', 'subclass of Pyjoyment')

with subtest('Handler'):
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.method = 'GET'
    tx.req.url.parse('/foo')
    MyApp.new().handler(tx)
    is_ok(tx.res.body, b'GET request for /foo!', 'right content')
    throws_ok(lambda: Pyjo.App.new().handler(tx), 'Method "handler" not implemented by subclass', 'abstract')

with subtest('Server'):
    ua = Pyjo.UserAgent.new()
    ua.server.app = MyApp.new()
    tx = ua.get('/bar')
    is_ok(tx.res.code, 200, 'right status')
    is_ok(tx.res.body, b'GET request for /bar!', 'right content')

with subtest('Application loader'):
    app = MyApp.new()
    is_ok(app.start(), app, 'started')
    os.environ['PYJO_APP_LOADER'] = '1'
    try:
        app.start()
        is_ok(Pyjo.Server.loaded_app, app, 'loaded')
    finally:
        del os.environ['PYJO_APP_LOADER']
        Pyjo.Server.loaded_app = None

with subtest('Subclasses'):
    isa_ok(Pyjo.HelloWorld.new(), Pyjo.App.object, 'Pyjo.HelloWorld')
    isa_ok(Pyjoyment.new(), Pyjo.App.object, 'Pyjoyment')

done_testing()
