import Pyjo.IOLoop
import Pyjo.Promise

from Pyjo.Test import *
from Pyjo.Util import warn

import gc
import warnings


# Left out from Mojolicious: plan skip_all unless TEST_ASYNC_AWAIT, as the coroutines of Python need nothing more

# Left out from Mojolicious: test_awaitable of Test::Future::AsyncAwait::Awaitable, the API of Future::AsyncAwait is
# __await__ in Python, which t/stdlib/Promise.py checks with asyncio

# TODO: the application, its routes, the user agent and Test::Mojo, when Pyjoyment.Lite, Pyjo.UserAgent and Test::Mojo
# are ported


# Not in Mojolicious: Perl frees a promise at the end of the statement, PyPy when its garbage collector runs, which
# takes more than one run for a promise that is rejected with an exception, as its traceback refers to the promise
def collect():
    for _ in range(3):
        gc.collect()


@Pyjo.Promise.coroutine
async def await_then_return_promise(method):
    return Pyjo.Promise.resolve(await getattr(Pyjo.Promise, method)(0.01, method))


@Pyjo.Promise.coroutine
async def reject_p():
    await Pyjo.Promise.reject('Rejected promise')


@Pyjo.Promise.coroutine
async def test_three(ok):
    def cb(resolve, reject):
        Pyjo.IOLoop.next_tick(lambda loop: (resolve if ok else reject)('value'))

    return Pyjo.Promise.new(cb)


# Left out from Mojolicious: "Basic async/await" and "Multiple awaits", which need the user agent

# Left out from Mojolicious: "Application with async/await action" and "Exception handling and async/await", which
# need the application

with subtest('Exception handling with file and line reporting'):
    error = None

    def error_cb(err):
        global error
        error = err

    reject_p().catch(error_cb).wait()
    # Unlike Mojolicious: the exception of Python keeps the file and the line in its traceback, not in its message
    like_ok(str(error), r'^Rejected promise$', 'right content')

with subtest('Exception handling without "Unhandled rejected promise" warning'):
    error = None
    with warnings.catch_warnings(record=True) as warn:
        warnings.simplefilter('always')
        reject_p().catch(error_cb).wait()
        collect()
        like_ok(str(error), r'^Rejected promise', 'right content')
        is_ok(len(warn), 0, 'no waring')
        warn.clear()
        reject_p().wait()
        collect()
        like_ok(' '.join(str(w.message) for w in warn), r'Unhandled rejected promise', 'unhandled promise')

# Left out from Mojolicious: "Runaway exception", which needs the application

with subtest('Async function body returning a promise'):
    text = None

    def text_cb(value):
        global text
        text = value

    test_three(True).then(text_cb).catch(lambda *reason: warn(str(reason))).wait()
    is_ok(text, 'value', 'right content')
    text = None
    test_three(False).then(lambda *values: warn(str(values))).catch(text_cb).wait()
    is_ok(text, 'value', 'right content')

with subtest('Async nested function returning a promise'):
    res = None

    def res_cb(value):
        global res
        res = value

    await_then_return_promise('timer').then(res_cb).catch(res_cb).wait()
    is_ok(res, 'timer', 'right content')
    await_then_return_promise('timeout').then(res_cb).catch(res_cb).wait()
    # Unlike Mojolicious: the exception of Python keeps the file and the line in its traceback, not in its message
    like_ok(str(res), r'^timeout', 'right content')

# Left out from Mojolicious: "Async WebSocket", which needs the application


# Top-level await
# Not in Mojolicious: Python awaits in a coroutine only, which runs as a promise
@Pyjo.Promise.coroutine
async def top_level():
    is_ok(await Pyjo.Promise.resolve('works'), 'works', 'top-level await resolved')
    is_deeply_ok(list(await Pyjo.Promise.resolve('just', 'works')), ['just', 'works'], 'top-level await resolved')
    try:
        await Pyjo.Promise.reject('works too')
    except Exception as e:
        like_ok(str(e), r'works too', 'top-level await rejected')


top_level().wait()

done_testing()
