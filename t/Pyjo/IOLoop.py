if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    from Pyjo.Util import getenv, setenv, steady_time

    setenv('PYJO_REACTOR', 'Pyjo.Reactor.Select')
    setenv('PYJO_REACTOR_DIE', '1')

    import Pyjo.IOLoop.Client
    import Pyjo.IOLoop.Delay
    import Pyjo.IOLoop.Server
    import Pyjo.IOLoop.Stream

    from t.lib.Value import Value

    import platform
    import socket

    # Reactor detection
    setenv('PYJO_REACTOR', 'MyReactorDoesNotExist')
    loop = Pyjo.IOLoop.new()
    like_ok(loop.reactor.__class__.__name__, '^Pyjo.Reactor.(Select|Poll)$', 'right class')
    setenv('PYJO_REACTOR', 't.lib.TestReactor')
    loop = Pyjo.IOLoop.new()
    is_ok(loop.reactor.__class__.__name__, 'TestReactor', 'right class')

    # Defaults
    loop = Pyjo.IOLoop.new()
    is_ok(loop.max_connections, 1000, 'right default')
    is_ok(loop.multi_accept, 50, 'right default')
    loop = Pyjo.IOLoop.new(max_connections=51)
    is_ok(loop.max_connections, 51, 'right value')
    is_ok(loop.multi_accept, 50, 'right value')
    loop = Pyjo.IOLoop.new(max_connections=10)
    is_ok(loop.max_connections, 10, 'right value')
    is_ok(loop.multi_accept, 1, 'right value')
    loop = Pyjo.IOLoop.new(multi_accept=10)
    is_ok(loop.max_connections, 1000, 'right value')
    is_ok(loop.multi_accept, 10, 'right value')

    # Double start
    err = Value('')

    @Pyjo.IOLoop.next_tick
    def cb1(loop):
        try:
            loop.start()
        except Exception as ex:
            err.set(ex)
        loop.stop()

    Pyjo.IOLoop.start()
    is_ok(str(err.get()), 'Pyjo.IOLoop already running', 'right error')

    # Basic functionality
    ticks = Value(0)
    timer = Value(0)
    hirestimer = Value(0)
    tid = loop.recurring(lambda loop: ticks.inc(), 0)

    @loop.timer(1)
    def cb2(loop):
        loop.timer(lambda loop: loop.stop(), 0)
        timer.inc()

    loop.timer(lambda loop: hirestimer.inc(), 0.25)
    loop.start()
    ok(timer, 'recursive timer works')
    ok(hirestimer, 'hires timer works')
    loop.one_tick()
    ok(ticks.get() > 2, 'more than two ticks')

    # Run again without first tick event handler
    before = ticks.get()
    after = Value(0)
    tid2 = loop.recurring(lambda loop: after.inc(), 0)
    loop.remove(tid)
    loop.timer(lambda loop: loop.stop(), 0.5)
    loop.start()
    loop.one_tick()
    loop.remove(tid2)
    ok(after.get() > 1, 'more than one tick')
    is_ok(ticks.get(), before, 'no additional ticks')

    # Recurring timer
    count = Value(0)
    tid = loop.recurring(lambda loop: count.inc(), 0.1)
    loop.timer(lambda loop: loop.stop(), 0.5)
    loop.start()
    loop.one_tick()
    loop.remove(tid)
    ok(count.get() > 1, 'more than one recurring event')
    ok(count.get() < 10, 'less than ten recurring events')

    # Handle and reset
    handle = Value(None)
    handle2 = Value(None)

    @Pyjo.IOLoop.server(address='127.0.0.1')
    def cid(loop, stream, cid):
        handle.set(stream.handle)
        Pyjo.IOLoop.stop()

    port = Pyjo.IOLoop.acceptor(cid).port
    Pyjo.IOLoop.acceptor(cid).on(lambda server, handle: handle2.set(handle), 'accept')
    cid2 = Pyjo.IOLoop.client(address='127.0.0.1', port=port, cb=lambda loop, err, stream: True)
    Pyjo.IOLoop.start()
    count.set(0)
    Pyjo.IOLoop.recurring(lambda loop: timer.inc(), 10)
    running = Value(None)

    @Pyjo.IOLoop.next_tick
    def cb(loop):
        Pyjo.IOLoop.reset()
        running.set(Pyjo.IOLoop.is_running())

    Pyjo.IOLoop.start()
    ok(not running.get(), 'not running')
    is_ok(count.get(), 0, 'no recurring events')
    ok(not Pyjo.IOLoop.acceptor(cid), 'acceptor has been removed')
    ok(not Pyjo.IOLoop.stream(cid2), 'stream has been removed')
    is_ok(handle.get(), handle2.get(), 'handles are equal')
    isa_ok(handle.get(), type(socket.socket()), 'right reference')

    # The poll reactor stops when there are no events being watched anymore
    time = steady_time()
    Pyjo.IOLoop.start()
    Pyjo.IOLoop.one_tick()
    Pyjo.IOLoop.reset()
    ok(steady_time() < time + 10, 'stopped automatically')

    # Stream
    buf = Value(b'')

    @Pyjo.IOLoop.server(address='127.0.0.1')
    def cid(loop, stream, cid):
        buf.set(buf.get() + b'accepted')

        @stream.on
        def read(stream, chunk):
            buf.set(buf.get() + chunk)
            if buf.get() == b'acceptedhello':
                stream.write(b'wo').write(b'').write(b'rld', lambda stream: stream.close())

    port = Pyjo.IOLoop.acceptor(cid).port
    delay = Pyjo.IOLoop.delay()
    end = delay.begin()
    handle = Value(None)

    @Pyjo.IOLoop.client(port=port)
    def cid2(loop, err, stream):
        handle.set(stream.steal_handle())
        end()
        stream.on(lambda stream: buf.set(buf.get() + b'should not happen'), 'close')
        stream.on(lambda stream, err: buf.set(buf.get() + b'should not happen either'), 'error')

    delay.wait()
    stream = Pyjo.IOLoop.Stream.new(handle.get())
    is_ok(stream.timeout, 15, 'right default')
    is_ok(stream.set(timeout=16).timeout, 16, 'right timeout')
    cid = Pyjo.IOLoop.stream(stream)
    stream.on(lambda stream: Pyjo.IOLoop.stop(), 'close')
    stream.on(lambda stream, chunk: buf.set(buf.get() + chunk), 'read')
    stream.write(b'hello')
    ok(Pyjo.IOLoop.stream(cid), 'stream exists')
    is_ok(stream.timeout, 16, 'right timeout')
    Pyjo.IOLoop.start()
    Pyjo.IOLoop.timer(lambda loop: Pyjo.IOLoop.stop(), 0.25)
    Pyjo.IOLoop.start()
    ok(not Pyjo.IOLoop.stream(cid), 'stream does not exist anymore')
    is_ok(buf.get(), b'acceptedhelloworld', 'right result')

    # Removed listen socket
    cid = loop.server(address='127.0.0.1', cb=lambda *args: True)
    port = loop.acceptor(cid).port
    connected = Value(False)

    @loop.client(port=port)
    def cid2(loop, err, stream):
        loop.remove(cid)
        loop.stop()
        connected.set(True)

    like_ok(getenv('PYJO_REUSE'), rf'(?:^|\,)127\.0\.0\.1:{port}:', 'file descriptor can be reused')
    loop.start()
    unlike_ok(getenv('PYJO_REUSE'), rf'(?:^|\,)127\.0\.0\.1:{port}:', 'environment is clean')
    ok(connected, 'connected')
    ok(not loop.acceptor(cid), 'acceptor has been removed')
    cid = None

    # Removed connection (with delay)
    removed = Value(0)
    delay = Pyjo.IOLoop.delay(lambda delay: removed.inc())
    end = delay.begin()
    cid = Pyjo.IOLoop.server(address='127.0.0.1', cb=lambda loop, stream, cid: stream.on(lambda stream: end(), 'close'))
    port = Pyjo.IOLoop.acceptor(cid).port
    end2 = delay.begin()

    @Pyjo.IOLoop.client(port=port)
    def cid2(loop, err, stream):
        stream.on(end2, 'close')
        loop.remove(cid2)

    delay.wait()
    is_ok(removed.get(), 1, 'connection has been removed')

    # Stream throttling
    client = Value(b'')
    client_after = Value(b'')
    client_before = Value(b'')
    server = Value(b'')
    server_after = Value(b'')
    server_before = Value(b'')

    @Pyjo.IOLoop.server(address='127.0.0.1')
    def cid(loop, stream, cid):
        stream.timeout = 0

        @stream.on
        def read(stream, chunk):
            if not server.get():

                @Pyjo.IOLoop.timer(0.5)
                def timer(loop):
                    server_before.set(server.get())
                    stream.stop()
                    stream.write(b'works!')

                    @Pyjo.IOLoop.timer(0.5)
                    def timer(loop):
                        server_after.set(server.get())
                        client_after.set(client.get())
                        stream.start()
                        Pyjo.IOLoop.timer(lambda loop: Pyjo.IOLoop.stop(), 0.5)

            server.set(server.get() + chunk)

    port = Pyjo.IOLoop.acceptor(cid).port

    @Pyjo.IOLoop.client(port=port)
    def cid2(loop, err, stream):
        def drain(stream):
            return stream.write(b'1', drain)

        drain(stream)
        stream.on(lambda stream, chunk: client.set(client.get() + chunk), 'read')

    Pyjo.IOLoop.start()
    is_ok(server_before.get(), server_after.get(), 'stream has been paused')
    ok(len(server.get()) > len(server_after.get()), 'stream has been resumed')
    is_ok(client.get(), client_after.get(), 'stream was writable while paused')
    is_ok(client.get(), b'works!', 'full message has been written')

    if platform.python_implementation() != 'PyPy':
        # Graceful shutdown
        err = Value('')
        loop = Pyjo.IOLoop.new()
        finish = Value(0)
        loop.on(lambda loop: finish.inc(), 'finish')
        loop.stop_gracefully()
        loop.remove(loop.client(port=Pyjo.IOLoop.Server.generate_port(), cb=lambda *args: True))

        @loop.timer(5)
        def timer(loop):
            loop.stop()
            err.set('failed')

        loop.start()
        ok(not err.get(), 'no error')
        is_ok(finish.get(), 1, 'finish event has been emitted once')
    else:
        skip('PyPy error', 2)

    # Graceful shutdown (max_accepts)
    err = Value('')
    loop = Pyjo.IOLoop.new(max_accepts=1)
    cid = loop.server(address='127.0.0.1', cb=lambda loop, stream, cid: stream.close())
    port = loop.acceptor(cid).port
    loop.client(port=port, cb=lambda loop, err, stream: True)

    @loop.timer(5)
    def cb3(loop):
        loop.stop()
        err.set('failed')

    loop.start()
    ok(not err.get(), 'no error')
    is_ok(loop.max_accepts, 1, 'right value')

    # Exception in timer
    loop = Pyjo.IOLoop.new()

    @loop.timer(0)
    def cb4(loop):
        raise Exception('Bye!')

    err = ''
    try:
        loop.start()
    except Exception as ex:
        err = str(ex)

    is_ok(err, 'Bye!', 'right error')

    # Defaults
    is_ok(Pyjo.IOLoop.Client.new().reactor, Pyjo.IOLoop.singleton.reactor, 'right default')
    is_ok(Pyjo.IOLoop.Delay.new().ioloop, Pyjo.IOLoop.singleton, 'right default')
    is_ok(Pyjo.IOLoop.Server.new().reactor, Pyjo.IOLoop.singleton.reactor, 'right default')
    is_ok(Pyjo.IOLoop.Stream.new(handle=None).reactor, Pyjo.IOLoop.singleton.reactor, 'right default')

    done_testing()
