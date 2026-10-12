"""
Pyjo.Cookie.Request - HTTP request cookie
=========================================
::

    Pyjo.Cookie.Request

    cookie = Pyjo.Cookie.Request.new()
    cookie.name = 'foo'
    cookie.value = 'bar'
    print(cookie)

:mod:`Pyjo.Cookie.Request` is a container for HTTP request cookies based on
:rfc:`6265`.

Classes
-------
"""

import Pyjo.Cookie

from Pyjo.Regexp import r
from Pyjo.Util import notnone, quote, split_header


re_quoted = r('[,;" ]')


class Pyjo_Cookie_Request(Pyjo.Cookie.object):
    """
    :mod:`Pyjo.Cookie.Request` inherits all attributes and methods from
    :mod:`Pyjo.Cookie` and implements the following new ones.
    """

    @classmethod
    def parse(self, string=''):
        """::

            cookies = Pyjo.Cookie.Request.parse('f=b; g=a')

        Parse cookies.
        """
        cookies = []

        for pairs in split_header(string):
            for name, value in pairs:
                if name.startswith('$'):
                    continue
                cookies.append(self.new(name=name, value=notnone(value, '')))
        return cookies

    def to_str(self):
        """::

            string = cookie.to_str()

        Render cookie.
        """
        name = str(notnone(self.name, ''))
        if not name:
            return ''

        value = str(notnone(self.value, ''))
        if re_quoted.search(value):
            value = quote(value)
        return '='.join([name, value])


parse = Pyjo_Cookie_Request.parse


new = Pyjo_Cookie_Request.new
object = Pyjo_Cookie_Request
