
"""
Pyjo.String.Bytes - Bytes string
================================
::

    import Pyjo.String.Bytes

    # Manipulate String.Bytes
    string = Pyjo.String.Bytes.new('foo:bar:baz')
    print(string.url_escape().decode('ascii'))

    # Use the alternative constructor
    from Pyjo.String.Bytes import b
    bstring = b('foo:bar:baz').url_escape()

:mod:`Pyjo.String.Bytes` is a container for bytes strings that provides a
more friendly API for many of the functions in :mod:`Pyjo.Util`.

It also inherits all methods from :class:`bytes`.

Classes
-------
"""

import Pyjo.String.Unicode
import Pyjo.Util



DEFAULT_CHARSET = 'utf-8'


class Pyjo_String_Bytes(bytes):
    """
    :mod:`Pyjo.String.Bytes` inherits all methods from :class:`bytes` and
    implements the following new ones.
    """

    def __new__(cls, value=b'', charset=DEFAULT_CHARSET):
        return super().__new__(cls, Pyjo.Util.b(value, charset))

    def __repr__(self):
        return "{0}.new({1})".format(self.__module__, super().__repr__())

    def decode(self, charset=DEFAULT_CHARSET):
        """::

            string = string.decode()
            string = string.decode('iso-8859-1')

        Decode bytes string, defaults to ``utf-8``, and return new :mod:`Pyjo.String.Unicode` object. ::

            string.decode('UTF-16LE').unquote().trim().say()

        """
        return Pyjo.String.Unicode.new(super().decode(charset))

    @classmethod
    def new(cls, value=b'', charset=DEFAULT_CHARSET):
        """::

            string = Pyjo.String.Bytes.new('test123')

        Construct a new :mod:`Pyjo.String.Bytes` object.
        """
        return Pyjo_String_Bytes(value, charset)

    def url_escape(self):
        r"""::

            string = string.url_escape()
            string = string.url_escape(br'^A-Za-z0-9\-._~')

        Percent encode all unsafe characters in bytes string with
        :func:`Pyjo.Util.url_escape`. ::

            b('foo bar baz').url_escape().decode().say()
        """
        return self.new(Pyjo.Util.url_escape(self))

    def url_unescape(self):
        """

            string = string.url_unescape()

        Decode percent encoded characters in bytes string with
        :func:`Pyjo.Util.url_unescape`. ::

            b('%3Chtml%3E').url_unescape().decode().xml_escape().say()
        """
        return self.new(Pyjo.Util.url_unescape(self))


def b(value=b'', charset=DEFAULT_CHARSET):
    """::

        string = b('test123')

    Construct a new :mod:`Pyjo.String.Bytes` object.
    """
    return Pyjo_String_Bytes(value, charset)


new = Pyjo_String_Bytes.new
object = Pyjo_String_Bytes
