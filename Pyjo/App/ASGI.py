"""
Pyjo.App.ASGI - ASGI application
================================
::

    from Pyjo.App.ASGI import ASGI


    async def hello(scope, receive, send):
        await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/plain')]})
        await send({'type': 'http.response.body', 'body': b'Hello World!'})


    app = ASGI(app=hello)

    # Or import the module, as in Google Python Style Guide

    import Pyjo.App.ASGI

    app = Pyjo.App.ASGI.new(app=hello)

    # Mount it in an application of Pyjoyment
    import Pyjoyment

    pyjoyment = Pyjoyment.new()
    pyjoyment.plugin('Mount', {'/hello': app})

:mod:`Pyjo.App.ASGI` is an application of :mod:`Pyjo` that runs an ``ASGI``
application, as https://asgi.readthedocs.io describes it, so that a server of
:mod:`Pyjo` serves it, a route of :mod:`Pyjoyment` embeds it, as
:mod:`Pyjoyment.Plugin.Mount` does, and :mod:`Pyjo.Test.Pyjo` tests it.

The part of the path that a route embeds the application under is
``root_path``, after the base path of the request, and ``path`` is the whole
path, with ``root_path`` in front of it. The body of the request is the
message ``http.request`` of ``receive``, in chunks with ``more_body``, and
the next ``receive`` waits for the end of the connection, the message
``http.disconnect``.

The application runs as a coroutine of the reactor, as
:meth:`Pyjo.Reactor.Pyjo_Reactor.run_coroutine` runs it: with
:mod:`Pyjo.Reactor.Asyncio`, a task of the event loop of :mod:`asyncio`,
where it can await anything of the loop, and with another reactor, as
:mod:`Pyjo.Reactor.Poll`, a coroutine that awaits only ``receive`` and
``send``, so that an application that awaits anything else fails there. A
response that the application gives in one message ``http.response.body`` is
written with its ``Content-Length``. Another one is written as the application
sends it, with the chunked transfer encoding when the application does not
give its ``Content-Length``, and ``send`` returns once the chunk has been
written, so that a stream of server-sent events goes at the pace of the
client. Once the connection is gone, ``send`` does nothing.

An exception of the application before its response starts is a response
``500``, the exception page of :mod:`Pyjoyment` in a route that embeds it, an
exception after that is logged and closes the connection, as does an
application that returns before the end of its response, and an exception
after the end of the response is logged.

Attributes
----------

:mod:`Pyjo.App.ASGI` inherits all attributes from :mod:`Pyjo.App` and
implements the following new ones.

See also
--------

:mod:`Pyjoyment`, :mod:`Pyjoyment.Plugin.Mount`, :mod:`Pyjo.App.WSGI`,
:mod:`Pyjo.Server.ASGI`, https://mojolicious.org.

It has no counterpart in Mojolicious; it is the reverse of
:mod:`Pyjo.Server.ASGI`.

Classes
-------
"""

import Pyjo.App
import Pyjo.Exception
import Pyjo.IOLoop
import Pyjo.Promise
import Pyjo.Transaction

from Pyjo.Server.ASGI import Application, Message, Scope
from Pyjo.Util import url_unescape

import traceback
import wsgiref.util

from typing import Any


