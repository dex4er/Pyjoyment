"""
Pyjo.IOLoop.Client - Non-blocking TCP/IP and UNIX domain socket client
======================================================================
::

    import Pyjo.IOLoop.Client

    # Create socket connection
    client = Pyjo.IOLoop.Client.new()
    client.on('connect', lambda client, handle: ...)
    client.on('error', lambda client, err: ...)
    client.connect(address='example.com', port=80)

    # Start reactor if necessary
    if not client.reactor.is_running:
        client.reactor.start()

:mod:`Pyjo.IOLoop.Client` opens TCP/IP and UNIX domain socket connections for
:mod:`Pyjo.IOLoop`.

Events
------

:mod:`Pyjo.IOLoop.Client` inherits all events from :mod:`Pyjo.EventEmitter`
and can emit the following new ones.

connect
~~~~~~~
::

    client.on('connect', lambda client, handle: ...)

Emitted once the connection is established, with its :class:`socket.socket`,
or the :class:`ssl.SSLSocket` once TLS has been negotiated.

error
~~~~~
::

    client.on('error', lambda client, err: ...)

Emitted if an error occurs on the connection, fatal if unhandled. The error is
a message, or the :class:`OSError` of the system.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::IOLoop::Client <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/IOLoop/Client.pm>`_
of Mojolicious 9.49.
"""

import Pyjo.EventEmitter
import Pyjo.IOLoop
import Pyjo.IOLoop.TLS
import Pyjo.Reactor

import concurrent.futures
import errno
import os
import socket
import sys
import weakref

from collections.abc import Callable
from typing import Any


# Non-blocking name resolution, which Mojo does with Net::DNS::Native, is a thread of the standard library here
NNR = not os.environ.get('PYJO_NO_NNR')
_executor: concurrent.futures.ThreadPoolExecutor | None = None

# Left out from Mojolicious: SOCKS support, which requires IO::Socket::Socks
SOCKS = False

type AddrInfo = list[tuple[Any, Any, Any, Any, Any]]


class _Resolver:
    """A name resolution in a thread, which makes a socket readable once it is done."""

    def __init__(self, host: str, port: int) -> None:
        global _executor
        if _executor is None:
            _executor = concurrent.futures.ThreadPoolExecutor(max_workers=5, thread_name_prefix='Pyjo.IOLoop.Client')
        self.handle, self._writer = socket.socketpair()
        self.handle.setblocking(False)
        self.future = _executor.submit(
            socket.getaddrinfo, host, port, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
        )
        self.future.add_done_callback(self._done)

    def _done(self, future: Any) -> None:
        try:
            self._writer.send(b'.')
        except OSError:
            pass

    def close(self) -> None:
        self.future.cancel()
        self.handle.close()
        self._writer.close()


