"""
Pyjo.IOLoop.ChildProcess - Non-blocking child process
======================================================
::

    from Pyjo.IOLoop.ChildProcess import ChildProcess

    child = ChildProcess()
    child.spawn(['ls', '-l'])

    # Or import the module, as in Google Python Style Guide

    import Pyjo.IOLoop.ChildProcess

    # Run a program, with its output and its exit status
    child = Pyjo.IOLoop.ChildProcess.new()
    child.on('spawn', lambda child: child.stdout.on('read', lambda stream, chunk: print(chunk)))
    child.on('close', lambda child, code, signal: print(f'Exited with {code}'))
    child.on('error', lambda child, err: print(f"Can't run: {err}"))
    child.spawn(['ls', '-l'])

    # Write to its standard input, and end it
    child = Pyjo.IOLoop.ChildProcess.new().spawn(['sort'])
    child.stdout.on('read', lambda stream, chunk: print(chunk))
    child.stdin.write(b'b\\na\\n')
    child.stdin.close_gracefully()

    # Its output as a promise, also in a coroutine
    child = Pyjo.IOLoop.ChildProcess.new()
    child.run_p(['ls', '-l']).then(lambda code, out, err: print(out))

    # Start reactor if necessary
    if not child.reactor.is_running:
        child.reactor.start()

:mod:`Pyjo.IOLoop.ChildProcess` runs a program in a process of its own, as
``CGI`` programs and command line tools are, with its standard input, output
and error as pipes that the reactor watches, as
:mod:`Pyjo.IOLoop.Stream` objects, without blocking the event loop. It runs
the program, not a function of Python, as :mod:`Pyjo.IOLoop.Subprocess` does
in a fork of the process.

The process is reaped by the reactor, which checks for its end with a timer,
and at once when its output and its error have ended, as most programs end
them when they exit. The end of the interpreter kills and reaps the processes
that are left, and closes their pipes.

The child of a fork leaves the processes of its parent to it: it closes its
copies of their pipes, and neither reaps them nor emits their events, which
the parent does.

The reactor watches pipes on POSIX systems, not on Windows, where
:meth:`~Pyjo_IOLoop_ChildProcess.spawn` emits the event ``error``.

Events
------

:mod:`Pyjo.IOLoop.ChildProcess` inherits all events from
:mod:`Pyjo.EventEmitter` and can emit the following new ones.

close
~~~~~
::

    child.on('close', lambda child, code, signal: ...)

Emitted once the process has exited and its output and its error have ended,
with its exit code, or the signal that terminated it, after the event
``exit``. ::

    child.on('close', lambda child, code, signal: print(f'Process {child.pid} closed with {code}'))

error
~~~~~
::

    child.on('error', lambda child, err: ...)

Emitted if the program could not be run, as one that does not exist. ::

    child.on('error', lambda child, err: print(f'Error: {err}'))

exit
~~~~
::

    child.on('exit', lambda child, code, signal: ...)

Emitted once the process has exited, with its exit code, or ``None`` and the
signal that terminated it. Its output and its error may not have ended yet.
::

    child.on('exit', lambda child, code, signal: print(f'Process {child.pid} exited with {code}'))

spawn
~~~~~
::

    child.on('spawn', lambda child: ...)

Emitted once the process has been spawned, before its output and its error
are read, so that the subscribers of this event get all of them. ::

    child.on('spawn', lambda child: print(f'Running process {child.pid}'))

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Inspired by `child_process <https://nodejs.org/api/child_process.html>`_ of
Node.js, as Mojolicious runs no programs in its event loop.

Classes
-------
"""

import Pyjo.EventEmitter
import Pyjo.Exception
import Pyjo.IOLoop
import Pyjo.IOLoop.Stream
import Pyjo.Reactor

import atexit
import os
import signal as signals
import subprocess
import weakref

from collections.abc import Mapping, Sequence
from typing import Any, Self


# The child processes that have not been reaped yet, with the process that started them, which the end of the
# interpreter kills and reaps, with their pipes, as Python warns of a process that still runs when it frees its object
_running: dict['Pyjo_IOLoop_ChildProcess', int] = {}

# The delay of the next check for the end of a process, which grows to the longest one
_DELAYS = (0, 0.01, 0.02, 0.05, 0.1)


