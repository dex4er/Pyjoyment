"""
Pyjo.UserAgent.Proxy - User agent proxy manager
===============================================
::

    import Pyjo.UserAgent.Proxy

    proxy = Pyjo.UserAgent.Proxy.new()
    proxy.detect()
    print(proxy.http)

:mod:`Pyjo.UserAgent.Proxy` manages proxy servers for :mod:`Pyjo.UserAgent`.

Classes
-------
"""

import Pyjo.Base

from Pyjo.Util import getenv


class Pyjo_UserAgent_Proxy(Pyjo.Base.object):
    """
    :mod:`Pyjo.UserAgent.Proxy` inherits all attributes and methods from
    :mod:`Pyjo.Base` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        self.http = kwargs.get('http')
        """::

            http = proxy.http
            proxy.http = 'socks://pyjo:secret@127.0.0.1:8080'

        Proxy server to use for HTTP and WebSocket requests.
        """

        self.https = kwargs.get('https')
        """::

            https = proxy.https
            proxy.https = 'http://pyjo:secret@127.0.0.1:8080'

        Proxy server to use for HTTPS and WebSocket requests.
        """

        self.no = kwargs.get('no', [])
        """::

            no = proxy.no
            proxy.no = ['localhost', 'intranet.pyjoyment.net']

        Domains that don't require a proxy server to be used.
        """

    def detect(self):
        """::

            proxy = proxy.detect()

        Check environment variables ``HTTP_PROXY``, ``http_proxy``, ``HTTPS_PROXY``,
        ``https_proxy``, ``NO_PROXY`` and ``no_proxy`` for proxy information. Automatic
        proxy detection can be enabled with the ``PYJO_PROXY`` environment variable.
        """
        self.http = getenv('HTTP_PROXY') or getenv('http_proxy')
        self.https = getenv('HTTPS_PROXY') or getenv('https_proxy')
        self.no = (getenv('NO_PROXY') or getenv('no_proxy') or '').split(',')
        return self

    def is_needed(self, domain):
        """::

            boolean = proxy.is_needed('intranet.example.com')

        Check if request for domain would use a proxy server.
        """
        for d in self.no:
            if domain.endswith(d):
                return False

        return True

    def prepare(self, tx):
        """::

            proxy.prepare(Pyjo.Transaction.HTTP.new())

        Prepare proxy server information for transaction.
        """
        if getenv('PYJO_PROXY'):
            self.detect()
        req = tx.req
        url = req.url
        if not self.is_needed(url.host) or req.proxy is not None:
            return

        # HTTP proxy
        proto = url.protocol
        http = self.http
        if http and proto == 'http':
            req.proxy = http

        # HTTPS proxy
        https = self.https
        if https and proto == 'https':
            req.proxy = https


new = Pyjo_UserAgent_Proxy.new
object = Pyjo_UserAgent_Proxy