class Pyjo_IOLoop_Client(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.IOLoop.Client` inherits all methods from
    :mod:`Pyjo.EventEmitter` and implements the following new ones.
    """

    def __init__(self, *, reactor: Pyjo.Reactor.object | None = None) -> None:
        """::

            client = Pyjo.IOLoop.Client.new()
            client = Pyjo.IOLoop.Client.new(reactor=Pyjo.Reactor.Poll.new())

        Construct a new :mod:`Pyjo.IOLoop.Client` object.
        """
        super().__init__()
        self._addresses: AddrInfo = []
        self._dns: _Resolver | None = None
        self._handle: Any = None
        self._reactor: weakref.ref[Pyjo.Reactor.object] | None = None
        self._timer: str | None = None
        if reactor is not None:
            self.reactor = reactor

    def __del__(self) -> None:
        # Module globals may be gone at the end of the interpreter
        try:
            if not sys.is_finalizing():
                self.close()
        except Exception:
            pass

    @property
    def reactor(self) -> Pyjo.Reactor.object:
        """::

            reactor = client.reactor
            client.reactor = Pyjo.Reactor.Poll.new()

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

    @classmethod
    def can_nnr(cls) -> bool:
        """::

            boolean = Pyjo.IOLoop.Client.object.can_nnr()

        True if non-blocking name resolution support is enabled, as it is
        unless the ``PYJO_NO_NNR`` environment variable is set. The names are
        resolved in a thread.
        """
        return NNR

    @classmethod
    def can_socks(cls) -> bool:
        """::

            boolean = Pyjo.IOLoop.Client.object.can_socks()

        True if SOCKS5 support is available, which it is not yet.
        """
        return SOCKS

    # Not in Mojolicious: what DESTROY does, which Python does when it frees the client, PyPy only later
    def close(self) -> None:
        """::

            client.close()

        Stop connecting and close a socket that is not connected yet, as it
        happens when the client is freed.
        """
        handle = self._handle
        self._cleanup()
        if handle is not None:
            handle.close()

    def connect(self, **options: Any) -> None:
        """::

            client.connect(address='127.0.0.1', port=3000)

        Open a socket connection to a remote host.

        These options are currently available:

        address
            ::

                address='mojolicious.org'

            Address or host name of the peer to connect to, defaults to
            ``127.0.0.1``.

        handle
            ::

                handle=handle

            Use an already prepared :class:`socket.socket` object.

        path
            ::

                path='/tmp/myapp.sock'

            Path of UNIX domain socket to connect to.

        port
            ::

                port=80

            Port to connect to, defaults to ``80`` or ``443`` with ``tls``
            option.

        source_address
            ::

                source_address=('127.0.0.1', 0)

            Local address and port to connect from.

        timeout
            ::

                timeout=15

            Maximum amount of time in seconds establishing connection may take
            before getting canceled, defaults to ``10``.

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

                tls_cert='/etc/tls/client.crt'

            Path to the TLS certificate file.

        tls_context
            ::

                tls_context=ssl.create_default_context()

            The :class:`ssl.SSLContext` to use instead of the one that the
            other options make.

        tls_hostname
            ::

                tls_hostname='mojolicious.org'

            Name of the server for SNI and the verification of its
            certificate instead of ``address``, an empty one for no SNI.

        tls_key
            ::

                tls_key='/etc/tls/client.key'

            Path to the TLS key file.
        """
        args = dict(options)

        # Timeout
        ref = weakref.ref(self)
        reactor = self.reactor

        def timeout(reactor: Any) -> None:
            if (client := ref()) is not None:
                client.emit('error', 'Connect timeout')

        self._timer = reactor.timer(args.get('timeout') or 10, timeout)

        # Blocking name resolution
        for key in ('address', 'socks_address'):
            if args.get(key):
                args[key] = str(args[key]).replace('[', '').replace(']', '')
        if not args.get('address'):
            args['address'] = '127.0.0.1'
        address = args.get('socks_address') or args['address']
        if not NNR or args.get('handle') or args.get('path'):

            def connect(reactor: Any) -> None:
                if (client := ref()) is not None:
                    client._connect(args)

            return reactor.next_tick(connect)

        # Non-blocking name resolution
        dns = self._dns = _Resolver(address, _port(args))

        def resolved(reactor: Any, writable: bool) -> None:
            if (client := ref()) is None:
                return
            reactor.remove(dns.handle)
            client._dns = None
            try:
                args['addr_info'] = dns.future.result()
            except OSError as e:
                client.emit('error', f"Can't resolve: {e.strerror or e}")
                return
            finally:
                dns.close()
            client._connect(args)

        reactor.io(dns.handle, resolved).watch(dns.handle, True, False)

    # Left out from Mojolicious: can_socks and the options socks_*, as SOCKS support requires IO::Socket::Socks

    def _cleanup(self) -> None:
        if (dns := self._dns) is not None:
            self._dns = None
            dns.close()
        reactor = self._reactor() if self._reactor is not None else None
        if reactor is None:
            return
        for name in ('_timer', '_handle'):
            if (value := getattr(self, name)) is not None:
                setattr(self, name, None)
                try:
                    reactor.remove(value)
                except Exception:
                    pass

    def _connect(self, args: dict[str, Any]) -> None:
        path = args.get('path')
        handle = self._handle = args.get('handle')

        if handle is None:
            try:
                # UNIX domain socket
                if path:
                    handle = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    handle.setblocking(False)
                    _connect_ex(handle, path)

                # IP socket, as IO::Socket::IP tries the addresses of the name one after another
                else:
                    self._addresses = list(
                        args.get('addr_info')
                        or socket.getaddrinfo(
                            args.get('socks_address') or args['address'],
                            _port(args),
                            type=socket.SOCK_STREAM,
                            proto=socket.IPPROTO_TCP,
                        )
                    )
                    handle = self._next(args)
            except OSError as e:
                self.emit('error', f"Can't connect: {e.strerror or e}")
                return
            self._handle = handle
        handle.setblocking(False)

        if path:
            self._try_socks(args)
        else:
            self._wait(self._ready, handle, args)

    # The next address of the name that a socket can connect from, as IO::Socket::IP tries them all
    def _next(self, args: dict[str, Any]) -> socket.socket:
        error: OSError | None = None
        while len(self._addresses):
            family, type, proto, _, sockaddr = self._addresses.pop(0)
            handle = socket.socket(family, type, proto)
            try:
                handle.setblocking(False)
                # Unlike Mojolicious: socket_options of IO::Socket::IP is source_address, as socket.create_connection has
                # it
                if (source := args.get('source_address')) is not None:
                    handle.bind(source)
                _connect_ex(handle, sockaddr)
            except OSError as e:
                handle.close()
                error = e
                continue
            return handle
        raise error or OSError(errno.EADDRNOTAVAIL, os.strerror(errno.EADDRNOTAVAIL))

    def _ready(self, args: dict[str, Any]) -> None:
        handle = self._handle
        if handle is None:
            return

        # Socket changes in between attempts and needs to be re-added for epoll/kqueue
        if err := handle.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR):
            self.reactor.remove(handle)
            handle.close()
            self._handle = None
            if not len(self._addresses):
                self.emit('error', OSError(err, os.strerror(err)))
                return
            try:
                handle = self._handle = self._next(args)
            except OSError as e:
                self.emit('error', e)
                return
            return self._wait(self._ready, handle, args)

        try:
            handle.getpeername()
        except OSError as e:
            self.emit('error', e)
            return

        # Disable Nagle's algorithm
        try:
            handle.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError:
            pass

        self._try_socks(args)

    def _try_socks(self, args: dict[str, Any]) -> None:
        if not args.get('socks_address'):
            return self._try_tls(args)
        self.emit('error', 'SOCKS support is not available')

    def _try_tls(self, args: dict[str, Any]) -> None:
        handle = self._handle
        if not args.get('tls'):
            self._cleanup()
            self.emit('connect', handle)
            return
        reactor = self.reactor
        reactor.remove(handle)
        self._handle = None

        # Start TLS handshake
        ref = weakref.ref(self)

        def upgrade(tls: Any, handle: Any) -> None:
            if (client := ref()) is not None:
                client._cleanup()
                client.emit('connect', handle)

        def error(tls: Any, err: Any) -> None:
            if (client := ref()) is not None:
                client.emit('error', err)

        tls = Pyjo.IOLoop.TLS.new(handle)
        tls.reactor = reactor
        tls.on('upgrade', upgrade)
        tls.on('error', error)
        tls.negotiate(**args)

    def _wait(self, next: Callable[[dict[str, Any]], None], handle: Any, args: dict[str, Any]) -> None:
        ref = weakref.ref(self)
        name = next.__name__

        def cb(reactor: Any, writable: bool) -> None:
            if (client := ref()) is not None:
                getattr(client, name)(args)

        self.reactor.io(handle, cb).watch(handle, False, True)


# A connection that does not block
def _connect_ex(handle: socket.socket, address: Any) -> None:
    err = handle.connect_ex(address)
    if err and err not in (errno.EINPROGRESS, errno.EWOULDBLOCK, errno.EAGAIN):
        raise OSError(err, os.strerror(err))


def _port(args: dict[str, Any]) -> int:
    return int(args.get('socks_port') or args.get('port') or (443 if args.get('tls') else 80))


new = Pyjo_IOLoop_Client.new
object = Pyjo_IOLoop_Client
