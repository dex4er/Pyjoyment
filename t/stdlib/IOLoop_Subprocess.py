from Pyjo.Test import *

import os
import subprocess
import sys


if not hasattr(os, 'fork'):
    plan(skip_all='no os.fork')

# PyPy with its JIT on macOS: the child of a fork crashes now and then with a bus error, under load
if sys.platform == 'darwin' and getattr(sys, 'pypy_translation_info', {}).get('translation.jit'):
    plan(skip_all='PyPy with its JIT on macOS: the child of a fork crashes now and then with SIGBUS')

import Pyjo.IOLoop
import Pyjo.IOLoop.Subprocess
import Pyjo.Reactor.Asyncio

import asyncio
import datetime
import pickle


ROOT = os.path.join(os.path.dirname(__file__), '..', '..')


# A script in a process of its own, with its output and the errors of the deprecations of Python
def script(code):
    env = dict(os.environ, PYTHONPATH=ROOT, PYTHONWARNINGS='error::DeprecationWarning')
    return subprocess.run([sys.executable, '-c', code], env=env, capture_output=True, text=True)


with subtest('Results and progress of pickle'):
    now = datetime.datetime.now(datetime.UTC)
    progress = []
    got = []
    sub = Pyjo.IOLoop.Subprocess.new(serialize=pickle.dumps, deserialize=pickle.loads)
    sub.on('progress', lambda sub, *data: progress.extend(data))

    def child(sub):
        sub.progress({1, 2}, b'bytes')
        return now, ('a', 'b')

    sub.run(child, lambda sub, err, *results: got.extend([err, *results]))
    Pyjo.IOLoop.start()
    is_deeply_ok(progress, [{1, 2}, b'bytes'], 'a set and bytes')
    is_deeply_ok(got, [None, now, ('a', 'b')], 'a datetime and a tuple')

with subtest('await in an asyncio task'):
    Pyjo.IOLoop.singleton.reactor = Pyjo.Reactor.Asyncio.new()

    async def main():
        return await Pyjo.IOLoop.subprocess().run_p(lambda sub: os.getpid())

    pid = asyncio.run(main())
    ok(pid and pid != os.getpid(), 'value of another process')

with subtest('Fork after a name resolution'):
    result = script("""
import Pyjo.IOLoop, threading

got = []
Pyjo.IOLoop.client(lambda loop, err, stream: loop.stop(), address='localhost', port=1)
Pyjo.IOLoop.start()
got.append(any(t.name.startswith('Pyjo.IOLoop.Client') for t in threading.enumerate()))

def child(sub):
    res = []
    Pyjo.IOLoop.client(lambda loop, err, stream: (res.append(err is not None), loop.stop()), address='localhost', port=1)
    Pyjo.IOLoop.start()
    return res[0]

Pyjo.IOLoop.subprocess(child, lambda sub, err, *results: (got.append((err, *results)), Pyjo.IOLoop.stop()))
Pyjo.IOLoop.start()
print(got)
""")
    is_ok(result.stdout, '[True, (None, True)]\n', 'the threads of the resolver are stopped, the child resolves again')
    unlike_ok(result.stderr, r'Warning', 'no warning of a fork with threads')

with subtest('Output of the parent and the child'):
    result = script("""
import Pyjo.IOLoop

print('before')
Pyjo.IOLoop.subprocess(lambda sub: print('child'), lambda sub, err, *results: Pyjo.IOLoop.stop())
Pyjo.IOLoop.start()
print('after')
""")
    is_ok(result.stdout, 'before\nchild\nafter\n', 'written once, in order')

done_testing()
