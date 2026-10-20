"""
Pyjo.Server.Hot - Production web server with hot deployment
============================================================
::

    from Pyjo.Server.Hot import Hot

    hot = Hot()
    hot.run('/home/sri/myapp.py')

    # Or import the module, as in Google Python Style Guide

    import Pyjo.Server.Hot

    hot = Pyjo.Server.Hot.new()
    hot.run('/home/sri/myapp.py')

:mod:`Pyjo.Server.Hot` is a full featured, UNIX optimized, pre-forking
non-blocking I/O HTTP and WebSocket server, built around the very well tested
and reliable :mod:`Pyjo.Server.Prefork`, with IPv6, TLS, SNI, UNIX domain
socket, Comet (long polling), keep-alive, multiple event loop and hot
deployment support that just works. Note that the server uses signals for
process management, so you should avoid modifying signal handlers in your
applications.

To start applications with it you can use the ``pyjo-hot`` script, or
``python -m Pyjo.Server.Hot``, which listens on port ``8080``, automatically
daemonizes the server process and defaults to ``production`` mode for
:mod:`Pyjoyment` applications. ::

    $ pyjo-hot ./myapp.py

You can run the same command again for automatic hot deployment. ::

    $ pyjo-hot ./myapp.py
    Starting hot deployment for Hot server 31841.

This second invocation will load the application again, detect the process id
file with it, and send a :ref:`HUP <hot-hup>` signal to the already running
server.

The server runs the command line of its process again, :data:`sys.orig_argv`,
for a clean start and for the new manager of a hot deployment, and the
workers are forks of the manager, made with :func:`os.fork`, so it runs where
:func:`os.fork` exists, not on Windows. Name resolution in a thread, SOCKS5
and TLS support can be disabled with the ``PYJO_NO_NNR``, ``PYJO_NO_SOCKS``
and ``PYJO_NO_TLS`` environment variables.

Manager signals
---------------

The :mod:`Pyjo.Server.Hot` manager process can be controlled at runtime with
the following signals.

INT, TERM
~~~~~~~~~

Shut down server gracefully. A second ``INT``, as of Ctrl-C pressed twice,
shuts it down immediately, a second ``TERM`` does nothing.

QUIT
~~~~

Shut down server immediately.

TTIN
~~~~

Increase worker pool by one.

TTOU
~~~~

Decrease worker pool by one.

.. _hot-hup:

HUP
~~~

Attempt zero downtime software upgrade (hot deployment) without losing any
incoming connections. ::

    Manager (old)
    |- Worker [1]
    |- Worker [2]
    |- Worker [3]
    |- Worker [4]
    +- Manager (new)
       |- Worker [1]
       |- Worker [2]
       |- Worker [3]
       +- Worker [4]

The new manager will automatically send a ``TERM`` signal to the old manager
and take over serving requests after starting up successfully.

Worker signals
--------------

:mod:`Pyjo.Server.Hot` worker processes can be controlled at runtime with the
following signals.

TERM
~~~~

Stop worker gracefully.

QUIT
~~~~

Stop worker immediately.

Settings
--------

:mod:`Pyjo.Server.Hot` can be configured with the following settings, in the
``hot`` key of the configuration of the application. ::

    app.config(hot={'listen': ['http://*:80'], 'workers': 10})

accepts
~~~~~~~
::

    'accepts': 100

Maximum number of connections a worker is allowed to accept, before stopping
gracefully and then getting replaced with a newly started worker, defaults to
the value of :attr:`Pyjo.Server.Prefork.Pyjo_Server_Prefork.accepts`. Setting
the value to ``0`` will allow workers to accept new connections indefinitely.
Note that up to half of this value can be subtracted randomly to improve load
balancing, and to make sure that not all workers restart at the same time.

backlog
~~~~~~~
::

    'backlog': 128

Listen backlog size, defaults to the value of
:attr:`Pyjo.Server.Daemon.Pyjo_Server_Daemon.backlog`.

clients
~~~~~~~
::

    'clients': 100

Maximum number of accepted connections each worker process is allowed to
handle concurrently, before stopping to accept new incoming connections,
defaults to the value of :attr:`Pyjo.IOLoop.Pyjo_IOLoop.max_connections`.
Note that high concurrency works best with applications that perform mostly
non-blocking operations, to optimize for blocking operations you can decrease
this value and increase `workers`_ instead for better performance.

graceful_timeout
~~~~~~~~~~~~~~~~
::

    'graceful_timeout': 15

Maximum amount of time in seconds stopping a worker gracefully may take
before being forced, defaults to the value of
:attr:`Pyjo.Server.Prefork.Pyjo_Server_Prefork.graceful_timeout`. Note that
this value should usually be a little larger than the maximum amount of time
you expect any one request to take.

heartbeat_interval
~~~~~~~~~~~~~~~~~~
::

    'heartbeat_interval': 3

Heartbeat interval in seconds, defaults to the value of
:attr:`Pyjo.Server.Prefork.Pyjo_Server_Prefork.heartbeat_interval`.

heartbeat_timeout
~~~~~~~~~~~~~~~~~
::

    'heartbeat_timeout': 2

Maximum amount of time in seconds before a worker without a heartbeat will be
stopped gracefully, defaults to the value of
:attr:`Pyjo.Server.Prefork.Pyjo_Server_Prefork.heartbeat_timeout`. Note that
this value should usually be a little larger than the maximum amount of time
you expect any one operation to block the event loop.

inactivity_timeout
~~~~~~~~~~~~~~~~~~
::

    'inactivity_timeout': 10

Maximum amount of time in seconds a connection with an active request can be
inactive before getting closed, defaults to the value of
:attr:`Pyjo.Server.Daemon.Pyjo_Server_Daemon.inactivity_timeout`. Setting the
value to ``0`` will allow connections to be inactive indefinitely.

keep_alive_timeout
~~~~~~~~~~~~~~~~~~
::

    'keep_alive_timeout': 10

Maximum amount of time in seconds a connection without an active request can
be inactive before getting closed, defaults to the value of
:attr:`Pyjo.Server.Daemon.Pyjo_Server_Daemon.keep_alive_timeout`. Setting the
value to ``0`` will allow connections to be inactive indefinitely.

listen
~~~~~~
::

    'listen': ['http://*:80']

List with one or more locations to listen on, defaults to
``http://*:8080``. See also
:attr:`Pyjo.Server.Daemon.Pyjo_Server_Daemon.listen` for more examples.

pid_file
~~~~~~~~
::

    'pid_file': '/var/run/hot.pid'

Full path to process id file, defaults to ``hot.pid`` in the same directory
as the application. Note that this value can only be changed after the server
has been stopped.

proxy
~~~~~
::

    'proxy': True

Activate reverse proxy support, which allows for the ``X-Forwarded-For`` and
``X-Forwarded-Proto`` headers to be picked up automatically, defaults to the
value of :attr:`Pyjo.Server.Pyjo_Server.reverse_proxy`.

requests
~~~~~~~~
::

    'requests': 50

Number of keep-alive requests per connection, defaults to the value of
:attr:`Pyjo.Server.Daemon.Pyjo_Server_Daemon.max_requests`.

spare
~~~~~
::

    'spare': 4

Temporarily spawn up to this number of additional workers if there is a need,
defaults to the value of :attr:`Pyjo.Server.Prefork.Pyjo_Server_Prefork.spare`.
This allows for new workers to be started while old ones are still shutting
down gracefully, drastically reducing the performance cost of worker
restarts.

threads
~~~~~~~
::

    'threads': True

Run the workers as threads of a :mod:`Pyjo.Server.Prethread` in the place of
the processes of :mod:`Pyjo.Server.Prefork`, as the option ``--threads`` of
``pyjo-hot`` does, which sets the ``PYJO_HOT_THREADS`` environment variable,
defaults to a false value. The server, its manager and the hot deployment are
the same.

trusted_proxies
~~~~~~~~~~~~~~~
::

    'trusted_proxies': ['10.0.0.0/8', '127.0.0.1', '172.16.0.0/12', '192.168.0.0/16', 'fc00::/7']

Trusted reverse proxies, addresses or networks in CIDR form.

upgrade_timeout
~~~~~~~~~~~~~~~
::

    'upgrade_timeout': 45

Maximum amount of time in seconds a zero downtime software upgrade may take
before getting canceled, defaults to ``180``.

workers
~~~~~~~
::

    'workers': 10

Number of worker processes, defaults to the value of
:attr:`Pyjo.Server.Prefork.Pyjo_Server_Prefork.workers`. A good rule of thumb
is two worker processes per CPU core for applications that perform mostly
non-blocking operations, blocking operations often require more and benefit
from decreasing concurrency with `clients`_ (often as low as ``1``). Note
that during zero downtime software upgrades there will be twice as many
workers active for a short amount of time.

pyjo-hot
--------
::

    Usage: pyjo-hot [OPTIONS] [APPLICATION]

      pyjo-hot ./myapp.py
      pyjo-hot -f ./myapp.py

    Options:
      -f, --foreground   Keep manager process in foreground
      -h, --help         Show this message
      -s, --stop         Stop server gracefully
      -t, --test         Test application and exit
          --threads      Run the workers as threads

Start :mod:`Pyjoyment` applications with the :mod:`Pyjo.Server.Hot` web
server.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Server::Hypnotoad <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Server/Hypnotoad.pm>`_
and `script/hypnotoad <https://github.com/mojolicious/mojo/blob/v9.49/script/hypnotoad>`_ of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.Base
import Pyjo.File
import Pyjo.GetOpt
import Pyjo.Server.Prefork
import Pyjo.Server.Prethread

from Pyjo.Util import die, extract_usage, getopt

import os
import signal
import sys
import time
import weakref

from collections.abc import Sequence
from typing import Any, NoReturn, cast


# Renamed from Mojolicious: Mojo::Server::Hypnotoad, as the names of Futurama are not ours
class Pyjo_Server_Hot(Pyjo.Base.object):
    """
    :mod:`Pyjo.Server.Hot` inherits all methods from :mod:`Pyjo.Base` and
    implements the following new ones.
    """

    def __init__(self, *, prefork: Pyjo.Server.Prefork.object | None = None, upgrade_timeout: float = 180) -> None:
        """::

            hot = Pyjo.Server.Hot.new()
            hot = Pyjo.Server.Hot.new(upgrade_timeout=15)

        Construct a new :mod:`Pyjo.Server.Hot` object.
        """
        super().__init__()

        self.upgrade_timeout = upgrade_timeout
        """::

            timeout = hot.upgrade_timeout
            hot.upgrade_timeout = 15

        Maximum amount of time in seconds a zero downtime software upgrade may
        take before getting canceled, defaults to ``180``.
        """

        self._config: dict[str, Any] = {}
        self._finished = False
        self._new: int | None = None
        self._prefork = prefork
        self._upgrade: float | None = None

    @property
    def prefork(self) -> Pyjo.Server.Prefork.object:
        """::

            prefork = hot.prefork
            hot.prefork = Pyjo.Server.Prefork.new()

        :mod:`Pyjo.Server.Prefork` object this server manages.
        """
        if self._prefork is None:
            self._prefork = Pyjo.Server.Prefork.new(listen=['http://*:8080'])
        return self._prefork

    @prefork.setter
    def prefork(self, value: Pyjo.Server.Prefork.object) -> None:
        self._prefork = value

    def configure(self, name: str) -> None:
        """::

            hot.configure('hot')

        Configure server from application settings.
        """
        # Hot settings
        prefork = self.prefork
        c: dict[str, Any] | None = self._settings().get(name)
        if c is None:
            c = {}
        if c.get('upgrade_timeout'):
            self.upgrade_timeout = c['upgrade_timeout']

        # Not in Mojolicious: the workers are threads of a Pyjo.Server.Prethread, with the application and the listen
        # locations of the server that it replaces
        if (c.get('threads') or os.environ.get('PYJO_HOT_THREADS')) and not isinstance(
            prefork, Pyjo.Server.Prethread.object
        ):
            cleanup, prefork.cleanup = prefork.cleanup, False
            prefork = self.prefork = Pyjo.Server.Prethread.new(app=prefork.app, cleanup=cleanup, listen=prefork.listen)

        # Pre-fork settings
        if c.get('proxy') is not None:
            prefork.reverse_proxy = c['proxy']
        if c.get('trusted_proxies') is not None:
            prefork.trusted_proxies = c['trusted_proxies']
        if c.get('clients'):
            prefork.max_clients = c['clients']
        if c.get('requests'):
            prefork.max_requests = c['requests']
        for setting in (
            'accepts',
            'backlog',
            'graceful_timeout',
            'heartbeat_interval',
            'heartbeat_timeout',
            'inactivity_timeout',
            'keep_alive_timeout',
            'listen',
            'pid_file',
            'spare',
            'workers',
        ):
            if c.get(setting) is not None:
                setattr(prefork, setting, c[setting])

    def run(self, app: str | os.PathLike[str]) -> None:
        """::

            hot.run('myapp.py')

        Run server for application and wait for the manager signals.
        """
        # Unlike Mojolicious: no fork at all, where Mojo has no fork emulation of Perl on Windows
        if not hasattr(os, 'fork'):
            _exit('Pyjo.Server.Hot needs os.fork.')

        # Remember executable and application for later
        # Left out from Mojolicious: HYPNOTOAD_EXE, as the command line of the process, sys.orig_argv, runs again
        os.environ['PYJO_HOT_APP'] = os.environ.get('PYJO_HOT_APP') or Pyjo.File.new(app).to_abs().to_str()
        app = sys.argv[0] = os.environ['PYJO_HOT_APP']

        # This is a production server
        os.environ['PYJO_MODE'] = os.environ.get('PYJO_MODE') or 'production'

        # Clean start (to make sure everything works)
        rev = int(os.environ.get('PYJO_HOT_REV') or 0)
        os.environ['PYJO_HOT_REV'] = str(rev + 1)
        if not rev:
            _exec()

        # Preload application and configure server
        prefork = self.prefork
        prefork.cleanup = False
        prefork.load_app(app)
        settings = self._settings().setdefault('hot', {})
        if settings.get('pid_file') is None:
            settings['pid_file'] = Pyjo.File.new(os.environ['PYJO_HOT_APP']).sibling('hot.pid').to_str()
        self.configure('hot')
        prefork = self.prefork
        ref = weakref.ref(self)

        def wait(prefork: Any) -> None:
            if (hot := ref()) is not None:
                hot._manage()

        def reap(prefork: Any, pid: int) -> None:
            if (hot := ref()) is not None:
                hot._cleanup(pid)

        def finish(prefork: Any, graceful: bool) -> None:
            if (hot := ref()) is not None:
                hot._finish()

        # Unlike Mojolicious: HUP, the signal of a reload, attempts a hot deployment, where Mojo has USR2, which is left
        # out, as the signals of the server follow the conventions of containers and not the ones of Mojo
        def reload(prefork: Any) -> None:
            if (hot := ref()) is not None:
                hot._upgrade = hot._upgrade or time.monotonic()

        prefork.on('wait', wait)
        prefork.on('reap', reap)
        prefork.on('finish', finish)
        prefork.on('reload', reload)

        # Testing
        if os.environ.get('PYJO_HOT_TEST'):
            _exit('Everything looks good!')

        # Stop running server
        if os.environ.get('PYJO_HOT_STOP'):
            self._stop()

        # Initiate hot deployment
        if not os.environ.get('PYJO_HOT_PID'):
            self._hot_deploy()

        # Daemonize as early as possible (but not for restarts)
        prefork.start()
        if not os.environ.get('PYJO_HOT_FOREGROUND') and int(os.environ['PYJO_HOT_REV']) < 3:
            prefork.daemonize()

        # Start accepting connections
        prefork.cleanup = True
        prefork.run()

    def _cleanup(self, pid: int) -> None:
        # Clean up failed upgrade
        if self._new != pid:
            return
        self.prefork.app.log.error('Zero downtime software upgrade failed')
        self._new = self._upgrade = None

    def _finish(self) -> None:
        # Unlike Mojolicious: no upgrade once the server is finished, where Mojo sets "finish" and checks "finished", so
        # that HUP during a graceful shutdown still starts a new manager
        self._finished = True
        if not (new := self._new):
            return

        prefork = self.prefork
        prefork.cleanup = False
        Pyjo.File.new(prefork.pid_file).remove()
        prefork.ensure_pid_file(new)

    def _hot_deploy(self) -> None:
        # Make sure server is running
        if not (pid := self.prefork.check_pid()):
            return

        # Start hot deployment
        # Unlike Mojolicious: HUP, where Mojo sends USR2
        _kill(signal.SIGHUP, pid)
        _exit(f'Starting hot deployment for Hot server {pid}.')

    def _manage(self) -> None:
        # Upgraded (wait for all workers to send a heartbeat)
        prefork = self.prefork
        log = prefork.app.log
        current = str(os.getpid())
        if (old := os.environ.get('PYJO_HOT_PID')) and old != current:
            if prefork.healthy != prefork.workers:
                return
            log.info(f'Upgrade successful, stopping {old}')
            # Unlike Mojolicious: TERM stops the old manager gracefully, where Mojo sends QUIT
            _kill(signal.SIGTERM, int(old))
        os.environ['PYJO_HOT_PID'] = current

        # Upgrade
        if self._upgrade and not self._finished:
            # Fresh start
            ut = self.upgrade_timeout
            if not self._new:
                log.info(f'Starting zero downtime software upgrade ({_number(ut)} seconds)')
                # Not in Mojolicious: the buffers of the standard streams are written before, so that the new manager
                # does not write them again
                _flush()
                try:
                    pid = self._new = os.fork()
                except OSError as e:
                    raise OSError(e.errno, f"Can't fork: {e.strerror}") from e
                if not pid:
                    # Not in Mojolicious: a new manager that cannot be run exits, as the exception would go on with the
                    # old manager in its fork
                    try:
                        _exec()
                    except BaseException as e:
                        print(e, file=sys.stderr)
                        _flush()
                        os._exit(255)

            # Timeout
            if self._upgrade + ut <= time.monotonic() and self._new:
                _kill(signal.SIGKILL, self._new)

    # Not in Mojolicious: the configuration of an application that has one, as the applications of Pyjoyment have, and
    # one of the server for another one
    def _settings(self) -> dict[str, Any]:
        config = getattr(self.prefork.app, 'config', None)
        return cast(dict[str, Any], config()) if callable(config) else self._config

    def _stop(self) -> None:
        if not (pid := self.prefork.check_pid()):
            _exit('Hot server not running.')
        # Unlike Mojolicious: TERM stops the server gracefully, where Mojo sends QUIT
        _kill(signal.SIGTERM, pid)
        _exit(f'Stopping Hot server {pid} gracefully.')


# Renamed from Mojolicious: script/hypnotoad, the command line interface, a function of the module, whose usage is the
# section pyjo-hot of its docstring
def main(argv: Sequence[str] | None = None) -> None:
    """::

        main(['-f', 'myapp.py'])

    The command line interface of ``pyjo-hot``: parse the options and run the
    server for the application.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    opts = getopt(
        args,
        {
            'f|foreground': Pyjo.GetOpt.env('PYJO_HOT_FOREGROUND'),
            'h|help': None,
            's|stop': Pyjo.GetOpt.env('PYJO_HOT_STOP'),
            't|test': Pyjo.GetOpt.env('PYJO_HOT_TEST'),
            # Not in Mojolicious: the workers are threads, as the setting "threads"
            'threads': Pyjo.GetOpt.env('PYJO_HOT_THREADS'),
        },
    )

    if not opts or opts.help or not (app := (args[0] if args else None) or os.environ.get('PYJO_HOT_APP')):
        # The usage without its last newline, as SystemExit writes the message with one
        die(extract_usage(section='pyjo-hot').rstrip('\n'))
    Pyjo_Server_Hot.new().run(app)


# Unlike Mojolicious: the command line of the process, sys.orig_argv, where Mojo runs $0 again and passes the arguments
# in the environment, as Python runs a module with -m and code with -c too
def _exec() -> NoReturn:
    _flush()
    try:
        os.execv(sys.executable, [sys.executable, *sys.orig_argv[1:]])
    except OSError as e:
        raise OSError(e.errno, f"Can't exec: {e.strerror}") from e


def _exit(message: str) -> NoReturn:
    print(message)
    sys.exit(0)


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


new = Pyjo_Server_Hot.new
object = Pyjo_Server_Hot
Hot = Pyjo_Server_Hot
