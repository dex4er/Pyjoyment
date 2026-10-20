"""
Pyjo.IOLoop.Subprocess - Subprocesses
=====================================
::

    from Pyjo.IOLoop.Subprocess import Subprocess

    import time

    # Operation that would block the event loop for 5 seconds
    subprocess = Subprocess()


    def blocking(subprocess):
        time.sleep(5)
        return '♥', 'Pyjoyment'


    def done(subprocess, err, *results):
        if err:
            print(f'Subprocess error: {err}')
            return
        print(f'I {results[0]} {results[1]}!')


    subprocess.run(blocking, done)

    # Or import the module, as in Google Python Style Guide

    import Pyjo.IOLoop.Subprocess

    import time

    # Operation that would block the event loop for 5 seconds
    subprocess = Pyjo.IOLoop.Subprocess.new()


    def blocking(subprocess):
        time.sleep(5)
        return '♥', 'Pyjoyment'


    def done(subprocess, err, *results):
        if err:
            print(f'Subprocess error: {err}')
            return
        print(f'I {results[0]} {results[1]}!')


    subprocess.run(blocking, done)

    # Operation that would block the event loop for 5 seconds (with promise)
    subprocess.run_p(blocking).then(lambda *results: print(f'I {results[0]} {results[1]}!')).catch(
        lambda err: print(f'Subprocess error: {err}')
    )

    # Start event loop if necessary
    if not subprocess.ioloop.is_running:
        subprocess.ioloop.start()

:mod:`Pyjo.IOLoop.Subprocess` allows :mod:`Pyjo.IOLoop` to perform
computationally expensive operations in subprocesses, without blocking the
event loop.

The subprocess is a fork of the process, made with :func:`os.fork`, so the
first callback of :meth:`~Pyjo_IOLoop_Subprocess.run` can be any function,
a closure too, and it has the state of the parent. It runs where
:func:`os.fork` exists, not on Windows.

Events
------

:mod:`Pyjo.IOLoop.Subprocess` inherits all events from :mod:`Pyjo.EventEmitter`
and can emit the following new ones.

cleanup
~~~~~~~
::

    subprocess.on('cleanup', lambda subprocess: ...)

Emitted in the subprocess right before the process will exit. ::

    subprocess.on('cleanup', lambda subprocess: print(f'Process {os.getpid()} is about to exit'))

progress
~~~~~~~~
::

    subprocess.on('progress', lambda subprocess, *data: ...)

Emitted in the parent process when the subprocess calls the
:meth:`~Pyjo_IOLoop_Subprocess.progress` method.

spawn
~~~~~
::

    subprocess.on('spawn', lambda subprocess: ...)

Emitted in the parent process when the subprocess has been spawned. ::

    subprocess.on('spawn', lambda subprocess: print(f'Performing work in process {subprocess.pid}'))

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::IOLoop::Subprocess <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/IOLoop/Subprocess.pm>`_
of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.EventEmitter
import Pyjo.Exception
import Pyjo.IOLoop
import Pyjo.IOLoop.Stream
import Pyjo.JSON
import Pyjo.Promise

from Pyjo.Util import warn

import builtins
import os
import re
import sys
import traceback
import weakref

from collections.abc import Callable
from typing import IO, Any, NoReturn, Self


type Anything = builtins.object

# The first callback of run runs in the subprocess, the second one in the parent process with the error and the results
type Child = Callable[[Any], Any]
type Parent = Callable[..., Anything]


class Pyjo_IOLoop_Subprocess(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.IOLoop.Subprocess` inherits all methods from
    :mod:`Pyjo.EventEmitter` and implements the following new ones.
    """

    def __init__(
        self,
        *,
        deserialize: Callable[[bytes], Any] | None = None,
        ioloop: Pyjo.IOLoop.object | None = None,
        serialize: Callable[[Any], bytes] | None = None,
    ) -> None:
        """::

            subprocess = Pyjo.IOLoop.Subprocess.new()
            subprocess = Pyjo.IOLoop.Subprocess.new(ioloop=Pyjo.IOLoop.new())

        Construct a new :mod:`Pyjo.IOLoop.Subprocess` object.
        """
        super().__init__()

        self.deserialize: Callable[[bytes], Any] = deserialize or Pyjo.JSON.decode_json
        """::

            cb = subprocess.deserialize
            subprocess.deserialize = lambda data: []

        A callback used to deserialize subprocess return values, defaults to
        using :mod:`Pyjo.JSON`.
        """

        self.serialize: Callable[[Any], bytes] = serialize or Pyjo.JSON.encode_json
        """::

            cb = subprocess.serialize
            subprocess.serialize = lambda array: b''

        A callback used to serialize subprocess return values, defaults to
        using :mod:`Pyjo.JSON`.
        """

        self._exit_code: int | None = None
        self._ioloop: weakref.ref[Pyjo.IOLoop.object] | None = None
        self._pid: int | None = None
        self._writer: IO[bytes] | None = None
        if ioloop is not None:
            self.ioloop = ioloop

    @property
    def ioloop(self) -> Pyjo.IOLoop.object:
        """::

            loop = subprocess.ioloop
            subprocess.ioloop = Pyjo.IOLoop.new()

        Event loop object to control, defaults to the global :mod:`Pyjo.IOLoop`
        singleton. Note that this attribute is weakened.
        """
        if self._ioloop is None:
            self._ioloop = weakref.ref(Pyjo.IOLoop.singleton)
        if (loop := self._ioloop()) is None:
            raise ReferenceError('weakly-referenced object no longer exists')
        return loop

    @ioloop.setter
    def ioloop(self, value: Pyjo.IOLoop.object) -> None:
        self._ioloop = weakref.ref(value)

    @property
    def exit_code(self) -> int | None:
        """::

            code = subprocess.exit_code

        Returns the subprocess exit code, or ``None`` if the subprocess is
        still running.
        """
        return self._exit_code

    @property
    def pid(self) -> int | None:
        """::

            pid = subprocess.pid

        Process id of the spawned subprocess if available.
        """
        return self._pid

    def progress(self, *data: Anything) -> None:
        """::

            subprocess.progress(*data)

        Send data serialized with :mod:`Pyjo.JSON` to the parent process at any
        time during the subprocess's execution. Must be called by the subprocess
        and emits the ``progress`` event in the parent process with the data. ::

            # Send progress information to the parent process
            def blocking(subprocess):
                subprocess.progress('0%')
                time.sleep(5)
                subprocess.progress('50%')
                time.sleep(5)
                return 'Hello Pyjo!'


            def done(subprocess, err, *results):
                print('Progress is 100%')
                print(results[0])


            subprocess.run(blocking, done)
            subprocess.on('progress', lambda subprocess, *data: print(f'Progress is {data[0]}'))
        """
        serialized = self.serialize(list(data))
        if (writer := self._writer) is None:
            Pyjo.Exception.object.throw('Progress can only be sent by the subprocess')
        writer.write(f'{len(serialized)}-'.encode() + serialized)
        writer.flush()

    def run(self, child: Child, parent: Parent) -> Self:
        """::

            subprocess = subprocess.run(lambda subprocess: ..., lambda subprocess, err, *results: ...)

        Execute the first callback in a child process and wait for it to return
        a value, a tuple for several ones and ``None`` for none, without
        blocking :attr:`ioloop` in the parent process. Then execute the second
        callback in the parent process with the error and the results. The
        return value of the first callback and the exception raised by it will
        be serialized with :mod:`Pyjo.JSON`, so they can be shared between
        processes.
        """
        self.ioloop.next_tick(lambda loop: self._start(child, parent))
        return self

    def run_p(self, child: Child) -> Pyjo.Promise.object:
        """::

            promise = subprocess.run_p(lambda subprocess: ...)

        Same as :meth:`run`, but returns a :mod:`Pyjo.Promise` object instead of
        accepting a second callback. ::

            subprocess.run_p(blocking).then(lambda *results: print(f'I {results[0]} {results[1]}!')).catch(
                lambda err: print(f'Subprocess error: {err}')
            ).wait()
        """
        p = Pyjo.Promise.new()

        def parent(self: Pyjo_IOLoop_Subprocess, err: Any, *results: Any) -> None:
            p.reject(err) if err else p.resolve(*results)

        self.ioloop.next_tick(lambda loop: self._start(child, parent))
        return p

    def _start(self, child: Child, parent: Parent) -> None:
        # Unlike Mojolicious: no fork at all, where Mojo has no fork emulation of Perl on Windows
        if not hasattr(os, 'fork'):
            parent(self, 'Subprocesses need os.fork')
            return

        # Pipe for subprocess communication
        try:
            reader, writer = os.pipe()
        except OSError as e:
            parent(self, f"Can't create pipe: {e.strerror or e}")
            return

        # Child
        # Not in Mojolicious: the buffers of the standard streams are written before, so that the child does not write
        # them again, as multiprocessing does it
        _flush()
        try:
            pid = self._pid = os.fork()
        except OSError as e:
            os.close(reader)
            os.close(writer)
            parent(self, f"Can't fork: {e.strerror or e}")
            return
        if not pid:
            self._child(child, reader, writer)

        # Parent
        me = os.getpid()
        os.close(writer)
        os.set_blocking(reader, False)
        stream = Pyjo.IOLoop.Stream.new(open(reader, 'rb', buffering=0))
        stream.timeout = 0
        self.emit('spawn').ioloop.stream(stream)
        buffer = bytearray()

        def read(stream: Pyjo.IOLoop.Stream.object, chunk: bytes) -> None:
            buffer.extend(chunk)
            while True:
                m = re.match(rb'([0-9]+)-', buffer)
                if not m or not int(m[1]) or len(buffer) < int(m[1]) + m.end():
                    break
                snippet = bytes(buffer[: int(m[1]) + m.end()])
                del buffer[: int(m[1]) + m.end()]
                args = self.deserialize(snippet[m.end() :])
                self.emit('progress', *args)

        def close(stream: Pyjo.IOLoop.Stream.object) -> None:
            if os.getpid() != me:
                return
            _, status = os.waitpid(pid, 0)
            self._exit_code = status >> 8
            del buffer[:2]
            err: Any = None
            try:
                results = list(self.deserialize(bytes(buffer)))
            except Exception as e:
                results, err = [], _error(e)
            first = results.pop(0) if len(results) else None
            parent(self, first if first is not None else err, *results)

        stream.on('read', read)
        stream.on('close', close)

    # The subprocess, which runs the first callback, writes its results and exits
    def _child(self, child: Child, reader: int, writer: int) -> NoReturn:
        code = 0
        try:
            os.close(reader)
            self._writer = open(writer, 'wb')
            self.ioloop.reset(freeze=True)
            err: Any = None
            try:
                results = _results(child(self))
            except Exception as e:
                results, err = [], _error(e)
            self._writer.write(b'0-' + self.serialize([err, *results]))
            self._writer.flush()
            self.emit('cleanup')

        # Not in Mojolicious: sys.exit() is the exit of the subprocess, as exit is in Perl
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 0 if e.code is None else 1
        except BaseException as e:
            warn(''.join(traceback.format_exception(e)))

        # Not in Mojolicious: the buffers of the standard streams, which os._exit leaves
        _flush()
        os._exit(code)


def _flush() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.flush()
        except Exception:
            pass


# The error of the subprocess, as the string of the exception that Perl has in $@
def _error(e: BaseException) -> str:
    if isinstance(e, Pyjo.Exception.object):
        return str(e)
    return ''.join(traceback.format_exception_only(e)).strip()


# The results of the first callback: none, one, or the values of a tuple
def _results(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, tuple):
        return list(value)  # pyright: ignore[reportUnknownArgumentType]
    return [value]


new = Pyjo_IOLoop_Subprocess.new
object = Pyjo_IOLoop_Subprocess
Subprocess = Pyjo_IOLoop_Subprocess
