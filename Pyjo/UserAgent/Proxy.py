"""
Pyjo.UserAgent.Proxy - User agent proxy manager
===============================================
::

    import Pyjo.UserAgent.Proxy

    proxy = Pyjo.UserAgent.Proxy.new()
    proxy.detect()
    print(proxy.http)

:mod:`Pyjo.UserAgent.Proxy` manages proxy servers for :mod:`Pyjo.UserAgent`.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::UserAgent::Proxy <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/UserAgent/Proxy.pm>`_
of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.Base
import Pyjo.Transaction
import Pyjo.URL

from Pyjo.String.Unicode import split

import os

from typing import Self


class Pyjo_UserAgent_Proxy(Pyjo.Base.object):
    """
    :mod:`Pyjo.UserAgent.Proxy` inherits all methods from :mod:`Pyjo.Base` and
    implements the following new ones.
    """

    def __init__(self, *, http: str | None = None, https: str | None = None, no: list[str] | None = None) -> None:
        """::

            proxy = Pyjo.UserAgent.Proxy.new()
            proxy = Pyjo.UserAgent.Proxy.new(http='http://127.0.0.1:8080')

        Construct a new :mod:`Pyjo.UserAgent.Proxy` object.
        """
        self.http = http
        """::

            http = proxy.http
            proxy.http = 'socks://sri:secret@127.0.0.1:8080'

        Proxy server to use for HTTP and WebSocket requests.
        """

        self.https = https
        """::

            https = proxy.https
            proxy.https = 'http://sri:secret@127.0.0.1:8080'

        Proxy server to use for HTTPS and WebSocket requests.
        """

        # Renamed from Mojolicious: not, a keyword of Python, as the environment variable NO_PROXY names it
        self.no = no
        """::

            no = proxy.no
            proxy.no = ['localhost', 'intranet.mojolicious.org']

        Domains that don't require a proxy server to be used.
        """

    def detect(self) -> Self:
        """::

            proxy = proxy.detect()

        Check environment variables ``HTTP_PROXY``, ``http_proxy``,
        ``HTTPS_PROXY``, ``https_proxy``, ``NO_PROXY`` and ``no_proxy`` for proxy
        information. Automatic proxy detection can be enabled with the
        ``PYJO_PROXY`` environment variable.
        """
        env = os.environ
        self.http = env.get('HTTP_PROXY') or env.get('http_proxy')
        self.https = env.get('HTTPS_PROXY') or env.get('https_proxy')
        self.no = [domain or '' for domain in split(',', env.get('NO_PROXY') or env.get('no_proxy') or '')]
        return self

    def is_needed(self, domain: str) -> bool:
        """::

            boolean = proxy.is_needed('intranet.example.com')

        Check if request for domain would use a proxy server.
        """
        return not any(domain.endswith(no) for no in self.no or [])

    def prepare(self, tx: Pyjo.Transaction.object) -> None:
        """::

            proxy.prepare(Pyjo.Transaction.HTTP.new())

        Prepare proxy server information for transaction.
        """
        if os.environ.get('PYJO_PROXY') not in (None, '', '0'):
            self.detect()
        req = tx.req
        url = req.url
        if not self.is_needed(url.host or ''):
            return

        # HTTP proxy
        proto = url.protocol
        if (http := self.http) and proto == 'http':
            req.proxy = Pyjo.URL.new(http)

        # HTTPS proxy
        if (https := self.https) and proto == 'https':
            req.proxy = Pyjo.URL.new(https)


new = Pyjo_UserAgent_Proxy.new
object = Pyjo_UserAgent_Proxy
