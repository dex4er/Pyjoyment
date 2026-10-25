"""
Pyjo.Server.Stdio - Standard input and output server
=====================================================
::

    from Pyjo.Server.Stdio import Stdio

    server = Stdio()


    # Lines of the standard input in capitals
    @server.on('stream')
    def stream(server, stream):
        stream.on('read', lambda stream, chunk: stream.write(chunk.upper()))


    server.run()

    # Or import the module, as in Google Python Style Guide

    import Pyjo.Server.Stdio

    server = Pyjo.Server.Stdio.new()


    # Lines of the standard input in capitals
    @server.on('stream')
    def stream(server, stream):
        stream.on('read', lambda stream, chunk: stream.write(chunk.upper()))


    server.run()

:mod:`Pyjo.Server.Stdio` serves a protocol on the standard input and output
of the process, as the transport stdio of MCP or LSP, or a protocol of lines
that inetd or systemd serves, with the stream of :mod:`Pyjo.IOLoop.Stdio`,
while the log goes to the standard error. It serves no HTTP: it builds no
transaction, and the application gives the protocol with a subscriber of the
event ``stream``, which a plugin or the application subscribes in the hook
``before_server_start``, so that the same application serves its routes with
another server. ::

    import Pyjo.IOLoop.Messages
    import Pyjo.Server.Stdio

    # The methods of JSON-RPC, one message on each line
    @app.hook('before_server_start')
    def stdio(server, app):
        if isinstance(server, Pyjo.Server.Stdio.object):
            server.on('stream', lambda server, stream: rpc.serve(Pyjo.IOLoop.Messages.new(stream)))

The server takes the standard input and output before it emits the hook,
so that what the application and its plugins print while they start goes to
the standard error, but not what a script prints while it is loaded, before
its command runs.

The server runs the event loop until the stream closes, which it does once
the standard input has ended and the rest is written, or which a subscriber
of the event ``end`` of the stream does, as
:meth:`~Pyjo.JSON.RPC.Pyjo_JSON_RPC.serve` does once the requests in
progress have their responses.

The reactor watches pipes on POSIX systems, not on Windows, where the server
raises an exception, as the stream does.

Signals
-------

The :mod:`Pyjo.Server.Stdio` process can be controlled at runtime with the
following signals.

INT, TERM
~~~~~~~~~

Shut down server gracefully: end the standard input, as at its end, and wait
for the stream to be closed. A second ``INT``, as of Ctrl-C pressed twice,
shuts it down immediately, a second ``TERM`` does nothing.

QUIT
~~~~

Shut down server immediately.

HUP
~~~

Ignored, as there is nothing to reload.

Events
------

:mod:`Pyjo.Server.Stdio` inherits all events from :mod:`Pyjo.Server` and can
emit the following new ones.

stream
~~~~~~
::

    server.on('stream', lambda server, stream: ...)

Emitted when the :mod:`Pyjo.IOLoop.Stdio` stream of the standard input and
output is ready to be served. ::

    @server.on('stream')
    def stream(server, stream):
        stream.on('end', lambda stream: stream.close_gracefully())

See also
--------

:mod:`Pyjoyment.Command.stdio`, :mod:`Pyjo.IOLoop.Stdio`,
:mod:`Pyjo.IOLoop.Messages`, :mod:`Pyjo.Server.Daemon`, :mod:`Pyjoyment`,
https://mojolicious.org.

It has no counterpart in Mojolicious.

Classes
-------
"""

import Pyjo.Exception
import Pyjo.IOLoop
import Pyjo.IOLoop.Stdio
import Pyjo.Server

import signal
import sys
import threading

from typing import Any


class Pyjo_Server_Stdio(Pyjo.Server.object):
    """
    :mod:`Pyjo.Server.Stdio` inherits all methods from :mod:`Pyjo.Server` and
    implements the following new ones.
    """

    def __init__(self, *, ioloop: Pyjo.IOLoop.object | None = None, **kwargs: Any) -> None:
        """::

            server = Pyjo.Server.Stdio.new()

        Construct a new :mod:`Pyjo.Server.Stdio` object.
        """
        super().__init__(**kwargs)

        self.ioloop: Pyjo.IOLoop.object = ioloop if ioloop is not None else Pyjo.IOLoop.object.singleton()
        """::

            loop = server.ioloop
            server.ioloop = Pyjo.IOLoop.new()

        Event loop object to use for I/O operations, defaults to the global
        :mod:`Pyjo.IOLoop` singleton.
        """

    def run(self) -> None:
        """::

            server.run()

        Run server until the stream of the standard input and output closes,
        and wait for the signals ``INT``, ``TERM`` and ``QUIT``.
        """
        # The standard input and output are taken before the application starts, so that what it prints then goes to
        # the standard error too
        loop = self.ioloop
        stdio = Pyjo.IOLoop.Stdio.new()
        handlers: dict[signal.Signals, Any] = {}
        interval = None
        graceful = immediate = False

        # INT and TERM end the standard input, as at its end, and QUIT stops the event loop immediately, as a second INT
        # does, as of Ctrl-C pressed twice; the end is left to the next tick, as a handler of Python runs in the middle of
        # what the event loop does
        def stop(signum: int, frame: Any) -> None:
            nonlocal graceful, immediate
            if signum == _QUIT or (signum == signal.SIGINT and graceful):
                immediate = True
                loop.stop()
            elif not graceful:
                graceful = True
                loop.next_tick(lambda loop: stdio.end())

        def close(stdio: Any) -> None:
            loop.stop()

        try:
            self.app.server(self)
            if not self.has_subscribers('stream'):
                raise Pyjo.Exception.new(
                    'Nothing serves the standard input and output, the event "stream" has no subscriber'
                )

            # Make sure the event loop can be stopped in regular intervals
            interval = loop.recurring(1, lambda loop: None)

            # A thread other than the main one cannot handle signals
            if threading.current_thread() is threading.main_thread():
                for name in (signal.SIGINT, signal.SIGTERM, _QUIT):
                    handlers[name] = signal.signal(name, stop)
                handlers[signal.SIGHUP] = signal.signal(signal.SIGHUP, signal.SIG_IGN)

            stdio.on('close', close)
            loop.stream(stdio)
            self.emit('stream', stdio)
            if stdio.handle is not None:
                loop.start()

            # The end of the server, unless it has stopped immediately
            if not immediate:
                self._server_stopped()
        finally:
            stdio.close()
            for name, handler in handlers.items():
                signal.signal(name, handler)
            if interval is not None:
                loop.remove(interval)


# Windows has no QUIT, but no stream of the standard input and output either
_QUIT = signal.SIGBREAK if sys.platform == 'win32' else signal.SIGQUIT


new = Pyjo_Server_Stdio.new
object = Pyjo_Server_Stdio
Stdio = Pyjo_Server_Stdio
