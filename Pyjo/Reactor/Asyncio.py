"""
Pyjo.Reactor.Asyncio - Low-level event reactor on asyncio
=========================================================
::

    import Pyjo.Reactor.Asyncio

    # Watch if handle becomes readable or writable
    reactor = Pyjo.Reactor.Asyncio.new()
    reactor.io(first, lambda reactor, writable: print(
        'First handle is writable' if writable else 'First handle is readable'
    ))

    # Change to watching only if handle becomes writable
    reactor.watch(first, False, True)

    # Watch a file descriptor if it becomes readable
    reactor.io(fd, lambda reactor, writable: print(
        'Second handle is writable' if writable else 'Second handle is readable'
    )).watch(fd, True, False)

    # Add a timer
    def timeout(reactor):
        reactor.remove(first)
        reactor.remove(fd)
        print('Timeout!')

    reactor.timer(15, timeout)

    # Start reactor if necessary
    if not reactor.is_running:
        reactor.start()

:mod:`Pyjo.Reactor.Asyncio` is a low-level event reactor based on
:mod:`asyncio`. It watches handles and runs timers in an asyncio event loop,
so coroutines, tasks and other users of the loop run along with it.

A reactor uses the event loop it is given, or else the loop that is running,
as inside :func:`asyncio.run`, or a new event loop of its own, and moves its
handles and timers to the loop that is running. In a loop that runs
already, :meth:`start` and :meth:`one_tick` return right away, as asyncio
does not nest event loops, and the handles and timers are watched by that
loop.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Reactor::Poll <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Reactor/Poll.pm>`_
of Mojolicious 9.49.
"""

import Pyjo.Exception
import Pyjo.Reactor

from Pyjo.Reactor import Handle, IOCallback, TimerCallback
from Pyjo.Util import md5_sum

import asyncio
import atexit
import random
import sys
import time
import weakref

from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, Self, TypedDict


class _IO(TypedDict):
    cb: IOCallback
    read: bool
    write: bool


class _Timer(TypedDict):
    cb: TimerCallback | None
    after: float
    recurring: bool
    handle: asyncio.Handle


