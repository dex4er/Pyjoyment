import Pyjo.IOLoop.Messages
import Pyjo.Server.Stdio

from Pyjoyment.Lite import *


# Lines in capitals on the standard input and output
@hook('before_server_start')
def stdio(server, app):
    if not isinstance(server, Pyjo.Server.Stdio.object):
        return

    @server.on('stream')
    def stream(server, stream):
        messages = Pyjo.IOLoop.Messages.new(stream)

        @messages.on('message')
        def message(messages, line):
            print(f'Got {line.decode()}')
            messages.send(line.upper())


app.start()
