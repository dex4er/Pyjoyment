from Pyjo.Test import *

import os

from unittest.mock import patch


with subtest('Synopsis'):
    import Pyjo.HelloWorld

    hello = Pyjo.HelloWorld.new()
    is_ok(hello.start(), hello, 'hello.start()')

with subtest('new'):
    import Pyjo.Log

    hello = Pyjo.HelloWorld.new()
    is_ok(hello.log.level, 'error', 'hello')
    hello = Pyjo.HelloWorld.new(log=Pyjo.Log.new())
    is_ok(hello.log.level, 'trace', 'log')

with subtest('log'):
    log = hello.log
    ok(isinstance(log, Pyjo.Log.object), 'log')
    hello.log = Pyjo.Log.new()
    ok(hello.log is not log, 'hello.log')

with subtest('moniker'):
    moniker = hello.moniker
    is_ok(moniker, 'pyjo-hello_world', 'moniker')
    hello.moniker = 'foo_bar'
    is_ok(hello.moniker, 'foo_bar', 'hello.moniker')

with subtest('build_tx'):
    import Pyjo.Transaction.HTTP

    tx = hello.build_tx()
    ok(isinstance(tx, Pyjo.Transaction.HTTP.object), 'tx')

with subtest('config'):
    config = hello.config()
    is_deeply_ok(config, {}, 'empty')
    is_ok(hello.config({'foo': 'bar', 'baz': 23}), hello, 'hello.config({...})')
    is_ok(hello.config(foo='bar', baz=23), hello, 'hello.config(...)')
    foo = hello.config('foo')
    is_ok(foo, 'bar', 'foo')
    foo = hello.config().pop('foo')
    is_ok(foo, 'bar', 'removed')
    is_ok(hello.config('foo'), None, 'no foo')
    hello.config(foo='test', bar=23)
    is_deeply_ok(hello.config(), {'baz': 23, 'foo': 'test', 'bar': 23}, 'multiple values')

with subtest('handler'):
    tx = Pyjo.Transaction.HTTP.new()
    hello.handler(tx)
    is_ok(tx.res.body, b'Your Pyjo is working!', 'response')

with subtest('server'):
    import Pyjo.Server

    is_ok(hello.server(Pyjo.Server.new()), None, 'hello.server(...)')

with subtest('start'):
    hello = hello.start()
    with patch.dict(os.environ, {'PYJO_APP_LOADER': '1'}):
        hello.start()
    is_ok(Pyjo.Server.loaded_app, hello, 'kept for the server')
    Pyjo.Server.loaded_app = None

done_testing()
