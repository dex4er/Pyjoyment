import Pyjo.IOLoop
import Pyjo.IOLoop.ChildProcess
import Pyjo.IOLoop.Stream

from Pyjo.Test import *

import os
import signal
import sys
import time


# Not in Mojolicious: child processes, inspired by child_process of Node.js
PYTHON = sys.executable


# The events of a process until it closes, or a limit of time
def run(child, timeout=10):
    events = []
    child.on('spawn', lambda child: events.append(('spawn',)))
    child.on('exit', lambda child, code, signal: events.append(('exit', code, signal)))
    child.on('error', lambda child, err: (events.append(('error', err)), Pyjo.IOLoop.stop()))
    child.on('close', lambda child, code, signal: (events.append(('close', code, signal)), Pyjo.IOLoop.stop()))
    timer = Pyjo.IOLoop.timer(timeout, lambda loop: Pyjo.IOLoop.stop())
    Pyjo.IOLoop.start()
    Pyjo.IOLoop.remove(timer)
    return events


def output(stream):
    chunks = []
    stream.on('read', lambda stream, chunk: chunks.append(chunk))
    return chunks


if os.name == 'nt':
    with subtest('Windows'):
        child = Pyjo.IOLoop.ChildProcess.new().spawn([PYTHON, '-c', 'pass'])
        events = run(child)
        is_ok(events[0][0], 'error', 'error')
        like_ok(str(events[0][1]), r'^Child processes need pipes that the reactor watches', 'right error')
        is_ok(child.stdout, None, 'no output')
    done_testing()
    sys.exit()

with subtest('Output and exit'):
    child = Pyjo.IOLoop.ChildProcess.new()
    is_ok(child.pid, None, 'no process id')
    is_ok(child.stdout, None, 'no output yet')
    child.spawn([PYTHON, '-c', 'print("Hello")'])
    ok(isinstance(child.stdout, Pyjo.IOLoop.Stream.object), 'stream of the output')
    ok(isinstance(child.stdin, Pyjo.IOLoop.Stream.object), 'stream of the input')
    ok(isinstance(child.stderr, Pyjo.IOLoop.Stream.object), 'stream of the error')
    isa_ok(child.pid, int, 'process id')
    chunks = output(child.stdout)
    events = run(child)
    is_deeply_ok(events, [('spawn',), ('exit', 0, None), ('close', 0, None)], 'right events')
    is_ok(b''.join(chunks), b'Hello' + os.linesep.encode(), 'right output')
    is_ok(child.exit_code, 0, 'right exit code')
    is_ok(child.signal_code, None, 'no signal')
    ok(not child.kill(), 'not running')

with subtest('Input'):
    data = b'0123456789' * 100000
    child = Pyjo.IOLoop.spawn(
        [PYTHON, '-c', 'import shutil, sys; shutil.copyfileobj(sys.stdin.buffer, sys.stdout.buffer)']
    )
    chunks = output(child.stdout)
    drained = []
    child.stdin.write(data, lambda stream: drained.append(True))
    child.stdin.close_gracefully()
    events = run(child)
    is_ok(events[-1], ('close', 0, None), 'closed')
    ok(drained, 'drained')
    is_ok(b''.join(chunks), data, 'right output')

with subtest('Error and exit code'):
    child = Pyjo.IOLoop.spawn([PYTHON, '-c', 'import sys; sys.stderr.write("oops"); sys.exit(3)'])
    chunks = output(child.stderr)
    events = run(child)
    is_deeply_ok(events[-2:], [('exit', 3, None), ('close', 3, None)], 'right events')
    is_ok(b''.join(chunks), b'oops', 'right error')
    is_ok(child.exit_code, 3, 'right exit code')

with subtest('Signals'):
    child = Pyjo.IOLoop.spawn([PYTHON, '-c', 'import time; time.sleep(10)'])
    child.on('spawn', lambda child: child.kill())
    events = run(child)
    is_ok(events[-1], ('close', None, signal.SIGTERM), 'terminated')
    is_ok(child.exit_code, None, 'no exit code')
    is_ok(child.signal_code, signal.SIGTERM, 'right signal')
    child = Pyjo.IOLoop.spawn(
        [PYTHON, '-c', 'import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(10)']
    )
    child.on('spawn', lambda child: child.kill(signal.SIGKILL))
    events = run(child)
    is_ok(events[-1], ('close', None, signal.SIGKILL), 'killed')

with subtest('Not found'):
    child = Pyjo.IOLoop.spawn(['/nonexistent/program'])
    events = run(child)
    is_ok(len(events), 1, 'one event')
    is_ok(events[0][0], 'error', 'error')
    ok(isinstance(events[0][1], FileNotFoundError), 'right error')
    is_ok(child.pid, None, 'no process id')
    is_ok(child.stdout, None, 'no output')
    ok(not child.kill(), 'not running')

with subtest('Directory and environment'):
    tmp = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))
    child = Pyjo.IOLoop.spawn(
        [PYTHON, '-c', 'import os; print(os.getcwd()); print(os.environ.get("FOO"), "PATH" in os.environ)'],
        cwd=tmp,
        env={'FOO': 'bar'},
    )
    chunks = output(child.stdout)
    run(child)
    is_deeply_ok(b''.join(chunks).decode().splitlines(), [tmp, 'bar False'], 'right directory and environment')

with subtest('Input that the process does not read'):
    child = Pyjo.IOLoop.spawn([PYTHON, '-c', 'import os, time; os.close(0); time.sleep(0.2)'])
    closed = []
    child.stdin.on('close', lambda stream: closed.append(True))
    child.stdin.write(b'x' * 1000000)
    start = time.monotonic()
    events = run(child)
    is_ok(events[-1], ('close', 0, None), 'closed')
    ok(closed, 'input closed')
    ok(time.monotonic() - start < 5, 'in time')

with subtest('Pause the output'):
    child = Pyjo.IOLoop.spawn([PYTHON, '-c', 'import sys; sys.stdout.write("x" * 1000000)'])
    chunks = output(child.stdout)
    child.stdout.stop()
    Pyjo.IOLoop.timer(0.2, lambda loop: (chunks.append(b'|'), child.stdout.start()))
    events = run(child)
    is_ok(events[-1], ('close', 0, None), 'closed')
    is_ok(chunks[0], b'|', 'paused first')
    is_ok(len(b''.join(chunks[1:])), 1000000, 'whole output')

with subtest('Exit before the end of the output'):
    # The shell exits at once, and its child keeps the output for a moment
    child = Pyjo.IOLoop.spawn(['/bin/sh', '-c', 'sleep 0.3 & exit 0'])
    times = {}
    child.on('exit', lambda child, code, signal: times.setdefault('exit', time.monotonic()))
    child.on('close', lambda child, code, signal: times.setdefault('close', time.monotonic()))
    events = run(child)
    is_deeply_ok([event[0] for event in events], ['spawn', 'exit', 'close'], 'right events')
    ok(times['close'] - times['exit'] > 0.1, 'closed later')

with subtest('Event loop'):
    loop = Pyjo.IOLoop.new()
    child = loop.spawn([PYTHON, '-c', 'print("loop")'])
    is_ok(child.reactor, loop.reactor, 'reactor of the loop')
    chunks = output(child.stdout)
    child.on('close', lambda child, code, signal: loop.stop())
    timer = loop.timer(10, lambda loop: loop.stop())
    loop.start()
    loop.remove(timer)
    is_ok(b''.join(chunks).strip(), b'loop', 'right output')

done_testing()
