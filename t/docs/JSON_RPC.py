import Pyjo.IOLoop
import Pyjo.IOLoop.ChildProcess
import Pyjo.IOLoop.Messages
import Pyjo.Promise
import Pyjo.Test.Pyjo
import Pyjoyment

from Pyjo.File import curfile
from Pyjo.Test import *

# The examples have a route of an application of Pyjoyment.Lite, which the user agent of the test requests
from Pyjoyment.Lite import app, post, websocket

import contextlib
import io
import os
import re
import sys


app.log.level = 'fatal'


def output():
    return contextlib.redirect_stdout(io.StringIO())


t = Pyjo.Test.Pyjo.new()
ua = t.ua

with subtest('Synopsis'):
    from Pyjo.JSON.RPC import RPC

    rpc = RPC()

    @rpc.method
    def subtract(minuend: int, subtrahend: int) -> int:
        """Subtract two numbers."""
        return minuend - subtrahend

    with output() as stdout:
        rpc.dispatch_p({'jsonrpc': '2.0', 'method': 'subtract', 'params': [42, 23], 'id': 1}).then(print).wait()
    is_ok(stdout.getvalue(), "{'jsonrpc': '2.0', 'result': 19, 'id': 1}\n", 'response')

    # Or import the module, as in Google Python Style Guide

    import Pyjo.JSON.RPC

    rpc = Pyjo.JSON.RPC.new()
    rpc.method('subtract', lambda minuend, subtrahend: minuend - subtrahend)

    # A route of an application of Pyjoyment.Lite
    post('/rpc', rpc.to_action())

    # A client, which sends its requests with a user agent
    client = Pyjo.JSON.RPC.Client.new(lambda request: ua.post_p('/rpc', json=request).then(lambda tx: tx.res.json()))
    with output() as stdout:
        client.call_p('subtract', 42, 23).then(print).wait()
    is_ok(stdout.getvalue(), '19\n', 'client')

with subtest('Description'):
    rpc = Pyjo.JSON.RPC.new()

    @rpc.method('subtract', schema=True)
    def subtract(minuend: int, subtrahend: int) -> int:
        return minuend - subtrahend

    with output() as stdout:
        rpc.dispatch_p({'jsonrpc': '2.0', 'method': 'subtract', 'params': [42, 'x'], 'id': 2}).then(print).wait()
    response = {
        'jsonrpc': '2.0',
        'error': {'code': -32602, 'message': 'Invalid params', 'data': '/subtrahend: Expected integer - got string.'},
        'id': 2,
    }
    is_ok(stdout.getvalue(), f'{response}\n', 'invalid params')

with subtest('Error'):

    def credit():
        raise Pyjo.JSON.RPC.Error.new(-32000, 'Not enough credit', {'balance': 3})

    throws_ok(credit, Pyjo.JSON.RPC.Error, 'raise')

with subtest('Error.new'):
    e = Pyjo.JSON.RPC.Error.new(-32000, 'Not enough credit')
    is_deeply_ok(e.__json__(), {'code': -32000, 'message': 'Not enough credit'}, 'e')
    e = Pyjo.JSON.RPC.Error.new(-32000, 'Not enough credit', {'balance': 3})
    is_deeply_ok(e.__json__(), {'code': -32000, 'message': 'Not enough credit', 'data': {'balance': 3}}, 'e')
    e = Pyjo.JSON.RPC.Error.new(Pyjo.JSON.RPC.INVALID_PARAMS)
    is_deeply_ok(e.__json__(), {'code': -32602, 'message': 'Invalid params'}, 'e')

with subtest('Error.code'):
    code = e.code
    is_ok(code, -32602, 'code')

with subtest('Error.data'):
    data = e.data
    is_ok(data, None, 'data')

with subtest('Error.__json__'):
    error = e.__json__()
    is_deeply_ok(error, {'code': -32602, 'message': 'Invalid params'}, 'error')

with subtest('Error.from_json'):
    e = Pyjo.JSON.RPC.Error.from_json({'code': -32601, 'message': 'Method not found'})
    isa_ok(e, Pyjo.JSON.RPC.Error, 'e')
    is_ok(e.code, -32601, 'code')

with subtest('exception'):
    rpc = Pyjo.JSON.RPC.new()
    got = []

    @rpc.on('exception')
    def exception(rpc, e, context):
        got.append((e, context))

    rpc.method('fails', lambda: 1 / 0)
    rpc.dispatch_p({'jsonrpc': '2.0', 'method': 'fails', 'id': 1}, 'context').wait()
    isa_ok(got[0][0], ZeroDivisionError, 'e')
    is_ok(got[0][1], 'context', 'context')

    rpc.on('exception', lambda rpc, e, context: print(f'Failed: {e}'))
    with output() as stdout:
        rpc.dispatch_p({'jsonrpc': '2.0', 'method': 'fails', 'id': 1}).wait()
    is_ok(stdout.getvalue(), 'Failed: division by zero\n', 'printed')

with subtest('new'):
    rpc = Pyjo.JSON.RPC.new()
    isa_ok(rpc, Pyjo.JSON.RPC.object, 'rpc')

