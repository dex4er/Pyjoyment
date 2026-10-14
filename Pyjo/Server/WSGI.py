"""
Pyjo.Server.WSGI - WSGI server
==============================
::

    import Pyjo.Server.WSGI

    from wsgiref.simple_server import make_server

    wsgi = Pyjo.Server.WSGI.new()
    wsgi.unsubscribe('request')

    @wsgi.on
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

    httpd = make_server('', 3000, app)
    httpd.serve_forever()

:mod:`Pyjo.Server.WSGI` allows :mod:`Pyjoyment` applications to run on all ``WSGI``
compatible servers.

The response is given in the ``request`` event, as ``WSGI`` is synchronous;
its content can come later, as the event loop of :mod:`Pyjo.IOLoop` runs
while the server waits for it. The request is read from the environment of
:pep:`3333` with ``read``, a body of unknown length when the server sets
``wsgi.input_terminated``, as for a chunked request. The response goes
without the hop-by-hop headers that :pep:`3333` forbids, so chunked content is
sent without its framing, which the server adds.

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

Classes
-------
"""

import Pyjo.Content.Single
import Pyjo.IOLoop
import Pyjo.Server

from Pyjo.Util import url_escape

import wsgiref.util


class Pyjo_Server_WSGI(Pyjo.Server.object):
    """
    :mod:`Pyjo.Server.WSGI` inherits all attributes and methods from
    :mod:`Pyjo.Server` and implements the following new ones.
    """

    def run(self, environ):
        """::

            status, headers, body = wsgi.run(environ)

        Run ``WSGI``.
        """
        env = _environ(environ)
        wsgi_input = environ.get('wsgi.input')

        # Not in Mojolicious: a request body of unknown length, as a server that removes the chunked framing marks it
        body = None
        if 'CONTENT_LENGTH' not in env and wsgi_input is not None and environ.get('wsgi.input_terminated'):
            body = b''
            while chunk := wsgi_input.read(131072):
                body += chunk
            if len(body):
                env['CONTENT_LENGTH'] = str(len(body))

        tx = self.build_tx()
        req = tx.req.parse(env)
        tx.local_port = int(port) if (port := environ.get('SERVER_PORT')) else None
        tx.remote_address = environ.get('REMOTE_ADDR', None)

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

        # Response headers, without the hop-by-hop headers that PEP 3333 forbids, so chunked content goes without its
        # framing, which the server adds
        res = tx.res.fix_headers()
        status = f'{res.code or 404} {res.message or res.default_message()}'
        chunked = res.content.is_chunked
        headers = [(name, value) for name, value in res.headers.to_list() if not wsgiref.util.is_hop_by_hop(name)]

        # WSGI response
        return status, headers, self._body(tx, tx.is_empty, chunked)

    def to_wsgi_app(self):
        """::

            app = wsgi.to_wsgi_app()

        Turn the application into a ``WSGI`` application.
        """
        # Preload application and wrap it
        self.app

        def application(environ, start_response):
            status, headers, body = self.run(environ)
            start_response(status, headers)
            return body

        return application

    def _body(self, tx, empty, chunked):
        # The end of the iteration closes the transaction, as close of the PSGI body does
        try:
            # Empty
            if empty:
                return

            unchunk = _Unchunk() if chunked else None
            offset = 0
            while True:
                # Not in Mojolicious: no content yet, so the event loop runs once before it tries again, where Mojo
                # tries again at once
                chunk = tx.res.get_body_chunk(offset)
                if chunk is None:
                    Pyjo.IOLoop.one_tick()
                    continue

                # End of content
                if not len(chunk):
                    return

                offset += len(chunk)
                if unchunk is not None:
                    chunk = unchunk.parse(chunk)
                if len(chunk):
                    yield bytes(chunk)
        finally:
            tx.closed()


# Chunked content without its framing, as in Pyjo.Server.ASGI
class _Unchunk:
    def __init__(self):
        self._chunks = []
        self._parser = Pyjo.Content.Single.new()
        self._parser.unsubscribe('read').on('read', lambda content, chunk: self._chunks.append(chunk))
        self._parser.parse(b'Transfer-Encoding: chunked\x0d\x0a\x0d\x0a')

    def parse(self, chunk):
        self._parser.parse(chunk)
        chunks, self._chunks = self._chunks, []
        return b''.join(chunks)


# The environment of PEP 3333 as the CGI environment that Pyjo.Message.Request parses
def _environ(environ):
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
