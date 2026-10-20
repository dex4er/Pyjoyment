import Pyjo.Exception
import Pyjo.File
import Pyjo.IOLoop
import Pyjo.Server.Daemon
import Pyjoyment

from Pyjo.Test import *
from Pyjo.Util import url_escape

import atexit
import os
import re
import signal
import socket
import struct
import subprocess
import sys
import tempfile


# Not in Mojolicious: FastCGI in the listen locations of Pyjo.Server.Daemon, which Mojolicious has no server for; the
# client of the test writes the records of the specification of FastCGI 1.0 itself

BEGIN_REQUEST = 1
ABORT_REQUEST = 2
END_REQUEST = 3
PARAMS = 4
STDIN = 5
STDOUT = 6
STDERR = 7
DATA = 8
GET_VALUES = 9
GET_VALUES_RESULT = 10
UNKNOWN_TYPE = 11

RESPONDER = 1
AUTHORIZER = 2

KEEP_CONN = 1

REQUEST_COMPLETE = 0
CANT_MPX_CONN = 1
UNKNOWN_ROLE = 3


def record(type, id, content=b''):
    padding = -len(content) % 8
    return struct.pack('>BBHHBx', 1, type, id, len(content), padding) + content + b'\0' * padding


def length(value):
    return struct.pack('>B', len(value)) if len(value) < 128 else struct.pack('>I', len(value) | 0x80000000)


def pairs(params):
    data = b''
    for name, value in params.items():
        if value is None:
            continue
        name, value = name.encode('latin-1'), value.encode('latin-1') if isinstance(value, str) else value
        data += length(name) + length(value) + name + value
    return data


def parse_pairs(data):
    params = {}
    while len(data):
        lengths = []
        for _ in range(2):
            if data[0] < 128:
                lengths.append(data[0])
                data = data[1:]
            else:
                lengths.append(struct.unpack('>I', data[:4])[0] & 0x7FFFFFFF)
                data = data[4:]
        name, value = data[: lengths[0]], data[lengths[0] : lengths[0] + lengths[1]]
        params[name.decode()] = value.decode()
        data = data[lengths[0] + lengths[1] :]
    return params


def stream(type, id, data, size=65535):
    # A stream of records, which ends with an empty one
    return b''.join(record(type, id, data[i : i + size]) for i in range(0, len(data), size)) + record(type, id)


def request(id=1, params=None, body=b'', keep=False, role=RESPONDER, method='GET', path='/'):
    env = {
        'GATEWAY_INTERFACE': 'CGI/1.1',
        'REQUEST_METHOD': method,
        'SCRIPT_NAME': '',
        'PATH_INFO': path,
        'QUERY_STRING': '',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'SERVER_ADDR': '127.0.0.1',
        'SERVER_PORT': '8080',
        'REMOTE_ADDR': '192.0.2.1',
        'REMOTE_PORT': '54321',
        'HTTP_HOST': 'example.com',
        **({'CONTENT_LENGTH': str(len(body))} if body else {}),
        **(params or {}),
    }
    env = {name: value for name, value in env.items() if value is not None}
    begin = record(BEGIN_REQUEST, id, struct.pack('>HB5x', role, KEEP_CONN if keep else 0))
    return begin + stream(PARAMS, id, pairs(env)) + stream(STDIN, id, body)


class Client:
    # A connection to the server, on the event loop that the server runs on
    def __init__(self, **options):
        self.buffer = b''
        self.closed = False
        self.stream = None

        @Pyjo.IOLoop.client(**options)
        def connected(loop, err, stream):
            if err:
                raise Pyjo.Exception.new(err)
            self.stream = stream
            stream.on('read', lambda stream, chunk: setattr(self, 'buffer', self.buffer + chunk))
            stream.on('close', lambda stream: setattr(self, 'closed', True))

        self.wait(lambda: self.stream is not None)

    def wait(self, done, timeout=10):
        # The event loop runs until the condition is true or the time is up
        interval = Pyjo.IOLoop.recurring(0.01, lambda loop: None)
        try:
            for _ in range(int(timeout / 0.01)):
                if done():
                    return True
                Pyjo.IOLoop.one_tick()
            return bool(done())
        finally:
            Pyjo.IOLoop.remove(interval)

    def send(self, data):
        self.stream.write(data)
        return self

    def records(self):
        records, data = [], self.buffer
        while len(data) >= 8:
            _, type, id, size, padding = struct.unpack('>BBHHBx', data[:8])
            if len(data) < 8 + size + padding:
                break
            records.append((type, id, data[8 : 8 + size]))
            data = data[8 + size + padding :]
        return records

    def end(self, id=1):
        # The output and the end of a request, once the server has ended it
        self.wait(lambda: any(type == END_REQUEST and rid == id for type, rid, _ in self.records()))
        stdout, stderr, end = b'', b'', None
        for type, rid, content in self.records():
            if rid != id:
                continue
            if type == STDOUT:
                stdout += content
            elif type == STDERR:
                stderr += content
            elif type == END_REQUEST:
                end = struct.unpack('>IB3x', content)
        return stdout, stderr, end

    def response(self, id=1):
        stdout, _, end = self.end(id)
        head, _, body = stdout.partition(b'\r\n\r\n')
        lines = head.decode('latin-1').split('\r\n')
        headers = dict(line.split(': ', 1) for line in lines)
        return headers, body, end

    def close(self):
        if self.stream is not None:
            self.stream.close()


