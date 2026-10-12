
"""
Pyjo.Cookie - HTTP cookie base class
====================================
::

    import Pyjo.Cookie

    class MyCookie(Pyjo.Cookie.object):
        def parse(self, string):
            ...

        def to_str(self):
            ...

:mod:`Pyjo.Cookie` is an abstract base class for HTTP cookie containers based on
:rfc:`6265`, like
:mod:`Pyjo.Cookie.Request` and :mod:`Pyjo.Cookie.Response`.

Classess
--------
"""

import Pyjo.Base
import Pyjo.String.Mixin

from Pyjo.Util import not_implemented


class Pyjo_Cookie(Pyjo.Base.object, Pyjo.String.Mixin.object):
    """
    :mod:`Pyjo.Cookie` inherits all methods from :mod:`Pyjo.Base` and :mod:`Pyjo.String.Mixin`
    and implements the following new ones.
    """

    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        """::

            name = cookie.name
            cookie.name = 'foo'

        Cookie name.
        """

        self.value = kwargs.get('value')
        """::

            value = cookie.value
            cookie.value = '/test'

        Cookie value.
        """

    def __bool__(self):
        """::

            boolean = bool(path)

        Always true. (Python 3.x)
        """
        return True

    def __nonzero__(self):
        """::

            boolean = bool(path)

        Always true. (Python 2.x)
        """
        return True

    @not_implemented
    def parse(self, string):
        """::

            cookies = cookie.parse(string)

        Parse cookies. Meant to be overloaded in a subclass.
        """
        pass

    @not_implemented
    def to_str(self):
        """::

            string = cookie.to_str()

        Render cookie. Meant to be overloaded in a subclass.
        """
        pass


new = Pyjo_Cookie.new
object = Pyjo_Cookie
