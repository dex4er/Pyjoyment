
"""
Pyjo.String.Mixin - Object with to_bytes/to_str methods
=======================================================
::

    import Pyjo.Base
    import Pyjo.String.Mixin

    class SubClass(Pyjo.Base.object, Pyjo.String.Mixin.object):
        def to_bytes(self):
            return b'value'

        def to_str(self):
            return 'value'

The mixin class for objects with :meth:`to_bytes` and/or :meth:`to_str` methods.

Classes
-------
"""


import Pyjo.Base

import platform


class Error(Exception):
    pass


class Pyjo_String_Mixin:
    """
    This mixin does not provide own constructor method
    and implements the following new methods.
    """

    def __bool__(self):
        """::

            boolean = bool(obj)

        True if string representation is also true.
        """
        if hasattr(self, 'to_str'):
            return bool(self.to_str())
        elif hasattr(self, 'to_bytes'):
            return bool(self.to_bytes())
        else:
            raise Error('Method "to_bytes" or "to_str" not implemented by subclass')

    def __bytes__(self):
        """::

            bstring = bytes(obj)

        Byte-string representation of an object.
        """
        if hasattr(self, 'to_bytes'):
            return self.to_bytes()
        elif hasattr(self, 'to_str'):
            return bytes(self.to_str(), 'utf-8')
        else:
            raise Error('Method "to_bytes" or "to_str" not implemented by subclass')

    def __complex__(self):
        """::

            complexnumber = complex(obj)

        Converts string representation into complex number.
        """
        if hasattr(self, 'to_str'):
            return complex(self.to_str())
        elif hasattr(self, 'to_bytes'):
            return complex(self.to_bytes())
        else:
            raise Error('Method "to_bytes" or "to_str" not implemented by subclass')

    def __eq__(self, other):
        """::

            boolean = obj == other

        True if string representation of the object is equal to other value.
        """
        if hasattr(self, 'to_str'):
            return self.to_str() == other
        elif hasattr(self, 'to_bytes'):
            return self.to_bytes() == other
        else:
            raise Error('Method "to_bytes" or "to_str" not implemented by subclass')

    def __float__(self):
        """::

            floatnumber = float(self)

        Converts string representation into float number.
        """
        if hasattr(self, 'to_str'):
            return float(self.to_str())
        elif hasattr(self, 'to_bytes'):
            return float(self.to_bytes())
        else:
            raise Error('Method "to_bytes" or "to_str" not implemented by subclass')

    def __ge__(self, other):
        """::

            boolean = obj >= other

        True if string representation of the object is equal or greater than other value.
        """
        if hasattr(self, 'to_str'):
            return self.to_str() >= other
        elif hasattr(self, 'to_bytes'):
            return self.to_bytes() >= other
        else:
            raise Error('Method "to_bytes" or "to_str" not implemented by subclass')

    def __gt__(self, other):
        """::

            boolean = obj > other

        True if string representation of the object is greater than other value.
        """
        if hasattr(self, 'to_str'):
            return self.to_str() > other
        elif hasattr(self, 'to_bytes'):
            return self.to_bytes() > other
        else:
            raise Error('Method "to_bytes" or "to_str" not implemented by subclass')

    def __hash__(self):
        """::

            hashvalue = hash(obj)

        Returns hash value of string representation of this object.
        """
        if hasattr(self, 'to_str'):
            return hash(self.to_str())
        elif hasattr(self, 'to_bytes'):
            return hash(self.to_bytes())
        else:
            raise Error('Method "to_bytes" or "to_str" not implemented by subclass')

    if platform.python_implementation() != 'PyPy':
        def __int__(self):
            """::

                intnumber = int(obj)

            Converts string representation into integer number.
            """
            if hasattr(self, 'to_str'):
                return int(self.to_str())
            elif hasattr(self, 'to_bytes'):
                return int(self.to_bytes())
            else:
                raise Error('Method "to_bytes" or "to_str" not implemented by subclass')
    else:
        pass  # PyPy3 error

    def __le__(self, other):
        """::

            boolean = obj <= other

        True if string representation of the object is equal or lesser than other value.
        """
        if hasattr(self, 'to_str'):
            return self.to_str() <= other
        elif hasattr(self, 'to_bytes'):
            return self.to_bytes() <= other
        else:
            raise Error('Method "to_bytes" or "to_str" not implemented by subclass')

    def __lt__(self, other):
        """::

            boolean = obj < other

        True if string representation of the object is lesser than other value.
        """
        if hasattr(self, 'to_str'):
            return self.to_str() < other
        elif hasattr(self, 'to_bytes'):
            return self.to_bytes() < other
        else:
            raise Error('Method "to_bytes" or "to_str" not implemented by subclass')

    def __ne__(self, other):
        """::

            boolean = obj != other

        True if string representation of the object is not equal to other value.
        """
        if hasattr(self, 'to_str'):
            return self.to_str() != other
        elif hasattr(self, 'to_bytes'):
            return self.to_bytes() != other
        else:
            raise Error('Method "to_bytes" or "to_str" not implemented by subclass')

    def __repr__(self):
        """::

            reprstring = repr(obj)

        String representation of an object shown in console.
        """
        if hasattr(self, 'to_str'):
            string = self.__str__()
        elif hasattr(self, 'to_bytes'):
            string = self.__bytes__()
        else:
            raise Error('Method "to_bytes" or "to_str" not implemented by subclass')

        if self.__module__ == '__main__':
            return f"{self.__class__.__name__}({repr(string)})"
        elif isinstance(self, Pyjo.Base.object):
            return f"{self.__module__}.new({repr(string)})"
        else:
            return f"{self.__module__}.{self.__class__.__name__}({repr(string)})"

    def __str__(self):
        """::

            string = str(obj)

        String representation of an object.
        """
        if hasattr(self, 'to_str'):
            string = self.to_str()
            if string is None:
                string = 'None'
            return string
        elif hasattr(self, 'to_bytes'):
            return repr(self.to_bytes())
        else:
            raise Error('Method "to_bytes" or "to_str" not implemented by subclass')


object = Pyjo_String_Mixin
