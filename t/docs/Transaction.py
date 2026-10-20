import Pyjo.DOM
import Pyjo.Message.Request
import Pyjo.Message.Response
import Pyjo.Transaction.HTTP

from Pyjo.Test import *

import contextlib
import io
import re


def output(cb):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        cb()
    return out.getvalue()


with subtest('Synopsis'):
    from Pyjo.Transaction import Transaction

    class MyTransaction(Transaction):
        def client_read(self, chunk): ...
        def client_write(self): ...
        def server_read(self, chunk): ...
        def server_write(self): ...

    isa_ok(MyTransaction(), Transaction, 'subclass')

    import Pyjo.Transaction

    class MyTransaction(Pyjo.Transaction.object):
        def client_read(self, chunk): ...
        def client_write(self): ...
        def server_read(self, chunk): ...
        def server_write(self): ...

    isa_ok(MyTransaction.new(), Pyjo.Transaction.object, 'subclass')

with subtest('connection'):
    tx = Pyjo.Transaction.HTTP.new()
    tx.on('connection', lambda tx, connection: ...)
    ok(tx.has_subscribers('connection'), 'subscribed')

with subtest('finish'):
    tx = Pyjo.Transaction.HTTP.new()
    tx.on('finish', lambda tx: ...)
    ok(tx.has_subscribers('finish'), 'subscribed')

with subtest('new'):
    tx = Pyjo.Transaction.HTTP.new()
    isa_ok(tx, Pyjo.Transaction.object, 'transaction')
    tx = Pyjo.Transaction.HTTP.new(req=Pyjo.Message.Request.new())
    isa_ok(tx.req, Pyjo.Message.Request.object, 'request')

with subtest('original_remote_address'):
    tx = Pyjo.Transaction.HTTP.new()
    address = tx.original_remote_address
    is_ok(address, None, 'default')
    tx.original_remote_address = '127.0.0.1'
    is_ok(tx.original_remote_address, '127.0.0.1', 'set')

with subtest('kept_alive'):
    tx = Pyjo.Transaction.HTTP.new()
    boolean = tx.kept_alive
    is_ok(boolean, None, 'default')
    tx.kept_alive = True
    is_ok(tx.kept_alive, True, 'set')

with subtest('local_address'):
    tx = Pyjo.Transaction.HTTP.new()
    address = tx.local_address
    is_ok(address, None, 'default')
    tx.local_address = '127.0.0.1'
    is_ok(tx.local_address, '127.0.0.1', 'set')

with subtest('local_port'):
    tx = Pyjo.Transaction.HTTP.new()
    port = tx.local_port
    is_ok(port, None, 'default')
    tx.local_port = 8080
    is_ok(tx.local_port, 8080, 'set')

with subtest('remote_port'):
    tx = Pyjo.Transaction.HTTP.new()
    port = tx.remote_port
    is_ok(port, None, 'default')
    tx.remote_port = 8081
    is_ok(tx.remote_port, 8081, 'set')

with subtest('req'):
    tx = Pyjo.Transaction.HTTP.new()
    req = tx.req
    isa_ok(req, Pyjo.Message.Request.object, 'default')
    tx.req = Pyjo.Message.Request.new()
    ok(tx.req is not req, 'set')

    tx.req.parse(
        b'POST /?a=b HTTP/1.1\x0d\x0aHost: localhost\x0d\x0aUser-Agent: Pyjoyment\x0d\x0aCustom-Header: yes\x0d\x0a'
        b'Content-Length: 46\x0d\x0a\x0d\x0a[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]'
    )
    method = tx.req.method
    is_ok(method, 'POST', 'method')
    url = tx.req.url.to_abs()
    is_ok(url, 'http://localhost/?a=b', 'URL')
    info = tx.req.url.to_abs().userinfo
    is_ok(info, None, 'userinfo')
    host = tx.req.url.to_abs().host
    is_ok(host, 'localhost', 'host')
    agent = tx.req.headers.user_agent
    is_ok(agent, 'Pyjoyment', 'agent')
    custom = tx.req.headers.header('Custom-Header')
    is_ok(custom, 'yes', 'custom header')
    data = tx.req.body
    is_ok(len(data), 46, 'body')
    string = tx.req.text
    is_ok(len(string), 46, 'text')
    params = tx.req.params.to_dict()
    is_deeply_ok(params, {'a': 'b'}, 'parameters')
    all = tx.req.uploads()
    is_deeply_ok(all, [], 'uploads')
    value = tx.req.json()
    is_ok(len(value), 14, 'JSON')
    foo = tx.req.json('/13')
    is_ok(foo, 13, 'JSON Pointer')

    tx.req.body = b'<div class="bar">Bar</div>'
    dom = tx.req.dom()
    isa_ok(dom, Pyjo.DOM.object, 'DOM')
    bar = tx.req.dom('div.bar').first().text
    is_ok(bar, 'Bar', 'text')

