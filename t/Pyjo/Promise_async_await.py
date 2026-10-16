import Pyjo.IOLoop
import Pyjo.Promise
import Pyjo.Test.Pyjo
import Pyjo.UserAgent

from Pyjo.Test import *
from Pyjo.Util import warn
from Pyjoyment.Lite import *

import gc
import warnings


# Left out from Mojolicious: plan skip_all unless TEST_ASYNC_AWAIT, as the coroutines of Python need nothing more

# Left out from Mojolicious: test_awaitable of Test::Future::AsyncAwait::Awaitable, the API of Future::AsyncAwait is
# __await__ in Python, which t/stdlib/Promise.py checks with asyncio

# Silence
app.log.level = 'fatal'


@helper('defer_resolve_p')
def defer_resolve_p(c, msg):
    promise = Pyjo.Promise.new()
    Pyjo.IOLoop.next_tick(lambda loop: promise.resolve(msg))
    return promise


@helper('defer_reject_p')
def defer_reject_p(c, msg):
    promise = Pyjo.Promise.new()
    Pyjo.IOLoop.next_tick(lambda loop: promise.reject(msg))
    return promise


get('/one', {'text': 'works!'})

get('/two', {'text': 'also'})


@get('/three')
async def three(c):
    first = await c.defer_resolve_p('this ')
    second = await c.defer_resolve_p('works')
    third = await c.defer_resolve_p(' too!')
    c.render(text=f'{first}{second}{third}')


@get('/four')
async def four(c):
    text = await Pyjo.Promise.resolve('fail')
    try:
        await c.defer_reject_p('this went perfectly')
        err = None
    except Exception as e:
        err = e
    if err is not None:
        c.render(text=str(err), status=500)
    else:
        c.render(text=text)


@get('/five')
async def five(c):
    runaway = c.defer_reject_p('runaway too')
    await c.defer_resolve_p('fail')
    await runaway


@get('/six')
def six(c):
    @c.on('message')
    @Pyjo.Promise.coroutine
    async def message(c, msg):
        first = await c.defer_resolve_p(f'One: {msg}')
        second = await c.defer_resolve_p(f'Two: {msg}')
        c.send(f'{first} {second}').finish()


ua = Pyjo.UserAgent.new(ioloop=Pyjo.IOLoop.singleton)


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
async def test_one():
    return await ua.get_p('/one')


@Pyjo.Promise.coroutine
async def test_two(separator):
    text = ''
    two = await ua.get_p('/two')
    text += two.res.text
    one = await ua.get_p('/one')
    text += separator + one.res.text

    return text


@Pyjo.Promise.coroutine
async def test_three(ok):
    def cb(resolve, reject):
        Pyjo.IOLoop.next_tick(lambda loop: (resolve if ok else reject)('value'))

    return Pyjo.Promise.new(cb)


t = Pyjo.Test.Pyjo.new()

with subtest('Basic async/await'):
    promise = test_one()
    isa_ok(promise, Pyjo.Promise.object, 'right class')
    tx = None

    def tx_cb(value):
        global tx
        tx = value

    promise.then(tx_cb).catch(lambda *reason: warn(str(reason)))
    promise.wait()
    is_ok(tx.res.text, 'works!', 'right content')

with subtest('Multiple awaits'):
    text = None

    def text_cb(value):
        global text
        text = value

    test_two(' ').then(text_cb).catch(lambda *reason: warn(str(reason))).wait()
    is_ok(text, 'also works!', 'right content')

with subtest('Application with async/await action'):
    t.get_ok('/three').content_is('this works too!')

with subtest('Exception handling and async/await'):
    t.get_ok('/four').status_is(500).content_like(r'this went perfectly')

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

with subtest('Runaway exception'):
    t.get_ok('/five').status_is(500).content_like(r'runaway too')

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

with subtest('Async WebSocket'):
    t.websocket_ok('/six').send_ok('test').message_ok().message_is('One: test Two: test').finish_ok()


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
