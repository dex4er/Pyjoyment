"""
Pyjo.EventEmitter - Event emitter base class
============================================
::

    import Pyjo.EventEmitter

    class Cat(Pyjo.EventEmitter.object):
        # Emit events
        def poke(self):
            self.emit('roar', 3)

    # Subscribe to events
    tiger = Cat.new()

    @tiger.on('roar')
    def roar(tiger, times):
        for _ in range(times):
            print('RAWR!')

    tiger.poke()

:mod:`Pyjo.EventEmitter` is a simple base class for event emitting objects.

Events
------

:mod:`Pyjo.EventEmitter` can emit the following events.

error
~~~~~
::

    e.on('error', lambda e, err: ...)

This is a special event for errors, it will not be emitted directly by this
class, but is fatal if unhandled. Subclasses may choose to emit it, but are
not required to do so. ::

    e.on('error', lambda e, err: print(f'This looks bad: {err}'))

An unhandled error raises a :mod:`Pyjo.Exception` with the name of the class
and the error in its message, and an error that is an exception is its cause.

Debugging
---------

You can set the ``PYJO_EVENTEMITTER_DEBUG`` environment variable to get some
advanced diagnostics information printed to ``sys.stderr``. ::

    PYJO_EVENTEMITTER_DEBUG=1

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::EventEmitter <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/EventEmitter.pm>`_
of Mojolicious 9.49.
"""

import Pyjo.Base
import Pyjo.Exception

from Pyjo.Util import warn

import os
import weakref

from collections.abc import Callable
from typing import Any, Self, overload


# A subscriber gets the emitter and the arguments of the event
type Callback = Callable[..., Any]

DEBUG = bool(os.environ.get('PYJO_EVENTEMITTER_DEBUG'))


class Pyjo_EventEmitter(Pyjo.Base.object):
    """
    :mod:`Pyjo.EventEmitter` inherits all methods from :mod:`Pyjo.Base` and
    implements the following new ones.
    """

    def __init__(self) -> None:
        self._events: dict[str, list[Callback]] = {}

    def catch(self, cb: Callback) -> Self:
        """::

            e = e.catch(lambda e, err: ...)

        Subscribe to the ``error`` event. ::

            # Longer version
            e.on('error', lambda e, err: ...)
        """
        self.on('error', cb)
        return self

    def emit(self, name: str, *args: Any) -> Self:
        """::

            e = e.emit('foo')
            e = e.emit('foo', 123)

        Emit event.
        """
        # Unlike Mojolicious: an empty list of subscribers, as subscribers() leaves it, is no subscriber, and Mojo
        # swallows an unhandled error then
        if s := self._events.get(name):
            if DEBUG:
                warn(f'-- Emit {name} in {_name(type(self))} ({len(s)})')
            for cb in s:
                cb(self, *args)
        else:
            if DEBUG:
                warn(f'-- Emit {name} in {_name(type(self))} (0)')
            if name == 'error':
                err = args[0] if args else ''
                e = Pyjo.Exception.new(f'{_name(type(self))}: {err}')
                # Not in Mojolicious: an error that is an exception is the cause
                if isinstance(err, BaseException):
                    raise e from err
                raise e

        return self

    def has_subscribers(self, name: str) -> bool:
        """::

            boolean = e.has_subscribers('foo')

        Check if event has subscribers.
        """
        # Unlike Mojolicious: an empty list of subscribers is no subscriber
        return bool(self._events.get(name))

    @overload
    def on[F: Callback](self, name: F, cb: None = None) -> F: ...

    @overload
    def on[F: Callback](self, name: str, cb: None = None) -> Callable[[F], F]: ...

    @overload
    def on[F: Callback](self, name: str, cb: F) -> F: ...

    def on(self, name: str | Callback, cb: Callback | None = None) -> Any:
        """::

            cb = e.on('foo', lambda e, *args: ...)

        Subscribe to event. ::

            e.on('foo', lambda e, *args: ...)

        Without a callback, it is a decorator, with the name of the event or
        of the function. ::

            @e.on('foo')
            def cb(e, *args):
                ...

            @e.on
            def foo(e, *args):
                ...
        """
        # Not in Mojolicious: a decorator
        if not isinstance(name, str):
            return self.on(name.__name__, name)
        if cb is None:
            event = name

            def decorator(cb: Callback) -> Callback:
                return self.on(event, cb)

            return decorator

        self._events.setdefault(name, []).append(cb)
        return cb

    @overload
    def once(self, name: Callback, cb: None = None) -> Callback: ...

    @overload
    def once(self, name: str, cb: None = None) -> Callable[[Callback], Callback]: ...

    @overload
    def once(self, name: str, cb: Callback) -> Callback: ...

    def once(self, name: str | Callback, cb: Callback | None = None) -> Any:
        """::

            cb = e.once('foo', lambda e, *args: ...)

        Subscribe to event and unsubscribe again after it has been emitted
        once. ::

            e.once('foo', lambda e, *args: ...)

        Without a callback, it is a decorator, as :meth:`on` is.
        """
        # Not in Mojolicious: a decorator
        if not isinstance(name, str):
            return self.once(name.__name__, name)
        event = name
        if cb is None:

            def once_decorator(cb: Callback) -> Callback:
                return self.once(event, cb)

            return once_decorator

        wrapper = _Once(weakref.proxy(self), event, cb)
        self.on(event, wrapper)

        return wrapper

    def subscribers(self, name: str) -> list[Callback]:
        """::

            subscribers = e.subscribers('foo')

        All subscribers for event. ::

            # Unsubscribe last subscriber
            e.unsubscribe('foo', e.subscribers('foo')[-1])

            # Change order of subscribers
            e.subscribers('foo').reverse()
        """
        return self._events.setdefault(name, [])

    def unsubscribe(self, name: str, cb: Callback | None = None) -> Self:
        """::

            e = e.unsubscribe('foo')
            e = e.unsubscribe('foo', cb)

        Unsubscribe from event.
        """
        # One
        if cb is not None:
            self._events[name] = [c for c in self._events.get(name, []) if c != cb]
            if not self._events[name]:
                del self._events[name]

        # All
        else:
            self._events.pop(name, None)

        return self


# The wrapper of once, which unsubscribes itself as the argument of its call, as Mojo does with __SUB__: a closure that
# refers to itself is a cycle, which keeps the callback, and the objects of its closure, until the garbage collector runs
class _Once:
    __slots__ = ('cb', 'emitter', 'event')

    def __init__(self, emitter: Pyjo_EventEmitter, event: str, cb: Callback) -> None:
        self.cb, self.emitter, self.event = cb, emitter, event

    def __call__(self, *args: Any) -> Any:
        self.emitter.unsubscribe(self.event, self)
        return self.cb(*args)


# The name of a class, as Perl's blessed gives the name of a package
def _name(cls: type) -> str:
    return f'{cls.__module__}.{cls.__qualname__}'


new = Pyjo_EventEmitter.new
object = Pyjo_EventEmitter
