import Pyjo.UserAgent

from Pyjo.Test import *

import contextlib
import io
import os


with subtest('Synopsis'):
    from Pyjoyment.HelloWorld import HelloWorld

    hello = HelloWorld()
    os.environ['PYJO_HARNESS_ACTIVE'] = '1'
    is_ok(hello.start(), True, 'started, without the list of the commands')

    # Or import the module, as in Google Python Style Guide

    import Pyjoyment.HelloWorld

    hello = Pyjoyment.HelloWorld.new()
    os.environ['PYJO_HARNESS_ACTIVE'] = '1'
    is_ok(hello.start(), True, 'started, without the list of the commands')
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        hello.start('routes')
    like_ok(buffer.getvalue(), r'/\*whatever', 'command')

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
