"""
Pyjo.IOLoop.Server - Non-blocking TCP and UNIX domain socket server
===================================================================
::

    import Pyjo.IOLoop.Server

    # Create listen socket
    server = Pyjo.IOLoop.Server.new()
    server.on('accept', lambda server, handle: ...)
    server.listen(port=3000)

    # Start and stop accepting connections
    server.start()
    server.stop()

    # Start reactor if necessary
    if not server.reactor.is_running:
        server.reactor.start()

:mod:`Pyjo.IOLoop.Server` accepts TCP/IP and UNIX domain socket connections
for :mod:`Pyjo.IOLoop`.

The end of a ``with`` block closes the listen socket.

Events
------

:mod:`Pyjo.IOLoop.Server` inherits all events from :mod:`Pyjo.EventEmitter`
and can emit the following new ones.

accept
~~~~~~
::

    server.on('accept', lambda server, handle: ...)

Emitted for each accepted connection, with its :class:`socket.socket`, or the
:class:`ssl.SSLSocket` once TLS has been negotiated.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::IOLoop::Server <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/IOLoop/Server.pm>`_
of Mojolicious 9.49.
"""

import Pyjo.EventEmitter
import Pyjo.IOLoop
import Pyjo.IOLoop.TLS
import Pyjo.Reactor

import os
import re
import socket
import stat
import sys
import weakref

from types import TracebackType
from typing import Any, Self


