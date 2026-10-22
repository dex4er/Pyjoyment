"""
Pyjo.App.FastCGI - FastCGI application
======================================
::

    from Pyjo.App.FastCGI import FastCGI

    app = FastCGI(url='fcgi://127.0.0.1:9000')

    # Or import the module, as in Google Python Style Guide

    import Pyjo.App.FastCGI

    app = Pyjo.App.FastCGI.new(url='fcgi://127.0.0.1:9000')

    # PHP on php-fpm, on a UNIX domain socket, with its script
    app = Pyjo.App.FastCGI.new(
        url='fcgi+unix://%2Frun%2Fphp%2Ffpm.sock',
        env={'SCRIPT_FILENAME': '/var/www/index.php', 'DOCUMENT_ROOT': '/var/www'},
    )

    # Mount it in an application of Pyjoyment
    import Pyjoyment

    pyjoyment = Pyjoyment.new()
    pyjoyment.plugin('Mount', {'/php': app})
    pyjoyment.plugin('Mount', {'/fcgi': 'fcgi://127.0.0.1:9000'})

:mod:`Pyjo.App.FastCGI` is an application of :mod:`Pyjo` that runs a
``FastCGI`` application, as php-fpm runs PHP, through a connection to it, as
a client of `FastCGI 1.0
<https://fastcgi-archives.github.io/FastCGI_Specification.html>`_ in the role
of a responder, so that a server of :mod:`Pyjo` serves it, a route of
:mod:`Pyjoyment` embeds it, as :mod:`Pyjoyment.Plugin.Mount` does, and
:mod:`Pyjo.Test.Pyjo` tests it.

The parameters of the request are its environment of ``CGI``: the part of the
path that a route embeds the application under is ``SCRIPT_NAME``, after the
base path of the request, which a part of the path that does not end with a
slash, as ``/php`` of ``/phpx``, cannot be, so that the application is not
found there, the rest of the path is ``PATH_INFO``, ``/`` for
the path of the mount itself, as an empty one is the whole path in
``SCRIPT_NAME`` for a server of ``FastCGI``, ``REQUEST_URI`` is the path with
the query, without the header ``Proxy``, whose ``HTTP_PROXY`` an application
may take for the proxy of its own requests, as with httpoxy, and :attr:`env`
adds to them, as ``SCRIPT_FILENAME`` for php-fpm, which :attr:`document_root`
gives for each request otherwise. The body of the request goes in records
``STDIN``, each once the one before has been written.

The connection is one for each request, through the event loop. A response of
``CGI`` that comes whole, with the end of the request, is written with its
``Content-Length``. Another one is written as it comes, each chunk once the
one before has been written to the client, with the chunked transfer encoding
when it does not give its ``Content-Length``. What the application writes to
its standard error is logged.

A connection that fails or closes before the response is a response ``502``,
and one that closes after the start of the response closes the connection of
the client, as one that is quiet for longer than :attr:`inactivity_timeout`
does, which, until the response starts, the connection of the client waits
for without the inactivity timeout of the server.

Attributes
----------

:mod:`Pyjo.App.FastCGI` inherits all attributes from :mod:`Pyjo.App` and
implements the following new ones.

See also
--------

:mod:`Pyjoyment`, :mod:`Pyjoyment.Plugin.Mount`, :mod:`Pyjo.App.WSGI`,
:mod:`Pyjo.Server.FastCGI`, https://mojolicious.org.

It has no counterpart in Mojolicious; it is the reverse of
:mod:`Pyjo.Server.FastCGI`.

Classes
-------
"""

import Pyjo.App
import Pyjo.App.CGI
import Pyjo.Exception
import Pyjo.IOLoop
import Pyjo.URL

from Pyjo.Server.FastCGI import (
    BEGIN_REQUEST,
    END_REQUEST,
    HEADER,
    MAX_CONTENT,
    PARAMS,
    RESPONDER,
    STDIN,
    STDOUT,
    _encode_pairs,  # pyright: ignore[reportPrivateUsage]
    _record,  # pyright: ignore[reportPrivateUsage]
)

