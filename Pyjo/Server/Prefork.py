"""
Pyjo.Server.Prefork - Pre-forking non-blocking I/O HTTP and WebSocket server
============================================================================
::

    import Pyjo.Server.Prefork

    prefork = Pyjo.Server.Prefork.new(listen=['http://*:8080'])


    @prefork.unsubscribe('request').on('request')
    def request(prefork, tx):
        # Request
        method = tx.req.method
        path = tx.req.url.path

        # Response
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = f'{method} request for {path}!'.encode()

        # Resume transaction
        tx.resume()


    prefork.run()

:mod:`Pyjo.Server.Prefork` is a full featured, UNIX optimized, pre-forking
non-blocking I/O HTTP and WebSocket server, built around the very well tested
and reliable :mod:`Pyjo.Server.Daemon`, with IPv6, TLS, SNI, UNIX domain
socket, Comet (long polling), keep-alive and multiple event loop support.
Note that the server uses signals for process management, so you should avoid
modifying signal handlers in your applications.

The workers are forks of the manager, made with :func:`os.fork`, so the
server runs where :func:`os.fork` exists, not on Windows. Name resolution in
a thread, SOCKS5 and TLS support can be disabled with the ``PYJO_NO_NNR``,
``PYJO_NO_SOCKS`` and ``PYJO_NO_TLS`` environment variables.

Manager signals
---------------

The :mod:`Pyjo.Server.Prefork` manager process can be controlled at runtime
with the following signals.

INT, TERM
~~~~~~~~~

Shut down server immediately.

QUIT
~~~~

Shut down server gracefully.

TTIN
~~~~

Increase worker pool by one.

TTOU
~~~~

Decrease worker pool by one.

Worker signals
--------------

:mod:`Pyjo.Server.Prefork` worker processes can be controlled at runtime
with the following signals.

QUIT
~~~~

Stop worker gracefully.

Events
------

:mod:`Pyjo.Server.Prefork` inherits all events from :mod:`Pyjo.Server.Daemon`
and can emit the following new ones.

finish
~~~~~~
::

    prefork.on('finish', lambda prefork, graceful: ...)

Emitted when the server shuts down. ::

    prefork.on('finish', lambda prefork, graceful: print('Graceful server shutdown' if graceful else 'Server shutdown'))

heartbeat
~~~~~~~~~
::

    prefork.on('heartbeat', lambda prefork, pid: ...)

Emitted when a heartbeat message has been received from a worker. ::

    prefork.on('heartbeat', lambda prefork, pid: print(f'Worker {pid} has a heartbeat'))

reap
~~~~
::

    prefork.on('reap', lambda prefork, pid: ...)

Emitted when a child process exited. ::

    prefork.on('reap', lambda prefork, pid: print(f'Worker {pid} stopped'))

spawn
~~~~~
::

    prefork.on('spawn', lambda prefork, pid: ...)

Emitted when a worker process is spawned. ::

    prefork.on('spawn', lambda prefork, pid: print(f'Worker {pid} started'))

wait
~~~~
::

    prefork.on('wait', lambda prefork: ...)

Emitted when the manager starts waiting for new heartbeat messages. ::

    prefork.on('wait', lambda prefork: print(f'Waiting for heartbeat messages from {prefork.workers} workers'))

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Server::Prefork <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Server/Prefork.pm>`_
of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.Exception
import Pyjo.File
import Pyjo.Server.Daemon

import os
import re
import select
import signal
import socket
import sys
import tempfile
import time
import traceback
import weakref

from typing import Any, NoReturn, TypedDict


class _Worker(TypedDict, total=False):
    force: bool
    graceful: float | None
    healthy: bool
    quit: int
    time: float


class Pyjo_Server_Prefork(Pyjo.Server.Daemon.object):
    """
    :mod:`Pyjo.Server.Prefork` inherits all methods from
    :mod:`Pyjo.Server.Daemon` and implements the following new ones.
    """

    def __init__(
        self,
        *,
        accepts: int = 10000,
        cleanup: bool = True,
        graceful_timeout: float = 120,
        heartbeat_interval: float = 5,
        heartbeat_timeout: float = 50,
        pid_file: str | os.PathLike[str] | None = None,
        spare: int = 2,
        workers: int = 4,
        **kwargs: Any,
    ) -> None:
        """::

            prefork = Pyjo.Server.Prefork.new()
            prefork = Pyjo.Server.Prefork.new(listen=['http://*:8080'], workers=10)

        Construct a new :mod:`Pyjo.Server.Prefork` object.
        """
        super().__init__(**kwargs)

        self.accepts = accepts
        """::

            accepts = prefork.accepts
            prefork.accepts = 100

        Maximum number of connections a worker is allowed to accept, before
        stopping gracefully and then getting replaced with a newly started
        worker, passed along to :attr:`Pyjo.IOLoop.Pyjo_IOLoop.max_accepts`,
        defaults to ``10000``. Setting the value to ``0`` will allow workers to
        accept new connections indefinitely. Note that up to half of this value
        can be subtracted randomly to improve load balancing, and to make sure
        that not all workers restart at the same time.
        """

        self.cleanup = cleanup
        """::

            boolean = prefork.cleanup
            prefork.cleanup = False

        Delete :attr:`pid_file` automatically once it is not needed anymore,
        defaults to a true value.
        """

        self.graceful_timeout = graceful_timeout
        """::

            timeout = prefork.graceful_timeout
            prefork.graceful_timeout = 15

        Maximum amount of time in seconds stopping a worker gracefully may take
        before being forced, defaults to ``120``. Note that this value should
        usually be a little larger than the maximum amount of time you expect
        any one request to take.
        """

        self.heartbeat_interval = heartbeat_interval
        """::

            interval = prefork.heartbeat_interval
            prefork.heartbeat_interval = 3

        Heartbeat interval in seconds, defaults to ``5``.
        """

        self.heartbeat_timeout = heartbeat_timeout
        """::

            timeout = prefork.heartbeat_timeout
            prefork.heartbeat_timeout = 2

        Maximum amount of time in seconds before a worker without a heartbeat
        will be stopped gracefully, defaults to ``50``. Note that this value
        should usually be a little larger than the maximum amount of time you
        expect any one operation to block the event loop.
        """

        self.pid_file: str | os.PathLike[str] = (
            pid_file if pid_file is not None else os.path.join(tempfile.gettempdir(), 'prefork.pid')
        )
        """::

            file = prefork.pid_file
            prefork.pid_file = '/tmp/prefork.pid'

        Full path of process id file, defaults to ``prefork.pid`` in a
        temporary directory.
        """

        self.spare = spare
        """::

            spare = prefork.spare
            prefork.spare = 4

        Temporarily spawn up to this number of additional workers if there is a
        need, defaults to ``2``. This allows for new workers to be started while
        old ones are still shutting down gracefully, drastically reducing the
        performance cost of worker restarts.
        """

        self.workers = workers
        """::

            workers = prefork.workers
            prefork.workers = 10

        Number of worker processes, defaults to ``4``. A good rule of thumb is
        two worker processes per CPU core for applications that perform mostly
        non-blocking operations, blocking operations often require more and
        benefit from decreasing concurrency with
        :attr:`Pyjo.Server.Daemon.Pyjo_Server_Daemon.max_clients` (often as
        low as ``1``).
        """

        self._finished = False
        self._graceful = False
        self._pool: dict[int, _Worker] = {}
        self._reader: int | None = None
        self._running = False
        self._signals: list[int] = []
        self._wakee: socket.socket | None = None
        self._writer: int | None = None

    def check_pid(self) -> int | None:
        """::

            pid = prefork.check_pid()

        Get process id for running server from :attr:`pid_file` or delete it if
        server is not running. ::

            if not prefork.check_pid():
                print('Server is not running')
        """
        file = Pyjo.File.new(self.pid_file)
        if not os.access(file, os.R_OK):
            return None
        try:
            pid = int((file.slurp() or b'').strip())
        except ValueError:
            pid = 0

        # Running
        if pid and _kill(0, pid):
            return pid

        # Not running
        file.remove()
        return None

    def ensure_pid_file(self, pid: int) -> None:
        """::

            prefork.ensure_pid_file(pid)

        Ensure :attr:`pid_file` exists.
        """
        # Check if PID file already exists
        file = Pyjo.File.new(self.pid_file)
        if os.path.exists(file):
            return

        # Create PID file
        try:
            file.spew(f'{pid}\n'.encode()).chmod(0o644)
        except Exception as e:
            err = f'Can\'t create process id file "{file}": {e}'
            self.app.log.error(err)
            raise Pyjo.Exception.new(err) from e
        self.app.log.info(f'Creating process id file "{file}"')

    @property
    def healthy(self) -> int:
        """::

            healthy = prefork.healthy

        Number of currently active worker processes with a heartbeat.
        """
        return sum(1 for w in self._pool.values() if w.get('healthy'))

    def run(self) -> None:
        """::

            prefork.run()

        Run server and wait for the manager signals.
        """
        # Unlike Mojolicious: no fork at all, where Mojo has no fork emulation of Perl on Windows
        if not hasattr(os, 'fork'):
            print('Pre-forking needs os.fork.')
            sys.exit(0)

        # Pipe for worker communication
        try:
            reader, writer = self._reader, self._writer = os.pipe()
        except OSError as e:
            raise OSError(e.errno, f"Can't create pipe: {e.strerror}") from e

        # Clean manager environment
        # Not in Mojolicious: a handler only notes the signal, which the manager handles where it waits for
        # heartbeats, as Perl defers the handlers of signals to a safe point, and a socket pair that Python writes to
        # on a signal wakes the manager up, as Python repeats a system call that a signal interrupts until its timeout
        def note(signum: int, frame: Any) -> None:
            self._signals.append(signum)

        # Not in Mojolicious: local %SIG, the handlers of the signals are set back at the end
        handlers: dict[signal.Signals, Any] = {}
        for name in (signal.SIGCHLD, signal.SIGINT, signal.SIGTERM, signal.SIGQUIT, signal.SIGTTIN, signal.SIGTTOU):
            handlers[name] = signal.signal(name, note)
        waker, self._wakee = socket.socketpair()
        waker.setblocking(False)
        self._wakee.setblocking(False)
        wakeup = signal.set_wakeup_fd(waker.fileno())

        try:
            # Preload application before starting workers
            self.start().app.log.info(f'Manager {os.getpid()} started')
            self.ioloop.max_accepts = self.accepts
            self._running = True
            while self._running:
                self._manage()
            self.app.log.info(f'Manager {os.getpid()} stopped')
        finally:
            signal.set_wakeup_fd(wakeup)
            for name, handler in handlers.items():
                signal.signal(name, handler)

            # Not in Mojolicious: the pipe is closed at the end, as Perl closes it with the object
            os.close(reader)
            os.close(writer)
            waker.close()
            self._wakee.close()
            self._reader = self._writer = self._wakee = None

    # DESTROY: the process id file is deleted with the object, after the listen sockets of the daemon are closed
    def _cleanup(self) -> None:
        super()._cleanup()
        if self.cleanup:
            Pyjo.File.new(self.pid_file).remove()

    def _heartbeat(self, finished: bool) -> None:
        try:
            assert self._writer is not None
            os.write(self._writer, f'{os.getpid()}:{int(finished)}\n'.encode())
        except Exception:
            _exit(0)

    def _manage(self) -> None:
        # Spawn more workers if necessary and check PID file
        if not self._finished:
            graceful = sum(1 for w in self._pool.values() if w.get('graceful'))
            spare = self.spare
            spare = (spare if graceful > spare else graceful) if graceful else 0
            need = (self.workers - len(self._pool)) + spare
            while need > 0:
                self._spawn()
                need -= 1
            self.ensure_pid_file(os.getpid())

        # Shutdown
        elif not len(self._pool):
            self._running = False
            return

        # Wait for heartbeats
        self._wait()

        interval = self.heartbeat_interval
        ht = self.heartbeat_timeout
        gt = self.graceful_timeout
        log = self.app.log
        now = time.monotonic()

        for pid in list(self._pool):
            if (w := self._pool.get(pid)) is None:
                continue

            # No heartbeat (graceful stop)
            if not w.get('graceful') and w.get('time', now) + interval + ht <= now:
                log.error(f'Worker {pid} has no heartbeat ({_number(ht)} seconds), restarting (see FAQ for more)')
                w['graceful'] = now

            # Graceful stop with timeout
            graceful = w['graceful'] = w.get('graceful') or (now if self._graceful else None)
            if graceful:
                quit = w.get('quit', 0)
                w['quit'] = quit + 1
                if not quit:
                    log.info(f'Stopping worker {pid} gracefully ({_number(gt)} seconds)')
                    if not _kill(signal.SIGQUIT, pid):
                        self._stopped(pid)
            if graceful and graceful + gt <= now:
                w['force'] = True

            # Normal stop
            if w.get('force') or (self._finished and not graceful):
                log.warn(f'Stopping worker {pid} immediately')
                if not _kill(signal.SIGKILL, pid):
                    self._stopped(pid)

    # The signals that the handlers noted, as the handlers of Mojo do them
    def _signal(self) -> None:
        while len(self._signals):
            signum = self._signals.pop(0)
            if signum == signal.SIGCHLD:
                while True:
                    try:
                        pid, _ = os.waitpid(-1, os.WNOHANG)
                    except ChildProcessError:
                        break
                    if pid <= 0:
                        break
                    self.emit('reap', pid)._stopped(pid)
            elif signum in (signal.SIGINT, signal.SIGTERM):
                self._term()
            elif signum == signal.SIGQUIT:
                self._term(True)
            elif signum == signal.SIGTTIN:
                self.workers += 1
            elif signum == signal.SIGTTOU and self.workers > 0:
                self.workers -= 1
                for w in self._pool.values():
                    if not w.get('graceful'):
                        w['graceful'] = time.monotonic()
                        break

    def _spawn(self) -> None:
        # Manager
        # Not in Mojolicious: the buffers of the standard streams are written before, so that the worker does not write
        # them again
        _flush()
        try:
            pid = os.fork()
        except OSError as e:
            raise OSError(e.errno, f"Can't fork: {e.strerror}") from e
        if pid:
            self.emit('spawn', pid)._pool[pid] = {'time': time.monotonic()}
            return

        self._worker()

    def _stopped(self, pid: int) -> None:
        if (w := self._pool.pop(pid, None)) is None:
            return

        log = self.app.log
        log.info(f'Worker {pid} stopped')
        if not w.get('healthy'):
            log.error(f'Worker {pid} stopped too early, shutting down')
            self._term()

    def _term(self, graceful: bool = False) -> None:
        self.emit('finish', graceful)
        self._finished, self._graceful = True, graceful

    def _wait(self) -> None:
        # Poll for heartbeats
        reader, wakee = self.emit('wait')._reader, self._wakee
        assert reader is not None and wakee is not None
        readable = select.select([reader, wakee], [], [], 1)[0]
        if wakee in readable:
            try:
                wakee.recv(4096)
            except OSError:
                pass
        self._signal()
        if reader not in readable:
            return
        try:
            chunk = os.read(reader, 4194304)
        except OSError:
            return
        if not chunk:
            return

        # Update heartbeats (and stop gracefully if necessary)
        now = time.monotonic()
        for m in re.finditer(rb'(\d+):(\d)\n', chunk):
            if (w := self._pool.get(int(m[1]))) is None:
                continue
            w['healthy'], w['time'] = True, now
            self.emit('heartbeat', int(m[1]))
            if m[2] != b'0':
                w['graceful'] = w.get('graceful') or now
                w['quit'] = w.get('quit', 0) + 1

    # The worker, a fork of the manager, which runs the event loop until it stops, and exits
    def _worker(self) -> NoReturn:
        code = 0
        try:
            # Heartbeat messages
            self.cleanup = False
            loop = self.ioloop
            finished = False

            def finish(loop: Any) -> None:
                nonlocal finished
                finished = True

            loop.on('finish', finish)
            ref = weakref.ref(self)

            def heartbeat(loop: Any) -> None:
                if (prefork := ref()) is not None:
                    prefork._heartbeat(finished)

            loop.next_tick(heartbeat)
            loop.recurring(self.heartbeat_interval, heartbeat)

            # Clean worker environment
            for name in (signal.SIGCHLD, signal.SIGINT, signal.SIGTERM, signal.SIGTTIN, signal.SIGTTOU):
                signal.signal(name, signal.SIG_DFL)
            # Not in Mojolicious: the handler of QUIT only notes the signal, which the event loop handles, as Perl defers
            # the handlers of signals to a safe point, and a socket pair that Python writes to on a signal wakes the
            # event loop up, as Python repeats a system call that a signal interrupts until its timeout
            quit = False

            def note(signum: int, frame: Any) -> None:
                nonlocal quit
                quit = True

            signal.signal(signal.SIGQUIT, note)
            waker, wakee = socket.socketpair()
            waker.setblocking(False)
            wakee.setblocking(False)
            signal.set_wakeup_fd(waker.fileno())

            def wake(reactor: Any, writable: bool) -> None:
                nonlocal quit
                try:
                    wakee.recv(4096)
                except OSError:
                    pass
                if quit:
                    quit = False
                    loop.stop_gracefully()

            loop.reactor.io(wakee, wake).watch(wakee, True, False)

            def max_requests(loop: Any) -> None:
                if (prefork := ref()) is not None:
                    prefork.max_requests = 1

            loop.on('finish', max_requests)
            if (reader := self._reader) is not None:
                self._reader = None
                os.close(reader)
            # Left out from Mojolicious: srand, as random seeds itself again in the child of a fork

            self.app.log.info(f'Worker {os.getpid()} started')
            loop.start()

        # Not in Mojolicious: sys.exit() is the exit of the worker, as exit is in Perl
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 0 if e.code is None else 1
        except BaseException:
            traceback.print_exc()
            code = 255
        _exit(code)


# Not in Mojolicious: os._exit, as the worker leaves what the manager does at its end, with the buffers of the standard
# streams written before, which os._exit leaves
def _exit(code: int) -> NoReturn:
    _flush()
    os._exit(code)


def _flush() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.flush()
        except Exception:
            pass


# Perl's kill, true if the signal was sent
def _kill(sig: int, pid: int) -> bool:
    try:
        os.kill(pid, sig)
        return True
    except OSError:
        return False


# A number of seconds as Perl prints it, without ".0"
def _number(value: float) -> str:
    return str(int(value)) if value == int(value) else str(value)


new = Pyjo_Server_Prefork.new
object = Pyjo_Server_Prefork
