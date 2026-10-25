import Pyjo.EventEmitter
import Pyjo.Promise

from Pyjo.Test import *

import io


def eval_(cb):
    try:
        cb()
    except Exception as e:
        return e


e = Pyjo.EventEmitter.new()

with subtest('Normal event'):
    called = 0

    def called_cb(*args):
        global called
        called += 1

    e.on('test1', called_cb)
    e.emit('test1')
    is_ok(called, 1, 'event was emitted once')
    e.unsubscribe('test1')

with subtest('Error'):

    def die_cb(*args):
        raise Exception('works!\n')

    e.on('die', die_cb)
    err = eval_(lambda: e.emit('die'))
    is_ok(str(err), 'works!\n', 'right error')

with subtest('Unhandled error event'):
    err = eval_(lambda: e.emit('error', 'works'))
    like_ok(str(err), r'^Pyjo\.EventEmitter\.Pyjo_EventEmitter: works', 'right error')

with subtest('Catch'):
    err = None

    def catch_cb(*args):
        global err
        err = args[-1]

    ok(not e.has_subscribers('foo'), 'no subscribers')
    e.catch(catch_cb)
    ok(e.has_subscribers('error'), 'has subscribers')
    e.emit('error', 'just works!')
    is_ok(err, 'just works!', 'right error')

with subtest('Exception in error event'):

    def entional_cb(e, err):
        raise Exception(f'{err}entional')

    e.once('error', entional_cb)
    err = eval_(lambda: e.emit('error', 'int'))
    like_ok(str(err), r'^intentional', 'right error')

with subtest('Normal event again'):
    called = 0
    e.on('test1', lambda *args: called_cb())
    e.emit('test1')
    is_ok(called, 1, 'event was emitted once')
    is_ok(len(e.subscribers('test1')), 1, 'one subscriber')
    e.emit('test1')
    e.unsubscribe('test1', e.subscribers('test1')[0])
    is_ok(called, 2, 'event was emitted twice')
    is_ok(len(e.subscribers('test1')), 0, 'no subscribers')
    e.emit('test1')
    is_ok(called, 2, 'event was not emitted again')
    e.emit('test1')
    is_ok(called, 2, 'event was not emitted again')

with subtest('One-time event'):
    once = 0

    def once_cb(*args):
        global once
        once += 1

    e.once('one_time', once_cb)
    is_ok(len(e.subscribers('one_time')), 1, 'one subscriber')
    e.unsubscribe('one_time', lambda *args: None)
    is_ok(len(e.subscribers('one_time')), 1, 'one subscriber')
    e.emit('one_time')
    is_ok(once, 1, 'event was emitted once')
    is_ok(len(e.subscribers('one_time')), 0, 'no subscribers')
    e.emit('one_time')
    is_ok(once, 1, 'event was not emitted again')
    e.emit('one_time')
    is_ok(once, 1, 'event was not emitted again')
    e.emit('one_time')
    is_ok(once, 1, 'event was not emitted again')
    e.once('one_time', lambda e: e.once('one_time', once_cb))
    e.emit('one_time')
    is_ok(once, 1, 'event was emitted once')
    e.emit('one_time')
    is_ok(once, 2, 'event was emitted again')
    e.emit('one_time')
    is_ok(once, 2, 'event was not emitted again')

    def has_subscribers_cb(e):
        global once
        once = e.has_subscribers('one_time')

    e.once('one_time', has_subscribers_cb)
    e.emit('one_time')
    ok(not once, 'no subscribers')

with subtest('Nested one-time events'):
    once = 0
    e.once('one_time', lambda e: e.once('one_time', lambda e: e.once('one_time', once_cb)))
    is_ok(len(e.subscribers('one_time')), 1, 'one subscriber')
    e.emit('one_time')
    is_ok(once, 0, 'only first event was emitted')
    is_ok(len(e.subscribers('one_time')), 1, 'one subscriber')
    e.emit('one_time')
    is_ok(once, 0, 'only second event was emitted')
    is_ok(len(e.subscribers('one_time')), 1, 'one subscriber')
    e.emit('one_time')
    is_ok(once, 1, 'third event was emitted')
    is_ok(len(e.subscribers('one_time')), 0, 'no subscribers')
    e.emit('one_time')
    is_ok(once, 1, 'event was not emitted again')
    e.emit('one_time')
    is_ok(once, 1, 'event was not emitted again')
    e.emit('one_time')
    is_ok(once, 1, 'event was not emitted again')

with subtest('One-time event used directly'):
    e = Pyjo.EventEmitter.new()
    ok(not e.has_subscribers('foo'), 'no subscribers')
    once = 0
    cb = e.once('foo', once_cb)
    ok(e.has_subscribers('foo'), 'has subscribers')
    cb()
    is_ok(once, 1, 'event was emitted once')
    ok(not e.has_subscribers('foo'), 'no subscribers')

