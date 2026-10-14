"""
Pyjo.Server.Daemon - Non-blocking I/O HTTP and WebSocket server
===============================================================
::

    import Pyjo.Server.Daemon
    from Pyjo.Util import b

    with Pyjo.Server.Daemon.new(listen=['http://*:8080']) as daemon:
        daemon.unsubscribe('request')

        @daemon.on
        def request(daemon, tx):
            # Request
            method = tx.req.method
            path = tx.req.url.path

            # Response
            tx.res.code = 200
            tx.res.headers.content_type = 'text/plain'
            tx.res.body = b("{0} request for {1}!".format(method, path))

            # Resume transaction
            tx.resume()

        daemon.run()

:mod:`Pyjo.Server.Daemon` is a full featured, highly portable non-blocking I/O
HTTP and WebSocket server, with IPv6, TLS, Comet (long polling), keep-alive and
multiple event loop support.

Signals
-------

The :mod:`Pyjo.Server.Daemon` process can be controlled at runtime with the
following signals.

INT, TERM
~~~~~~~~~

Shut down server immediately.

Events
------

:mod:`Pyjo.Server.Daemon` inherits all events from :mod:`Pyjo.Server.Base`.

Debugging
---------

You can set the ``PYJO_DAEMON_DEBUG`` environment variable to get some advanced
diagnostics information printed to :attr:`sys.stderr`. ::

    MOJO_DAEMON_DEBUG=1

Classes
-------
"""

import Pyjo.IOLoop
import Pyjo.Server.Base
import Pyjo.Transaction.WebSocket
import Pyjo.URL

from Pyjo.Util import convert, getenv, isalive, notnone, warn
from Pyjo.WebSocket import server_handshake

import platform
import signal
import socket
import weakref


DEBUG = getenv('PYJO_DAEMON_DEBUG', False)


