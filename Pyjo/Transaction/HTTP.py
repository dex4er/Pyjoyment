r"""
Pyjo.Transaction.HTTP - HTTP transaction
========================================
::

    from Pyjo.Transaction.HTTP import HTTP

    # Client
    tx = HTTP()
    tx.req.method = 'GET'
    tx.req.url.parse('http://example.com')
    tx.req.headers.accept = 'application/json'
    print(tx.res.code)
    print(tx.res.headers.content_type)
    print(tx.res.body)
    print(tx.remote_address)

    import Pyjo.Transaction.HTTP

    # Client
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.method = 'GET'
    tx.req.url.parse('http://example.com')
    tx.req.headers.accept = 'application/json'
    print(tx.res.code)
    print(tx.res.headers.content_type)
    print(tx.res.body)
    print(tx.remote_address)

    # Server
    tx = Pyjo.Transaction.HTTP.new()
    print(tx.req.method)
    print(tx.req.url.to_abs())
    print(tx.req.headers.accept)
    print(tx.remote_address)
    tx.res.code = 200
    tx.res.headers.content_type = 'text/plain'
    tx.res.body = b'Hello World!'

:mod:`Pyjo.Transaction.HTTP` is a container for HTTP transactions, based on
`RFC 7230 <https://tools.ietf.org/html/rfc7230>`_ and
`RFC 7231 <https://tools.ietf.org/html/rfc7231>`_.

The end of a ``with`` block resumes the transaction with
:meth:`~Pyjo_Transaction_HTTP.resume`, so that a server writes the response
that the block prepares. An exception that the block does not catch ends it
with the default error: the response is replaced with a
``500 Internal Server Error``, which is resumed, and the exception goes to
``sys.stderr`` as a warning, so that the server writes the response. ::

    # Server
    with tx:
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = b'Hello World!'

Events
------

:mod:`Pyjo.Transaction.HTTP` inherits all events from :mod:`Pyjo.Transaction`
and can emit the following new ones.

request
~~~~~~~
::

    tx.on('request', lambda tx: ...)

Emitted when a request is ready and needs to be handled. ::

    tx.on('request', lambda tx: tx.res.headers.header('X-Bender', 'Bite my shiny metal ass!'))

resume
~~~~~~
::

    tx.on('resume', lambda tx: ...)

Emitted when transaction is resumed.

unexpected
~~~~~~~~~~
::

    tx.on('unexpected', lambda tx, res: ...)

Emitted for unexpected ``1xx`` responses that will be ignored. ::

    tx.on('unexpected', lambda tx, res: tx.res.on('finish', lambda res: print('Follow-up response is finished.')))

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Transaction::HTTP <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Transaction/HTTP.pm>`_
of Mojolicious 9.49.
"""

import Pyjo.Exception
import Pyjo.Message
import Pyjo.Message.Response
import Pyjo.Transaction

from Pyjo.Util import warn

from types import TracebackType
from typing import Any, Self