import os
import struct

from typing import Any


# The type of a record of the standard error of the application, which a responder may send
STDERR = 7

# The id of the request, the only one of its connection
ID = 1


class Pyjo_App_FastCGI(Pyjo.App.object):
    """
    :mod:`Pyjo.App.FastCGI` inherits all methods from :mod:`Pyjo.App` and
    implements the following new ones.
    """

    def __init__(self, attrs: dict[str, Any] | None = None, /, **kwargs: Any) -> None:
        """::

            app = Pyjo.App.FastCGI.new(url='fcgi://127.0.0.1:9000')

        Construct a new :mod:`Pyjo.App.FastCGI` object.
        """
        self.connect_timeout: float | None = None
        """::

            timeout = app.connect_timeout
            app.connect_timeout = 5

        Maximum amount of time in seconds establishing a connection to the
        application may take before getting canceled, the parameter
        ``connect_timeout`` of the query of :attr:`url` or ``10``.
        """

        self.document_root: str | os.PathLike[str] | None = None
        """::

            root = app.document_root
            app.document_root = '/var/www'

        Directory of the scripts of the application, as of PHP, as the
        application sees it, which takes the script of each request from its
        path, as a web server does: the path after the mount, up to its first
        part that ends with one of :attr:`script_extensions`, names the script,
        whose file in the directory is ``SCRIPT_FILENAME`` and whose path after
        the mount is ``SCRIPT_NAME``, the rest of the path is ``PATH_INFO``, and
        a path that ends with a slash names ``index`` with the first of them in
        it, as ``index.php``. A path with ``..`` is not found. With :attr:`script`, a path that names no script of the
        directory is the one of :attr:`script`, as the one entry of an
        application that takes every path, as with ``try_files`` of nginx,
        which the path decides, not the files, which the application may see
        elsewhere. ``SCRIPT_FILENAME`` of :attr:`env` takes its place.
        """

        self.env: dict[str, str] = {}
        """::

            env = app.env
            app.env = {'SCRIPT_FILENAME': '/var/www/index.php'}

        Parameters that are added to the environment of ``CGI`` of each
        request, and replace the ones of the same name.
        """

        self.inactivity_timeout: float | None = None
        """::

            timeout = app.inactivity_timeout
            app.inactivity_timeout = 300

        Maximum amount of time in seconds a connection to the application can
        be inactive before it gets closed, the parameter
        ``inactivity_timeout`` of the query of :attr:`url` or ``60``. Until the
        response starts, the connection of the client waits for it without
        the inactivity timeout of the server, so that this one gives the
        response ``502`` to an application that takes longer.
        """

        self.script: str | None = None
        """::

            script = app.script
            app.script = '/var/www/index.php'
            app.script = 'index.php'

        Script of the application for every path, as the one entry of an
        application of PHP that takes every path, with the path after the
        mount as ``PATH_INFO``, or for every path that names no script of
        :attr:`document_root`, in which it is then.
        """

        self.script_extensions: list[str] | None = None
        """::

            extensions = app.script_extensions
            app.script_extensions = ['.php', '.phtml']

        Extensions of the names of the scripts of :attr:`document_root`, the
        parameters ``script_extensions`` of the query of :attr:`url`, or
        ``['.php']``.
        """

        self.sendfile: Pyjo.App.CGI.Sendfile | None = None
        """::

            places = app.sendfile
            app.sendfile = '/var/www/private'
            app.sendfile = ['/var/www/private', '/var/www/media']
            app.sendfile = re.compile(r'/var/www/[^/]+/private/.*')

        Directories of the files that the application may reply with by the
        header ``X-Sendfile``, as Apache and lighttpd take it, with the path of
        the file, absolute or in one of them, or regular expressions of the
        whole path of such a file, once its symbolic links are resolved, as the
        private files that are not in :attr:`document_root`, the parameters
        ``sendfile`` of the query of :attr:`url`, which are directories, or
        none, which passes the header on as it is. A route that embeds the
        application replies then with the file, as the helper ``reply.file`` of
        :mod:`Pyjoyment` does, with the status and the other headers of the
        application, and a file that they do not allow is not found.
        """

        self.static: bool | None = None
        """::

            boolean = app.static
            app.static = True

        Reply with a file of :attr:`document_root` for a path that names it and
        no script, as ``try_files`` of nginx does, as the helper ``reply.file``
        of :mod:`Pyjoyment` does, with ranges and conditional requests, the
        parameter ``static`` of the query of :attr:`url`, false by default.
        The files are those that :mod:`Pyjoyment` sees, as for an application
        on the same file system, and a route that embeds the application
        replies with them, as :mod:`Pyjoyment.Plugin.Mount` makes.
        """

        self.url: str | Pyjo.URL.object | None = None
        """::

            url = app.url
            app.url = 'fcgi://127.0.0.1:9000'
            app.url = 'fcgi+unix://%2Frun%2Fphp%2Ffpm.sock'

        Location of the application, a TCP/IP address and port of ``fcgi://``
        or the path of a UNIX domain socket of ``fcgi+unix://``, escaped as the
        listen locations of :mod:`Pyjo.Server.Daemon` are. Its query can give
        :attr:`connect_timeout`, :attr:`document_root`,
        :attr:`inactivity_timeout`, :attr:`script`, :attr:`script_extensions`,
        :attr:`sendfile` and :attr:`static`, as the listen locations give their options, which the
        attributes take the place of. ::

            app.url = 'fcgi://127.0.0.1:9000?document_root=%2Fvar%2Fwww&script=index.php'
            app.url = 'fcgi://127.0.0.1:9000?inactivity_timeout=300'
        """

        super().__init__(attrs, **kwargs)

    def handler(self, tx: Any) -> None:
        """::

            app.handler(Pyjo.Transaction.HTTP.new())
            app.handler(Pyjoyment.Controller.new())

        Run the application for the request of the transaction, or of the
        controller of a route that embeds the application, and write its
        response.
        """
        if (url := self.url) is None:
            raise Pyjo.Exception.new('No FastCGI application')
        options, query = _location(url)
        options['timeout'] = _seconds(self.connect_timeout, query.get('connect_timeout'), 10)
        config = {
            'inactivity': _seconds(self.inactivity_timeout, query.get('inactivity_timeout'), 60),
            'root': os.fspath(self.document_root) if self.document_root is not None else query.get('document_root'),
            'script': self.script if self.script is not None else query.get('script'),
            'extensions': _extensions(self.script_extensions, query.get('script_extensions')),
            'sendfile': Pyjo.App.CGI._places(self.sendfile if self.sendfile is not None else query.get('sendfile')),  # pyright: ignore[reportPrivateUsage]
            'static': self.static if self.static is not None else _flag(query.get('static')),
        }
        _Call.run(self, config, tx, options)


