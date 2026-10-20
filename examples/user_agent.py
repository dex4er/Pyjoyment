import Pyjo.HelloWorld
import Pyjo.IOLoop
import Pyjo.Server.Daemon
import Pyjo.UserAgent


# A request of the user agent every second, which does not block the event loop; the variable keeps the user agent,
# whose connections close when it is freed
ua = Pyjo.UserAgent.new()


@Pyjo.IOLoop.recurring(1)
def fetch(loop):
    ua.get('http://127.0.0.1:3000/', lambda ua, tx: print(tx.result.code, tx.result.text))


# The application on the server, in the same event loop
Pyjo.Server.Daemon.new(app=Pyjo.HelloWorld.new(), listen=['http://*:3000']).run()
