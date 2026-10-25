"""
Pyjo.IOLoop.Stdio - Standard input and output as a stream
==========================================================
::

    from Pyjo.IOLoop.Stdio import Stdio

    # Echo what comes in
    stdio = Stdio()
    stdio.on('read', lambda stdio, chunk: stdio.write(chunk))

    # Or import the module, as in Google Python Style Guide

    import Pyjo.IOLoop.Stdio

    # Echo what comes in, and end once the input has ended and the rest is written
    stdio = Pyjo.IOLoop.Stdio.new()
    stdio.on('read', lambda stdio, chunk: stdio.write(chunk))
    stdio.on('close', lambda stdio: stdio.reactor.stop())
    stdio.start()

    # Start reactor if necessary
    if not stdio.reactor.is_running:
        stdio.reactor.start()

:mod:`Pyjo.IOLoop.Stdio` is the standard input and output of the process as
one :mod:`Pyjo.IOLoop.Stream`, which reads the file descriptor ``0`` and
writes the file descriptor ``1``, as a connection of TCP is read and written,
so that a protocol does not tell them apart: the messages of a protocol, as
JSON-RPC or a protocol of lines, come in on the standard input and go out on
the standard output, and the log goes to the standard error.

The stream takes the standard input and output for itself while it is open:
it reads and writes duplicates of them, the file descriptor ``0`` reads
``/dev/null``, and the file descriptor ``1`` and :data:`sys.stdout` write to
the standard error, so that a stray ``print``, a library, or a process that
inherits them reads and writes nothing of the protocol. Closing the stream
gives them back.

A pipe or a socket is read and written in the non-blocking mode, which belongs
to the open file description that the process shares with its parent, so the
stream gives back the mode that it had when it closes; a terminal is read and
written without it. The reactor watches pipes, sockets and terminals, and a
file, or ``/dev/null``, which a reactor of epoll does not watch, is read in
the next cycles of the event loop and written at once, as its reads and writes
do not block.

The stream has no inactivity timeout by default, as the peer of a server of
standard input and output may send nothing for a long time.

The reactor watches pipes on POSIX systems, not on Windows, where the
constructor raises an exception, and only one stream at a time has the
standard input and output.

The end of a ``with`` block closes the stream.

Events
------

:mod:`Pyjo.IOLoop.Stdio` inherits all events from :mod:`Pyjo.IOLoop.Stream`
and can emit the following new ones.

end
~~~
::

    stdio.on('end', lambda stdio: ...)

Emitted once the standard input has ended, while the standard output can still
be written, as the responses of the requests that are in progress. Without a
subscriber of this event, the stream closes gracefully, once all data has been
written, as a connection of TCP that the peer closes; with one, the subscriber
closes it. ::

    stdio.on('end', lambda stdio: stdio.close_gracefully())

See also
--------

:mod:`Pyjo.IOLoop.Stream`, :mod:`Pyjo.IOLoop.ChildProcess`, :mod:`Pyjoyment`,
https://mojolicious.org.

Inspired by ``process.stdin`` and ``process.stdout`` of Node.js, as
Mojolicious has no stream of the standard input and output.

Classes
-------
"""

import Pyjo.Exception
import Pyjo.IOLoop.Stream

import os
import stat
import sys
import weakref

from typing import IO, Any, Self


# The stream that has the standard input and output, as there is one of them
_open: weakref.ref[Any] | None = None


