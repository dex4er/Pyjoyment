import Pyjo.JSON
import Pyjo.JSON.RPC
import Pyjo.Promise
import Pyjo.Test.Pyjo
import Pyjoyment

from Pyjo.Test import *

import re


# Not in Mojolicious: JSON-RPC 2.0, with the examples of the specification


def dispatch(rpc, message, context=None):
    responses = []
    rpc.dispatch_p(message, context).then(lambda response=None: responses.append(response)).wait()
    return responses[0] if responses else None


rpc = Pyjo.JSON.RPC.new()


@rpc.method
def subtract(minuend, subtrahend):
    return minuend - subtrahend


@rpc.method
def update(*values):
    pass


@rpc.method
def sum(*values):
    return values[0] + values[1] + values[2]


@rpc.method('notify_hello')
def hello(value):
    pass


@rpc.method
def get_data():
    return ['hello', 5]


with subtest('Positional parameters'):
    request = {'jsonrpc': '2.0', 'method': 'subtract', 'params': [42, 23], 'id': 1}
    is_deeply_ok(dispatch(rpc, request), {'jsonrpc': '2.0', 'result': 19, 'id': 1}, 'right response')
    request = {'jsonrpc': '2.0', 'method': 'subtract', 'params': [23, 42], 'id': 2}
    is_deeply_ok(dispatch(rpc, request), {'jsonrpc': '2.0', 'result': -19, 'id': 2}, 'right response')

with subtest('Named parameters'):
    request = {'jsonrpc': '2.0', 'method': 'subtract', 'params': {'subtrahend': 23, 'minuend': 42}, 'id': 3}
    is_deeply_ok(dispatch(rpc, request), {'jsonrpc': '2.0', 'result': 19, 'id': 3}, 'right response')
    request = {'jsonrpc': '2.0', 'method': 'subtract', 'params': {'minuend': 42, 'subtrahend': 23}, 'id': 4}
    is_deeply_ok(dispatch(rpc, request), {'jsonrpc': '2.0', 'result': 19, 'id': 4}, 'right response')

with subtest('Notifications'):
    is_ok(dispatch(rpc, {'jsonrpc': '2.0', 'method': 'update', 'params': [1, 2, 3, 4, 5]}), None, 'no response')
    is_ok(dispatch(rpc, {'jsonrpc': '2.0', 'method': 'foobar'}), None, 'no response')
    is_ok(dispatch(rpc, {'jsonrpc': '2.0', 'method': 'subtract', 'params': [1]}), None, 'no response to an error')

with subtest('Method that does not exist'):
    error = {'code': -32601, 'message': 'Method not found'}
    response = dispatch(rpc, {'jsonrpc': '2.0', 'method': 'foobar', 'id': '1'})
    is_deeply_ok(response, {'jsonrpc': '2.0', 'error': error, 'id': '1'}, 'right response')

with subtest('Invalid JSON'):
    error = {'code': -32700, 'message': 'Parse error'}
    response = dispatch(rpc, b'{"jsonrpc": "2.0", "method": "foobar, "params": "bar", "baz]')
    is_deeply_ok(response, {'jsonrpc': '2.0', 'error': error, 'id': None}, 'right response')
    response = dispatch(rpc, '{"jsonrpc": "2.0", "method"')
    is_deeply_ok(response, {'jsonrpc': '2.0', 'error': error, 'id': None}, 'right response for a string')
    response = dispatch(rpc, b'\xff')
    is_deeply_ok(response, {'jsonrpc': '2.0', 'error': error, 'id': None}, 'right response for bytes not of UTF-8')

with subtest('JSON'):
    response = dispatch(rpc, b'{"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 1}')
    is_deeply_ok(response, {'jsonrpc': '2.0', 'result': 19, 'id': 1}, 'right response')
    response = dispatch(rpc, '{"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 1}')
    is_deeply_ok(response, {'jsonrpc': '2.0', 'result': 19, 'id': 1}, 'right response for a string')

