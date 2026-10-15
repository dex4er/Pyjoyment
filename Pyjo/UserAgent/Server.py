"""
Pyjo.UserAgent.Server - Application server
==========================================
::

    import Pyjo.UserAgent.Server

    server = Pyjo.UserAgent.Server.new()
    print(server.url())

:mod:`Pyjo.UserAgent.Server` is an embedded web server based on
:mod:`Pyjo.Server.Daemon` that processes requests for :mod:`Pyjo.UserAgent`.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::UserAgent::Server <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/UserAgent/Server.pm>`_
of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.Base
import Pyjo.IOLoop
import Pyjo.Server
import Pyjo.Server.Daemon
import Pyjo.URL

import sys
import weakref

from typing import Any, cast


# The application of all servers that have none of their own
_singleton: Pyjo.Server.Application | None = None


class Pyjo_UserAgent_Server(Pyjo.Base.object):
    """
    :mod:`Pyjo.UserAgent.Server` inherits all methods from :mod:`Pyjo.Base`
    and implements the following new ones.
    """

    def __init__(self, *, app: Pyjo.Server.Application | None = None, ioloop: Pyjo.IOLoop.object | None = None) -> None:
        """::

            server = Pyjo.UserAgent.Server.new()
            server = Pyjo.UserAgent.Server.new(ioloop=Pyjo.IOLoop.new())

        Construct a new :mod:`Pyjo.UserAgent.Server` object.
        """
        self._app = app

        self.ioloop: Pyjo.IOLoop.object = ioloop if ioloop is not None else Pyjo.IOLoop.object.singleton()
        """::

            loop = server.ioloop
            server.ioloop = Pyjo.IOLoop.new()

        Event loop object to use for I/O operations, defaults to the global
        :mod:`Pyjo.IOLoop` singleton.
        """

        self._proto = 'http'
        self._port: int | None = None
        self._nb_port: int | None = None
        self._server: Pyjo.Server.Daemon.object | None = None
        self._nb_server: Pyjo.Server.Daemon.object | None = None
        self._previous: set[int] = set()

    def __del__(self) -> None:
        if sys.is_finalizing():
            return
        try:
            self.restart()
        except Exception:
            pass

    @property
    def app(self) -> Pyjo.Server.Application | None:
        """::

            app = server.app
            server.app = Pyjoyment.new()

        Application this server handles, instance specific applications
        override the global default, which :func:`app` of the module gives.
        """
        return self._app or _singleton

    @app.setter
    def app(self, value: Pyjo.Server.Application) -> None:
        self._app = value

    def nb_url(self, proto: str | None = None) -> Pyjo.URL.object:
        """::

            url = server.nb_url()
            url = server.nb_url('http')
            url = server.nb_url('https')

        Get absolute :mod:`Pyjo.URL` object for server processing non-blocking
        requests with :attr:`app` and switch protocol if necessary.
        """
        return self._url(True, proto)

    def restart(self) -> None:
        """::

            server.restart()

        Restart server with new port.
        """
        self._previous = {port for port in (self._port, self._nb_port) if port is not None}
        self._nb_port = self._port = None
        self._close()

    def _close(self) -> None:
        _close_servers(self._server, self._nb_server)
        self._nb_server = self._server = None

    # Unlike Mojolicious: a server on a new port gets another one than before the restart, as the system may give the
    # port that the restart freed again, and Mojo takes what it gives
    def _listen(self, proto: str, port: int | None, ioloop: Pyjo.IOLoop.object | None) -> Pyjo.Server.Daemon.object:
        while True:
            server = (
                Pyjo.Server.Daemon.new(silent=True)
                if ioloop is None
                else Pyjo.Server.Daemon.new(ioloop=ioloop, silent=True)
            )
            if (app := self.app) is not None:
                server.app = _weak(app)
            server.listen = [f'{proto}://127.0.0.1' + (f':{port}' if port else '')]
            server.start()
            if port or server.ports()[0] not in self._previous:
                return server
            _close_servers(server)

    def url(self, proto: str | None = None) -> Pyjo.URL.object:
        """::

            url = server.url()
            url = server.url('http')
            url = server.url('https')

        Get absolute :mod:`Pyjo.URL` object for server processing blocking
        requests with :attr:`app` and switch protocol if necessary.
        """
        return self._url(False, proto)

    def _url(self, nb: bool, proto: str | None) -> Pyjo.URL.object:
        if self._server is None or proto:
            proto = self._proto = proto or 'http'
            self._close()

            # Blocking
            server = self._server = self._listen(proto, self._port, self.ioloop)
            self._port = server.ports()[0]

            # Non-blocking
            server = self._nb_server = self._listen(proto, self._nb_port, None)
            self._nb_port = server.ports()[0]

        port = self._nb_port if nb else self._port
        return Pyjo.URL.new(f'{self._proto}://127.0.0.1:{port}/')


# Not in Mojolicious: the servers are closed where they are dropped, as Perl closes them when it frees them, and PyPy frees
# them only when its garbage collector runs, after a new server has taken over the port
def _close_servers(*servers: Pyjo.Server.Daemon.object | None) -> None:
    for server in servers:
        if server is not None:
            server.__exit__(None, None, None)


def app(value: Pyjo.Server.Application | None = None) -> Pyjo.Server.Application | None:
    """::

        app = Pyjo.UserAgent.Server.app()
        Pyjo.UserAgent.Server.app(Pyjoyment.new())

    The global default application of the servers, as Mojo calls ``app`` on
    the class. ::

        # Change application behavior
        Pyjo.UserAgent.Server.app().log.level = 'fatal'
    """
    global _singleton
    if value is not None:
        _singleton = value
    return _singleton


# A server refers to the application weakly, as Mojo weakens it
def _weak(app: Any) -> Any:
    if isinstance(app, weakref.ProxyType):
        return cast(Any, app)
    return cast(Any, weakref.proxy(app))


new = Pyjo_UserAgent_Server.new
object = Pyjo_UserAgent_Server
