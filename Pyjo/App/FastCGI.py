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
base path of the request, the rest of the path is ``PATH_INFO``, ``/`` for
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
import Pyjo.Exception
import Pyjo.IOLoop
import Pyjo.Transaction
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
import re
import struct
import wsgiref.util

from typing import Any


# The type of a record of the standard error of the application, which a responder may send
STDERR = 7

# The id of the request, the only one of its connection
ID = 1

# The headers of a response by X-Sendfile that the file takes the place of
_SENT = ('content-length', 'x-sendfile')


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
        part that ends with ``.php``, names the script, whose file in the
        directory is ``SCRIPT_FILENAME`` and whose path after the mount is
        ``SCRIPT_NAME``, the rest of the path is ``PATH_INFO``, and a path that
        ends with a slash names ``index.php`` in it. A path with ``..`` is not
        found. With :attr:`script`, a path that names no script of the
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

        self.sendfile: str | os.PathLike[str] | None = None
        """::

            directory = app.sendfile
            app.sendfile = '/var/www/private'

        Directory of the files that the application may reply with by the
        header ``X-Sendfile``, as Apache and lighttpd take it, with the path of
        the file, as the private files that are not in :attr:`document_root`,
        the parameter ``sendfile`` of the query of :attr:`url`, or
        :attr:`document_root` with :attr:`static`, none otherwise. A route that
        embeds the application replies then with the file, as the helper
        ``reply.file`` of :mod:`Pyjoyment` does, with the status and the other
        headers of the application, and a file that is not in the directory is
        not found.
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
        :attr:`inactivity_timeout`, :attr:`script`, :attr:`sendfile` and
        :attr:`static`, as the listen locations give their options, which the
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
            'sendfile': os.fspath(self.sendfile) if self.sendfile is not None else query.get('sendfile'),
            'static': self.static if self.static is not None else _flag(query.get('static')),
        }
        c = None
        if not isinstance(tx, Pyjo.Transaction.object):
            c = tx
            tx = c.tx
            if not Pyjo.App._within(c):  # pyright: ignore[reportPrivateUsage]
                return c.helpers.reply.not_found()
            c.render_later()
        _Call(self, options, config, tx, c).start()


# A request to the application, whose response of CGI is written as it comes
class _Call:
    def __init__(self, app: Pyjo_App_FastCGI, options: dict[str, Any], config: dict[str, Any], tx: Any, c: Any) -> None:
        self.app = app
        self.options = options
        self.inactivity: float = config['inactivity']
        self.root: str | None = config['root']
        self.script: str | None = config['script']
        self.sendfile: str | None = config['sendfile']
        self.static: bool = config['static']
        self.waiting: tuple[str, float] | None = None
        self.c = c
        self.tx = tx
        self.buffer = bytearray()
        self.chunked = False
        self.closed = False
        self.done = False
        self.head = bytearray()
        self.headers: list[tuple[str, str]] | None = None
        self.id: str | None = None
        self.offset = 0
        self.pending: list[bytes] = []
        self.started = False
        self.stream: Any = None

    def start(self) -> None:
        self.tx.on('finish', self._finish)
        params = {**Pyjo.App._cgi(self.tx, self.c), **_extra(self.tx)}  # pyright: ignore[reportPrivateUsage]

        # Not the header Proxy, whose HTTP_PROXY an application may take for the proxy of its own requests, as httpoxy
        # (CVE-2016-5385) does, as nginx and Apache leave it out
        params.pop('HTTP_PROXY', None)

        # A file of the directory of the scripts, as try_files of nginx serves it
        if (c := self.c) is not None and self.static and (root := self.root) is not None:
            if (file := _file(root, params['PATH_INFO'])) is not None:
                self.done = True
                return c.helpers.reply.file(file)

        env = self.app.env

        # The script of the path in the directory of the scripts, or the one script for a path that names none
        if (root := self.root) is not None and 'SCRIPT_FILENAME' not in env:
            if (script := self.script) is not None and not _names_script(params['PATH_INFO']):
                params['PATH_INFO'] = f'/{script.lstrip("/")}'
            if not _script(params, root):
                return self._not_found()

        else:
            # The one script for every path
            if (script := self.script) is not None and 'SCRIPT_FILENAME' not in env:
                params['SCRIPT_FILENAME'] = script

            # The path of the mount itself, as a server of FastCGI takes an empty PATH_INFO for the whole path in
            # SCRIPT_NAME, as nginx and Caddy send it
            if not params['PATH_INFO'] and params['SCRIPT_NAME']:
                params['PATH_INFO'] = '/'
        params.update(env)
        self.params = _encode_pairs(params)

        # The connection of the client waits for the response without its inactivity timeout, which the one of the
        # connection to the application takes the place of, so that an application that takes longer gives 502
        if (connection := self.tx.connection) is not None and (stream := Pyjo.IOLoop.stream(connection)) is not None:
            self.waiting = (connection, stream.timeout)
            stream.timeout = 0

        self.id = Pyjo.IOLoop.client(self._connected, **self.options)

    def _close(self) -> None:
        if (connection := self.tx.connection) is not None and (stream := Pyjo.IOLoop.stream(connection)) is not None:
            stream.close()

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

    # End of the response
    def _end(self) -> None:
        self.done = True
        content = self.tx.res.content
        (content.write_chunk if self.chunked else content.write)(b'')
        self._rendered()
        self._stop()

    def _error(self, stream: Any, err: Any) -> None:
        self._failed(f'FastCGI connection failed: {err}')

    def _failed(self, message: str) -> None:
        if self.done:
            return

        # The response has started, so the connection is closed, as the response cannot change
        if self.started:
            self.done = True
            if not self.closed:
                self.app.log.error(message)
                self._close()
            return self._stop()

        self.done = True
        self._stop()
        self._waited()
        self.app.log.error(message)
        res = self.tx.res
        res.code = 502
        res.headers.content_type = 'text/plain'
        res.body = b'Bad Gateway'
        self._rendered()

    # The end of the transaction, also when the connection of the client is gone before the end of the response
    def _finish(self, *args: Any) -> None:
        self.closed = True
        self._stop()

    # The response of CGI of the records that have come
    def _flush(self, ended: bool) -> None:
        if self.headers is None:
            if ended:
                self._failed('FastCGI application ended without a response')
            return

        # Whole response
        res = self.tx.res
        if not self.started:
            self.started = True
            self._waited()
            if self._sendfile():
                return
            _status(res, self.headers)
            if ended:
                self.done = True
                res.body = b''.join(self.pending)
                self.pending = []
                self._rendered()
                return self._stop()

            # Response as it comes, with the headers only for a HEAD request
            self.chunked = res.headers.content_length is None and self.tx.req.version == '1.1'
            if self.tx.is_empty:
                return self._end()

        if len(self.pending):
            chunk, self.pending = b''.join(self.pending), []
            content = res.content
            stream = self.stream

            # The next records once the chunk has been written to the client
            def drained(*args: Any) -> None:
                if (stream := self.stream) is not None and not self.done:
                    stream.start()

            if stream is not None and not ended:
                stream.stop()
            (content.write_chunk if self.chunked else content.write)(chunk, drained)
            self._rendered()
        if ended:
            self._end()

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

    def _not_found(self) -> None:
        self.done = True
        if (c := self.c) is not None:
            return c.helpers.reply.not_found()
        res = self.tx.res
        res.code = 404
        res.headers.content_type = 'text/plain'
        res.body = b'Not Found'
        self.tx.resume()

    def _rendered(self) -> None:
        if (c := self.c) is not None:
            c.rendered()
        else:
            self.tx.resume()

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

    # The headers of the response of CGI, and the start of its body
    def _stdout(self, content: bytes) -> None:
        if self.headers is not None:
            if len(content):
                self.pending.append(content)
            return
        self.head += content
        if (m := re.search(rb'\r?\n\r?\n', self.head)) is None:
            return
        head, body = bytes(self.head[: m.start()]), bytes(self.head[m.end() :])
        self.head = bytearray()
        self.headers = [
            (name.strip(), value.strip())
            for name, _, value in (line.partition(':') for line in re.split(r'\r?\n', head.decode('latin-1')))
            if name.strip()
        ]
        if len(body):
            self.pending.append(body)

    # The file of the header X-Sendfile of the application, in the directory of the files that it may reply with
    def _sendfile(self) -> bool:
        # The directory of sendfile, or the one of the files that static replies with
        directory = self.sendfile if self.sendfile is not None else self.root if self.static else None
        if (c := self.c) is None or directory is None or (headers := self.headers) is None:
            return False
        if (value := next((value for name, value in headers if name.lower() == 'x-sendfile'), None)) is None:
            return False
        self.done = True
        self._stop()
        if (file := _inside(directory, value)) is None:
            self.app.log.error(f'FastCGI application sent the file "{value}", which is not in "{directory}"')
            c.helpers.reply.not_found()
            return True
        _status(self.tx.res, [(name, value) for name, value in headers if name.lower() not in _SENT])
        c.helpers.reply.file(file)
        return True

    # The inactivity timeout of the connection of the client again, once the response starts
    def _waited(self) -> None:
        if (waiting := self.waiting) is not None:
            self.waiting = None
            connection, timeout = waiting
            if (stream := Pyjo.IOLoop.stream(connection)) is not None:
                stream.timeout = timeout

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


# The parameters that CGI servers add, which the applications of PHP need
def _extra(tx: Any) -> dict[str, str]:
    req = tx.req
    url = req.url
    uri = url.path.to_abs_str()
    if base := url.base.path.to_str().rstrip('/'):
        uri = base + uri
    if query := url.query.to_str():
        uri += f'?{query}'
    extra = {'GATEWAY_INTERFACE': 'CGI/1.1', 'REQUEST_URI': uri, 'SERVER_SOFTWARE': 'Pyjoyment (Python)'}
    if req.is_secure:
        extra['HTTPS'] = 'on'
    return extra


# The options of the connection to the location of the application, and the parameters of its query
def _location(url: Any) -> tuple[dict[str, Any], dict[str, str]]:
    url = Pyjo.URL.new(str(url))
    names = ('connect_timeout', 'document_root', 'inactivity_timeout', 'script', 'sendfile', 'static')
    query = {name: value for name in names if (value := url.query.param(name)) is not None}
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


# A file of the directory for a path that names no script and no directory, as try_files of nginx takes it
def _file(root: str, path: str) -> str | None:
    if not path or path.endswith('/') or _names_script(path) or '..' in path.split('/'):
        return None
    return _inside(root, os.fsdecode(path.lstrip('/').encode('latin-1')))


# A flag of the query of the location, as the listen locations of Pyjo.Server.Daemon have them
def _flag(value: str | None) -> bool:
    return value is not None and value not in ('', '0')


# A file in a directory, also once its symbolic links are resolved, so that no link leads out of it
def _inside(directory: str, path: str) -> str | None:
    base = os.path.realpath(directory)
    file = os.path.realpath(os.path.join(base, path))
    if os.path.commonpath([base, file]) != base or not os.path.isfile(file):
        return None
    return file


# A path that names a script of PHP
def _names_script(path: str) -> bool:
    return any(part.endswith('.php') for part in path.split('/'))


# The script of the path in the directory of the scripts, as nginx has it with fastcgi_split_path_info and
# $document_root$fastcgi_script_name, unless the path has ..
def _script(params: dict[str, str], root: str) -> bool:
    parts = (params['PATH_INFO'] or '/').split('/')
    if '..' in parts:
        return False
    end = next((i + 1 for i, part in enumerate(parts) if part.endswith('.php')), len(parts))
    script, rest = '/'.join(parts[:end]), '/'.join(parts[end:])
    if end == len(parts) and script.endswith('/'):
        script += 'index.php'
    params['SCRIPT_FILENAME'] = root.rstrip('/') + script
    params['SCRIPT_NAME'] += script
    params['PATH_INFO'] = f'/{rest}' if end < len(parts) else ''
    params['DOCUMENT_ROOT'] = root
    return True


# The status of a response of CGI from its header Status, or a redirect for a header Location, and its other headers
def _status(res: Any, headers: list[tuple[str, str]]) -> None:
    res.code = 200
    location = False
    for name, value in headers:
        if name.lower() == 'status':
            code, _, message = value.partition(' ')
            res.code = int(code)
            res.message = message or None
            continue
        if name.lower() == 'location':
            location = True
        if not wsgiref.util.is_hop_by_hop(name):
            res.headers.add(name, value)
    if location and not any(name.lower() == 'status' for name, _ in headers):
        res.code = 302


new = Pyjo_App_FastCGI.new
object = Pyjo_App_FastCGI
FastCGI = Pyjo_App_FastCGI
