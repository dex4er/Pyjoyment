"""
Pyjo.JSON.Pointer - JSON Pointers
=================================
::

    import Pyjo.JSON.Pointer

    pointer = Pyjo.JSON.Pointer.new({'foo': [23, 'bar']})
    print(pointer.get('/foo/1'))
    if pointer.contains('/foo'):
        print('Contains "/foo".')

:mod:`Pyjo.JSON.Pointer` is an implementation of :rfc:`6901`.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::JSON::Pointer <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/JSON/Pointer.pm>`_
of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.Base

import re

from typing import Any, cast


class Pyjo_JSON_Pointer(Pyjo.Base.object):
    """
    :mod:`Pyjo.JSON.Pointer` inherits all methods from :mod:`Pyjo.Base` and
    implements the following new ones.
    """

    def __init__(self, data: Any = None) -> None:
        """::

            pointer = Pyjo.JSON.Pointer.new()
            pointer = Pyjo.JSON.Pointer.new({'foo': 'bar'})

        Build new :mod:`Pyjo.JSON.Pointer` object.
        """
        self.data: Any = data
        """::

            data = pointer.data
            pointer.data = {'foo': 'bar'}

        Data structure to be processed.
        """

    def contains(self, pointer: str) -> bool:
        """::

            boolean = pointer.contains('/foo/1')

        Check if :attr:`data` contains a value that can be identified with the
        given JSON Pointer. ::

            # True
            Pyjo.JSON.Pointer.new('just a string').contains('')
            Pyjo.JSON.Pointer.new({'♥': 'pyjoyment'}).contains('/♥')
            Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5]}).contains('/foo')
            Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5]}).contains('/baz/1')

            # False
            Pyjo.JSON.Pointer.new({'♥': 'pyjoyment'}).contains('/☃')
            Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5]}).contains('/bar')
            Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5]}).contains('/baz/9')
        """
        return self._pointer(False, pointer) is not None

    def get(self, pointer: str) -> Any:
        """::

            value = pointer.get('/foo/bar')

        Extract value from :attr:`data` identified by the given JSON Pointer. ::

            # "just a string"
            Pyjo.JSON.Pointer.new('just a string').get('')

            # "pyjoyment"
            Pyjo.JSON.Pointer.new({'♥': 'pyjoyment'}).get('/♥')

            # "bar"
            Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5, 6]}).get('/foo')

            # 4
            Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5, 6]}).get('/baz/0')

            # 6
            Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5, 6]}).get('/baz/2')
        """
        return self._pointer(True, pointer)

    def _pointer(self, get: bool, pointer: str) -> Any:
        data: Any = self.data
        if not pointer.startswith('/'):
            return None if len(pointer) else data if get else True
        for p in pointer[1:].split('/'):
            p = p.replace('~1', '/').replace('~0', '~')

            # Hash
            if isinstance(data, dict) and p in data:
                data = cast(dict[str, Any], data)[p]

            # Array
            elif isinstance(data, (list, tuple)) and re.fullmatch(r'[0-9]+', p) and len(cast(list[Any], data)) > int(p):
                data = cast(list[Any], data)[int(p)]

            # Nothing
            else:
                return None

        return data if get else True


new = Pyjo_JSON_Pointer.new
object = Pyjo_JSON_Pointer