class Pyjo_IOLoop_Stdio(Pyjo.IOLoop.Stream.object):
    """
    :mod:`Pyjo.IOLoop.Stdio` inherits all attributes and methods from
    :mod:`Pyjo.IOLoop.Stream` and implements the following new ones.
    """

    def __init__(self) -> None:
        """::

            stdio = Pyjo.IOLoop.Stdio.new()

        Construct a new :mod:`Pyjo.IOLoop.Stdio` object, which takes the
        standard input and output.
        """
        global _open
        if os.name == 'nt':
            raise Pyjo.Exception.new('Standard input and output need pipes that the reactor watches')
        if _open is not None and (stdio := _open()) is not None and stdio.handle is not None:
            raise Pyjo.Exception.new('Standard input and output are a stream already')

        # What Python has kept for the file descriptor 1 goes there before it changes
        if sys.stdout is not None:
            sys.stdout.flush()
        input, output = os.dup(0), os.dup(1)
        self._blocking: dict[int, bool] = {}
        for fd in (input, output):
            if _is_pipe(fd):
                self._blocking[fd] = os.get_blocking(fd)
                os.set_blocking(fd, False)

        # Nothing else reads the input or writes the output of the protocol
        null = os.open(os.devnull, os.O_RDONLY)
        os.dup2(null, 0)
        os.close(null)
        os.dup2(2, 1)
        self._stdout = sys.stdout
        sys.stdout = sys.stderr

        super().__init__(os.fdopen(input, 'rb', buffering=0))
        self._timeout = 0
        self._ended = False
        self._reading: str | None = None
        self._registered = False
        self._watched = _is_watched(input)
        self._output = _Output(os.fdopen(output, 'wb', buffering=0), _is_watched(output))
        self._output.timeout = 0
        ref = weakref.ref(self)

        def drain(output: Any) -> None:
            if (stdio := ref()) is not None:
                stdio._drained()

        def write(output: Any, chunk: bytes) -> None:
            if (stdio := ref()) is not None:
                stdio.emit('write', chunk)._again()

        def hangup(output: Any) -> None:
            if (stdio := ref()) is not None:
                stdio.close()

        self._output.on('drain', drain)
        self._output.on('write', write)
        self._output.on('hangup', hangup)
        _open = ref

    @property
    def bytes_waiting(self) -> int:
        return self._output.bytes_waiting

    @property
    def bytes_written(self) -> int:
        return self._output.bytes_written

    @property
    def can_write(self) -> bool:
        return self._handle is not None and self.bytes_waiting < self.high_water_mark

    def close(self) -> None:
        """::

            stdio.close()

        Close stream immediately, and give back the standard input and output.
        """
        if self._handle is None:
            return
        self._restore()
        if (timer := self._reading) is not None:
            self._reading = None
            if self._reactor is not None and (reactor := self._reactor()) is not None:
                reactor.remove(timer)
        self._output.close()
        super().close()

    @property
    def is_writing(self) -> bool:
        if self._handle is None:
            return False
        return bool(self._output.bytes_waiting) or self.has_subscribers('drain')

    def start(self) -> None:
        """::

            stdio.start()

        Start or resume watching for new data on the standard input.
        """
        if (handle := self._handle) is None:
            return
        reactor = self.reactor
        output = self._output
        output.reactor = reactor
        output.start()
        if self.has_subscribers('drain'):
            output.flush()
        self._paused = False
        if self._ended:
            return
        if not self._watched:
            return self._read_later()
        if self._registered:
            reactor.watch(handle, True, False)
            return
        ref = weakref.ref(self)

        def cb(reactor: Any, writable: bool) -> None:
            if (stdio := ref()) is not None:
                stdio._read_handle()

        reactor.io(handle, cb)
        self._registered = True

    def stop(self) -> None:
        """::

            stdio.stop()

        Stop watching for new data on the standard input.
        """
        if (handle := self._handle) is None or self._paused:
            return
        self._paused = True
        if self._registered:
            self.reactor.watch(handle, False, False)

    def write(self, chunk: bytes, cb: Pyjo.IOLoop.Stream.DrainCallback | None = None) -> Self:
        """::

            stdio = stdio.write(chunk)
            stdio = stdio.write(chunk, lambda stdio: ...)

        Enqueue data to be written to the standard output as soon as possible,
        the optional drain callback will be executed once all data has been
        written.
        """
        if cb is not None:
            self.once('drain', cb)
        self._output.write(chunk)
        if self.has_subscribers('drain'):
            self._output.flush()
        return self

    def _drained(self) -> None:
        self.emit('drain')
        if self._graceful and not self.is_writing:
            self.close()

    def _end(self) -> None:
        self._ended = True
        if self._registered and self._handle is not None:
            self._registered = False
            self.reactor.remove(self._handle)
        if not self.has_subscribers('end'):
            return self.close_gracefully()
        self.emit('end')

    def _read_handle(self) -> None:
        if (handle := self._handle) is None or self._ended:
            return
        try:
            chunk = os.read(handle.fileno(), 131072)
        except (BlockingIOError, InterruptedError):
            return
        except OSError as e:
            if isinstance(e, ConnectionResetError):
                return self.close()
            return self.emit('error', e).close()
        if not len(chunk):
            return self._end()
        self._read += len(chunk)
        self.emit('read', chunk)._again()

    # A file, which the reactor may not watch, is read in the next cycles of the event loop, as its reads do not block
    def _read_later(self) -> None:
        if self._reading is not None:
            return
        ref = weakref.ref(self)

        def read(reactor: Any) -> None:
            if (stdio := ref()) is None:
                return
            stdio._reading = None
            if stdio._paused or stdio._ended or stdio._handle is None:
                return
            stdio._read_handle()
            if not stdio._paused and not stdio._ended and stdio._handle is not None:
                stdio._read_later()

        self._reading = self.reactor.timer(0, read)

    def _restore(self) -> None:
        output = self._output.handle
        if output is not None:
            os.dup2(output.fileno(), 1)
        os.dup2(self._handle.fileno(), 0)
        for fd, blocking in self._blocking.items():
            os.set_blocking(fd, blocking)
        if sys.stdout is not None:
            sys.stdout.flush()
        sys.stdout = self._stdout


