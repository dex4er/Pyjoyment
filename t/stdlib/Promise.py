import Pyjo.Exception
import Pyjo.IOLoop
import Pyjo.Promise
import Pyjo.Reactor.Asyncio

from Pyjo.Test import *

import asyncio
import gc
import os
import subprocess
import sys
import warnings


# The tests of asyncio need the reactor of asyncio, whatever PYJO_REACTOR says
Pyjo.IOLoop.singleton.reactor = Pyjo.Reactor.Asyncio.new()

with subtest('await in an asyncio task'):

    async def main():
        got = [
            await Pyjo.Promise.resolve('one'),
            await Pyjo.Promise.resolve('a', 'b'),
            await Pyjo.Promise.resolve(),
            await Pyjo.Promise.timer(0.01, 'timer'),
        ]
        try:
            await Pyjo.Promise.reject(KeyError('key'))
        except KeyError as e:
            got.append(type(e).__name__)
        try:
            await Pyjo.Promise.reject('reason', 'more')
        except Pyjo.Exception.object as e:
            got.append(e.message)
        return got

    is_deeply_ok(
        asyncio.run(main()),
        ['one', ('a', 'b'), None, 'timer', 'KeyError', 'reason'],
        'values, tuple, None, and exceptions',
    )

with subtest('asyncio.gather'):

    async def gather():
        return await asyncio.gather(Pyjo.Promise.timer(0.01, 'promise'), asyncio.sleep(0, 'coroutine'))

    is_deeply_ok(asyncio.run(gather()), ['promise', 'coroutine'], 'promises and coroutines together')

with subtest('A coroutine with asyncio in a promise'):

    @Pyjo.Promise.async_
    async def slow(value):
        await asyncio.sleep(0.01)
        return await Pyjo.Promise.timer(0.01, value)

    got = []
    slow('done').then(got.append).wait()
    is_deeply_ok(got, ['done'], 'wait runs the loop until the task is done')

    @Pyjo.Promise.async_
    async def nothing():
        await asyncio.sleep(0)

    got = []
    nothing().then(lambda *values: got.append(values)).wait()
    is_deeply_ok(got, [()], 'None is no value')

    @Pyjo.Promise.async_
    async def fails():
        await asyncio.sleep(0)
        raise ValueError('Oops')

    got = []
    fails().catch(got.append).wait()
    isa_ok(got[0], ValueError, 'rejected with the exception')

with subtest('A coroutine without asyncio'):
    code = """
import asyncio, Pyjo.Promise

@Pyjo.Promise.async_
async def twice(value):
    first = await Pyjo.Promise.timer(0.01, value)
    return first * 2

@Pyjo.Promise.async_
async def foreign():
    await asyncio.sleep(0)

got = []
twice(21).then(got.append).wait()
foreign().catch(lambda e: got.append(type(e).__name__)).wait()
print(got)
"""
    env = dict(os.environ, PYJO_REACTOR='Pyjo.Reactor.Poll')
    result = subprocess.run([sys.executable, '-c', code], env=env, capture_output=True, text=True)
    is_ok(result.stdout, "[42, 'TypeError']\n", 'promises of Pyjoyment only')

with subtest('warnings'):
    with warnings.catch_warnings(record=True) as warn:
        warnings.simplefilter('always')
        Pyjo.Promise.reject('Oops')
        gc.collect()
        is_ok(len(warn), 1, 'one warning')
        is_ok(warn[0].category, UserWarning, 'UserWarning')
        is_ok(str(warn[0].message), 'Unhandled rejected promise: Oops', 'message')

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        Pyjo.Promise.reject('Ignored')
        gc.collect()
        pass_ok('warnings can be ignored')

done_testing()
