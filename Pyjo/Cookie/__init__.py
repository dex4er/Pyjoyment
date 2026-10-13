"""
Pyjo.Cookie - HTTP cookie base class
====================================
::

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


class Pyjo_Cookie(Pyjo.Base.object, Pyjo.String.Mixin.object):
    """
    :mod:`Pyjo.Cookie` inherits all methods from :mod:`Pyjo.Base` and
    :mod:`Pyjo.String.Mixin` and implements the following new ones.
    """

    def __init__(self, *, name: str | None = None, value: str | None = None) -> None:
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
    def parse[C: Pyjo_Cookie](cls: type[C], string: str | None = None) -> list[C]:
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


new = Pyjo_Cookie.new
object = Pyjo_Cookie