with subtest('Unsubscribe'):
    e = Pyjo.EventEmitter.new()
    counter = 0

    def counter_cb(*args):
        global counter
        counter += 1

    cb = e.on('foo', lambda *args: counter_cb())
    e.on('foo', lambda *args: counter_cb())
    e.on('foo', lambda *args: counter_cb())
    e.unsubscribe('foo', e.once('foo', lambda *args: counter_cb()))
    is_ok(len(e.subscribers('foo')), 3, 'three subscribers')
    e.emit('foo').unsubscribe('foo', cb)
    is_ok(counter, 3, 'event was emitted three times')
    is_ok(len(e.subscribers('foo')), 2, 'two subscribers')
    e.emit('foo')
    is_ok(counter, 5, 'event was emitted two times')
    ok(e.has_subscribers('foo'), 'has subscribers')
    ok(not e.unsubscribe('foo').has_subscribers('foo'), 'no subscribers')
    is_ok(len(e.subscribers('foo')), 0, 'no subscribers')
    e.emit('foo')
    is_ok(counter, 5, 'event was not emitted again')

with subtest('Manipulate events'):
    e = Pyjo.EventEmitter.new()
    buffer = ''

    def buffer_cb(string):
        global buffer
        buffer += string

    e.subscribers('foo').append(lambda e: buffer_cb('one'))
    e.subscribers('foo').append(lambda e: buffer_cb('two'))
    e.subscribers('foo').append(lambda e: buffer_cb('three'))
    e.emit('foo')
    is_ok(buffer, 'onetwothree', 'right result')
    e.subscribers('foo').reverse()
    e.emit('foo')
    is_ok(buffer, 'onetwothreethreetwoone', 'right result')

with subtest('Pass by reference and assignment to $_'):
    e = Pyjo.EventEmitter.new()
    # Unlike Mojolicious: Python has no aliased arguments, the callbacks change a mutable buffer
    buffer = io.StringIO()
    e.on('one', lambda e, buffer, string: buffer.write('abc' + string))
    e.on('one', lambda e, buffer, string: buffer.write('123' + string))
    is_ok(buffer.getvalue(), '', 'no result')
    e.emit('one', buffer, 'two')
    is_ok(buffer.getvalue(), 'abctwo123two', 'right result')
    e.once('one', lambda e, buffer, string: buffer.write('def'))
    e.emit('one', buffer, 'three')
    is_ok(buffer.getvalue(), 'abctwo123twoabcthree123threedef', 'right result')
    e.emit('one', buffer, 'x')
    is_ok(buffer.getvalue(), 'abctwo123twoabcthree123threedefabcx123x', 'right result')

# Not in Mojolicious: a promise of an event, as events.once of Node.js
with subtest('Promise of an event'):
    e = Pyjo.EventEmitter.new()
    promise = e.once_p('foo')
    ok(e.has_subscribers('foo'), 'subscribed')
    ok(e.has_subscribers('error'), 'subscribed to errors')
    e.emit('foo', 1, 2)
    got = []
    promise.then(lambda *args: got.append(args)).wait()
    is_deeply_ok(got, [(1, 2)], 'arguments of the event')
    ok(not e.has_subscribers('foo'), 'unsubscribed')
    ok(not e.has_subscribers('error'), 'unsubscribed from errors')
    promise = e.once_p('foo')
    e.emit('error', 'boom')
    promise.catch(lambda err: got.append(err)).wait()
    is_deeply_ok(got, [(1, 2), 'boom'], 'rejected with the error')
    ok(not e.has_subscribers('foo'), 'unsubscribed after the error')
    promise = e.once_p('error')
    e.emit('error', 'once more')
    promise.then(lambda err: got.append(err)).wait()
    is_deeply_ok(got[-1], 'once more', 'the event error itself')

# Not in Mojolicious: the events as an asynchronous iterator, as events.on of Node.js
with subtest('Events as an asynchronous iterator'):
    e = Pyjo.EventEmitter.new()
    got = []

    # The iterator subscribes when it is made, before the events, as the reactor of asyncio runs a coroutine later
    @Pyjo.Promise.coroutine
    async def collect(events):
        async for args in events:
            got.append(args)

    promise = collect(e.events('foo'))
    e.emit('foo', 1)
    e.emit('foo', 2, 3)
    e.emit('bar')
    e.emit('close')
    promise.wait()
    is_deeply_ok(got, [(1,), (2, 3)], 'events until close')
    ok(not e.has_subscribers('foo'), 'unsubscribed at the end')

    iterator = e.events('foo')
    e.emit('foo', 'queued')
    e.emit('end')
    got = []

    @Pyjo.Promise.coroutine
    async def queued():
        async for (value,) in iterator:
            got.append(value)

    queued().wait()
    is_deeply_ok(got, ['queued'], 'queued before, until end')

    errors = []
    promise = collect(e.events('foo')).catch(lambda err: errors.append(str(err)))
    e.emit('error', 'boom')
    promise.wait()
    like_ok(errors[0], r'^boom', 'error raised')

done_testing()
