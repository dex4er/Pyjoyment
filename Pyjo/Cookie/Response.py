"""
Pyjo.Cookie.Response - HTTP response cookie
===========================================
::

    Pyjo.Cookie.Response

    cookie = Pyjo.Cookie.Response.new()
    cookie.name = 'foo'
    cookie.value = 'bar'
    print(cookie)

:mod:`Pyjo.Cookie.Response` is a container for HTTP response cookies based on
:rfc:`6265`.

Classes
-------
"""

import Pyjo.Cookie
import Pyjo.Date

from Pyjo.Regexp import r
from Pyjo.Util import notnone, quote, split_cookie_header


ATTRS = set(['domain', 'expires', 'httponly', 'max-age', 'path', 'secure'])

re_quoted = r('[,;" ]')


class Pyjo_Cookie_Response(Pyjo.Cookie.object):
    """
    :mod:`Pyjo.Cookie.Response` inherits all attributes and methods from
    :mod:`Pyjo.Cookie` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.domain = kwargs.get('domain')
        """::

            domain = cookie.domain
            cookie.domain = 'localhost'

        Cookie domain.
        """

        self.expires = kwargs.get('expires')
        """::

            expires = cookie.expires
            cookie.expires = steady_time() + 60

        Expiration for cookie.
        """

        self.httponly = kwargs.get('httponly', False)
        """::

            boolean = cookie.httponly
            cookie.httponly = boolean

        HttpOnly flag, which can prevent client-side scripts from accessing this
        cookie.
        """

        self.max_age = kwargs.get('max_age')
        """::

            max_age = cookie.max_age
            cookie.max_age = 60

        Max age for cookie.
        """

        self.origin = kwargs.get('origin')
        """::

            origin = cookie.origin
            cookie.origin = 'mojolicio.us'

        Origin of the cookie.
        """

        self.path = kwargs.get('path')
        """::

            path = cookie.path
            cookie.path = '/test'

        Cookie path.
        """

        self.secure = kwargs.get('secure', False)
        """::

            boolean = cookie.secure
            cookie.secure = boolean

        Secure flag, which instructs browsers to only send this cookie over HTTPS
        connections.
        """

    @classmethod
    def parse(self, string=''):
        """::

            cookies = Pyjo.Cookie.Response.parse('f=b; path=/')

        Parse cookies.
        """
        cookies = []
        for pairs in split_cookie_header(string):
            name, value = pairs.pop(0)
            cookies.append(self.new(name=name, value=notnone(value, '')))
            for name, value in pairs:
                attr = name.lower()
                if attr in ATTRS:
                    if attr == 'expires':
                        value = Pyjo.Date.new(value).epoch
                    elif attr == 'secure' or attr == 'httponly':
                        value = True
                    elif attr == 'max-age':
                        attr = 'max_age'
                        value = int(value)
                    setattr(cookies[-1], attr, value)

        return cookies

    def to_str(self):
        """::

            string = cookie.to_str()

        Render cookie.
        """
        # Name and value
        name = str(notnone(self.name, ''))
        if not name:
            return ''

        value = str(notnone(self.value, ''))
        if re_quoted.search(value):
            value = quote(value)
        cookie = '='.join([name, value])

        # "expires"
        expires = self.expires
        if expires is not None:
            cookie += '; expires=' + str(Pyjo.Date.new(expires))

        # "domain"
        domain = self.domain
        if domain:
            cookie += '; domain=' + domain

        # "path"
        path = self.path
        if path:
            cookie += '; path=' + path

        # "secure"
        if self.secure:
            cookie += '; secure'

        # "HttpOnly"
        if self.httponly:
            cookie += '; HttpOnly'

        # "Max-Age"
        max_age = self.max_age
        if max_age is not None:
            cookie += '; Max-Age=' + str(max_age)

        return cookie


parse = Pyjo_Cookie_Response.parse

new = Pyjo_Cookie_Response.new
object = Pyjo_Cookie_Response