# A request to the application, in records of FastCGI on a connection to it
class _Call(Pyjo.App.CGI._Response):  # pyright: ignore[reportPrivateUsage]
    name = 'FastCGI'

    # The path of the mount itself, as a server of FastCGI takes an empty PATH_INFO for the whole path in SCRIPT_NAME,
    # as nginx and Caddy send it
    mount_path = '/'

    def __init__(self, app: Pyjo_App_FastCGI, config: dict[str, Any], tx: Any, c: Any, options: dict[str, Any]) -> None:
        super().__init__(app, config, tx, c)
        self.options = options
        self.buffer = bytearray()
        self.id: str | None = None
        self.params = b''

    # The connection to the application has been closed, before the end of the request or after it
    def _closed(self, stream: Any) -> None:
        self.stream = None
        if self.done or self.closed:
            return
        self._failed('FastCGI connection closed before the end of the response')

    def _connected(self, loop: Any, err: Any, stream: Any) -> None:
        self.id = None
        if self.closed:
            if stream is not None:
                stream.close()
            return
        if err:
            return self._failed(f'FastCGI connection failed: {err}')

        self.stream = stream
        stream.timeout = self.inactivity
        stream.on('read', self._read)
        stream.on('close', self._closed)
        stream.on('error', self._error)
        stream.on('timeout', self._timeout)

        # The request, one for the connection, which the application closes after it
        begin = _record(BEGIN_REQUEST, ID, struct.pack('>HB5x', RESPONDER, 0))
        params = b''.join(
            _record(PARAMS, ID, self.params[i : i + MAX_CONTENT]) for i in range(0, len(self.params), MAX_CONTENT)
        )
        stream.write(begin + params + _record(PARAMS, ID))
        self._stdin()

    def _error(self, stream: Any, err: Any) -> None:
        self._failed(f'FastCGI connection failed: {err}')

    def _open(self, params: dict[str, str]) -> None:
        self.params = _encode_pairs(params)
        self.id = Pyjo.IOLoop.client(self._connected, **self.options)

    def _read(self, stream: Any, chunk: bytes) -> None:
        if self.done:
            return
        buffer = self.buffer
        buffer += chunk
        ended = False
        while len(buffer) >= HEADER.size:
            version, type, id, length, padding = HEADER.unpack_from(buffer)
            if version != 1:
                return self._failed(f'FastCGI version {version} is not supported')
            end = HEADER.size + length + padding
            if len(buffer) < end:
                break
            content = bytes(buffer[HEADER.size : HEADER.size + length])
            del buffer[:end]
            if id != ID:
                continue
            if type == STDOUT:
                self._stdout(content)
            elif type == STDERR and len(content):
                self.app.log.warn(f'FastCGI application: {content.decode("utf-8", "replace").rstrip()}')
            elif type == END_REQUEST:
                ended = True
                break
        self._flush(ended)

    # The body of the request, a record once the one before has been written, and an empty record at its end
    def _stdin(self, *args: Any) -> None:
        if (stream := self.stream) is None or self.done:
            return
        chunk = self.tx.req.content.get_body_chunk(self.offset) or b''
        if not len(chunk):
            return stream.write(_record(STDIN, ID))
        self.offset += len(chunk)
        records = b''.join(_record(STDIN, ID, chunk[i : i + MAX_CONTENT]) for i in range(0, len(chunk), MAX_CONTENT))
        stream.write(records, self._stdin)

    def _timeout(self, stream: Any) -> None:
        self._failed('FastCGI connection inactive')

    # The end of the connection to the application, and of its connecting
    def _stop(self) -> None:
        if (id := self.id) is not None:
            self.id = None
            Pyjo.IOLoop.remove(id)
        if (stream := self.stream) is not None:
            self.stream = None
            stream.close()


