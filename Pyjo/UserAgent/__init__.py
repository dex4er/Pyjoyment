# -*- coding: utf-8 -*-

"""
Pyjo.UserAgent - Non-blocking I/O HTTP and WebSocket user agent
===============================================================

::

    import Pyjo.UserAgent

    # Say hello to the Unicode snowman with "Do Not Track" header
    ua = Pyjo.UserAgent.new()
    print(ua.get(u'www.☃.net?hello=there', headers={'DNT': 1}).res.body

    # Form POST with exception handling
    tx = ua.post('https://metacpan.org/search', form={'q': 'pyjo'})
    if tx.success:
        print(tx.res.body)
    else:
        err = tx.error
        if err.code:
            raise Exception('{0} response: {1}'.format(err.code, err.message))
        else:
            raise Exception('Connection error: {0}'.format(err.message))

:mod:`Pyjo.UserAgent` is a full featured non-blocking I/O HTTP.

Classes
-------
"""

import Pyjo.EventEmitter
import Pyjo.IOLoop
import Pyjo.UserAgent.Transactor

from Pyjo.Base import lazy
from Pyjo.Util import getenv, nonlocals, warn

import weakref


DEBUG = getenv('PYJO_USERAGENT_DEBUG', 0)


class Pyjo_UserAgent(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.UserAgent` inherits all attributes and methods from
    :mod:`Pyjo.EventEmitter` and implements the following new ones.
    """

    connect_timeout = lazy(lambda self: getenv('PYJO_CONNECT_TIMEOUT', 10))
    inactivity_timeout = lazy(lambda self: getenv('PYJO_INACTIVITY_TIMEOUT', 30))
    ioloop = Pyjo.IOLoop.new()
    local_address = None
    request_timeout = lazy(lambda self: getenv('PYJO_REQUEST_TIMEOUT', 0))
    transactor = lazy(lambda self: Pyjo.UserAgent.Transactor.new())

    _connections = lazy(lambda self: {})

    def build_tx(self, method, url, **kwargs):
        return self.transactor.tx(method, url, **kwargs)

    def get(self, url, **kwargs):
        """::

            tx = ua.get('example.com')
            tx = ua.get('http://example.com', headers={'Accept': '*/*'}, data='Hi!')
            tx = ua.get('http://example.com', headers={'Accept': '*/*'},
                        form={'a': 'b'})
            tx = ua.get('http://example.com', headers={'Accept': '*/*'},
                        json={'a': 'b'})

        Perform blocking ``GET`` request and return resulting
        :mod:`Pyjo.Transaction.HTTP` object, takes the same arguments as
        :meth:`Pyjo.UserAgent.Transactor.tx` (except for the ``GET`` method, which is
        implied). You can also append a callback to perform requests non-blocking. ::

            def cb(ua, tx):
                print(tx.res.body)

            tx = ua.get('http://example.com', cb=cb)

            if not Pyjo.IOLoop.is_running()
                Pyjo.IOLoop.start()
        """
        return self.start(self.build_tx('GET', url, **kwargs), kwargs.get('cb'))

    def start(self, tx, cb=None):
        # TODO Pyjo.UserAgent.Server nad fork safety

        # Non-blocking
        if cb:
            if DEBUG:
                warn("-- Non-blocking request ({0})\n".format(self._url(tx)))
            return self._start(True, tx, cb)

        # Blocking
        else:
            if DEBUG:
                warn("-- Blocking request ({0})\n".format(self._url(tx)))

            def blocking_cb(ua, tx):
                ua.ioloop.stop()

            self._start(False, tx, blocking_cb)
            self.ioloop.start()
            return tx

    def _connect(self, nb, peer, tx, handle, cb):
        t = self.transactor
        proto, host, port = t.peer(tx) if peer else t.endpoint(tx)
        options = {'address': host, 'port': port, 'timeout': self.connect_timeout}
        local = self.local_address
        if local:
            options['local_address'] = local
        if handle:
            options['handle'] = handle

        # TODO SOCKS
        # TODO TLS
        connect_vars = nonlocals()
        connect_vars.cb = cb
        connect_vars.ua = weakref.proxy(self)

        def client_cb(loop, err, stream):
            cb = connect_vars.cb
            cid = connect_vars.cid
            ua = connect_vars.ua

            # Connection error
            if not ua:
                return

            if err:
                return ua._error(cid, err)

            # Connection established
            stream.on(lambda ua: self._error(cid, 'Inactivity timeout'), 'timeout')
            stream.on(lambda ua: ua and self._finish(cid, True), 'close')
            stream.on(lambda ua, err: ua and self._error(cid, err), 'error')
            stream.on(lambda ua, chunk: self._read(cid, chunk), 'read')
            cb(cid)

        cid = self._loop(nb).client(client_cb, **options)
        connect_vars.cid = cid
        return cid

    def _connected(self, cid):
        # Inactivity timeout
        c = self._connections[cid]
        stream = self._loop(c['nb']).stream(cid).set(timeout=self.inactivity_timeout)

        # Store connection information in transaction
        tx = c['tx']
        tx.connection = cid
        handle = stream.handle
        tx.local_address, tx.local_port = handle.getsockname()
        tx.remove_address, tx.remote_port = handle.getpeername()

        # Start writing
        self = weakref.proxy(self)
        tx.on(lambda ua: self._write(cid), 'resume')
        self._write(cid)

    def _connection(self, nb, tx, cb):
        # TODO Reuse connection
        # Reuse connection
        cid = tx.connection
        proto, host, port = self.transactor.endpoint(tx)
        # TODO CONNECT request to proxy required

        # Connect
        if DEBUG:
            warn("-- Connect ({0}://{1}:{2})\n".format(proto, host, port))
        cid = self._connect(nb, True, tx, cid, self._connected)
        self._connections[cid] = {'cb': cb, 'nb': nb, 'tx': tx, 'writing': False}

        return cid

    def _error(self, cid, err):
        ...

    def _finish(self, cid, close):
        ...

    def _loop(self, nb):
        if nb:
            return Pyjo.IOLoop.singleton()
        else:
            return self.ioloop

    def _read(self, cid, chunk):
        # Corrupted connection
        if cid not in self._connections:
            return

        c = self._connections[cid]

        if not c:
            del self._connections[cid]
            return

        tx = c['tx']

        if not tx:
            return self._remove(cid)

        # Process incoming data
        if DEBUG:
            warn("-- Client <<< Server ({0})\n{1}\n".format(self._url(tx), str(chunk)))

        tx.client_read(chunk)
        if tx.is_finished:
            self._finish(cid, False)
        elif tx.is_writing:
            self._write(cid)

    def _start(self, nb, tx, cb):
        # TODO Application server
        # TODO proxy, cookiejar

        # Connect and add request timeout if necessary
        cid = self.emit('start', tx)._connection(nb, tx, cb)
        timeout = self.request_timeout
        if timeout:
            self.connections[id][timeout] = self._loop(nb) \
                .timer(lambda loop: self._error(cid, 'Request timeout'), timeout)

        return cid

    def _url(self, tx):
        return tx.req.url.to_abs()

    def _write(self, cid):
        # Get and write chunk
        if cid not in self._connections:
            return

        c = self._connections[cid]

        if not c:
            return

        tx = c['tx']

        if not tx:
            return

        if not tx.is_writing:
            return

        if c['writing']:
            return

        c['writing'] = True
        chunk = tx.client_write()
        c['writing'] = False
        if DEBUG:
            warn("-- Client >>> Server ({0})\n{1}\n".format(self._url(tx), str(chunk)))

        stream = self._loop(c['nb']).stream(cid).write(chunk)
        if tx.is_finished:
            self._finish(cid)

        # Continue writing
        if not tx.is_writing:
            return

        self = weakref.proxy(self)
        stream.write(b'', cb=lambda ua: self._write(cid))


new = Pyjo_UserAgent.new
object = Pyjo_UserAgent  # @ReservedAssignment
