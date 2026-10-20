import Pyjo.HelloWorld
import Pyjo.IOLoop
import Pyjo.Server.Daemon
import Pyjo.UserAgent


# The server and the user agent, in the same event loop, which close their sockets at the end of the block
with (
    Pyjo.Server.Daemon.new(app=Pyjo.HelloWorld.new(), listen=['http://*:3000']) as daemon,
    Pyjo.UserAgent.new() as ua,
):
    # A request every second, which does not block the event loop; a request that the end of the block interrupts gets
    # an error
    @Pyjo.IOLoop.recurring(1)
    def fetch(loop):
        def done(ua, tx):
            print(tx.error['message'] if tx.error else f'{tx.res.code} {tx.res.text}')

        ua.get('http://127.0.0.1:3000/', done)

    # The server runs the event loop until INT or TERM stops it
    daemon.run()
