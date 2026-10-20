"""
Pyjo.IOLoop.TLS - Non-blocking TLS handshake
============================================
::

    import Pyjo.IOLoop.TLS

    # Negotiate TLS
    tls = Pyjo.IOLoop.TLS.new(old_handle)
    tls.on('upgrade', lambda tls, new_handle: ...)
    tls.on('error', lambda tls, err: ...)
    tls.negotiate(server=True)

    # Start reactor if necessary
    if not tls.reactor.is_running:
        tls.reactor.start()

:mod:`Pyjo.IOLoop.TLS` negotiates TLS for :mod:`Pyjo.IOLoop`, with the
:mod:`ssl` module of the standard library.

The end of a ``with`` block closes the connection of the handshake.

Events
------

:mod:`Pyjo.IOLoop.TLS` inherits all events from :mod:`Pyjo.EventEmitter` and
can emit the following new ones.

upgrade
~~~~~~~
::

    tls.on('upgrade', lambda tls, handle: ...)

Emitted once TLS has been negotiated, with the :class:`ssl.SSLSocket`.

error
~~~~~
::

    tls.on('error', lambda tls, err: ...)

Emitted if an error occurs during negotiation, fatal if unhandled.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::IOLoop::TLS <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/IOLoop/TLS.pm>`_
of Mojolicious 9.49.
"""

import Pyjo.EventEmitter
import Pyjo.IOLoop
import Pyjo.Reactor

import os
import ssl
import sys
import weakref

from types import TracebackType
from typing import Any, Self, cast


TLS = not os.environ.get('PYJO_NO_TLS')

# The built-in certificate for localhost and 127.0.0.1, which certs/ca.crt signs
CERT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certs', 'server.crt')
KEY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certs', 'server.key')


