"""
Pyjo.Server - HTTP/WebSocket server base class
==============================================
::

    import Pyjo.Server

    class Pyjo_Server_MyServer(Pyjo.Server.object):
        def run(self):
            # Get a transaction
            tx = self.build_tx()

            # Emit "request" event
            self.emit('request', tx)

:mod:`Pyjo.Server` is an abstract base class for HTTP/WebSocket servers and
server interfaces, like :mod:`Pyjo.Server.ASGI`, :mod:`Pyjo.Server.CGI`,
:mod:`Pyjo.Server.Daemon` and :mod:`Pyjo.Server.WSGI`.

A server of another distribution is a module in the namespace
``Pyjo.Server``, which :func:`pkgutil.extend_path` keeps open, as for
:mod:`Pyjo.Reactor`.

Events
------

:mod:`Pyjo.Server` inherits all events from :mod:`Pyjo.EventEmitter` and can
emit the following new ones.

request
~~~~~~~
::

    server.on('request', lambda server, tx: ...)

Emitted when a request is ready and needs to be handled. ::

    @server.on('request')
    def request(server, tx):
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = b'Hello World!'
        tx.resume()

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Server <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Server.pm>`_
of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.EventEmitter
import Pyjo.Exception
import Pyjo.File
import Pyjo.Log
import Pyjo.Transaction
import Pyjo.Transaction.HTTP

from Pyjo.Loader import load_class
from Pyjo.String.Unicode import split
from Pyjo.Util import md5_sum

import builtins
import importlib
import importlib.machinery
import importlib.util
import os
import sys

from pkgutil import extend_path
from typing import Any, NoReturn, Protocol


type Anything = builtins.object


class Application(Protocol):
    """
    What a server needs from the application it handles.
    """

    @property
    def log(self) -> Pyjo.Log.object: ...

    def build_tx(self) -> Pyjo.Transaction.HTTP.object: ...

    def handler(self, tx: Pyjo.Transaction.HTTP.object) -> Anything: ...

    def server(self, server: 'Pyjo_Server') -> Anything: ...


# Not in Mojolicious: a namespace that other distributions can add servers to
__path__ = extend_path(__path__, __name__)

# Renamed from Mojolicious: @ARGS_OVERRIDE, a variable of the module that changes
args_override: dict[str, Any] = {}
"""
The arguments of :meth:`~Pyjo_Server.load_app` for the constructor of the
application that the script builds.
"""

# Not in Mojolicious: the application that the script of load_app starts, where Mojo takes the value of the script
loaded_app: Application | None = None
"""
The application that the script of :meth:`~Pyjo_Server.load_app` starts:
its ``start`` keeps itself here instead of running a command, when the
environment variable ``PYJO_APP_LOADER`` is set.
"""


class Pyjo_Server(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.Server` inherits all methods from :mod:`Pyjo.EventEmitter` and
    implements the following new ones.
    """

    def __init__(
        self,
        *,
        app: Application | None = None,
        reverse_proxy: bool | None = None,
        trusted_proxies: list[str] | None = None,
    ) -> None:
        """::

            server = Pyjo.Server.new()
            server = Pyjo.Server.new(reverse_proxy=True)

        Construct a new :mod:`Pyjo.Server` object and subscribe to
        ``request`` event with default request handling.
        """
        super().__init__()

        self._app = app

        self._trusted_proxies: list[str] | None = trusted_proxies
        self._reverse_proxy: bool | None = reverse_proxy

        self.on('request', _request)

    @property
    def trusted_proxies(self) -> list[str]:
        """::

            proxies = server.trusted_proxies
            server.trusted_proxies = ['10.0.0.0/8', '127.0.0.1', '172.16.0.0/12', '192.168.0.0/16', 'fc00::/7']

        This server expects requests from trusted reverse proxies, defaults to
        the value of the ``PYJO_TRUSTED_PROXIES`` environment variable split
        on commas with optional whitespace. These proxies should be addresses
        or networks in CIDR form.
        """
        if self._trusted_proxies is None:
            self._trusted_proxies = [
                proxy or '' for proxy in split(r'\s*,\s*', os.environ.get('PYJO_TRUSTED_PROXIES') or '')
            ]
        return self._trusted_proxies

    @trusted_proxies.setter
    def trusted_proxies(self, value: list[str]) -> None:
        self._trusted_proxies = value

    @property
    def reverse_proxy(self) -> bool:
        """::

            boolean = server.reverse_proxy
            server.reverse_proxy = boolean

        This server operates behind a reverse proxy, defaults to the value of
        the ``PYJO_REVERSE_PROXY`` environment variable or true if
        :attr:`trusted_proxies` is not empty.
        """
        if self._reverse_proxy is None:
            self._reverse_proxy = bool(os.environ.get('PYJO_REVERSE_PROXY')) or bool(self.trusted_proxies)
        return self._reverse_proxy

    @reverse_proxy.setter
    def reverse_proxy(self, value: bool) -> None:
        self._reverse_proxy = value

    @property
    def app(self) -> Application:
        """::

            app = server.app
            server.app = MyApp.new()

        Application this server handles, defaults to a :mod:`Pyjo.HelloWorld`
        object.
        """
        if self._app is None:
            return self.build_app('Pyjo.HelloWorld')
        return self._app

    @app.setter
    def app(self, value: Application) -> None:
        self._app = value

    def build_app(self, app: str | type, **kwargs: Any) -> Application:
        """::

            app = server.build_app('MyApp')
            app = server.build_app('MyApp', log=Pyjo.Log.new())
            app = server.build_app(MyApp)

        Build application from class and assign it to :attr:`app`. The class
        is a dotted name of a module with a ``new`` function, as the modules
        of Pyjoyment have, or of a class in a module, or the class itself.
        """
        exe = os.environ.pop('PYJO_EXE', None)
        try:
            # Not in Mojolicious: a class of Python
            if isinstance(app, type):
                self.app = app(**kwargs)
                return self.app
            if not (e := load_class(app)):
                self.app = sys.modules[app].new(**kwargs)
                return self.app
            if isinstance(e, Exception):
                raise e
            # Not in Mojolicious: a class in a module, as the longest prefix of the name that is a module
            if (cls := _class(app)) is not None:
                self.app = cls(**kwargs)
                return self.app
            raise Pyjo.Exception.new(f'Can\'t find application class "{app}" in sys.path. ({" ".join(sys.path)})\n')
        finally:
            if exe is not None:
                os.environ['PYJO_EXE'] = exe

    def build_tx(self) -> Pyjo.Transaction.HTTP.object:
        """::

            tx = server.build_tx()

        Let application build a transaction.
        """
        tx = self.app.build_tx()
        tx.req.trusted_proxies.extend(self.trusted_proxies)
        if self.reverse_proxy:
            tx.req.reverse_proxy = True
        return tx

    def daemonize(self) -> None:
        """::

            server.daemonize()

        Daemonize server process.
        """
        # Fork and kill parent
        try:
            pid = os.fork()
        except OSError as e:
            _croak(e, "Can't fork")
        if pid:
            os._exit(0)
        try:
            os.setsid()
        except OSError as e:
            _croak(e, "Can't start a new session")

        # Close filehandles
        null = os.open(os.devnull, os.O_RDWR)
        for handle in (sys.stdin, sys.stdout, sys.stderr):
            os.dup2(null, handle.fileno())
        os.close(null)

    def load_app(self, path: str | os.PathLike[str], **kwargs: Any) -> Application:
        """::

            app = server.load_app('/home/sri/myapp.py')
            app = server.load_app('/home/sri/myapp.py', log=Pyjo.Log.new())

        Load application from script and assign it to :attr:`app`. The
        script starts its application, as ``MyApp.new().start()``, and the
        ``start`` method keeps it in :data:`loaded_app` instead of running a
        command, as the environment variable ``PYJO_APP_LOADER`` is set. ::

            print(Pyjo.Server.new().load_app('./myapp.py').log.level)
        """
        global args_override, loaded_app

        # Clean environment
        path = Pyjo.File.path(path).to_abs().to_str()
        argv = sys.argv[:1]
        loader, exe = os.environ.get('PYJO_APP_LOADER'), os.environ.pop('PYJO_EXE', None)
        args, loaded = args_override, loaded_app
        # Left out from Mojolicious: FindBin, which Python does not have
        try:
            sys.argv[:1] = [path]
            os.environ['PYJO_APP_LOADER'] = '1'
            args_override, loaded_app = kwargs, None

            # Try to load application from script into sandbox
            try:
                _run(path, f'Pyjo.Server.Sandbox.{md5_sum(path.encode())}')
            except Exception as e:
                raise Pyjo.Exception.new(f'Can\'t load application from file "{path}": {e}') from e
            if (app := loaded_app) is None or not callable(getattr(app, 'handler', None)):
                raise Pyjo.Exception.new(f'File "{path}" did not return an application object.\n')
            self.app = app
        finally:
            sys.argv[:1] = argv
            if loader is None:
                os.environ.pop('PYJO_APP_LOADER', None)
            else:
                os.environ['PYJO_APP_LOADER'] = loader
            if exe is not None:
                os.environ['PYJO_EXE'] = exe
            args_override, loaded_app = args, loaded

        return self.app

    def run(self) -> Anything:
        """::

            server.run()

        Run server. Meant to be overloaded in a subclass.
        """
        raise NotImplementedError('Method "run" not implemented by subclass')


