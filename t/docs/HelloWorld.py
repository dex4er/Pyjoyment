from Pyjo.Test import *


with subtest('Synopsis'):
    from Pyjo.HelloWorld import HelloWorld

    hello = HelloWorld()
    is_ok(hello.start(), hello, 'hello.start()')

    # Or import the module, as in Google Python Style Guide
    import Pyjo.HelloWorld

    hello = Pyjo.HelloWorld.new()
    is_ok(hello.start(), hello, 'hello.start()')

with subtest('new'):
    import Pyjo.Log

    hello = Pyjo.HelloWorld.new()
    is_ok(hello.log.level, 'error', 'hello')
    hello = Pyjo.HelloWorld.new(log=Pyjo.Log.new())
    is_ok(hello.log.level, 'trace', 'log')

with subtest('handler'):
    import Pyjo.Transaction.HTTP

    tx = Pyjo.Transaction.HTTP.new()
    hello.handler(tx)
    is_ok(tx.res.body, b'Your Pyjo is working!', 'response')

done_testing()