class Pyjo_IOLoop_Server(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.IOLoop.Server` inherits all methods from
    :mod:`Pyjo.EventEmitter` and implements the following new ones.
    """

    def __init__(self) -> None:
        """::

            server = Pyjo.IOLoop.Server.new()

        Construct a new :mod:`Pyjo.IOLoop.Server` object.
        """
        super().__init__()
        self._active = False
        self._args: dict[str, Any] = {}
        self._handle: socket.socket | None = None
        self._reactor: weakref.ref[Pyjo.Reactor.object] | None = None
        self._reuse: str | None = None
        self._watched: weakref.ref[Pyjo.Reactor.object] | None = None

    def __del__(self) -> None:
        # Module globals may be gone at the end of the interpreter
        try:
            if not sys.is_finalizing() and getattr(self, '_handle', None) is not None:
                reactor = self._reactor() if self._reactor is not None else None
                Pyjo.Reactor._finalize(self.close, reactor)  # pyright: ignore[reportPrivateUsage]
        except Exception:
            pass

    # Not in Mojolicious: a context manager, which closes the listen socket where the block ends, as PyPy frees the
    # object only when its garbage collector runs
    def __enter__(self) -> Self:
        return self

    def __exit__(
        self, type: type[BaseException] | None, value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        self.close()

    @property
    def reactor(self) -> Pyjo.Reactor.object:
        """::

            reactor = server.reactor
            server.reactor = Pyjo.Reactor.Poll.new()

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

    # Not in Mojolicious: what DESTROY does, which Python does when it frees the server, PyPy only later
    def close(self) -> None:
        """::

            server.close()

        Stop accepting connections, close the listen socket and remove it from
        the ``PYJO_REUSE`` environment variable, as it happens when the server
        is freed.
        """
        if (reuse := self._reuse) is not None:
            self._reuse = None
            os.environ['PYJO_REUSE'] = re.sub(
                rf'(?:^|,){re.escape(reuse)}', '', os.environ.get('PYJO_REUSE', ''), count=1
            )
        if (handle := self._handle) is not None:
            if self._reactor is None or self._reactor() is not None:
                self.stop()
            self._handle = None
            handle.close()

    @classmethod
    def generate_port(cls) -> int:
        """::

            port = Pyjo.IOLoop.Server.object.generate_port()

        Find a free TCP port, primarily used for tests.
        """
        with socket.create_server(('127.0.0.1', 0), backlog=5) as handle:
            return handle.getsockname()[1]

    @property
    def handle(self) -> socket.socket | None:
        """::

            handle = server.handle

        Get handle for server, usually a :class:`socket.socket` object.
        """
        return self._handle

    @property
    def is_accepting(self) -> bool:
        """::

            boolean = server.is_accepting

        Check if connections are currently being accepted.
        """
        return self._active

    def listen(self, **options: Any) -> None:
        """::

            server.listen(port=3000)

        Create a new listen socket.

        These options are currently available:

        address
            ::

                address='127.0.0.1'

            Local address to listen on, defaults to ``0.0.0.0``.

        backlog
            ::

                backlog=128

            Maximum backlog size, defaults to :data:`socket.SOMAXCONN`.

        fd
            ::

                fd=3

            File descriptor with an already prepared listen socket.

        path
            ::

                path='/tmp/myapp.sock'

            Path for UNIX domain socket to listen on.

        port
            ::

                port=80

            Port to listen on, defaults to a random port.

        reuse
            ::

                reuse=True

            Allow multiple servers to use the same port with the
            ``SO_REUSEPORT`` socket option.

        single_accept
            ::

                single_accept=True

            Only accept one connection at a time.

        tls
            ::

                tls=True

            Enable TLS.

        tls_ca
            ::

                tls_ca='/etc/tls/ca.crt'

            Path to TLS certificate authority file.

        tls_cert
            ::

                tls_cert='/etc/tls/server.crt'
                tls_cert={'mojolicious.org': '/etc/tls/mojo.crt'}

            Path to the TLS cert file, defaults to a built-in test certificate.

        tls_context
            ::

                tls_context=ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

            The :class:`ssl.SSLContext` to use instead of the one that the
            other options make.

        tls_key
            ::

                tls_key='/etc/tls/server.key'
                tls_key={'mojolicious.org': '/etc/tls/mojo.key'}

            Path to the TLS key file, defaults to a built-in test key.
        """
        # Look for reusable file descriptor
        path = options.get('path')
        address = options.get('address') or '0.0.0.0'
        port = options.get('port')
        reuse_env = os.environ.setdefault('PYJO_REUSE', '')
        fd: int | None = None
        if path and (m := re.search(rf'(?:^|,)unix:{re.escape(path)}:(\d+)', reuse_env)):
            fd = int(m[1])
        elif port and (m := re.search(rf'(?:^|,){re.escape(f"{address}:{port}")}:(\d+)', reuse_env)):
            fd = int(m[1])

        # Reuse file descriptor
        if fd is None:
            fd = options.get('fd')
        if fd is not None:
            try:
                handle = socket.socket(fileno=fd)
            except OSError as e:
                raise _error(e, f"Can't open file descriptor {fd}") from e

        else:
            backlog = options.get('backlog')
            backlog = socket.SOMAXCONN if backlog is None else int(backlog)
            created: socket.socket | None = None
            try:
                # UNIX domain socket
                if path:
                    if os.path.exists(path) and stat.S_ISSOCK(os.stat(path).st_mode):
                        os.remove(path)
                    handle = created = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    handle.bind(path)
                    handle.listen(backlog)
                    reuse = self._reuse = f'unix:{path}:{handle.fileno()}'

                # IP socket
                else:
                    host = address.replace('[', '').replace(']', '')
                    family, _, _, _, sockaddr = socket.getaddrinfo(
                        host, port or 0, type=socket.SOCK_STREAM, flags=socket.AI_PASSIVE
                    )[0]
                    handle = created = socket.socket(family, socket.SOCK_STREAM)
                    handle.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    if options.get('reuse'):
                        handle.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                    handle.bind(sockaddr)
                    handle.listen(backlog)
                    reuse = self._reuse = f'{address}:{handle.getsockname()[1]}:{handle.fileno()}'
            except OSError as e:
                # The socket that cannot listen is closed, as Perl frees it
                if created is not None:
                    created.close()
                raise _error(e, "Can't create listen socket") from e

            os.environ['PYJO_REUSE'] = f'{reuse_env},{reuse}' if len(reuse_env) else reuse

        # Allow file descriptor inheritance, as local $^F = 1023
        handle.set_inheritable(True)
        handle.setblocking(False)
        self._args, self._handle = options, handle

        if not Pyjo.IOLoop.TLS.object.can_tls() and options.get('tls'):
            raise RuntimeError('TLS support is disabled')

    @property
    def port(self) -> int | None:
        """::

            port = server.port

        Get port this server is listening on.
        """
        if self._handle is None or self._handle.family == getattr(socket, 'AF_UNIX', None):
            return None
        return self._handle.getsockname()[1]

    def start(self) -> None:
        """::

            server.start()

        Start or resume accepting connections.
        """
        if (handle := self._handle) is None:
            return
        # Not in Mojolicious: an acceptor that is active already in this reactor is not watched again, where Mojo
        # replaces its watcher
        reactor = self.reactor
        if self._active and self._watched is not None and self._watched() is reactor:
            return
        ref = weakref.ref(self)

        def cb(reactor: Any, writable: bool) -> None:
            if (server := ref()) is not None:
                server._accept()

        self._active, self._watched = True, weakref.ref(reactor)
        reactor.io(handle, cb).watch(handle, True, False)

    def stop(self) -> None:
        """::

            server.stop()

        Stop accepting connections.
        """
        if self._active:
            self._active, self._watched = False, None
            if self._handle is not None:
                self.reactor.remove(self._handle)

    def _accept(self) -> None:
        # Greedy accept
        args = self._args
        accepted = 0
        ref = weakref.ref(self)

        def upgrade(tls: Any, handle: Any) -> None:
            if (server := ref()) is not None:
                server.emit('accept', handle)

        while self._active and self._handle is not None:
            if args.get('single_accept'):
                if accepted:
                    break
                accepted += 1
            try:
                handle = self._handle.accept()[0]
            except OSError:
                return
            handle.setblocking(False)

            # Disable Nagle's algorithm
            try:
                handle.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except OSError:
                pass

            if not args.get('tls'):
                self.emit('accept', handle)
                continue

            # Start TLS handshake
            tls = Pyjo.IOLoop.TLS.new(handle)
            tls.reactor = self.reactor
            tls.on('upgrade', upgrade)
            tls.on('error', _ignore)
            tls.negotiate(**{**args, 'server': True})


# The errors of a TLS handshake that fails are ignored
def _ignore(tls: Any, err: Any) -> None:
    pass


# Mojo's croak with $!: the same kind of error, with the message in front
def _error(e: OSError, message: str) -> OSError:
    error = type(e)(f'{message}: {e.strerror}' if e.strerror else message)
    error.errno = e.errno
    return error


new = Pyjo_IOLoop_Server.new
object = Pyjo_IOLoop_Server
