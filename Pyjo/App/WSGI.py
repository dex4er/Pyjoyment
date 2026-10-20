"""
Pyjo.App.WSGI - WSGI application
================================
::

    from Pyjo.App.WSGI import WSGI


    def hello(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [b'Hello World!']


    app = WSGI(app=hello)

    # Or import the module, as in Google Python Style Guide

    import Pyjo.App.WSGI

    app = Pyjo.App.WSGI.new(app=hello)

    # Mount it in an application of Pyjoyment
    import Pyjoyment

    pyjoyment = Pyjoyment.new()
    pyjoyment.plugin('Mount', {'/hello': app})

:mod:`Pyjo.App.WSGI` is an application of :mod:`Pyjo` that runs a ``WSGI``
application, as :pep:`3333` describes it, so that a server of :mod:`Pyjo`
serves it, a route of :mod:`Pyjoyment` embeds it, as
:mod:`Pyjoyment.Plugin.Mount` does, and :mod:`Pyjo.Test.Pyjo` tests it.

The part of the path that a route embeds the application under is
``SCRIPT_NAME``, after the base path of the request, and the rest of the path is
``PATH_INFO``. The body of the request is ``wsgi.input``, of the length of
``CONTENT_LENGTH``, also when the request was chunked.

A ``WSGI`` application blocks, so it runs in a pool of :attr:`threads`, and the
event loop goes on meanwhile. A response that the application has given whole
is written with its ``Content-Length``. Another one is written as the
application gives it, each chunk once the one before has been written, with the
chunked transfer encoding when the application does not give its
``Content-Length``. The threads are stopped before a fork, and the next request
starts them again.

An exception of the application before its response starts is a response
``500``, the exception page of :mod:`Pyjoyment` in a route that embeds it, and
an exception after that is logged and closes the connection.

Attributes
----------

:mod:`Pyjo.App.WSGI` inherits all attributes from :mod:`Pyjo.App` and
implements the following new ones.

See also
--------

:mod:`Pyjoyment`, :mod:`Pyjoyment.Plugin.Mount`, :mod:`Pyjo.Server.WSGI`,
https://mojolicious.org.

It has no counterpart in Mojolicious, it is inspired by
`Mojolicious::Plugin::MountPSGI <https://metacpan.org/pod/Mojolicious::Plugin::MountPSGI>`_ of CPAN; it is the
reverse of :mod:`Pyjo.Server.WSGI`.

Classes
-------
"""

import Pyjo.App
import Pyjo.Exception
import Pyjo.IOLoop
import Pyjo.Promise
import Pyjo.Transaction
import Pyjo.Util

from Pyjo.Util import url_unescape

import concurrent.futures
import io
import os
import sys
import threading
import traceback
import weakref
import wsgiref.util

from collections.abc import Callable, Iterable, Iterator
from typing import Any, cast
from wsgiref.types import WSGIApplication, WSGIEnvironment


class Pyjo_App_WSGI(Pyjo.App.object):
    """
    :mod:`Pyjo.App.WSGI` inherits all methods from :mod:`Pyjo.App` and
    implements the following new ones.
    """

    def __init__(self, attrs: dict[str, Any] | None = None, /, **kwargs: Any) -> None:
        """::

            app = Pyjo.App.WSGI.new(app=application)
            app = Pyjo.App.WSGI.new(app=application, threads=10)

        Construct a new :mod:`Pyjo.App.WSGI` object.
        """
        self.app: WSGIApplication | None = None
        """::

            application = app.app
            app.app = application

        The ``WSGI`` application to run.
        """

        self.threads = 4
        """::

            threads = app.threads
            app.threads = 10

        Maximum number of threads that run the application at the same time,
        defaults to ``4``.
        """

        self._executor: concurrent.futures.ThreadPoolExecutor | None = None
        super().__init__(attrs, **kwargs)
        _apps.add(self)

    def close(self) -> None:
        """::

            app.close()

        Stop the threads, after the calls of the application that they run,
        and close the connections and the servers of
        :attr:`~Pyjo.App.Pyjo_App.ua`, as the end of a ``with`` block does.
        """
        _shutdown(self)
        super().close()

    def handler(self, tx: Any) -> None:
        """::

            app.handler(Pyjo.Transaction.HTTP.new())
            app.handler(Pyjoyment.Controller.new())

        Run the application for the request of the transaction, or of the
        controller of a route that embeds the application, and write its
        response.
        """
        if (application := self.app) is None:
            raise Pyjo.Exception.new('No WSGI application')
        c = None
        if not isinstance(tx, Pyjo.Transaction.object):
            c = tx
            tx = c.tx
            c.render_later()
        _Call(self, application, tx, c).start()

    def _submit[T](self, fn: Callable[..., T], *args: Any) -> Pyjo.Promise.object:
        with _lock:
            if (executor := self._executor) is None:
                executor = self._executor = concurrent.futures.ThreadPoolExecutor(
                    max_workers=self.threads, thread_name_prefix='Pyjo.App.WSGI'
                )
        return Pyjo.Promise.new(executor.submit(fn, *args))


