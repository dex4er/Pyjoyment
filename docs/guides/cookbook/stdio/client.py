import Pyjo.IOLoop
import Pyjo.IOLoop.Messages
import Pyjo.Promise

from Pyjo.JSON.RPC import RPC

import sys


# The server in a child process, whose standard output and input are a stream of messages
child = Pyjo.IOLoop.spawn([sys.executable, 'rpc.py', 'stdio'])
messages = Pyjo.IOLoop.Messages.new(child.stdout, output=child.stdin)
client = RPC().serve(messages)


@Pyjo.Promise.coroutine
async def main():
    print(await client.call_p('divide', 7, 2))

    # The end of its standard input ends the server
    closed = child.once_p('close')
    messages.close_gracefully()
    await closed


main().wait()
