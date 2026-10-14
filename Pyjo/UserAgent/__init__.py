"""
Pyjo.UserAgent - Non-blocking I/O HTTP and WebSocket user agent
===============================================================
::

    import Pyjo.IOLoop
    import Pyjo.Promise
    import Pyjo.URL
    import Pyjo.UserAgent

    # Fine grained response handling (raises on connection errors)
    ua = Pyjo.UserAgent.new()
    res = ua.get('docs.mojolicious.org').result
    if res.is_success:
        print(res.body)
    elif res.is_error:
        print(res.message)
    elif res.code == 301:
        print(res.headers.location)
    else:
        print('Whatever...')

    # Say hello to the Unicode snowman and include an Accept header
    print(ua.get('www.☃.net?hello=there', {'Accept': '*/*'}).result.body)

    # Extract data from HTML and XML resources with CSS selectors
    print(ua.get('www.perl.org').result.dom().at('title').text)

    # Scrape the latest headlines from a news site
    print(ua.get('blogs.perl.org').result.dom().find('h2 > a').map('text').join('\\n'))

    # IPv6 PUT request with Content-Type header and content
    tx = ua.put('[::1]:3000', {'Content-Type': 'text/plain'}, b'Hi!')

    # Quick JSON API request with Basic authentication
    url = Pyjo.URL.new('https://example.com/test.json')
    url.userinfo = 'sri:☃'
    value = ua.get(url).result.json()

    # JSON POST (application/json) with TLS certificate authentication
    ua.cert, ua.key = 'tls.crt', 'tls.key'
    tx = ua.post('https://example.com', json={'top': 'secret'})

    # Form POST (application/x-www-form-urlencoded)
    tx = ua.post('https://metacpan.org/search', form={'q': 'mojo'})

    # Search DuckDuckGo anonymously through Tor
    ua.proxy.http = 'socks://127.0.0.1:9050'
    print(ua.get('api.3g2upl4pq6kufc4m.onion/?q=mojolicious&format=json').result.json('/Abstract'))

    # GET request via UNIX domain socket "/tmp/myapp.sock" (percent encoded slash)
    print(ua.get('http+unix://%2Ftmp%2Fmyapp.sock/test').result.body)

    # Follow redirects to download Mojolicious from GitHub
    ua.max_redirects = 5
    ua.get('https://www.github.com/mojolicious/mojo/tarball/main').result.save_to('/home/sri/mojo.tar.gz')

    # Non-blocking request
    ua.get('mojolicious.org', lambda ua, tx: print(tx.result.dom().at('title').text))
    if not Pyjo.IOLoop.is_running():
        Pyjo.IOLoop.start()

    # Concurrent non-blocking requests (synchronized with promises)
    mojo_promise = ua.get_p('mojolicious.org')
    cpan_promise = ua.get_p('cpan.org')


    @Pyjo.Promise.all(mojo_promise, cpan_promise).then
    def titles(mojo, cpan):
        print(mojo[0].result.dom().at('title').text)
        print(cpan[0].result.dom().at('title').text)


    titles.wait()


    # WebSocket connection sending and receiving JSON via UNIX domain socket
    @ua.websocket('ws+unix://%2Ftmp%2Fmyapp.sock/echo.json')
    def echo(ua, tx):
        if not tx.is_websocket:
            return print('WebSocket handshake failed!')

        @tx.on('json')
        def json(tx, hash):
            print(f'WebSocket message via JSON: {hash["msg"]}')
            tx.finish()

        tx.send({'json': {'msg': 'Hello World!'}})


    if not Pyjo.IOLoop.is_running():
        Pyjo.IOLoop.start()

:mod:`Pyjo.UserAgent` is a full featured non-blocking I/O HTTP and WebSocket
user agent, with IPv6, TLS, SNI, IDNA, HTTP/SOCKS5 proxy, UNIX domain socket,
Comet (long polling), Promises/A+, keep-alive, connection pooling, timeout,
cookie, multipart, gzip compression and multiple event loop support.

All connections will be reset automatically if a new process has been forked,
this allows multiple processes to share the same :mod:`Pyjo.UserAgent` object
safely.

Non-blocking name resolution, SOCKS5 and TLS support come with
:mod:`Pyjo.IOLoop` and the standard library. Individual features can be
disabled with the ``PYJO_NO_NNR``, ``PYJO_NO_SOCKS`` and ``PYJO_NO_TLS``
environment variables.

Events
------

:mod:`Pyjo.UserAgent` inherits all events from :mod:`Pyjo.EventEmitter` and
can emit the following new ones.

prepare
~~~~~~~
::

    ua.on('prepare', lambda ua, tx: ...)

Emitted whenever a new transaction is being prepared, before relative URLs
are rewritten and cookies added. This includes automatically prepared proxy
``CONNECT`` requests and followed redirects. ::

    @ua.on('prepare')
    def prepare(ua, tx):
        if tx.req.url.host == 'mojolicious.org':
            tx.req.url = Pyjo.URL.new('/mock-mojolicious')

start
~~~~~
::

    ua.on('start', lambda ua, tx: ...)

Emitted whenever a new transaction is about to start. This includes
automatically prepared proxy ``CONNECT`` requests and followed redirects. ::

    @ua.on('start')
    def start(ua, tx):
        tx.req.headers.header('X-Bender', 'Bite my shiny metal ass!')

Debugging
---------

You can set the ``PYJO_CLIENT_DEBUG`` environment variable to get some
advanced diagnostics information printed to :data:`sys.stderr`. ::

    PYJO_CLIENT_DEBUG=1

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::UserAgent <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/UserAgent.pm>`_
of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.EventEmitter
import Pyjo.IOLoop
import Pyjo.IOLoop.Stream
import Pyjo.IOLoop.TLS
import Pyjo.Promise
import Pyjo.Transaction
import Pyjo.Transaction.HTTP
import Pyjo.UserAgent.CookieJar
import Pyjo.UserAgent.Proxy
import Pyjo.UserAgent.Server
import Pyjo.UserAgent.Transactor

from Pyjo.String.Unicode import split
from Pyjo.Util import term_escape, warn

import builtins
import os
import socket
import ssl
import sys
import weakref

from collections.abc import Callable
from typing import Any, Self, overload


type Anything = builtins.object

# The callback of a request gets the user agent and the transaction
type Callback = Callable[[Any, Any], Anything]

DEBUG = bool(os.environ.get('PYJO_CLIENT_DEBUG'))


class _Request:
    # A method for a common HTTP method, as Mojo makes them with monkey_patch
    def __init__(self, method: str, promise: bool) -> None:
        self.method = method
        name = method.lower()
        if promise:
            self.__doc__ = f"""::

            promise = ua.{name}_p('http://example.com')

        Same as :attr:`{name}`, but performs all requests non-blocking and
        returns a :mod:`Pyjo.Promise` object instead of accepting a callback. ::

            @ua.{name}_p('http://example.com', json={{'a': 'b'}}).then
            def ok(tx):
                print(tx.result.body)

            ok.catch(lambda err: warn(f'Connection error: {{err}}')).wait()
        """
        else:
            self.__doc__ = f"""::

            tx = ua.{name}('example.com')
            tx = ua.{name}('http://example.com', {{'Accept': '*/*'}}, b'Content!')
            tx = ua.{name}('http://example.com', {{'Accept': '*/*'}}, form={{'a': 'b'}})
            tx = ua.{name}('http://example.com', {{'Accept': '*/*'}}, json={{'a': 'b'}})

        Perform blocking ``{method}`` request and return resulting
        :mod:`Pyjo.Transaction.HTTP` object, takes the same arguments as
        :meth:`Pyjo.UserAgent.Transactor.Pyjo_UserAgent_Transactor.tx`
        (except for the ``{method}`` method, which is implied). You can also
        append a callback to perform requests non-blocking. ::

            ua.{name}('http://example.com', lambda ua, tx: print(tx.result.body), json={{'a': 'b'}})
            if not Pyjo.IOLoop.is_running():
                Pyjo.IOLoop.start()
        """
        self.promise = promise

    @overload
    def __get__(self, ua: None, owner: type | None = None) -> Self: ...

    @overload
    def __get__(self, ua: 'Pyjo_UserAgent', owner: type | None = None) -> Callable[..., Any]: ...

    # The arguments of the transactor come before the callback, so the method is not typed further
    def __get__(self, ua: 'Pyjo_UserAgent | None', owner: type | None = None) -> Self | Callable[..., Any]:
        if ua is None:
            return self
        method = self.method

        if self.promise:

            def request_p(*args: Any, **generator: Any) -> Pyjo.Promise.object:
                return ua.start_p(ua.build_tx(method, *args, **generator))

            return request_p

        def request(*args: Any, **generator: Any) -> Any:
            cb = args[-1] if args and callable(args[-1]) else None
            if cb is not None:
                args = args[:-1]
            return ua.start(ua.build_tx(method, *args, **generator), cb)

        return request


class Pyjo_UserAgent(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.UserAgent` inherits all methods from :mod:`Pyjo.EventEmitter`
    and implements the following new ones.
    """

    def __init__(
        self,
        *,
        ca: str | None = None,
        cert: str | None = None,
        connect_timeout: float | None = None,
        cookie_jar: 'Pyjo.UserAgent.CookieJar.object | None' = None,
        inactivity_timeout: float | None = None,
        insecure: bool | None = None,
        ioloop: Pyjo.IOLoop.object | None = None,
        key: str | None = None,
        max_connections: int = 5,
        max_redirects: int | None = None,
        max_response_size: int | None = None,
        proxy: 'Pyjo.UserAgent.Proxy.object | None' = None,
        request_timeout: float | None = None,
        server: 'Pyjo.UserAgent.Server.object | None' = None,
        source_address: tuple[str, int] | None = None,
        tls_context: ssl.SSLContext | None = None,
        transactor: 'Pyjo.UserAgent.Transactor.object | None' = None,
    ) -> None:
        """::

            ua = Pyjo.UserAgent.new()
            ua = Pyjo.UserAgent.new(max_redirects=3, request_timeout=5)

        Construct a new :mod:`Pyjo.UserAgent` object.
        """
        super().__init__()
        env = os.environ

        # Left out from Mojolicious: the example with set_defaults of IO::Socket::SSL, which ssl does not have
        self.ca = ca if ca is not None else env.get('PYJO_CA_FILE')
        """::

            ca = ua.ca
            ua.ca = '/etc/tls/ca.crt'

        Path to TLS certificate authority file used to verify the peer
        certificate, defaults to the value of the ``PYJO_CA_FILE``
        environment variable.
        """

        self.cert = cert if cert is not None else env.get('PYJO_CERT_FILE')
        """::

            cert = ua.cert
            ua.cert = '/etc/tls/client.crt'

        Path to TLS certificate file, defaults to the value of the
        ``PYJO_CERT_FILE`` environment variable.
        """

        self.connect_timeout: float = (
            connect_timeout if connect_timeout is not None else _number(env.get('PYJO_CONNECT_TIMEOUT'), True) or 10
        )
        """::

            timeout = ua.connect_timeout
            ua.connect_timeout = 5

        Maximum amount of time in seconds establishing a connection may take
        before getting canceled, defaults to the value of the
        ``PYJO_CONNECT_TIMEOUT`` environment variable or ``10``.
        """

        # Left out from Mojolicious: the example with IO::Socket::SSL::PublicSuffix, which ssl does not have
        self.cookie_jar = cookie_jar if cookie_jar is not None else Pyjo.UserAgent.CookieJar.new()
        """::

            cookie_jar = ua.cookie_jar
            ua.cookie_jar = Pyjo.UserAgent.CookieJar.new()

        Cookie jar to use for requests performed by this user agent, defaults
        to a :mod:`Pyjo.UserAgent.CookieJar` object. ::

            # Ignore all cookies
            ua.cookie_jar.ignore = lambda cookie: True

            # Add custom cookie to the jar
            ua.cookie_jar.add(
                Pyjo.Cookie.Response.new(
                    name='foo', value='bar', domain='docs.mojolicious.org', path='/Mojolicious'
                )
            )
        """

        self.inactivity_timeout: float = (
            inactivity_timeout
            if inactivity_timeout is not None
            else _number(env.get('PYJO_INACTIVITY_TIMEOUT'), False, 40)
        )
        """::

            timeout = ua.inactivity_timeout
            ua.inactivity_timeout = 15

        Maximum amount of time in seconds a connection can be inactive before
        getting closed, defaults to the value of the
        ``PYJO_INACTIVITY_TIMEOUT`` environment variable or ``40``. Setting the
        value to ``0`` will allow connections to be inactive indefinitely.
        """

        self.insecure = insecure if insecure is not None else env.get('PYJO_INSECURE') not in (None, '', '0')
        """::

            boolean = ua.insecure
            ua.insecure = boolean

        Do not require a valid TLS certificate to access HTTPS/WSS sites,
        defaults to the value of the ``PYJO_INSECURE`` environment variable. ::

            # Disable TLS certificate verification for testing
            ua.insecure = True
            print(ua.get('https://127.0.0.1:3000').result.code)
        """

        self._ioloop = ioloop

        self.key = key if key is not None else env.get('PYJO_KEY_FILE')
        """::

            key = ua.key
            ua.key = '/etc/tls/client.crt'

        Path to TLS key file, defaults to the value of the ``PYJO_KEY_FILE``
        environment variable.
        """

        self.max_connections = max_connections
        """::

            max = ua.max_connections
            ua.max_connections = 5

        Maximum number of keep-alive connections that the user agent will
        retain before it starts closing the oldest ones, defaults to ``5``.
        Setting the value to ``0`` will prevent any connections from being
        kept alive.
        """

        self.max_redirects: int = (
            max_redirects if max_redirects is not None else int(_number(env.get('PYJO_MAX_REDIRECTS'), True) or 0)
        )
        """::

            max = ua.max_redirects
            ua.max_redirects = 3

        Maximum number of redirects the user agent will follow before it
        fails, defaults to the value of the ``PYJO_MAX_REDIRECTS`` environment
        variable or ``0``.
        """

        self.max_response_size = max_response_size
        """::

            max = ua.max_response_size
            ua.max_response_size = 16777216

        Maximum response size in bytes, defaults to the value of
        :attr:`Pyjo.Message.Response.Pyjo_Message_Response.max_message_size`.
        Setting the value to ``0`` will allow responses of indefinite size.
        Note that increasing this value can also drastically increase memory
        usage, should you for example attempt to parse an excessively large
        response body with the methods ``dom`` or ``json`` of
        :mod:`Pyjo.Message`.
        """

        self.proxy = proxy if proxy is not None else Pyjo.UserAgent.Proxy.new()
        """::

            proxy = ua.proxy
            ua.proxy = Pyjo.UserAgent.Proxy.new()

        Proxy manager, defaults to a :mod:`Pyjo.UserAgent.Proxy` object. ::

            # Detect proxy servers from environment
            ua.proxy.detect()

            # Manually configure HTTP proxy (using CONNECT for HTTPS/WebSockets)
            ua.proxy.http = ua.proxy.https = 'http://127.0.0.1:8080'

            # Manually configure Tor (SOCKS5)
            ua.proxy.http = ua.proxy.https = 'socks://127.0.0.1:9050'

            # Manually configure UNIX domain socket (using CONNECT for HTTPS/WebSockets)
            ua.proxy.http = ua.proxy.https = 'http+unix://%2Ftmp%2Fproxy.sock'
        """

        self.request_timeout: float = (
            request_timeout if request_timeout is not None else _number(env.get('PYJO_REQUEST_TIMEOUT'), False, 0)
        )
        """::

            timeout = ua.request_timeout
            ua.request_timeout = 5

        Maximum amount of time in seconds establishing a connection, sending
        the request and receiving a whole response may take before getting
        canceled, defaults to the value of the ``PYJO_REQUEST_TIMEOUT``
        environment variable or ``0``. Setting the value to ``0`` will allow
        the user agent to wait indefinitely. The timeout will reset for every
        followed redirect. ::

            # Total limit of 5 seconds, of which 3 seconds may be spent connecting
            ua.max_redirects, ua.connect_timeout, ua.request_timeout = 0, 3, 5
        """

        self._server = server
        self._own_server = False

        # Unlike Mojolicious: socket_options of IO::Socket::IP is source_address, as socket.create_connection has it
        self.source_address = source_address
        """::

            address = ua.source_address
            ua.source_address = ('127.0.0.1', 0)

        Local address and port to connect from when opening new connections,
        as :func:`socket.create_connection` takes it.
        """

        # Unlike Mojolicious: tls_options of IO::Socket::SSL is an ssl.SSLContext
        self.tls_context = tls_context
        """::

            context = ua.tls_context
            ua.tls_context = ssl.create_default_context()

        The :class:`ssl.SSLContext` to use for TLS connections instead of the
        one that :attr:`ca`, :attr:`cert` and :attr:`key` make.
        """

        self.transactor = transactor if transactor is not None else Pyjo.UserAgent.Transactor.new()
        """::

            t = ua.transactor
            ua.transactor = Pyjo.UserAgent.Transactor.new()

        Transaction builder, defaults to a :mod:`Pyjo.UserAgent.Transactor`
        object. ::

            # Change name of user agent
            ua.transactor.name = 'MyUA 1.0'

            # Disable compression
            ua.transactor.compressed = False
        """

        self._connections: dict[str, dict[str, Any]] = {}
        self._pid: int | None = None
        self._queue: dict[Pyjo.IOLoop.object, list[tuple[str, str]]] = {}

    # Common HTTP methods
    delete = _Request('DELETE', False)
    delete_p = _Request('DELETE', True)
    get = _Request('GET', False)
    get_p = _Request('GET', True)
    head = _Request('HEAD', False)
    head_p = _Request('HEAD', True)
    options = _Request('OPTIONS', False)
    options_p = _Request('OPTIONS', True)
    patch = _Request('PATCH', False)
    patch_p = _Request('PATCH', True)
    post = _Request('POST', False)
    post_p = _Request('POST', True)
    put = _Request('PUT', False)
    put_p = _Request('PUT', True)
    query = _Request('QUERY', False)
    query_p = _Request('QUERY', True)

    def __del__(self) -> None:
        if sys.is_finalizing():
            return
        try:
            self._cleanup()
            # Not in Mojolicious: the server that the user agent made is closed here, as Perl closes it when it frees
            # it, and PyPy frees it only when its garbage collector runs
            if self._own_server and self._server is not None:
                self._server.restart()
        except Exception:
            pass

    @property
    def ioloop(self) -> Pyjo.IOLoop.object:
        """::

            loop = ua.ioloop
            ua.ioloop = Pyjo.IOLoop.new()

        Event loop object to use for blocking I/O operations, defaults to a
        :mod:`Pyjo.IOLoop` object.
        """
        if self._ioloop is None:
            self._ioloop = Pyjo.IOLoop.new()
        return self._ioloop

    @ioloop.setter
    def ioloop(self, value: Pyjo.IOLoop.object) -> None:
        self._ioloop = value

    @property
    def server(self) -> 'Pyjo.UserAgent.Server.object':
        """::

            server = ua.server
            ua.server = Pyjo.UserAgent.Server.new()

        Application server relative URLs will be processed with, defaults to a
        :mod:`Pyjo.UserAgent.Server` object. ::

            # Change log level
            ua.server.app.log.level = 'fatal'

            # Port currently used for processing relative URLs blocking
            print(ua.server.url().port)

            # Port currently used for processing relative URLs non-blocking
            print(ua.server.nb_url().port)
        """
        # TODO: the example of a mock web service, when Pyjoyment is ported
        if self._server is None:
            self._server = Pyjo.UserAgent.Server.new(ioloop=self.ioloop)
            self._own_server = True
        return self._server

    @server.setter
    def server(self, value: 'Pyjo.UserAgent.Server.object') -> None:
        self._server = value

    def build_tx(self, *args: Any, **generator: Any) -> Pyjo.Transaction.HTTP.object:
        """::

            tx = ua.build_tx('GET', 'example.com')
            tx = ua.build_tx('PUT', 'http://example.com', {'Accept': '*/*'}, b'Content!')
            tx = ua.build_tx('PUT', 'http://example.com', {'Accept': '*/*'}, form={'a': 'b'})
            tx = ua.build_tx('PUT', 'http://example.com', {'Accept': '*/*'}, json={'a': 'b'})

        Generate :mod:`Pyjo.Transaction.HTTP` object with
        :meth:`Pyjo.UserAgent.Transactor.Pyjo_UserAgent_Transactor.tx`. ::

            # Request with custom cookie
            tx = ua.build_tx('GET', 'https://example.com/account')
            tx.req.cookies({'name': 'user', 'value': 'sri'})
            tx = ua.start(tx)

            # Deactivate gzip compression
            tx = ua.build_tx('GET', 'example.com')
            tx.req.headers.remove('Accept-Encoding')
            tx = ua.start(tx)

            # Interrupt response by raising an error
            tx = ua.build_tx('GET', 'http://example.com')

            @tx.res.on('progress')
            def progress(res):
                if (server := res.headers.server) and 'IIS' in server:
                    res.error = {'message': 'Oh noes, it is IIS!'}

            tx = ua.start(tx)
        """
        return self.transactor.tx(*args, **generator)

    def build_websocket_tx(self, *args: Any) -> Pyjo.Transaction.HTTP.object:
        """::

            tx = ua.build_websocket_tx('ws://example.com')
            tx = ua.build_websocket_tx('ws://example.com', {'DNT': 1}, ['v1.proto'])

        Generate :mod:`Pyjo.Transaction.HTTP` object with
        :meth:`Pyjo.UserAgent.Transactor.Pyjo_UserAgent_Transactor.websocket`. ::

            # Custom WebSocket handshake with cookie
            tx = ua.build_websocket_tx('wss://example.com/echo')
            tx.req.cookies({'name': 'user', 'value': 'sri'})

            def echo(ua, tx):
                if not tx.is_websocket:
                    return print('WebSocket handshake failed!')

                @tx.on('message')
                def message(tx, msg):
                    print(f'WebSocket message: {msg}')
                    tx.finish()

                tx.send('Hi!')

            ua.start(tx, echo)
            if not Pyjo.IOLoop.is_running():
                Pyjo.IOLoop.start()
        """
        return self.transactor.websocket(*args)

    @overload
    def start(self, tx: Pyjo.Transaction.HTTP.object) -> Any: ...

    @overload
    def start(self, tx: Pyjo.Transaction.HTTP.object, cb: Callback) -> str | None: ...

    @overload
    def start(self, tx: Pyjo.Transaction.HTTP.object, cb: None) -> Any: ...

    def start(self, tx: Pyjo.Transaction.HTTP.object, cb: Callback | None = None) -> Any:
        """::

            tx = ua.start(Pyjo.Transaction.HTTP.new())

        Perform blocking request for a custom :mod:`Pyjo.Transaction.HTTP`
        object, which can be prepared manually or with :meth:`build_tx`. You
        can also append a callback to perform requests non-blocking, or use
        the method as a decorator of the callback. ::

            tx = ua.build_tx('GET', 'http://example.com')
            ua.start(tx, lambda ua, tx: print(tx.result.body))
            if not Pyjo.IOLoop.is_running():
                Pyjo.IOLoop.start()
        """
        # Fork-safety
        pid = os.getpid()
        if self._pid is not None and self._pid != pid:
            self._cleanup().server.restart()
        if self._pid is None:
            self._pid = pid

        # Non-blocking
        if cb is not None:
            if DEBUG:
                warn(f'-- Non-blocking request ({_url(tx)})\n')
            return self._start(Pyjo.IOLoop.object.singleton(), tx, cb)

        # Blocking
        if DEBUG:
            warn(f'-- Blocking request ({_url(tx)})\n')
        result = [tx]

        def blocking(ua: Pyjo_UserAgent, tx: Pyjo.Transaction.HTTP.object) -> None:
            ua.ioloop.stop()
            result[0] = tx

        self._start(self.ioloop, tx, blocking)
        self.ioloop.start()

        return result[0]

    def start_p(self, tx: Pyjo.Transaction.HTTP.object) -> Pyjo.Promise.object:
        """::

            promise = ua.start_p(Pyjo.Transaction.HTTP.new())

        Same as :meth:`start`, but performs all requests non-blocking and
        returns a :mod:`Pyjo.Promise` object instead of accepting a callback. ::

            tx = ua.build_tx('GET', 'http://example.com')

            @ua.start_p(tx).then
            def ok(tx):
                print(tx.result.body)

            ok.catch(lambda err: warn(f'Connection error: {err}')).wait()
        """
        promise = Pyjo.Promise.new()
        self.start(tx, lambda ua, tx: ua.transactor.promisify(promise, tx))
        return promise

    # The arguments of the transactor come before the callback, so the method is not typed further
    def websocket(self, *args: Any) -> Any:
        """::

            ua.websocket('ws://example.com', lambda ua, tx: ...)
            ua.websocket('ws://example.com', {'DNT': 1}, ['v1.proto'], lambda ua, tx: ...)

        Open a non-blocking WebSocket connection with transparent handshake,
        takes the same arguments as
        :meth:`Pyjo.UserAgent.Transactor.Pyjo_UserAgent_Transactor.websocket`.
        The callback will receive either a :mod:`Pyjo.Transaction.WebSocket`
        or :mod:`Pyjo.Transaction.HTTP` object, depending on if the handshake
        was successful, and without it the method is a decorator. ::

            @ua.websocket('wss://example.com/echo', ['v1.proto'])
            def echo(ua, tx):
                if not tx.is_websocket:
                    return print('WebSocket handshake failed!')
                if not tx.protocol:
                    return print('Subprotocol negotiation failed!')
                tx.on('finish', lambda tx, code, reason: print(f'WebSocket closed with status {code}.'))

                @tx.on('message')
                def message(tx, msg):
                    print(f'WebSocket message: {msg}')
                    tx.finish()

                tx.send('Hi!')

            if not Pyjo.IOLoop.is_running():
                Pyjo.IOLoop.start()

        You can activate ``permessage-deflate`` compression by setting the
        ``Sec-WebSocket-Extensions`` header, this can result in much better
        performance, but also increases memory usage by up to 300KiB per
        connection. ::

            ua.websocket('ws://example.com/foo', {'Sec-WebSocket-Extensions': 'permessage-deflate'}, lambda ua, tx: ...)
        """
        # Not in Mojolicious: a decorator without the callback
        if not args or not callable(args[-1]):

            def decorator(cb: Callback) -> Callback:
                self.start(self.build_websocket_tx(*args), cb)
                return cb

            return decorator

        return self.start(self.build_websocket_tx(*args[:-1]), args[-1])

    def websocket_p(self, *args: Any) -> Pyjo.Promise.object:
        """::

            promise = ua.websocket_p('ws://example.com')

        Same as :meth:`websocket`, but returns a :mod:`Pyjo.Promise` object
        instead of accepting a callback. ::

            @ua.websocket_p('wss://example.com/echo').then
            def ok(tx):
                promise = Pyjo.Promise.new()
                tx.on('finish', lambda tx, code, reason: promise.resolve())

                @tx.on('message')
                def message(tx, msg):
                    print(f'WebSocket message: {msg}')
                    tx.finish()

                tx.send('Hi!')
                return promise

            ok.catch(lambda err: warn(f'WebSocket error: {err}')).wait()
        """
        return self.start_p(self.build_websocket_tx(*args))

    def _cleanup(self) -> Self:
        self._pid = None
        for id in list(self._connections):
            self._finish(id, True)
        return self

    def _connect(self, loop: Pyjo.IOLoop.object, tx: Pyjo.Transaction.object, handle: Any = None) -> str:
        t = self.transactor
        proto, host, port = t.endpoint(tx) if handle is not None else t.peer(tx)

        options: dict[str, Any] = {'timeout': self.connect_timeout}
        if proto == 'http+unix':
            options['path'] = host
        else:
            options['address'], options['port'] = host, port
        # Unlike Mojolicious: socket_options of IO::Socket::IP is source_address
        if self.source_address is not None:
            options['source_address'] = self.source_address
        if handle is not None:
            options['handle'] = handle

        # SOCKS
        if proto == 'socks':
            options['socks_address'], options['socks_port'] = options['address'], options['port']
            proto, options['address'], options['port'] = t.endpoint(tx)
            req = tx.req
            req.via_proxy = False
            if req.proxy is not None and (userinfo := req.proxy.userinfo):
                user, *password = [part or '' for part in split(':', userinfo)]
                options['socks_user'], options['socks_pass'] = user, password[0] if password else None

        # TLS
        if options.setdefault('tls', proto == 'https'):
            options['tls_ca'], options['tls_cert'], options['tls_key'] = self.ca, self.cert, self.key
            context = self.tls_context
            # Unlike Mojolicious: no verification changes the context, where Mojo sets SSL_verify_mode of tls_options
            if self.insecure:
                if context is None:
                    context = Pyjo.IOLoop.TLS.context(**options)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            if context is not None:
                options['tls_context'] = context

        ref = weakref.ref(self)
        id = ''

        def connected(loop: Pyjo.IOLoop.object, err: Any, stream: Pyjo.IOLoop.Stream.object) -> None:
            # Connection error
            if (ua := ref()) is None:
                return
            if err:
                return ua._error(id, err)

            # Connection established
            def timeout(stream: Pyjo.IOLoop.Stream.object) -> None:
                _call(ref, '_error', id, 'Inactivity timeout')

            def close(stream: Pyjo.IOLoop.Stream.object) -> None:
                _call(ref, '_finish', id, True)

            def error(stream: Pyjo.IOLoop.Stream.object, err: Any) -> None:
                _call(ref, '_error', id, err)

            def read(stream: Pyjo.IOLoop.Stream.object, chunk: bytes) -> None:
                _call(ref, '_read', id, chunk)

            stream.on('timeout', timeout)
            stream.on('close', close)
            stream.on('error', error)
            stream.on('read', read)
            ua._process(id)

        id = loop.client(connected, **options)
        return id

    def _connect_proxy(self, loop: Pyjo.IOLoop.object, old: Pyjo.Transaction.HTTP.object, cb: Callback) -> str | None:
        # Start CONNECT request
        if (new := self.transactor.proxy_connect(old)) is None:
            return None
        id: str | None = None

        def connected(ua: Pyjo_UserAgent, tx: Pyjo.Transaction.HTTP.object) -> None:
            nonlocal id
            assert id is not None

            # Real transaction
            old.previous = tx
            old.req.via_proxy = False
            c = ua._connections[id] = {'cb': cb, 'ioloop': loop, 'tx': old}

            # CONNECT failed
            if tx.error or not tx.res.is_success or not tx.keep_alive:
                return ua._error(id, 'Proxy connection failed')

            # Start real transaction without TLS upgrade
            if tx.req.url.protocol != 'https':
                return ua._process(id)

            # TLS upgrade before starting the real transaction
            handle = loop.stream(id).steal_handle()
            ua._remove(id)
            id = ua._connect(loop, old, handle)
            ua._connections[id] = c

        id = self._start(loop, new, connected)
        return id

    def _connection(self, loop: Pyjo.IOLoop.object, tx: Pyjo.Transaction.HTTP.object, cb: Callback) -> str | None:
        # Reuse connection
        proto, host, port = self.transactor.endpoint(tx)
        if id := self._dequeue(loop, f'{proto}:{host}:{port}', True):
            if DEBUG:
                warn(f'-- Reusing connection {id} ({proto}://{host}:{port})\n')
            c = self._connections[id]
            c['cb'], c['tx'] = cb, tx
            if tx.connection is None:
                tx.kept_alive = True
            self._process(id)
            return id

        # CONNECT request to proxy required
        if id := self._connect_proxy(loop, tx, cb):
            return id

        # New connection
        if proto not in ('http', 'https', 'http+unix'):
            tx.res.error = {'message': f'Unsupported protocol: {proto}'}
            return loop.next_tick(lambda loop: cb(self, tx))
        id = self._connect(loop, tx)
        if DEBUG:
            warn(f'-- Connect {id} ({proto}://{host}:{port})\n')
        self._connections[id] = {'cb': cb, 'ioloop': loop, 'tx': tx}

        return id

    def _dequeue(self, loop: Pyjo.IOLoop.object, name: str, test: bool = False) -> str | None:
        old = self._queue.setdefault(loop, [])
        found: str | None = None
        new: list[tuple[str, str]] = []
        for queued in old:
            if found or name not in queued:
                new.append(queued)
                continue

            # Search for id/name and sort out corrupted connections if necessary
            if (stream := loop.stream(queued[1])) is None:
                continue
            if test and stream.is_readable:
                stream.close()
            else:
                found = queued[1]
        old[:] = new

        return found

    def _error(self, id: str, err: Any) -> None:
        if (tx := self._connections.get(id, {}).get('tx')) is not None:
            tx.res.error = {'message': str(err)}
        self._finish(id, True)

    def _finish(self, id: str, close: bool = False) -> None:
        # Remove request timeout and finish transaction
        if (c := self._connections.get(id)) is None:
            return None
        if (timeout := c.pop('timeout', None)) is not None and (loop := c.get('ioloop')) is not None:
            loop.remove(timeout)
        if (old := c.get('tx')) is None:
            return self._reuse(id, close)

        # Premature connection close
        res = old.closed().res.finish()
        if close and not res.code and not res.error:
            res.error = {'message': 'Premature connection close'}

        # Always remove connection for WebSockets
        if old.is_websocket:
            return self._remove(id)
        self.cookie_jar.collect(old)

        # Upgrade connection to WebSocket
        if (new := self.transactor.upgrade(old)) is not None:
            ref = weakref.ref(self)

            def resume(tx: Pyjo.Transaction.object) -> None:
                _call(ref, '_write', id)

            new.on('resume', resume)
            c['tx'] = new
            c['cb'](self, new)
            new.client_read(old.res.content.leftovers())
            return None

        # CONNECT requests always have a follow-up request
        if old.req.method.upper() != 'CONNECT':
            self._reuse(id, close)
        if res.is_error:
            res.error = {'message': res.message, 'code': res.code}
        if not self._redirect(c, old):
            c['cb'](self, old)

    def _process(self, id: str) -> None:
        c = self._connections[id]
        stream = c['ioloop'].stream(id)
        stream.timeout = self.inactivity_timeout
        tx = c['tx']
        tx.connection = id
        handle = stream.handle
        if handle.family != getattr(socket, 'AF_UNIX', None):
            tx.local_address, tx.local_port = handle.getsockname()[:2]
            tx.remote_address, tx.remote_port = handle.getpeername()[:2]

        ref = weakref.ref(self)

        def resume(tx: Pyjo.Transaction.object) -> None:
            _call(ref, '_write', id)

        tx.on('resume', resume)
        self._write(id)

    def _read(self, id: str, chunk: bytes) -> None:
        # Corrupted connection
        if (tx := self._connections.get(id, {}).get('tx')) is None:
            return self._remove(id)
        if DEBUG:
            warn(term_escape(f'-- Client <<< Server ({_url(tx)})\n{chunk.decode("latin-1")}\n'))
        tx.client_read(chunk)
        if tx.is_finished:
            self._finish(id)

    def _redirect(self, c: dict[str, Any], old: Pyjo.Transaction.HTTP.object) -> str | None:
        if (new := self.transactor.redirect(old)) is None:
            return None
        if not len(old.redirects()) < self.max_redirects:
            return None
        return self._start(c['ioloop'], new, c.pop('cb'))

    def _remove(self, id: str) -> None:
        if (c := self._connections.pop(id, None)) is None or (loop := c.get('ioloop')) is None:
            return
        self._dequeue(loop, id)
        loop.remove(id)

    def _reuse(self, id: str, close: bool) -> None:
        # Connection close
        c = self._connections.get(id, {})
        tx = c.pop('tx', None)
        max = self.max_connections
        if close or tx is None or not max or not tx.keep_alive or tx.error:
            return self._remove(id)

        # Keep connection alive
        queue = self._queue.setdefault(c['ioloop'], [])
        while len(queue) and len(queue) >= max:
            self._remove(queue.pop(0)[1])
        queue.append((':'.join(str(part) for part in self.transactor.endpoint(tx)), id))

    def _start(self, loop: Pyjo.IOLoop.object, tx: Pyjo.Transaction.HTTP.object, cb: Callback) -> str | None:
        # Application server
        self.emit('prepare', tx)
        url = tx.req.url
        if not url.is_abs:
            server = self.server
            base = server.url() if loop is self.ioloop else server.nb_url()
            url.scheme, url.host, url.port = base.scheme, base.host, base.port

        for helper in (self.proxy, self.cookie_jar):
            helper.prepare(tx)
        if (max := self.max_response_size) is not None:
            tx.res.max_message_size = max
        self.emit('start', tx)

        # Allow test servers sharing the same event loop to clean up connections
        if not loop.is_running:
            loop.next_tick(lambda loop: None)
            loop.one_tick()
        if not (id := self._connection(loop, tx, cb)):
            return None

        if t := self.request_timeout:
            ref = weakref.ref(self)
            c = self._connections.setdefault(id, {})
            if not c.get('timeout'):
                c['timeout'] = loop.timer(t, lambda loop: _call(ref, '_error', id, 'Request timeout'))

        return id

    def _write(self, id: str) -> None:
        # Protect from resume event recursion
        c = self._connections.get(id)
        if c is None or (tx := c.get('tx')) is None or c.get('writing'):
            return
        writing = c.get('writing')
        c['writing'] = True
        try:
            chunk = tx.client_write()
            if DEBUG:
                warn(term_escape(f'-- Client >>> Server ({_url(tx)})\n{chunk.decode("latin-1")}\n'))
            if not len(chunk):
                return

            ref = weakref.ref(self)

            def written(stream: Pyjo.IOLoop.Stream.object) -> None:
                _call(ref, '_write', id)

            c['ioloop'].stream(id).write(chunk, written)
        finally:
            c['writing'] = writing


# A method of the user agent, as long as it exists, as Mojo weakens the user agent in its callbacks
def _call(ref: 'weakref.ref[Any]', method: str, *args: Any) -> None:
    if (ua := ref()) is not None:
        getattr(ua, method)(*args)


# A number of the environment, where a false value is the default with "||" and only a missing one with "//"
def _number(value: str | None, or_: bool, default: float = 0) -> float:
    if value is None or (or_ and value in ('', '0')):
        return default
    number = float(value)
    return int(number) if number.is_integer() else number


def _url(tx: Pyjo.Transaction.object) -> str:
    return str(tx.req.url.to_abs())


new = Pyjo_UserAgent.new
object = Pyjo_UserAgent