# The extensions of the scripts of the attribute, of the query of the location, or the one of PHP
def _extensions(value: list[str] | None, query: list[str] | None) -> list[str]:
    if value is not None:
        return value
    return query if query else ['.php']


# The options of the connection to the location of the application, and the parameters of its query
def _location(url: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    url = Pyjo.URL.new(str(url))
    names = ('connect_timeout', 'document_root', 'inactivity_timeout', 'script', 'static')
    query: dict[str, Any] = {name: value for name in names if (value := url.query.param(name)) is not None}
    for name in ('script_extensions', 'sendfile'):
        if values := url.query.every_param(name):
            query[name] = values
    if (proto := url.protocol) == 'fcgi+unix':
        return {'path': url.host}, query
    if proto == 'fcgi' and url.host and url.port:
        return {'address': url.host, 'port': url.port}, query
    raise Pyjo.Exception.new(f'Invalid FastCGI location "{url}"')


# A timeout of the attribute, of the query of the location, or its default
def _seconds(value: float | None, query: str | None, default: float) -> float:
    if value is not None:
        return value
    if query is None:
        return default
    try:
        return float(query)
    except ValueError:
        raise Pyjo.Exception.new(f'Invalid FastCGI timeout "{query}"') from None


# A flag of the query of the location, as the listen locations of Pyjo.Server.Daemon have them
def _flag(value: str | None) -> bool:
    return value is not None and value not in ('', '0')


new = Pyjo_App_FastCGI.new
object = Pyjo_App_FastCGI
FastCGI = Pyjo_App_FastCGI
