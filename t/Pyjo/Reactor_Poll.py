if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import select

    if not hasattr(select, 'poll'):
        plan_skip_all('select.poll is required for this test!')

    import Pyjo.Reactor.Poll

    from Pyjo.Util import setenv, steady_time
    from t.lib.Value import Value

    import socket
    import time

    # Instantiation
    setenv('PYJO_REACTOR', 'Pyjo.Reactor.Poll')
    reactor = Pyjo.Reactor.Poll.new()
    is_ok(reactor.__class__.__name__, 'Pyjo_Reactor_Poll', 'right object')
    is_ok(Pyjo.Reactor.Poll.new().__class__.__name__, 'Pyjo_Reactor_Poll', 'right object')
    reactor = None
    is_ok(Pyjo.Reactor.Poll.new().__class__.__name__, 'Pyjo_Reactor_Poll', 'right object')
    import Pyjo.IOLoop

    reactor = Pyjo.IOLoop.singleton.reactor
    is_ok(reactor.__class__.__name__, 'Pyjo_Reactor_Poll', 'right object')

    # Make sure it stops automatically when not watching for events
    triggered = Value(0)
    Pyjo.IOLoop.next_tick(lambda reactor: triggered.inc())
    Pyjo.IOLoop.start()
    is_ok(triggered.get(), 1, 'reactor waited for one event')
    t = steady_time()
    Pyjo.IOLoop.start()
    Pyjo.IOLoop.one_tick()
    ok(steady_time() < (t + 10), 'stopped automatically')

    # Listen
    listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen.bind(('127.0.0.1', 0))
    listen.listen(5)
    port = listen.getsockname()[1]
    readable = Value(0)
    writable = Value(0)
    reactor.io(lambda reactor, write: writable.inc() if write else readable.inc(), listen).watch(
        listen, False, False
    ).watch(listen, True, True)
    reactor.timer(lambda reactor: reactor.stop(), 0.025)
    reactor.start()
    ok(not readable.get(), 'handle is not readable')
    ok(not writable.get(), 'handle is not writable')

    # Connect
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', port))
    reactor.timer(lambda reactor: reactor.stop(), 1)
    reactor.start()
    ok(readable.get(), 'handle is readable')
    ok(not writable.get(), 'handle is not writable')

    # Accept
    server, addr = listen.accept()
    reactor.remove(listen)
    readable.set(0)
    writable.set(0)
    reactor.io(lambda reactor, write: writable.inc() if write else readable.inc(), client)
    reactor.again(reactor.timer(lambda reactor: reactor.stop(), 0.025))
    reactor.start()
    ok(not readable.get(), 'handle is not readable')
    ok(writable.get(), 'handle is writable')
    client.send(b'hello!\n')
    time.sleep(1)
    reactor.remove(client)
    readable.set(0)
    writable.set(0)
    reactor.io(lambda reactor, write: writable.inc() if write else readable.inc(), server)
    reactor.watch(server, True, False)
    reactor.timer(lambda reactor: reactor.stop(), 0.025)
    reactor.start()
    ok(readable.get(), 'handle is readable')
    ok(not writable.get(), 'handle is not writable')
    readable.set(0)
    writable.set(0)
    reactor.watch(server, True, True)
    reactor.timer(lambda reactor: reactor.stop(), 0.025)
    reactor.start()
    ok(readable.get(), 'handle is readable')
    ok(writable.get(), 'handle is writable')
    readable.set(0)
    writable.set(0)
    reactor.watch(server, False, False)
    reactor.timer(lambda reactor: reactor.stop(), 0.025)
    reactor.start()
    ok(not readable.get(), 'handle is not readable')
    ok(not writable.get(), 'handle is not writable')
    readable.set(0)
    writable.set(0)
    reactor.watch(server, True, False)
    reactor.timer(lambda reactor: reactor.stop(), 0.025)
    reactor.start()
    ok(readable.get(), 'handle is readable')
    ok(not writable.get(), 'handle is not writable')
    readable.set(0)
    writable.set(0)
    reactor.io(lambda reactor, write: writable.inc() if write else readable.inc(), server)
    reactor.timer(lambda reactor: reactor.stop(), 0.025)
    reactor.start()
    ok(readable.get(), 'handle is readable')
    ok(writable.get(), 'handle is writable')

    # Timers
    timer = Value(0)
    recurring = Value(0)
    reactor.timer(lambda reactor: timer.inc(), 0)
    reactor.remove(reactor.timer(lambda reactor: timer.inc(), 0))
    tid = reactor.recurring(lambda reactor: recurring.inc(), 0)
    readable.set(0)
    writable.set(0)
    reactor.timer(lambda reactor: reactor.stop(), 0.025)
    reactor.start()
    ok(readable.get(), 'handle is readable again')
    ok(writable.get(), 'handle is writable again')
    ok(timer.get(), 'timer was triggered')
    ok(recurring.get(), 'recurring was triggered')
    done = Value(False)
    readable.set(0)
    writable.set(0)
    timer.set(0)
    recurring.set(0)
    reactor.timer(lambda reactor: done.set(reactor.is_running), 0.025)
    while not done.get():
        reactor.one_tick()
    ok(readable.get(), 'handle is readable again')
    ok(writable.get(), 'handle is writable again')
    ok(not timer.get(), 'timer was not triggered')
    ok(recurring.get(), 'recurring was triggered again')
    readable.set(0)
    writable.set(0)
    timer.set(0)
    recurring.set(0)
    reactor.timer(lambda reactor: done.set(reactor.stop()), 0.025)
    reactor.start()
    ok(readable.get(), 'handle is readable again')
    ok(writable.get(), 'handle is writable again')
    ok(not timer.get(), 'timer was not triggered')
    ok(recurring.get(), 'recurring was triggered again')
    reactor.remove(tid)
    readable.set(0)
    writable.set(0)
    timer.set(0)
    recurring.set(0)
    reactor.timer(lambda reactor: done.set(reactor.stop()), 0.025)
    reactor.start()
    ok(readable.get(), 'handle is readable again')
    ok(writable.get(), 'handle is writable again')
    ok(not timer.get(), 'timer was not triggered')
    ok(not recurring.get(), 'recurring was not triggered again')
    readable.set(0)
    writable.set(0)
    timer.set(0)
    recurring.set(0)
    tid = reactor.recurring(lambda reactor: recurring.inc(), 0)
    is_ok(reactor.next_tick(lambda reactor: reactor.stop()), None, 'returned None')
    reactor.start()
    ok(readable.get(), 'handle is readable again')
    ok(writable.get(), 'handle is writable again')
    ok(not timer.get(), 'timer was not triggered')
    ok(recurring.get(), 'recurring was triggered again')

    # Reset
    reactor.reset()
    readable.set(0)
    writable.set(0)
    timer.set(0)
    recurring.set(0)
    reactor.timer(lambda reactor: reactor.stop(), 0.025)
    reactor.start()
    ok(not readable.get(), 'io event was not triggered again')
    ok(not writable.get(), 'io event was not triggered again')
    ok(not recurring.get(), 'recurring was not triggered again')
    reactor2 = Pyjo.Reactor.Poll.new()
    is_ok(reactor2.__class__.__name__, 'Pyjo_Reactor_Poll', 'right object')

    # Reset while watchers are active
    writable = Value(0)
    for handle in client, server:
        reactor.io(lambda reactor, write: writable.inc() and reactor.reset(), handle).watch(handle, False, True)
    reactor.start()
    is_ok(writable.get(), 1, 'only one handle was writable')

    # Concurrent reactors
    timer.set(0)
    reactor.recurring(lambda reactor: timer.inc(), 0)
    timer2 = Value(0)
    reactor2.recurring(lambda reactor: timer2.inc(), 0)
    reactor.timer(lambda reactor: reactor.stop(), 0.025)
    reactor.start()
    ok(timer.get(), 'timer was triggered')
    ok(not timer2.get(), 'timer was not triggered')
    timer.set(0)
    timer2.set(0)
    reactor2.timer(lambda reactor: reactor.stop(), 0.025)
    reactor2.start()
    ok(not timer.get(), 'timer was not triggered')
    ok(timer2.get(), 'timer was triggered')
    timer.set(0)
    timer2.set(0)
    reactor.timer(lambda reactor: reactor.stop(), 0.025)
    reactor.start()
    ok(timer.get(), 'timer was triggered')
    ok(not timer2.get(), 'timer was not triggered')
    timer.set(0)
    timer2.set(0)
    reactor2.timer(lambda reactor: reactor.stop(), 0.025)
    reactor2.start()
    ok(not timer.get(), 'timer was not triggered')
    ok(timer2, 'timer was triggered')

    # Restart timer
    single = Value(0)
    pair = Value(0)
    last = Value(0)
    one = Value(None)
    two = Value(None)
    reactor.timer(lambda reactor: single.inc(), 0.025)

    def one_cb(reactor):
        if single.get() and pair.get():
            last.inc()
        if pair.get():
            pair.inc()
            reactor.stop()
        else:
            pair.inc()
            reactor.again(two.get())

    one.set(reactor.timer(one_cb, 0.025))

    def two_cb(reactor):
        if single.get() and pair.get():
            last.inc()
        if pair.get():
            pair.inc()
            reactor.stop()
        else:
            pair.inc()
            reactor.again(one.get())

    two.set(reactor.timer(two_cb, 0.025))

    reactor.start()
    is_ok(pair.get(), 2, 'timer pair was triggered')
    ok(single.get(), 'single timer was triggered')
    ok(last.get(), 'timers were triggered in the right order')

    # Error
    err = Value('')

    def error_cb(reactor, e, event):
        reactor.stop()
        err.set(e)

    reactor.unsubscribe('error').on('error', error_cb)

    def die_cb(reactor):
        raise Exception('works!')

    reactor.timer(die_cb, 0)
    reactor.start()

    in_ok(err.get().args[0], 'works!', 'right error')

    # Recursion
    timer = Value(0)
    reactor = reactor.new()
    reactor.timer(lambda reactor: timer.inc() and reactor.one_tick(), 0)
    reactor.one_tick()
    is_ok(timer.get(), 1, 'timer was triggered once')

    # Detection
    is_ok(Pyjo.Reactor.Base.detect(), 'Pyjo.Reactor.Poll', 'right class')

    setenv('PYJO_REACTOR', 't.lib.TestReactor')

    # Detection (env)
    is_ok(Pyjo.Reactor.Base.detect(), 't.lib.TestReactor', 'right class')

    # Reactor in control
    setenv('PYJO_REACTOR', 'Pyjo.Reactor.Poll')

    is_ok(Pyjo.IOLoop.singleton.reactor.__class__.__name__, 'Pyjo_Reactor_Poll', 'right object')
    ok(not Pyjo.IOLoop.is_running(), 'loop is not running')
    buf = Value('')
    server_err = Value('')
    server_running = Value(False)
    client_err = Value('')
    client_running = Value(False)

    @Pyjo.IOLoop.server(address='127.0.0.1')
    def server(loop, stream, cid):
        stream.write(b'test', lambda stream: stream.write(b'321'))
        server_running.set(Pyjo.IOLoop.is_running())
        try:
            Pyjo.IOLoop.start()
        except Exception as ex:
            server_err.set(ex.args[0])

    port = Pyjo.IOLoop.acceptor(server).port

    @Pyjo.IOLoop.client(port=port)
    def client(loop, err, stream):

        @stream.on
        def read(stream, chunk):
            buf.set(buf.get() + chunk)
            if buf.get() == b'test321':
                Pyjo.IOLoop.singleton.reactor.stop()

        client_running.set(Pyjo.IOLoop.is_running())
        try:
            Pyjo.IOLoop.start()
        except Exception as ex:
            client_err.set(ex.args[0])

    Pyjo.IOLoop.singleton.reactor.start()
    ok(not Pyjo.IOLoop.is_running(), 'loop is not running')
    in_ok(server_err.get(), 'Pyjo.IOLoop already running', 'right error')
    in_ok(client_err.get(), 'Pyjo.IOLoop already running', 'right error')
    ok(server_running.get(), 'loop is running')
    ok(client_running.get(), 'loop is running')

    done_testing()
