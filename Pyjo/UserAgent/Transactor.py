"""
Pyjo.UserAgent.Transactor - User agent transactor
=================================================
::

    import Pyjo.UserAgent.Transactor

    # Simple GET request
    t = Pyjo.UserAgent.Transactor.new()
    print(t.tx('GET', 'http://example.com').req)

    # PATCH request with "Do Not Track" header and content
    print(t.tx('PATCH', 'example.com', headers={'DNT': 1}, data='Hi!').req)

    # POST request with form-data
    print(t.tx('POST', 'example.com', form={'a': 'b'}).req)

    # PUT request with JSON data
    print(t.tx('PUT', 'example.com', json={'a': 'b'}).req)

:mod:`Pyjo.UserAgent.Transactor` is the transaction building and manipulation
framework used by :mod:`Pyjo.UserAgent`.

Generators
----------

These content generators are available by default.

form
~~~~
::

    t.tx('POST', 'http://example.com', form={'a': 'b'})

Generate query string, ``application/x-www-form-urlencoded`` or
``multipart/form-data`` content.

json
~~~~
::

    t.tx('PATCH', 'http://example.com', json={'a': 'b'})

Generate JSON content with :mod:`Pyjo.JSON`.

Classes
-------
"""

import Pyjo.Base
import Pyjo.Content.MultiPart
import Pyjo.Parameters
import Pyjo.Transaction.HTTP
import Pyjo.URL

from Pyjo.JSON import encode_json
from Pyjo.Regexp import r
from Pyjo.Util import b, notnone


re_no_proto = r(r'^/|://')