with subtest('Invalid Request object'):
    error = {'code': -32600, 'message': 'Invalid Request'}
    response = dispatch(rpc, {'jsonrpc': '2.0', 'method': 1, 'params': 'bar'})
    is_deeply_ok(response, {'jsonrpc': '2.0', 'error': error, 'id': None}, 'right response')
    response = dispatch(rpc, {'jsonrpc': '1.0', 'method': 'subtract', 'params': [42, 23], 'id': 1})
    is_deeply_ok(response, {'jsonrpc': '2.0', 'error': error, 'id': 1}, 'version 1.0 with its id')
    response = dispatch(rpc, {'method': 'subtract', 'params': [42, 23], 'id': 1})
    is_deeply_ok(response, {'jsonrpc': '2.0', 'error': error, 'id': 1}, 'without the version')
    response = dispatch(rpc, {'jsonrpc': '2.0', 'method': 'subtract', 'params': 42, 'id': 1})
    is_deeply_ok(response, {'jsonrpc': '2.0', 'error': error, 'id': 1}, 'params that are not structured')
    response = dispatch(rpc, {'jsonrpc': '2.0', 'method': 'get_data', 'id': {'a': 1}})
    is_deeply_ok(response, {'jsonrpc': '2.0', 'error': error, 'id': None}, 'id that is an object')
    response = dispatch(rpc, {'jsonrpc': '2.0', 'method': 'get_data', 'id': True})
    is_deeply_ok(response, {'jsonrpc': '2.0', 'error': error, 'id': None}, 'id that is a boolean')
    response = dispatch(rpc, {'jsonrpc': '2.0', 'result': 19, 'id': 1})
    is_deeply_ok(response, {'jsonrpc': '2.0', 'error': error, 'id': 1}, 'a response')
    response = dispatch(rpc, 'true')
    is_deeply_ok(response, {'jsonrpc': '2.0', 'error': error, 'id': None}, 'a value')

with subtest('Ids'):
    request = {'jsonrpc': '2.0', 'method': 'get_data', 'id': None}
    is_deeply_ok(dispatch(rpc, request), {'jsonrpc': '2.0', 'result': ['hello', 5], 'id': None}, 'null')
    request = {'jsonrpc': '2.0', 'method': 'get_data', 'id': 1.5}
    is_deeply_ok(dispatch(rpc, request), {'jsonrpc': '2.0', 'result': ['hello', 5], 'id': 1.5}, 'fraction')

with subtest('Batch, invalid JSON'):
    error = {'code': -32700, 'message': 'Parse error'}
    message = b'[{"jsonrpc": "2.0", "method": "sum", "params": [1,2,4], "id": "1"}, {"jsonrpc": "2.0", "method"]'
    is_deeply_ok(dispatch(rpc, message), {'jsonrpc': '2.0', 'error': error, 'id': None}, 'right response')

with subtest('Empty array'):
    error = {'code': -32600, 'message': 'Invalid Request'}
    is_deeply_ok(dispatch(rpc, []), {'jsonrpc': '2.0', 'error': error, 'id': None}, 'right response')

with subtest('Invalid batch, but not empty'):
    error = {'code': -32600, 'message': 'Invalid Request'}
    is_deeply_ok(dispatch(rpc, [1]), [{'jsonrpc': '2.0', 'error': error, 'id': None}], 'right response')

with subtest('Invalid batch'):
    error = {'code': -32600, 'message': 'Invalid Request'}
    response = [{'jsonrpc': '2.0', 'error': error, 'id': None}] * 3
    is_deeply_ok(dispatch(rpc, [1, 2, 3]), response, 'right response')