with subtest('dispatch_p'):
    rpc.method('subtract', lambda minuend, subtrahend: minuend - subtrahend)
    rpc.method('whoami', lambda c: c, context=True)
    request = {'jsonrpc': '2.0', 'method': 'whoami', 'id': 1}
    response = {'jsonrpc': '2.0', 'result': 19, 'id': 1}
    got = []
    promise = rpc.dispatch_p({'jsonrpc': '2.0', 'method': 'subtract', 'params': [42, 23], 'id': 1})
    promise.then(got.append).wait()
    promise = rpc.dispatch_p(b'{"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 1}')
    promise.then(got.append).wait()
    c = 'controller'
    promise = rpc.dispatch_p(request, context=c)
    promise.then(got.append).wait()
    is_deeply_ok(got, [response, response, {'jsonrpc': '2.0', 'result': 'controller', 'id': 1}], 'promise')

    with output() as stdout:
        rpc.dispatch_p({'jsonrpc': '2.0', 'method': 'foobar', 'id': 1}).then(print).wait()
    response = {'jsonrpc': '2.0', 'error': {'code': -32601, 'message': 'Method not found'}, 'id': 1}
    is_ok(stdout.getvalue(), f'{response}\n', 'method not found')

with subtest('method'):
    rpc = Pyjo.JSON.RPC.new()

    def subtract(minuend: int, subtrahend: int) -> int:
        return minuend - subtrahend

    cb = rpc.method('subtract', lambda minuend, subtrahend: minuend - subtrahend)
    is_ok(cb(42, 23), 19, 'cb')
    cb = rpc.method('whoami', lambda c: c.req.headers.user_agent, context=True)
    cb = rpc.method('subtract', subtract, schema=True)
    is_ok(cb, subtract, 'cb')
    cb = rpc.method('subtract', subtract, schema={'type': 'object'})
    is_ok(cb, subtract, 'cb')

    rpc = Pyjo.JSON.RPC.new()

    @rpc.method
    def subtract(minuend: int, subtrahend: int) -> int:
        return minuend - subtrahend

    @rpc.method('math.add', schema=True)
    def add(a: int, b: int) -> int:
        return a + b

    is_deeply_ok(rpc.methods, ['subtract', 'math.add'], 'decorated')
    got = []
    rpc.dispatch_p({'jsonrpc': '2.0', 'method': 'math.add', 'params': [1, 'x'], 'id': 1}).then(got.append).wait()
    is_ok(got[0]['error']['data'], '/b: Expected integer - got string.', 'schema of the type hints')

with subtest('methods'):
    names = rpc.methods
    is_deeply_ok(names, ['subtract', 'math.add'], 'names')

with subtest('serve'):
    if os.name != 'nt':
        # Standard input and output, whose method asks the client, in a process of its own, which the test calls
        code = """
import Pyjo.IOLoop.Messages, Pyjo.IOLoop.Stdio, Pyjo.JSON.RPC

rpc = Pyjo.JSON.RPC.new()

@rpc.method(context=True)
def greet(client, name):
    return client.call_p('confirm', f'Greet {name}?').then(lambda yes: f'Hello, {name}!' if yes else 'Bye')

messages = Pyjo.IOLoop.Messages.new(Pyjo.IOLoop.Stdio.new())
rpc.serve(messages)
messages.start()

messages.on('close', lambda messages: messages.stream.reactor.stop())
messages.stream.reactor.start()
"""
        env = {
            **os.environ,
            'PYTHONPATH': os.pathsep.join([curfile().dirname().dirname().dirname().to_str(), *sys.path]),
        }
        child = Pyjo.IOLoop.ChildProcess.new().spawn([sys.executable, '-c', code], env=env)
        peer = Pyjo.JSON.RPC.new()
        questions = []
        peer.method('confirm', lambda question: (questions.append(question), True)[1])
        messages = Pyjo.IOLoop.Messages.new(child.stdout, output=child.stdin)
        client = peer.serve(messages)
        got = []
        client.call_p('greet', 'Pyjo').then(got.append).lastly(messages.close_gracefully)
        child.on('close', lambda child, code, signal: Pyjo.IOLoop.stop())
        timer = Pyjo.IOLoop.timer(10, lambda loop: Pyjo.IOLoop.stop())
        Pyjo.IOLoop.start()
        Pyjo.IOLoop.remove(timer)
        is_deeply_ok(questions, ['Greet Pyjo?'], 'the client asked')
        is_deeply_ok(got, ['Hello, Pyjo!'], 'result')
        is_ok(child.exit_code, 0, 'ended with its input')

    # A WebSocket of Pyjoyment.Lite
    websocket('/rpc', lambda c: rpc.serve(c))

    t.websocket_ok('/rpc').send_ok({'json': {'jsonrpc': '2.0', 'method': 'subtract', 'params': [42, 23], 'id': 1}})
    t.message_ok().json_message_is({'jsonrpc': '2.0', 'result': 19, 'id': 1}).finish_ok()