class Pyjo_Reactor_Asyncio(Pyjo.Reactor.object):
    """
    :mod:`Pyjo.Reactor.Asyncio` inherits all methods from
    :mod:`Pyjo.Reactor` and implements the following new ones.
    """

    def __init__(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        """::

            reactor = Pyjo.Reactor.Asyncio.new()
            reactor = Pyjo.Reactor.Asyncio.new(loop=asyncio.new_event_loop())

        Construct a new :mod:`Pyjo.Reactor.Asyncio` object.
        """
        super().__init__()

        # Not in Mojolicious: the asyncio event loop
        self._fixed = loop is not None
        self._loop = loop
        self._own: asyncio.AbstractEventLoop | None = None

        self._error: BaseException | None = None
        self._io: dict[int, _IO] = {}
        self._next_tick: list[TimerCallback] = []
        self._next_timer: str | None = None
        self._one = 0
        self._running = 0
        self._tasks: set[asyncio.Task[Any]] = set()
        self._timers: dict[str, _Timer] = {}

    def __del__(self) -> None:
        # Not in Mojolicious: the event loop of the reactor is closed with it, unless the interpreter is finishing
        # Module globals may be gone at the end of the interpreter
        try:
            loop = getattr(self, '_own', None)
            if loop is not None and not sys.is_finalizing() and not loop.is_running() and not loop.is_closed():
                loop.close()
        except Exception:
            pass

    # Not in Mojolicious: the asyncio event loop
    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """::

            loop = reactor.loop

        The :mod:`asyncio` event loop of the reactor: the one it is given, or
        else the loop that is running, as inside :func:`asyncio.run`, or a
        loop of its own. A reactor that is not given a loop follows the loop
        that is running, and moves its handles and timers to it, unless it
        has tasks in another loop, which cannot move.
        """
        loop = self._loop
        if self._fixed and loop is not None:
            return loop

        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None

        if running is not None:
            if running is not loop and not len(self._tasks):
                self._move(running)
        elif loop is None or loop.is_closed() or (loop is not self._own and not loop.is_running()):
            if self._own is None or self._own.is_closed():
                self._own = asyncio.new_event_loop()
                _OWN.add(self._own)
            self._move(self._own)

        assert self._loop is not None
        return self._loop

    # Move the handles and timers to another loop
    def _move(self, new: asyncio.AbstractEventLoop) -> None:
        old, self._loop = self._loop, new
        alive = old is not None and not old.is_closed()
        for id, timer in self._timers.items():
            handle = timer['handle']
            after = timer['after']
            if old is not None and alive and isinstance(handle, asyncio.TimerHandle):
                after = max(0.0, handle.when() - old.time())
            handle.cancel()
            timer['handle'] = self._schedule(new, after, id)
        for fd, io in self._io.items():
            if old is not None and alive:
                if io['read']:
                    old.remove_reader(fd)
                if io['write']:
                    old.remove_writer(fd)
            if io['read']:
                new.add_reader(fd, Pyjo_Reactor_Asyncio._weak_ready, weakref.ref(self), fd, False)
            if io['write']:
                new.add_writer(fd, Pyjo_Reactor_Asyncio._weak_ready, weakref.ref(self), fd, True)

    def again(self, id: str, after: float | None = None) -> None:
        """::

            reactor.again(id)
            reactor.again(id, 0.5)

        Restart timer and optionally change the invocation time. Note that this
        method requires an active timer.
        """
        if (timer := self._timers.get(id)) is None:
            Pyjo.Exception.object.throw('Timer not active')
        if after is not None:
            timer['after'] = after
        timer['handle'].cancel()
        timer['handle'] = self._schedule(self.loop, timer['after'], id)

    # Not in Mojolicious: a future of the loop
    def awaitable(self, promise: Any) -> Awaitable[None]:
        """::

            future = reactor.awaitable(promise)

        Return a future of :attr:`loop` that is done when the promise is
        fulfilled or rejected, so that ``await promise`` works in any task of
        the loop.
        """
        future: asyncio.Future[None] = self.loop.create_future()

        def settle(*values: Any) -> None:
            if not future.done():
                future.set_result(None)

        promise.then(settle, settle)
        return future

    # Not in Mojolicious: a task of the loop
    def run_coroutine(
        self, coro: Coroutine[Any, Any, Any], resolve: Callable[[Any], Any], reject: Callable[[Any], Any]
    ) -> None:
        """::

            reactor.run_coroutine(coro, resolve, reject)

        Run a coroutine as a task of :attr:`loop`, where it can await anything
        of the loop, and call ``resolve`` with what it returns or ``reject``
        with the exception it raises. A task that is not done is something to
        watch, so that :meth:`start` does not stop before it.
        """
        task = self.loop.create_task(coro)
        self._tasks.add(task)

        def done(task: asyncio.Task[Any]) -> None:
            self._tasks.discard(task)
            if task.cancelled():
                reject(asyncio.CancelledError())
            elif (e := task.exception()) is not None:
                reject(e)
            else:
                resolve(task.result())

        task.add_done_callback(done)

    # Not in Mojolicious: a future of the loop
    def future(self) -> asyncio.Future[Any]:
        """::

            future = reactor.future()

        Return a new :class:`asyncio.Future` of :attr:`loop`, which
        :meth:`Pyjo.Promise.Pyjo_Promise.to_future` turns a promise into.
        """
        return self.loop.create_future()

    def io(self, handle: Handle, cb: IOCallback) -> Self:
        """::

            reactor = reactor.io(handle, cb)

        Watch handle for I/O events, invoking the callback whenever handle
        becomes readable or writable. ::

            # Callback will be executed twice if handle becomes readable and writable
            reactor.io(handle, lambda reactor, writable: print('Handle is writable' if writable else 'Handle is readable'))
        """
        self._io[_fileno(handle)] = {'cb': cb, 'read': False, 'write': False}
        return self.watch(handle, True, True)

    @property
    def is_running(self) -> bool:
        """::

            boolean = reactor.is_running

        Check if reactor is running.
        """
        return bool(self._running)

    def next_tick(self, cb: TimerCallback) -> None:
        """::

            none = reactor.next_tick(cb)

        Execute callback as soon as possible, but not before returning or other
        callbacks that have been registered with this method, always returns
        ``None``.
        """
        self._next_tick.append(cb)
        if self._next_timer is None:
            self._next_timer = self.timer(0, Pyjo_Reactor_Asyncio._next)
        return None

    def one_tick(self) -> None:
        """::

            reactor.one_tick()

        Run reactor until an event occurs or no events are being watched
        anymore. ::

            # Don't block longer than 0.5 seconds
            id = reactor.timer(0.5, lambda reactor: None)
            reactor.one_tick()
            reactor.remove(id)
        """
        # Just one tick
        running = self._running
        if not running:
            self._running = 1

        try:
            # Stop automatically if there is nothing to watch
            if not len(self._timers) and not len(self._io) and not len(self._tasks):
                return self.stop()

            # Unlike Mojolicious: asyncio does not nest event loops, the one that runs already watches the events
            loop = self.loop
            if loop.is_running():
                return

            # Wait for one event
            self._one += 1
            try:
                loop.run_forever()
            finally:
                self._one -= 1

            # An exception of an unhandled error event
            if (error := self._error) is not None:
                self._error = None
                raise error
        finally:
            if not running:
                self._running = running

    def recurring(self, after: float, cb: TimerCallback) -> str:
        """::

            id = reactor.recurring(0.25, cb)

        Create a new recurring timer, invoking the callback repeatedly after a
        given amount of time in seconds.
        """
        return self._timer(True, after, cb)

    def remove(self, remove: Handle | str) -> bool:
        """::

            boolean = reactor.remove(handle)
            boolean = reactor.remove(id)

        Remove handle or timer.
        """
        if isinstance(remove, str):
            if (timer := self._timers.pop(remove, None)) is None:
                return False
            timer['handle'].cancel()
            return True
        fd = _fileno(remove)
        if (io := self._io.pop(fd, None)) is None:
            return False
        self._unwatch(fd, io)
        return True

    def reset(self) -> None:
        """::

            reactor.reset()

        Remove all handles and timers.
        """
        for fd, io in self._io.items():
            self._unwatch(fd, io)
        for timer in self._timers.values():
            timer['handle'].cancel()
        self._events = {}
        self._io = {}
        self._next_tick = []
        self._next_timer = None
        self._running = 0
        self._tasks = set()
        self._timers = {}
        self._stop()

    def start(self) -> None:
        """::

            reactor.start()

        Start watching for I/O and timer events, this will block until
        :meth:`stop` is called or no events are being watched anymore. ::

            # Start reactor only if it is not running already
            if not reactor.is_running:
                reactor.start()
        """
        running = self._running
        self._running = running + 1
        try:
            # Unlike Mojolicious: asyncio does not nest event loops, the one that runs already watches the events
            while self._running and not self.loop.is_running():
                self.one_tick()
        finally:
            self._running = running

    def stop(self) -> None:
        """::

            reactor.stop()

        Stop watching for I/O and timer events.
        """
        self._running = 0
        self._stop()

    def timer(self, after: float, cb: TimerCallback) -> str:
        """::

            id = reactor.timer(0.5, cb)

        Create a new timer, invoking the callback after a given amount of time
        in seconds.
        """
        return self._timer(False, after, cb)

    def watch(self, handle: Handle, read: bool, write: bool) -> Self:
        """::

            reactor = reactor.watch(handle, readable, writable)

        Change I/O events to watch handle for with true and false values. Note
        that this method requires an active I/O watcher. ::

            # Watch only for readable events
            reactor.watch(handle, True, False)

            # Watch only for writable events
            reactor.watch(handle, False, True)

            # Watch for readable and writable events
            reactor.watch(handle, True, True)

            # Pause watching for events
            reactor.watch(handle, False, False)
        """
        fd = _fileno(handle)
        if (io := self._io.get(fd)) is None:
            Pyjo.Exception.object.throw('I/O watcher not active')

        self._unwatch(fd, io)
        loop = self.loop
        if read:
            loop.add_reader(fd, Pyjo_Reactor_Asyncio._weak_ready, weakref.ref(self), fd, False)
        if write:
            loop.add_writer(fd, Pyjo_Reactor_Asyncio._weak_ready, weakref.ref(self), fd, True)
        io['read'], io['write'] = bool(read), bool(write)

        return self

    # A timer of no time runs before the I/O of the next iteration of the loop, as the timers of Mojo's reactor run in
    # the same tick, after its I/O; call_later would run it after the I/O of the next iteration
    def _schedule(self, loop: asyncio.AbstractEventLoop, after: float, id: str) -> asyncio.Handle:
        if after <= 0:
            return loop.call_soon(Pyjo_Reactor_Asyncio._weak_alarm, weakref.ref(self), id)
        return loop.call_later(after, Pyjo_Reactor_Asyncio._weak_alarm, weakref.ref(self), id)

    # The loop refers to the reactor weakly, so that the reactor and its loop do not make a cycle
    @staticmethod
    def _weak_alarm(ref: 'weakref.ref[Any]', id: str) -> None:
        if (reactor := ref()) is not None:
            reactor._alarm(id)

    @staticmethod
    def _weak_ready(ref: 'weakref.ref[Any]', fd: int, writable: bool) -> None:
        if (reactor := ref()) is not None:
            reactor._ready(fd, writable)

    # A timer is due
    def _alarm(self, id: str) -> None:
        if (timer := self._timers.get(id)) is None:
            return

        # Recurring timer
        if timer['recurring']:
            timer['handle'] = self._schedule(self.loop, timer['after'], id)

        # Normal timer
        else:
            self.remove(id)

        if (cb := timer['cb']) is not None:
            self._event('Timer', cb)

    # An event of a watcher or a timer, which ends one_tick
    def _event(self, what: str, cb: Any, *args: Any) -> None:
        try:
            self._try(what, cb, *args)
        except Exception as e:
            # Not in Mojolicious: asyncio logs an exception of a callback, Perl dies out of one_tick, so it is kept and
            # raised by one_tick, unless the loop runs without it
            if not self._one:
                raise
            self._error = e
        if self._one:
            self._stop()

    def _id(self) -> str:
        while True:
            id = md5_sum(f't{time.monotonic()}{random.random()}'.encode())
            if id not in self._timers:
                return id

    def _next(self) -> None:
        self._next_timer = None
        while len(self._next_tick):
            self._next_tick.pop(0)(self)

    # A handle is ready
    def _ready(self, fd: int, writable: bool) -> None:
        if (io := self._io.get(fd)) is not None:
            self._event('I/O watcher', io['cb'], writable)

    def _stop(self) -> None:
        if self._one and self.loop.is_running():
            self.loop.stop()

    def _timer(self, recurring: bool, after: float, cb: TimerCallback) -> str:
        id = self._id()
        handle = self._schedule(self.loop, after, id)
        self._timers[id] = {'cb': cb, 'after': after, 'recurring': recurring, 'handle': handle}
        return id

    def _try(self, what: str, cb: Any, *args: Any) -> None:
        try:
            cb(self, *args)
        except Exception as e:
            # Unlike Mojolicious: the message of Python has no file and line, the exception keeps the frames
            err = Pyjo.Exception.new(e)
            err.message = f'{what} failed: {err.message}'
            err.__cause__ = e
            self.emit('error', err)

    def _unwatch(self, fd: int, io: _IO) -> None:
        if io['read']:
            self.loop.remove_reader(fd)
        if io['write']:
            self.loop.remove_writer(fd)
        io['read'] = io['write'] = False


def _fileno(handle: Handle) -> int:
    fd = handle if isinstance(handle, int) else handle.fileno()
    if fd < 0:
        Pyjo.Exception.object.throw('Handle is closed')
    return fd


# Not in Mojolicious: the event loops that the reactors make for themselves, which are closed at the exit of the
# interpreter, before it finalizes the objects and the loops of the reactors that still exist would warn that they are
# not closed
_OWN: 'weakref.WeakSet[asyncio.AbstractEventLoop]' = weakref.WeakSet()


@atexit.register
def _close() -> None:
    for loop in list(_OWN):
        if not loop.is_running() and not loop.is_closed():
            loop.close()


new = Pyjo_Reactor_Asyncio.new
object = Pyjo_Reactor_Asyncio