with subtest('Batch'):
    batch = [
        {'jsonrpc': '2.0', 'method': 'sum', 'params': [1, 2, 4], 'id': '1'},
        {'jsonrpc': '2.0', 'method': 'notify_hello', 'params': [7]},
        {'jsonrpc': '2.0', 'method': 'subtract', 'params': [42, 23], 'id': '2'},
        {'foo': 'boo'},
        {'jsonrpc': '2.0', 'method': 'foo.get', 'params': {'name': 'myself'}, 'id': '5'},
        {'jsonrpc': '2.0', 'method': 'get_data', 'id': '9'},
    ]
    response = [
        {'jsonrpc': '2.0', 'result': 7, 'id': '1'},
        {'jsonrpc': '2.0', 'result': 19, 'id': '2'},
        {'jsonrpc': '2.0', 'error': {'code': -32600, 'message': 'Invalid Request'}, 'id': None},
        {'jsonrpc': '2.0', 'error': {'code': -32601, 'message': 'Method not found'}, 'id': '5'},
        {'jsonrpc': '2.0', 'result': ['hello', 5], 'id': '9'},
    ]
    is_deeply_ok(dispatch(rpc, batch), response, 'right response')

with subtest('Batch of notifications'):
    batch = [
        {'jsonrpc': '2.0', 'method': 'notify_sum', 'params': [1, 2, 4]},
        {'jsonrpc': '2.0', 'method': 'notify_hello', 'params': [7]},
    ]
    is_ok(dispatch(rpc, batch), None, 'no response')

with subtest('Invalid params'):
    response = dispatch(rpc, {'jsonrpc': '2.0', 'method': 'subtract', 'params': [42], 'id': 1})
    is_ok(response['error']['code'], -32602, 'right code')
    is_ok(response['error']['message'], 'Invalid params', 'right message')
    is_ok(response['error']['data'], "missing a required argument: 'subtrahend'", 'right data')
    response = dispatch(rpc, {'jsonrpc': '2.0', 'method': 'subtract', 'params': {'minuend': 42, 'foo': 1}, 'id': 1})
    is_ok(response['error']['code'], -32602, 'right code for an unknown name')
    response = dispatch(rpc, {'jsonrpc': '2.0', 'method': 'get_data', 'params': [1], 'id': 1})
    is_ok(response['error']['code'], -32602, 'right code for too many')

with subtest('Errors of methods'):
    other = Pyjo.JSON.RPC.new()
    exceptions = []
    other.on('exception', lambda rpc, e, context: exceptions.append((e, context)))

    @other.method
    def credit():
        raise Pyjo.JSON.RPC.Error.new(-32000, 'Not enough credit', {'balance': 3})

    @other.method
    def standard():
        raise Pyjo.JSON.RPC.Error.new(Pyjo.JSON.RPC.INVALID_PARAMS)

    @other.method
    def null():
        raise Pyjo.JSON.RPC.Error.new(-32001, 'Null', None)

    @other.method
    def fails():
        raise ValueError('Secret')

    @other.method
    def type_error(value):
        return value + 1

    error = {'code': -32000, 'message': 'Not enough credit', 'data': {'balance': 3}}
    response = dispatch(other, {'jsonrpc': '2.0', 'method': 'credit', 'id': 1})
    is_deeply_ok(response, {'jsonrpc': '2.0', 'error': error, 'id': 1}, 'error of the method')
    error = {'code': -32602, 'message': 'Invalid params'}
    response = dispatch(other, {'jsonrpc': '2.0', 'method': 'standard', 'id': 1})
    is_deeply_ok(response, {'jsonrpc': '2.0', 'error': error, 'id': 1}, 'error of the specification')
    error = {'code': -32001, 'message': 'Null', 'data': None}
    response = dispatch(other, {'jsonrpc': '2.0', 'method': 'null', 'id': 1})
    is_deeply_ok(response, {'jsonrpc': '2.0', 'error': error, 'id': 1}, 'data that is null')
    is_deeply_ok(exceptions, [], 'no exceptions')
    error = {'code': -32603, 'message': 'Internal error'}
    response = dispatch(other, {'jsonrpc': '2.0', 'method': 'fails', 'id': 1}, 'context')
    is_deeply_ok(response, {'jsonrpc': '2.0', 'error': error, 'id': 1}, 'internal error without the message')
    is_ok(len(exceptions), 1, 'one exception')
    isa_ok(exceptions[0][0], ValueError, 'right exception')
    is_ok(exceptions[0][1], 'context', 'right context')
    response = dispatch(other, {'jsonrpc': '2.0', 'method': 'type_error', 'params': ['x'], 'id': 1})
    is_deeply_ok(response, {'jsonrpc': '2.0', 'error': error, 'id': 1}, 'TypeError of the method is internal')
    is_ok(len(exceptions), 2, 'two exceptions')
    is_ok(dispatch(other, {'jsonrpc': '2.0', 'method': 'fails'}), None, 'no response to a notification')
    is_ok(len(exceptions), 3, 'three exceptions')