with subtest('to_action'):
    action = rpc.to_action()
    ok(callable(action), 'action')

    # Pyjoyment.Lite
    post('/math', rpc.to_action())

    # Pyjoyment
    other = Pyjoyment.new()
    other.log.level = 'fatal'
    other.routes.post('/rpc').to(cb=rpc.to_action())

    t.post_ok('/math', json={'jsonrpc': '2.0', 'method': 'math.add', 'params': [1, 2], 'id': 1}).status_is(200)
    t.json_is({'jsonrpc': '2.0', 'result': 3, 'id': 1})
    other_t = Pyjo.Test.Pyjo.new(other)
    other_t.post_ok('/rpc', json={'jsonrpc': '2.0', 'method': 'subtract', 'params': [3, 2], 'id': 1}).status_is(200)
    other_t.json_is({'jsonrpc': '2.0', 'result': 1, 'id': 1})
    other_t.ua.close()

with subtest('Client'):
    # HTTP, whose response comes back from the request
    url = '/rpc'
    client = Pyjo.JSON.RPC.Client.new(lambda request: ua.post_p(url, json=request).then(lambda tx: tx.res.json()))
    got = []
    client.call_p('subtract', 42, 23).then(got.append).wait()
    is_deeply_ok(got, [19], 'HTTP')

    # The server of the WebSocket, which answers its messages
    @websocket('/ws')
    def ws_rpc(c):
        def respond(c, message):
            rpc.dispatch_p(message).then(lambda response=None: response and c.send({'json': response}))

        c.on('json', respond)

    def connected(ws):
        # A WebSocket, whose responses come back on their own
        client = Pyjo.JSON.RPC.Client.new(lambda request: ws.send({'json': request}))
        ws.on('json', lambda ws, message: client.receive(message))

        return client.call_p('subtract', 42, 23).then(got.append).lastly(ws.finish)

    got = []
    ua.websocket_p('/ws').then(connected).wait()
    is_deeply_ok(got, [19], 'WebSocket')

with subtest('Client.new'):
    client = Pyjo.JSON.RPC.Client.new()
    is_ok(client.send, None, 'client')

    def send(request):
        pass

    client = Pyjo.JSON.RPC.Client.new(send)
    is_ok(client.send, send, 'client')

with subtest('Client.send'):
    send = client.send
    client.send = lambda request: ...
    ok(callable(client.send), 'send')

with subtest('Client.call_p'):
    rpc.method('subtract', lambda minuend, subtrahend: minuend - subtrahend)
    client = Pyjo.JSON.RPC.Client.new(rpc.dispatch_p)
    got = []
    promise = client.call_p('subtract', 42, 23)
    promise.then(got.append).wait()
    promise = client.call_p('subtract', minuend=42, subtrahend=23)
    promise.then(got.append).wait()
    is_deeply_ok(got, [19, 19], 'promise')

    with output() as stdout:
        client.call_p('subtract', 42, 23).then(print).catch(lambda e: print(f'{e.code}: {e.message}')).wait()
        client.call_p('subtract', 42).then(print).catch(lambda e: print(f'{e.code}: {e.message}')).wait()
    is_ok(stdout.getvalue(), '19\n-32602: Invalid params\n', 'printed')

with subtest('Client.fail'):
    client = Pyjo.JSON.RPC.Client.new(lambda request: None)
    got = []
    client.call_p('subtract', 42, 23).catch(lambda e: got.append(str(e)))
    client.fail(Pyjo.Exception.new('Connection closed'))
    Pyjo.IOLoop.one_tick()
    like_ok(got[0], r'^Connection closed', 'rejected')

with subtest('Client.notify'):
    sent = []
    client = Pyjo.JSON.RPC.Client.new(sent.append)
    client.notify('update', 1, 2, 3)
    client.notify('update', values=[1, 2, 3])
    is_deeply_ok(
        sent,
        [
            {'jsonrpc': '2.0', 'method': 'update', 'params': [1, 2, 3]},
            {'jsonrpc': '2.0', 'method': 'update', 'params': {'values': [1, 2, 3]}},
        ],
        'notifications',
    )

with subtest('Client.receive'):
    client.call_p('subtract', 42, 23)
    client.call_p('subtract', 42, 23)
    boolean = client.receive({'jsonrpc': '2.0', 'result': 19, 'id': 1})
    ok(boolean, 'boolean')
    boolean = client.receive(b'{"jsonrpc": "2.0", "result": 19, "id": 2}')
    ok(boolean, 'boolean')
    ok(not client.receive({'jsonrpc': '2.0', 'method': 'update'}), 'a request goes elsewhere')

with subtest('Constants'):
    is_deeply_ok(
        [
            Pyjo.JSON.RPC.PARSE_ERROR,
            Pyjo.JSON.RPC.INVALID_REQUEST,
            Pyjo.JSON.RPC.METHOD_NOT_FOUND,
            Pyjo.JSON.RPC.INVALID_PARAMS,
            Pyjo.JSON.RPC.INTERNAL_ERROR,
        ],
        [-32700, -32600, -32601, -32602, -32603],
        'codes',
    )
    like_ok(Pyjo.JSON.RPC.MESSAGES[-32601], re.compile(r'^Method not found$'), 'message')

t.ua.close()

done_testing()
