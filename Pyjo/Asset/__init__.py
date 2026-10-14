"""
Pyjo.Asset - HTTP content storage base class
============================================
::

    import Pyjo.Asset

    class MyAsset(Pyjo.Asset.object):
        def add_chunk(self, chunk): ...
        def contains(self, string): ...
        def get_chunk(self, offset, max=None): ...
        def move_to(self, to): ...
        @property
        def mtime(self): ...
        @property
        def size(self): ...
        def slurp(self): ...
        def to_file(self): ...

:mod:`Pyjo.Asset` is an abstract base class for HTTP content storage
backends, like :mod:`Pyjo.Asset.File` and :mod:`Pyjo.Asset.Memory`.

Events
------

:mod:`Pyjo.Asset` inherits all events from :mod:`Pyjo.EventEmitter`.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Asset <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Asset.pm>`_
of Mojolicious 9.49.
"""

import Pyjo.EventEmitter

import builtins

from typing import Self


type Anything = builtins.object


class Pyjo_Asset(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.Asset` inherits all methods from :mod:`Pyjo.EventEmitter` and
    implements the following new ones.
    """

    def __init__(self, *, end_range: int | None = None, start_range: int = 0) -> None:
        """::

            asset = Pyjo.Asset.new()
            asset = Pyjo.Asset.new(start_range=3, end_range=8)

        Construct a new :mod:`Pyjo.Asset` object.
        """
        super().__init__()

        self.end_range = end_range
        """::

            end = asset.end_range
            asset.end_range = 8

        Pretend file ends earlier.
        """

        self.start_range = start_range
        """::

            start = asset.start_range
            asset.start_range = 3

        Pretend file starts later.
        """

    def add_chunk(self, chunk: bytes) -> 'Pyjo_Asset':
        """::

            asset = asset.add_chunk(b'foo bar baz')

        Add chunk of data to asset. Meant to be overloaded in a subclass.
        """
        raise NotImplementedError('Method "add_chunk" not implemented by subclass')

    def contains(self, string: bytes) -> int:
        """::

            position = asset.contains(b'bar')

        Check if asset contains a specific string. Meant to be overloaded in a
        subclass.
        """
        raise NotImplementedError('Method "contains" not implemented by subclass')

    def get_chunk(self, offset: int, max: int | None = None) -> bytes:
        """::

            chunk = asset.get_chunk(offset)
            chunk = asset.get_chunk(offset, max)

        Get chunk of data starting from a specific position, defaults to a
        maximum chunk size of ``131072`` bytes (128KiB). Meant to be overloaded
        in a subclass.
        """
        raise NotImplementedError('Method "get_chunk" not implemented by subclass')

    @property
    def is_file(self) -> bool:
        """::

            boolean = asset.is_file

        False, this is not a :mod:`Pyjo.Asset.File` object.
        """
        return False

    @property
    def is_range(self) -> bool:
        """::

            boolean = asset.is_range

        Check if asset has a :attr:`start_range` or :attr:`end_range`.
        """
        return bool(self.end_range or self.start_range)

    def move_to(self, to: Anything) -> Self:
        """::

            asset = asset.move_to('/home/sri/foo.txt')

        Move asset data into a specific file. Meant to be overloaded in a
        subclass.
        """
        raise NotImplementedError('Method "move_to" not implemented by subclass')

    @property
    def mtime(self) -> float:
        """::

            mtime = asset.mtime

        Modification time of asset. Meant to be overloaded in a subclass.
        """
        raise NotImplementedError('Method "mtime" not implemented by subclass')

    @property
    def size(self) -> int:
        """::

            size = asset.size

        Size of asset data in bytes. Meant to be overloaded in a subclass.
        """
        raise NotImplementedError('Method "size" not implemented by subclass')

    def slurp(self) -> bytes:
        """::

            content = asset.slurp()

        Read all asset data at once. Meant to be overloaded in a subclass.
        """
        raise NotImplementedError('Method "slurp" not implemented by subclass')

    def to_file(self) -> 'Pyjo_Asset':
        """::

            file = asset.to_file()

        Convert asset to :mod:`Pyjo.Asset.File` object. Meant to be overloaded
        in a subclass.
        """
        raise NotImplementedError('Method "to_file" not implemented by subclass')


new = Pyjo_Asset.new
object = Pyjo_Asset
