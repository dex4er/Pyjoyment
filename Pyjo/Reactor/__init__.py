"""
Pyjo.Reactor - Low-level event reactor base class
=================================================
::

    import Pyjo.Reactor

    class MyEventLoop(Pyjo.Reactor.object):
        def again(self, id, after=None): ...
        def io(self, handle, cb): ...
        @property
        def is_running(self): ...
        def next_tick(self, cb): ...
        def one_tick(self): ...
        def recurring(self, after, cb): ...
        def remove(self, remove): ...
        def reset(self): ...
        def start(self): ...
        def stop(self): ...
        def timer(self, after, cb): ...
        def watch(self, handle, read, write): ...

:mod:`Pyjo.Reactor` is an abstract base class for low-level event reactors,
like :mod:`Pyjo.Reactor.Asyncio`.

Events
------

:mod:`Pyjo.Reactor` inherits all events from :mod:`Pyjo.EventEmitter` and can
emit the following new ones.

error
~~~~~
::

    reactor.on('error', lambda reactor, err: ...)

Emitted for exceptions caught in callbacks, fatal if unhandled. Note that if
this event is unhandled or fails it might kill your program, so you need to be
careful. ::

    reactor.on('error', lambda reactor, err: print(f'Something very bad happened: {err}'))

Alternative reactors
--------------------

:mod:`Pyjo.Reactor` is a namespace that other distributions can add reactors
to, and the ``PYJO_REACTOR`` environment variable selects one for
:mod:`Pyjo.IOLoop`. A reactor on another implementation of the asyncio event
loop, like uvloop, is a subclass of :mod:`Pyjo.Reactor.Asyncio`, and one on
an event loop that is not asyncio's, like the ones of Trio or gevent,
implements the methods of :mod:`Pyjo.Reactor`.

A reactor is a module named ``Pyjo.Reactor.<Name>``, with a function ``new``
that constructs it and the class as ``object``, as the modules of Pyjoyment
have them. ::

    # Pyjo/Reactor/MyLoop.py of another distribution
    import Pyjo.Reactor.Asyncio

    import asyncio
    import selectors

    class Pyjo_Reactor_MyLoop(Pyjo.Reactor.Asyncio.object):
        def __init__(self, loop=None):
            super().__init__(loop=loop or asyncio.SelectorEventLoop(selectors.SelectSelector()))

    new = Pyjo_Reactor_MyLoop.new
    object = Pyjo_Reactor_MyLoop

The distribution contains the module and no ``__init__.py`` of ``Pyjo`` or
``Pyjo.Reactor``: those of Pyjoyment have the base class and keep the
namespace open with :func:`pkgutil.extend_path`, and another one would
replace them when both are installed in the same directory. Its package
depends on Pyjoyment and holds only the files of its own reactor::

    Pyjo/
        Reactor/
            MyLoop.py

The reactor is found when the distribution is installed next to Pyjoyment or
in another directory of :data:`sys.path`, and the environment variable
selects it::

    PYJO_REACTOR=Pyjo.Reactor.MyLoop

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Reactor <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Reactor.pm>`_
of Mojolicious 9.49.
"""

import Pyjo.EventEmitter

from Pyjo.Loader import load_class

import builtins
import os

from collections.abc import Awaitable, Callable, Coroutine, Generator
from pkgutil import extend_path
from typing import Any, Protocol, Self


type Anything = builtins.object


class HasFileno(Protocol):
    def fileno(self) -> int: ...


# A handle to watch: an object with a fileno() method, or a file descriptor
type Handle = HasFileno | int

# A callback of an I/O watcher gets the reactor and whether the handle is writable
type IOCallback = Callable[[Any, bool], Anything]

# A callback of a timer gets the reactor
type TimerCallback = Callable[[Any], Anything]

_DETECTED: dict[str, str] = {}

# Not in Mojolicious: a namespace that other distributions can add reactors to
__path__ = extend_path(__path__, __name__)


