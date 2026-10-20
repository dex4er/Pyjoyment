"""
Pyjo.Server.CGI - CGI server
============================
::

    from Pyjo.Server.CGI import CGI

    cgi = CGI()


    @cgi.unsubscribe('request').on('request')
    def request(cgi, tx):
        # Request
        method = tx.req.method
        path = tx.req.url.path

        # Response
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = f'{method} request for {path}!'.encode()

        # Resume transaction
        tx.resume()


    cgi.run()

    # Or import the module, as in Google Python Style Guide

    import Pyjo.Server.CGI

    cgi = Pyjo.Server.CGI.new()


    @cgi.unsubscribe('request').on('request')
    def request(cgi, tx):
        # Request
        method = tx.req.method
        path = tx.req.url.path

        # Response
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = f'{method} request for {path}!'.encode()

        # Resume transaction
        tx.resume()


    cgi.run()

:mod:`Pyjo.Server.CGI` is a simple and portable implementation of
:rfc:`3875`.

The content of the response can come later, as the event loop of
:mod:`Pyjo.IOLoop` runs while the script waits for it. The request body is
read with the length of ``CONTENT_LENGTH``, so a chunked request, which has
none, reaches the application without its body.

CGI servers
-----------

* uWSGI with its plugin ``cgi``: a chunked request is not answered.
* :mod:`http.server` with ``--cgi``, up to Python 3.14: it sends the output of
  the script as it is, after a status line ``200`` and headers of its own,
  so the status of the response is lost, and the ``Status`` header and the
  ``Date`` header of the script reach the client.

Events
------

:mod:`Pyjo.Server.CGI` inherits all events from :mod:`Pyjo.Server`.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Server::CGI <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Server/CGI.pm>`_
of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.IOLoop
import Pyjo.Message.Response
import Pyjo.Server

import os
import sys

from typing import Any, BinaryIO, cast


class Pyjo_Server_CGI(Pyjo.Server.object):
    """
    :mod:`Pyjo.Server.CGI` inherits all methods from :mod:`Pyjo.Server` and
    implements the following new ones.
    """

    def __init__(self, *, nph: bool | None = None, **kwargs: Any) -> None:
        """::

            cgi = Pyjo.Server.CGI.new()
            cgi = Pyjo.Server.CGI.new(nph=True)

        Construct a new :mod:`Pyjo.Server.CGI` object.
        """
        super().__init__(**kwargs)

        self.nph = nph
        """::

            boolean = cgi.nph
            cgi.nph = boolean

        Activate non-parsed header mode.
        """

    def run(self) -> int | None:
        """::

            status = cgi.run()

        Run CGI.
        """
        self.app.server(self)
        tx = self.build_tx()
        req = tx.req.parse(dict(os.environ))
        tx.local_port = int(port) if (port := os.environ.get('SERVER_PORT')) else None
        tx.remote_address = os.environ.get('REMOTE_ADDR')

        # Request body (may block if we try to read too much)
        stdin = cast(BinaryIO, sys.stdin.buffer)
        length = int(req.headers.content_length or 0)
        while not req.is_finished:
            chunk = stdin.read(length if length and length < 131072 else 131072)
            if not chunk:
                break
            req.parse(chunk)
            length -= len(chunk)
            if length <= 0:
                break

        self.emit('request', tx)

        # Response start-line
        res = tx.res.fix_headers()
        if self.nph and not _write(res, 'get_start_line_chunk'):
            return None

        # Response headers
        code = res.code or 404
        msg = res.message or res.default_message()
        if not self.nph:
            res.headers.status = f'{code} {msg}'
        if not _write(res, 'get_header_chunk'):
            return None

        # Response body
        if not tx.is_empty and not _write(res, 'get_body_chunk'):
            return None

        # Finish transaction
        tx.closed()

        return res.code


def _write(res: Pyjo.Message.Response.object, method: str) -> bool:
    # Text written to sys.stdout before goes first
    sys.stdout.flush()
    stdout = cast(BinaryIO, sys.stdout.buffer)
    offset = 0
    while True:
        # Not in Mojolicious: no chunk yet, so the event loop runs once before it tries again, where Mojo sleeps for a
        # second
        chunk: bytes | None = getattr(res, method)(offset)
        if chunk is None:
            Pyjo.IOLoop.one_tick()
            continue

        # End of part
        if not (length := len(chunk)):
            break

        # Make sure we can still write
        offset += length
        if stdout.closed:
            return False
        stdout.write(chunk)
        stdout.flush()

    return True


new = Pyjo_Server_CGI.new
object = Pyjo_Server_CGI
CGI = Pyjo_Server_CGI
