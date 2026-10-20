"""
Pyjo.Server.Prethread - Pre-threading non-blocking I/O HTTP and WebSocket server
================================================================================
::

    import Pyjo.Server.Prethread

    prethread = Pyjo.Server.Prethread.new(listen=['http://*:8080'])


    @prethread.unsubscribe('request').on('request')
    def request(prethread, tx):
        # Request
        method = tx.req.method
        path = tx.req.url.path

        # Response
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = f'{method} request for {path}!'.encode()

        # Resume transaction
        tx.resume()


    prethread.run()

:mod:`Pyjo.Server.Prethread` is a full featured pre-threading non-blocking
I/O HTTP and WebSocket server, which works as :mod:`Pyjo.Server.Prefork`
does, with threads of one process for the worker processes. Each worker is a
copy of the server in a thread of its own, with the :data:`Pyjo.IOLoop.singleton`
of the thread and the listen sockets of the manager. Note that the server uses
signals for process management, so you should avoid modifying signal handlers
in your applications.

The workers share the memory of the process and the application that the
manager has loaded, so the application has to be safe to use in several
threads at the same time. Python runs one thread at a time where it has the
global interpreter lock, so that the workers run at the same time only while
they wait, for the network or a blocking call, and on all processor cores on
a free-threaded Python. A worker that does not stop when it is told to, as
one in a blocking call, cannot be killed, as a process can, so the manager
leaves it, and it ends with the process.

Manager signals
---------------

The :mod:`Pyjo.Server.Prethread` manager process can be controlled at runtime
with the following signals.

INT, TERM
~~~~~~~~~

Shut down server gracefully. A second ``INT``, as of Ctrl-C pressed twice,
shuts it down immediately, a second ``TERM`` does nothing.

QUIT
~~~~

Shut down server immediately.

HUP
~~~

Restart the workers gracefully, or emit the event ``reload`` when it has
subscribers.

TTIN
~~~~

Increase worker pool by one.

TTOU
~~~~

Decrease worker pool by one.

The manager does not handle ``CHLD``, so that the application gets the exit
status of its child processes.

Events
------

:mod:`Pyjo.Server.Prethread` inherits all events from
:mod:`Pyjo.Server.Prefork`, which pass the id of the thread of a worker, as
:func:`threading.get_native_id` gives it, where :mod:`Pyjo.Server.Prefork`
passes its process id. ::

    prethread.on('spawn', lambda prethread, id: print(f'Worker {id} started'))

See also
--------

:mod:`Pyjoyment.Command.prethread`, :mod:`Pyjo.Server.Prefork`,
:mod:`Pyjoyment`, https://mojolicious.org.

It has no counterpart in Mojolicious; it is inspired by
:mod:`Pyjo.Server.Prefork`, the counterpart of `Mojo::Server::Prefork
<https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Server/Prefork.pm>`_,
as `Thrall <https://metacpan.org/pod/Thrall>`_ is by Starlight.

Classes
-------
"""

import Pyjo.IOLoop
import Pyjo.Server.Prefork
import Pyjo.URL

import copy
import os
import signal
import socket
import sys
import tempfile
import threading
import time
import traceback
import weakref

from typing import Any, NotRequired, TypedDict


class _Thread(TypedDict):
    control: socket.socket
    ended: threading.Event
    killed: NotRequired[float]
    thread: threading.Thread