class Pyjo_UserAgent_Transactor(Pyjo.Base.object):
    """
    :mod:`Pyjo.UserAgent.Transactor` inherits all attributes and methods from
    :mod:`Pyjo.Base` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        self.generators = kwargs.get('generators', {'data': self._data, 'form': self._form, 'json': self._json})
        """::

            generators = t.generators
            t.generators = {'foo': lambda t, tx, form, **kwargs: ...}

        Registered content generators, by default only ``form`` and ``json`` are already
        defined.
        """

        self.name = kwargs.get('name', 'Pyjoyment (Python)')
        """::

            name = t.name
            t.name = 'Pyjoyment'

        Value for ``User-Agent`` request header of generated transactions, defaults to
        ``Pyjoyment (Python)``.
        """

    def add_generator(self, name, generator):
        """::

            t = t.add_generator('foo', lambda t, tx, form, **kwargs: ...)

        Register a new content generator.
        """
        self.generators[name] = generator
        return self

    def endpoint(self, tx):
        """::

            proto, host, port = t.endpoint(Pyjo.Transaction.HTTP.new())

        Actual endpoint for transaction.
        """
        # Basic endpoint
        req = tx.req
        url = req.url
        proto = url.protocol or 'http'
        host = url.ihost
        port = url.port or (443 if proto == 'https' else 80)

        # Proxy for normal HTTP requests
        socks = False
        proxy = req.proxy
        if proxy:
            socks = proxy.protocol == 'socks'
        if proto == 'http' and not req.is_handshake and not socks:
            return self._proxy(tx, proto, host, port)

        return proto, host, port

    def peer(self, tx):
        proto, host, port = self.endpoint(tx)
        return self._proxy(tx, proto, host, port)

    def proxy_connect(self, old):
        # Already a CONNECT request
        req = old.req
        if req.method.upper() == 'CONNECT':
            return

        # No proxy
        proxy = req.proxy
        if not proxy:
            return
        if proxy.protocol == 'socks':
            return

        # WebSocket and/or HTTPS
        url = req.url
        if not req.is_handshake and url.protocol != 'https':
            return

        # CONNECT request (expect a bad response)
        new = self.tx('CONNECT', url.clone().set(userinfo=None))
        new.req.proxy = proxy
        new.res.content.set(auto_relax=False).headers.connection = 'keep-alive'

        return new

    def redirect(self, old):
        # Commonly used codes
        res = old.res
        code = res.code or 0
        if code not in [301, 302, 303, 307, 308]:
            return

        # Fix location without authority and/or scheme
        location = res.headers.location
        if not location:
            return

        location = Pyjo.URL.new(location)
        if not location.is_abs:
            location = location.base(old.req.url).to_abs()
        proto = location.protocol
        if proto != 'http' and proto != 'https':
            return

        # Clone request if necessary
        new = Pyjo.Transaction.HTTP.new()
        req = old.req
        if code == 307 or code == 308:
            clone = req.clone()
            if not clone:
                return
            new.req = clone
        else:
            method = req.method.upper()
            headers = (
                new.req.set(method='GET' if method == 'POST' else method)
                .content.set(headers=req.headers.clone())
                .headers
            )
            for n in filter(lambda n: n.lower().startswith('content-'), headers.names()):
                headers.remove(n)

        headers = new.req.set(url=location).headers
        for n in ['Authorization', 'Cookie', 'Host', 'Referer']:
            headers.remove(n)

        new.previous = old
        return new

    def tx(self, method, url, headers=None, body=None, **kwargs):
        # Method and URL
        tx = Pyjo.Transaction.HTTP.new()
        req = tx.req
        req.method = method
        if isinstance(url, Pyjo.URL.object):
            req.url = url
        else:
            req.url.parse(url if re_no_proto.search(url) else 'http://' + url)

        # Headers (we identify ourselves and accept gzip compression)
        h = req.headers
        if headers:
            h.from_dict(headers)
        if not h.user_agent:
            h.user_agent = self.name
        if not h.accept_encoding:
            h.accept_encoding = 'gzip'

        # Generator
        generators = list(set(self.generators) & set(kwargs))
        if generators:
            g = generators[0]
            self.generators[g](tx, **kwargs)

        # Body
        elif body is not None:
            req.body = body

        return tx

    def upgrade(self, tx):
        # TODO websocket
        pass

    def websocket(self, url, headers=None, **kwargs):
        # TODO websocket
        pass

    def _data(self, tx, data, **kwargs):
        tx.req.body = b(data)

    def _form(self, tx, form, **kwargs):
        # Check for uploads and force multipart if necessary
        req = tx.req
        headers = req.headers
        multipart = 'multipart/form-data' in notnone(headers.content_type, '').lower()
        for value in [v for l in map(lambda v: v if isinstance(v, (list, tuple)) else (v,), form.values()) for v in l]:
            if isinstance(value, dict):
                multipart = True
                break

        # Multipart
        if multipart:
            parts = self._multipart(kwargs['charset'], form)
            req.content = Pyjo.Content.MultiPart.new(headers=headers, parts=parts)
            self._type(headers, 'multipart/form-data')
            return tx

        # Query parameters or urlencoded
        p = Pyjo.Parameters.new(**form)
        if 'charset' in kwargs:
            p.charset = kwargs['charset']
        method = req.method.upper()
        if method == 'GET' or method == 'HEAD':
            req.url.query = p
        else:
            req.body = p.to_bytes()
            self._type(headers, 'application/x-www-form-urlencoded')

        return tx

    def _json(self, tx, json, **kwargs):
        tx.req.body = encode_json(json)
        self._type(tx.req.headers, 'application/json')
        return tx

    def _multipart(self, charset, form):
        raise Exception(self, charset, form)

    def _proxy(self, tx, proto, host, port):
        # Update with proxy information
        proxy = tx.req.proxy
        if proxy:
            proto = proxy.protocol
            host = proxy.ihost
            port = proxy.port or (443 if proto == 'https' else 80)

        return proto, host, port

    def _type(self, headers, content_type):
        if not headers.content_type:
            headers.content_type = content_type


new = Pyjo_UserAgent_Transactor.new
object = Pyjo_UserAgent_Transactor
