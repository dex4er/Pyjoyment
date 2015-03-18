# -*- coding: utf-8 -*-

"""
Pyjo.Asset.Memory - In-memory storage for HTTP content
======================================================
::

    import Pyjo.Asset.Memory

    mem = Pyjo.Asset.Memory.new()
    mem.add_chunk('foo bar baz')
    print(mem.slurp())

:mod:`Pyjo.Asset.Memory` is an in-memory storage backend for HTTP content.

Events
------

:mod:`Pyjo.Asset.Memory` inherits all events from :mod:`Pyjo.Asset` and can emit
the following new ones.

upgrade
^^^^^^^
::

    @content.on
    def upgrade(mem, file):
        ...

Emitted when asset gets upgraded to a :mod:`Pyjo.Asset.File` object. ::

    @content.on
    def upgrade(mem, file):
        file.tmpdir = '/tmp'

Classes
-------
"""

import Pyjo.Asset

from Pyjo.Util import notnone, spurt


class Pyjo_Asset_Memory(Pyjo.Asset.object):
    """
    :mod:`Pyjo.Asset.Memory` inherits all attributes and methods from
    :mod:`Pyjo.Asset` and implements the following new ones.
    """

    _content = b''

    def add_chunk(self, chunk=b''):
        """::

            asset_mem = mem.add_chunk(b'foo bar baz')
            asset_file = mem.add_chunk(b'abc' * 262144)

        Add chunk of data and upgrade to :mod:`Pyjo.Asset.File` object if necessary.
        """
        # Upgrade if necessary
        self._content += chunk
        return self
        # TODO upgrade

    def contains(self, bstring):
        """::

            position = mem.contains(b'bar')

        Check if asset contains a specific string.
        """
        start = self.start_range
        pos = notnone(self._content, b'').find(bstring, start)
        if start and pos >= 0:
            pos -= start
        end = self.end_range

        if end and (pos + len(bstring)) >= end:
            return -1
        else:
            return pos

    def get_chunk(self, offset, maximum=131072):
        """::

            bstream = mem.get_chunk(offset)
            bstream = mem.get_chunk(offset, maximum)

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

            file = mem.move_to('/home/pyjo/bar.txt')

        Move asset data into a specific file.
        """
        spurt(self._content, dst)
        return self

    @property
    def size(self):
        """::

            size = mem.size

        Size of asset data in bytes.
        """
        return len(notnone(self._content, b''))

    def slurp(self):
        """::

            bstring = mem.slurp()

        Read all asset data at once.
        """
        return notnone(self._content, b'')


new = Pyjo_Asset_Memory.new
object = Pyjo_Asset_Memory  # @ReservedAssignment