# The standard output, which the reactor writes and does not read, so that the stream closes when a write fails, where a
# stream finds an error when it reads, and which is written at once when it is a file, which the reactor may not watch.
# It does not close itself, as the stream gives back the descriptors and their modes first
class _Output(Pyjo.IOLoop.Stream.object):
    def __init__(self, handle: IO[bytes], watched: bool) -> None:
        super().__init__(handle)
        self._watched = watched
        self._started = False
        self._writing: str | None = None

    def close(self) -> None:
        if (timer := self._writing) is not None:
            self._writing = None
            if self._reactor is not None and (reactor := self._reactor()) is not None:
                reactor.remove(timer)
        super().close()

    def flush(self) -> None:
        if (handle := self._handle) is None or not self._started:
            return
        if not self._watched:
            return self._write_later()
        self.reactor.watch(handle, False, True)

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        if not self._watched:
            self.timeout = self._timeout
            if self._buffer or self.has_subscribers('drain'):
                self._write_later()
            return
        super().start()
        self.reactor.watch(self._handle, False, self.is_writing)

    def stop(self) -> None:
        return

    def write(self, chunk: bytes, cb: Pyjo.IOLoop.Stream.DrainCallback | None = None) -> Self:
        self._buffer += chunk
        if cb is not None:
            self.once('drain', cb)
        if self._buffer:
            self.flush()
        return self

    # A hang-up or an error of the pipe, which a reactor of poll reports also when it watches for nothing, as the peer
    # has closed its end
    def _read_handle(self) -> None:
        self.emit('hangup')

    def _write(self) -> None:
        handle = self._handle
        if len(self._buffer):
            try:
                written = os.write(handle.fileno(), self._buffer)
            except (BlockingIOError, InterruptedError):
                return

            # The peer has closed its end
            except OSError:
                self.emit('hangup')
                return
            self._written += written
            chunk, self._buffer = self._buffer[:written], self._buffer[written:]
            self.emit('write', chunk)._again()

        if not len(self._buffer):
            self.emit('drain')
        if self._handle is not None and self._watched and not self.is_writing:
            self.reactor.watch(self._handle, False, False)

    def _write_later(self) -> None:
        if self._writing is not None:
            return
        ref = weakref.ref(self)

        def write(reactor: Any) -> None:
            if (output := ref()) is None:
                return
            output._writing = None
            while output._handle is not None and output._buffer:
                output._write()
            if output._handle is not None and output.has_subscribers('drain'):
                output._write()

        self._writing = self.reactor.timer(0, write)


# A pipe or a socket, whose mode the stream changes
def _is_pipe(fd: int) -> bool:
    mode = os.fstat(fd).st_mode
    return stat.S_ISFIFO(mode) or stat.S_ISSOCK(mode)


# A pipe, a socket or a terminal, which every reactor watches, where a reactor of epoll watches no file and no device
def _is_watched(fd: int) -> bool:
    return _is_pipe(fd) or os.isatty(fd)


new = Pyjo_IOLoop_Stdio.new
object = Pyjo_IOLoop_Stdio
Stdio = Pyjo_IOLoop_Stdio
