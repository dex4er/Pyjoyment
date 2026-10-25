import Pyjo.IOLoop
import Pyjo.IOLoop.ChildProcess

from Pyjo.File import curfile
from Pyjo.Test import *

import os
import sys


if os.name == 'nt':
    plan(skip_all='the standard input and output need pipes that the reactor watches, which Windows does not have')

ENV = {**os.environ, 'PYTHONPATH': os.pathsep.join([curfile().dirname().dirname().dirname().to_str(), *sys.path])}

# The event loop of a script whose stream is started, as the examples that only make it
START = """
stdio.on('close', lambda stdio: stdio.reactor.stop())
stdio.start()
stdio.reactor.start()
"""


# The examples run in a process of their own, as the stream takes the standard input and output of its process
def run(code, input):
    result = []
    promise = Pyjo.IOLoop.ChildProcess.new().run_p([sys.executable, '-c', code], input=input, env=ENV)
    promise.then(lambda *args: (result.extend(args), Pyjo.IOLoop.stop()))
    timer = Pyjo.IOLoop.timer(10, lambda loop: Pyjo.IOLoop.stop())
    Pyjo.IOLoop.start()
    Pyjo.IOLoop.remove(timer)
    code, out, err = result
    return code, bytes(out), bytes(err)


with subtest('Synopsis'):
    code = """
from Pyjo.IOLoop.Stdio import Stdio

# Echo what comes in
stdio = Stdio()
stdio.on('read', lambda stdio, chunk: stdio.write(chunk))
"""
    is_deeply_ok(run(code + START, b'hello'), (0, b'hello', b''), 'echo')

    code = """
import Pyjo.IOLoop.Stdio

# Echo what comes in, and end once the input has ended and the rest is written
stdio = Pyjo.IOLoop.Stdio.new()
stdio.on('read', lambda stdio, chunk: stdio.write(chunk))
stdio.on('close', lambda stdio: stdio.reactor.stop())
stdio.start()

# Start reactor if necessary
if not stdio.reactor.is_running:
    stdio.reactor.start()
"""
    is_deeply_ok(run(code, b'hello'), (0, b'hello', b''), 'echo until the end')

with subtest('end'):
    code = """
import Pyjo.IOLoop.Stdio

stdio = Pyjo.IOLoop.Stdio.new()
stdio.on('read', lambda stdio, chunk: stdio.write(chunk))
stdio.on('end', lambda stdio: stdio.close_gracefully())
"""
    is_deeply_ok(run(code + START, b'hello'), (0, b'hello', b''), 'closed at the end')

done_testing()
