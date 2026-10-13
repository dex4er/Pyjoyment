import Pyjo.IOLoop
import Pyjo.Promise

from Pyjo.Test import *

import gc
import warnings


# Left out from Mojolicious: BEGIN { $ENV{MOJO_REACTOR} = 'Mojo::Reactor::Poll' }, the tests run on the reactor that
# Pyjo.Reactor.detect() gives


# sub { @target = @_ }
def store(target):
    def cb(*values):
        target[:] = values

    return cb


# sub { push @target, @prefix, @_ }
def push(target, *prefix):
    def cb(*values):
        target.extend([*prefix, *values])

    return cb


with subtest('Resolved'):
    promise = Pyjo.Promise.new()
    results, errors = [], []
    promise.then(store(results), store(errors))
    promise.resolve('hello', 'world')
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(results, ['hello', 'world'], 'promise resolved')
    is_deeply_ok(errors, [], 'promise not rejected')

    promise = Pyjo.Promise.resolve('test')
    promise.then(store(results), store(errors))
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(results, ['test'], 'promise resolved')
    is_deeply_ok(errors, [], 'promise not rejected')

with subtest('Already resolved'):
    promise = Pyjo.Promise.new().resolve('early')
    results, errors = [], []
    promise.then(store(results), store(errors))
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(results, ['early'], 'promise resolved')
    is_deeply_ok(errors, [], 'promise not rejected')

with subtest('Resolved with finally'):
    promise = Pyjo.Promise.new()
    results = []

    def finally_cb():
        results[:] = ['finally']
        return 'fail'

    promise.finally_(finally_cb).then(push(results))
    promise.resolve('hello', 'world')
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(results, ['finally', 'hello', 'world'], 'promise settled')

with subtest('Rejected'):
    promise = Pyjo.Promise.new()
    results, errors = [], []
    promise.then(store(results), store(errors))
    promise.reject('bye', 'world')
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(results, [], 'promise not resolved')
    is_deeply_ok(errors, ['bye', 'world'], 'promise rejected')

    promise = Pyjo.Promise.reject('test')
    promise.then(store(results), store(errors))
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(results, [], 'promise not resolved')
    is_deeply_ok(errors, ['test'], 'promise rejected')

with subtest('Rejected early'):
    promise = Pyjo.Promise.new().reject('early')
    results, errors = [], []
    promise.then(store(results), store(errors))
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(results, [], 'promise not resolved')
    is_deeply_ok(errors, ['early'], 'promise rejected')

with subtest('Rejected with finally'):
    promise = Pyjo.Promise.new()
    errors = []

    def finally_cb():
        errors[:] = ['finally']
        return 'fail'

    promise.finally_(finally_cb).then(None, push(errors))
    promise.reject('bye', 'world')
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(errors, ['finally', 'bye', 'world'], 'promise settled')

with subtest('Wrap'):
    results, errors = [], []

    def resolving(resolve, reject):
        Pyjo.IOLoop.timer(0, lambda loop: resolve('resolved', '!'))

    promise = Pyjo.Promise.new(resolving)
    promise.then(store(results), store(errors)).wait()
    is_deeply_ok(results, ['resolved', '!'], 'promise resolved')
    is_deeply_ok(errors, [], 'promise not rejected')

    results, errors = [], []

    def rejecting(resolve, reject):
        Pyjo.IOLoop.timer(0, lambda loop: reject('rejected', '!'))

    promise = Pyjo.Promise.new(rejecting)
    promise.then(store(results), store(errors)).wait()
    is_deeply_ok(results, [], 'promise not resolved')
    is_deeply_ok(errors, ['rejected', '!'], 'promise rejected')

with subtest('No state change'):
    promise = Pyjo.Promise.new()
    results, errors = [], []
    promise.then(store(results), store(errors))
    promise.resolve('pass').reject('fail').resolve('fail')
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(results, ['pass'], 'promise resolved')
    is_deeply_ok(errors, [], 'promise not rejected')

with subtest('Resolved chained'):
    promise = Pyjo.Promise.new()
    results = []
    promise.then(lambda value: f'{value}:1').then(lambda value: f'{value}:2').then(lambda value: f'{value}:3').then(
        lambda value: results.append(f'{value}:4')
    )
    promise.resolve('test')
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(results, ['test:1:2:3:4'], 'promises resolved')

