from Pyjo.Test import *

import os
import sys


# Left out from Mojolicious: TEST_SUBPROCESS, which enables the tests, as they are quick; MOJO_REACTOR, as the tests run
# on the reactor of Pyjo.Reactor.detect()
if not hasattr(os, 'fork'):
    plan(skip_all='no os.fork')

# PyPy with its JIT on macOS: the child of a fork crashes now and then with a bus error, under load
if sys.platform == 'darwin' and getattr(sys, 'pypy_translation_info', {}).get('translation.jit'):
    plan(skip_all='PyPy with its JIT on macOS: the child of a fork crashes now and then with SIGBUS')

import Pyjo.Exception
import Pyjo.IOLoop
import Pyjo.IOLoop.Subprocess
import Pyjo.Promise

from Pyjo.File import tempfile


with subtest('Huge result'):
    fail = result = None
    start = []
    subprocess = Pyjo.IOLoop.Subprocess.new()
    subprocess.on('spawn', lambda subprocess: start.append(subprocess.pid))

    def parent(subprocess, err, two=None):
        global fail, result
        fail = err
        result += two

    subprocess.run(lambda subprocess: f'{subprocess.pid}{os.getpid()}' + ('x' * 100000), parent)

    result = str(os.getpid())
    ok(not subprocess.pid, 'no process id available yet')
    is_ok(subprocess.exit_code, None, 'no exit code')
    Pyjo.IOLoop.start()
    ok(subprocess.pid, 'process id available')
    is_ok(subprocess.exit_code, 0, 'zero exit code')
    ok(not fail, 'no error')
    is_ok(result, f'{os.getpid()}0{subprocess.pid}' + ('x' * 100000), 'right result')
    is_deeply_ok(start, [subprocess.pid], 'spawn event has been emitted once')

with subtest('Custom event loop'):
    fail = result = None
    loop = Pyjo.IOLoop.new()

    def parent(subprocess, err, *results):
        global fail, result
        fail = err
        result = list(results)

    loop.subprocess(lambda subprocess: '♥', parent)
    loop.start()
    ok(not fail, 'no error')
    is_deeply_ok(result, ['♥'], 'right structure')

with subtest('Multiple return values'):
    fail = result = None
    subprocess = Pyjo.IOLoop.Subprocess.new()

    def parent(subprocess, err, *results):
        global fail, result
        fail = err
        result = list(results)

    subprocess.run(lambda subprocess: ('♥', [{'two': 2}], 3), parent)
    Pyjo.IOLoop.start()
    ok(not fail, 'no error')
    is_deeply_ok(result, ['♥', [{'two': 2}], 3], 'right structure')

with subtest('Promises'):
    result = []
    subprocess = Pyjo.IOLoop.Subprocess.new()
    is_ok(subprocess.exit_code, None, 'no exit code')

    def then(*values):
        global result
        result = list(values)

    subprocess.run_p(lambda subprocess: ('♥', [{'two': 2}], 3)).then(then).wait()
    is_deeply_ok(result, ['♥', [{'two': 2}], 3], 'right structure')
    fail = None

    def catch(err):
        global fail
        fail = err

    subprocess = Pyjo.IOLoop.Subprocess.new()
    subprocess.run_p(lambda subprocess: Pyjo.Exception.object.throw('Whatever')).catch(catch).wait()
    is_ok(subprocess.exit_code, 0, 'zero exit code')
    like_ok(fail, r'Whatever', 'right error')
    result = []
    Pyjo.IOLoop.subprocess().run_p(lambda subprocess: '♥').then(then).wait()
    is_deeply_ok(result, ['♥'], 'right structure')

with subtest('Event loop in subprocess'):
    fail = result = None
    subprocess = Pyjo.IOLoop.Subprocess.new()

    def child(subprocess):
        result = None

        def tick(loop):
            nonlocal result
            result = 23

        Pyjo.IOLoop.next_tick(tick)
        Pyjo.IOLoop.start()
        return result

    def parent(subprocess, err, twenty_three=None):
        global fail, result
        fail = err
        result = twenty_three

    subprocess.run(child, parent)
    Pyjo.IOLoop.start()
    ok(not fail, 'no error')
    is_ok(result, 23, 'right result')

with subtest('Event loop in subprocess (already running event loop)'):
    fail = result = None

    def child(subprocess):
        result = None
        promise = Pyjo.Promise.new()

        def then(value):
            nonlocal result
            result = value

        promise.then(then)
        Pyjo.IOLoop.next_tick(lambda loop: promise.resolve(25))
        promise.wait()
        return result

    def parent(subprocess, err, twenty_five=None):
        global fail, result
        fail = err
        result = twenty_five

    Pyjo.IOLoop.next_tick(lambda loop: Pyjo.IOLoop.subprocess(child, parent))
    Pyjo.IOLoop.start()
    ok(not fail, 'no error')
    is_ok(result, 25, 'right result')

