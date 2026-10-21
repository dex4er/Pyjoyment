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
the query, and :attr:`env` adds to them, as ``SCRIPT_FILENAME`` for
php-fpm, which :attr:`document_root` gives for each request otherwise. The
body of the request goes in records ``STDIN``, each once the one before has
been written.

The connection is one for each request, through the event loop. A response of
``CGI`` that comes whole, with the end of the request, is written with its
``Content-Length``. Another one is written as it comes, each chunk once the
one before has been written to the client, with the chunked transfer encoding
when it does not give its ``Content-Length``. What the application writes to
its standard error is logged.

A connection that fails or closes before the response is a response ``502``,
and one that closes after the start of the response closes the connection of
the client, as one that is quiet for longer than :attr:`inactivity_timeout`
does.

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
        found. ``SCRIPT_FILENAME`` of :attr:`env` takes its place.
        """

        self.env: dict[str, str] = {}
        """::

            env = app.env
            app.env = {'SCRIPT_FILENAME': '/var/www/index.php'}

        Parameters that are added to the environment of ``CGI`` of each
        request, and replace the ones of the same name.
        """

        self.inactivity_timeout: float = 60
        """::

            timeout = app.inactivity_timeout
            app.inactivity_timeout = 300

        Maximum amount of time in seconds a connection to the application can
        be inactive before it gets closed, defaults to ``60``.
        """

        self.url: str | Pyjo.URL.object | None = None
        """::

            url = app.url
            app.url = 'fcgi://127.0.0.1:9000'
            app.url = 'fcgi+unix://%2Frun%2Fphp%2Ffpm.sock'

        Location of the application, a TCP/IP address and port of ``fcgi://``
        or the path of a UNIX domain socket of ``fcgi+unix://``, escaped as the
        listen locations of :mod:`Pyjo.Server.Daemon` are.
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
        options = _options(url)
        c = None
        if not isinstance(tx, Pyjo.Transaction.object):
            c = tx
            tx = c.tx
            c.render_later()
        _Call(self, options, tx, c).start()


# A request to the application, whose response of CGI is written as it comes
class _Call:
    def __init__(self, app: Pyjo_App_FastCGI, options: dict[str, Any], tx: Any, c: Any) -> None:
        self.app = app
        self.options = options
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

        # The script of the path in the directory of the scripts
        if (root := self.app.document_root) is not None and 'SCRIPT_FILENAME' not in self.app.env:
            if not _script(params, os.fspath(root)):
                return self._not_found()

        # The path of the mount itself, as a server of FastCGI takes an empty PATH_INFO for the whole path in
        # SCRIPT_NAME, as nginx and Caddy send it
        elif not params['PATH_INFO'] and params['SCRIPT_NAME']:
            params['PATH_INFO'] = '/'
        params.update(self.app.env)
        self.params = _encode_pairs(params)
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
        stream.timeout = self.app.inactivity_timeout
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


# The options of the connection to the location of the application
def _options(url: Any) -> dict[str, Any]:
    url = Pyjo.URL.new(str(url))
    if (proto := url.protocol) == 'fcgi+unix':
        return {'path': url.host}
    if proto == 'fcgi' and url.host and url.port:
        return {'address': url.host, 'port': url.port}
    raise Pyjo.Exception.new(f'Invalid FastCGI location "{url}"')


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
