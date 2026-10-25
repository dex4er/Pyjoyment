import Pyjo.File
import Pyjo.IOLoop
import Pyjo.IOLoop.ChildProcess
import Pyjoyment.Command.stdio

from Pyjo.File import curfile
from Pyjo.Test import *

import os
import sys


ENV = {**os.environ, 'PYTHONPATH': os.pathsep.join([curfile().dirname().dirname().dirname().to_str(), *sys.path])}

# An application of lines in capitals, which tells its mode on stderr
APP = """
import Pyjo.IOLoop.Messages
import Pyjo.Server.Stdio

from Pyjoyment.Lite import *


@hook('before_server_start')
def stdio(server, app):
    if isinstance(server, Pyjo.Server.Stdio.object):
        print(app.mode)

        @server.on('stream')
        def stream(server, stream):
            messages = Pyjo.IOLoop.Messages.new(stream)
            messages.on('message', lambda messages, line: messages.send(line.upper()))


app.start()
"""


# The command in a process of its own, as the server takes the standard input and output of its process
def run(*args):
    result = []
    promise = Pyjo.IOLoop.ChildProcess.new().run_p([sys.executable, *args], input=b'hello\n', env=ENV)
    promise.then(lambda *args: (result.extend(args), Pyjo.IOLoop.stop()))
    timer = Pyjo.IOLoop.timer(10, lambda loop: Pyjo.IOLoop.stop())
    Pyjo.IOLoop.start()
    Pyjo.IOLoop.remove(timer)
    code, out, err = result
    return code, bytes(out), bytes(err)


with subtest('Synopsis'):
    stdio_command = Pyjoyment.Command.stdio.new()
    like_ok(stdio_command.usage, r'^Usage: APPLICATION stdio \[OPTIONS\]\n\n  \./myapp\.py stdio\n', 'usage')

with subtest('Attributes'):
    stdio_command = Pyjoyment.Command.stdio.new()
    is_ok(stdio_command.description, 'Start application on standard input and output', 'description')

with subtest('run'):
    if os.name == 'nt':
        plan(skip_all='the standard input and output need pipes that the reactor watches, which Windows does not have')
    dir = Pyjo.File.tempdir()
    script = dir.child('myapp.py').spew(APP.encode()).to_str()

    # ./myapp.py stdio
    is_deeply_ok(run(script, 'stdio'), (0, b'HELLO\n', b'development\n'), 'served in development mode')

    # ./myapp.py stdio -m production
    is_deeply_ok(
        run(script, 'stdio', '-m', 'production'), (0, b'HELLO\n', b'production\n'), 'served in production mode'
    )

done_testing()