with subtest('Concurrent subprocesses'):
    fail = result = None
    promise = Pyjo.IOLoop.subprocess().run_p(lambda subprocess: 1)
    promise2 = Pyjo.IOLoop.subprocess().run_p(lambda subprocess: 2)

    def then(*values):
        global result
        result = [value[0] for value in values]

    def catch(err):
        global fail
        fail = err

    Pyjo.Promise.all(promise, promise2).then(then).catch(catch).wait()
    ok(not fail, 'no error')
    is_deeply_ok(result, [1, 2], 'right structure')

with subtest('No result'):
    fail = result = None

    def parent(subprocess, err, *results):
        global fail, result
        fail = err
        result = list(results)

    Pyjo.IOLoop.Subprocess.new().run(lambda subprocess: None, parent)
    Pyjo.IOLoop.start()
    ok(not fail, 'no error')
    is_deeply_ok(result, [], 'right structure')

with subtest('Stream inherited from previous subprocesses'):
    fail = None
    result = []
    promises = []
    me = os.getpid()
    for _ in range(2):
        promise = Pyjo.Promise.new()
        promises.append(promise)
        subprocess = Pyjo.IOLoop.Subprocess.new()

        def parent(subprocess, err, two=None, promise=promise):
            global fail
            fail = fail or err
            result.append(two)
            is_ok(me, os.getpid(), 'we are the parent')
            promise.resolve()

        subprocess.run(lambda subprocess: 1 + 1, parent)
    Pyjo.Promise.all(*promises).wait()
    ok(not fail, 'no error')
    is_deeply_ok(result, [2, 2], 'right structure')

with subtest('Exception'):
    fail = None

    def parent(subprocess, err, *results):
        global fail
        fail = err

    Pyjo.IOLoop.Subprocess.new().run(lambda subprocess: Pyjo.Exception.object.throw('Whatever'), parent)
    Pyjo.IOLoop.start()
    like_ok(fail, r'Whatever', 'right error')

with subtest('Non-zero exit status'):
    fail = None
    subprocess = Pyjo.IOLoop.Subprocess.new()

    def parent(subprocess, err, *results):
        global fail
        fail = err

    subprocess.run(lambda subprocess: sys.exit(3), parent)
    Pyjo.IOLoop.start()
    is_ok(subprocess.exit_code, 3, 'right exit code')
    # Unlike Mojolicious: the message of the json module for no input, where Mojo::JSON names the offset
    like_ok(fail, r'char 0', 'right error')

with subtest('Serialization error'):
    fail = None
    subprocess = Pyjo.IOLoop.Subprocess.new()
    subprocess.deserialize = lambda data: Pyjo.Exception.object.throw('Whatever')

    def parent(subprocess, err, *results):
        global fail
        fail = err

    subprocess.run(lambda subprocess: 1 + 1, parent)
    Pyjo.IOLoop.start()
    like_ok(fail, r'Whatever', 'right error')

with subtest('Progress'):
    fail = result = None
    progress = []
    subprocess = Pyjo.IOLoop.Subprocess.new()

    def child(s):
        s.progress(20)
        s.progress({'percentage': 45})
        s.progress({'percentage': 90}, {'long_data': list(range(1, 100001))})
        return 'yay'

    def parent(subprocess, err, *res):
        global fail, result
        fail = err
        result = list(res)

    subprocess.run(child, parent)
    subprocess.on('progress', lambda subprocess, *args: progress.append(list(args)))
    Pyjo.IOLoop.start()
    ok(not fail, 'no error')
    is_deeply_ok(result, ['yay'], 'correct result')
    is_deeply_ok(
        progress,
        [[20], [{'percentage': 45}], [{'percentage': 90}, {'long_data': list(range(1, 100001))}]],
        'correct progress',
    )

with subtest('Cleanup'):
    fail = result = None
    file = tempfile()
    called = 0
    subprocess = Pyjo.IOLoop.Subprocess.new()

    def cleanup(subprocess):
        global called
        called += 1
        file.spew(subprocess.serialize({'test': called}))

    subprocess.on('cleanup', cleanup)

    def parent(subprocess, err, hello=None):
        global fail, result
        fail = err
        result = hello

    subprocess.run(lambda subprocess: 'Hello Mojo!', parent)
    Pyjo.IOLoop.start()
    is_deeply_ok(subprocess.deserialize(file.slurp()), {'test': 1}, 'cleanup event emitted once')
    ok(not fail, 'no error')
    is_ok(result, 'Hello Mojo!', 'right result')

done_testing()