with subtest('res'):
    tx = Pyjo.Transaction.HTTP.new()
    res = tx.res
    isa_ok(res, Pyjo.Message.Response.object, 'default')
    tx.res = Pyjo.Message.Response.new()
    ok(tx.res is not res, 'set')

    tx.res.parse(
        b'HTTP/1.1 200 OK\x0d\x0aServer: Pyjoyment\x0d\x0aCustom-Header: yes\x0d\x0a'
        b'Content-Length: 23\x0d\x0a\x0d\x0a[{"foo": "bar"}, 1, 2]'
    )
    code = tx.res.code
    is_ok(code, 200, 'code')
    message = tx.res.message
    is_ok(message, 'OK', 'message')
    server = tx.res.headers.server
    is_ok(server, 'Pyjoyment', 'server')
    custom = tx.res.headers.header('Custom-Header')
    is_ok(custom, 'yes', 'custom header')
    data = tx.res.body
    is_ok(data, b'[{"foo": "bar"}, 1, 2]', 'body')
    string = tx.res.text
    is_ok(string, '[{"foo": "bar"}, 1, 2]', 'text')
    value = tx.res.json()
    is_deeply_ok(value, [{'foo': 'bar'}, 1, 2], 'JSON')
    foo = tx.res.json('/0/foo')
    is_ok(foo, 'bar', 'JSON Pointer')

    tx.res.body = b'<div class="bar">Bar</div>'
    dom = tx.res.dom()
    isa_ok(dom, Pyjo.DOM.object, 'DOM')
    bar = tx.res.dom('div.bar').first().text
    is_ok(bar, 'Bar', 'text')

with subtest('client_read'):
    tx = MyTransaction.new()
    throws_ok(lambda: Pyjo.Transaction.object.client_read(tx, b''), NotImplementedError, 'abstract')

with subtest('client_write'):
    tx = MyTransaction.new()
    throws_ok(lambda: Pyjo.Transaction.object.client_write(tx), NotImplementedError, 'abstract')

with subtest('closed'):
    tx = Pyjo.Transaction.HTTP.new()
    finished = []
    tx.on('finish', lambda tx: finished.append(True))
    tx = tx.closed()
    ok(tx.is_finished, 'finished')
    is_deeply_ok(finished, [True], 'finish event')

with subtest('completed'):
    tx = Pyjo.Transaction.HTTP.new()
    tx = tx.completed()
    ok(tx.is_finished, 'finished')

with subtest('connection'):
    tx = Pyjo.Transaction.HTTP.new()
    id = tx.connection
    is_ok(id, None, 'no connection')
    tx.connection = 'abc'
    is_ok(tx.connection, 'abc', 'set')

with subtest('error'):
    tx = Pyjo.Transaction.HTTP.new()
    err = tx.error
    is_ok(err, None, 'no error')

    tx.res.error = {'message': 'Not Found', 'code': 404}
    err = tx.req.error or tx.res.error
    is_deeply_ok(err, {'message': 'Not Found', 'code': 404}, 'longer version')

    def check():
        if err := tx.error:
            if 'code' in err:
                raise Exception(f'{err["code"]} response: {err["message"]}')
            raise Exception(f'Connection error: {err["message"]}')

    throws_ok(check, '404 response: Not Found', 'response error')
    tx = Pyjo.Transaction.HTTP.new()
    tx.res.error = {'message': 'Connection refused'}
    throws_ok(check, 'Connection error: Connection refused', 'connection error')

with subtest('is_finished'):
    tx = Pyjo.Transaction.HTTP.new()
    boolean = tx.is_finished
    is_ok(boolean, False, 'not finished')

with subtest('is_websocket'):
    tx = Pyjo.Transaction.HTTP.new()
    boolean = tx.is_websocket
    is_ok(boolean, False, 'not a WebSocket')

with subtest('remote_address'):
    tx = Pyjo.Transaction.HTTP.new()
    address = tx.remote_address
    is_ok(address, None, 'default')
    tx.remote_address = '127.0.0.1'
    is_ok(tx.remote_address, '127.0.0.1', 'set')
    tx.req.reverse_proxy = True
    tx.req.headers.header('X-Forwarded-For', '192.0.2.2, 192.0.2.1')
    is_ok(tx.remote_address, '192.0.2.1', 'reverse proxy')
    tx.req.trusted_proxies = ['127.0.0.1', '192.0.2.1']
    is_ok(tx.remote_address, '192.0.2.2', 'trusted proxies')

with subtest('result'):
    tx = Pyjo.Transaction.HTTP.new()
    tx.res.parse(b'HTTP/1.1 200 OK\x0d\x0aContent-Length: 2\x0d\x0a\x0d\x0aHi')
    res = tx.result
    isa_ok(res, Pyjo.Message.Response.object, 'response')

    def handle():
        # Fine grained response handling (raises on connection errors)
        res = tx.result
        if res.is_success:
            print(res.body)
        elif res.is_error:
            print(res.message)
        elif res.code == 301:
            print(res.headers.location)
        else:
            print('Whatever...')

    is_ok(output(handle), "b'Hi'\n", 'success')
    tx.res.error = {'message': 'Connection refused'}
    throws_ok(handle, re.compile(r'^Connection refused'), 'connection error')

with subtest('server_read'):
    tx = MyTransaction.new()
    throws_ok(lambda: Pyjo.Transaction.object.server_read(tx, b''), NotImplementedError, 'abstract')

with subtest('server_write'):
    tx = MyTransaction.new()
    throws_ok(lambda: Pyjo.Transaction.object.server_write(tx), NotImplementedError, 'abstract')

done_testing()
