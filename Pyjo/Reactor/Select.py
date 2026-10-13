"""
Pyjo.Reactor.Select - Low-level event reactor with select support
=================================================================
::

    import Pyjo.Reactor.Select

    # Watch if handle becomes readable or writable
    reactor = Pyjo.Reactor.Select.new()

    def io_cb(reactor, writable):
        if writable:
            print('Handle is writable')
        else:
            print('Handle is readable')

    reactor.io(io_cb, handle)

    # Change to watching only if handle becomes writable
    reactor.watch(handle, read=False, write=True)

    # Add a timer
    def timer_cb(reactor):
        reactor.remove(handle)
        print('Timeout!')

    reactor.timer(timer_cb, 15)

    # Start reactor if necessary
    if not reactor.is_running:
        reactor.start()

:mod:`Pyjo.Reactor.Select` is a low-level event reactor based on :meth:`select.select`.

Events
------

:mod:`Pyjo.Reactor.Select` inherits all events from :mod:`Pyjo.Reactor.Base`.

Debugging
---------

You can set the ``PYJO_REACTOR_DEBUG`` environment variable to get some
advanced diagnostics information printed to ``stderr``. ::

    PYJO_REACTOR_DEBUG=1

You can set the ``PYJO_REACTOR_DIE`` environment variable to make reactor die if task
dies with exception.

    PYJO_REACTOR_DIE=1

Classes
-------
"""

import Pyjo.Reactor.Base

from Pyjo.Util import getenv, md5_sum, rand, steady_time, warn

import errno
import select
import time


DEBUG = getenv('PYJO_REACTOR_DEBUG', False)
DIE = getenv('PYJO_REACTOR_DIE', False)