# Not in Mojolicious: the script as a module of its own with a loader, where runpy.run_path gives it none, so that
# linecache finds its source for a stack trace, as asyncio in debug mode makes them, without the DeprecationWarning of
# Python 3.15; a script without the suffix .py runs too, and no bytecode is written next to it
def _run(path: str, name: str) -> None:
    loader = importlib.machinery.SourceFileLoader(name, path)
    module = importlib.util.module_from_spec(importlib.machinery.ModuleSpec(name, loader, origin=path))
    module.__file__ = path
    exec(compile(loader.get_source(name) or '', path, 'exec'), module.__dict__)


def _request(server: Pyjo_Server, tx: Pyjo.Transaction.HTTP.object) -> None:
    server.app.handler(tx)


def _class(name: str) -> Any:
    parts = name.split('.')
    for i in range(len(parts) - 1, 0, -1):
        try:
            found: Any = importlib.import_module('.'.join(parts[:i]))
        except ImportError:
            continue
        try:
            for attr in parts[i:]:
                found = getattr(found, attr)
        except AttributeError:
            return None
        return found if isinstance(found, type) else None
    return None


def _croak(e: OSError, message: str) -> NoReturn:
    error = type(e)(f'{message}: {e.strerror}' if e.strerror else message)
    error.errno = e.errno
    raise error from e


new = Pyjo_Server.new
object = Pyjo_Server
