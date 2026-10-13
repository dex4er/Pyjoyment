"""
Pyjo.IOLoop.Delay - Manage callbacks and control the flow of events
===================================================================
::

    import Pyjo.IOLoop

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

    @delay.step
    def step1(delay):
        # First step (simple timer)
        Pyjo.IOLoop.timer(delay.begin(), 2)
        print('Second step in 2 seconds.')

    @delay.step
    def step2(delay):
        # Second step (concurrent timers)
        Pyjo.IOLoop.timer(delay.begin(), 1)
        Pyjo.IOLoop.timer(delay.begin(), 3)
        print('Third step in 3 seconds.')

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
    def step2(delay):
        print('Never actually reached.')

    @delay.catch
    def step3(delay, err):
        print("Something went wrong: {0}".format(err))

    delay.wait()

:mod:`Pyjo.IOLoop.Delay` manages callbacks and controls the flow of events for
:mod:`Pyjo.IOLoop`, which can help you avoid deep nested closures and memory
leaks that often result from continuation-passing style.

Events
------

:mod:`Pyjo.IOLoop.Delay` inherits all events from :mod:`Pyjo.EventEmitter` and can
emit the following new ones.

error
~~~~~
::

    @delay.on
    def error(delay, err):
        ...

Emitted if an exception gets thrown in one of the steps, breaking the chain,
fatal if unhandled.

finish
~~~~~~
::

    @delay.on
    def finish(delay, *args):
        ...

Emitted once the active event counter reaches zero and there are no more
steps.

Classes
-------
"""

import Pyjo.EventEmitter
import Pyjo.IOLoop
import Pyjo.Util

from Pyjo.Util import notnone


REMAINING = {}


class Pyjo_IOLoop_Delay(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.IOLoop.Delay` inherits all attributes and methods from
    :mod:`Pyjo.EventEmitter` and implements the following new ones.
    """

    def __init__(self, *args, **kwargs):
        super().__init__()

        self.ioloop = notnone(kwargs.get('ioloop'), lambda: Pyjo.IOLoop.singleton)
        """::

            ioloop = delay.ioloop
            delay.ioloop = Pyjo.IOLoop.new()

        Event loop object to control, defaults to the global :mod:`Pyjo.IOLoop`
        singleton.
        """

        self._counter = 0
        self._pending = 0
        self._lock = False
        self._fail = False

        self._data = {}
        self._args = []

    def begin(self, offset=1, length=0, *args):
        """::

            cb = delay.begin
            cb = delay.begin(offset)
            cb = delay.begin(offset, length)

        Indicate an active event by incrementing the active event counter, the
        returned callback needs to be called when the event has completed, to
        decrement the active event counter again. When all callbacks have been called
        and the active event counter reached zero, :meth:`steps` will continue. ::

            # Capture all arguments except for the first one (invocant)
            delay = Pyjo.IOLoop.delay()

            @delay.step
            def step1(delay, err, stream):
                ...

            Pyjo.IOLoop.client(delay.begin(), port=3000)
            delay.wait()

        Arguments passed to the returned callback are sliced with the given offset
        and length, defaulting to an offset of ``1`` with no default length. The
        arguments are then combined in the same order :meth:`begin` was called, and
        passed together to the next step or ``finish`` event. ::

            # Capture all arguments
            delay = Pyjo.IOLoop.delay()

            @delay.step
            def step2(delay, loop, err, stream):
                ...

            Pyjo.IOLoop.client(delay.begin(0), port=3000)
            delay.wait()

            # Capture only the second argument
            delay = Pyjo.IOLoop.delay()

            @delay.step
            def step3(delay, err):
                ...

            Pyjo.IOLoop.client(delay.begin(1, 1), port=3000)
            delay.wait()

            # Capture and combine arguments
            delay = Pyjo.IOLoop.delay()

            @delay.step
            def step4(delay, three_err, three_stream, four_err, four_stream):
                ...

            Pyjo.IOLoop.client(delay.begin(), port=3000)
            Pyjo.IOLoop.client(delay.begin(), port=4000)
            delay.wait()
        """
        self._pending += 1
        self._counter += 1
        sid = self._counter

        def step_cb(*args):
            return self._step(sid, offset, length, *args)

        return step_cb

    def data(self, *args, **kwargs):
        """::

            data = delay.data()
            foo  = delay.data('foo')
            delay = delay.data(foo='bar')

        Data shared between all :meth:`steps`. ::

            # Remove value
            del delay.data()['foo']

            # Assign multiple values at once
            delay.data(foo='test', bar=23)
        """
        return Pyjo.Util._stash(self, self._data, *args, **kwargs)

    def remaining(self, steps=None):
        """::

            remaining = delay.remaining()
            delay = delay.remaining([])

        Remaining steps in chain, stored outside the object to protect from
        circular references.

        The first step runs during next reactor tick after :meth:`wait` method is called.
        """
        if steps is None:
            if self not in REMAINING:
                REMAINING[self] = []
            return REMAINING[self]
        else:
            if len(steps):
                REMAINING[self] = steps
            elif self in REMAINING:
                del REMAINING[self]
            return self

    def step(self, cb):
        """::

            delay = delay.step(cb)

        Add another step to :meth:`remaining` steps in chain. ::

            @delay.step
            def step1(delay, args*)
                ...
        """
        remaining = self.remaining()
        remaining.append(cb)
        return self

    def steps(self, *args):
        """::

            delay = delay.steps(cb, cb)

        Add another steps to :meth:`remaining` steps in chain.
        """
        remaining = self.remaining()
        remaining.extend(args)
        return self

    def wait(self):
        """::

            delay.wait()

        This sequentialize multiple events, every time the active event counter reaches
        zero a callback will run, the first one automatically runs during the next
        reactor tick unless it is delayed by incrementing the active event counter.
        This chain will continue until there are no more callbacks, a callback does
        not increment the active event counter or an exception gets thrown in a
        callback.

        Also start :attr:`ioloop` and stop it again once an ``error`` or ``finish`` event
        gets emitted.
        """
        self.ioloop.next_tick(self.begin())

        if self.ioloop.is_running:
            return

        def error_cb(delay, *args):
            delay._die(*args)

        self.once('error', error_cb)

        def finish_cb(delay, *args):
            delay.ioloop.stop()

        self.once('finish', finish_cb)

        self.ioloop.start()

    def _die(self, err):
        if self.has_subscribers('error'):
            self.ioloop.stop()
        else:
            raise Exception(err)

    def _step(self, sid, offset=1, length=0, *args):
        if args:
            if length:
                args = args[offset : offset + length]
            else:
                args = args[offset:]

        if sid >= len(self._args):
            self._args.append(args)
        else:
            self._args[sid] = args

        if self._fail:
            return self

        self._pending -= 1

        if self._pending:
            return self

        if self._lock:
            return self

        args = [item for sublist in self._args for item in sublist]
        self._args = []

        self._counter = 0
        remaining = self.remaining()
        if len(remaining):
            cb = remaining.pop(0)
            try:
                cb(self, *args)
            except Exception as ex:
                self._fail = True
                self.remaining([]).emit('error', ex)

        if not self._counter:
            return self.remaining([]).emit('finish', *args)

        if not self._pending:
            self.ioloop.next_tick(self.begin())

        return self


new = Pyjo_IOLoop_Delay.new
object = Pyjo_IOLoop_Delay
