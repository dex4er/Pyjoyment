r"""
Pyjo.Content.Single - HTTP content
==================================
::

    import Pyjo.Content.Single

    single = Pyjo.Content.Single.new()
    single.parse(b'Content-Length: 12\x0d\x0a\x0d\x0aHello World!')
    print(single.headers.content_length)

:mod:`Pyjo.Content.Single` is a container for HTTP content, based on
`RFC 7230 <https://tools.ietf.org/html/rfc7230>`_ and
`RFC 7231 <https://tools.ietf.org/html/rfc7231>`_.

Events
------

:mod:`Pyjo.Content.Single` inherits all events from :mod:`Pyjo.Content` and
can emit the following new ones.

upgrade
~~~~~~~
::

    single.on('upgrade', lambda single, multi: ...)

Emitted when content gets upgraded to a :mod:`Pyjo.Content.MultiPart`
object. ::

    @single.on('upgrade')
    def upgrade(single, multi):
        if m := re.search(r'multipart/([^;]+)', multi.headers.content_type, re.I):
            print(f'Multipart: {m[1]}')

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Content::Single <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Content/Single.pm>`_
of Mojolicious 9.49.
"""

import Pyjo.Asset
import Pyjo.Asset.Memory
import Pyjo.Content
import Pyjo.Content.MultiPart

from typing import Any, Self


class Pyjo_Content_Single(Pyjo.Content.object):
    """
    :mod:`Pyjo.Content.Single` inherits all methods from :mod:`Pyjo.Content`
    and implements the following new ones.
    """

    def __init__(self, *, asset: Pyjo.Asset.object | None = None, auto_upgrade: bool = True, **kwargs: Any) -> None:
        """::

            single = Pyjo.Content.Single.new()
            single = Pyjo.Content.Single.new(asset=Pyjo.Asset.File.new())

        Construct a new :mod:`Pyjo.Content.Single` object and subscribe to
        event ``read`` with default content parser.
        """
        super().__init__(**kwargs)

        self.auto_upgrade = auto_upgrade
        """::

            boolean = single.auto_upgrade
            single.auto_upgrade = boolean

        Try to detect multipart content and automatically upgrade to a
        :mod:`Pyjo.Content.MultiPart` object, defaults to a true value.
        """

        self._asset = asset
        self._body_size: int | None = None
        self._read = self.on('read', _read)

    @property
    def asset(self) -> Pyjo.Asset.object:
        """::

            asset = single.asset
            single.asset = Pyjo.Asset.Memory.new()

        The actual content, defaults to a :mod:`Pyjo.Asset.Memory` object
        with :attr:`Pyjo.Asset.Memory.Pyjo_Asset_Memory.auto_upgrade` enabled.
        """
        if self._asset is None:
            self._asset = Pyjo.Asset.Memory.new(auto_upgrade=True)
        return self._asset

    @asset.setter
    def asset(self, value: Pyjo.Asset.object) -> None:
        self._asset = value

    def body_contains(self, chunk: bytes) -> bool:
        """::

            boolean = single.body_contains(b'1234567')

        Check if content contains a specific string.
        """
        return self.asset.contains(chunk) >= 0

    @property
    def body_size(self) -> int:
        """::

            size = single.body_size

        Content size in bytes.
        """
        if self.is_dynamic:
            return int(self._number(self.headers.content_length) or 0)
        if self._body_size is None:
            self._body_size = self.asset.size
        return self._body_size

    def clone(self) -> Self | None:
        """::

            clone = single.clone()

        Return a new :mod:`Pyjo.Content.Single` object cloned from this
        content if possible, otherwise return ``None``.
        """
        if (clone := super().clone()) is None:
            return None
        clone.asset = self.asset
        return clone

    def get_body_chunk(self, offset: int) -> bytes | None:
        """::

            chunk = single.get_body_chunk(0)

        Get a chunk of content starting from a specific position. Note that it
        might not be possible to get the same chunk twice if content was
        generated dynamically.
        """
        if self.is_dynamic:
            return self.generate_body_chunk(offset)
        return self.asset.get_chunk(offset)

    def parse(self, chunk: bytes | None = None) -> Pyjo.Content.object:
        r"""::

            single = single.parse(b'Content-Length: 12\x0d\x0a\x0d\x0aHello World!')
            multi = single.parse(b'Content-Type: multipart/form-data\x0d\x0a\x0d\x0a')

        Parse content chunk and upgrade to :mod:`Pyjo.Content.MultiPart`
        object if necessary.
        """
        # Parse headers
        self._parse_until_body(chunk)

        # Parse body
        if not (self.auto_upgrade and self.boundary is not None):
            return super().parse()

        # Content needs to be upgraded to multipart, with the state and the subscribers of this content, as %$self
        self.unsubscribe('read', self._read)
        multi = Pyjo.Content.MultiPart.new()
        read = multi.subscribers('read')[:]
        multi.__dict__.update(self.__dict__)
        for cb in read:
            multi.on('read', cb)
        self.emit('upgrade', multi)
        return multi.parse()


# The default content parser
def _read(single: Pyjo_Content_Single, chunk: bytes) -> None:
    single.asset = single.asset.add_chunk(chunk)


new = Pyjo_Content_Single.new
object = Pyjo_Content_Single
Single = Pyjo_Content_Single
