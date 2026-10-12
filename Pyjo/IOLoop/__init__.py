r"""
Pyjo.IOLoop - Minimalistic event loop
=====================================
::

    import Pyjo.IOLoop

    # Listen on port 3000
    @Pyjo.IOLoop.server(port=3000)
    def server(loop, stream, cid):

        @stream.on
        def read(stream, chunk):
            # Process input chunk
            print("Server: {0}".format(chunk.decode('utf-8')))

            # Write response
            stream.write(b"HTTP/1.1 200 OK\x0d\x0a\x0d\x0a")

            # Disconnect client
            stream.close_gracefully()

    # Connect to port 3000
    @Pyjo.IOLoop.client(port=3000)
    def client(loop, err, stream):

        @stream.on
        def read(stream, chunk):
            # Process input
            print("Client: {0}".format(chunk.decode('utf-8')))

        # Write request
        stream.write(b"GET / HTTP/1.1\x0d\x0a\x0d\x0a")

    # Add a timer
    @Pyjo.IOLoop.timer(3)
    def timeouter(loop):
        print("Timeout")
        # Shutdown server
        loop.remove(server)

    # Start event loop if necessary
    if not Pyjo.IOLoop.is_running():
        Pyjo.IOLoop.start()

:mod:`Pyjo.IOLoop` is a very minimalistic event loop based on :mod:`Pyjo.Reactor`,
it has been reduced to the absolute minimal feature set required to build
solid and scalable non-blocking TCP clients and servers.

Events
------

:mod:`Pyjo.IOLoop` inherits all events from :mod:`Pyjo.EventEmitter` and can emit the
following new ones.

finish
~~~~~~
::

    @loop.on
    def finish(loop):
        ...

Emitted when the event loop wants to shut down gracefully and is just waiting
for all existing connections to be closed.

Debugging
---------

You can set the ``PYJO_IOLOOP_DEBUG`` environment variable to get some
advanced diagnostics information printed to :attr:`sys.stderr`. ::

    PYJO_IOLOOP_DEBUG=1

Classes
-------
"""

import Pyjo.EventEmitter
import Pyjo.IOLoop.Client
import Pyjo.IOLoop.Delay
import Pyjo.IOLoop.Server
import Pyjo.IOLoop.Stream
import Pyjo.Reactor.Base

from Pyjo.Util import decorator, decoratormethod, getenv, isalive, md5_sum, notnone, steady_time, rand, warn

import importlib
import traceback
import weakref


DEBUG = getenv('PYJO_IOLOOP_DEBUG', False)


class Error(Exception):
    """
    Exception raised on unhandled error event.
    """
    pass


