"""
Pyjo.UserAgent.CookieJar - Cookie jar for HTTP user agents
==========================================================
::

    import Pyjo.UserAgent.CookieJar

    # Add response cookies
    jar = Pyjo.UserAgent.CookieJar.new()
    jar.add(
        Pyjo.UserAgent.CookieJar.new({
            'name': 'foo',
            'value': 'bar',
            'domain': 'localhost',
            'path': '/test'
        })
    )

    # Find request cookies
    for cookie in jar.find(Pyjo.URL.new('http://localhost/test')):
        print(cookie.name)
        print(cookie.value)

:mod:`Pyjo.UserAgent.CookieJar` is the transaction building and manipulation
framework used by :mod:`Pyjo.UserAgent`.

Classes
-------
"""

import Pyjo.Base
import Pyjo.Cookie.Request

from Pyjo.Regexp import r
from Pyjo.Util import notnone

import time


re_domain_or_localhost = r(r'[^.]+\.[^.]+|localhost$')
re_domain = r(r'^[^.]+\.?')
re_endswith_numeric_domain = r(r'\.\d+$')


class Pyjo_UserAgent_CookieJar(Pyjo.Base.object):
    """
    :mod:`Pyjo.UserAgent.CookieJar` inherits all attributes and methods from
    :mod:`Pyjo.Base` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        self.collecting = kwargs.get('collecting', True)
        """::

            boolean = jar.collecting
            jar.collecting = boolean

        Allow :meth:`collect` to :meth:`add` new cookies to the jar, defaults to a ``True``
        value.
        """

        self.max_cookie_size = kwargs.get('max_cookie_size', 4096)
        """::

            size = jar.max_cookie_size
            jar.max_cookie_size = 4096

        Maximum cookie size in bytes, defaults to ``4096`` (4KB).
        """

        self._jar = {}

    def add(self, *cookies):
        """::

            jar = jar.add(cookie)
            jar = jar.add(cookie, cookie)

        Add multiple :mod:`Pyjo.Cookie.Response` objects to the jar.
        """
        size = self.max_cookie_size

        for cookie in cookies:
            # Convert max age to expires
            age = cookie.max_age
            if age:
                cookie.expires = age + time.time()

            # Check cookie size
            if len(notnone(cookie.value, '')) > size:
                continue

            # Replace cookie
            domain = notnone(cookie.domain, '').lower()
            if not domain:
                continue

            if domain.startswith('.'):
                domain = domain[1:]

            path = cookie.path
            if not path:
                continue

            name = notnone(cookie.name, '')
            if not len(name):
                continue

            if domain not in self._jar:
                self._jar[domain] = []

            jar = [c for c in self._jar[domain] if self._compare(c, path, name, domain)]
            jar.append(cookie)
            self._jar[domain] = jar

        return self

    @property
    def all(self):
        """::

            cookies = jar.all

        Return all L<Mojo::Cookie::Response> objects that are currently stored in the
        jar. ::

            # Names of all cookies
            for c in jar.all:
                print(c.name)
        """
        jar = self._jar
        cookies = [jar[domain] for domain in sorted(jar.keys())]
        return [i for sub in cookies for i in sub]

    def collect(self, tx):
        """::

            jar.collect(Pyjo.Transaction.HTTP.new())

        Collect response cookies from transaction.
        """
        if not self.collecting:
            return

        url = tx.req.url
        if tx.res.cookies:
            for cookie in tx.res.cookies:
                # Validate domain
                host = url.ihost
                if not cookie.domain:
                    cookie.domain, cookie.host_only = host, True
                domain = cookie.domain.lower()
                if domain.startswith('.'):
                    domain = domain[1:]
                if host != domain and (not host.endswith('.' + domain) or re_endswith_numeric_domain.search(host)):
                    continue

                # Validate path
                path = notnone(cookie.path, url.path.to_dir().to_abs_str())
                path = Pyjo.Path.new(path).set(trailing_slash=False).to_abs_str()
                if not self._path(path, url.path.to_abs_str()):
                    continue

                cookie.path = path
                self.add(cookie)

    def empty(self):
        """::

            jar.empty()

        Empty the jar.
        """
        self._jar = {}

    def find(self, url):
        """::

            cookies = jar.find(Pyjo.URL.new())

        Find :mod:`Pyjo.Cookie.Request` objects in the jar for :mod:`Pyjo.URL` object. ::

            # Names of all cookies found
            for cookie in jar.find(Pyjo.URL.new('http://example.com/foo')):
                print(cookie.name)
        """
        found = []
        domain = host = url.ihost
        if not domain:
            return found
        path = url.path.to_abs_str()

        while re_domain_or_localhost.search(domain):
            old = self._jar.get(domain, None)
            if old:
                # Grab cookies
                new = self._jar[domain] = []
                for cookie in old:
                    if cookie.host_only and host != cookie.domain:
                        continue

                    # Check if cookie has expired
                    expires = cookie.expires
                    if expires:
                        if time.time() > (expires or 0):
                            continue

                    new.append(cookie)

                    # Taste cookie
                    if cookie.secure and url.protocol != 'https':
                        continue

                    if not self._path(cookie.path, path):
                        continue

                    name = cookie.name
                    value = cookie.value
                    found.append(Pyjo.Cookie.Request.new(name=name, value=value))

            domain = re_domain.sub('', domain)

        return found

    def prepare(self, tx):
        """::

            jar.prepare(Pyjo.Transaction.HTTP.new())

        Prepare request cookies for transaction.
        """
        if not self._jar:
            return

        req = tx.req
        req.set_cookie(*self.find(req.url))

    def _compare(self, cookie, path, name, domain):
        return cookie.path != path or cookie.name != name or cookie.domain != domain

    def _path(self, path1, path2):
        return path1 == '/' or path1 == path2 or path2.find(path1 + '/') == 0


new = Pyjo_UserAgent_CookieJar.new
object = Pyjo_UserAgent_CookieJar
