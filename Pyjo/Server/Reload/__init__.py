"""
Pyjo.Server.Reload - Auto-restarting development server
========================================================
::

    import Pyjo.Server.Reload

    reload = Pyjo.Server.Reload.new()
    reload.run('/home/sri/myapp.py')

:mod:`Pyjo.Server.Reload` is a full featured, self-restart capable
non-blocking I/O HTTP and WebSocket server, built around the very well tested
and reliable :mod:`Pyjo.Server.Daemon`, with IPv6, TLS, SNI, UNIX domain
socket, Comet (long polling), keep-alive and multiple event loop support.
Note that the server uses signals for process management, so you should avoid
modifying signal handlers in your applications.

To start applications with it you can use the ``pyjo-reload`` script, or
``python -m Pyjo.Server.Reload``. ::

    $ pyjo-reload ./myapp.py
    Web application available at http://127.0.0.1:3000

The server restarts the application whenever a file that it watches changes,
in a fork of itself, made with :func:`os.fork`, so it runs where
:func:`os.fork` exists, not on Windows. Name resolution in a thread, SOCKS5
and TLS support can be disabled with the ``PYJO_NO_NNR``, ``PYJO_NO_SOCKS``
and ``PYJO_NO_TLS`` environment variables.

Signals
-------

The :mod:`Pyjo.Server.Reload` process can be controlled at runtime with the
following signals.

INT, TERM
~~~~~~~~~

Shut down server immediately.

pyjo-reload
-----------
::

    Usage: pyjo-reload [OPTIONS] [APPLICATION]

      pyjo-reload ./myapp.py
      pyjo-reload -m production -l https://*:443 -l http://[::]:3000 ./myapp.py
      pyjo-reload -l 'https://*:443?cert=./server.crt&key=./server.key' ./myapp.py
      pyjo-reload -w /usr/local/lib -w public -w myapp.conf ./myapp.py

    Options:
      -b, --backend <name>           Reload backend to use for reloading,
                                     defaults to "Poll"
      -h, --help                     Show this message
      -l, --listen <location>        One or more locations you want to listen
                                     on, defaults to the value of PYJO_LISTEN,
                                     the port of PORT or "http://*:3000"
          --log-format <name>        Format of log messages, "text" or
                                     "json", defaults to the value of
                                     PYJO_LOG_FORMAT or "text"
      -m, --mode <name>              Operating mode for your application,
                                     defaults to the value of PYJO_MODE or
                                     "development"
      -v, --verbose                  Print details about what files changed to
                                     sys.stdout
      -w, --watch <directory/file>   One or more directories and files to watch
                                     for changes, defaults to the application
                                     script as well as the "lib" and
                                     "templates" directories in the current
                                     working directory

Start :mod:`Pyjoyment` applications with the :mod:`Pyjo.Server.Reload` web
server.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Server::Morbo <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Server/Morbo.pm>`_
and `script/morbo <https://github.com/mojolicious/mojo/blob/v9.49/script/morbo>`_ of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.Base
import Pyjo.Exception
import Pyjo.GetOpt
import Pyjo.Server.Daemon

from Pyjo.Loader import load_class
from Pyjo.Util import die, extract_usage, getopt

import os
import signal
import sys
import traceback

from collections.abc import Sequence
from pkgutil import extend_path
from typing import TYPE_CHECKING, Any, NoReturn


if TYPE_CHECKING:
    import Pyjo.Server.Reload.Backend


# Not in Mojolicious: a namespace that other distributions can add to, as Pyjo.Server.Reload.Backend is one
__path__ = extend_path(__path__, __name__)


# Renamed from Mojolicious: Mojo::Server::Morbo, as the names of Futurama are not ours
class Pyjo_Server_Reload(Pyjo.Base.object):
    """
    :mod:`Pyjo.Server.Reload` inherits all methods from :mod:`Pyjo.Base` and
    implements the following new ones.
    """

    def __init__(
        self,
        *,
        backend: 'Pyjo.Server.Reload.Backend.object | None' = None,
        daemon: Pyjo.Server.Daemon.object | None = None,
        silent: bool = True,
    ) -> None:
        """::

            reload = Pyjo.Server.Reload.new()
            reload = Pyjo.Server.Reload.new(silent=False)

        Construct a new :mod:`Pyjo.Server.Reload` object.
        """
        super().__init__()

        self.silent = silent
        """::

            boolean = reload.silent
            reload.silent = False

        Disable console messages, defaults to a true value.
        """

        self._backend = backend
        self._daemon = daemon
        self._finished = False
        self._modified = False
        self._worker: int | None = None

    @property
    def backend(self) -> 'Pyjo.Server.Reload.Backend.object':
        """::

            backend = reload.backend
            reload.backend = Pyjo.Server.Reload.Backend.Poll.new()

        Backend, usually a :mod:`Pyjo.Server.Reload.Backend.Poll` object, or
        ``Pyjo.Server.Reload.Backend.<Name>`` of the ``PYJO_RELOAD_BACKEND``
        environment variable.
        """
        if self._backend is None:
            name = f'Pyjo.Server.Reload.Backend.{os.environ.get("PYJO_RELOAD_BACKEND") or "Poll"}'
            if e := load_class(name):
                if isinstance(e, BaseException):
                    raise e
                raise Pyjo.Exception.new(f'Can\'t find Reload backend class "{name}" in sys.path. ({sys.path})\n')
            self._backend = sys.modules[name].new()
        return self._backend

    @backend.setter
    def backend(self, value: 'Pyjo.Server.Reload.Backend.object') -> None:
        self._backend = value

    @property
    def daemon(self) -> Pyjo.Server.Daemon.object:
        """::

            daemon = reload.daemon
            reload.daemon = Pyjo.Server.Daemon.new()

        :mod:`Pyjo.Server.Daemon` object this server manages.
        """
        if self._daemon is None:
            self._daemon = Pyjo.Server.Daemon.new()
        return self._daemon

    @daemon.setter
    def daemon(self, value: Pyjo.Server.Daemon.object) -> None:
        self._daemon = value

    def run(self, app: str) -> NoReturn:
        """::

            reload.run('myapp.py')

        Run server for application and wait for the signals.
        """

        # Clean manager environment
        def stop(signum: int, frame: Any) -> None:
            self._finished = True
            # Unlike Mojolicious: QUIT stops the worker immediately, as TERM stops Pyjo.Server.Daemon gracefully
            if self._worker:
                _kill(signal.SIGQUIT, self._worker)

        # Not in Mojolicious: local %SIG, the handlers of the signals are set back at the end
        handlers = {name: signal.signal(name, stop) for name in (signal.SIGINT, signal.SIGTERM)}
        try:
            self.backend.watch.insert(0, app)
            sys.argv[0] = app
            self._modified = True

            # Prepare and cache listen sockets for smooth restarting
            self.daemon.start().stop()

            while not (self._finished and not self._worker):
                self._manage()
        finally:
            for name, handler in handlers.items():
                signal.signal(name, handler)
        sys.exit(0)

    def _manage(self) -> None:
        if files := self.backend.modified_files():
            if not self.silent:
                print(
                    f'File "{files[0]}" changed, restarting.'
                    if len(files) == 1
                    else f'{len(files)} files changed, restarting.'
                )
            # Unlike Mojolicious: QUIT stops the worker immediately, as TERM stops Pyjo.Server.Daemon gracefully
            if self._worker:
                _kill(signal.SIGQUIT, self._worker)
            self._modified = True

        if pid := self._worker:
            try:
                if os.waitpid(pid, os.WNOHANG)[0] == pid:
                    self._worker = None
            except ChildProcessError:
                self._worker = None

        # Unlike Mojolicious: no worker once the server is finished, where Mojo spawns one that nothing stops when INT or
        # TERM comes before the first one
        if not self._worker and self._modified and not self._finished:
            self._modified = False
            self._spawn()

    def _spawn(self) -> None:
        # Manager
        manager = os.getpid()
        # Not in Mojolicious: the buffers of the standard streams are written before, so that the worker does not write
        # them again
        _flush()
        try:
            pid = self._worker = os.fork()
        except OSError as e:
            raise OSError(e.errno, f"Can't fork: {e.strerror}") from e
        if pid:
            return

        # Worker
        code = 0
        try:
            daemon = self.daemon
            daemon.load_app(self.backend.watch[0]).server(daemon)
            daemon.ioloop.recurring(1, lambda loop: None if _kill(0, manager) else loop.stop())
            daemon.run()

        # Not in Mojolicious: sys.exit() is the exit of the worker, as exit is in Perl, and os._exit leaves what the
        # manager does at its end
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 0 if e.code is None else 1
        except BaseException:
            traceback.print_exc()
            code = 255
        _flush()
        os._exit(code)


# Renamed from Mojolicious: script/morbo, the command line interface, a function of the module, whose usage is the
# section pyjo-reload of its docstring
def main(argv: Sequence[str] | None = None) -> NoReturn:
    """::

        main(['-l', 'http://*:8080', 'myapp.py'])

    The command line interface of ``pyjo-reload``: parse the options and run
    the server for the application.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    listen: list[str] = []
    watch: list[str] = []
    opts = getopt(
        args,
        {
            'b|backend=s': Pyjo.GetOpt.env('PYJO_RELOAD_BACKEND'),
            'h|help': None,
            'l|listen=s': listen,
            # Not in Mojolicious: the format of the log messages of Pyjo.Log, as the option of the commands
            'log-format=s': Pyjo.GetOpt.env('PYJO_LOG_FORMAT'),
            'm|mode=s': Pyjo.GetOpt.env('PYJO_MODE'),
            'v|verbose': None,
            'w|watch=s': watch,
        },
    )

    if not opts or opts.help or not args:
        # The usage without its last newline, as SystemExit writes the message with one
        die(extract_usage(section='pyjo-reload').rstrip('\n'))
    reload = Pyjo_Server_Reload.new(silent=not opts.verbose)
    if listen:
        reload.daemon.listen = listen
    if watch:
        reload.backend.watch = watch
    reload.run(args[0])


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


new = Pyjo_Server_Reload.new
object = Pyjo_Server_Reload
