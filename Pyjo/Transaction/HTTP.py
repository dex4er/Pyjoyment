"""
Pyjo.Transaction.HTTP - HTTP transaction
========================================
::

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

:mod:`Pyjo.Transaction.HTTP` is a container for HTTP transactions based on
:rfc:`7230` and
:rfc:`7231`.

Events
------

:mod:`Pyjo.Transaction.HTTP` inherits all events from :mod:`Pyjo.Transaction` and
can emit the following new ones.

request
~~~~~~~
::

    @tx.on
    def request(tx):
        ...

Emitted when a request is ready and needs to be handled. ::

    @tx.on
    def request(tx):
        tx.res.headers.header('X-Bender', 'Bite my shiny metal ass!')

unexpected
~~~~~~~~~~
::

    @tx.on
    def unexpected(tx, res):
        ...

Emitted for unexpected ``1xx`` responses that will be ignored. ::

    @tx.on
    def unexpected(tx, res):
        @tx.res.on
        def finish():
            print('Follow-up response is finished.')

upgrade
~~~~~~~
::

    @tx.on
    def upgrade(tx, ws):
        ...

Emitted when transaction gets upgraded to a :mod:`Pyjo.Transaction.WebSocket`
object. ::

    @tx.on
    def upgrade(tx, ws):
        ws.res.headers.header('X-Bender', 'Bite my shiny metal ass!')

Classes
-------
"""

import Pyjo.Transaction.WebSocket

from Pyjo.Util import notnone


class Pyjo_Transaction_HTTP(Pyjo.Transaction.object):
    """
    :mod:`Pyjo.Transaction.HTTP` inherits all attributes and methods from
    :mod:`Pyjo.Transaction` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.previous = kwargs.get('previous')
        """::

            previous = tx.previous
            tx.previous = Pyjo.Transaction.HTTP.new()

        Previous transaction that triggered this follow-up transaction, usually a
        :mod:`Pyjo.Transaction.HTTP` object. ::

            # Paths of previous requests
            print(tx.previous.previous.req.url.path)
            print(tx.previous.req.url.path)
        """

        self._delay = False
        self._handled = False
        self._http_state = None
        self._offset = None
        self._state = None
        self._towrite = None

    def client_read(self, chunk):
        """::

            tx.client_read(chunk)

        Read data client-side, used to implement user agents.
        """
        # Skip body for HEAD request
        res = self.res
        if self.req.method.upper() == 'HEAD':
            res.content.skip_body = True
        if not res.parse(chunk).is_finished:
            return

        # Unexpected 1xx response
        if not res.is_status_class(100) or res.headers.upgrade:
            self._state = 'finished'
            return

        self.res(res.new()).emit('unexpected', res)
        leftovers = res.content.leftovers()
        if not len(leftovers):
            return
        self.client_read(leftovers)

    def client_write(self):
        """::

            chunk = tx.client_write

        Write data client-side, used to implement user agents.
        """
        return self._write(False)

    @property
    def is_empty(self):
        """::

            boolean = tx.is_empty

        Check transaction for ``HEAD`` request and ``1xx``, ``204`` or ``304`` response.
        """
        return bool(self.req.method.upper() == 'HEAD' or self.res.is_empty)

    @property
    def keep_alive(self):
        """::

            boolean = tx.keep_alive

        Check if connection can be kept alive.
        """
        # Close
        req = self.req
        res = self.res
        req_conn = notnone(req.headers.connection, '').lower()
        res_conn = notnone(res.headers.connection, '').lower()
        if req_conn == 'close' or res_conn == 'close':
            return False

        # Keep-alive is optional for 1.0
        if res.version == '1.0':
            return res_conn == 'keep-alive'
        if req.version == '1.0':
            return req_conn == 'keep-alive'

        # Keep-alive is the default for 1.1
        return True

    @property
    def redirects(self):
        """::

            redirects = tx.redirects

        Return a list of all previous transactions that preceded this follow-up
        transaction. ::

            # Paths of all previous requests
            for redir in tx.redirects:
                print(redir.req.url.path)
        """
        redirects = []
        previous = self
        while True:
            previous = previous.previous
            if not previous:
                break
            redirects.insert(0, previous)
        return redirects

    def server_read(self, chunk):
        """::

            tx.server_read(chunk)

        Read data server-side, used to implement web servers.
        """
        # Parse request
        req = self.req
        if not req.error:
            req.parse(chunk)
        if self._state is None:
            self._state = 'read'

        # Generate response
        if not req.is_finished or self._handled:
            return

        # Pyjo.Transaction.WebSocket
        if req.is_handshake:
            self.emit('upgrade', Pyjo.Transaction.WebSocket.new(handshake=self))

        self.emit('request')

    def server_write(self):
        """::

            chunk = tx.server_write()

        Write data server-side, used to implement web servers.
        """
        return self._write(True)

    def _body(self, msg, finish):
        # Prepare body chunk
        buf = msg.get_body_chunk(self._offset)

        if buf is not None:
            written = len(buf)
        else:
            written = 0

        if msg.content.is_dynamic:
            self._towrite = 1
        else:
            self._towrite = self._towrite - written

        self._offset += written

        if buf is not None:
            self._delay = False

        # Delayed
        else:
            if self._delay:
                self._delay = False
                self._state = 'paused'
            else:
                self._delay = True

        # Finished
        if self._towrite <= 0 or buf is not None and not len(buf):
            if finish:
                self._state = 'finished'
            else:
                self._state = 'read'

        if buf is not None:
            return buf
        else:
            return b''

    def _headers(self, msg, head):
        # Prepare header chunk
        buf = msg.get_header_chunk(self._offset)
        written = len(buf) if buf is not None else 0
        self._towrite -= written
        self._offset += written

        # Switch to body
        if self._towrite <= 0:
            self._offset = 0

            # Response without body
            if head and self.is_empty:
                self._state = 'finished'

            # Body
            else:
                self._http_state = 'body'
                self._towrite = 1 if msg.content.is_dynamic else msg.body_size

        return buf

    def _start_line(self, msg):
        # Prepare start-line chunk
        buf = msg.get_start_line_chunk(self._offset)
        written = len(buf) if buf is not None else 0
        self._towrite -= written
        self._offset += written

        # Switch to headers
        if self._towrite <= 0:
            self._http_state = 'headers'
            self._towrite = msg.header_size
            self._offset = 0

        return buf

    def _write(self, server):
        # Client starts writing right away
        if not server and self._state is None:
            self._state = 'write'

        if self._state != 'write':
            return ''

        # Nothing written yet
        if self._offset is None:
            self._offset = 0
        if self._towrite is None:
            self._towrite = 0

        if server:
            msg = self.res
        else:
            msg = self.req

        if not self._http_state:
            # Connection header
            headers = msg.headers
            if not headers.connection:
                headers.connection = 'keep-alive' if self.keep_alive else 'close'

            # Switch to start-line
            self._http_state = 'start_line'
            self._written = msg.start_line_size

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
