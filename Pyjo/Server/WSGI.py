"""
Pyjo.Server.WSGI - WSGI server
==============================
::

    import Pyjo.Server.WSGI

    wsgi = Pyjo.Server.WSGI.new()


    @wsgi.unsubscribe('request').on('request')
    def request(wsgi, tx):
        # Request
        method = tx.req.method
        path = tx.req.url.path

        # Response
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = f'{method} request for {path}!'.encode()

        # Resume transaction
        tx.resume()


    app = wsgi.to_wsgi_app()

:mod:`Pyjo.Server.WSGI` allows :mod:`Pyjoyment` applications to run on all
``WSGI`` compatible servers, as :pep:`3333` describes them. ::

    # Serve with the server of wsgiref
    from wsgiref.simple_server import make_server

    make_server('', 3000, app).serve_forever()

The response is given in the ``request`` event, as ``WSGI`` is synchronous;
its content can come later, as the event loop of :mod:`Pyjo.IOLoop` runs
while the server waits for it. The request is read from the environment of
:pep:`3333` with ``read``, a body of unknown length when the server sets
``wsgi.input_terminated``, as for a chunked request. The response goes
without the hop-by-hop headers that :pep:`3333` forbids, so chunked content is
sent without its framing, which the server adds. The transaction is finished
when the server closes the body of the response.

WSGI servers
------------

* Gunicorn and Waitress: also chunked requests.
* uWSGI with ``--http-socket``: a chunked request reaches the application
  without its body.
* Werkzeug: also chunked requests, with a ``Date`` header of its own next to
  the one of the response.

Events
------

:mod:`Pyjo.Server.WSGI` inherits all events from :mod:`Pyjo.Server`.

Attributes
----------

:mod:`Pyjo.Server.WSGI` inherits all attributes from :mod:`Pyjo.Server`.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Server::PSGI <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Server/PSGI.pm>`_
of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.Content.Single
import Pyjo.IOLoop
import Pyjo.Server
import Pyjo.Transaction

from Pyjo.Util import url_escape

import wsgiref.util

from collections.abc import Iterable, Iterator
from typing import Any, Self
from wsgiref.types import StartResponse, WSGIApplication, WSGIEnvironment


class Pyjo_Server_WSGI(Pyjo.Server.object):
    """
    :mod:`Pyjo.Server.WSGI` inherits all methods from :mod:`Pyjo.Server` and
    implements the following new ones.
    """

    # reportIncompatibleMethodOverride "Method "run" overrides class "Pyjo_Server" in an incompatible manner": the run of
    # Mojo::Server::PSGI takes the environment, as the subclasses of Mojo::Server take what they need
    def run(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, environ: WSGIEnvironment
    ) -> tuple[str, list[tuple[str, str]], Iterable[bytes]]:
        """::

            status, headers, body = wsgi.run(environ)

        Run ``WSGI``: the status, the headers and the body of the response,
        whose ``close`` finishes the transaction.
        """
        env = _environ(environ)
        wsgi_input = environ.get('wsgi.input')

        # Not in Mojolicious: a request body of unknown length, as a server that removes the chunked framing marks it
        body = None
        if not env.get('CONTENT_LENGTH') and wsgi_input is not None and environ.get('wsgi.input_terminated'):
            body = b''
            while chunk := wsgi_input.read(131072):
                body += chunk
            if len(body):
                env['CONTENT_LENGTH'] = str(len(body))

        tx = self.build_tx()
        req = tx.req.parse(env)
        tx.local_port = int(port) if (port := environ.get('SERVER_PORT')) else None
        tx.remote_address = environ.get('REMOTE_ADDR')

        # Request body (may block if we try to read too much)
        if body is not None:
            req.parse(body)
        else:
            length = int(env.get('CONTENT_LENGTH') or 0)
            while not req.is_finished and wsgi_input is not None:
                chunk = wsgi_input.read(length if length and length < 131072 else 131072)
                if not chunk:
                    break
                req.parse(chunk)
                length -= len(chunk)
                if length <= 0:
                    break

        self.emit('request', tx)

        # Response headers
        res = tx.res.fix_headers()
        # Unlike Mojolicious: without the hop-by-hop headers that PEP 3333 forbids, so chunked content goes without its
        # framing, which the server adds
        headers = [(name, value) for name, value in res.headers.to_list() if not wsgiref.util.is_hop_by_hop(name)]

        # WSGI response
        # Unlike Mojolicious: the status of WSGI has its reason phrase
        status = f'{res.code or 404} {res.message or res.default_message()}'
        return status, headers, _IO(tx, tx.is_empty, res.content.is_chunked)

    # Renamed from Mojolicious: to_psgi_app
    def to_wsgi_app(self) -> WSGIApplication:
        """::

            app = wsgi.to_wsgi_app()

        Turn :mod:`Pyjoyment` application into ``WSGI`` application.
        """
        # Preload application and wrap it
        self.app.server(self)

        def application(environ: WSGIEnvironment, start_response: StartResponse) -> Iterable[bytes]:
            status, headers, body = self.run(environ)
            start_response(status, headers)
            return body

        return application


# The body of the response, which the server iterates and closes
class _IO(Iterator[bytes]):
    def __init__(self, tx: Pyjo.Transaction.object, empty: bool, chunked: bool) -> None:
        self._tx = tx
        self._empty = empty
        self._offset = 0
        # Not in Mojolicious: chunked content without its framing
        self._unchunk = _Unchunk() if chunked else None

    def __iter__(self) -> Self:
        return self

    # Renamed from Mojolicious: getline, as the server iterates the body
    def __next__(self) -> bytes:
        # Empty
        if self._empty:
            raise StopIteration

        while True:
            # Not in Mojolicious: no content yet, so the event loop runs once before it tries again, where Mojo
            # returns an empty chunk for the server to try again
            chunk = self._tx.res.get_body_chunk(self._offset)
            if chunk is None:
                Pyjo.IOLoop.one_tick()
                continue

            # End of content
            if not len(chunk):
                raise StopIteration

            self._offset += len(chunk)
            if self._unchunk is not None:
                chunk = self._unchunk.parse(chunk)
            if len(chunk):
                return bytes(chunk)

    # Finish transaction
    def close(self) -> None:
        self._tx.closed()


# Chunked content without its framing, as in Pyjo.Server.ASGI
class _Unchunk:
    def __init__(self) -> None:
        self._chunks: list[bytes] = []
        self._parser = Pyjo.Content.Single.new()
        self._parser.unsubscribe('read').on('read', self._read)
        self._parser.parse(b'Transfer-Encoding: chunked\x0d\x0a\x0d\x0a')

    def _read(self, content: Pyjo.Content.Single.object, chunk: bytes) -> None:
        self._chunks.append(chunk)

    def parse(self, chunk: bytes) -> bytes:
        self._parser.parse(chunk)
        chunks, self._chunks = self._chunks, []
        return b''.join(chunks)


# Not in Mojolicious: the environment of PEP 3333 as the CGI environment that Pyjo.Message.Request parses
def _environ(environ: WSGIEnvironment) -> dict[str, Any]:
    env = dict(environ)

    # A path is bytes as the characters 0-255, which a path of Pyjoyment takes as characters, so the bytes beyond ASCII
    # are percent-encoded, as the path is escaped
    for key in ('PATH_INFO', 'SCRIPT_NAME'):
        if key in env:
            env[key] = url_escape(env[key].encode('latin-1'), rb'\x80-\xff').decode('ascii')

    # The server removes the chunked framing of a request
    env.pop('HTTP_TRANSFER_ENCODING', None)
    return env


new = Pyjo_Server_WSGI.new
object = Pyjo_Server_WSGI
WSGI = Pyjo_Server_WSGI
