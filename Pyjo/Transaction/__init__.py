"""
Pyjo.Transaction - Transaction base class
=========================================
::

    import Pyjo.Transaction

    class MyTransaction(Pyjo.Transaction.object):

        def client_read(self, chunk):
            ...

        def client_write(self):
            ...

        def server_read(self, chunk):
            ...

        def server_write(self):
            ...

:mod:`Pyjo.Transaction` is an abstract base class for transactions.

Events
------

:mod:`Pyjo.Transaction` inherits all events from :mod:`Pyjo.EventEmitter` and can
emit the following new ones.

connection
~~~~~~~~~~
::

    @tx.on
    def connection(tx, connection):
        ...

Emitted when a connection has been assigned to transaction.

finish
~~~~~~
::

    @tx.on
    def finish(tx):
        ...

Emitted when transaction is finished.

resume
~~~~~~
::

    @tx.on
    def resume(tx):
        ...

Emitted when transaction is resumed.

Classes
-------
"""

import Pyjo.EventEmitter
import Pyjo.Message.Request
import Pyjo.Message.Response

from Pyjo.Regexp import r
from Pyjo.Util import not_implemented, notnone


re_x_forwarded_for = r(r'([^,\s]+)$')


class Pyjo_Transaction(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.Transaction` inherits all attributes and methods from
    :mod:`Pyjo.EventEmitter` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        super().__init__()

        self.kept_alive = kwargs.get('kept_alive')
        """::

            kept_alive = tx.kept_alive
            tx.kept_alive = True

        Connection has been kept alive.
        """

        self.local_address = kwargs.get('local_address')
        """::

            address = tx.local_address
            tx.local_address = '127.0.0.1'

        Local interface address.
        """

        self.local_port = kwargs.get('local_port')
        """::

            port = tx.local_port
            tx.local_port = 8080

        Local interface port.
        """

        self.original_remote_address = kwargs.get('original_remote_address')
        """::

            address = tx.original_remote_address
            tx.original_remote_address = '127.0.0.1'

        Remote interface address.
        """

        self.remote_port = kwargs.get('remote_port')
        """::

            port = tx.remote_port
            tx.remote_port = 8081

        Remote interface port.
        """

        self.req = notnone(kwargs.get('req'), lambda: Pyjo.Message.Request.new())
        """::

            req = tx.req
            tx.req = Pyjo.Message.Request.new()

        HTTP request, defaults to a :mod:`Pyjo.Message.Request` object.
        """

        self.res = notnone(kwargs.get('res'), lambda: Pyjo.Message.Response.new())
        """::

            res = tx.res
            tx.res = Pyjo.Message.Response.new()

        HTTP response, defaults to a :mod:`Pyjo.Message.Response` object.
        """

        self._connection = None
        self._state = None

    def client_close(self, close=False):
        """::

            tx.client_close()
            tx.client_close(True)

        Transaction closed client-side, no actual connection close is assumed by
        default, used to implement user agents.
        """
        # Premature connection close
        res = self.res.finish()
        if close and not res.code and not res.error:
            res.error = {'message': 'Premature connection close'}

        # 4xx/5xx
        elif res.is_error:
            res.error = {'message': res.message, 'code': res.code}

        return self.server_close()

    @not_implemented
    def client_read(self, chunk):
        """::

            tx.client_read(chunk)

        Read data client-side, used to implement user agents. Meant to be overloaded in
        a subclass.
        """
        pass

    @not_implemented
    def client_write(self):
        """::

            chunk = tx.client_write

        Write data client-side, used to implement user agents. Meant to be overloaded
        in a subclass.
        """
        pass

    @property
    def connection(self):
        """::

            cid = tx.connection
            tx.connection = cid

        Connection identifier.
        """
        return self._connection

    @connection.setter
    def connection(self, value):
        self._connection = value
        self.emit('connection', value)

    @property
    def error(self):
        """::

            err = tx.error

        Get request or response error and return ``None`` if there is no error,
        commonly used together with :attr:`success`. ::

            # Longer version
            err = tx.req.error or tx.res.error

            # Check for different kinds of errors
            err = tx.error
            if err:
                if err['code']:
                    raise Exception("{code} response: {message}".format(**err))
                else:
                    raise Exception("Connection error: {message}".format(**err))
        """
        return self.req.error or self.res.error

    @property
    def is_finished(self):
        """::

            bool = tx.is_finished

        Check if transaction is finished.
        """
        return self._state == 'finished'

    @property
    def is_websocket(self):
        """::

            false = tx.is_websocket

        False.
        """
        return False

    @property
    def is_writing(self):
        """::

            boolean = tx.is_writing

        Check if transaction is writing.
        """
        if self._state is None:
            return True
        else:
            return self._state == 'write'

    @property
    def remote_address(self):
        """::

            address = tx.remote_address
            tx.remote_address = '127.0.0.1'

        Same as :attr:`original_remote_address` or the last value of the
        ``X-Forwarded-For`` header if :attr:`req` has been performed through a reverse
        proxy.
        """
        if not self.req.reverse_proxy:
            return self.original_remote_address

        # Reverse proxy
        x_forwarded_for = notnone(self.req.headers.header('X-Forwarded-For'), '')
        m = re_x_forwarded_for.search(x_forwarded_for)
        if m:
            return m.group(1)
        else:
            return self.original_remote_address

    @remote_address.setter
    def remote_address(self, value):
        self.original_remote_address = value

    def resume(self):
        """::

            tx = tx.resume

        Resume transaction.
        """
        return self._set_state('write', 'resume')

    def server_close(self):
        """::

            tx.server_close

        Transaction closed server-side, used to implement web servers.
        """
        return self._set_state('finished', 'finish')

    @not_implemented
    def server_read(self, chunk):
        """::

            tx.server_read(chunk)

        Read data server-side, used to implement web servers. Meant to be overloaded in
        a subclass.
        """
        pass

    @not_implemented
    def server_write(self):
        """::

            chunk = tx.server_write()

        Write data server-side, used to implement web servers. Meant to be overloaded
        in a subclass.
        """
        pass

    @property
    def success(self):
        """::

            res = tx.success

        Returns the :mod:`Pyjo.Message.Response` object from :attr:`res` if transaction was
        successful or ``None`` otherwise. Connection and parser errors have only a
        message in :attr:`error`, 400 and 500 responses also a code. ::

            # Sensible exception handling
            res = tx.success
            if res:
                print(res.body)
            else:
                err = tx.error
                if err['code']:
                    raise Exception("{code} response: {message}".format(**err))
                else:
                    raise Exception("Connection error: {message}".format(**err))
        """
        if self.error:
            return None
        else:
            return self.res

    def _set_state(self, state, event):
        self._state = state
        return self.emit(event)


new = Pyjo_Transaction.new
object = Pyjo_Transaction
