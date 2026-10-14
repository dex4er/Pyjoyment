import Pyjo.IOLoop
import Pyjo.IOLoop.Client

from Pyjo.Test import *

import os
import socket
import tempfile


def connect(**options):
    got = {'handle': None, 'err': None}
    client = Pyjo.IOLoop.Client.new()

    def connected(client, handle):
        got['handle'] = handle
        Pyjo.IOLoop.stop()

    def error(client, err):
        got['err'] = err
        Pyjo.IOLoop.stop()

    client.on('connect', connected)
    client.on('error', error)
    client.connect(**options)
    Pyjo.IOLoop.start()
    client.close()
    return got


with subtest('A server of the standard library'):
    listening = socket.create_server(('127.0.0.1', 0))
    port = listening.getsockname()[1]
    got = connect(port=port)
    isa_ok(got['handle'], socket.socket, 'connected')
    ok(not got['handle'].getblocking(), 'non-blocking')
    ok(got['handle'].getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY), 'TCP_NODELAY')
    listening.accept()[0].close()
    got['handle'].close()

    got = connect(address='localhost', port=port)
    isa_ok(got['handle'], socket.socket, 'by name, resolved in a thread')
    got['handle'].close()

    got = connect(port=port, source_address=('127.0.0.1', 0))
    is_ok(got['handle'].getsockname()[0], '127.0.0.1', 'from the source address')
    got['handle'].close()
    listening.close()

with subtest('Errors'):
    closed = socket.create_server(('127.0.0.1', 0))
    port = closed.getsockname()[1]
    closed.close()
    got = connect(port=port)
    isa_ok(got['err'], ConnectionRefusedError, 'refused')
    got = connect(address='name.invalid', port=80)
    like_ok(str(got['err']), r"^Can't resolve: ", 'unknown name')
    got = connect(port=port, socks_address='127.0.0.1')
    ok(got['err'], 'no SOCKS')

with subtest('Blocking name resolution'):
    listening = socket.create_server(('127.0.0.1', 0))
    os.environ['PYJO_NO_NNR'] = '1'
    code = f"""
import Pyjo.IOLoop, Pyjo.IOLoop.Client
print(Pyjo.IOLoop.Client.object.can_nnr())
client = Pyjo.IOLoop.Client.new()
client.on('connect', lambda client, handle: print('connected') or Pyjo.IOLoop.stop())
client.connect(address='localhost', port={listening.getsockname()[1]})
Pyjo.IOLoop.start()
"""
    import subprocess
    import sys

    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True)
    del os.environ['PYJO_NO_NNR']
    is_ok(result.stdout, 'False\nconnected\n', 'PYJO_NO_NNR')
    listening.close()

with subtest('UNIX domain socket'):
    with tempfile.TemporaryDirectory() as dir:
        path = os.path.join(dir, 'test.sock')
        listening = socket.socket(socket.AF_UNIX)
        listening.bind(path)
        listening.listen()
        got = connect(path=path)
        is_ok(got['handle'].family, socket.AF_UNIX, 'connected')
        got['handle'].close()
        listening.close()

done_testing()
