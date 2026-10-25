import Pyjo.IOLoop.Messages
import Pyjo.Server.Stdio

from Pyjo.JSON.RPC import RPC, Error
from Pyjoyment.Lite import *


# A method of JSON-RPC, whose parameters the schema of its type hints validates
rpc = RPC()


@rpc.method(schema=True)
def divide(a: float, b: float) -> float:
    if b == 0:
        raise Error.new(1, 'Division by zero')
    return a / b


# The server, one message on each line, on the standard input and output
@hook('before_server_start')
def stdio(server, app):
    if isinstance(server, Pyjo.Server.Stdio.object):
        server.on('stream', lambda server, stream: rpc.serve(Pyjo.IOLoop.Messages.new(stream)))


# And the same server over HTTP
post('/rpc', rpc.to_action())

app.start()