with subtest('Error'):
    e = Pyjo.JSON.RPC.Error.new(-32000, 'Not enough credit', {'balance': 3})
    is_ok(e.code, -32000, 'right code')
    is_ok(e.message, 'Not enough credit', 'right message')
    is_deeply_ok(e.data, {'balance': 3}, 'right data')
    is_ok(Pyjo.JSON.to_json(e), '{"code":-32000,"data":{"balance":3},"message":"Not enough credit"}', 'right JSON')
    e = Pyjo.JSON.RPC.Error.new()
    is_deeply_ok(e.__json__(), {'code': -32603, 'message': 'Internal error'}, 'internal error')
    e = Pyjo.JSON.RPC.Error.new(-32099)
    is_deeply_ok(e.__json__(), {'code': -32099, 'message': 'Server error'}, 'server error')
    e = Pyjo.JSON.RPC.Error.from_json({'code': -32601, 'message': 'Method not found'})
    is_deeply_ok(e.__json__(), {'code': -32601, 'message': 'Method not found'}, 'from JSON')
    e = Pyjo.JSON.RPC.Error.from_json({'code': -32000, 'message': 'Null', 'data': None})
    is_deeply_ok(e.__json__(), {'code': -32000, 'message': 'Null', 'data': None}, 'from JSON with data')
    e = Pyjo.JSON.RPC.Error.from_json('Oops')
    is_deeply_ok(e.__json__(), {'code': -32603, 'message': 'Invalid error', 'data': 'Oops'}, 'invalid error')
    e = Pyjo.JSON.RPC.Error.from_json({'code': True, 'message': 1})
    is_deeply_ok(e.__json__(), {'code': -32603, 'message': 'Internal error'}, 'invalid code and message')

with subtest('Promises and coroutines'):
    other = Pyjo.JSON.RPC.new()

    @other.method
    def promise(value):
        return Pyjo.Promise.timer(0.01, value)

    @other.method
    def rejected():
        return Pyjo.Promise.timer(0.01).then(lambda: Pyjo.Promise.reject(Pyjo.JSON.RPC.Error.new(-32000, 'Later')))

    @other.method
    def empty():
        return Pyjo.Promise.resolve()

    @other.method
    async def coroutine(value):
        await Pyjo.Promise.timer(0.01)
        return value * 2

    @other.method
    async def failing():
        await Pyjo.Promise.timer(0.01)
        raise ValueError('Secret')

    response = dispatch(other, {'jsonrpc': '2.0', 'method': 'promise', 'params': ['later'], 'id': 1})
    is_deeply_ok(response, {'jsonrpc': '2.0', 'result': 'later', 'id': 1}, 'promise')
    error = {'code': -32000, 'message': 'Later'}
    response = dispatch(other, {'jsonrpc': '2.0', 'method': 'rejected', 'id': 1})
    is_deeply_ok(response, {'jsonrpc': '2.0', 'error': error, 'id': 1}, 'rejected promise')
    response = dispatch(other, {'jsonrpc': '2.0', 'method': 'empty', 'id': 1})
    is_deeply_ok(response, {'jsonrpc': '2.0', 'result': None, 'id': 1}, 'promise without a value')
    response = dispatch(other, {'jsonrpc': '2.0', 'method': 'coroutine', 'params': [21], 'id': 1})
    is_deeply_ok(response, {'jsonrpc': '2.0', 'result': 42, 'id': 1}, 'coroutine')
    error = {'code': -32603, 'message': 'Internal error'}
    response = dispatch(other, {'jsonrpc': '2.0', 'method': 'failing', 'id': 1})
    is_deeply_ok(response, {'jsonrpc': '2.0', 'error': error, 'id': 1}, 'coroutine that fails')
    batch = [
        {'jsonrpc': '2.0', 'method': 'promise', 'params': ['later'], 'id': 1},
        {'jsonrpc': '2.0', 'method': 'coroutine', 'params': [1]},
        {'jsonrpc': '2.0', 'method': 'coroutine', 'params': [2], 'id': 2},
    ]
    response = [{'jsonrpc': '2.0', 'result': 'later', 'id': 1}, {'jsonrpc': '2.0', 'result': 4, 'id': 2}]
    is_deeply_ok(dispatch(other, batch), response, 'batch of promises and coroutines')

