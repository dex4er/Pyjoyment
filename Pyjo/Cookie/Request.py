"""
Pyjo.Cookie.Request - HTTP request cookie
=========================================
::

    import Pyjo.Cookie.Request

    cookie = Pyjo.Cookie.Request.new()
    cookie.name = 'foo'
    cookie.value = 'bar'
    print(cookie)

:mod:`Pyjo.Cookie.Request` is a container for HTTP request cookies, based on
:rfc:`6265`.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Cookie::Request <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Cookie/Request.pm>`_
of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.Cookie

from Pyjo.Util import quote, split_header

import re

from http.cookies import BaseCookie


class Pyjo_Cookie_Request(Pyjo.Cookie.object):
    """
    :mod:`Pyjo.Cookie.Request` inherits all attributes and methods from
    :mod:`Pyjo.Cookie` and implements the following new ones.
    """

    @classmethod
    def parse[C: Pyjo_Cookie_Request](cls: type[C], string: str | BaseCookie[str] | None = None) -> list[C]:
        """::

            cookies = Pyjo.Cookie.Request.parse('f=b; g=a')
            cookies = Pyjo.Cookie.Request.parse(SimpleCookie('f=b; g=a'))

        Parse cookies, also from a :class:`http.cookies.SimpleCookie` of the standard
        library.
        """
        # Not in Mojolicious: http.cookies of the standard library
        if isinstance(string, BaseCookie):
            return [cls.new(morsel) for morsel in string.values()]

        cookies: list[C] = []
        tree: list[list[list[str | None]]] = split_header(string or '')
        for name, value in (pair for pairs in tree for pair in pairs):
            if name is None or name.startswith('$'):
                continue
            cookies.append(cls.new(name=name, value=value or ''))
        return cookies

    def to_str(self) -> str:
        """::

            string = cookie.to_str()

        Render cookie.
        """
        if not (name := self.name or ''):
            return ''
        value = self.value or ''
        return '='.join([name, quote(value) if re.search(r'[,;" ]', value) else value])


parse = Pyjo_Cookie_Request.parse
new = Pyjo_Cookie_Request.new
object = Pyjo_Cookie_Request
