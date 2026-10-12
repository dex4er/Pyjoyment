"""
Pyjo.Reactor.Base - Low-level event reactor base class
======================================================
::

    import Pyjo.Reactor.Base
    class MyEventLoop(Pyjo.Reactor.Base.object):

        def again(self, tid):
            ...

        def io(self, cb, handle):
            ...

        def is_running(self):
            ...

        def one_tick(self):
            ...

        def recurring(self, cb, after):
            ...

        def remove(self, remove):
            ...

        def reset(self):
            ...

        def start(self):
            ...

        def stop(self):
            ...

        def timer(self, cb, after):
            ...

        def watch(self, handle, read, write):
            ...

:mod:`Pyjo.Reactor.Base` is an abstract base class for low-level event reactors.

Events
------

:mod:`Pyjo.Reactor.Base` inherits all events from :mod:`Pyjo.EventEmitter` and can emit
the following new ones.

error
~~~~~
::

    @reactor.on
    def error(reactor, e, event):
        ...

Emitted for exceptions caught in callbacks, fatal if unhandled. Note that if
this event is unhandled or fails it might kill your program, so you need to be
careful.

Classes
-------
"""

import Pyjo.EventEmitter

from Pyjo.Util import getenv, not_implemented

import importlib
import select


class Error(Exception):
    """
    Exception raised on unhandled error event.
    """

    pass


class Pyjo_Reactor_Base(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.Reactor` inherits all attributes and methods from
    :mod:`Pyjo.EventEmitter` and implements the following new ones.
    """

    @not_implemented
    def again(self, tid):
        """::

            reactor.again(tid)

        Restart active timer. Meant to be overloaded in a subclass.
        """
        pass

    @classmethod
    def detect(self, reactor=None):
        """::

            cls = Pyjo.Reactor.detect()
            cls = Pyjo.Reactor.detect('Pyjo.Reactor.EV')

        Detect and load the best reactor implementation available, will try the value
        of the argument or ``PYJO_REACTOR`` environment variable, then
        :mod:`Pyjo.Reactor.Poll` if available or :mod:`Pyjo.Reactor.Select` otherwise. ::

            # Instantiate best reactor implementation available
            reactor = Pyjo.Reactor.detect().new()
        """
        if reactor is None:
            reactor = getenv('PYJO_REACTOR')

        if reactor:
            try:
                importlib.import_module(reactor)
                return reactor
            except ImportError:
                pass

        if hasattr(select, 'poll'):
            return 'Pyjo.Reactor.Poll'
        else:
            return 'Pyjo.Reactor.Select'

    @not_implemented
    def io(self, cb, handle):
        """::

            reactor = reactor.io(cb, handle)

        Watch handle for I/O events, invoking the callback whenever handle becomes
        readable or writable. Meant to be overloaded in a subclass. ::

            # Callback will be invoked twice if handle becomes readable and writable
            def cb(reactor, writable):
                if writable:
                    print('Handle is writable')
                else:
                    print('Handle is readable')

            reactor.io(cb, handle)
        """
        pass

    @not_implemented
    def is_running(self):
        """::

            boolean = reactor.is_running

        Check if reactor is running. Meant to be overloaded in a subclass.
        """
        pass

    def next_tick(self, cb):
        """::

            reactor.next_tick(cb)

        Invoke callback as soon as possible, but not before returning.
        """
        self.timer(cb, 0)

    @not_implemented
    def one_tick(self):
        """::

            reactor.one_tick()

        Run reactor until an event occurs. Note that this method can recurse back into
        the reactor, so you need to be careful. Meant to be overloaded in a subclass. ::

            # Don't block longer than 0.5 seconds
            tid = reactor.timer(cb, 0.5)
            reactor.one_tick()
            reactor.remove(tid)
        """
        pass

    @not_implemented
    def recurring(self, cb, after):
        """::

            tid = reactor.recurring(cb, 0.25)

        Create a new recurring timer, invoking the callback repeatedly after a given
        amount of time in seconds. Meant to be overloaded in a subclass.
        """
        pass

    @not_implemented
    def remove(self, remove):
        """::

            boolean = reactor.remove(handle)
            boolean = reactor.remove(tid)

        Remove handle or timer. Meant to be overloaded in a subclass.
        """
        pass

    @not_implemented
    def reset(self):
        """::

            reactor.reset()

        Remove all handles and timers. Meant to be overloaded in a subclass.
        """
        pass

    @not_implemented
    def start(self):
        """::

            reactor.start()

        Start watching for I/O and timer events, this will block until :meth:`stop` is
        called. Note that some reactors stop automatically if there are no events
        being watched anymore. Meant to be overloaded in a subclass. ::

            # Start reactor only if it is not running already
            if not reactor.is_running:
                reactor.start()
        """
        pass

    @not_implemented
    def stop(self):
        """::

            reactor.stop()

        Stop watching for I/O and timer events. Meant to be overloaded in a subclass.
        """
        pass

    @not_implemented
    def timer(self, cb, after):
        """::

            tid = reactor.timer(cb, 0.5)

        Create a new timer, invoking the callback after a given amount of time in
        seconds. Meant to be overloaded in a subclass.
        """
        pass

    @not_implemented
    def watch(self, handle, read, write):
        """::

            reactor = reactor.watch(handle, read, write)

        Change I/O events to watch handle for with true and false values. Meant to be
        overloaded in a subclass. Note that this method requires an active I/O
        watcher. ::

            # Watch only for readable events
            reactor.watch(handle, read=True, write=False)

            # Watch only for writable events
            reactor.watch(handle, read=False, write=True)

            # Watch for readable and writable events
            reactor.watch(handle, read=True, write=True)

            # Pause watching for events
            reactor.watch(handle, read=False, write=False)
        """
        pass


detect = Pyjo_Reactor_Base.detect

new = Pyjo_Reactor_Base.new
object = Pyjo_Reactor_Base