with subtest('Schema'):
    other = Pyjo.JSON.RPC.new()

    @other.method(schema=True)
    def weather(city: str, days: int = 3, **options: bool) -> str:
        return f'{city} {days} {sorted(options)}'

    @other.method('schema', schema={'type': 'object', 'properties': {'a': {'type': 'integer', 'minimum': 1}}})
    def given(a=0):
        return a

    @other.method('context', schema=True, context=True)
    def with_context(c, value: int) -> str:
        return f'{c} {value}'

    request = {'jsonrpc': '2.0', 'method': 'weather', 'params': ['Warsaw', 5], 'id': 1}
    is_deeply_ok(dispatch(other, request), {'jsonrpc': '2.0', 'result': 'Warsaw 5 []', 'id': 1}, 'positional')
    request = {'jsonrpc': '2.0', 'method': 'weather', 'params': {'city': 'Warsaw', 'rain': True}, 'id': 1}
    response = {'jsonrpc': '2.0', 'result': "Warsaw 3 ['rain']", 'id': 1}
    is_deeply_ok(dispatch(other, request), response, 'named with the keywords')
    request = {'jsonrpc': '2.0', 'method': 'weather', 'params': ['Warsaw', 'five'], 'id': 1}
    error = {'code': -32602, 'message': 'Invalid params', 'data': '/days: Expected integer - got string.'}
    is_deeply_ok(dispatch(other, request), {'jsonrpc': '2.0', 'error': error, 'id': 1}, 'positional not valid')
    request = {'jsonrpc': '2.0', 'method': 'weather', 'params': {'city': 'Warsaw', 'rain': 'yes'}, 'id': 1}
    error = {'code': -32602, 'message': 'Invalid params', 'data': '/rain: Expected boolean - got string.'}
    is_deeply_ok(dispatch(other, request), {'jsonrpc': '2.0', 'error': error, 'id': 1}, 'keyword not valid')
    request = {'jsonrpc': '2.0', 'method': 'schema', 'params': {'a': 0}, 'id': 1}
    error = {'code': -32602, 'message': 'Invalid params', 'data': '/a: Less than the minimum 1.'}
    is_deeply_ok(dispatch(other, request), {'jsonrpc': '2.0', 'error': error, 'id': 1}, 'schema of its own')
    request = {'jsonrpc': '2.0', 'method': 'schema', 'params': {'a': 2}, 'id': 1}
    is_deeply_ok(dispatch(other, request), {'jsonrpc': '2.0', 'result': 2, 'id': 1}, 'valid with a schema of its own')
    request = {'jsonrpc': '2.0', 'method': 'context', 'params': [7], 'id': 1}
    response = {'jsonrpc': '2.0', 'result': 'ctx 7', 'id': 1}
    is_deeply_ok(dispatch(other, request, 'ctx'), response, 'context before the parameters')
    request = {'jsonrpc': '2.0', 'method': 'context', 'params': ['seven'], 'id': 1}
    error = {'code': -32602, 'message': 'Invalid params', 'data': '/value: Expected integer - got string.'}
    is_deeply_ok(dispatch(other, request, 'ctx'), {'jsonrpc': '2.0', 'error': error, 'id': 1}, 'context not validated')
    is_deeply_ok(other.methods, ['weather', 'schema', 'context'], 'right methods')

