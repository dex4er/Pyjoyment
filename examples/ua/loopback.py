import Pyjo.HelloWorld
import Pyjo.IOLoop
import Pyjo.Server.Daemon
import Pyjo.UserAgent


# The server, on a port that the system picks, and the user agent, in the same event loop, which close their sockets at
# the end of the block
with (
    Pyjo.Server.Daemon.new(app=Pyjo.HelloWorld.new(), listen=['http://127.0.0.1'], silent=True) as daemon,
    Pyjo.UserAgent.new(ioloop=Pyjo.IOLoop.singleton) as ua,
):
    # A blocking request, which runs the event loop of the server until the response
    tx = ua.get(f'http://127.0.0.1:{daemon.start().ports()[0]}/')
    print(tx.result.code, tx.result.text)
