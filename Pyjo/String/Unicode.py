
"""
Pyjo.String.Unicode - Unicode string
====================================
::

    import Pyjo.String.Unicode

    # Manipulate String.Unicode
    string = Pyjo.String.Unicode.new('foo_bar_baz')
    print(string.camelize())

    # Chain methods
    string = Pyjo.String.Unicode.new('foo_bar_baz').quote()
    string = string.unquote().encode('utf-8').b64_encode('')
    print(string.decode('ascii'))

    # Use the alternative constructor
    from Pyjo.String.Unicode import u
    string = u('foobarbaz').camelize('').say()

:mod:`Pyjo.String.Unicode` is a container for unicode strings that provides a
more friendly API for many of the functions in :mod:`Pyjo.Util`.

It also inherits all methods from
either :class:`unicode` (Python 2.x) or :class:`str` (Python 3.x).

Classes
-------
"""


import Pyjo.String.Bytes
import Pyjo.Util

import sys


if sys.version_info >= (3, 0):
    base_object = str
else:
    base_object = unicode


DEFAULT_CHARSET = 'utf-8'


class Pyjo_String_Unicode(base_object):
    """
    :mod:`Pyjo.String.Unicode` inherits all methods from
    either :class:`unicode` (Python 2.x) or :class:`str` (Python 3.x)
    and implements the following new ones.
    """

    def __new__(cls, value='', charset=DEFAULT_CHARSET):
        return super().__new__(cls, Pyjo.Util.u(value, charset))

    def __repr__(self):
        return "{0}.new({1})".format(self.__module__, super().__repr__())

    def html_unescape(self):
        """::

            string = string.html_unescape()

        Unescape all HTML entities in unicode string with :func:`Pyjo.Util.html_unescape`. ::

            b('&lt;html&gt;').html_unescape().url_escape().say()
        """
        return self.new(Pyjo.Util.html_unescape(self))

    def encode(self, charset=DEFAULT_CHARSET):
        """::

            string = string.encode()
            string = string.encode('iso-8859-1')

        Encode unicode string, defaults to ``utf-8``, and return new :mod:`Pyjo.String.Bytes` object. ::

            string.trim().quote().encode().say()
        """
        return Pyjo.String.Bytes.new(super().encode(charset))

    @classmethod
    def new(cls, value='', charset=DEFAULT_CHARSET):
        """::

            string = Pyjo.String.Unicode.new('test123')

        Construct a new :mod:`Pyjo.String.Unicode` object.
        """
        return Pyjo_String_Unicode(value, charset)

    def say(self, **kwargs):
        """::

            string = string.say()
            string = string.say(file=sys.stderr, end='', flush=True)

        Print unicode string to handle and append a newline, defaults to :attr:`sys.stdout`.
        """
        if 'flush' in kwargs and sys.version_info < (3, 0):
            flush = kwargs.pop('flush')
        else:
            flush = False
        print(self.to_str(), **kwargs)
        if flush:
            f = kwargs.get('file', sys.stdout)
            f.flush()
        return self

    def to_bytes(self, charset=DEFAULT_CHARSET):
        """::

            bstring = string.to_bytes()
            bstring = string.to_bytes(charset)

        Turn unicode string into a bytes string.
        """
        return Pyjo.Util.b(self, charset)

    def to_str(self, charset=DEFAULT_CHARSET):
        """::

            string = string.to_str()

        Turn unicode string into a string:
        on Python 2.x into bytes string, on Python 3.x into unicode string.
        """
        if sys.version_info >= (3, 0):
            return self.to_unicode(charset)
        else:
            return self.to_bytes(charset)

    def to_unicode(self, charset=DEFAULT_CHARSET):
        """::

            ustring = string.to_unicode()
            ustring = string.to_unicode(charset)

        Turn unicode string into an unicode string.
        """
        return Pyjo.Util.u(self, charset)

    def trim(self):
        """::

            string = string.trim()

        Trim whitespace characters from both ends of bytestring with :func:`Pyjo.Util.trim`.
        """
        return self.new(Pyjo.Util.trim(self))

    def xml_escape(self):
        """::

            string = string.xml_escape()

        Escape only the characters ``&``, ``<``, ``>``, ``"`` and ``'`` in
        unicode string with :func:`Pyjo.Util.xml_escape`.
        """
        return self.new(Pyjo.Util.xml_escape(self))


def u(value='', charset=DEFAULT_CHARSET):
    """::

        string = u('test123')

    Construct a new :mod:`Pyjo.String.Unicode` object.
    """
    return Pyjo_String_Unicode(value, charset)


new = Pyjo_String_Unicode.new
object = Pyjo_String_Unicode
