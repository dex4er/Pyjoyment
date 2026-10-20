"""
Pyjo.Cookie - HTTP cookie base class
====================================
::

    from Pyjo.Cookie import Cookie

    class MyCookie(Cookie):
        @classmethod
        def parse(cls, string=None): ...

        def to_str(self): ...

    # Or import the module, as in Google Python Style Guide

    import Pyjo.Cookie

    class MyCookie(Pyjo.Cookie.object):
        @classmethod
        def parse(cls, string=None): ...

        def to_str(self): ...

:mod:`Pyjo.Cookie` is an abstract base class for HTTP cookie containers, based on
:rfc:`6265`, like :mod:`Pyjo.Cookie.Request` and :mod:`Pyjo.Cookie.Response`.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Cookie <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Cookie.pm>`_
of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.Base
import Pyjo.String.Mixin

from Pyjo.Util import quote

import re

from http.cookies import BaseCookie, Morsel


class Pyjo_Cookie(Pyjo.Base.object, Pyjo.String.Mixin.object):
    """
    :mod:`Pyjo.Cookie` inherits all methods from :mod:`Pyjo.Base` and
    :mod:`Pyjo.String.Mixin` and implements the following new ones.
    """

    def __init__(self, morsel: Morsel[str] | None = None, *, name: str | None = None, value: str | None = None) -> None:
        """::

            cookie = Pyjo.Cookie.Request.new()
            cookie = Pyjo.Cookie.Request.new(name='foo', value='bar')
            cookie = Pyjo.Cookie.Request.new(SimpleCookie('foo=bar')['foo'])

        Construct a new cookie, from a :class:`http.cookies.Morsel` of the standard
        library if one is given.
        """
        self.name = name
        """::

            name = cookie.name
            cookie.name = 'foo'

        Cookie name.
        """

        self.value = value
        """::

            value = cookie.value
            cookie.value = '/test'

        Cookie value.
        """

        # Not in Mojolicious: a Morsel of http.cookies of the standard library
        if morsel is not None:
            self.name, self.value = morsel.key, morsel.value

    def __bool__(self) -> bool:
        """::

            boolean = bool(cookie)

        Always true.
        """
        return True

    def __str__(self) -> str:
        """::

            string = str(cookie)

        Alias for :meth:`to_str`.
        """
        return self.to_str()

    @classmethod
    def parse[C: Pyjo_Cookie](cls: type[C], string: str | BaseCookie[str] | None = None) -> list[C]:
        """::

            cookies = cookie.parse(string)

        Parse cookies. Meant to be overloaded in a subclass.
        """
        raise NotImplementedError('Method "parse" not implemented by subclass')

    def to_str(self) -> str:
        """::

            string = cookie.to_str()

        Render cookie. Meant to be overloaded in a subclass.
        """
        raise NotImplementedError('Method "to_str" not implemented by subclass')

    # Not in Mojolicious: http.cookies of the standard library
    def to_morsel(self) -> Morsel[str]:
        """::

            morsel = cookie.to_morsel()

        Turn cookie into a :class:`http.cookies.Morsel`, for the standard library. ::

            # "foo=\"b r\""
            Pyjo.Cookie.Request.new(name='foo', value='b r').to_morsel().OutputString()
        """
        morsel: Morsel[str] = Morsel()
        value = self.value or ''
        morsel.set(self.name or '', value, quote(value) if re.search(r'[,;" ]', value) else value)
        return morsel


new = Pyjo_Cookie.new
object = Pyjo_Cookie
Cookie = Pyjo_Cookie
