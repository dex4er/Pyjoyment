"""
Pyjo.Parameters - Parameters
============================
::

    import Pyjo.Parameters

    # Parse
    params = Pyjo.Parameters.new('foo=bar&baz=23')
    print(params.param('baz'))

    # Build
    params = Pyjo.Parameters.new(foo='bar', baz=23)
    params.append(i=u'♥ pyjo')
    print(params)

:mod:`Pyjo.Parameters` is a container for form parameters used by :mod:`Pyjo.URL`
and based on :rfc:`3986` as well as `the HTML Living Standard <https://html.spec.whatwg.org>`_.

Classes
-------
"""

import Pyjo.Base
import Pyjo.String.Mixin

from Pyjo.Regexp import r
from Pyjo.Util import b, isiterable, notnone, u, url_escape, url_unescape


re_pair = r(rb'^([^=]+)(?:=(.*))?$')


class Pyjo_Parameters(Pyjo.Base.object, Pyjo.String.Mixin.object):
    """
    :mod:`Pyjo.Parameters` inherits all attributes and methods from
    :mod:`Pyjo.Base` and :mod:`Pyjo.String.Mixin` and implements the following new ones.
    """

    def __init__(self, *args, **kwargs):
        """::

            params = Pyjo.Parameters.new()
            params = Pyjo.Parameters.new('foo=b%3Bar&baz=23')
            params = Pyjo.Parameters.new(foo='b&ar')
            params = Pyjo.Parameters.new(foo=['ba&r', 'baz'])
            params = Pyjo.Parameters.new(foo=['bar', 'baz'], bar=23)

        Construct a new :mod:`Pyjo.Parameters` object and :meth:`parse` parameters if
        necessary.
        """

        self.charset = 'utf-8'
        """::

            charset = params.charset
            params.charset = 'utf-8'

        Charset used for encoding and decoding parameters, defaults to ``utf-8``. ::

            # Disable encoding and decoding
            params.charset = None
        """

        self._pairs = []
        self._string = None

        self.parse(*args, **kwargs)

    def __bool__(self):
        """::

            boolean = bool(params)

        Always true.
        """
        return True

    def __iter__(self):
        """::

            pairs = list(params)

        Iterator based on :attr:`params`. Note that this will normalize the parameters.
        """
        return iter(self.pairs)

    def append(self, *args, **kwargs):
        """::

            params = params.append(foo='ba&r')
            params = params.append(foo=['ba&r', 'baz'])
            params = params.append(('foo', ['bar', 'baz']), ('bar', 23))
            params = params.append(Pyjo.Params.new())

        Append parameters. Note that this method will normalize the parameters.

        ::

            # "foo=bar&foo=baz"
            Pyjo.Parameters.new('foo=bar').append(Pyjo.Parameters.new('foo=baz'))

            # "foo=bar&foo=baz"
            Pyjo.Parameters.new('foo=bar').append(foo='baz')

            # "foo=bar&foo=baz&foo=yada"
            Pyjo.Parameters.new('foo=bar').append(foo=['baz', 'yada'])

            # "foo=bar&foo=baz&foo=yada&bar=23"
            Pyjo.Parameters.new('foo=bar').append(('foo', ['baz', 'yada']), ('bar', 23))
        """
        pairs = self.pairs

        if args and len(args) == 1 and isinstance(args[0], Pyjo_Parameters):
            args = args[0].pairs

        for k, v in list(args) + sorted(kwargs.items()):
            if isiterable(v):
                for vv in v:
                    pairs.append(
                        (k, vv),
                    )
            else:
                pairs.append(
                    (k, v),
                )
        return self

    def clone(self):
        """::

            params2 = params.clone()

        Clone parameters.
        """
        new_obj = type(self)()
        new_obj.charset = self.charset
        if self._string is not None:
            new_obj._string = self._string
        else:
            new_obj._pairs = list(self._pairs)
        return new_obj

    def every_param(self, name):
        """::

            values = params.every_param('foo')

        Similar to :meth:`param`, but returns all values sharing the same name as a
        list. Note that this method will normalize the parameters. ::

            # Get first value
            print(params.every_param('foo')[0])
        """
        values = []
        pairs = self.pairs
        for k, v in pairs:
            if k == name:
                values.append(v)

        return values

    def merge(self, *args, **kwargs):
        """::

            params = params.merge(('foo', 'ba&r'),)
            params = params.merge(foo='baz')
            params = params.merge(foo=['ba&r', 'baz'])
            params = params.merge(('foo', ['bar', 'baz']), ('bar', 23))
            params = params.merge(Pyjo.Parameters.new())

        Merge parameters. Note that this method will normalize the parameters. ::

            # "foo=baz"
            Pyjo.Parameters.new('foo=bar').merge(Pyjo.Parameters.new('foo=baz'))

            # "yada=yada&foo=baz"
            Pyjo.Parameters.new('foo=bar&yada=yada').merge(foo='baz')

            # "yada=yada"
            Pyjo.Parameters.new('foo=bar&yada=yada').merge(foo=None)
        """
        if len(args) == 1 and hasattr(args[0], 'pairs'):
            pairs = args[0].pairs
        else:
            pairs = list(args) + sorted(kwargs.items())
        for k, v in pairs:
            if v is None:
                self.remove(k)
            else:
                self.param(k, v)
        return self

    @property
    def names(self):
        """::

            names = params.names

        Return a list of all parameter names. ::

          # Names of all parameters
          for n in params.names:
              print(n)
        """
        return sorted(self.to_dict().keys())

    @property
    def pairs(self):
        """::

            array = params.pairs
            params.pairs = [('foo', 'b&ar'), ('baz', 23)]

        Parsed parameters. Note that setting this property will normalize the parameters.
        """
        # Parse string
        if self._string is not None:
            string = self._string
            self._string = None
            self._pairs = []

            if not len(string):
                return self._pairs

            charset = self.charset

            for pair in string.split(b'&'):
                m = re_pair.search(pair)

                if not m:
                    continue

                name = m.group(1)
                value = notnone(m.group(2), b'')

                # Replace "+" with whitespace, unescape and decode
                name = name.replace(b'+', b' ')
                value = value.replace(b'+', b' ')

                name = url_unescape(name)
                value = url_unescape(value)

                if charset:
                    name = u(name, charset)
                    value = u(value, charset)

                self._pairs.append(
                    (name, value),
                )

        return self._pairs

    @pairs.setter
    def pairs(self, value=None):
        # Replace parameters
        self._pairs = value
        self._string = None
        return self

    def param(self, name, value=None):
        """::

            value = params.param('foo')
            foo, baz = params.param(['foo', 'baz'])
            params = params.param('foo', 'ba&r')
            params = params.param('foo', ['ba;r', 'baz'])

        Access parameter values. If there are multiple values sharing the same name,
        and you want to access more than just the last one, you can use
        :meth:`every_param`. Note that this method will normalize the parameters.
        """
        # Multiple names
        if name is not None and isinstance(
            name,
            (
                list,
                tuple,
            ),
        ):
            return [self.param(n) for n in name]

        # Last value
        if value is None:
            param = self.every_param(name)
            if param:
                return self.every_param(name)[-1]
            else:
                return

        # Replace values
        return self._replace(name, value)

    def parse(self, *args, **kwargs):
        """::

            params = params.parse('foo=b%3Bar&baz=23')

        Parse parameters.
        """
        if len(args) == 1 and not isinstance(args[0], tuple):
            # String
            self._string = b(args[0], self.charset)
            return self
        else:
            # Pairs
            return self.append(*args, **kwargs)

    def remove(self, name):
        """::

            params = params.remove('foo')

        Remove parameters. Note that this method will normalize the parameters. ::

            # "bar=yada"
            Pyjo.Parameters.new('foo=bar&foo=baz&bar=yada').remove('foo')
        """
        pairs = self.pairs
        i = 0
        while i < len(pairs):
            if pairs[i][0] == name:
                pairs.pop(i)
            else:
                i += 1
        return self

    def to_bytes(self):
        """::

            bstring = params.to_bytes()

        Turn parameters into a bytes string.
        """
        # String
        charset = self.charset

        if self._string is not None:
            return url_escape(self._string, rb'^A-Za-z0-9\-._~!$&\'()*+,;=%:@/?')

        # Build pairs
        pairs = self.pairs
        if not pairs:
            return b''

        strpairs = []
        for name, value in pairs:
            if charset:
                name = b(name, charset)
                value = b(value, charset)

            name = url_escape(name, rb'^A-Za-z0-9\-._~!$\'()*,:@/?')
            value = url_escape(value, rb'^A-Za-z0-9\-._~!$\'()*,:@/?')

            name = name.replace(b'%20', b'+')
            value = value.replace(b'%20', b'+')

            strpairs.append(name + b'=' + value)

        return b'&'.join(strpairs)

    def to_dict(self):
        """::

            d = params.to_dict()

        Turn parameters into a :class:`dict`. Note that this method will normalize
        the parameters. ::

            # "baz"
            Pyjo.Parameters.new('foo=bar&foo=baz').to_dict()['foo'][1]
        """
        d = {}
        pairs = self.pairs
        for k, v in pairs:
            if k in d:
                if not isinstance(d[k], list):
                    d[k] = [d[k]]
                d[k].append(v)
            else:
                d[k] = v
        return d

    def to_str(self):
        """::

            string = params.to_str()

        Turn parameters into a string.
        """
        return self.to_bytes().decode('ascii')

    def _replace(self, name, value):
        pairs = self.pairs

        if isinstance(
            value,
            (
                list,
                tuple,
            ),
        ):
            values = value
        else:
            values = [value]

        i = 0

        while i < len(pairs) and len(values):
            if pairs[i][0] == name:
                pairs[i] = (
                    name,
                    values.pop(0),
                )
            i += 1

        while i < len(pairs):
            if pairs[i] == name:
                pairs.pop(i)
            else:
                i += 1

        while len(values):
            self.append(
                (name, values.pop(0)),
            )

        return self


new = Pyjo_Parameters.new
object = Pyjo_Parameters