with subtest('Rejected chained'):
    promise = Pyjo.Promise.new()
    errors = []
    promise.then(None, lambda reason: f'{reason}:1').then(
        lambda value: f'{value}:2', lambda reason: f'{reason}:fail'
    ).then(lambda value: f'{value}:3').then(lambda value: errors.append(f'{value}:4'))
    promise.reject('tset')
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(errors, ['tset:1:2:3:4'], 'promises rejected')

with subtest('Resolved nested'):
    promise = Pyjo.Promise.new()
    promise2 = Pyjo.Promise.new()
    results = []
    promise.then(lambda *values: promise2).then(store(results))
    promise.resolve()
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(results, [], 'promise not resolved')

    promise2.resolve('works too')
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(results, ['works too'], 'promise resolved')

with subtest('Rejected nested'):
    promise = Pyjo.Promise.new()
    promise2 = Pyjo.Promise.new()
    errors = []
    promise.then(None, lambda *reason: promise2).then(None, store(errors))
    promise.reject()
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(errors, [], 'promise not resolved')

    promise2.reject('hello world')
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(errors, ['hello world'], 'promise rejected')

with subtest('Double finally'):
    promise = Pyjo.Promise.new()
    results = []
    promise.finally_(lambda: results.append('finally1')).finally_(lambda: results.append('finally2'))
    promise.resolve('pass')
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(results, ['finally1', 'finally2'], 'promise not resolved')

with subtest('Promise returned by finally'):
    loop = Pyjo.IOLoop.new()
    promise = Pyjo.Promise.new().set(ioloop=loop)
    promise2 = Pyjo.Promise.new().set(ioloop=loop)
    results = []

    def finally_cb():
        loop.next_tick(lambda loop: promise2.resolve())
        return promise2

    def finally2_cb():
        results[:] = ['finally']

    promise3 = promise.finally_(finally_cb).finally_(finally2_cb)
    promise.resolve('pass')
    promise3.wait()
    is_deeply_ok(results, ['finally'], 'promise already resolved')

with subtest('Promise returned by finally'):
    promise = Pyjo.Promise.new()
    promise2 = Pyjo.Promise.new()
    results = []

    def finally_cb():
        Pyjo.IOLoop.next_tick(lambda loop: promise2.resolve())
        return promise2

    promise3 = promise.finally_(finally_cb).finally_(finally2_cb)
    promise.resolve('pass')
    promise3.wait()
    is_deeply_ok(results, ['finally'], 'promise already resolved')

with subtest('Promise returned by finally (rejected)'):
    promise = Pyjo.Promise.new()
    promise2 = Pyjo.Promise.new()
    results, errors = [], []

    def finally_cb():
        Pyjo.IOLoop.next_tick(lambda loop: promise2.reject('works'))
        return promise2

    promise3 = promise.finally_(finally_cb).then(store(results), store(errors))
    promise.resolve('failed')
    promise3.wait()
    is_deeply_ok(results, [], 'promises not resolved')
    is_deeply_ok(errors, ['works'], 'promises rejected')

with subtest('Exception in finally'):
    promise = Pyjo.Promise.new()
    results = []

    def finally_cb():
        raise Exception('Test!\n')

    promise.finally_(finally_cb).catch(push(results))
    promise.resolve('pass')
    Pyjo.IOLoop.one_tick()
    # Unlike Mojolicious: the reason is the exception, Perl's is its message
    is_deeply_ok([str(e) for e in results], ['Test!\n'], 'promise rejected')

with subtest('Clone'):
    loop = Pyjo.IOLoop.new()
    promise = Pyjo.Promise.new().set(ioloop=loop).resolve('failed')
    promise2 = promise.clone()
    results, errors = [], []
    promise2.then(store(results), store(errors))
    promise2.resolve('success')
    is_ok(loop, promise2.ioloop, 'same loop')
    loop.one_tick()
    is_deeply_ok(results, ['success'], 'promise resolved')
    is_deeply_ok(errors, [], 'promise not rejected')

with subtest('Exception in chain'):
    promise = Pyjo.Promise.new()
    results, errors = [], []

    def die_cb(value):
        raise Exception(f'test: {value}\n')

    promise.then(lambda value: value).then(lambda value: value).then(die_cb).then(
        lambda *values: results.append('fail')
    ).catch(store(errors))
    promise.resolve('works')
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(results, [], 'promises not resolved')
    # Unlike Mojolicious: the reason is the exception, Perl's is its message
    is_deeply_ok([str(e) for e in errors], ['test: works\n'], 'promises rejected')

