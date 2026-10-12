
"""
Pyjo.Asset.Memory - In-memory storage for HTTP content
======================================================
::

    import Pyjo.Asset.Memory

    asset_mem = Pyjo.Asset.Memory.new()
    asset_mem.add_chunk(b'foo bar baz')
    print(asset_mem.slurp())

:mod:`Pyjo.Asset.Memory` is an in-memory storage backend for HTTP content.

Events
------

:mod:`Pyjo.Asset.Memory` inherits all events from :mod:`Pyjo.Asset` and can emit
the following new ones.

upgrade
^^^^^^^
::

    @content.on
    def upgrade(asset_mem, asset_file):
        ...

Emitted when asset gets upgraded to a :mod:`Pyjo.Asset.File` object. ::

    @content.on
    def upgrade(asset_mem, asset_file):
        asset_file.tmpdir = '/tmp'

Classes
-------
"""

import Pyjo.Asset.File

from Pyjo.Util import convert, getenv, notnone, spurtb, steady_time


MTIME = steady_time()


class Pyjo_Asset_Memory(Pyjo.Asset.object):
    """
    :mod:`Pyjo.Asset.Memory` inherits all attributes and methods from
    :mod:`Pyjo.Asset` and implements the following new ones.
    """

    mtime = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.auto_upgrade = kwargs.get('auto_upgrade', False)
        """::

            boolean = asset_mem.auto_upgrade
            asset_mem.auto_upgrade = boolean

        Try to detect if content size exceeds :attr:`max_memory_size` limit and
        automatically upgrade to a :mod:`Pyjo.Asset.File` object.
        """

        self.max_memory_size = notnone(kwargs.get('max_memory_size'), lambda: convert(getenv('PYJO_MAX_MEMORY_SIZE'), int, 262144))
        """::

            size = asset_mem.max_memory_size
            asset_mem.max_memory_size = 1024

        Maximum size in bytes of data to keep in memory before automatically upgrading
        to a :mod:`Pyjo.Asset.File` object, defaults to the value of the
        ``MOJO_MAX_MEMORY_SIZE`` environment variable or ``262144`` (256KB).
        """

        self.mtime = kwargs.get('mtime', MTIME)
        """::

            mtime = asset_mem.mtime
            asset_mem.mtime = 1408567500

        Modification time of asset, defaults to the time this class was loaded.
        """

        self._content = bytearray()

    def __repr__(self):
        """::

            string = repr(asset_mem)

        String representation of an object shown in console.
        """
        return f"<{self.__class__.__module__}.{self.__class__.__name__} _content={repr(self._content)}>"

    def add_chunk(self, chunk=b''):
        """::

            asset_mem = asset_mem.add_chunk(b'foo bar baz')
            asset_mem.auto_upgrade = True
            asset_file = asset_mem.add_chunk(b'abc' * 262144)

        Add chunk of data and upgrade to :mod:`Pyjo.Asset.File` object if necessary.
        """
        # Upgrade if necessary
        self._content.extend(chunk)
        if not self.auto_upgrade or self.size <= self.max_memory_size:
            return self

        asset_file = Pyjo.Asset.File.new()
        return asset_file.add_chunk(self.emit('upgrade', asset_file).slurp())

    def close(self):
        """::

            asset_mem.close()

        Close asset immediately and free resources.
        """
        self._content = bytearray()

    def contains(self, chunk):
        """::

            position = asset_mem.contains(b'bar')

        Check if asset contains a specific string.
        """
        start = self.start_range
        pos = notnone(self._content, b'').find(chunk, start)
        if start and pos >= 0:
            pos -= start
        end = self.end_range

        if end and (pos + len(chunk)) >= end:
            return -1
        else:
            return pos

    def get_chunk(self, offset, maximum=131072):
        """::

            chunk = asset_mem.get_chunk(offset)
            chunk = asset_mem.get_chunk(offset, maximum)

        Get chunk of data starting from a specific position, defaults to a maximum
        chunk size of ``131072`` bytes (128KB).
        """
        offset += self.start_range
        end = self.end_range
        if end and offset + maximum > end:
            maximum = end + 1 - offset

        return self._content[offset:offset + maximum]

    def move_to(self, dst):
        """::

            file = asset_mem.move_to('/home/pyjo/bar.txt')

        Move asset data into a specific file.
        """
        spurtb(self._content, dst)
        return self

    @property
    def size(self):
        """::

            size = asset_mem.size

        Size of asset data in bytes.
        """
        return len(notnone(self._content, b''))

    def slurp(self):
        """::

            bstring = asset_mem.slurp()

        Read all asset data at once.
        """
        return notnone(self._content, bytearray())


new = Pyjo_Asset_Memory.new
object = Pyjo_Asset_Memory
