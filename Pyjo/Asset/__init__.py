"""
Pyjo.Asset - HTTP content storage base class
============================================
::

    import Pyjo.Asset

    class MyAsset(Pyjo.Asset.object):
        def add_chunk(self, chunk=b''):
            ...

        def close():
            ...

        def contains(self, chunk):
            ...

        def get_chunk(self, offset, maximum=131072):
            ...

        def move_to(self, dst):
            ...

        @property
        def mtime(self):
            ...

        @property
        def size(self):
            ...

        def slurp(self):
            ...

:mod:`Pyjo.Asset` is an abstract base class for HTTP content storage.

Events
------

:mod:`Pyjo.Asset` inherits all events from :mod:`Pyjo.EventEmitter`.

Classes
-------
"""

import Pyjo.EventEmitter

from Pyjo.Util import not_implemented


class Pyjo_Asset(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.Asset` inherits all attributes and methods from
    :mod:`Pyjo.EventEmitter` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.end_range = kwargs.get('end_range')
        """::

            end = asset.end_range
            asset.end_range = 8

        Pretend file ends earlier.
        """

        self.start_range = kwargs.get('start_range', 0)
        """::

            start = asset.start_range
            asset.start_range = 3

        Pretend file starts later.
        """

    def __del__(self):
        try:
            self.close()
        except:
            pass

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        self.close()

    @not_implemented
    def add_chunk(self, chunk=b''):
        """::

            asset = asset.add_chunk('foo bar baz')

        Add chunk of data to asset. Meant to be overloaded in a subclass.
        """
        pass

    def close(self):
        """::

            asset.close()

        Close asset immediately and free resources. Used by context manager.
        """
        pass

    @not_implemented
    def contains(self, chunk):
        """::

            position = asset.contains(b'bar')

        Check if asset contains a specific string. Meant to be overloaded
        in a subclass.
        """
        pass

    @not_implemented
    def get_chunk(self, offset, maximum=131072):
        """::

            bstream = asset.get_chunk(offset)
            bstream = asset.get_chunk(offset, maximum)

        Get chunk of data starting from a specific position, defaults to a maximum
        chunk size of ``131072`` bytes (128KB). Meant to be overloaded in a subclass.
        """
        pass

    @property
    def is_file(self):
        """::

            false = asset.is_file

        False.
        """
        return False

    @property
    def is_range(self):
        """::

            boolean = asset.is_range

        Check if asset has a :attr:`start_range` or :attr:`end_range`.
        """
        return bool(self.end_range or self.start_range)

    @not_implemented
    def move_to(self, dst):
        """::

            asset = asset.move_to('/home/pyjo/foo.txt')

        Move asset data into a specific file. Meant to be overloaded in a subclass.
        """
        pass

    @property
    @not_implemented
    def mtime(self):
        """::

            mtime = asset.mtime

        Modification time of asset. Meant to be overloaded in a subclass.
        """
        pass

    @property
    @not_implemented
    def size(self):
        """::

            size = asset.size

        Size of asset data in bytes. Meant to be overloaded in a subclass.
        """
        pass

    @not_implemented
    def slurp(self):
        """::

            bstring = asset.slurp()

        Read all asset data at once. Meant to be overloaded in a subclass.
        """
        pass


new = Pyjo_Asset.new
object = Pyjo_Asset