class Pyjo_IOLoop_TLS(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.IOLoop.TLS` inherits all methods from :mod:`Pyjo.EventEmitter`
    and implements the following new ones.
    """

    def __init__(self, handle: Any = None) -> None:
        """::

            tls = Pyjo.IOLoop.TLS.new(handle)

        Construct a new :mod:`Pyjo.IOLoop.TLS` object.
        """
        super().__init__()
        self._handle: Any = handle
        self._reactor: weakref.ref[Pyjo.Reactor.object] | None = None

    def __del__(self) -> None:
        # Module globals may be gone at the end of the interpreter
        try:
            if not sys.is_finalizing() and getattr(self, '_handle', None) is not None:
                reactor = self._reactor() if self._reactor is not None else None
                Pyjo.Reactor._finalize(self._release, reactor)  # pyright: ignore[reportPrivateUsage]
        except Exception:
            pass

    # Not in Mojolicious: a context manager, which closes the connection of the handshake where the block ends, as PyPy
    # frees the object only when its garbage collector runs
    def __enter__(self) -> Self:
        return self

    def __exit__(
        self, type: type[BaseException] | None, value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        self.close()

    def _release(self) -> None:
        self._cleanup()
        self._close()

    @property
    def reactor(self) -> Pyjo.Reactor.object:
        """::

            reactor = tls.reactor
            tls.reactor = Pyjo.Reactor.Poll.new()

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
    def can_tls(cls) -> bool:
        """::

            boolean = Pyjo.IOLoop.TLS.object.can_tls()

        True if TLS support is enabled, as it is unless the ``PYJO_NO_TLS``
        environment variable is set.
        """
        return TLS

    # Not in Mojolicious: the release of the connection of the handshake, which Perl does in DESTROY, also at the end of
    # a with block
    def close(self) -> None:
        """::

            tls.close()

        Close the connection of the handshake, as the end of a ``with`` block
        does.
        """
        self._release()

    def negotiate(self, **options: Any) -> None:
        """::

            tls.negotiate(server=True)
            tls.negotiate(tls_ca='/etc/tls/ca.crt')

        Negotiate TLS.

        These options are currently available:

        address
            ::

                address='mojolicious.org'

            Name of the server, for SNI and the verification of its
            certificate on the client-side.

        server
            ::

                server=True

            Negotiate TLS from the server-side, defaults to the client-side.

        tls_ca
            ::

                tls_ca='/etc/tls/ca.crt'

            Path to TLS certificate authority file. On the server-side, a
            client certificate is then required.

        tls_cert
            ::

                tls_cert='/etc/tls/server.crt'
                tls_cert={'mojolicious.org': '/etc/tls/mojo.crt'}

            Path to the TLS cert file, defaults to a built-in test certificate
            on the server-side.

        tls_context
            ::

                tls_context=ssl.create_default_context()

            The :class:`ssl.SSLContext` to use instead of the one that the
            other options make.

        tls_hostname
            ::

                tls_hostname='mojolicious.org'
                tls_hostname=''

            Name of the server for SNI and the verification of its
            certificate on the client-side instead of ``address``, an empty
            one for no SNI.

        tls_key
            ::

                tls_key='/etc/tls/server.key'
                tls_key={'mojolicious.org': '/etc/tls/mojo.key'}

            Path to the TLS key file, defaults to a built-in test key on the
            server-side.
        """
        if not TLS:
            return self._error('TLS support is disabled')

        handle = self._handle
        server = bool(options.get('server'))
        try:
            context = _expand(options)
            # Not in Mojolicious: tls_hostname for the SSL_hostname and SSL_verifycn_name of IO::Socket::SSL
            hostname = None if server else options.get('tls_hostname', options.get('address')) or None
            handle = context.wrap_socket(
                handle, server_side=server, do_handshake_on_connect=False, server_hostname=hostname
            )
        except (OSError, ValueError) as e:
            return self._error(e)
        self._handle = handle

        # The reactor keeps the negotiation alive until it is done, as Mojo's callback refers to it
        def cb(reactor: Any, writable: bool) -> None:
            self._tls(handle)

        self.reactor.io(handle, cb)

    def _cleanup(self) -> None:
        reactor = self._reactor() if self._reactor is not None else None
        if reactor is not None and self._handle is not None:
            try:
                reactor.remove(self._handle)
            except Exception:
                pass

    # The handle that is not upgraded is closed where it is dropped, as Perl closes it with the last reference
    def _close(self) -> None:
        if (handle := self._handle) is not None:
            self._handle = None
            handle.close()

    def _error(self, err: Any) -> None:
        self._cleanup()
        self._close()
        self.emit('error', err)

    def _tls(self, handle: ssl.SSLSocket) -> None:
        # Switch between reading and writing
        try:
            handle.do_handshake()
        except ssl.SSLWantReadError:
            self.reactor.watch(handle, True, False)
            return
        except ssl.SSLWantWriteError:
            self.reactor.watch(handle, True, True)
            return
        except OSError as e:
            return self._error(e)

        self._cleanup()
        self._handle = None
        self.emit('upgrade', handle)


# The certificates or keys of names, with '' for the one of any name
def _named(value: Any) -> dict[str, str]:
    if isinstance(value, dict):
        return {str(k): str(v) for k, v in cast(dict[Any, Any], value).items()}
    return {'': value} if value else {}


# Left out from Mojolicious: _expand makes the options of IO::Socket::SSL, here an ssl.SSLContext
def _expand(options: dict[str, Any]) -> ssl.SSLContext:
    # Unlike Mojolicious: tls_options of IO::Socket::SSL is tls_context, an ssl.SSLContext
    if (context := options.get('tls_context')) is not None:
        return context

    ca = options.get('tls_ca')
    if ca is not None and not os.path.isfile(ca):
        ca = None
    cert, key = options.get('tls_cert'), options.get('tls_key')

    if options.get('server'):

        def server_context(cert: str, key: str) -> ssl.SSLContext:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            # Not in Mojolicious: no session tickets of TLS 1.3 on Windows, which the server sends after the handshake
            # of the client, where a write to a client that has closed already aborts the handshake of the server
            if sys.platform == 'win32':
                context.num_tickets = 0
            context.load_cert_chain(cert, key)
            if ca is not None:
                context.load_verify_locations(ca)
                context.verify_mode = ssl.CERT_REQUIRED
            return context

        certs, keys = _named(cert), _named(key)
        context = server_context(certs.pop('', None) or CERT, keys.pop('', None) or KEY)

        # Not in Mojolicious: a certificate for each name, which IO::Socket::SSL chooses by SNI
        if len(certs):
            contexts = {name: server_context(c, keys.get(name) or KEY) for name, c in certs.items()}

            def sni(socket: ssl.SSLObject | ssl.SSLSocket, name: str | None, context: ssl.SSLContext) -> None:
                if name is not None and (named := contexts.get(name)) is not None:
                    socket.context = named

            context.sni_callback = sni
        return context

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    if ca is not None:
        context.load_verify_locations(ca)
    else:
        context.load_default_certs()
    if cert:
        context.load_cert_chain(cert, key)
    if not options.get('tls_hostname', options.get('address')):
        context.check_hostname = False
    return context


# Not in Mojolicious: the context that negotiate makes of the options, for a server that changes it, as
# Mojo::Server::Daemon adds tls_options of IO::Socket::SSL to the other options
def context(**options: Any) -> ssl.SSLContext:
    """::

        context = context(server=True, tls_cert='/etc/tls/server.crt', tls_key='/etc/tls/server.key')

    The :class:`ssl.SSLContext` that :meth:`Pyjo_IOLoop_TLS.negotiate` makes
    of its options. A context of a server sends no session tickets of TLS 1.3
    on Windows, where a client that closes the connection right after its
    handshake would make the handshake of the server fail.
    """
    return _expand(options)


new = Pyjo_IOLoop_TLS.new
object = Pyjo_IOLoop_TLS
