from Pyjo.Test import *

import contextlib
import io
import os
import sys


if not hasattr(os, 'fork'):
    plan(skip_all='no os.fork')

# PyPy with its JIT on macOS: the child of a fork crashes now and then with a bus error, under load
if sys.platform == 'darwin' and getattr(sys, 'pypy_translation_info', {}).get('translation.jit'):
    plan(skip_all='PyPy with its JIT on macOS: the child of a fork crashes now and then with SIGBUS')


# The output of the callbacks in the parent process
def output(cb):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        cb()
    return out.getvalue()


with subtest('Synopsis'):
    import Pyjo.IOLoop.Subprocess

    import time

    def synopsis():
        # Operation that would block the event loop for 5 seconds
        subprocess = Pyjo.IOLoop.Subprocess.new()

        def blocking(subprocess):
            time.sleep(0.05)
            return '♥', 'Pyjoyment'

        def done(subprocess, err, *results):
            if err:
                print(f'Subprocess error: {err}')
                return
            print(f'I {results[0]} {results[1]}!')

        subprocess.run(blocking, done)

        # Operation that would block the event loop for 5 seconds (with promise)
        subprocess.run_p(blocking).then(lambda *results: print(f'I {results[0]} {results[1]}!')).catch(
            lambda err: print(f'Subprocess error: {err}')
        )

        # Start event loop if necessary
        if not subprocess.ioloop.is_running:
            subprocess.ioloop.start()

    is_ok(output(synopsis), 'I ♥ Pyjoyment!\nI ♥ Pyjoyment!\n', 'two subprocesses')

with subtest('cleanup'):
    import Pyjo.IOLoop

    from Pyjo.File import tempfile

    file = tempfile()
    subprocess = Pyjo.IOLoop.Subprocess.new()
    subprocess.on('cleanup', lambda subprocess: ...)
    subprocess.on('cleanup', lambda subprocess: print(f'Process {os.getpid()} is about to exit'))
    subprocess.on('cleanup', lambda subprocess: file.spew(str(os.getpid()).encode()))

    def cleanup():
        subprocess.run(lambda subprocess: None, lambda subprocess, err, *results: None)
        Pyjo.IOLoop.start()

    is_ok(output(cleanup), '', 'printed in the subprocess')
    is_ok(file.slurp(), str(subprocess.pid).encode(), 'emitted in the subprocess')

with subtest('progress'):
    progress = []
    subprocess = Pyjo.IOLoop.Subprocess.new()
    subprocess.on('progress', lambda subprocess, *data: ...)
    subprocess.on('progress', lambda subprocess, *data: progress.append(data))
    subprocess.run(lambda subprocess: subprocess.progress('50%'), lambda subprocess, err, *results: None)
    Pyjo.IOLoop.start()
    is_deeply_ok(progress, [('50%',)], 'emitted in the parent process')

with subtest('spawn'):
    subprocess = Pyjo.IOLoop.Subprocess.new()
    subprocess.on('spawn', lambda subprocess: ...)
    subprocess.on('spawn', lambda subprocess: print(f'Performing work in process {subprocess.pid}'))

    def spawn():
        subprocess.run(lambda subprocess: None, lambda subprocess, err, *results: None)
        Pyjo.IOLoop.start()

    is_ok(output(spawn), f'Performing work in process {subprocess.pid}\n', 'emitted in the parent process')

with subtest('deserialize'):
    import Pyjo.JSON

    cb = subprocess.deserialize
    is_ok(cb, Pyjo.JSON.decode_json, 'default')
    subprocess.deserialize = lambda data: []
    is_deeply_ok(subprocess.deserialize(b'x'), [], 'set')

with subtest('ioloop'):
    loop = subprocess.ioloop
    is_ok(loop, Pyjo.IOLoop.singleton, 'default')
    loop = Pyjo.IOLoop.new()
    subprocess.ioloop = loop
    is_ok(subprocess.ioloop, loop, 'set')

with subtest('serialize'):
    cb = subprocess.serialize
    is_ok(cb, Pyjo.JSON.encode_json, 'default')
    subprocess.serialize = lambda array: b''
    is_ok(subprocess.serialize([]), b'', 'set')

with subtest('exit_code'):
    subprocess = Pyjo.IOLoop.Subprocess.new()
    code = subprocess.exit_code
    is_ok(code, None, 'still running')
    subprocess.run(lambda subprocess: None, lambda subprocess, err, *results: None)
    Pyjo.IOLoop.start()
    is_ok(subprocess.exit_code, 0, 'exit code')

with subtest('pid'):
    pid = subprocess.pid
    ok(pid, 'process id')

with subtest('progress'):

    def send():
        subprocess = Pyjo.IOLoop.Subprocess.new()

        # Send progress information to the parent process
        def blocking(subprocess):
            subprocess.progress('0%')
            time.sleep(0.01)
            subprocess.progress('50%')
            time.sleep(0.01)
            return 'Hello Pyjo!'

        def done(subprocess, err, *results):
            print('Progress is 100%')
            print(results[0])

        subprocess.run(blocking, done)
        subprocess.on('progress', lambda subprocess, *data: print(f'Progress is {data[0]}'))
        Pyjo.IOLoop.start()

    is_ok(output(send), 'Progress is 0%\nProgress is 50%\nProgress is 100%\nHello Pyjo!\n', 'progress')

with subtest('run'):
    subprocess = Pyjo.IOLoop.Subprocess.new()
    got = []
    subprocess = subprocess.run(lambda subprocess: 1, lambda subprocess, err, *results: got.extend(results))
    isa_ok(subprocess, Pyjo.IOLoop.Subprocess.object, 'subprocess')
    Pyjo.IOLoop.start()
    is_deeply_ok(got, [1], 'results')

with subtest('run_p'):
    import Pyjo.Promise

    def blocking(subprocess):
        time.sleep(0.05)
        return '♥', 'Pyjoyment'

    subprocess = Pyjo.IOLoop.Subprocess.new()
    promise = subprocess.run_p(lambda subprocess: ...)
    isa_ok(promise, Pyjo.Promise.object, 'promise')
    promise.wait()

    def run_p():
        subprocess.run_p(blocking).then(lambda *results: print(f'I {results[0]} {results[1]}!')).catch(
            lambda err: print(f'Subprocess error: {err}')
        ).wait()

    is_ok(output(run_p), 'I ♥ Pyjoyment!\n', 'promise')

done_testing()