with subtest('Race'):
    promise = Pyjo.Promise.new().then(lambda value: value)
    promise2 = Pyjo.Promise.new().then(lambda value: value)
    promise3 = Pyjo.Promise.new().then(lambda value: value)
    results = []
    Pyjo.Promise.race(promise2, promise, promise3).then(store(results))
    promise2.resolve('second')
    promise3.resolve('third')
    promise.resolve('first')
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(results, ['second'], 'promise resolved')

with subtest('Rejected race'):
    promise = Pyjo.Promise.new().then(lambda value: value)
    promise2 = Pyjo.Promise.new().then(lambda value: value)
    promise3 = Pyjo.Promise.new().then(lambda value: value)
    results, errors = [], []
    Pyjo.Promise.race(promise, promise2, promise3).then(store(results), store(errors))
    promise2.reject('second')
    promise3.resolve('third')
    promise.resolve('first')
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(results, [], 'promises not resolved')
    is_deeply_ok(errors, ['second'], 'promise rejected')

with subtest('Any'):
    promise = Pyjo.Promise.new().then(lambda value: value)
    promise2 = Pyjo.Promise.new().then(lambda value: value)
    promise3 = Pyjo.Promise.new().then(lambda value: value)
    results = []
    Pyjo.Promise.any(promise2, promise, promise3).then(store(results))
    promise2.reject('second')
    promise3.resolve('third')
    promise.resolve('first')
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(results, ['third'], 'promise resolved')

with subtest('Any (all rejections)'):
    promise = Pyjo.Promise.new().then(lambda value: value)
    promise2 = Pyjo.Promise.new().then(lambda value: value)
    promise3 = Pyjo.Promise.new().then(lambda value: value)
    results, errors = [], []
    Pyjo.Promise.any(promise, promise2, promise3).then(store(results), store(errors))
    promise2.reject('second')
    promise3.reject('third')
    promise.reject('first')
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(results, [], 'promises not resolved')
    is_deeply_ok(errors, [['first'], ['second'], ['third']], 'promises rejected')

with subtest('Timeout'):
    errors, results = [], []
    promise = Pyjo.Promise.timeout(0.25, 'Timeout1')
    promise2 = Pyjo.Promise.new().timeout(0.025, 'Timeout2')
    promise3 = Pyjo.Promise.race(promise, promise2).then(store(results)).catch(store(errors)).wait()
    is_deeply_ok(results, [], 'promises not resolved')
    is_deeply_ok(errors, ['Timeout2'], 'promise rejected')

with subtest('Timeout with default message'):
    errors = []
    Pyjo.Promise.timeout(0.025).catch(store(errors)).wait()
    is_deeply_ok(errors, ['Promise timeout'], 'default timeout message')

with subtest('Timer without value'):
    results = []
    Pyjo.Promise.timer(0.025).then(lambda *values: results.extend([*values, 'works!'])).wait()
    is_deeply_ok(results, ['works!'], 'default timer result')

with subtest('Timer with values'):
    results = []
    Pyjo.Promise.new().timer(0, 'first', 'second').then(lambda *values: results.extend([*values, 'works too!'])).wait()
    is_deeply_ok(results, ['first', 'second', 'works too!'], 'timer result')

with subtest('All'):
    promise = Pyjo.Promise.new().then(lambda value: value)
    promise2 = Pyjo.Promise.new().then(lambda value: value)
    promise3 = Pyjo.Promise.new().then(lambda value: value)
    results = []
    Pyjo.Promise.all(promise, promise2, promise3).then(store(results))
    promise2.resolve('second')
    promise3.resolve('third')
    promise.resolve('first')
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(results, [['first'], ['second'], ['third']], 'promises resolved')

with subtest('Rejected all'):
    promise = Pyjo.Promise.new().then(lambda value: value)
    promise2 = Pyjo.Promise.new().then(lambda value: value)
    promise3 = Pyjo.Promise.new().then(lambda value: value)
    results, errors = [], []
    Pyjo.Promise.all(promise, promise2, promise3).then(store(results), store(errors))
    promise2.resolve('second')
    promise3.reject('third')
    promise.resolve('first')
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(results, [], 'promises not resolved')
    is_deeply_ok(errors, ['third'], 'promise rejected')