class Pyjo_Transaction_HTTP(Pyjo.Transaction.object):
    """
    :mod:`Pyjo.Transaction.HTTP` inherits all methods from
    :mod:`Pyjo.Transaction` and implements the following new ones.
    """

    def __init__(self, *, previous: 'Pyjo_Transaction_HTTP | None' = None, **kwargs: Any) -> None:
        """::

            tx = Pyjo.Transaction.HTTP.new()
            tx = Pyjo.Transaction.HTTP.new(req=Pyjo.Message.Request.new())

        Construct a new :mod:`Pyjo.Transaction.HTTP` object.
        """
        super().__init__(**kwargs)

        self.previous = previous
        """::

            previous = tx.previous
            tx.previous = Pyjo.Transaction.HTTP.new()

        Previous transaction that triggered this follow-up transaction, usually
        a :mod:`Pyjo.Transaction.HTTP` object. ::

            # Paths of previous requests
            print(tx.previous.previous.req.url.path)
            print(tx.previous.req.url.path)
        """

        # The state of the reader and of the writer, as the keys of Mojo's hash
        self._handled = False
        self._http_state: str | None = None
        self._offset = 0
        self._write = 0
        self._writing: bool | None = None

    def client_read(self, chunk: bytes) -> Self | None:
        """::

            tx.client_read(data)

        Read data client-side, used to implement user agents such as
        :mod:`Pyjo.UserAgent`.
        """
        # Skip body for HEAD request
        res = self.res
        if self.req.method.upper() == 'HEAD':
            res.content.skip_body = True
        if not res.parse(chunk).is_finished:
            return None

        # Unexpected 1xx response
        if not res.is_info or res.headers.upgrade:
            return self.completed()
        self.res = res.new()
        self.emit('unexpected', res)
        if not len(leftovers := res.content.leftovers()):
            return None
        return self.client_read(leftovers)

    def client_write(self) -> bytes:
        """::

            data = tx.client_write()

        Write data client-side, used to implement user agents such as
        :mod:`Pyjo.UserAgent`.
        """
        return self._write_chunk(False)

    @property
    def is_empty(self) -> bool:
        """::

            boolean = tx.is_empty

        Check transaction for ``HEAD`` request and ``1xx``, ``204`` or ``304``
        response.
        """
        return self.req.method.upper() == 'HEAD' or self.res.is_empty

    @property
    def keep_alive(self) -> bool:
        """::

            boolean = tx.keep_alive

        Check if connection can be kept alive.
        """
        # Close
        req, res = self.req, self.res
        req_conn = (req.headers.connection or '').lower()
        res_conn = (res.headers.connection or '').lower()
        if req_conn == 'close' or res_conn == 'close':
            return False

        # Keep-alive is optional for 1.0
        if res.version == '1.0':
            return res_conn == 'keep-alive'
        if req.version == '1.0':
            return req_conn == 'keep-alive'

        # Keep-alive is the default for 1.1
        return True

    def redirects(self) -> list['Pyjo_Transaction_HTTP']:
        """::

            redirects = tx.redirects()

        Return a list with all previous transactions that preceded this
        follow-up transaction. ::

            # Paths of all previous requests
            for previous in tx.redirects():
                print(previous.req.url.path)
        """
        redirects: list[Pyjo_Transaction_HTTP] = []
        previous = self
        while previous := previous.previous:
            redirects.insert(0, previous)
        return redirects

    def resume(self) -> Self:
        """::

            tx = tx.resume()

        Resume transaction.
        """
        self._writing = True
        return self.emit('resume')

    # Not in Mojolicious: a context manager, which resumes the transaction where the block ends, as a handler of a
    # server ends with a call of resume, with the default error after an exception, which it does not pass on, as the
    # server writes the response after the handler returns
    def __enter__(self) -> Self:
        return self

    def __exit__(
        self, type: type[BaseException] | None, value: BaseException | None, traceback: TracebackType | None
    ) -> bool:
        error = isinstance(value, Exception)
        if error:
            warn(str(Pyjo.Exception.new(value)))
            res = self.res = Pyjo.Message.Response.new()
            res.code = 500
            res.headers.content_type = 'text/plain;charset=UTF-8'
            res.body = b'Internal Server Error'
        self.resume()
        return error

    def server_read(self, chunk: bytes) -> None:
        """::

            tx.server_read(data)

        Read data server-side, used to implement web servers such as
        :mod:`Pyjo.Server.Daemon`.
        """
        # Parse request
        req = self.req
        if not req.error:
            req.parse(chunk)

        # Generate response
        if req.is_finished and not self._handled:
            self._handled = True
            self.emit('request')

    def server_write(self) -> bytes:
        """::

            data = tx.server_write()

        Write data server-side, used to implement web servers such as
        :mod:`Pyjo.Server.Daemon`.
        """
        return self._write_chunk(True)

    def _body(self, msg: Pyjo.Message.object, finish: bool) -> bytes:
        # Prepare body chunk
        buffer = msg.get_body_chunk(self._offset)
        self._offset += len(buffer) if buffer is not None else 0

        # Delayed
        if buffer is None:
            self._writing = False

        # Finished
        elif not len(buffer):
            if finish:
                self.completed()
            else:
                self._writing = False

        return buffer if buffer is not None else b''

    def _headers(self, msg: Pyjo.Message.object, head: bool) -> bytes:
        # Prepare header chunk
        buffer = msg.get_header_chunk(self._offset)
        written = len(buffer)
        self._write -= written
        self._offset += written

        # Switch to body
        if self._write <= 0:
            self._http_state, self._offset = 'body', 0

            # Response without body
            if head and self.is_empty:
                self.completed()._http_state = 'empty'

        return buffer

    def _start_line(self, msg: Pyjo.Message.object) -> bytes:
        # Prepare start-line chunk
        buffer = msg.get_start_line_chunk(self._offset)
        written = len(buffer)
        self._write -= written
        self._offset += written

        # Switch to headers
        if self._write <= 0:
            self._http_state, self._write, self._offset = 'headers', msg.header_size, 0

        return buffer

    # Renamed from Mojolicious: _write, the attribute _write is the size left to write
    def _write_chunk(self, server: bool) -> bytes:
        # Client starts writing right away
        if self._writing is None and not server:
            self._writing = True
        if not self._writing:
            return b''

        # Nothing written yet
        msg = self.res if server else self.req
        if not self._http_state:
            self._http_state, self._write = 'start_line', msg.start_line_size

        # Start-line
        chunk = b''
        if self._http_state == 'start_line':
            chunk += self._start_line(msg)

        # Headers
        if self._http_state == 'headers':
            chunk += self._headers(msg, server)

        # Body
        if self._http_state == 'body':
            chunk += self._body(msg, server)

        return chunk


new = Pyjo_Transaction_HTTP.new
object = Pyjo_Transaction_HTTP
HTTP = Pyjo_Transaction_HTTP
