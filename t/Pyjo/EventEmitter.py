class TestException(Exception):
    pass


if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import Pyjo.EventEmitter

    from t.lib.Value import Value

    # Normal event
    e = Pyjo.EventEmitter.new()
    called = Value(0)

    @e.on
    def test1(e):
        called.inc()

    e.emit('test1')
    is_ok(called.get(), 1, 'event was emitted once')

    # Error
    @e.on
    def die(e):
        raise TestException('works!')

    try:
        e.emit('die')
    except TestException:
        pass_ok('right error')
    except:
        fail_ok('right error')
    else:
        fail_ok('right error')

    try:
        e.emit('error', 'works')
    except Exception as ex:
        is_ok(str(ex), 'works', 'right error')
    else:
        fail_ok('right error')

    # Catch
    value = Value('')
    ok(not e.has_subscribers('foo'), 'no subscribers')
    e.catch(lambda e, err: value.set(err))
    ok(e.has_subscribers('error'), 'has subscribers')
    e.emit('error', 'just works!')
    is_ok(value.get(), 'just works!', 'right error')

    # Exception in error event
    e.once(lambda e, err: value.set(err + 'entional'), 'error')
    e.emit('error', 'int')
    is_ok(value.get(), 'intentional', 'right error')

    # Normal event again
    e.emit('test1')
    is_ok(called.get(), 2, 'event was emitted twice')
    is_ok(len(e.subscribers('test1')), 1, 'one subscriber')
    e.emit('test1')
    e.unsubscribe('test1', e.subscribers('test1')[0])
    is_ok(called.get(), 3, 'event was emitted three times')
    is_ok(len(e.subscribers('test1')), 0, 'no subscribers')
    e.emit('test1')
    is_ok(called.get(), 3, 'event was not emitted again')
    e.emit('test1')
    is_ok(called.get(), 3, 'event was not emitted again')

    # One-time event
    once = Value(0)
    e.once(lambda e: once.inc(), 'one_time1')
    is_ok(len(e.subscribers('one_time1')), 1, 'one subscriber')
    e.unsubscribe('one_time1', lambda e: None)
    is_ok(len(e.subscribers('one_time1')), 1, 'one subscriber')
    e.emit('one_time1')
    is_ok(once.get(), 1, 'event was emitted once')
    is_ok(len(e.subscribers('one_time1')), 0, 'no subscribers')
    e.emit('one_time1')
    is_ok(once.get(), 1, 'event was not emitted again')
    e.emit('one_time1')
    is_ok(once.get(), 1, 'event was not emitted again')
    e.emit('one_time1')
    is_ok(once.get(), 1, 'event was not emitted again')

    @e.once
    def one_time2(e):
        e.once(lambda e: once.inc(), 'one_time2')

    e.emit('one_time2')
    is_ok(once.get(), 1, 'event was emitted once')
    e.emit('one_time2')
    is_ok(once.get(), 2, 'event was emitted again')
    e.emit('one_time2')
    is_ok(once.get(), 2, 'event was not emitted again')
    e.once(lambda e: once.set(e.has_subscribers('one_time2')), 'one_time2')
    e.emit('one_time2')
    ok(not once.get(), 'no subscribers')

    # Nested one-time events
    once = Value(0)

    @e.once
    def one_time3(e):
        @e.once
        def one_time3(e):
            e.once(lambda e: once.inc(), 'one_time3')

    is_ok(len(e.subscribers('one_time3')), 1, 'one subscriber')
    e.emit('one_time3')
    is_ok(once.get(), 0, 'only first event was emitted')
    is_ok(len(e.subscribers('one_time3')), 1, 'one subscriber')
    e.emit('one_time3')
    is_ok(once.get(), 0, 'only second event was emitted')
    is_ok(len(e.subscribers('one_time3')), 1, 'one subscriber')
    e.emit('one_time3')
    is_ok(once.get(), 1, 'third event was emitted')
    is_ok(len(e.subscribers('one_time3')), 0, 'no subscribers')
    e.emit('one_time3')
    is_ok(once.get(), 1, 'event was not emitted again')
    e.emit('one_time3')
    is_ok(once.get(), 1, 'event was not emitted again')
    e.emit('one_time3')
    is_ok(once.get(), 1, 'event was not emitted again')

    # Unsubscribe
    e = Pyjo.EventEmitter.new()
    counter = Value(0)

    @e.on
    def foo(e):
        counter.inc()

    e.on(lambda e: counter.inc(), 'foo')
    e.on(lambda e: counter.inc(), 'foo')
    e.unsubscribe('foo', e.once(lambda e: counter.inc(), 'foo'))
    is_ok(len(e.subscribers('foo')), 3, 'three subscribers')
    e.emit('foo').unsubscribe('foo', foo)
    is_ok(counter.get(), 3, 'event was emitted three times')
    is_ok(len(e.subscribers('foo')), 2, 'two subscribers')
    e.emit('foo')
    is_ok(counter.get(), 5, 'event was emitted two times')
    ok(e.has_subscribers('foo'), 'has subscribers')
    ok(not e.unsubscribe('foo').has_subscribers('foo'), 'no subscribers')
    is_ok(len(e.subscribers('foo')), 0, 'no subscribers')
    e.emit('foo')
    is_ok(counter.get(), 5, 'event was not emitted again')

    # Unsubscribe all
    e = Pyjo.EventEmitter.new()
    counter = Value(0)
    e.on(lambda e: counter.inc(), 'foo')
    e.on(lambda e: counter.inc(), 'foo')
    e.unsubscribe_all()
    is_ok(len(e.subscribers('foo')), 0, 'no subscribers')
    e.emit('foo')
    is_ok(counter.get(), 0, 'event was not emitted again')

    # Pass by reference and assignment to $_
    e = Pyjo.EventEmitter.new()
    buf = Value('')
    e.on(lambda e, s: buf.set(buf.get() + 'abc' + s), 'one')
    e.on(lambda e, s: buf.set(buf.get() + '123' + s), 'one')
    is_ok(buf.get(), '', 'no result')
    e.emit('one', 'two')
    is_ok(buf.get(), 'abctwo123two', 'right result')
    e.once(lambda e, s: buf.set(buf.get() + 'def'), 'one')
    e.emit('one', 'three')
    is_ok(buf.get(), 'abctwo123twoabcthree123threedef', 'right result')
    e.emit('one', 'x')
    is_ok(buf.get(), 'abctwo123twoabcthree123threedefabcx123x', 'right result')

    done_testing()
