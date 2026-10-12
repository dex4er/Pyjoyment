
"""
Pyjo.JSON.Pointer - JSON Pointers
=================================
::

    import Pyjo.JSON.Pointer

    pointer = Pyjo.JSON.Pointer.new({'foo': [23, 'bar']})
    print(pointer.get('/foo/1'))
    if pointer.contains('/foo'):
        print('Contains "/foo"')

:mod:`Pyjo.JSON.Pointer` is a relaxed implementation of
:rfc:`6901`.

Classes
-------
"""

import Pyjo.Base


class Pyjo_JSON_Pointer(Pyjo.Base.object):
    """
    :mod:`Pyjo.JSON.Pointer` inherits all attributes and methods from
    :mod:`Pyjo.Base` and implements the following new ones.
    """

    def __init__(self, data=None):
        """::

            pointer = Pyjo.JSON.Pointer.new()
            pointer = Pyjo.JSON.Pointer.new({'foo': 'bar'})

        Build new :mod:`Pyjo.JSON.Pointer` object.
        """

        self.data = data
        """::

            data = pointer.data
            pointer.data = {'foo': 'bar'}

        Data structure to be processed.
        """

    def contains(self, pointer):
        """::

            boolean = pointer.contains('/foo/1')

        Check if :attr:`data` contains a value that can be identified with the given
        JSON Pointer. ::

            # True
            Pyjo.JSON.Pointer.new({u'♥': 'pyjo'}).contains(u'/♥')
            Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5]}).contains('/foo')
            Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5]}).contains('/baz/1')

            # False
            Pyjo.JSON.Pointer.new({u'♥': 'pyjo'}).contains(u'/☃')
            Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5]}).contains('/bar')
            Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5]}).contains('/baz/9')
        """
        return self._pointer(True, pointer)

    def get(self, pointer):
        """::

            value = pointer.get('/foo/bar')

        Extract value from L</"data"> identified by the given JSON Pointer. ::

            # "pyjo"
            Pyjo.JSON.Pointer.new({u'♥': 'pyjo'}).get(u'/♥')

            # "bar"
            Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5, 6]}).get('/foo')

            # "4"
            Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5, 6]}).get('/baz/0')

            # "6"
            Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5, 6]}).get('/baz/2')

        Numeric key is prefered before string key. ::

            # "number"
            Pyjo.JSON.Pointer.new({4: 'number', '4': 'string'}).get('4')
        """
        return self._pointer(False, pointer)

    def _pointer(self, contains, pointer):
        data = self.data
        if not pointer.startswith('/'):
            return data

        for p in pointer[1:].split('/'):
            p = p.replace('~1', '/').replace('~0', '~')

            # dict with int as key
            if isinstance(data, dict) and p.isdigit() and int(p) in data:
                data = data[int(p)]

            # dict with str as key
            elif isinstance(data, dict) and p in data:
                data = data[p]

            # list
            elif isinstance(data, (list, tuple)) and p.isdigit() and len(data) > int(p):
                data = data[int(p)]

            else:
                if contains:
                    return False
                else:
                    return

        if contains:
            return True
        else:
            return data


new = Pyjo_JSON_Pointer.new
object = Pyjo_JSON_Pointer
