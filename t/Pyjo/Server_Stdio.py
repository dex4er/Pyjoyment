import Pyjo.File
import Pyjo.IOLoop
import Pyjo.IOLoop.ChildProcess
import Pyjo.Server.Stdio

from Pyjo.File import curfile
from Pyjo.Test import *

import os
import re
import signal
import sys


# Not in Mojolicious: a protocol on the standard input and output
PYTHON = sys.executable
ENV = {**os.environ, 'PYTHONPATH': os.pathsep.join([curfile().dirname().dirname().dirname().to_str(), *sys.path])}

# An application with a protocol of lines in capitals, which prints that it starts and what it gets, answers "slow" a second later, also
# after the end of the input, which it prints, and logs its errors and its end
APP = """
import Pyjo.IOLoop.Messages
import Pyjo.Server.Stdio

from Pyjoyment.Lite import *


@hook('before_server_start')
def stdio(server, app):
    if isinstance(server, Pyjo.Server.Stdio.object):
        print('starting')

        @server.on('stream')
        def stream(server, stream):
            messages = Pyjo.IOLoop.Messages.new(stream)
            messages.on('error', lambda messages, err: app.log.error(str(err)))
            slow, ended = [], []

            @messages.on('message')
            def message(messages, line):
                print(f'got {line.decode()}')
                if line != b'slow':
                    return messages.send(line.upper())
                slow.append(line)

                def answer(reactor):
                    messages.send(slow.pop().upper())
                    if ended:
                        messages.close_gracefully()

                stream.reactor.timer(1, answer)

            @messages.on('end')
            def end(messages):
                print('ended')
                ended.append(True)
                if not slow:
                    messages.close_gracefully()


@hook('after_server_stop')
def stopped(server, app):
    app.log.info('Stopped')


app.start()
"""

if os.name == 'nt':
    with subtest('Windows'):
        throws_ok(
            lambda: Pyjo.Server.Stdio.new().run(),
            re.compile(r'^Standard input and output need pipes that the reactor watches'),
            'no stream',
        )
    done_testing()
    sys.exit()

dir = Pyjo.File.tempdir()
script = dir.child('myapp.py').spew(APP.encode()).to_str()


# The output, the error and the exit code of the command, whose input is written and ended
def run(input=b'', env=ENV, args=(script, 'stdio')):
    result = []
    promise = Pyjo.IOLoop.ChildProcess.new().run_p([PYTHON, *args], input=input, env=env)
    promise.then(lambda *args: (result.extend(args), Pyjo.IOLoop.stop()))
    timer = Pyjo.IOLoop.timer(10, lambda loop: Pyjo.IOLoop.stop())
    Pyjo.IOLoop.start()
    Pyjo.IOLoop.remove(timer)
    code, out, err = result
    return code, bytes(out), bytes(err).decode()


# The exit code, the output and the error of the command, whose input is written and left open, and which is acted on
# once it has got the slow line, and once its input has ended
def talk(input, action, ended=None):
    child = Pyjo.IOLoop.ChildProcess.new()
    out, err, result = bytearray(), bytearray(), []
    child.on('close', lambda child, code, signal: (result.append(code), Pyjo.IOLoop.stop()))
    child.spawn([PYTHON, script, 'stdio'], env=ENV)
    child.stdout.on('read', lambda stream, chunk: out.extend(chunk))

    def errors(stream, chunk):
        before = bytes(err)
        err.extend(chunk)
        for line, cb in ((b'got slow', action), (b'ended', ended)):
            if cb is not None and line not in before and line in err:
                cb(child)

    child.stderr.on('read', errors)
    child.stdin.write(input)
    timer = Pyjo.IOLoop.timer(10, lambda loop: Pyjo.IOLoop.stop())
    Pyjo.IOLoop.start()
    Pyjo.IOLoop.remove(timer)
    child.kill(signal.SIGKILL)
    return result[0] if result else None, bytes(out), bytes(err).decode()


with subtest('No protocol'):
    code, out, err = run(b'hello\n', args=('-c', 'import Pyjo.Server.Stdio; Pyjo.Server.Stdio.new().run()'))
    is_ok(code, 1, 'right exit code')
    is_ok(out, b'', 'no output')
    like_ok(err, r'Nothing serves the standard input and output, the event "stream" has no subscriber', 'no subscriber')

with subtest('Lines'):
    code, out, err = run(b'hello\nworld\r\n')
    is_ok(code, 0, 'right exit code')
    is_ok(out, b'HELLO\nWORLD\n', 'right output')
    like_ok(
        err, re.compile(r'^starting\ngot hello\ngot world\nended\n.*\[info\] Stopped\n$'), 'print and log on stderr'
    )

with subtest('End of input'):
    code, out, err = run()
    is_ok(code, 0, 'right exit code')
    is_ok(out, b'', 'no output')
    like_ok(err, re.compile(r'^starting\nended\n.*\[info\] Stopped\n$'), 'stopped')

with subtest('Responses after the end of input'):
    code, out, err = run(b'slow\nhello\n')
    is_ok(code, 0, 'right exit code')
    is_ok(out, b'HELLO\nSLOW\n', 'right output')

with subtest('Message over the maximum size'):
    code, out, err = run(b'hello\n' + b'x' * 20 + b'\nworld\n', {**ENV, 'PYJO_MAX_MESSAGE_SIZE': '10'})
    is_ok(code, 0, 'right exit code')
    is_ok(out, b'HELLO\n', 'right output')
    like_ok(err, re.compile(r'(?s)\[error\] Maximum message size exceeded\n.*\[info\] Stopped\n$'), 'error and stopped')

with subtest('Graceful stop'):
    code, out, err = talk(b'slow\n', lambda child: child.kill(signal.SIGTERM))
    is_ok(code, 0, 'right exit code')
    is_ok(out, b'SLOW\n', 'response of the request in progress')
    like_ok(err, re.compile(r'\[info\] Stopped\n$'), 'stopped')

    # The input after the end of the input that the server has ended
    code, out, err = talk(
        b'slow\n', lambda child: child.kill(signal.SIGINT), lambda child: child.stdin.write(b'hello\n')
    )
    is_ok(code, 0, 'right exit code')
    is_ok(out, b'SLOW\n', 'response of the request in progress only')
    like_ok(err, re.compile(r'\[info\] Stopped\n$'), 'stopped')

with subtest('Immediate stop'):
    code, out, err = talk(b'slow\n', lambda child: child.kill(signal.SIGQUIT))
    is_ok(code, 0, 'right exit code')
    is_ok(out, b'', 'no response')
    unlike_ok(err, re.compile(r'Stopped'), 'not stopped gracefully')

    # Ctrl-C pressed twice
    def twice(child):
        child.kill(signal.SIGINT)
        Pyjo.IOLoop.timer(0.2, lambda loop: child.kill(signal.SIGINT))

    code, out, err = talk(b'slow\n', twice)
    is_ok(code, 0, 'right exit code')
    is_ok(out, b'', 'no response')
    unlike_ok(err, re.compile(r'Stopped'), 'not stopped gracefully')

with subtest('Ignored signal'):

    def hangup(child):
        child.kill(signal.SIGHUP)
        Pyjo.IOLoop.timer(0.2, lambda loop: child.stdin.write(b'hello\n').close_gracefully())

    code, out, err = talk(b'slow\n', hangup)
    is_ok(code, 0, 'right exit code')
    is_ok(out, b'HELLO\nSLOW\n', 'right output')
    like_ok(err, re.compile(r'\[info\] Stopped\n$'), 'stopped')

done_testing()