class Pyjo_IOLoop_ChildProcess(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.IOLoop.ChildProcess` inherits all methods from
    :mod:`Pyjo.EventEmitter` and implements the following new ones.
    """

    def __init__(self, *, reactor: Pyjo.Reactor.object | None = None) -> None:
        """::

            child = Pyjo.IOLoop.ChildProcess.new()
            child = Pyjo.IOLoop.ChildProcess.new(reactor=Pyjo.Reactor.Poll.new())

        Construct a new :mod:`Pyjo.IOLoop.ChildProcess` object.
        """
        super().__init__()

        self._check = 0
        self._detached = False
        self._ended = 0
        self._exit_code: int | None = None
        self._process: subprocess.Popen[bytes] | None = None
        self._reactor: weakref.ref[Pyjo.Reactor.object] | None = None
        self._signal_code: int | None = None
        self._stderr: Pyjo.IOLoop.Stream.object | None = None
        self._stdin: Pyjo.IOLoop.Stream.object | None = None
        self._stdout: Pyjo.IOLoop.Stream.object | None = None
        self._timer: str | None = None
        if reactor is not None:
            self.reactor = reactor

    @property
    def exit_code(self) -> int | None:
        """::

            code = child.exit_code

        Exit code of the process, or ``None`` if it is still running or a
        signal terminated it.
        """
        return self._exit_code

    @property
    def pid(self) -> int | None:
        """::

            pid = child.pid

        Process id of the spawned process if available.
        """
        return self._process.pid if self._process is not None else None

    @property
    def reactor(self) -> Pyjo.Reactor.object:
        """::

            reactor = child.reactor
            child.reactor = Pyjo.Reactor.Poll.new()

        Low-level event reactor, defaults to the ``reactor`` attribute value of
        the global :mod:`Pyjo.IOLoop` singleton. Note that this attribute is
        weakened.
        """
        if self._reactor is None:
            self._reactor = weakref.ref(Pyjo.IOLoop.singleton.reactor)
        if (reactor := self._reactor()) is None:
            raise ReferenceError('weakly-referenced object no longer exists')
        return reactor

    @reactor.setter
    def reactor(self, value: Pyjo.Reactor.object) -> None:
        self._reactor = weakref.ref(value)

    @property
    def signal_code(self) -> int | None:
        """::

            signal = child.signal_code

        Signal that terminated the process, or ``None``.
        """
        return self._signal_code

    @property
    def stderr(self) -> Pyjo.IOLoop.Stream.object | None:
        """::

            stream = child.stderr

        :mod:`Pyjo.IOLoop.Stream` object of the standard error of the process,
        which the reactor reads without an inactivity timeout.
        """
        return self._stderr

    @property
    def stdin(self) -> Pyjo.IOLoop.Stream.object | None:
        """::

            stream = child.stdin

        :mod:`Pyjo.IOLoop.Stream` object of the standard input of the process,
        which the reactor writes without an inactivity timeout, and which ends
        with :meth:`~Pyjo.IOLoop.Stream.Pyjo_IOLoop_Stream.close_gracefully`.
        It closes once the process closes its end, so that a write that fails
        is no error.
        """
        return self._stdin

    @property
    def stdout(self) -> Pyjo.IOLoop.Stream.object | None:
        """::

            stream = child.stdout

        :mod:`Pyjo.IOLoop.Stream` object of the standard output of the
        process, which the reactor reads without an inactivity timeout. ::

            # Kill a process that has been quiet for 60 seconds
            child.stdout.timeout = 60
            child.stdout.on('timeout', lambda stream: child.kill())
        """
        return self._stdout

    def kill(self, signal: int = signals.SIGTERM) -> bool:
        """::

            boolean = child.kill()
            boolean = child.kill(signal.SIGKILL)

        Send a signal to the process, ``SIGTERM`` by default, if it is still
        running, or to the processes of its group, which it may have started,
        when it has been spawned ``detached``, while any of them runs.
        """
        if (process := self._process) is None:
            return False
        if self._detached:
            try:
                os.killpg(process.pid, signal)

            # No process of the group, or only the process that has exited and has not been reaped yet, for which macOS
            # gives EPERM
            except (ProcessLookupError, PermissionError):
                return False
            return True
        if process.poll() is not None:
            return False
        process.send_signal(signal)
        return True

    def run_p(self, args: Sequence[str | bytes | os.PathLike[str]], *, input: bytes = b'', **options: Any) -> Any:
        """::

            promise = child.run_p(['ls', '-l'])
            promise = child.run_p(['sort'], input=b'b\\na\\n', cwd='/tmp')

        Same as :meth:`spawn`, with the options of :meth:`spawn`, but writes
        ``input`` to the standard input of the process and ends it, and
        returns a :mod:`Pyjo.Promise` object, which is fulfilled with the exit
        code, ``None`` for a signal, and the whole output and error of the
        process as :mod:`Pyjo.String.Bytes` objects once it closes, or
        rejected if the program could not be run. ::

            # The output of a program in a coroutine
            code, out, err = await Pyjo.IOLoop.ChildProcess.new().run_p(['git', 'log', '-1'])
        """
        # Imported here, as Pyjo.Promise uses Pyjo.IOLoop
        import Pyjo.Promise
        import Pyjo.String.Bytes

        p = Pyjo.Promise.new()
        out: list[bytes] = []
        err: list[bytes] = []

        def close(child: Pyjo_IOLoop_ChildProcess, code: int | None, signal: int | None) -> None:
            p.resolve(code, Pyjo.String.Bytes.new(b''.join(out)), Pyjo.String.Bytes.new(b''.join(err)))

        def error(child: Pyjo_IOLoop_ChildProcess, e: BaseException) -> None:
            p.reject(e)

        def output(stream: Any, chunk: bytes) -> None:
            out.append(chunk)

        def errors(stream: Any, chunk: bytes) -> None:
            err.append(chunk)

        self.once('close', close)
        self.once('error', error)
        self.spawn(args, **options)
        if (stdout := self._stdout) is not None and (stderr := self._stderr) is not None:
            stdout.on('read', output)
            stderr.on('read', errors)
        if (stdin := self._stdin) is not None:
            stdin.write(input).close_gracefully()
        return p

    def spawn(
        self,
        args: Sequence[str | bytes | os.PathLike[str]],
        *,
        cwd: str | bytes | os.PathLike[str] | None = None,
        detached: bool = False,
        env: Mapping[str, str] | Mapping[bytes, bytes] | None = None,
    ) -> Self:
        """::

            child = child.spawn(['ls', '-l'])
            child = child.spawn(['php-cgi', 'index.php'], cwd='/var/www', env={'REDIRECT_STATUS': '200'})
            child = child.spawn(['make', 'all'], detached=True)

        Run a program, the first of ``args``, with the others as its
        arguments, in the directory ``cwd`` and with the environment ``env``,
        the ones of this process by default. With ``detached``, the process
        runs in a session of its own, as the leader of a process group, as
        ``detached`` of Node.js, so that :meth:`kill` signals the processes
        that it starts too, and a signal of the terminal of this process, as
        of Ctrl-C, does not reach it. The events ``spawn`` or ``error`` are
        emitted in the next tick of the reactor, so that the ones that are
        subscribed after the call get them too, and the output and the error
        are read from the event ``spawn`` on.
        """
        reactor = self.reactor
        if os.name == 'nt':
            return self._later('error', Pyjo.Exception.new('Child processes need pipes that the reactor watches'))
        try:
            self._process = process = subprocess.Popen(
                args,
                bufsize=0,
                cwd=cwd,
                env=env,
                start_new_session=detached,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError as e:
            return self._later('error', e)
        self._detached = detached
        _running[self] = os.getpid()
        _register()
        assert process.stdin is not None and process.stdout is not None and process.stderr is not None

        # The output and the error, until their end, which the end of the process usually is, read from the event
        # spawn on
        for name, handle in (('_stdout', process.stdout), ('_stderr', process.stderr)):
            os.set_blocking(handle.fileno(), False)
            stream = _Output(handle)
            stream.reactor = reactor
            stream.timeout = 0
            stream.on('close', self._closed)
            setattr(self, name, stream)

        # The input, which the reactor writes without reading
        os.set_blocking(process.stdin.fileno(), False)
        self._stdin = stdin = _Input(process.stdin)
        stdin.reactor = reactor
        stdin.timeout = 0
        stdin.start()

        self._wait(_DELAYS[-1])
        ref = weakref.ref(self)

        # The output and the error are read once the subscribers of the event spawn can read them, as a reactor may
        # read before the next tick
        def spawned(reactor: Any) -> None:
            if (child := ref()) is None or child._process is None:
                return
            for stream in (child._stdout, child._stderr):
                if isinstance(stream, _Output):
                    stream.begin()
            child.emit('spawn')

        reactor.next_tick(spawned)
        return self

    # The output or the error of the process has ended, so that it has likely exited
    def _closed(self, stream: Any) -> None:
        if (process := self._process) is None:
            return
        self._ended += 1
        if self._ended < 2:
            return
        if process.returncode is not None:
            return self._emit_close()
        self._check = 0
        self._wait(_DELAYS[0])

    # The process of the parent of a fork, whose pipes the child closes, without the events of its end, as Popen.poll
    # gives the exit code 0 for a process that is not a child of the process that calls it
    def _leave(self) -> None:
        # The poll of a process that is not a child gives it the exit code 0, so that Popen does not warn that it still
        # runs when it is freed
        if (process := self._process) is not None:
            self._process = None
            process.poll()
        if (timer := self._timer) is not None:
            self._timer = None
            self.reactor.remove(timer)
        for stream in (self._stdin, self._stdout, self._stderr):
            if stream is not None:
                stream.close()

    def _emit_close(self) -> None:
        self.emit('close', self._exit_code, self._signal_code)

    def _later(self, name: str, *args: Any) -> Self:
        ref = weakref.ref(self)

        def emit(reactor: Any) -> None:
            if (child := ref()) is not None:
                child.emit(name, *args)

        self.reactor.next_tick(emit)
        return self

    # The end of the process
    def _poll(self, reactor: Any) -> None:
        self._timer = None
        if (process := self._process) is None:
            return
        if (code := process.poll()) is None:
            self._check = min(self._check + 1, len(_DELAYS) - 1)
            return self._wait(_DELAYS[self._check])
        _running.pop(self, None)

        # The input that the process can read no more
        if (stdin := self._stdin) is not None:
            stdin.close()
        if code < 0:
            self._signal_code = -code
        else:
            self._exit_code = code
        self.emit('exit', self._exit_code, self._signal_code)
        if self._ended >= 2:
            self._emit_close()

    def _wait(self, after: float) -> None:
        reactor = self.reactor
        if self._timer is not None:
            reactor.remove(self._timer)
        self._timer = reactor.timer(after, self._poll)


# The output or the error of a process, which the reactor reads from the event spawn on, and which keeps whether it is
# paused until then
class _Output(Pyjo.IOLoop.Stream.object):
    _begun = False

    def begin(self) -> None:
        self._begun = True
        paused, self._paused = self._paused, False
        super().start()
        if paused:
            super().stop()

    def start(self) -> None:
        if self._begun:
            return super().start()
        self._paused = False

    def stop(self) -> None:
        if self._begun:
            return super().stop()
        self._paused = True


# The standard input of a process, which the reactor writes and does not read, so that it closes when a write fails,
# where a stream finds an error when it reads
class _Input(Pyjo.IOLoop.Stream.object):
    def start(self) -> None:
        super().start()
        self.stop()

    # A hang-up or an error of the pipe, which a reactor of poll reports also when it watches for nothing, as the
    # process has closed its end
    def _read_handle(self) -> None:
        self.close()

    def _write(self) -> None:
        handle = self._handle
        if len(self._buffer):
            try:
                written = os.write(handle.fileno(), self._buffer)
            except (BlockingIOError, InterruptedError):
                return

            # The process has closed its end
            except OSError:
                return self.close()
            self._written += written
            chunk, self._buffer = self._buffer[:written], self._buffer[written:]
            self.emit('write', chunk)._again()

        if not len(self._buffer):
            self.emit('drain')
        if self.is_writing:
            return
        if self._graceful:
            return self.close()
        if self._handle is not None:
            self.reactor.watch(self._handle, False, False)


# The child of a fork leaves the processes of its parent, before its event loop reads their pipes. The handler is
# registered when a process is spawned, after the one of the reactor, which os.register_at_fork calls first, so that the
# reactor has moved to a loop of its own, as a loop of epoll shares its state with the parent
_registered = False


def _register() -> None:
    global _registered
    if not _registered and hasattr(os, 'register_at_fork'):
        _registered = True
        os.register_at_fork(after_in_child=_after_fork_in_child)


def _after_fork_in_child() -> None:
    pid = os.getpid()
    for child, owner in list(_running.items()):
        if owner != pid:
            del _running[child]
            try:
                child._leave()  # pyright: ignore[reportPrivateUsage]
            except Exception:
                pass


# The processes that are left, killed and reaped, of this process, not of the one that forked it
@atexit.register
def _kill() -> None:
    pid = os.getpid()
    for child, owner in list(_running.items()):
        if owner != pid or (process := child._process) is None:  # pyright: ignore[reportPrivateUsage]
            continue
        if process.poll() is None:
            child.kill(signals.SIGKILL)
        process.wait()
        for stream in (child.stdin, child.stdout, child.stderr):
            if stream is not None:
                stream.close()
    _running.clear()


new = Pyjo_IOLoop_ChildProcess.new
object = Pyjo_IOLoop_ChildProcess
ChildProcess = Pyjo_IOLoop_ChildProcess