with subtest('Methods'):
    other = Pyjo.JSON.RPC.new()
    cb = other.method('add', lambda a, b: a + b)
    is_ok(cb(1, 2), 3, 'callback returned')

    @other.method('math.mul')
    def mul(a, b):
        return a * b

    is_ok(mul(2, 3), 6, 'function decorated')
    is_deeply_ok(other.methods, ['add', 'math.mul'], 'right methods')
    request = {'jsonrpc': '2.0', 'method': 'math.mul', 'params': [6, 7], 'id': 1}
    is_deeply_ok(dispatch(other, request), {'jsonrpc': '2.0', 'result': 42, 'id': 1}, 'dotted name')

with subtest('Client'):
    sent = []

    def send(request):
        sent.append(request)

    client = Pyjo.JSON.RPC.Client.new(send)
    results = []
    client.call_p('subtract', 42, 23).then(lambda value: results.append(('result', value)))
    client.call_p('subtract', minuend=42, subtrahend=23).then(lambda value: results.append(('named', value)))
    client.call_p('foobar').catch(lambda e: results.append(('error', e.code, e.message, e.data)))
    client.call_p('get_data')
    is_ok(client.notify('update', 1, 2), None, 'what send returns')
    request = {'jsonrpc': '2.0', 'method': 'subtract', 'params': [42, 23], 'id': 1}
    is_deeply_ok(sent[0], request, 'positional')
    request = {'jsonrpc': '2.0', 'method': 'subtract', 'params': {'minuend': 42, 'subtrahend': 23}, 'id': 2}
    is_deeply_ok(sent[1], request, 'named')
    is_deeply_ok(sent[2], {'jsonrpc': '2.0', 'method': 'foobar', 'id': 3}, 'without params')
    is_deeply_ok(sent[4], {'jsonrpc': '2.0', 'method': 'update', 'params': [1, 2]}, 'notification')
    ok(client.receive({'jsonrpc': '2.0', 'result': 19, 'id': 1}), 'response received')
    ok(client.receive(b'{"jsonrpc": "2.0", "result": 19, "id": 2}'), 'JSON received')
    ok(not client.receive({'jsonrpc': '2.0', 'result': 19, 'id': 2}), 'response received once')
    ok(not client.receive({'jsonrpc': '2.0', 'method': 'subtract', 'params': [1, 2], 'id': 3}), 'not a request')
    ok(not client.receive(b'{'), 'not JSON')
    batch = [
        {'jsonrpc': '2.0', 'error': {'code': -32601, 'message': 'Method not found', 'data': 'foobar'}, 'id': 3},
        {'jsonrpc': '2.0', 'result': ['hello', 5], 'id': 4},
    ]
    ok(client.receive(batch), 'batch received')
    Pyjo.Promise.timer(0.01).wait()
    is_deeply_ok(
        results,
        [('result', 19), ('named', 19), ('error', -32601, 'Method not found', 'foobar')],
        'promises settled',
    )
    throws_ok(
        lambda: client.notify('subtract', 1, b=2), re.compile(r'positional or named, not both'), 'both kinds of params'
    )
    rejected = []
    client.call_p('subtract', 1, b=2).catch(lambda e: rejected.append(e.message))
    Pyjo.Promise.timer(0.01).wait()
    like_ok(rejected[0], r'positional or named, not both', 'call rejected')
    rejected = []
    Pyjo.JSON.RPC.Client.new().call_p('foo').catch(lambda e: rejected.append(e.message)).wait()
    like_ok(rejected[0], r'No function to send the request', 'no transport')

with subtest('Client and server'):
    client = Pyjo.JSON.RPC.Client.new(lambda request: rpc.dispatch_p(request))
    results = []
    client.call_p('subtract', 42, 23).then(results.append).wait()
    client.call_p('foobar').catch(lambda e: results.append(e.code)).wait()
    is_deeply_ok(results, [19, -32601], 'promise of the response')
    client = Pyjo.JSON.RPC.Client.new(lambda request: {'jsonrpc': '2.0', 'result': 'now', 'id': request['id']})
    client.call_p('anything').then(results.append).wait()
    is_ok(results[-1], 'now', 'the response itself')
    client = Pyjo.JSON.RPC.Client.new(lambda request: Pyjo.Promise.reject(Pyjo.Exception.new('Connection refused')))
    client.call_p('anything').catch(lambda e: results.append(e.message)).wait()
    like_ok(results[-1], r'Connection refused', 'transport rejected')

