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
import Pyjo.UserAgent.CookieJar
import Pyjo.UserAgent.Proxy
import Pyjo.UserAgent.Transactor

from Pyjo.Util import getenv, isalive, notnone, warn

import weakref


DEBUG = getenv('PYJO_USERAGENT_DEBUG', 0)


class Pyjo_UserAgent(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.UserAgent` inherits all attributes and methods from
    :mod:`Pyjo.EventEmitter` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        super().__init__()

        self.ca = notnone(kwargs.get('ca'), lambda: getenv('PYJO_CA_FILE'))
        self.cert = notnone(kwargs.get('cert'), lambda: getenv('PYJO_CERT_FILE'))
        self.connect_timeout = notnone(kwargs.get('connect_timeout'), lambda: getenv('PYJO_CONNECT_TIMEOUT', 10))
        self.cookie_jar = notnone(kwargs.get('cookie_jar'), lambda: Pyjo.UserAgent.CookieJar.new())
        self.inactivity_timeout = notnone(
            kwargs.get('inactivity_timeout'), lambda: getenv('PYJO_INACTIVITY_TIMEOUT', 30)
        )
        self.ioloop = notnone(kwargs.get('ioloop'), lambda: Pyjo.IOLoop.new())
        self.key = notnone(kwargs.get('key'), lambda: getenv('PYJO_KEY_FILE'))
        self.local_address = kwargs.get('local_address')
        self.max_connections = kwargs.get('max_connections', 5)
        self.max_redirects = notnone(kwargs.get('max_redirects'), lambda: getenv('PYJO_MAX_REDIRECTS', 0))
        self.request_timeout = notnone(kwargs.get('request_timeout'), lambda: getenv('PYJO_REQUEST_TIMEOUT', 0))
        self.proxy = notnone(kwargs.get('proxy'), lambda: Pyjo.UserAgent.Proxy.new())
        self.transactor = notnone(kwargs.get('transactor'), lambda: Pyjo.UserAgent.Transactor.new())

        self._connections = {}
        self._nb_queue = []
        self._queue = []

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

            if not Pyjo.IOLoop.is_running
                Pyjo.IOLoop.start()
        """
        return self.start(self.build_tx('GET', url, **kwargs), kwargs.get('cb'))

    def post(self, url, **kwargs):
        """::

            tx = ua.post('example.com')
            tx = ua.post('http://example.com', headers={'Accept': '*/*'}, data='Hi!')
            tx = ua.post('http://example.com', headers={'Accept': '*/*'},
                        form={'a': 'b'})
            tx = ua.post('http://example.com', headers={'Accept': '*/*'},
                        json={'a': 'b'})

        Perform blocking ``POST`` request and return resulting
        :mod:`Pyjo.Transaction.HTTP` object, takes the same arguments as
        :meth:`Pyjo.UserAgent.Transactor.tx` (except for the ``POST`` method, which is
        implied). You can also append a callback to perform requests non-blocking. ::

            def cb(ua, tx):
                print(tx.res.body)

            tx = ua.post('http://example.com', cb=cb)

            if not Pyjo.IOLoop.is_running
                Pyjo.IOLoop.start()
        """
        return self.start(self.build_tx('POST', url, **kwargs), kwargs.get('cb'))

    def start(self, tx, cb=None):
        # TODO Pyjo.UserAgent.Server and fork safety

        # Non-blocking
        if cb:
            if DEBUG:
                warn(f'-- Non-blocking request ({self._url(tx)})\n')
            return self._start(True, tx, cb)

        # Blocking
        else:
            if DEBUG:
                warn(f'-- Blocking request ({self._url(tx)})\n')

            class context:
                pass

            context.tx = tx

            def blocking_cb(ua, tx):
                ua.ioloop.stop()
                context.tx = tx

            self._start(False, tx, blocking_cb)
            self.ioloop.start()
            return context.tx

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

        # TLS
        options['tls'] = proto == 'https'
        if options['tls']:
            options['tls_ca'] = self.ca
            options['tls_cert'] = self.cert
            options['tls_key'] = self.key

        class context:
            pass

        context.cb = cb
        context.ua = weakref.proxy(self)

        def client_cb(loop, err, stream):
            cb = context.cb
            cid = context.cid
            ua = context.ua

            # Connection error
            if not ua:
                return

            if err:
                return ua._error(cid, err)

            # Connection established
            def timeout_cb(ua):
                self._error(cid, 'Inactivity timeout')

            stream.on('timeout', timeout_cb)

            def close_cb(ua):
                if ua:
                    self._finish(cid, True)

            stream.on('close', close_cb)

            def error_cb(ua, err):
                if ua:
                    self._error(cid, err)

            stream.on('error', error_cb)

            def read_cb(ua, chunk):
                self._read(cid, chunk)

            stream.on('read', read_cb)
            cb(cid)

        cid = self._loop(nb).client(client_cb, **options)
        context.cid = cid
        return cid

    def _connect_proxy(self, nb, old, cb):
        # Start CONNECT request
        new = self.transactor.proxy_connect(old)
        if not new:
            return

    def _connected(self, cid):
        # Inactivity timeout
        c = self._connections[cid]
        stream = self._loop(c['nb']).stream(cid).set(timeout=self.inactivity_timeout)

        # Store connection information in transaction
        tx = c['tx']
        tx.connection = cid
        handle = stream.handle
        tx.local_address, tx.local_port = handle.getsockname()[:2]
        tx.remote_address, tx.remote_port = handle.getpeername()[:2]

        # Start writing
        def resume_cb(ua):
            ua._write(cid)

        tx.on('resume', resume_cb)
        self._write(cid)

    def _connection(self, nb, tx, cb):
        # Reuse connection
        proto, host, port = self.transactor.endpoint(tx)
        cid = tx.connection or self._dequeue(nb, f'{proto}:{host}:{port}', True)
        if cid:
            if DEBUG:
                warn(f'-- Reusing connection {cid} ({proto}://{host}:{port})\n')
            self._connections[cid] = {'cb': cb, 'nb': nb, 'tx': tx}
            if not tx.connection:
                tx.kept_alive = True
            self._connected(cid)
            return cid

        # CONNECT request to proxy required
        cid = self._connect_proxy(nb, tx, cb)
        if cid:
            return cid

        # Connect
        if DEBUG:
            warn(f'-- Connect ({proto}://{host}:{port})\n')
        cid = self._connect(nb, True, tx, cid, self._connected)
        self._connections[cid] = {'cb': cb, 'nb': nb, 'tx': tx, 'writing': False}

        return cid

    def _dequeue(self, nb, name, test=False):
        loop = self._loop(nb)
        if nb:
            old = self._nb_queue
        else:
            old = self._queue

        found = False
        new = []
        for queued in old:
            if found or name not in queued:
                new.append(queued)
                continue

            # Search for id/name and sort out corrupted connections if necessary
            stream = loop.stream(queued[1])
            if not stream:
                continue

            if test and stream.is_readable:
                stream.close()
            else:
                found = queued[1]

        if nb:
            self._nb_queue = new
        else:
            self._queue = new

        return found

    def _enqueue(self, nb, name, cid):
        # Enforce connection limit
        if nb:
            queue = self._nb_queue
        else:
            queue = self._queue

        max_connections = self.max_connections
        while queue and len(queue) >= max_connections:
            self._remove(queue.pop(0)[1])

        if max_connections:
            queue.append([name, cid])
        else:
            self._loop(nb).stream(cid).close()

    def _error(self, cid, err):
        tx = self._connections[cid]['tx']
        if tx:
            tx.res.error = {'message': err}
        self._finish(cid, True)

    def _finish(self, cid, close):
        # Remove request timeout
        c = self._connections.get(cid)
        if not c:
            return

        loop = self._loop(c['nb'])
        if not loop:
            return

        if c.get('timeout'):
            loop.remove(c['timeout'])

        old = c['tx']
        if not old:
            return self._remove(cid, close)

        # Premature connection close
        res = old.closed().res.finish()
        if close and not res.code and not res.error:
            res.error = {'message': 'Premature connection close'}

        # TODO Finish WebSocket

        jar = self.cookie_jar
        if jar:
            jar.collect(old)

        # TODO Upgrade connection to WebSocket

        # Finish normal connection and handle redirects
        self._remove(cid, close)
        if res.is_error:
            res.error = {'message': res.message, 'code': res.code}
        if not self._redirect(c, old):
            c['cb'](self, old)

    def _loop(self, nb):
        if nb:
            return Pyjo.IOLoop.singleton
        else:
            return self.ioloop

    def _read(self, cid, chunk):
        # Corrupted connection
        c = self._connections.get(cid)
        if not c:
            self._connections.pop(cid, None)
            return

        tx = c.get('tx', None)

        if not tx:
            return self._remove(cid)

        # Process incoming data
        if DEBUG:
            warn(f'-- Client <<< Server ({self._url(tx)})\n{str(chunk)}\n')

        tx.client_read(chunk)
        if tx.is_finished:
            self._finish(cid, False)

    def _redirect(self, c, old):
        new = self.transactor.redirect(old)
        if not new:
            return

        if len(old.redirects()) >= self.max_redirects:
            return

        return self._start(c['nb'], new, c.pop('cb', None))

    def _remove(self, cid, close):
        # Close connection
        c = self._connections.pop(cid, None)
        tx = c['tx'] if c else None
        if close or not tx or not tx.keep_alive or tx.error:
            for nb in True, False:
                self._dequeue(nb, cid)
                self._loop(nb).remove(cid)
            return

        # Keep connection alive (CONNECT requests get upgraded)
        if tx.req.method.upper() != 'CONNECT':
            self._enqueue(c['nb'], '{}:{}:{}'.format(*self.transactor.endpoint(tx)), cid)

    def _start(self, nb, tx, cb):
        # Application server
        url = tx.req.url
        if not url.is_abs:
            base = self.server.db_url if nb else self.server.url
            url.scheme, url.host, url.port = base.scheme, base.host, base.port

        if self.proxy:
            self.proxy.prepare(tx)
        if self.cookie_jar:
            self.cookie_jar.prepare(tx)

        # Connect and add request timeout if necessary
        cid = self.emit('start', tx)._connection(nb, tx, cb)
        timeout = self.request_timeout
        if timeout:

            def timeout_cb(loop):
                self._error(cid, 'Request timeout')

            self._connections[cid]['timeout'] = self._loop(nb).timer(timeout, timeout_cb)

        return cid

    def _url(self, tx):
        return tx.req.url.to_abs()

    def _write(self, cid):
        # Protect from resume event recursion
        c = self._connections.get(cid)
        if not c or not (tx := c.get('tx')) or c.get('writing'):
            return
        c['writing'] = True
        try:
            chunk = tx.client_write()
        finally:
            c['writing'] = False
        if DEBUG:
            warn(f'-- Client >>> Server ({self._url(tx)})\n{chunk!r}')
        if not len(chunk):
            return

        ua = weakref.proxy(self)
        self._loop(c['nb']).stream(cid).write(chunk, lambda stream: ua._write(cid) if isalive(ua) else None)


new = Pyjo_UserAgent.new
object = Pyjo_UserAgent
