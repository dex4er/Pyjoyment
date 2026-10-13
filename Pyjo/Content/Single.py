r"""
Pyjo.Content.Single - HTTP content
==================================
::

    import Pyjo.Content.Single

    single = Pyjo.Content.Single.new()
    single.parse(b"Content-Length: 12\x0d\x0a\x0d\x0aHello World!")
    print(single.headers.content_length)

:mod:`Pyjo.Content.Single` is a container for HTTP content based on
:rfc:`7230` and
:rfc:`7231`.

Events
------

:mod:`Pyjo.Content.Single` inherits all events from :mod:`Pyjo.Content` and can
emit the following new ones.

upgrade
^^^^^^^
::

    @single.on
    def upgrade(single, multi):
        ...

Emitted when content gets upgraded to a :mod:`Pyjo.Content.MultiPart` object. ::

    from Pyjo.Regexp import r

    @single.on
    def upgrade(single, multi):
        m = r(r'multipart\/([^;]+)', 'i').search(multi.headers.content_type)
        if m:
            print("Multipart: {0}".format(m.group(1)))

Classes
-------
"""

import Pyjo.Asset.Memory
import Pyjo.Content.MultiPart
import Pyjo.String.Mixin

from Pyjo.Util import convert, notnone


class Pyjo_Content_Single(Pyjo.Content.object, Pyjo.String.Mixin.object):
    """
    :mod:`Pyjo.Content.Single` inherits all attributes and methods from
    :mod:`Pyjo.Content` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        """::

            single = Pyjo.Content.Single.new()
            single = Pyjo.Content.Single.new(asset=Pyjo.Asset.File.new())

        Construct a new :mod:`Pyjo.Content.Single` object and subscribe to ``read``
        event with default content parser.
        """
        super().__init__(**kwargs)

        self.asset = notnone(kwargs.get('asset'), lambda: Pyjo.Asset.Memory.new(auto_upgrade=True))
        """::

            asset = single.asset
            single.asset = Pyjo.Asset.Memory.new()

        The actual content, defaults to a :mod:`Pyjo.Asset.Memory` object with
        :attr:`Pyjo.Asset.Memory.auto_upgrade` enabled.
        """

        self.auto_upgrade = kwargs.get('auto_upgrade', True)
        """::

            boolean = single.auto_upgrade
            single.auto_upgrade = boolean

        Try to detect multipart content and automatically upgrade to a
        :mod:`Pyjo.Content.MultiPart` object, defaults to a true value.
        """

        def read_cb(content, chunk):
            content.set(asset=content.asset.add_chunk(chunk))

        self._on_read = self.on('read', read_cb)

    def body_contains(self, chunk):
        """::

            boolean = single.body_contains(b'1234567')

        Check if content contains a specific string.
        """
        return self.asset.contains(chunk) >= 0

    @property
    def body_size(self):
        """::

            size = single.body_size

        Content size in bytes.
        """
        if self._dynamic:
            return convert(self.headers.content_length, int, 0)
        else:
            return self.asset.size

    def clone(self):
        """::

            clone = single.clone()

        Clone content if possible, otherwise return ``None``.
        """
        clone = super().clone()
        if clone is not None:
            clone.asset = self.asset
            return clone
        else:
            return

    def get_body_chunk(self, offset):
        """::

            bstring = single.get_body_chunk(0)

        Get a chunk of content starting from a specific position.
        """
        if self._dynamic:
            return self.generate_body_chunk(offset)
        else:
            return self.asset.get_chunk(offset)

    def parse(self, chunk):
        r"""::

            single = single.parse(b"Content-Length: 12\x0d\x0a\x0d\x0aHello World!")
            multi = single.parse(b"Content-Type: multipart/form-data\x0d\x0a\x0d\x0a")

        Parse content chunk and upgrade to :mod:`Pyjo.Content.MultiPart` object if
        necessary.
        """
        # Parse headers
        self._parse_until_body(chunk)

        # Parse body
        if not self.auto_upgrade or self.boundary is None:
            return super().parse()

        # Content needs to be upgraded to multipart
        self.unsubscribe('read', self._on_read)
        multi = Pyjo.Content.MultiPart.new(**vars(self))
        self.emit('upgrade', multi)
        return multi.parse()


new = Pyjo_Content_Single.new
object = Pyjo_Content_Single