with subtest('to_action'):
    app = Pyjoyment.new()
    app.log.level = 'error'
    app.log.unsubscribe('message')
    logged = []
    app.log.on('message', lambda log, level, *lines: logged.append((level, lines[-1])))
    server = Pyjo.JSON.RPC.new()

    @server.method('whoami', context=True)
    def whoami(c):
        return c.req.headers.user_agent

    @server.method
    async def later(value):
        await Pyjo.Promise.timer(0.01)
        return value

    @server.method
    def fails():
        raise ValueError('Secret')

    @server.method
    def log():
        pass

    app.routes.post('/rpc').to(cb=server.to_action())
    t = Pyjo.Test.Pyjo.new(app)
    t.post_ok('/rpc', {'User-Agent': 'Test'}, json={'jsonrpc': '2.0', 'method': 'whoami', 'id': 1}).status_is(200)
    t.header_is('Content-Type', 'application/json;charset=UTF-8')
    t.json_is({'jsonrpc': '2.0', 'result': 'Test', 'id': 1})
    t.post_ok('/rpc', json={'jsonrpc': '2.0', 'method': 'later', 'params': ['async'], 'id': 2}).status_is(200)
    t.json_is({'jsonrpc': '2.0', 'result': 'async', 'id': 2})
    batch = [{'jsonrpc': '2.0', 'method': 'later', 'params': [1], 'id': 1}, {'jsonrpc': '2.0', 'method': 'log'}]
    t.post_ok('/rpc', json=batch).status_is(200).json_is([{'jsonrpc': '2.0', 'result': 1, 'id': 1}])
    t.post_ok('/rpc', json={'jsonrpc': '2.0', 'method': 'log'}).status_is(202).content_is('')
    t.post_ok('/rpc', json=[{'jsonrpc': '2.0', 'method': 'log'}]).status_is(202).content_is('')
    t.post_ok('/rpc', json={'jsonrpc': '2.0', 'method': 'foobar', 'id': 3}).status_is(200)
    t.json_is('/error/code', -32601)
    t.post_ok('/rpc', b'{"jsonrpc": "2.0", "method"').status_is(400).json_is('/error/code', -32700)
    t.post_ok('/rpc').status_is(400).json_is('/error/code', -32700)
    t.post_ok('/rpc', json={'jsonrpc': '2.0', 'method': 1}).status_is(400).json_is('/error/code', -32600)
    t.post_ok('/rpc', json=[]).status_is(400).json_is('/error/code', -32600)
    t.post_ok('/rpc', json=[1]).status_is(200).json_is('/0/error/code', -32600)
    is_deeply_ok(logged, [], 'nothing logged')
    t.post_ok('/rpc', json={'jsonrpc': '2.0', 'method': 'fails', 'id': 4}).status_is(200)
    t.json_is({'jsonrpc': '2.0', 'error': {'code': -32603, 'message': 'Internal error'}, 'id': 4})
    t.content_unlike(r'Secret')
    is_ok(len(logged), 1, 'exception logged')
    is_ok(logged[0][0], 'error', 'right level')
    like_ok(str(logged[0][1]), r'^Secret', 'right message')

    # A client of the server, through the user agent
    client = Pyjo.JSON.RPC.Client.new(lambda request: t.ua.post_p('/rpc', json=request).then(lambda tx: tx.res.json()))
    results = []
    client.call_p('later', 'client').then(results.append).wait()
    client.call_p('foobar').catch(lambda e: results.append(e.code)).wait()
    is_deeply_ok(results, ['client', -32601], 'client through HTTP')
    t.ua.close()

done_testing()