class Pyjo_IOLoop(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.IOLoop` inherits all attributes and methods from
    :mod:`Pyjo.EventEmitter` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.max_accepts = kwargs.get('max_accepts', 0)
        """::

            max_accepts = loop.max_accepts
            loop.max_accepts = 1000

        The maximum number of connections this event loop is allowed to accept before
        shutting down gracefully without interrupting existing connections, defaults
        to ``0``. Setting the value to ``0`` will allow this event loop to accept new
        connections indefinitely. Note that up to half of this value can be subtracted
        randomly to improve load balancing between multiple server processes.
        """

        self.max_connections = kwargs.get('max_connections', 1000)
        """::

            max_connections = loop.max_connections
            loop.max_connections = 1000

        The maximum number of concurrent connections this event loop is allowed to
        handle before stopping to accept new incoming connections, defaults to ``1000``.
        """

        self.multi_accept = notnone(kwargs.get('multi_accept'), lambda: 50 if self.max_connections > 50 else 1)
        """::

            multi = loop.multi_accept
            loop.multi_accept = 100

        Number of connections to accept at once, defaults to ``50`` or ``1``, depending
        on if the value of :attr:`max_connections` is smaller than ``50``.
        """

        module = importlib.import_module(Pyjo.Reactor.Base.detect())

        self.reactor = notnone(kwargs.get('reactor'), module.new())
        """::

            reactor = loop.reactor
            loop.reactor = Pyjo.Reactor.new()

        Low-level event reactor, usually a :mod:`Pyjo.Reactor.Poll` or
        :mod:`Pyjo.Reactor.Select` object with a default subscriber to the event
        ``error``. ::

            # Watch if handle becomes readable or writable
            def io_cb(reactor, writable):
                if writable:
                    print('Handle is writable')
                else:
                    print('Handle is readable')

            loop.reactor.io(io_cb, handle)

            # Change to watching only if handle becomes writable
            loop.reactor.watch(handle, read=False, write=True)

            # Remove handle again
            loop.reactor.remove(handle)
        """

        self._accepting_timer = False
        self._acceptors = {}
        self._accepts = None
        self._connections = {}
        self._stop_timer = None

        if DEBUG:
            warn(f"-- Reactor initialized ({self.reactor})")

        def catch_cb(reactor, e, event):
            warn(f"{reactor}: {event}\n{traceback.format_exc()}")

        self.reactor.catch(catch_cb)

    def acceptor(self, acceptor):
        """::

            server = Pyjo.IOLoop.acceptor(cid)
            server = loop.acceptor(cid)
            cid = loop.acceptor(Pyjo.IOLoop.Server.new())

        Get :mod:`Pyjo.IOLoop.Server` object for id or turn object into an acceptor.
        """
        # Find acceptor for id
        if isinstance(acceptor, str):
            if acceptor in self._acceptors:
                return self._acceptors[acceptor]
            else:
                return

        # Connect acceptor with reactor
        cid = self._id()
        acceptor.multi_accept = self.multi_accept
        self._acceptors[cid] = acceptor
        acceptor.reactor = weakref.proxy(self.reactor)

        # Allow new acceptor to get picked up
        self._not_accepting()._maybe_accepting()

        return cid

    def client(self, cb=None, **kwargs):
        """::

            cid = Pyjo.IOLoop.client(cb, address='127.0.0.1', port=3000)

            @Pyjo.IOLoop.client(address='127.0.0.1', port=3000)
            def cid(loop, err, stream):
                ...

            cid = loop.client(cb, address='127.0.0.1', port=3000)

            @loop.client(cb, address='127.0.0.1', port=3000)
            def cid(loop, err, stream):
                ...

        Open TCP connection with :mod:`Pyjo.IOLoop.Client`, takes the same arguments as
        :meth:`Pyjo.IOLoop.Client.connect`.
        """
        if cb is None:
            def wrap(func):
                return self.client(func, **kwargs)
            return wrap

        cid = self._id()
        client = Pyjo.IOLoop.Client.new()
        self._connections[cid] = {'client': client}

        client.reactor = weakref.proxy(self.reactor)
        loop = weakref.proxy(self)

        def connect_cb(client, handle):
            if isalive(loop):
                del loop._connections[cid]['client']
                stream = Pyjo.IOLoop.Stream.new(handle)
                loop._stream(stream, cid)
                cb(loop, None, stream)

        client.on(connect_cb, 'connect')

        def error_cb(client, err):
            if isalive(loop):
                loop._remove(cid)
                cb(loop, err, None)

        client.on(error_cb, 'error')

        client.connect(**kwargs)
        return cid

    def delay(self, *args):
        """::

            delay = Pyjo.IOLoop.delay()
            delay = loop.delay()
            delay = loop.delay(cb)
            delay = loop.delay(cb1, cb2)

        Build :mod:`Pyjo.IOLoop.Delay` object to manage callbacks and control the flow
        of events for this event loop, which can help you avoid deep nested closures
        and memory leaks that often result from continuation-passing style. Callbacks
        will be passed along to :meth:`Pyjo.IOLoop.Delay.steps`. ::

            # Synchronize multiple events
            delay = Pyjo.IOLoop.delay()

            @delay.step
            def step(delay):
                print('BOOM!')

            for i in range(10):
                end = delay.begin()

                def timer_wrap(i):
                    def timer_cb(loop):
                        print(10 - i)
                        end()
                    return timer_cb

                Pyjo.IOLoop.timer(timer_wrap(i), i)

            delay.wait()

            # Sequentialize multiple events
            delay = Pyjo.IOLoop.delay()

            # First step (simple timer)
            @delay.step
            def step1(delay):
                Pyjo.IOLoop.timer(delay.begin(), 2)
                print('Second step in 2 seconds.')

            # Second step (concurrent timers)
            @delay.step
            def step2(delay):
                Pyjo.IOLoop.timer(delay.begin(), 1)
                Pyjo.IOLoop.timer(delay.begin(), 3)
                print('Third step in 3 seconds.')

            # Third step (the end)
            @delay.step
            def step3(delay):
                print('And done after 5 seconds total.')

            delay.wait()

            # Handle exceptions in all steps
            delay = Pyjo.IOLoop.delay()

            @delay.step
            def step1(delay):
                raise Exception('Intentional error')

            @delay.step
            def step2(delay, *args):
                say('Never actually reached.')

            @delay.catch
            def catch(delay, err):
                print("Something went wrong: " + err)

            delay.wait()
        """
        delay = Pyjo.IOLoop.Delay.new()
        delay.ioloop = weakref.proxy(self)
        if args:
            return delay.steps(*args)
        else:
            return delay

    @property
    def is_running(self):
        """::

            boolean = Pyjo.IOLoop.is_running()
            boolean = loop.is_running

        Check if event loop is running. ::

            if not Pyjo.IOLoop.is_running():
                Pyjo.IOLoop.start()
        """
        return self.reactor.is_running

    @decoratormethod
    def next_tick(self, cb):
        """::

            Pyjo.IOLoop.next_tick(cb)
            loop.next_tick(cb)

        Invoke callback as soon as possible, but not before returning, always returns
        ``None``. ::

            # Perform operation on next reactor tick
            @Pyjo.IOLoop.next_tick
            def do_something(loop):
                ...
        """
        loop = weakref.proxy(self)

        def next_tick_cb(reactor):
            if isalive(loop):
                cb(loop)

        return self.reactor.next_tick(next_tick_cb)

    def one_tick(self):
        """::

            Pyjo.IOLoop.one_tick()
            loop.one_tick()

        Run event loop until an event occurs. Note that this method can recurse back
        into the reactor, so you need to be careful. ::

            # Don't block longer than 0.5 seconds
            tid = Pyjo.IOLoop.timer(lambda loop: None, 0.5)
            Pyjo.IOLoop.one_tick()
            Pyjo.IOLoop.remove(tid)
        """
        return self.reactor.one_tick()

    @decoratormethod
    def recurring(self, cb, after):
        """::

            tid = Pyjo.IOLoop.recurring(cb, 3)
            tid = loop.recurring(cb, 0)
            tid = loop.recurring(cb, 0.25)

        Create a new recurring timer, invoking the callback repeatedly after a given
        amount of time in seconds. ::

            @Pyjo.IOLoop.recurring(5)
            def do_something(loop):
                ...
        """
        if DEBUG:
            warn(f"-- Recurring after {after} cb {cb}")
        return self._timer(cb, 'recurring', after)

    def remove(self, taskid):
        """::

            Pyjo.IOLoop.remove(taskid)
            loop.remove(taskid)

        Remove anything with an id, connections will be dropped gracefully by allowing
        them to finish writing all data in their write buffers.
        """
        if taskid in self._connections:
            c = self._connections[taskid]
            if c:
                stream = c.get('stream')
                if stream:
                    return stream.close_gracefully()

        self._remove(taskid)

    def reset(self):
        """::

            Pyjo.IOLoop.reset()
            loop.reset()

        Remove everything and stop the event loop.
        """
        self._acceptors = {}
        self._connections = {}
        self._accepting_timer = False
        self._stop_timer = None

        self.reactor.reset()
        self.stop()

    def server(self, cb=None, **kwargs):
        """::

            cid = Pyjo.IOLoop.server(cb, port=3000)

            @Pyjo.IOLoop.server(port=3000)
            def server(loop, stream, cid):
                ...

            cid = loop.server(cb, port=3000)

            @loop.server(port=3000)
            def server(loop, stream, cid):
                ...

        Accept TCP connections with :mod:`Pyjo.IOLoop.Server`, takes the same arguments
        as :meth:`Pyjo.IOLoop.Server.listen`. ::

            # Listen on port 3000
            @Pyjo.IOLoop.server(port=3000)
            def server(loop, stream, cid):
                ...

            # Listen on random port
            @Pyjo.IOLoop.server(address='127.0.0.1')
            def server(loop, stream, cid):
                ...

            port = Pyjo.IOLoop.acceptor(server).port
        """
        if cb is None:
            def wrap(func):
                return self.server(func, **kwargs)
            return wrap

        server = Pyjo.IOLoop.Server.new()

        def accept_cb(server, handle):
            # Enforce connection limit (randomize to improve load balancing)
            max_accepts = self.max_accepts
            if max_accepts:
                if self._accepts is None:
                    self._accepts = max_accepts - int(rand(max_accepts / 2))
                self._accepts -= 1
                if self._accepts <= 0:
                    self.stop_gracefully()

            stream = Pyjo.IOLoop.Stream.new(handle)
            cb(self, stream, self.stream(stream))

            # Stop accepting if connection limit has been reached
            if self._limit():
                self._not_accepting()

        server.on(accept_cb, 'accept')
        server.listen(**kwargs)

        return self.acceptor(server)

    def start(self):
        """::

            Pyjo.IOLoop.start()
            loop.start()

        Start the event loop, this will block until :meth:`stop` is called. Note that
        some reactors stop automatically if there are no events being watched anymore. ::

            # Start event loop only if it is not running already
            if not Pyjo.IOLoop.is_running():
                Pyjo.IOLoop.start()
        """
        if self.is_running:
            raise Error('Pyjo.IOLoop already running')
        self.reactor.start()

    def stop(self):
        """::

            Pyjo.IOLoop.stop()
            loop.stop()

        Stop the event loop, this will not interrupt any existing connections and the
        event loop can be restarted by running :meth:`start` again.
        """
        self.reactor.stop()

    def stop_gracefully(self):
        """::

            Pyjo.IOLoop.stop_gracefully()
            loop.stop_gracefully()

        Stop accepting new connections and wait for all existing connections to be
        closed before stopping the event loop.
        """
        self._not_accepting()

        if self._stop_timer is None:
            def finish_cb(loop):
                loop._stop()

            self._stop_timer = self.emit('finish').recurring(finish_cb, 1)

    def stream(self, stream):
        """::

            stream = Pyjo.IOLoop.stream(cid)
            stream = loop.stream(cid)
            cid = loop.stream(Pyjo.IOLoop.Stream.new())

        Get :mod:`Pyjo.IOLoop.Stream` object for id or turn object into a connection. ::

            # Increase inactivity timeout for connection to 300 seconds
            Pyjo.IOLoop.stream(cid).timeout = 300
        """
        # Find stream for id
        if isinstance(stream, str):
            if stream in self._connections:
                return self._connections[stream]['stream']
            else:
                return

        return self._stream(stream, self._id())

    @decoratormethod
    def timer(self, cb, after):
        """::

            tid = Pyjo.IOLoop.timer(cb, 3)
            tid = loop.timer(cb, 0)
            tid = loop.timer(cb, 0.25)

        Create a new timer, invoking the callback after a given amount of time in
        seconds. ::

            # Perform operation in 5 seconds
            @Pyjo.IOLoop.timer(5)
            def timer_cb(loop):
                ...
        """
        if DEBUG:
            warn(f"-- Timer after {after} cb {cb}")
        return self._timer(cb, 'timer', after)

    def _id(self):
        taskid = None
        while True:
            taskid = md5_sum(f'c{steady_time()}{rand()}'.encode('ascii'))
            if taskid not in self._connections and taskid not in self._acceptors:
                break
        return taskid

    def _limit(self):
        if self._stop_timer:
            return True
        else:
            return len(self._connections) >= self.max_connections

    def _maybe_accepting(self):
        if self._accepting_timer or self._limit():
            return
        else:
            for acceptor in self._acceptors.values():
                acceptor.start()
            self._accepting_timer = True

    def _not_accepting(self):
        accepting = self._accepting_timer
        self._accepting_timer = False
        if not accepting:
            return self
        else:
            for acceptor in self._acceptors.values():
                acceptor.stop()
            return self

    def _remove(self, taskid):
        # Acceptor
        if taskid in self._acceptors:
            self._acceptors[taskid].unsubscribe('accept').close()
            del self._acceptors[taskid]
            return self._not_accepting()._maybe_accepting()

        # Connections
        if taskid in self._connections:
            if 'client' in self._connections[taskid]:
                self._connections[taskid]['client'].unsubscribe('connect').close()
            del self._connections[taskid]
            self._maybe_accepting()
            if DEBUG:
                warn(f"-- Removed connection {taskid} ({len(self._connections)} connections)")
            return

        # Timer
        reactor = self.reactor

        if not reactor:
            return

        if reactor.remove(taskid):
            return

    def _stop(self):
        if self._connections:
            return

        self._remove(self._stop_timer)
        self._stop_timer = None
        self.stop()

    def _stream(self, stream, cid):
        # Connect stream with reactor
        self._connections[cid] = {'stream': stream}

        if DEBUG:
            warn(f"-- New connection {cid} ({len(self._connections)} connections)")

        stream.reactor = weakref.proxy(self.reactor)
        loop = weakref.proxy(self)

        def close_cb(stream):
            if isalive(loop):
                loop._remove(cid)

        stream.on(close_cb, 'close')
        stream.start()

        return cid

    def _timer(self, cb, method, after):
        loop = weakref.proxy(self)

        def timer_cb(reactor):
            if isalive(loop):
                cb(loop)

        return getattr(self.reactor, method)(timer_cb, after)


def new(*args, **kwargs):
    return Pyjo_IOLoop(*args, **kwargs)


singleton = Pyjo_IOLoop()
"""::

    loop = Pyjo.IOLoop.singleton

The global :mod:`Pyjo.IOLoop` singleton, used to access a single shared event
loop object from everywhere inside the process. ::

    # Many methods also allow you to take shortcuts
    Pyjo.IOLoop.timer(lambda loop: Pyjo.IOLoop.stop(), 2)
    Pyjo.IOLoop.start()

    # Restart active timer
    @Pyjo.IOLoop.timer(3)
    def timeouter(loop):
        print('Timeout!')

    Pyjo.IOLoop.singleton.reactor.again(timeouter)
"""


def acceptor(acceptor):
    return singleton.acceptor(acceptor)


def client(cb=None, **kwargs):
    if cb is None:
        def wrap(func):
            return singleton.client(func, **kwargs)
        return wrap

    return singleton.client(cb, **kwargs)


def delay(*args):
    return singleton.delay(*args)


def is_running():
    return singleton.is_running


@decorator
def next_tick(cb):
    return singleton.next_tick(cb)


def one_tick():
    return singleton.one_tick()


@decorator
def recurring(cb, after):
    return singleton.recurring(cb, after)


def remove(taskid):
    return singleton.remove(taskid)


def reset():
    return singleton.reset()


def server(cb=None, **kwargs):
    if cb is None:
        def wrap(func):
            return singleton.server(func, **kwargs)
        return wrap

    return singleton.server(cb, **kwargs)


def start():
    return singleton.start()


def stop():
    return singleton.stop()


def stop_gracefully():
    return singleton.stop_gracefully()


def stream(stream):
    return singleton.stream(stream)


@decorator
def timer(cb, after=None):
    return singleton.timer(cb, after)


object = Pyjo_IOLoop