class Pyjo_Reactor_Select(Pyjo.Reactor.Base.object):
    """
    :mod:`Pyjo.Reactor.Select` inherits all attributes and methods from
    :mod:`Pyjo.Reactor.Base` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._running = False
        self._select_select = None
        self._timers = {}
        self._ios = {}

        self._inputs = []
        self._outputs = []

    def again(self, tid):
        """::

            reactor.again(tid)

        Restart active timer.
        """
        timer = self._timers[tid]
        timer['time'] = steady_time() + timer['after']

    def io(self, cb, handle):
        """::

            reactor = reactor.io(cb, handle)

        Watch handle for I/O events, invoking the callback whenever handle becomes
        readable or writable.
        """
        fd = handle.fileno()
        if fd in self._ios:
            self._ios[fd]['cb'] = cb
            if DEBUG:
                warn(f'-- Reactor found io[{fd}] = {self._ios[fd]}')
        else:
            self._ios[fd] = {'cb': cb}
            if DEBUG:
                warn(f'-- Reactor adding io[{fd}] = {self._ios[fd]}')
        return self.watch(handle, True, True)

    @property
    def is_running(self):
        """::

            boolean = reactor.is_running

        Check if reactor is running.
        """
        return self._running

    def one_tick(self):
        """::

            reactor.one_tick()

        Run reactor until an event occurs. Note that this method can recurse back into
        the reactor, so you need to be careful. Meant to be overloaded in a subclass.
        """
        # Remember state for later
        running = self._running
        self._running = True

        # Wait for one event
        last = False
        while not last and self._running:
            # Stop automatically if there is nothing to watch
            if not self._timers and not self._ios:
                return self.stop()

            # Calculate ideal timeout based on timers
            times = [t['time'] for t in self._timers.values()]
            if times:
                timeout = min(times) - steady_time()
            else:
                timeout = 0.5

            if timeout < 0:
                timeout = 0

            # I/O
            if self._ios and (self._inputs or self._outputs):
                try:
                    readable, writable, exceptional = select.select(self._inputs, self._outputs, self._inputs, timeout)
                    for fd in list(set([item for sublist in (exceptional, readable, writable) for item in sublist])):
                        if fd in self._ios:
                            if fd in readable or fd in exceptional:
                                io = self._ios[fd]
                                last = True
                                self._sandbox(io['cb'], f'Read fd {fd}', False)
                        if fd in self._ios:
                            if fd in writable:
                                io = self._ios[fd]
                                last = True
                                self._sandbox(io['cb'], f'Write fd {fd}', True)
                except OSError as e:
                    # Ctrl-c generates EINTR on Python 2.x
                    if e.args[0] != errno.EINTR:
                        raise Exception(e) from e

            # Wait for timeout if poll can't be used
            elif timeout:
                time.sleep(timeout)

            # Timers (time should not change in between timers)
            now = steady_time()
            for tid in list(self._timers):
                if tid not in self._timers:
                    continue

                t = self._timers[tid]

                if t['time'] > now:
                    continue

                # Recurring timer
                if 'recurring' in t:
                    t['time'] = now + t['recurring']

                # Normal timer
                else:
                    self.remove(tid)

                last = True
                if t['cb']:
                    if DEBUG:
                        warn(f'-- Alarm timer[{tid}] = {t}')
                    self._sandbox(t['cb'], f'Timer {tid}')

        # Restore state if necessary
        if self._running:
            self._running = running

    def recurring(self, cb, after):
        """::

            tid = reactor.recurring(cb, 0.25)

        Create a new recurring timer, invoking the callback repeatedly after a given
        amount of time in seconds.
        """
        return self._timer(cb, True, after)

    def remove(self, remove):
        """::

            boolean = reactor.remove(handle)
            boolean = reactor.remove(tid)

        Remove handle or timer.
        """
        if remove is None:
            if DEBUG:
                warn('-- Reactor remove None')
            return

        if isinstance(remove, str):
            if DEBUG:
                if remove in self._timers:
                    warn(f'-- Reactor remove timer[{remove}] = {self._timers[remove]}')
                else:
                    warn(f'-- Reactor remove timer[{remove}] = None')
            if remove in self._timers:
                del self._timers[remove]
                return True

            return False

        elif remove is not None:
            try:
                fd = remove.fileno()
                if DEBUG:
                    if fd in self._ios:
                        warn(f'-- Reactor remove io[{fd}]')
                if fd in self._inputs:
                    self._inputs.remove(fd)
                if fd in self._outputs:
                    self._outputs.remove(fd)
                if fd in self._ios:
                    del self._ios[fd]
                    return True
            except OSError:
                if DEBUG:
                    warn(f'-- Reactor remove io {remove} already closed')

        return False

    def reset(self):
        """::

            reactor.reset()

        Remove all handles and timers.
        """
        self._ios = {}
        self._inputs = []
        self._outputs = []
        self._timers = {}

    def start(self):
        """::

            reactor.start()

        Start watching for I/O and timer events, this will block until :meth:`stop` is
        called or there is no any active I/O or timer event.
        """
        self._running = True
        while self._running:
            self.one_tick()

    def stop(self):
        """::

            reactor.stop()

        Stop watching for I/O and timer events.
        """
        self._running = False

    def timer(self, cb, after):
        """::

            tid = reactor.timer(cb, 0.5)

        Create a new timer, invoking the callback after a given amount of time in
        seconds.
        """
        return self._timer(cb, False, after)

    def watch(self, handle, read, write):
        """::

            reactor = reactor.watch(handle, read, write)

        Change I/O events to watch handle for with true and false values. Meant to be
        overloaded in a subclass. Note that this method requires an active I/O
        watcher.
        """
        fd = handle.fileno()

        if read:
            if fd not in self._inputs:
                self._inputs.append(fd)
        else:
            if fd in self._inputs:
                self._inputs.remove(fd)

        if write:
            if fd not in self._outputs:
                self._outputs.append(fd)
        else:
            if fd in self._outputs:
                self._outputs.remove(fd)

        return self

    def _sandbox(self, cb, event, *args):
        if DIE:
            cb(self, *args)
        else:
            try:
                cb(self, *args)
            except Exception as e:
                self.emit('error', e, event)

    def _timer(self, cb, recurring, after):
        tid = None
        while True:
            tid = md5_sum(f't{steady_time()}{rand()}'.encode('ascii'))
            if tid not in self._timers:
                break

        timer = {'cb': cb, 'after': after, 'time': steady_time() + after}
        if recurring:
            timer['recurring'] = after
        self._timers[tid] = timer

        if DEBUG:
            warn(f'-- Reactor adding timer[{tid}] = {self._timers[tid]}')

        return tid


new = Pyjo_Reactor_Select.new
object = Pyjo_Reactor_Select
