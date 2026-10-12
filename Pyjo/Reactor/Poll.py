"""
Pyjo.Reactor.Poll - Low-level event reactor with poll support
=============================================================
::

    import Pyjo.Reactor.Poll

    # Watch if handle becomes readable or writable
    reactor = Pyjo.Reactor.Poll.new()

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

:mod:`Pyjo.Reactor.Poll` is a low-level event reactor based on :meth:`select.poll`.

Events
------

:mod:`Pyjo.Reactor.Poll` inherits all events from :mod:`Pyjo.Reactor.Select`.

Classes
-------
"""

import Pyjo.Reactor.Select

from Pyjo.Util import getenv, steady_time, warn

import errno
import select
import time


DEBUG = getenv('PYJO_REACTOR_DEBUG', False)


class Pyjo_Reactor_Poll(Pyjo.Reactor.Select.object):
    """
    :mod:`Pyjo.Reactor.Poll` inherits all attributes and methods from
    :mod:`Pyjo.Reactor.Select` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._running = False
        self._select_poll = None
        self._timers = {}
        self._ios = {}

    def one_tick(self):
        """::

            reactor.one_tick()

        Run reactor until an event occurs. Note that this method can recurse back into
        the reactor, so you need to be careful. Meant to be overloaded in a subclass.
        """
        # Remember state for later
        running = self._running
        self._running = True

        poll = self._poll()

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

            if timeout <= 0:
                timeout = 0
            else:
                timeout = int(timeout * 1000) + 1

            # I/O
            if self._ios:
                try:
                    events = poll.poll(timeout)
                    for fd, flag in events:
                        if fd in self._ios:
                            if flag & (
                                select.POLLIN | select.POLLPRI | select.POLLNVAL | select.POLLHUP | select.POLLERR
                            ):
                                io = self._ios[fd]
                                last = True
                                self._sandbox(io['cb'], 'Read', False)
                        if fd in self._ios:
                            if flag & (select.POLLOUT):
                                io = self._ios[fd]
                                last = True
                                self._sandbox(io['cb'], 'Write', True)
                except OSError as e:
                    # Ctrl-c generates EINTR on Python 2.x
                    if e.args[0] != errno.EINTR:
                        raise Exception(e)

            # Wait for timeout if poll can't be used
            elif timeout:
                time.sleep(timeout / 1000)

            # Timers (time should not change in between timers)
            now = steady_time()
            for tid in list(self._timers):
                t = self._timers.get(tid)

                if not t or t['time'] > now:
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
                poll = self._poll()
                if poll:
                    poll.unregister(remove)
                if fd in self._ios:
                    del self._ios[fd]
                    return True
                # remove.close()  # TODO remove?
            except KeyError:
                if DEBUG:
                    warn(f'-- Reactor remove io {remove} already closed')
            except OSError:
                if DEBUG:
                    warn(f'-- Reactor remove io {remove} already closed')
                pass

        return False

    def reset(self):
        """::

            reactor.reset()

        Remove all handles and timers.
        """
        self._ios = {}
        self._select_poll = None
        self._timers = {}

    def watch(self, handle, read, write):
        """::

            reactor = reactor.watch(handle, read, write)

        Change I/O events to watch handle for with true and false values. Meant to be
        overloaded in a subclass. Note that this method requires an active I/O
        watcher.
        """
        mode = 0
        if read:
            mode |= select.POLLIN | select.POLLPRI
        if write:
            mode |= select.POLLOUT

        poll = self._poll()
        poll.register(handle, mode)

        return self

    def _poll(self):
        if not self._select_poll:
            self._select_poll = select.poll()

        return self._select_poll


new = Pyjo_Reactor_Poll.new
object = Pyjo_Reactor_Poll
