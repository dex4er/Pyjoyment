import Pyjo.EventEmitter
import Pyjo.Exception

from Pyjo.Test import *

import functools
import gc


class Counter:
    def __init__(self):
        self.count = 0

    def inc(self, *args):
        self.count += 1


with subtest('Bound methods'):
    e = Pyjo.EventEmitter.new()
    counter = Counter()
    e.on('foo', counter.inc)
    e.emit('foo')
    is_ok(counter.count, 1, 'called')
    e.unsubscribe('foo', counter.inc)
    ok(not e.has_subscribers('foo'), 'a new bound method of the same object unsubscribes')

with subtest('Callable objects'):
    e = Pyjo.EventEmitter.new()
    counter = Counter()
    e.on('foo', functools.partial(counter.inc, 'partial'))
    e.emit('foo')
    is_ok(counter.count, 1, 'partial')

with subtest('Decorators'):
    e = Pyjo.EventEmitter.new()
    got = []

    @e.on
    def foo(e, value):
        got.append(('on', value))

    @e.once('foo')
    def bar(e, value):
        got.append(('once', value))

    @e.once
    def baz(e, value):
        got.append(('baz', value))

    ok(callable(foo), 'on returns the function')
    ok(callable(bar), 'once returns the wrapper')
    e.emit('foo', 1).emit('foo', 2).emit('baz', 3).emit('baz', 4)
    is_deeply_ok(got, [('on', 1), ('once', 1), ('on', 2), ('baz', 3)], 'right events')

with subtest('Unhandled error'):
    e = Pyjo.EventEmitter.new()
    try:
        e.emit('error', 'Oops')
    except Exception as err:
        isa_ok(err, Pyjo.Exception.object, 'a Pyjo.Exception')
        is_ok(err.__cause__, None, 'no cause')

    try:
        e.emit('error', KeyError('foo'))
    except Pyjo.Exception.object as err:
        isa_ok(err.__cause__, KeyError, 'exception is the cause')

    try:
        e.emit('error')
    except Pyjo.Exception.object as err:
        is_ok(err.message, 'Pyjo.EventEmitter.Pyjo_EventEmitter: ', 'no error')

    class MyEmitter(Pyjo.EventEmitter.object):
        pass

    try:
        MyEmitter.new().emit('error', 'Oops')
    except Pyjo.Exception.object as err:
        like_ok(err.message, r'MyEmitter: Oops$', 'name of the subclass')

with subtest('Empty list of subscribers'):
    e = Pyjo.EventEmitter.new()
    is_ok(e.subscribers('error'), [], 'no subscribers')
    ok(not e.has_subscribers('error'), 'empty list is no subscriber')
    throws_ok(lambda: e.emit('error', 'Oops'), Pyjo.Exception.object, 'unhandled error is not swallowed')

with subtest('Once does not keep the emitter alive'):
    emitter = Pyjo.EventEmitter.new()
    cb = emitter.once('foo', lambda e: ...)
    del emitter
    gc.collect()
    throws_ok(lambda: cb(), ReferenceError, 'emitter is gone')

done_testing()