class Pyjo_App_ASGI(Pyjo.App.object):
    """
    :mod:`Pyjo.App.ASGI` inherits all methods from :mod:`Pyjo.App` and
    implements the following new ones.
    """

    def __init__(self, attrs: dict[str, Any] | None = None, /, **kwargs: Any) -> None:
        """::

            app = Pyjo.App.ASGI.new(app=application)

        Construct a new :mod:`Pyjo.App.ASGI` object.
        """
        self.app: Application | None = None
        """::

            application = app.app
            app.app = application

        The ``ASGI`` application to run.
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
        if (application := self.app) is None:
            raise Pyjo.Exception.new('No ASGI application')
        c = None
        if not isinstance(tx, Pyjo.Transaction.object):
            c = tx
            tx = c.tx
            c.render_later()
        _Call(self, application, tx, c).start()


# A call of the application, whose messages are the request and the response of the transaction
class _Call:
    def __init__(self, app: Pyjo_App_ASGI, application: Application, tx: Any, c: Any) -> None:
        self.app = app
        self.application = application
        self.c = c
        self.tx = tx
        self.chunked = False
        self.closed = False
        self.ended = False
        self.finished = Pyjo.Promise.new()
        self.headers: list[tuple[str, str]] = []
        self.offset = 0
        self.read = False
        self.started = False
        self.status: int | None = None
        self.written: Pyjo.Promise.object | None = None

    def start(self) -> None:
        self.tx.on('finish', self._finish)
        try:
            coro = self.application(_scope(self.tx, self.c), self._receive, self._send)
        except Exception as e:
            return self._error(e)
        Pyjo.Promise.new(coro).then(self._returned, self._error)

    # End of the response
    def _end(self) -> None:
        self.ended = True
        content = self.tx.res.content
        (content.write_chunk if self.chunked else content.write)(b'')
        self._rendered()

    def _error(self, e: Any) -> None:
        message = _message(e)

        # The response has started, so the connection is closed, as the response cannot change, unless it has ended, as
        # Starlette raises the exception after its response 500
        if self.started:
            if not self.closed:
                self.app.log.error(f'ASGI application failed: {message}')
                if not self.ended:
                    self._close()
            return

        # The exception page of Pyjoyment
        self.started = self.ended = True
        if (c := self.c) is not None:
            c.helpers.reply.exception(e)
            return

        self.app.log.error(f'ASGI application failed: {message}')
        res = self.tx.res
        res.code = 500
        res.headers.content_type = 'text/plain'
        res.body = b'Internal Server Error'
        self.tx.resume()

    def _close(self) -> None:
        if (connection := self.tx.connection) is not None and (stream := Pyjo.IOLoop.stream(connection)) is not None:
            stream.close()

    # The end of the transaction, also when the connection is gone before the end of the response, after which receive
    # gives http.disconnect and send does nothing
    def _finish(self, *args: Any) -> None:
        self.closed = True
        self.finished.resolve()
        if (written := self.written) is not None:
            self.written = None
            written.resolve()

    # The status and the headers of http.response.start, and the chunked transfer encoding for a body that comes in more
    # than one message without its length
    def _headers(self, whole: bool) -> None:
        self.started = True
        res = self.tx.res
        res.code = self.status
        headers = res.headers
        for name, value in self.headers:
            if not wsgiref.util.is_hop_by_hop(name):
                headers.add(name, value)
        self.chunked = not whole and headers.content_length is None and self.tx.req.version == '1.1'

    async def _receive(self) -> Message:
        # The body of the request, which has been read whole, in chunks
        if not self.read:
            content = self.tx.req.content
            chunk = content.get_body_chunk(self.offset) or b''
            self.offset += len(chunk)
            more = len(chunk) > 0 and self.offset < content.body_size
            self.read = not more
            return {'type': 'http.request', 'body': bytes(chunk), 'more_body': more}

        # The end of the connection
        if not self.closed:
            await self.finished
        return {'type': 'http.disconnect'}

    def _rendered(self) -> None:
        if (c := self.c) is not None:
            c.rendered()
        else:
            self.tx.resume()

    def _returned(self, *args: Any) -> None:
        if not self.started:
            return self._error(Pyjo.Exception.new('ASGI application returned without a response'))
        if not self.ended and not self.closed:
            self.app.log.error('ASGI application returned without the end of its response')
            self._close()

    async def _send(self, message: Message) -> None:
        if self.closed:
            return
        type = message['type']

        # Status and headers
        if type == 'http.response.start':
            if self.status is not None:
                raise Pyjo.Exception.new('ASGI message "http.response.start" has already been sent')
            self.status = int(message['status'])
            self.headers = [
                (bytes(name).decode('latin-1'), bytes(value).decode('latin-1')) for name, value in message['headers']
            ]
            return

        if type != 'http.response.body':
            raise Pyjo.Exception.new(f'Unknown ASGI message "{type}"')
        if self.status is None:
            raise Pyjo.Exception.new('ASGI message "http.response.start" has not been sent')
        if self.ended:
            # A HEAD request, whose response ends with its headers
            if self.tx.is_empty:
                return
            raise Pyjo.Exception.new('ASGI response has already ended')
        body = bytes(message.get('body', b''))
        more = bool(message.get('more_body', False))

        # Whole response
        if not self.started:
            self._headers(not more)
            if not more:
                self.ended = True
                self.tx.res.body = body
                return self._rendered()

        # Response as the application sends it, with the headers only for a HEAD request
        if self.tx.is_empty:
            return self._end()
        if len(body):
            written = self.written = Pyjo.Promise.new()
            content = self.tx.res.content

            def drained(*args: Any) -> None:
                written.resolve()

            (content.write_chunk if self.chunked else content.write)(body, drained)
            self._rendered()
            await written
        if not more and not self.closed:
            self._end()


# The connection scope of the request of the transaction: the path that a route embeds the application under is
# root_path, which path begins with
def _scope(tx: Any, c: Any) -> Scope:
    req = tx.req
    url = req.url
    base = url.base
    script, path = Pyjo.App._mount(tx, c)  # pyright: ignore[reportPrivateUsage]

    # Headers, with the length of the body, which is whole, as it has been read
    headers = [
        (name.lower().encode('latin-1'), value.encode('latin-1'))
        for name, value in req.headers.to_list()
        if name.lower() not in ('content-length', 'transfer-encoding')
    ]
    if size := req.content.body_size:
        headers.append((b'content-length', str(size).encode()))

    https = req.is_secure
    scope: dict[str, Any] = {
        'type': 'http',
        'asgi': {'version': '3.0', 'spec_version': '2.4'},
        'http_version': req.version,
        'method': req.method,
        'scheme': 'https' if https else 'http',
        'path': _str(script + path),
        'raw_path': (script + path).encode(),
        'query_string': url.query.to_str().encode(),
        'root_path': _str(script),
        'headers': headers,
        'server': (base.host or tx.local_address or 'localhost', base.port or tx.local_port or (443 if https else 80)),
    }
    if (address := tx.remote_address) is not None:
        scope['client'] = (address, tx.remote_port or 0)
    return scope


# An exception with its traceback, for the log
def _message(e: Any) -> str:
    return ''.join(traceback.format_exception(e)).rstrip() if isinstance(e, BaseException) else str(e)


# A path of ASGI: the unescaped bytes as UTF-8
def _str(path: str) -> str:
    return url_unescape(path.encode()).decode('utf-8', 'replace')


new = Pyjo_App_ASGI.new
object = Pyjo_App_ASGI
ASGI = Pyjo_App_ASGI
