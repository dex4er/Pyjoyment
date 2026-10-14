"""
Pyjo.Upload - Upload
====================
::

    import Pyjo.Upload

    upload = Pyjo.Upload.new()
    print(upload.filename)
    upload.move_to('/home/sri/foo.txt')

:mod:`Pyjo.Upload` is a container for uploaded files.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Upload <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Upload.pm>`_
of Mojolicious 9.49.
"""

import Pyjo.Asset
import Pyjo.Base
import Pyjo.Headers

import builtins

from typing import Self


type Anything = builtins.object


class Pyjo_Upload(Pyjo.Base.object):
    """
    :mod:`Pyjo.Upload` inherits all methods from :mod:`Pyjo.Base` and
    implements the following new ones.
    """

    def __init__(
        self,
        *,
        asset: Pyjo.Asset.object | None = None,
        filename: str | None = None,
        headers: Pyjo.Headers.object | None = None,
        name: str | None = None,
    ) -> None:
        """::

            upload = Pyjo.Upload.new()
            upload = Pyjo.Upload.new(name='foo', filename='foo.txt', asset=Pyjo.Asset.Memory.new())

        Construct a new :mod:`Pyjo.Upload` object.
        """
        self.asset = asset
        """::

            asset = upload.asset
            upload.asset = Pyjo.Asset.File.new()

        Asset containing the uploaded data, usually a :mod:`Pyjo.Asset.File`
        or :mod:`Pyjo.Asset.Memory` object.
        """

        self.filename = filename
        """::

            filename = upload.filename
            upload.filename = 'foo.txt'

        Name of the uploaded file.
        """

        self.headers = headers
        """::

            headers = upload.headers
            upload.headers = Pyjo.Headers.new()

        Headers for upload, usually a :mod:`Pyjo.Headers` object.
        """

        self.name = name
        """::

            name = upload.name
            upload.name = 'foo'

        Name of the upload.
        """

    def move_to(self, to: Anything) -> Self:
        """::

            upload = upload.move_to('/home/sri/foo.txt')

        Move uploaded data into a specific file.
        """
        self._asset().move_to(to)
        return self

    @property
    def size(self) -> int:
        """::

            size = upload.size

        Size of uploaded data in bytes.
        """
        return self._asset().size

    def slurp(self) -> bytes:
        """::

            content = upload.slurp()

        Read all uploaded data at once.
        """
        return self._asset().slurp()

    # The asset, which an upload without one does not have, as in Mojo
    def _asset(self) -> Pyjo.Asset.object:
        if (asset := self.asset) is None:
            raise AttributeError("'NoneType' object has no attribute 'slurp'")
        return asset


new = Pyjo_Upload.new
object = Pyjo_Upload
