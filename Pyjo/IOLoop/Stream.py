"""
Pyjo.IOLoop.Stream - Non-blocking I/O stream
============================================
::

    import Pyjo.IOLoop.Stream

    # Create stream
    with Pyjo.IOLoop.Stream.new(handle) as stream:

        @stream.on
        def read(stream, chunk):
            ...

        @stream.on
        def close(stream):
            ...

        @stream.on
        def error(stream, err):
            ...

        # Start and stop watching for new data
        stream.start()
        stream.stop()

        # Start reactor if necessary
        if not stream.reactor.is_running:
            stream.reactor.start()


:mod:`Pyjo.IOLoop.Stream` is a container for I/O streams used by :mod:`Pyjo.IOLoop`.

Events
------

:mod:`Pyjo.IOLoop.Stream` inherits all events from :mod:`Pyjo.IOLoop.EventEmitter` and can
emit the following new ones.

close
~~~~~
::

    @stream.on
    def close(stream):
        ...

Emitted if the stream gets closed.

drain
~~~~~
::

    @stream.on
    def drain(stream):
        ...

Emitted once all data has been written.

error
~~~~~
::

    @stream.on
    def error(stream, err):
        ...

Emitted if an error occurs on the stream, fatal if unhandled.

read
~~~~
::

    @stream.on
    def read(stream, chunk):
        ...

Emitted if new data arrives on the stream.

timeout
~~~~~~~
::

    @stream.on
    def timeout(stream):
        ...

Emitted if the stream has been inactive for too long and will get closed
automatically.

write
~~~~~
::

    @stream.on
    def write(stream, chunk):
        ...

Emitted if new data has been written to the stream.

Classes
-------
"""

import Pyjo.EventEmitter
import Pyjo.IOLoop

from Pyjo.Util import getenv, isalive, notnone, warn

import errno
import weakref


DEBUG = getenv('PYJO_IOLOOP_DEBUG', False)


NoneType = type(None)

if getenv('PYJO_NO_TLS', False):
    ssl = None
else:
    try:
        import ssl
    except ImportError:
        ssl = None


class Pyjo_IOLoop_Stream(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.IOLoop.Stream` inherits all attributes and methods from
    :mod:`Pyjo.EventEmitter` and implements the following new ones.
    """

    def __init__(self, handle, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.reactor = notnone(kwargs.get('reactor'), lambda: Pyjo.IOLoop.singleton.reactor)
        """::

            reactor = stream.reactor
            stream.reactor = Pyjo.Reactor.Poll.new()

        Low-level event reactor, defaults to the :attr:`reactor` attribute value of the
        global :mod:`Pyjo.IOLoop` singleton.
        """

        self.handle = handle
        """::

            handle = stream.handle

        Handle for stream.
        """

        self._buffer = b''
        self._graceful = False
        self._paused = False
        self._timeout = 15
        self._timer = None

    def __del__(self):
        if DEBUG:
            warn(f"-- Method {self}.__del__")

        try:
            self.close()
        except:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        """::

            stream.close()

        Close stream immediately. Used by context manager.
        """
        if not isalive(self):
            return

        reactor = self.reactor
        if not isalive(reactor):
            return

        self.timeout = 0
        handle = self.handle
        self.handle = None
        if not isalive(handle):
            return

        if handle:
            reactor.remove(handle)
            handle.close()
            self.emit('close')

    def close_gracefully(self):
        """::

            stream.close_gracefully()

        Close stream gracefully.
        """
        if self.is_writing:
            self._graceful = True
            return self
        return self.close()

    @property
    def fd(self):
        """::

            fd = stream.fd

        Number of descriptor for handle
        """
        if self.handle:
            return self.handle.fileno()

    @property
    def is_readable(self):
        """::

            boolean = stream.is_readable

        Quick non-blocking check if stream is readable, useful for identifying tainted
        sockets.
        """
        self._again()
        if not self.handle:
            return None
        return self.handle and Pyjo.Util._readable(self.handle.fileno())

    @property
    def is_writing(self):
        """::

            boolean = stream.is_writing

        Check if stream is writing.
        """
        if not self.handle:
            return None
        return len(self._buffer) or self.has_subscribers('drain')

    def start(self):
        """::

            stream.start()

        Start watching for new data on the stream.
        """
        # Resume
        reactor = self.reactor
        if self._paused:
            self._paused = False
            return reactor.watch(self.handle, True, self.is_writing)

        stream = weakref.proxy(self)

        def read_write_cb(reactor, write):
            if isalive(stream):
                if write:
                    stream._write()
                else:
                    stream._read()

        reactor.io(read_write_cb, self.set(timeout=self._timeout).handle)

    def stop(self):
        """::

            stream.stop()

        Stop watching for new data on the stream.
        """
        if not self._paused:
            self.reactor.watch(self.handle, False, self.is_writing)
        self._paused = True

    def steal_handle(self):
        """::

            handle = stream.steal_handle()

        Steal handle from stream and prevent it from getting closed automatically.
        """
        handle = self.handle
        self.reactor.remove(handle)
        self.handle = None
        return handle

    @property
    def timeout(self):
        """::

            timeout = stream.timeout
            stream.timeout = 45

        Maximum amount of time in seconds stream can be inactive before getting closed
        automatically, defaults to ``15``. Setting the value to ``0`` will allow this
        stream to be inactive indefinitely.
        """
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        reactor = self.reactor
        if self._timer:
            reactor.remove(self._timer)
            self._timer = None

        self._timeout = value

        if not value:
            return

        stream = weakref.proxy(self)

        def timeout_cb(reactor):
            if isalive(stream):
                stream.emit('timeout').close()

        self._timer = reactor.timer(timeout_cb, value)

    def write(self, chunk, cb=None):
        """::

            stream = stream.write(bstring)
            stream = stream.write(bstring, cb)

        Write data to stream, the optional drain callback will be invoked once all data
        has been written.
        """
        self._buffer += chunk
        if cb:
            self.once(cb, 'drain')
        elif not len(self._buffer):
            return self
        if self.handle:
            self.reactor.watch(self.handle, not self._paused, 1)

        return self

    def _again(self):
        if self._timer:
            self.reactor.again(self._timer)

    def _error(self, e):
        # Retry
        if e.errno == errno.EAGAIN or e.errno == errno.EINTR or e.errno == errno.EWOULDBLOCK:
            return

        if ssl and isinstance(e, (ssl.SSLWantReadError, ssl.SSLWantReadError)):
            return

        if ssl and isinstance(e, (ssl.SSLError,)) and e.strerror.startswith('The operation did not complete'):
            return

        # Closed
        if e.errno == errno.ECONNRESET or e.errno == errno.EPIPE:
            return self.close()

        # Error
        self.emit('error', e).close()

    def _read(self):
        readbuffer = b''
        try:
            readbuffer = self.handle.recv(131072)
        except OSError as e:
            return self._error(e)
        if not readbuffer:
            return self.close()
        self.emit('read', readbuffer)._again()

    def _write(self):
        handle = self.handle
        if len(self._buffer):
            try:
                written = handle.send(self._buffer)
            except OSError as e:
                self._error(e)
            self.emit('write', self._buffer[:written])
            self._buffer = self._buffer[written:]
            if not len(self._buffer):
                self.emit('drain')
            self._again()

        if self.is_writing:
            return
        if self._graceful:
            return self.close()
        if self.handle:
            self.reactor.watch(handle, not self._paused, 0)


new = Pyjo_IOLoop_Stream.new
object = Pyjo_IOLoop_Stream