with subtest('All settled'):
    promise = Pyjo.Promise.new().then(lambda value: value)
    promise2 = Pyjo.Promise.new().then(lambda value: value)
    promise3 = Pyjo.Promise.new().then(lambda value: value)
    results = []
    Pyjo.Promise.all_settled(promise, promise2, promise3).then(store(results))
    promise2.resolve('second')
    promise3.resolve('third')
    promise.resolve('first')
    Pyjo.IOLoop.one_tick()
    result = [
        {'status': 'fulfilled', 'value': ['first']},
        {'status': 'fulfilled', 'value': ['second']},
        {'status': 'fulfilled', 'value': ['third']},
    ]
    is_deeply_ok(results, result, 'promise resolved')

with subtest('All settled (with rejection)'):
    promise = Pyjo.Promise.new().then(lambda value: value)
    promise2 = Pyjo.Promise.new().then(lambda value: value)
    promise3 = Pyjo.Promise.new().then(lambda value: value)
    results, errors = [], []
    Pyjo.Promise.all_settled(promise, promise2, promise3).then(store(results), store(errors))
    promise2.resolve('second')
    promise3.reject('third')
    promise.resolve('first')
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(errors, [], 'promise not rejected')
    result = [
        {'status': 'fulfilled', 'value': ['first']},
        {'status': 'fulfilled', 'value': ['second']},
        {'status': 'rejected', 'reason': ['third']},
    ]
    is_deeply_ok(results, result, 'promise resolved')

with subtest('Settle with promise'):
    promise = Pyjo.Promise.new().resolve('works')
    results = []

    def first_cb(*values):
        results.extend(['first', *values])
        return Pyjo.Promise.resolve(*values)

    promise2 = Pyjo.Promise.new().resolve(promise).then(first_cb)
    promise2.then(push(results, 'second'))
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(results, ['first', 'works', 'second', 'works'], 'promises resolved')

    promise = Pyjo.Promise.new().reject('works too')
    errors = []
    results = []
    promise2 = Pyjo.Promise.new().reject(promise).catch(push(errors, 'first'))
    promise2.then(push(results, 'second'))
    Pyjo.IOLoop.one_tick()
    is_deeply_ok(errors, ['first', promise], 'promises rejected')
    is_deeply_ok(results, ['second'], 'promises resolved')
    promise.catch(lambda *reason: None)

with subtest('Promisify'):
    is_ok(type(Pyjo.Promise.resolve('foo')), Pyjo.Promise.object, 'right class')

    promise = Pyjo.Promise.reject('foo')
    is_ok(type(promise), Pyjo.Promise.object, 'right class')
    errors = []
    promise.catch(push(errors)).wait()
    is_deeply_ok(errors, ['foo'], 'promise rejected')

    promise = Pyjo.Promise.resolve('foo')
    ok(Pyjo.Promise.resolve(promise) is promise, 'same object')

    promise = Pyjo.Promise.resolve('foo')
    ok(Pyjo.Promise.new().resolve(promise) is not promise, 'different object')

    promise = Pyjo.Promise.reject('foo')
    ok(Pyjo.Promise.resolve(promise) is promise, 'same object')
    errors = []
    promise.catch(push(errors)).wait()
    is_deeply_ok(errors, ['foo'], 'promise rejected')

with subtest('Warnings'):
    with warnings.catch_warnings(record=True) as warn:
        warnings.simplefilter('always')
        Pyjo.Promise.reject('one')
        # Not in Mojolicious: Perl frees the promise at the end of the statement, PyPy when its garbage collector runs
        gc.collect()
        like_ok(str(warn[0].message), r'Unhandled rejected promise: one', 'unhandled')
        is_ok(len(warn), 1, 'no more warnings')

        warn.clear()
        Pyjo.Promise.reject('two').then(lambda *values: None).wait()
        gc.collect()
        like_ok(str(warn[0].message), r'Unhandled rejected promise: two', 'unhandled')
        is_ok(len(warn), 1, 'no more warnings')

        warn.clear()
        Pyjo.Promise.reject('three').finally_(lambda: None).wait()
        gc.collect()
        like_ok(str(warn[0].message), r'Unhandled rejected promise: three', 'unhandled')
        is_ok(len(warn), 1, 'no more warnings')

        warn.clear()
        promise = Pyjo.Promise.new()
        promise.reject('four')
        Pyjo.IOLoop.one_tick()
        gc.collect()
        is_ok(len(warn), 0, 'no warnings')
        del promise
        gc.collect()
        like_ok(str(warn[0].message), r'Unhandled rejected promise: four', 'unhandled')
        is_ok(len(warn), 1, 'no more warnings')

