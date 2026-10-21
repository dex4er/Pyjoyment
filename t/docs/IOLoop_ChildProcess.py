import Pyjo.IOLoop

from Pyjo.Test import *

import io
import os
import signal
import sys

from contextlib import redirect_stdout


if os.name == 'nt':
    plan(skip_all='child processes need pipes that the reactor watches, which Windows does not have')

# The programs of the examples, as Python, which every system of the tests has, with one write of the whole line, as
# print writes the end of the line apart when the output is not buffered
LS = [sys.executable, '-c', 'import sys; sys.stdout.write("total 0\\n")']
SORT = [sys.executable, '-c', 'import sys; sys.stdout.write("".join(sorted(sys.stdin)))']


# The event loop until the process closes
def wait(child):
    child.on('close', lambda child, code, signal: child.reactor.stop())
    timer = child.reactor.timer(10, lambda reactor: reactor.stop())
    if not child.reactor.is_running:
        child.reactor.start()
    child.reactor.remove(timer)


with subtest('Synopsis'):
    from Pyjo.IOLoop.ChildProcess import ChildProcess

    child = ChildProcess()
    child.spawn(LS)
    wait(child)
    is_ok(child.exit_code, 0, 'exit code')

    # Or import the module, as in Google Python Style Guide

    import Pyjo.IOLoop.ChildProcess

    # Run a program, with its output and its exit status
    with redirect_stdout(io.StringIO()) as stdout:
        child = Pyjo.IOLoop.ChildProcess.new()
        child.on('spawn', lambda child: child.stdout.on('read', lambda stream, chunk: print(chunk)))
        child.on('close', lambda child, code, signal: print(f'Exited with {code}'))
        child.on('error', lambda child, err: print(f"Can't run: {err}"))
        child.spawn(LS)
        wait(child)
    like_ok(stdout.getvalue(), r"^b'total 0\\n'\nExited with 0\n$", 'output and exit status')

    # Write to its standard input, and end it
    with redirect_stdout(io.StringIO()) as stdout:
        child = Pyjo.IOLoop.ChildProcess.new().spawn(SORT)
        child.stdout.on('read', lambda stream, chunk: print(chunk))
        child.stdin.write(b'b\na\n')
        child.stdin.close_gracefully()

        # Start reactor if necessary
        wait(child)
    is_ok(stdout.getvalue(), "b'a\\nb\\n'\n", 'sorted')

with subtest('close'):
    with redirect_stdout(io.StringIO()) as stdout:
        child = Pyjo.IOLoop.ChildProcess.new()
        child.on('close', lambda child, code, signal: print(f'Process {child.pid} closed with {code}'))
        child.spawn(LS)
        wait(child)
    is_ok(stdout.getvalue(), f'Process {child.pid} closed with 0\n', 'closed')

with subtest('error'):
    with redirect_stdout(io.StringIO()) as stdout:
        child = Pyjo.IOLoop.ChildProcess.new()
        child.on('error', lambda child, err: (print(f'Error: {err}'), child.reactor.stop()))
        child.spawn(['/nonexistent/program'])
        child.reactor.start()
    like_ok(stdout.getvalue(), r'^Error: .*No such file or directory', 'error')

with subtest('exit'):
    with redirect_stdout(io.StringIO()) as stdout:
        child = Pyjo.IOLoop.ChildProcess.new()
        child.on('exit', lambda child, code, signal: print(f'Process {child.pid} exited with {code}'))
        child.spawn(LS)
        wait(child)
    is_ok(stdout.getvalue(), f'Process {child.pid} exited with 0\n', 'exited')

with subtest('spawn'):
    with redirect_stdout(io.StringIO()) as stdout:
        child = Pyjo.IOLoop.ChildProcess.new()
        child.on('spawn', lambda child: print(f'Running process {child.pid}'))
        child.spawn(LS)
        wait(child)
    is_ok(stdout.getvalue(), f'Running process {child.pid}\n', 'spawned')

with subtest('exit_code'):
    child = Pyjo.IOLoop.ChildProcess.new().spawn(LS)
    code = child.exit_code
    is_ok(code, None, 'still running')
    wait(child)
    is_ok(child.exit_code, 0, 'exit code')

with subtest('pid'):
    child = Pyjo.IOLoop.ChildProcess.new()
    pid = child.pid
    is_ok(pid, None, 'not spawned')
    wait(child.spawn(LS))
    isa_ok(child.pid, int, 'process id')

with subtest('reactor'):
    import Pyjo.Reactor.Poll

    child = Pyjo.IOLoop.ChildProcess.new()
    reactor = child.reactor
    is_ok(reactor, Pyjo.IOLoop.singleton.reactor, 'reactor of the singleton')
    poll = Pyjo.Reactor.Poll.new()
    child.reactor = poll
    is_ok(child.reactor, poll, 'reactor')

with subtest('signal_code'):
    child = Pyjo.IOLoop.ChildProcess.new().spawn([sys.executable, '-c', 'import time; time.sleep(10)'])
    signal_ = child.signal_code
    is_ok(signal_, None, 'no signal')
    child.on('spawn', lambda child: child.kill())
    wait(child)
    is_ok(child.signal_code, signal.SIGTERM, 'signal')

with subtest('stderr'):
    child = Pyjo.IOLoop.ChildProcess.new().spawn([sys.executable, '-c', 'import sys; sys.stderr.write("oops")'])
    stream = child.stderr
    chunks = []
    stream.on('read', lambda stream, chunk: chunks.append(chunk))
    wait(child)
    is_ok(b''.join(chunks), b'oops', 'error')

with subtest('stdin'):
    child = Pyjo.IOLoop.ChildProcess.new().spawn(SORT)
    stream = child.stdin
    chunks = []
    child.stdout.on('read', lambda stream, chunk: chunks.append(chunk))
    stream.write(b'b\na\n').close_gracefully()
    wait(child)
    is_ok(b''.join(chunks), b'a\nb\n', 'input')

with subtest('stdout'):
    child = Pyjo.IOLoop.ChildProcess.new().spawn([sys.executable, '-c', 'import time; time.sleep(10)'])
    stream = child.stdout

    # Kill a process that has been quiet for 60 seconds
    child.stdout.timeout = 60
    child.stdout.on('timeout', lambda stream: child.kill())
    child.stdout.timeout = 0.1
    wait(child)
    is_ok(child.signal_code, signal.SIGTERM, 'killed')

with subtest('kill'):
    child = Pyjo.IOLoop.ChildProcess.new().spawn([sys.executable, '-c', 'import time; time.sleep(10)'])
    boolean = child.kill()
    ok(boolean, 'running')
    wait(child)
    child = Pyjo.IOLoop.ChildProcess.new().spawn([sys.executable, '-c', 'import time; time.sleep(10)'])
    boolean = child.kill(signal.SIGKILL)
    ok(boolean, 'running')
    wait(child)
    is_ok(child.signal_code, signal.SIGKILL, 'killed')

with subtest('spawn'):
    child = Pyjo.IOLoop.ChildProcess.new()
    child = child.spawn(LS)
    wait(child)
    child = Pyjo.IOLoop.ChildProcess.new()
    child = child.spawn(
        [sys.executable, '-c', 'import os; print(os.environ["REDIRECT_STATUS"])'],
        cwd='/',
        env={'REDIRECT_STATUS': '200'},
    )
    chunks = []
    child.stdout.on('read', lambda stream, chunk: chunks.append(chunk))
    wait(child)
    is_ok(b''.join(chunks).strip(), b'200', 'environment')

done_testing()