# The applications whose threads are stopped before a fork, as a process with threads may deadlock in its child, which
# Python warns about, and the child would have a pool without its threads; the next request starts the pool again
_apps: 'weakref.WeakSet[Pyjo_App_WSGI]' = weakref.WeakSet()
_lock = threading.Lock()


def _before_fork() -> None:
    if any([_shutdown(app) for app in list(_apps)]):
        Pyjo.Util._threads_joined()  # pyright: ignore[reportPrivateUsage]


def _shutdown(app: Pyjo_App_WSGI) -> bool:
    with _lock:
        executor, app._executor = app._executor, None  # pyright: ignore[reportPrivateUsage]
    if executor is None:
        return False
    executor.shutdown(wait=True)
    return True


if hasattr(os, 'register_at_fork'):
    os.register_at_fork(before=_before_fork)


# A call of the application, whose response is written on the event loop, while the application runs in a thread
class _Call:
    def __init__(self, app: Pyjo_App_WSGI, application: WSGIApplication, tx: Any, c: Any) -> None:
        self.app = app
        self.application = application
        self.c = c
        self.tx = tx
        self.response = _Response()
        self.busy = False
        self.chunked = False
        self.closed = False
        self.done = False

    def start(self) -> None:
        self.tx.on('finish', self._finish)
        self._submit(self.response.start, self.application, _environ(self.tx, self.c)).then(self._headers).catch(
            self._error
        )

    def _close(self) -> None:
        self.done = True
        self._submit(self.response.close).catch(self._failed)

    # End of the response
    def _end(self) -> None:
        content = self.tx.res.content
        (content.write_chunk if self.chunked else content.write)(b'')
        self._rendered()

    def _error(self, e: BaseException) -> None:
        if not self.done:
            self._close()
        message = _message(e)

        # The response has started, so the connection is closed, as the response cannot change
        if self.response.started:
            self.app.log.error(f'WSGI application failed: {message}')
            if (connection := self.tx.connection) is not None and (
                stream := Pyjo.IOLoop.stream(connection)
            ) is not None:
                stream.close()
            return

        # The exception page of Pyjoyment
        if (c := self.c) is not None:
            c.helpers.reply.exception(e)
            return

        self.app.log.error(f'WSGI application failed: {message}')
        res = self.tx.res
        res.code = 500
        res.headers.content_type = 'text/plain'
        res.body = b'Internal Server Error'
        self.tx.resume()

    def _failed(self, e: BaseException) -> None:
        self.app.log.error(f'WSGI application failed to close: {_message(e)}')

    # The end of the transaction, also when the connection is gone before the end of the response
    def _finish(self, *args: Any) -> None:
        self.closed = True
        if not self.busy and not self.done:
            self._close()

    def _headers(self, chunks: list[bytes] | None = None) -> None:
        response = self.response
        if response.status is None:
            raise Pyjo.Exception.new('WSGI application did not call start_response')
        res = self.tx.res
        code, _, message = response.status.partition(' ')
        res.code = int(code)
        res.message = message or None
        headers = res.headers
        for name, value in response.headers:
            if not wsgiref.util.is_hop_by_hop(name):
                headers.add(name, value)
        response.started = True

        # Whole response
        if response.iterator is None:
            self.done = True
            res.body = b''.join(chunks or [])
            return self._rendered()

        # Response as the application gives it, with the headers only for a HEAD request
        self.chunked = headers.content_length is None and self.tx.req.version == '1.1'
        if self.tx.is_empty:
            self._close()
            return self._end()
        self._write(chunks or [])

    def _more(self, chunks: list[bytes] | None = None) -> None:
        self.busy = False
        if self.closed:
            return self._close()
        if chunks is not None:
            return self._write(chunks)

        self.done = True
        self._end()

    def _next(self, *args: Any) -> None:
        if self.closed:
            return self._close()
        self.busy = True
        self._submit(self.response.next).then(self._more).catch(self._error)

    def _rendered(self) -> None:
        if (c := self.c) is not None:
            c.rendered()
        else:
            self.tx.resume()

    def _submit(self, fn: Callable[..., Any], *args: Any) -> Pyjo.Promise.object:
        return self.app._submit(fn, *args)  # pyright: ignore[reportPrivateUsage]

    def _write(self, chunks: list[bytes]) -> None:
        content = self.tx.res.content
        (content.write_chunk if self.chunked else content.write)(b''.join(chunks), self._next)
        self._rendered()


