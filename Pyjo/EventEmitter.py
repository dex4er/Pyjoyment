# flake8: ignore=E731

"""
Pyjo.EventEmitter - Event emitter base class
============================================
::

    import Pyjo.EventEmitter

    class Cat(Pyjo.EventEmitter.object):
        # Emit events
        def poke(self, times):
            self.emit('roar', 3)

    # Subscribe to events
    tiger = Cat.new()

    @tiger.on
    def road(cat, times):
        for _ in range(0, times):
            print('RAWR!')

    tiger.poke()

:mod:`Pyjo.EventEmitter` is a simple base class for event emitting objects.

Events
------

:mod:`Pyjo.EventEmitter` can emit the following events.

error
~~~~~
::

    @e.on
    def error(e, err):
        ...

This is a special event for errors, it will not be emitted directly by this
class but is fatal if unhandled. ::

    @e.on
    def error(e, err):
        print("This looks bad: {0}".format(err))

Debugging
---------

You can set the ``PYJO_EVENTEMITTER_DEBUG`` environment variable to get some
advanced diagnostics information printed to ``stderr``. ::

    PYJO_EVENTEMITTER_DEBUG=1

Classes
-------
"""

import Pyjo.Base

from Pyjo.Util import getenv, isalive, warn

import weakref


DEBUG = getenv('PYJO_EVENTEMITTER_DEBUG', False)


class Error(Exception):
    """
    Exception raised on unhandled error event.
    """
    pass


class Pyjo_EventEmitter(Pyjo.Base.object):
    """
    :mod:`Pyjo.EventEmitter` inherits all attributes and methods from
    :mod:`Pyjo.Base` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        self._events = {}

    def catch(self, cb):
        """::

            e = e.catch(lambda e, err: ...)

            @e.catch
            def cb(e, err):
                ...

        Subscribe to ``error`` event. ::

            # Longer version
            @e.on
            def error(e, err):
                ...
        """
        self.on(cb, 'error')
        return self

    def emit(self, name, *args, **kwargs):
        """::

            e = e.emit('foo')
            e = e.emit('foo', 123)

        Emit event.
        """
        if name in self._events:
            s = self._events[name]

            if DEBUG:
                warn("-- Emit {0} in {1} ({2})".format(name, self, len(s)))

            for cb in s:
                cb(self, *args, **kwargs)
        else:
            if DEBUG:
                warn("-- Emit {0} in {1} (0)".format(name, self))

            if name == 'error':
                raise Error(*args, **kwargs)

        return self

    def has_subscribers(self, name):
        """::

            boolean = e.has_subscribers('foo')

        Check if event has subscribers.
        """
        return name in self._events

    def on(self, cb, name=None):
        """::

            cb = e.on(cb, 'foo')

        Subscribe to event. Can be used as decorator. ::

            @e.on
            def foo(e, *args, **kwargs):
                ...
        """
        if not callable(cb):
            raise TypeError('cb argument is not callable')

        if name is None:
            name = cb.__name__

        if name in self._events:
            self._events[name].append(cb)
        else:
            self._events[name] = [cb]

        return cb

    def once(self, cb, name=None):
        """::

            cb = e.once(cb, 'foo')

        Subscribe to event and unsubscribe again after it has been emitted once.
        Can be used as decorator. ::

            @e.once
            def foo(e, *args, **kwargs):
                ...
        """
        if not callable(cb):
            raise TypeError('cb argument is not callable')

        if name is None:
            name = cb.__name__

        emitter = weakref.proxy(self)

        def wrap_cb(*args, **kwargs):
            if isalive(emitter):
                emitter.unsubscribe(name, wrap_cb)
                return cb(*args, **kwargs)

        wrap_cb.__name__ = name

        self.on(wrap_cb, name)

        return wrap_cb

    def subscribers(self, name):
        """::

            subscribers = e.subscribers('foo')

        All subscribers for event. ::

            # Unsubscribe last subscriber
            e.unsubscribe('foo', e.subscribers('foo')[-1])
        """
        if name in self._events:
            return self._events[name]
        else:
            return []

    def unsubscribe(self, name, cb=None):
        """::

            e = e.unsubscribe('foo')
            e = e.unsubscribe('foo', cb)

        Unsubscribe from event.
        """
        if name in self._events:
            # One
            if cb:
                self._events[name] = [c for c in self._events[name] if c != cb]
                if not len(self._events[name]):
                    del self._events[name]

            # All
            else:
                del self._events[name]

        return self

    def unsubscribe_all(self):
        """::

            e = e.unsubscribe_all()

        Unsubscribe from all events.
        """
        self._events = {}
        return self


new = Pyjo_EventEmitter.new
object = Pyjo_EventEmitter