with subtest('Warnings (multiple branches)'):
    with warnings.catch_warnings(record=True) as warn:
        warnings.simplefilter('always')
        errors = []
        promise = Pyjo.Promise.new()
        promise.catch(push(errors))
        promise.reject('branches')
        promise.wait()
        gc.collect()
        is_deeply_ok(errors, ['branches'], 'promise rejected')
        is_ok(len(warn), 0, 'no warnings')

        errors.clear()
        warn.clear()
        promise = Pyjo.Promise.new()
        promise.catch(push(errors))
        promise.then(lambda *values: None)
        promise.reject('branches2')
        promise.wait()
        gc.collect()
        is_deeply_ok(errors, ['branches2'], 'promise rejected')
        like_ok(str(warn[0].message), r'Unhandled rejected promise: branches2', 'unhandled')
        is_ok(len(warn), 1, 'no more warnings')

        warn.clear()
        promise = Pyjo.Promise.new()
        promise.then(lambda *values: None).then(lambda *values: None).then(lambda *values: None)
        promise.then(lambda *values: None)
        promise.reject('branches3')
        promise.wait()
        gc.collect()
        like_ok(str(warn[0].message), r'Unhandled rejected promise: branches3', 'unhandled')
        like_ok(str(warn[1].message), r'Unhandled rejected promise: branches3', 'unhandled')
        is_ok(len(warn), 2, 'no more warnings')

with subtest('Map'):
    results, errors, started = [], [], []

    def start_cb(item):
        started.append(item)
        return Pyjo.Promise.resolve(item)

    promise = Pyjo.Promise.map(start_cb, 1, 2, 3, 4, 5, None, 0).then(store(results), store(errors))
    is_deeply_ok(started, [1, 2, 3, 4, 5, None, 0], 'all started without concurrency')
    promise.wait()
    is_deeply_ok(results, [[1], [2], [3], [4], [5], [None], [0]], 'correct result')
    is_deeply_ok(errors, [], 'promise not rejected')

with subtest('Map (with concurrency limit)'):
    concurrent = 0
    results, errors = [], []

    def limited_cb(n):
        global concurrent
        concurrent += 1
        if concurrent > 3:
            fail_ok('Concurrency too high')

        def then_cb(*values):
            global concurrent
            if concurrent > 3:
                fail_ok('Concurrency too high')
            concurrent -= 1
            # Not in Mojolicious: None is no value, a promise of it is one
            return Pyjo.Promise.resolve(n)

        return Pyjo.Promise.resolve().then(then_cb)

    Pyjo.Promise.map(limited_cb, 1, 2, 3, 4, 5, 6, 7, None, 0, concurrency=3).then(store(results), store(errors)).wait()
    is_deeply_ok(results, [[1], [2], [3], [4], [5], [6], [7], [None], [0]], 'correct result')
    is_deeply_ok(errors, [], 'promise not rejected')

with subtest('Map (with reject)'):
    results, errors, started = [], [], []

    def reject_cb(n):
        started.append(n)
        return Pyjo.Promise.resolve().then(lambda *values: Pyjo.Promise.reject(n))

    Pyjo.Promise.map(reject_cb, 1, 2, 3, 4, 5, concurrency=3).then(store(results), store(errors)).wait()
    is_deeply_ok(results, [], 'promise not resolved')
    is_deeply_ok(errors, [1], 'correct errors')
    is_deeply_ok(started, [1, 2, 3], 'only initial batch started')

with subtest('Map (custom event loop)'):
    done = False
    loop = Pyjo.IOLoop.new()
    promise = Pyjo.Promise.map(lambda item: Pyjo.Promise.new().set(ioloop=loop).resolve(), 1)
    is_ok(promise.ioloop, loop, 'same loop')
    isnt_ok(promise.ioloop, Pyjo.IOLoop.singleton, 'not the singleton')

    def done_cb(*values):
        global done
        done = True
        loop.stop()

    promise.then(done_cb)
    loop.start()
    ok(done, 'loop completed')

with subtest('Wait for stopped loop'):
    results = []
    promise = Pyjo.Promise.new()

    def stop_cb(loop):
        Pyjo.IOLoop.stop()
        Pyjo.IOLoop.timer(0.1, lambda loop: promise.resolve('wait'))

    Pyjo.IOLoop.next_tick(stop_cb)
    promise.then(store(results)).wait()
    is_deeply_ok(results, ['wait'], 'promise resolved')

done_testing()
