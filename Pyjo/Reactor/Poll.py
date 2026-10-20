"""
Pyjo.Reactor.Poll - Low-level event reactor with poll support
=============================================================
::

    from Pyjo.Reactor.Poll import Poll

    # Watch if handle becomes readable or writable
    reactor = Poll()
    reactor.io(first, lambda reactor, writable: print(
        'First handle is writable' if writable else 'First handle is readable'
    ))

    import Pyjo.Reactor.Poll

    # Watch if handle becomes readable or writable
    reactor = Pyjo.Reactor.Poll.new()
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

:mod:`Pyjo.Reactor.Poll` is a low-level event reactor based on
:func:`select.poll`, without asyncio. Windows has no :func:`select.poll`,
and :func:`select.select` takes its place there, which watches sockets only,
not pipes or files, up to 512 of them. ``PYJO_REACTOR`` selects it for
:mod:`Pyjo.IOLoop`::

    PYJO_REACTOR=Pyjo.Reactor.Poll

Events
------

:mod:`Pyjo.Reactor.Poll` inherits all events from :mod:`Pyjo.Reactor`.

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

import random
import select
import sys
import threading
import time

from typing import Any, Self, TypedDict


class _IO(TypedDict):
    cb: IOCallback
    mode: int


class _Timer(TypedDict):
    cb: TimerCallback | None
    after: float
    recurring: bool
    time: float


class Pyjo_Reactor_Poll(Pyjo.Reactor.object):
    """
    :mod:`Pyjo.Reactor.Poll` inherits all methods from :mod:`Pyjo.Reactor`
    and implements the following new ones.
    """

    def __init__(self) -> None:
        """::

            reactor = Pyjo.Reactor.Poll.new()

        Construct a new :mod:`Pyjo.Reactor.Poll` object.
        """
        super().__init__()
        self._io: dict[int, _IO] = {}
        self._next_tick: list[TimerCallback] = []
        self._next_timer: str | None = None
        self._running = 0
        self._timers: dict[str, _Timer] = {}

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
        timer['time'] = time.monotonic() + timer['after']

    def io(self, handle: Handle, cb: IOCallback) -> Self:
        """::

            reactor = reactor.io(handle, cb)

        Watch handle for I/O events, invoking the callback whenever handle
        becomes readable or writable. ::

            # Callback will be executed twice if handle becomes readable and writable
            reactor.io(handle, lambda reactor, writable: print('Handle is writable' if writable else 'Handle is readable'))
        """
        self._io[_fileno(handle)] = {'cb': cb, 'mode': 0}
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
            self._next_timer = self.timer(0, Pyjo_Reactor_Poll._next)
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
            # Wait for one event
            i = 0
            while not i and self._running:
                # Not in Mojolicious: the cleanups that finalizers deferred, before the reactor waits
                if Pyjo.Reactor._DEFERRED.get(threading.get_ident()):  # pyright: ignore[reportPrivateUsage]
                    Pyjo.Reactor._drain()  # pyright: ignore[reportPrivateUsage]

                # Stop automatically if there is nothing to watch
                if not len(self._timers) and not len(self._io):
                    return self.stop()

                # Calculate ideal timeout based on timers and round up to next millisecond
                first = min((t['time'] for t in self._timers.values()), default=None)
                timeout = first - time.monotonic() if first is not None else 0.5
                timeout = 0 if timeout <= 0 else int(timeout * 1000) + 1

                # I/O
                if len(self._io):
                    for fd, mode in _poll({fd: io['mode'] for fd, io in self._io.items()}, timeout):
                        if mode & (_POLLIN | _POLLPRI | _POLLNVAL | _POLLHUP | _POLLERR):
                            if (io := self._io.get(fd)) is None:
                                continue
                            i += 1
                            self._try('I/O watcher', io['cb'], False)
                        if not mode & _POLLOUT or (io := self._io.get(fd)) is None:
                            continue
                        i += 1
                        self._try('I/O watcher', io['cb'], True)

                # Wait for timeout if poll can't be used
                elif timeout:
                    time.sleep(timeout / 1000)

                # Timers (time should not change in between timers)
                now = time.monotonic()
                for id in list(self._timers):
                    if (t := self._timers.get(id)) is None:
                        continue
                    if t['time'] > now:
                        continue

                    # Recurring timer
                    if t['recurring']:
                        t['time'] = now + t['after']

                    # Normal timer
                    else:
                        self.remove(id)

                    if (cb := t['cb']) is not None:
                        i += 1
                        self._try('Timer', cb)
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
            return self._timers.pop(remove, None) is not None
        return self._io.pop(_fileno(remove), None) is not None

    def reset(self) -> None:
        """::

            reactor.reset()

        Remove all handles and timers.
        """
        self._events = {}
        self._io = {}
        self._next_tick = []
        self._next_timer = None
        self._running = 0
        self._timers = {}

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
            while self._running:
                self.one_tick()
        finally:
            self._running = running

    def stop(self) -> None:
        """::

            reactor.stop()

        Stop watching for I/O and timer events.
        """
        self._running = 0

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
        if (io := self._io.get(_fileno(handle))) is None:
            Pyjo.Exception.object.throw('I/O watcher not active')
        io['mode'] = 0
        if read:
            io['mode'] |= _POLLIN | _POLLPRI
        if write:
            io['mode'] |= _POLLOUT
        return self

    def _id(self) -> str:
        while True:
            id = md5_sum(f't{time.monotonic()}{random.random()}'.encode())
            if id not in self._timers:
                return id

    def _next(self) -> None:
        self._next_timer = None
        while len(self._next_tick):
            self._next_tick.pop(0)(self)

    def _timer(self, recurring: bool, after: float, cb: TimerCallback) -> str:
        id = self._id()
        self._timers[id] = {'cb': cb, 'after': after, 'recurring': recurring, 'time': time.monotonic() + after}
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


def _fileno(handle: Handle) -> int:
    fd = handle if isinstance(handle, int) else handle.fileno()
    if fd < 0:
        Pyjo.Exception.object.throw('Handle is closed')
    return fd


# The events of poll, which Windows does not have, with the values of Linux there
if sys.platform == 'win32':
    _POLLIN, _POLLPRI, _POLLOUT, _POLLERR, _POLLHUP, _POLLNVAL = 0x001, 0x002, 0x004, 0x008, 0x010, 0x020
else:
    _POLLIN, _POLLPRI, _POLLOUT = select.POLLIN, select.POLLPRI, select.POLLOUT
    _POLLERR, _POLLHUP, _POLLNVAL = select.POLLERR, select.POLLHUP, select.POLLNVAL


# The events of the handles that are ready, in the time in milliseconds
def _poll(modes: dict[int, int], timeout: int) -> list[tuple[int, int]]:
    if sys.platform == 'win32':
        return _select(modes, timeout)
    poll = select.poll()
    for fd, mode in modes.items():
        poll.register(fd, mode)
    return poll.poll(timeout)


# Not in Mojolicious: Windows has no poll, and its select, which watches sockets only, takes the place of it; a
# connection that failed is an exceptional condition there, which poll reports as an error and writable, and the
# selector of asyncio as writable
def _select(modes: dict[int, int], timeout: int) -> list[tuple[int, int]]:
    readers = [fd for fd, mode in modes.items() if mode & (_POLLIN | _POLLPRI)]
    writers = [fd for fd, mode in modes.items() if mode & _POLLOUT]
    if not len(readers) and not len(writers):
        time.sleep(timeout / 1000)
        return []
    try:
        readable, writable, failed = select.select(readers, writers, writers, timeout / 1000)
    except OSError:
        # A handle that is closed, which poll reports as invalid
        if not len(invalid := [fd for fd in modes if not _is_valid(fd)]):
            raise
        return [(fd, _POLLNVAL) for fd in invalid]
    events: dict[int, int] = {}
    for fd in readable:
        events[fd] = events.get(fd, 0) | _POLLIN
    for fd in writable:
        events[fd] = events.get(fd, 0) | _POLLOUT
    for fd in failed:
        events[fd] = events.get(fd, 0) | _POLLERR | _POLLOUT
    return list(events.items())


def _is_valid(fd: int) -> bool:
    try:
        select.select([fd], [], [], 0)
    except OSError:
        return False
    return True


new = Pyjo_Reactor_Poll.new
object = Pyjo_Reactor_Poll
Poll = Pyjo_Reactor_Poll