app = Pyjoyment.new()
app.log.level = 'fatal'
r = app.routes


@r.any('/hello')
def hello(c):
    c.render(
        json={
            'method': c.req.method,
            'path': c.req.url.path.to_str(),
            'query': c.req.url.query.to_str(),
            'url': c.req.url.to_abs().to_str(),
            'base': c.req.url.base.to_str(),
            'remote': [c.tx.remote_address, c.tx.remote_port],
            'local': [c.tx.local_address, c.tx.local_port],
            'agent': c.req.headers.user_agent,
        }
    )


@r.post('/upload')
def upload(c):
    c.render(json={'length': len(c.req.body), 'type': c.req.headers.content_type, 'name': c.param('name')})


@r.get('/stream')
def streaming(c):
    c.write_chunk(b'Hello ')
    Pyjo.IOLoop.timer(0.1, lambda loop: c.write_chunk(b'FastCGI!', lambda c: c.finish()))


finished = []


@r.get('/delay')
def delay(c):
    c.on('finish', lambda c: finished.append(c.req.url.path.to_str()))
    Pyjo.IOLoop.timer(1, lambda loop: c.render(text='Delayed'))


r.get('/big').to(cb=lambda c: c.render(data=b'x' * 200000))
r.get('/empty').to(cb=lambda c: c.rendered(204))
r.get('/♥').to(text='Heart')
r.get('/link').to(cb=lambda c: c.render(text=c.url_for('link').to_abs().to_str()), name='link')

daemon = Pyjo.Server.Daemon.new(app=app, listen=['fcgi://127.0.0.1'], silent=True).start()
port = daemon.ports()[0]

with subtest('Simple request'):
    client = Client(address='127.0.0.1', port=port)
    client.send(request(params={'QUERY_STRING': 'a=b', 'HTTP_USER_AGENT': 'Test'}, path='/hello'))
    headers, body, end = client.response()
    is_ok(headers['Status'], '200 OK', 'status')
    is_ok(headers['Content-Type'], 'application/json;charset=UTF-8', 'content type')
    is_ok(headers['Content-Length'], str(len(body)), 'content length')
    ok('Server' in headers, 'server')
    ok('Connection' not in headers, 'no hop-by-hop header')
    like_ok(body, re.compile(rb'"method":"GET"'), 'method')
    like_ok(body, re.compile(rb'"path":"\\/hello"'), 'path')
    like_ok(body, re.compile(rb'"query":"a=b"'), 'query')
    like_ok(body, re.compile(rb'"url":"http:\\/\\/example\.com\\/hello\?a=b"'), 'absolute URL')
    like_ok(body, re.compile(rb'"remote":\["192\.0\.2\.1",54321\]'), 'remote address')
    like_ok(body, re.compile(rb'"local":\["127\.0\.0\.1",8080\]'), 'local address')
    like_ok(body, re.compile(rb'"agent":"Test"'), 'header')
    is_ok(end, (0, REQUEST_COMPLETE), 'request complete')
    ok(client.wait(lambda: client.closed), 'closed without FCGI_KEEP_CONN')

with subtest('Keep-alive connection'):
    client = Client(address='127.0.0.1', port=port)
    client.send(request(id=1, keep=True, path='/hello', method='POST'))
    headers, body, end = client.response(1)
    like_ok(body, re.compile(rb'"method":"POST"'), 'first request')
    client.send(request(id=2, keep=True, path='/hello', params={'QUERY_STRING': 'second=1'}))
    headers, body, end = client.response(2)
    like_ok(body, re.compile(rb'"query":"second=1"'), 'second request')
    is_ok(end, (0, REQUEST_COMPLETE), 'request complete')
    ok(not client.wait(lambda: client.closed, 0.3), 'still open')
    client.send(request(id=3, path='/hello'))
    headers, body, end = client.response(3)
    is_ok(headers['Status'], '200 OK', 'last request')
    ok(client.wait(lambda: client.closed), 'closed after the last request')