# What the application gives in its thread: the status and the headers of start_response, the chunks of the body, and
# the iterator of the rest of the body
class _Response:
    def __init__(self) -> None:
        self.headers: list[tuple[str, str]] = []
        self.iterator: Iterator[bytes] | None = None
        self.result: Iterable[bytes] | None = None
        self.started = False
        self.status: str | None = None
        self.written: list[bytes] = []

    def close(self) -> None:
        if callable(close := getattr(self.result, 'close', None)):
            close()

    # The chunks of the body up to its first one that is not empty, as the application may call start_response when its
    # body is iterated, or none at the end of the body
    def next(self) -> list[bytes] | None:
        if (iterator := self.iterator) is None:
            return None
        try:
            while not len(chunk := next(iterator)):
                pass
            chunks = self.written + [bytes(chunk)]
        except StopIteration:
            self.iterator = None
            self.close()
            chunks = self.written
        except BaseException:
            self.close()
            raise
        self.written = []
        return chunks if len(chunks) or self.iterator is not None else None

    def start(self, application: WSGIApplication, environ: WSGIEnvironment) -> list[bytes]:
        result = self.result = application(environ, self.start_response)

        # A body in a list is whole
        if isinstance(result, list | tuple):
            chunks = [*self.written, *(bytes(chunk) for chunk in cast(list[bytes], result))]
            self.written = []
            self.close()
            return chunks

        try:
            self.iterator = iter(result)
        except BaseException:
            self.close()
            raise
        return self.next() or []

    def start_response(
        self, status: str, headers: list[tuple[str, str]], exc_info: Any = None
    ) -> Callable[[bytes], Any]:
        if exc_info is not None:
            try:
                if self.started:
                    raise exc_info[1].with_traceback(exc_info[2])
            finally:
                exc_info = None
        elif self.status is not None:
            raise AssertionError('start_response has already been called')
        self.status, self.headers = status, list(headers)
        return self.write

    def write(self, data: bytes) -> None:
        self.written.append(bytes(data))


# The body of the request, read in the thread of the application
class _Input(io.RawIOBase):
    def __init__(self, content: Any) -> None:
        self._content = content
        self._offset = 0

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: Any, /) -> int:
        chunk = self._content.get_body_chunk(self._offset)
        if not chunk:
            return 0
        size = min(len(buffer), len(chunk))
        buffer[:size] = chunk[:size]
        self._offset += size
        return size


# The environment of PEP 3333 for the request of the transaction: the path that a route embeds the application under,
# after the base path, is SCRIPT_NAME, and the rest of it, which the route left in the stash, is PATH_INFO
def _environ(tx: Any, c: Any) -> WSGIEnvironment:
    req = tx.req
    url = req.url
    base = url.base
    path = url.path.to_abs_str()
    script = base.path.to_str().rstrip('/')

    if c is not None and (rest := c.stash().get('path')) is not None:
        route = url.path.to_route()
        if not route.endswith(rest):
            path = rest
        else:
            # The rest begins at the slash after the ones of the path above it
            end = len(path)
            if len(rest):
                end = -1
                for _ in range(route[: len(route) - len(rest)].count('/') + 1):
                    if (end := path.find('/', end + 1)) < 0:
                        end = len(path)
                        break
            script += path[:end]
            path = path[end:]

    https = req.is_secure
    environ: WSGIEnvironment = {
        'REQUEST_METHOD': req.method,
        'SCRIPT_NAME': _bytes(script),
        'PATH_INFO': _bytes(path),
        'QUERY_STRING': url.query.to_str(),
        'SERVER_NAME': base.host or tx.local_address or 'localhost',
        'SERVER_PORT': str(base.port or tx.local_port or (443 if https else 80)),
        'SERVER_PROTOCOL': f'HTTP/{req.version}',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https' if https else 'http',
        'wsgi.input': io.BufferedReader(_Input(req.content)),
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': True,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
        'wsgi.input_terminated': True,
    }
    if (address := tx.remote_address) is not None:
        environ['REMOTE_ADDR'] = address
    if (port := tx.remote_port) is not None:
        environ['REMOTE_PORT'] = str(port)

    # Headers, joined as CGI has them, and the length of the body, which is whole, as it has been read
    headers = req.headers
    for name in headers.names():
        key = name.upper().replace('-', '_')
        if key == 'CONTENT_TYPE':
            environ[key] = headers.header(name)
        elif key not in ('CONTENT_LENGTH', 'TRANSFER_ENCODING'):
            environ[f'HTTP_{key}'] = ('; ' if key == 'COOKIE' else ', ').join(headers.every_header(name))
    if size := req.content.body_size:
        environ['CONTENT_LENGTH'] = str(size)

    return environ


# An exception with its traceback, for the log
def _message(e: BaseException) -> str:
    return ''.join(traceback.format_exception(e)).rstrip()


# A path of PEP 3333: the unescaped bytes as the characters 0-255
def _bytes(path: str) -> str:
    return url_unescape(path.encode()).decode('latin-1')


new = Pyjo_App_WSGI.new
object = Pyjo_App_WSGI
WSGI = Pyjo_App_WSGI