class Pyjo_Server_Prethread(Pyjo.Server.Prefork.object):
    """
    :mod:`Pyjo.Server.Prethread` inherits all attributes and methods from
    :mod:`Pyjo.Server.Prefork`, with ``prethread.pid`` in a temporary
    directory for the default of :attr:`~Pyjo.Server.Prefork.Pyjo_Server_Prefork.pid_file`.
    """

    # The signals of the manager, without CHLD, which is the one of the children of the application; Windows has INT,
    # TERM and BREAK of Ctrl-Break, which takes the place of QUIT
    if sys.platform == 'win32':
        _MANAGED = (signal.SIGINT, signal.SIGTERM, signal.SIGBREAK)
    else:
        _MANAGED = (signal.SIGHUP, signal.SIGINT, signal.SIGTERM, signal.SIGQUIT, signal.SIGTTIN, signal.SIGTTOU)

    # The seconds that a worker has to stop once it is told to stop immediately, before the manager leaves it
    _LEAVE = 1

    def __init__(self, *, pid_file: str | os.PathLike[str] | None = None, **kwargs: Any) -> None:
        """::

            prethread = Pyjo.Server.Prethread.new()
            prethread = Pyjo.Server.Prethread.new(listen=['http://*:8080'], workers=10)

        Construct a new :mod:`Pyjo.Server.Prethread` object.
        """
        super().__init__(
            pid_file=pid_file if pid_file is not None else os.path.join(tempfile.gettempdir(), 'prethread.pid'),
            **kwargs,
        )
        self._threads: dict[int, _Thread] = {}

    def _heartbeat(self, finished: bool) -> None:
        try:
            assert self._writer is not None
            os.write(self._writer, f'{threading.get_native_id()}:{int(finished)}\n'.encode())
        except Exception:
            Pyjo.IOLoop.singleton.stop()

    def _kill_worker(self, pid: int, graceful: bool) -> bool:
        if (t := self._threads.get(pid)) is None:
            return False
        if not graceful:
            now = time.monotonic()
            if (killed := t.get('killed')) is not None:
                if killed + self._LEAVE > now:
                    return True
                self.app.log.error(f'Worker {pid} does not stop, leaving it')
                self._threads.pop(pid)['control'].close()
                return False
            t['killed'] = now
        try:
            t['control'].send(b'T' if graceful else b'Q')
        except OSError:
            pass
        return True

    def _spawn(self) -> None:
        # The listen sockets of the manager, which the worker duplicates
        loop = self.ioloop
        listen = [
            (location, loop.acceptor(id).handle.fileno())
            for location, id in zip(self.listen, self.acceptors, strict=True)
        ]
        control, wakee = socket.socketpair()
        ended = threading.Event()
        thread = threading.Thread(
            target=self._serve, args=(listen, wakee, ended), name='Pyjo.Server.Prethread', daemon=True
        )
        thread.start()
        assert (id := thread.native_id) is not None
        self._threads[id] = {'control': control, 'ended': ended, 'thread': thread}
        self.emit('spawn', id)._pool[id] = {'time': time.monotonic()}

    def _wait(self) -> None:
        super()._wait()

        # The workers that have stopped, which the last line of a worker tells, with the moment that its thread takes to
        # end after it
        for id, t in list(self._threads.items()):
            if t['ended'].is_set():
                t['thread'].join(1)
            if t['thread'].is_alive():
                continue
            t['control'].close()
            del self._threads[id]
            self.emit('reap', id)._stopped(id)

    # The worker, a copy of the server in a thread, which runs the event loop of the thread until it stops
    def _serve(self, listen: list[tuple[Any, int]], control: socket.socket, ended: threading.Event) -> None:
        worker = copy.copy(self)
        loop = worker.ioloop = Pyjo.IOLoop.singleton
        worker.acceptors, worker._connections, worker._servers = [], {}, {}
        worker.cleanup, worker.silent = False, True
        try:
            # The listen sockets of the manager, duplicated, as the worker closes them
            loop.max_accepts = self.accepts
            if max := worker.max_clients:
                loop.max_connections = max
            for location, fd in listen:
                worker._listen(_location(location, os.dup(fd)))

            # Heartbeat messages
            finished = False
            ref = weakref.ref(worker)

            def finish(loop: Any) -> None:
                nonlocal finished
                finished = True
                if (worker := ref()) is not None:
                    worker.max_requests = 1

            loop.on('finish', finish)

            def heartbeat(loop: Any) -> None:
                if (worker := ref()) is not None:
                    worker._heartbeat(finished)

            loop.next_tick(heartbeat)
            loop.recurring(self.heartbeat_interval, heartbeat)

            # The manager stops the worker with a byte, gracefully, or immediately, also when it is gone
            def command(reactor: Any, writable: bool) -> None:
                try:
                    chunk = control.recv(4096)
                except OSError:
                    return
                if not chunk or b'Q' in chunk:
                    loop.stop()
                else:
                    loop.stop_gracefully()

            loop.reactor.io(control, command).watch(control, True, False)

            self.app.log.info(f'Worker {threading.get_native_id()} started')
            loop.start()
        except BaseException:
            traceback.print_exc()
        finally:
            loop.reactor.remove(control)
            control.close()
            worker._cleanup()
            loop.reset()

            # The manager is woken up, to reap the worker at once
            ended.set()
            try:
                if (writer := self._writer) is not None:
                    os.write(writer, b'\n')
            except OSError:
                pass


# A listen location for the duplicate of a listen socket, without the port and the path that would find the socket of
# the manager in PYJO_REUSE
def _location(location: Any, fd: int) -> str:
    url = Pyjo.URL.new(str(location))
    if url.protocol.endswith('+unix'):
        url.host = None
    else:
        url.port = None
    url.query.append(fd=fd)
    return str(url)


new = Pyjo_Server_Prethread.new
object = Pyjo_Server_Prethread