with subtest('Request body'):
    client = Client(address='127.0.0.1', port=port)
    body = b'name=' + b'x' * 150000
    params = {'CONTENT_TYPE': 'application/x-www-form-urlencoded'}
    client.send(request(method='POST', path='/upload', body=body, params=params))
    headers, body, end = client.response()
    is_ok(headers['Status'], '200 OK', 'status')
    like_ok(body, re.compile(rb'"length":150005'), 'whole body in several records')
    like_ok(body, re.compile(rb'"name":"x{150000}"'), 'form')

    # The web server removes the chunked framing of a request and has no length for it
    client = Client(address='127.0.0.1', port=port)
    params = {'CONTENT_TYPE': 'text/plain', 'CONTENT_LENGTH': None, 'HTTP_TRANSFER_ENCODING': 'chunked'}
    data = record(BEGIN_REQUEST, 1, struct.pack('>HB5x', RESPONDER, 0))
    data += stream(PARAMS, 1, pairs({'REQUEST_METHOD': 'POST', 'PATH_INFO': '/upload', **params}))
    data += record(STDIN, 1, b'Hello ') + record(STDIN, 1, b'World!') + record(STDIN, 1)
    client.send(data)
    headers, body, end = client.response()
    like_ok(body, re.compile(rb'"length":12'), 'body without length')
    like_ok(body, re.compile(rb'"type":"text\\/plain"'), 'content type')

with subtest('Streaming response'):
    client = Client(address='127.0.0.1', port=port)
    client.send(request(path='/stream'))
    headers, body, end = client.response()
    is_ok(headers['Status'], '200 OK', 'status')
    ok('Transfer-Encoding' not in headers, 'no chunked framing')
    is_ok(body, b'Hello FastCGI!', 'body')
    is_ok(end, (0, REQUEST_COMPLETE), 'request complete')

with subtest('Large response'):
    client = Client(address='127.0.0.1', port=port)
    client.send(request(path='/big'))
    headers, body, end = client.response()
    is_ok(len(body), 200000, 'whole body')
    stdout = [content for type, _, content in client.records() if type == STDOUT]
    ok(all(len(content) <= 65535 for content in stdout), 'records of 64KiB at most')
    is_ok(stdout[-1], b'', 'empty record at the end')

with subtest('Empty responses'):
    client = Client(address='127.0.0.1', port=port)
    client.send(request(id=1, keep=True, path='/empty'))
    headers, body, end = client.response(1)
    is_ok(headers['Status'], '204 No Content', 'status')
    is_ok(body, b'', 'no body')
    client.send(request(id=2, method='HEAD', path='/hello'))
    headers, body, end = client.response(2)
    is_ok(headers['Status'], '200 OK', 'status')
    ok(int(headers['Content-Length']) > 0, 'content length')
    is_ok(body, b'', 'no body')

with subtest('Paths'):
    client = Client(address='127.0.0.1', port=port)
    client.send(request(id=1, keep=True, path='/♥'.encode().decode('latin-1')))
    headers, body, end = client.response(1)
    is_ok(body, b'Heart', 'path of UTF-8 bytes')

    # The whole path in SCRIPT_NAME, as nginx with fastcgi_params and Caddy send it
    client.send(request(id=2, keep=True, params={'SCRIPT_NAME': '/hello', 'PATH_INFO': None}))
    headers, body, end = client.response(2)
    like_ok(body, re.compile(rb'"path":"\\/hello"'), 'path in SCRIPT_NAME')
    like_ok(body, re.compile(rb'"base":"http:\\/\\/example\.com"'), 'no base path')

    client.send(request(id=3, keep=True, params={'SCRIPT_NAME': '/myapp', 'PATH_INFO': '/link'}))
    headers, body, end = client.response(3)
    is_ok(body, b'http://example.com/myapp/link', 'base path')

    client.send(request(id=4, params={'HTTPS': 'on', 'SERVER_PORT': '443'}, path='/link'))
    headers, body, end = client.response(4)
    is_ok(body, b'https://example.com/link', 'HTTPS')

with subtest('Management records'):
    client = Client(address='127.0.0.1', port=port)
    query = pairs({'FCGI_MAX_CONNS': '', 'FCGI_MAX_REQS': '', 'FCGI_MPXS_CONNS': '', 'UNKNOWN': ''})
    client.send(record(GET_VALUES, 0, query))
    client.wait(lambda: len(client.records()))
    type, id, content = client.records()[0]
    is_ok(type, GET_VALUES_RESULT, 'result')
    is_ok(id, 0, 'management record')
    values = parse_pairs(content)
    is_ok(values['FCGI_MPXS_CONNS'], '0', 'no multiplexing')
    like_ok(values['FCGI_MAX_CONNS'], re.compile(r'^\d+$'), 'maximum connections')
    is_ok(values['FCGI_MAX_REQS'], values['FCGI_MAX_CONNS'], 'maximum requests')
    ok('UNKNOWN' not in values, 'unknown variable left out')

    client.send(record(99, 0, b'?'))
    client.wait(lambda: len(client.records()) > 1)
    type, id, content = client.records()[1]
    is_ok(type, UNKNOWN_TYPE, 'unknown type')
    is_ok(content, struct.pack('>B7x', 99), 'type')
    ok(not client.closed, 'still open')
    client.close()

