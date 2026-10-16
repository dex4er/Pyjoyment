import Pyjo.UserAgent

from Pyjo.Test import *


with subtest('Synopsis'):
    import Pyjoyment.HelloWorld

    hello = Pyjoyment.HelloWorld.new()
    is_ok(hello.start(), hello, 'started')

with subtest('startup'):
    hello = Pyjoyment.HelloWorld.new()
    hello.startup()
    is_ok(hello.log.level, 'error', 'errors only')
    is_ok(hello.moniker, 'pyjoyment-hello_world', 'moniker')
    ua = Pyjo.UserAgent.new()
    ua.server.app = hello
    for path in ('/', '/foo/bar.txt'):
        tx = ua.get(path)
        is_ok(tx.res.text, 'Your Pyjoyment is working!', f'catch-all route for {path}')

done_testing()