class Pyjo_Reactor(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.Reactor` inherits all methods from :mod:`Pyjo.EventEmitter` and
    implements the following new ones.
    """

    def again(self, id: str, after: float | None = None) -> None:
        """::

            reactor.again(id)
            reactor.again(id, 0.5)

        Restart timer and optionally change the invocation time. Meant to be
        overloaded in a subclass. Note that this method requires an active
        timer.
        """
        raise NotImplementedError('Method "again" not implemented by subclass')

    # Not in Mojolicious: what awaiting a promise of Pyjoyment waits on
    def awaitable(self, promise: Any) -> Awaitable[None]:
        """::

            awaitable = reactor.awaitable(promise)

        Return what ``await promise`` waits on, which completes when the
        promise is fulfilled or rejected. The base class gives one that
        :meth:`coroutine` drives, without asyncio, and a reactor of an event
        loop gives one of its loop, so that a promise can be awaited in the
        tasks of that loop.
        """
        return _Awaitable(promise)

    # Not in Mojolicious: how a coroutine runs as a promise, as Mojo's async sub
    def coroutine(
        self, coro: Coroutine[Any, Any, Any], resolve: Callable[[Any], Anything], reject: Callable[[Any], Anything]
    ) -> None:
        """::

            reactor.coroutine(coro, resolve, reject)

        Run a coroutine and call ``resolve`` with what it returns or
        ``reject`` with the exception it raises. The base class runs it at
        once, until it waits for a promise, as Mojo runs an ``async sub``,
        and continues it when the promise is fulfilled or rejected, so that it
        can await the promises of Pyjoyment without asyncio. A reactor of an
        event loop runs it as a task of its loop, where it can await anything
        of that loop.
        """

        def step() -> None:
            try:
                waiting = coro.send(None)
            except StopIteration as e:
                resolve(e.value)
                return
            except Exception as e:
                reject(e)
                return
            then = getattr(waiting, 'then', None)
            if not callable(then):
                coro.close()
                reject(TypeError(f'{_name(type(self))} cannot wait for {waiting!r}'))
                return
            then(resume, resume)

        def resume(*values: Any) -> None:
            step()

        step()

    @classmethod
    def detect(cls) -> str:
        """::

            name = Pyjo.Reactor.detect()

        Detect and load the best reactor implementation available, will try
        the value of the ``PYJO_REACTOR`` environment variable or
        :mod:`Pyjo.Reactor.Asyncio`, and return the name of its module. ::

            # Instantiate best reactor implementation available
            reactor = sys.modules[Pyjo.Reactor.detect()].new()
        """
        # Left out from Mojolicious: Mojo::Reactor::EV, as asyncio is the event loop
        default = 'Pyjo.Reactor.Asyncio'
        tried = os.environ.get('PYJO_REACTOR') or default
        if tried not in _DETECTED:
            _DETECTED[tried] = default if load_class(tried) else tried
        load_class(_DETECTED[tried])
        return _DETECTED[tried]

    def io(self, handle: Handle, cb: IOCallback) -> Self:
        """::

            reactor = reactor.io(handle, cb)

        Watch handle for I/O events, invoking the callback whenever handle
        becomes readable or writable. Meant to be overloaded in a subclass. ::

            # Callback will be executed twice if handle becomes readable and writable
            reactor.io(handle, lambda reactor, writable: print('Handle is writable' if writable else 'Handle is readable'))
        """
        raise NotImplementedError('Method "io" not implemented by subclass')

    @property
    def is_running(self) -> bool:
        """::

            boolean = reactor.is_running

        Check if reactor is running. Meant to be overloaded in a subclass.
        """
        raise NotImplementedError('Method "is_running" not implemented by subclass')

    def next_tick(self, cb: TimerCallback) -> None:
        """::

            none = reactor.next_tick(cb)

        Execute callback as soon as possible, but not before returning or other
        callbacks that have been registered with this method, always returns
        ``None``. Meant to be overloaded in a subclass.
        """
        raise NotImplementedError('Method "next_tick" not implemented by subclass')

    def one_tick(self) -> None:
        """::

            reactor.one_tick()

        Run reactor until an event occurs. Note that this method can recurse
        back into the reactor, so you need to be careful. Meant to be
        overloaded in a subclass. ::

            # Don't block longer than 0.5 seconds
            id = reactor.timer(0.5, lambda reactor: None)
            reactor.one_tick()
            reactor.remove(id)
        """
        raise NotImplementedError('Method "one_tick" not implemented by subclass')

    def recurring(self, after: float, cb: TimerCallback) -> str:
        """::

            id = reactor.recurring(0.25, cb)

        Create a new recurring timer, invoking the callback repeatedly after a
        given amount of time in seconds. Meant to be overloaded in a subclass.
        """
        raise NotImplementedError('Method "recurring" not implemented by subclass')

    def remove(self, remove: Handle | str) -> bool:
        """::

            boolean = reactor.remove(handle)
            boolean = reactor.remove(id)

        Remove handle or timer. Meant to be overloaded in a subclass.
        """
        raise NotImplementedError('Method "remove" not implemented by subclass')

    def reset(self) -> None:
        """::

            reactor.reset()

        Remove all handles and timers. Meant to be overloaded in a subclass.
        """
        raise NotImplementedError('Method "reset" not implemented by subclass')

    def start(self) -> None:
        """::

            reactor.start()

        Start watching for I/O and timer events, this will block until
        :meth:`stop` is called. Note that some reactors stop automatically if
        there are no events being watched anymore. Meant to be overloaded in a
        subclass. ::

            # Start reactor only if it is not running already
            if not reactor.is_running:
                reactor.start()
        """
        raise NotImplementedError('Method "start" not implemented by subclass')

    def stop(self) -> None:
        """::

            reactor.stop()

        Stop watching for I/O and timer events. Meant to be overloaded in a
        subclass.
        """
        raise NotImplementedError('Method "stop" not implemented by subclass')

    def timer(self, after: float, cb: TimerCallback) -> str:
        """::

            id = reactor.timer(0.5, cb)

        Create a new timer, invoking the callback after a given amount of time
        in seconds. Meant to be overloaded in a subclass.
        """
        raise NotImplementedError('Method "timer" not implemented by subclass')

    def watch(self, handle: Handle, read: bool, write: bool) -> Self:
        """::

            reactor = reactor.watch(handle, readable, writable)

        Change I/O events to watch handle for with true and false values.
        Meant to be overloaded in a subclass. Note that this method requires an
        active I/O watcher. ::

            # Watch only for readable events
            reactor.watch(handle, True, False)

            # Watch only for writable events
            reactor.watch(handle, False, True)

            # Watch for readable and writable events
            reactor.watch(handle, True, True)

            # Pause watching for events
            reactor.watch(handle, False, False)
        """
        raise NotImplementedError('Method "watch" not implemented by subclass')


# What the base class gives to await: it waits for the promise itself
class _Awaitable:
    def __init__(self, promise: Any) -> None:
        self.promise = promise

    def __await__(self) -> Generator[Any, Any, None]:
        yield self.promise


def _name(cls: type) -> str:
    return f'{cls.__module__}.{cls.__qualname__}'


detect = Pyjo_Reactor.detect
new = Pyjo_Reactor.new
object = Pyjo_Reactor