class Pyjo_Server_Daemon(Pyjo.Server.Base.object):
    """
    :mod:`Pyjo.Server.Daemon` inherits all attributes and methods from
    :mod:`Pyjo.Server.Base` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.acceptors = kwargs.get('acceptors', [])
        """::

            acceptors = daemon.acceptors
            daemon.acceptors = []

        Active acceptors.
        """

        self.backlog = kwargs.get('backlog')
        """::

            backlog = daemon.backlog
            daemon.backlog = 128

        Listen backlog size, defaults to ``SOMAXCONN``.
        """

        self.inactivity_timeout = notnone(
            kwargs.get('inactivity_timeout'), lambda: convert(getenv('PYJO_INACTIVITY_TIMEOUT'), int, 15)
        )
        """::

            timeout = daemon.inactivity_timeout
            daemon.inactivity_timeout = 5

        Maximum amount of time in seconds a connection can be inactive before getting
        closed, defaults to the value of the ``PYJO_INACTIVITY_TIMEOUT`` environment
        variable or ``15``. Setting the value to ``0`` will allow connections to be
        inactive indefinitely.
        """

        self.ioloop = notnone(kwargs.get('ioloop'), lambda: Pyjo.IOLoop.singleton)
        """::

            loop = daemon.ioloop
            daemon.ioloop = Pyjo.IOLoop.new()

        Event loop object to use for I/O operations, defaults to the global
        :mod:`Pyjo.IOLoop` singleton.
        """

        self.listen = notnone(kwargs.get('listen'), lambda: (getenv('PYJO_LISTEN') or 'http://*:3000').split(','))
        """::

            listen = daemon.listen
            daemon.listen = ['https://127.0.0.1:8080']

        List of one or more locations to listen on, defaults to the value of the
        ``PYJO_LISTEN`` environment variable or ``http://*:3000`` (shortcut for
        ``http://0.0.0.0:3000``). ::

            # Listen on all IPv4 interfaces
            daemon.listen = ['http://*:3000']

            # Listen on all IPv4 and IPv6 interfaces
            daemon.listen = ['http://[::]:3000']

            # Listen on IPv6 interface
            daemon.listen = ['http://[::1]:4000']

            # Listen on IPv4 and IPv6 interfaces
            daemon.listen = ['http://127.0.0.1:3000', 'http://[::1]:3000']

            # Allow multiple servers to use the same port (SO_REUSEPORT)
            daemon.listen = ['http://*:8080?reuse=1']

            # Listen on two ports with HTTP and HTTPS at the same time
            daemon.listen = ['http://*:3000', 'https://*:4000']

            # Use a custom certificate and key
            daemon.listen = ['https://*:3000?cert=/x/server.crt&key=/y/server.key']

            # Or even a custom certificate authority
            daemon.listen = ['https://*:3000?cert=/x/server.crt&key=/y/server.key&ca=/z/ca.crt']

        These parameters are currently available:

        ``ca``
            ::

                ca='/etc/tls/ca.crt'

            Path to TLS certificate authority file.

        ``cert``
            ::

                cert='/etc/tls/server.crt'

            Path to the TLS cert file, defaults to a built-in test certificate.

        ``ciphers``
            ::

                ciphers='AES128-GCM-SHA256:RC4:HIGH:!MD5:!aNULL:!EDH'

            Cipher specification string.

        ``key``
            ::

                key='/etc/tls/server.key'

            Path to the TLS key file, defaults to a built-in test key.

        ``reuse``
            ::

                reuse=True

            Allow multiple servers to use the same port with the ``SO_REUSEPORT`` socket
            option.

        ``verify``
            ::

                verify=0x00

            TLS verification mode, defaults to ``0x03``.
        """

        self.max_clients = None
        """::

          max_clients = daemon.max_clients
          daemon.max_clients = 1000

        Maximum number of concurrent connections this server is allowed to handle
        before stopping to accept new incoming connections, passed along to
        :attr:`Pyjo.IOLoop.max_connections`.
        """

        self.max_requests = 25
        """::

            max_requests = daemon.max_requests
            daemon.max_requests = 100

        Maximum number of keep-alive requests per connection, defaults to ``25``.
        """

        self.silent = None
        """::

            boolean = daemon.silent
            daemon.silent = boolean

        Disable console messages.
        """

        self._connections = {}
        self._servers = {}

    def __del__(self):
        if DEBUG:
            warn(f'-- Method {self}.__del__')

        try:
            self.stop()
        except:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    def run(self):
        """::

            daemon.run()

        Run server.
        """
        # Make sure the event loop can be stopped in regular intervals
        loop = weakref.proxy(self.ioloop)

        def ticker_cb(loop):
            pass

        ticker = loop.recurring(1, ticker_cb)

        def signal_cb(signal, frame):
            if isalive(loop):
                loop.stop()

        for sig in signal.SIGINT, signal.SIGTERM:
            signal.signal(sig, signal_cb)

        self.start().ioloop.start()
        loop.remove(ticker)

    def start(self):
        """::

            daemon = daemon.start()

        Start accepting connections. ::

            cid  = daemon.set(listen=['http://127.0.0.1']).start().acceptors[0]
            port = daemon.ioloop.acceptor(cid).port
        """
        # Resume accepting connections
        loop = self.ioloop
        max_clients = self.max_clients
        if max_clients:
            loop.max_connections = max_clients
        servers = self._servers
        if servers:
            for name, server in servers.items():
                self.acceptors.append(loop.acceptor(server))
                del servers[name]

        # Start listening
        else:
            for listen in self.listen:
                self._listen(listen)

        return self

    def stop(self):
        """::

            daemon = daemon.stop()

        Stop accepting connections. Used by context manager.
        """
        # Suspend accepting connections but keep listen sockets open
        loop = self.ioloop
        while self.acceptors:
            cid = self.acceptors.pop(0)
            server = self._servers[cid] = loop.acceptor(cid)
            loop.remove(cid)
            server.stop()

        return self

    def _build_tx(self, cid, c):
        tx = self.build_tx()
        tx.connection = cid
        tx.res.headers.server = f'Pyjoyment ({platform.python_implementation()})'
        stream = self.ioloop.stream(cid)
        stream.timeout = self.inactivity_timeout
        handle = stream.handle
        if handle.family != socket.AF_UNIX:
            tx.local_address, tx.local_port = handle.getsockname()[:2]
            tx.remote_address, tx.remote_port = handle.getpeername()[:2]
        if c.get('tls'):
            tx.req.url.base.scheme = 'https'

        daemon = weakref.proxy(self)

        @tx.on('request')
        def request(tx):
            if not isalive(daemon):
                return
            req = tx.req
            if error := req.error:
                daemon._trace(cid, error['message'])

            # WebSocket
            if req.is_handshake:
                ws = daemon._connections[cid]['next'] = Pyjo.Transaction.WebSocket.new(handshake=tx)
                daemon.emit('request', server_handshake(ws))

            # HTTP
            else:
                daemon.emit('request', tx)

            # Last keep-alive request or corrupted connection
            c = daemon._connections[cid]
            if (c.get('requests') or 1) >= daemon.max_requests or req.error:
                tx.res.headers.connection = 'close'

            tx.on('resume', lambda tx: daemon._write(cid) if isalive(daemon) else None)
            daemon._write(cid)

        # Kept alive if we have more than one request on the connection
        c['requests'] = c.get('requests', 0) + 1
        if c['requests'] > 1:
            tx.kept_alive = True
        return tx

    def _close(self, cid):
        if tx := self._connections.get(cid, {}).get('tx'):
            tx.closed()
        self._connections.pop(cid, None)

    def _trace(self, cid, message):
        if self._connections.get(cid, {}).get('tx'):
            self.app.log.trace(message)

    def _finish(self, cid):
        # Always remove connection for WebSockets
        c = self._connections.get(cid)
        if not c or not (tx := c.get('tx')):
            return
        if tx.is_websocket:
            return self._remove(cid)

        # Finish transaction
        c.pop('tx').closed()

        # Upgrade connection to WebSocket
        if ws := c.pop('next', None):
            # Successful upgrade
            if ws.handshake.res.code == 101:
                c['tx'] = ws.set(established=True)
                daemon = weakref.proxy(self)
                ws.on('resume', lambda ws: daemon._write(cid) if isalive(daemon) else None)
                self._write(cid)

            # Failed upgrade
            else:
                ws.closed()

        # Close connection if necessary
        if tx.error or not tx.keep_alive:
            return self._remove(cid)

        # Build new transaction for leftovers
        if len(leftovers := tx.req.content.leftovers()):
            tx = c['tx'] = self._build_tx(cid, c)
            tx.server_read(leftovers)

    def _listen(self, listen):
        url = Pyjo.URL.new(listen)
        query = url.query
        options = {
            'address': url.host,
            'backlog': self.backlog,
            'reuse': query.param('reuse'),
        }
        port = url.port
        if port:
            options['port'] = port
        for param in 'ca', 'cert', 'ciphers', 'key':
            options['tls_' + param] = query.param(param)
        verify = query.param('verify')
        if verify is not None:
            if verify.startswith('0x'):
                options['tls_verify'] = int(verify, 16)
            else:
                options['tls_verify'] = int(verify)
        if options['address'] == '*':
            del options['address']
        tls = options['tls'] = url.protocol == 'https'

        daemon = weakref.proxy(self)

        @self.ioloop.server(**options)
        def server(loop, stream, cid):
            if isalive(daemon):
                c = daemon._connections[cid] = {'tls': tls}
                if DEBUG:
                    warn(f'-- Accept {cid} {stream.handle.getpeername()}\n')
                stream.timeout = daemon.inactivity_timeout

                def close_cb(stream):
                    if isalive(daemon):
                        daemon._close(cid)

                stream.on('close', close_cb)

                def error_cb(stream, err):
                    if isalive(daemon):
                        daemon.app.log.error(err)
                        daemon._close(cid)

                stream.on('error', error_cb)

                def read_cb(stream, chunk):
                    if isalive(daemon):
                        daemon._read(cid, chunk)

                stream.on('read', read_cb)

                def timeout_cb(stream):
                    if isalive(daemon) and c and c['tx']:
                        self.app.log.debug('Inactivity timeout')

                stream.on('timeout', timeout_cb)

        self.acceptors.append(server)

        if self.silent:
            return
        self.app.log.info(f'Listening at "{url}"')
        query.pairs = []
        if url.host == '*':
            url.host = '127.0.0.1'
        print(f'Server available at {url}')

    def _read(self, cid, chunk):
        # Make sure we have a transaction
        c = self._connections[cid]
        if not c.get('tx'):
            c['tx'] = self._build_tx(cid, c)
        tx = c['tx']
        if DEBUG:
            warn(f'-- Server <<< Client ({self._url(tx)})\n{chunk!r}')
        tx.server_read(chunk)

    def _remove(self, cid):
        self.ioloop.remove(cid)
        self._close(cid)

    def _url(self, tx):
        return tx.req.url.to_abs()

    def _write(self, cid):
        # Protect from resume event recursion
        c = self._connections.get(cid)
        if not c or not (tx := c.get('tx')) or c.get('writing'):
            return
        c['writing'] = True
        try:
            chunk = tx.server_write()
        finally:
            c['writing'] = False
        if DEBUG:
            warn(f'-- Server >>> Client ({self._url(tx)})\n{chunk!r}')
        next = self._finish if tx.is_finished else self._write if len(chunk) else None
        stream = self.ioloop.stream(cid)
        if next is None:
            stream.write(chunk)
            return
        daemon = weakref.proxy(self)
        stream.write(chunk, lambda stream: next(cid) if isalive(daemon) else None)


new = Pyjo_Server_Daemon.new
object = Pyjo_Server_Daemon