with subtest('Unsupported requests'):
    client = Client(address='127.0.0.1', port=port)
    client.send(request(id=1, keep=True, role=AUTHORIZER))
    stdout, stderr, end = client.end(1)
    is_ok(end, (0, UNKNOWN_ROLE), 'unknown role')
    is_ok(stdout, b'', 'no output')

    # A second request on the connection while the first one is active
    client.send(request(id=2, keep=True, path='/delay') + request(id=3, keep=True, path='/hello'))
    stdout, stderr, end = client.end(3)
    is_ok(end, (0, CANT_MPX_CONN), 'no multiplexing')
    headers, body, end = client.response(2)
    is_ok(body, b'Delayed', 'first request answered')
    client.close()

with subtest('Aborted request'):
    client = Client(address='127.0.0.1', port=port)
    finished.clear()
    client.send(request(id=1, keep=True, path='/delay'))
    client.wait(lambda: False, 0.2)
    client.send(record(ABORT_REQUEST, 1))
    stdout, stderr, end = client.end(1)
    is_ok(end, (0, REQUEST_COMPLETE), 'ended')
    is_ok(stdout, b'', 'no response')
    is_deeply_ok(finished, ['/delay'], 'transaction finished')
    client.send(request(id=2, path='/hello'))
    headers, body, end = client.response(2)
    is_ok(headers['Status'], '200 OK', 'next request')

with subtest('Long names and values'):
    client = Client(address='127.0.0.1', port=port)
    client.send(request(path='/hello', params={'HTTP_USER_AGENT': 'x' * 300}))
    headers, body, end = client.response()
    like_ok(body, re.compile(rb'"agent":"x{300}"'), 'four bytes of length')

with subtest('UNIX domain socket'):
    if not hasattr(socket, 'AF_UNIX'):
        skip('no UNIX domain sockets', 2)
    else:
        with tempfile.TemporaryDirectory(dir='/tmp') as tmp:
            path = os.path.join(tmp, 'fcgi.sock')
            with Pyjo.Server.Daemon.new(app=app, listen=[f'fcgi+unix://{url_escape(path)}'], silent=True) as unix:
                unix.start()
                client = Client(path=path)
                client.send(request(path='/hello', params={'REMOTE_ADDR': None, 'REMOTE_PORT': None}))
                headers, body, end = client.response()
                is_ok(headers['Status'], '200 OK', 'status')
                like_ok(body, re.compile(rb'"remote":\[null,null\]'), 'no remote address')

with subtest('Started by the web server'):
    # The listen socket as the file descriptor 0 of the script, as Apache with mod_fcgid and lighttpd start it
    script = "from Pyjoyment.Lite import *\n\nget('/', {'text': 'Started'})\n\napp.start()\n"
    if sys.platform == 'win32':
        skip('a socket of Windows is not a file descriptor', 3)
    else:
        with tempfile.TemporaryDirectory() as tmp, socket.socket() as listener:
            Pyjo.File.path(tmp, 'myapp.py').spew(script)
            listener.bind(('127.0.0.1', 0))
            listener.listen()
            env = {**os.environ, 'PYTHONPATH': os.getcwd(), 'PYJO_LOG_LEVEL': 'fatal'}
            env.pop('PYJO_HOME', None)
            process = subprocess.Popen(
                [sys.executable, os.path.join(tmp, 'myapp.py')], stdin=listener.fileno(), env=env
            )
            atexit.register(lambda: process.poll() is None and process.kill())
            client = Client(address='127.0.0.1', port=listener.getsockname()[1])
            client.send(request(path='/'))
            headers, body, end = client.response()
            is_ok(headers['Status'], '200 OK', 'status')
            is_ok(body, b'Started', 'detected')
            process.send_signal(signal.SIGTERM)
            is_ok(process.wait(30), 0, 'stopped gracefully')

with subtest('Invalid location'):
    throws_ok(
        lambda: Pyjo.Server.Daemon.new(app=app, listen=['fcgis://127.0.0.1'], silent=True).start(),
        re.compile(r'Invalid listen location "fcgis://127\.0\.0\.1"'),
        'right error',
    )

daemon.stop()

done_testing()
