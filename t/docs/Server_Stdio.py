import Pyjo.IOLoop
import Pyjo.IOLoop.ChildProcess
import Pyjo.Server.Stdio

from Pyjo.File import curfile
from Pyjo.Test import *

import os
import sys


ENV = {**os.environ, 'PYTHONPATH': os.pathsep.join([curfile().dirname().dirname().dirname().to_str(), *sys.path])}


# The examples run in a process of their own, as the server takes the standard input and output of its process
def run(code, input, *args):
    result = []
    promise = Pyjo.IOLoop.ChildProcess.new().run_p([sys.executable, '-c', code, *args], input=input, env=ENV)
    promise.then(lambda *args: (result.extend(args), Pyjo.IOLoop.stop()))
    timer = Pyjo.IOLoop.timer(10, lambda loop: Pyjo.IOLoop.stop())
    Pyjo.IOLoop.start()
    Pyjo.IOLoop.remove(timer)
    code, out, err = result
    return code, bytes(out), bytes(err)


with subtest('Synopsis'):
    if os.name == 'nt':
        plan(skip_all='the standard input and output need pipes that the reactor watches, which Windows does not have')

    code = """
from Pyjo.Server.Stdio import Stdio

server = Stdio()


# Lines of the standard input in capitals
@server.on('stream')
def stream(server, stream):
    stream.on('read', lambda stream, chunk: stream.write(chunk.upper()))


server.run()
"""
    is_deeply_ok(run(code, b'hello\n'), (0, b'HELLO\n', b''), 'capitals')

    code = """
import Pyjo.Server.Stdio

server = Pyjo.Server.Stdio.new()


# Lines of the standard input in capitals
@server.on('stream')
def stream(server, stream):
    stream.on('read', lambda stream, chunk: stream.write(chunk.upper()))


server.run()
"""
    is_deeply_ok(run(code, b'hello\n'), (0, b'HELLO\n', b''), 'capitals of the module')

with subtest('Description'):
    if os.name == 'nt':
        plan(skip_all='the standard input and output need pipes that the reactor watches, which Windows does not have')

    code = """
from Pyjo.JSON.RPC import RPC
from Pyjoyment.Lite import *

rpc = RPC()
rpc.method('upper', lambda text: text.upper())
app.log.level = 'fatal'

import Pyjo.IOLoop.Messages
import Pyjo.Server.Stdio

# The methods of JSON-RPC, one message on each line
@app.hook('before_server_start')
def stdio(server, app):
    if isinstance(server, Pyjo.Server.Stdio.object):
        server.on('stream', lambda server, stream: rpc.serve(Pyjo.IOLoop.Messages.new(stream)))

app.start()
"""
    request = b'{"jsonrpc":"2.0","method":"upper","params":["hello"],"id":1}\n'
    is_deeply_ok(run(code, request, 'stdio'), (0, b'{"jsonrpc":"2.0","result":"HELLO","id":1}\n', b''), 'JSON-RPC')

with subtest('Events'):
    if os.name == 'nt':
        plan(skip_all='the standard input and output need pipes that the reactor watches, which Windows does not have')

    code = """
import Pyjo.Server.Stdio

server = Pyjo.Server.Stdio.new()
server.on('stream', lambda server, stream: stream.on('read', lambda stream, chunk: stream.write(chunk)))

@server.on('stream')
def stream(server, stream):
    stream.on('end', lambda stream: stream.close_gracefully())

server.run()
"""
    is_deeply_ok(run(code, b'hello\n'), (0, b'hello\n', b''), 'closed at the end')

with subtest('ioloop'):
    server = Pyjo.Server.Stdio.new()
    loop = server.ioloop
    is_ok(loop, Pyjo.IOLoop.singleton, 'loop')
    with Pyjo.IOLoop.new() as other:
        server.ioloop = other
        is_ok(server.ioloop, other, 'server.ioloop')

with subtest('run'):
    if os.name == 'nt':
        plan(skip_all='the standard input and output need pipes that the reactor watches, which Windows does not have')
    code, out, err = run('import Pyjo.Server.Stdio; Pyjo.Server.Stdio.new().run()', b'')
    like_ok(err, rb'event "stream" has no subscriber', 'no subscriber')

done_testing()
