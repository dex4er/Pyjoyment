"""
Pyjo.Asset.File - File storage for HTTP content
===============================================
::

    import Pyjo.Asset.File

    # Temporary file
    with Pyjo.Asset.File.new() as asset_file:
        asset_file.add_chunk(b'foo bar baz')
        if asset_file.contains(b'bar'):
            print('File contains "bar"')
        print(asset_file.slurp())

    # Existing file
    asset_file = Pyjo.Asset.File.new(path='/home/pyjo/foo.txt')
    asset_file.move_to('/tmp/yada.txt')
    print(asset_file.slurp())

:mod:`Pyjo.Asset.File` is an file storage backend for HTTP content.

Events
------

:mod:`Pyjo.Asset.File` inherits all events from :mod:`Pyjo.Asset`.

Classes
-------
"""

import Pyjo.Asset

from Pyjo.Util import b, getenv, md5_sum, notnone, rand, slurpb, steady_time

import errno
import os
import tempfile


class Pyjo_Asset_File(Pyjo.Asset.object):
    """
    :mod:`Pyjo.Asset.File` inherits all attributes and methods from
    :mod:`Pyjo.Asset` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.cleanup = kwargs.get('cleanup')
        """::

            boolean = asset_file.cleanup
            asset_file.cleanup = boolean

        Delete :attr:`path` automatically once the file is not used anymore.
        """

        self.path = kwargs.get('path')
        """::

            path = asset_file.path
            asset_file.path = '/home/pyjo/foo.txt'

        File path used to create :attr:`handle`, can also be automatically generated if
        necessary.
        """

        self.tmpdir = notnone(kwargs.get('tmpdir'), lambda: getenv('PYJO_TMPDIR') or tempfile.gettempdir())
        """::

            tmpdir = asset_file.tmpdir
            asset_file.tmpdir = '/tmp'

        Temporary directory used to generate :attr:`path`, defaults to the value of the
        ``PYJO_TMPDIR`` environment variable or auto detection.
        """

        self._handle = kwargs.get('handle')

    def __del__(self):
        try:
            self.close()
        except:
            pass

    def __repr__(self):
        """::

            string = repr(asset_file)

        String representation of an object shown in console.
        """
        return (
            f'<{self.__class__.__module__}.{self.__class__.__name__} handle={repr(self.handle)} path={repr(self.path)}>'
        )

    def add_chunk(self, chunk=b''):
        """::

            asset_file = asset_file.add_chunk(b'foo bar baz')

        Add chunk of data.
        """
        self.handle.write(chunk)
        return self

    def close(self):
        """::

            asset_file.close()

        Close asset immediately and free resources.
        """
        if self.handle:
            self.handle.close()

        if self.cleanup and self.path is not None:
            if os.access(self.path, os.W_OK):
                os.unlink(self.path)
            self.path = None

    def contains(self, bstring):
        """::

            position = asset_file.contains(b'bar')

        Check if asset contains a specific string.
        """
        handle = self.handle
        handle.seek(self.start_range, os.SEEK_SET)

        # Calculate window size
        end = notnone(self.end_range, self.size)
        length = len(bstring)
        size = max(length, 131072)
        size = min(size, end - self.start_range)

        # Sliding window search
        offset = 0
        window = handle.read(length)
        start = len(window)

        while offset < end:
            # Read as much as possible
            diff = end - (start + offset)
            buf = handle.read(min(diff, size))
            read = len(buf)
            window += buf

            # Search window
            pos = window.find(bstring)
            if pos >= 0:
                return offset + pos

            if read == 0:
                return -1

            offset += read
            if offset == end:
                return -1

            window = window[read:]

        return -1

    def get_chunk(self, offset, maximum=131072):
        """::

            bstream = asset.get_chunk(offset)
            bstream = asset.get_chunk(offset, maximum)

        Get chunk of data starting from a specific position, defaults to a maximum
        chunk size of ``131072`` bytes (128KB).
        """
        offset += self.start_range
        handle = self.handle
        handle.seek(offset, os.SEEK_SET)

        end = self.end_range
        if end is not None:
            chunk = end + 1 - offset
            if chunk <= 0:
                return b''
            else:
                return handle.read(min(chunk, maximum))
        else:
            return handle.read(maximum)

    @property
    def is_file(self):
        """::

            true = asset_file.is_file

        True.
        """
        return True

    def move_to(self, dst):
        """::

            asset_file = asset_file.move_to('/home/pyjo/bar.txt')

        Move asset data into a specific file and disable :attr:`cleanup`.
        """
        # Windows requires that the handle is closed
        self.handle.close()
        self._handle = None

        # Move file and prevent clean up
        src = self.path
        os.rename(src, dst)
        self.path = dst
        self.cleanup = False
        return self

    @property
    def mtime(self):
        """::

            mtime = asset_file.mtime

        Modification time of asset.
        """
        return os.fstat(self.handle.fileno()).st_mtime

    @property
    def size(self):
        """::

            size = asset_file.size

        Size of asset data in bytes. Reading the size flushes writing buffer.
        """
        self.handle.flush()
        return os.fstat(self.handle.fileno()).st_size

    def slurp(self):
        """::

            bstring = asset_file.slurp()

        Read all asset data at once.
        """
        if self.path is None:
            return b''
        else:
            return slurpb(self.path)

    @property
    def handle(self):
        """::

            handle = asset_file.handle
            asset_file.handle = open('/home/pyjo/foo.txt', 'rb')

        Filehandle, created on demand.
        """
        if self._handle is not None:
            return self._handle

        # Open existing file
        path = self.path
        if path is not None and os.path.isfile(path):
            handle = open(path, 'rb')
            return handle

        # Open new or temporary file
        base = os.path.join(self.tmpdir, 'pyjo.tmp')
        if path is not None:
            name = path
            fd = os.open(name, os.O_APPEND | os.O_CREAT | os.O_EXCL | os.O_RDWR)
        else:
            name = base
            while True:
                try:
                    fd = os.open(name, os.O_APPEND | os.O_CREAT | os.O_EXCL | os.O_RDWR)
                except OSError as e:
                    if e.errno == errno.EEXIST:
                        name = f'{base}.{md5_sum(b(f"{steady_time()}{os.getpid()}{rand()}"))}'
                    else:
                        raise e
                else:
                    break

        self.path = name

        # Enable automatic cleanup
        if self.cleanup is None:
            self.cleanup = True

        self._handle = os.fdopen(fd, 'a+b', 0)
        return self._handle


new = Pyjo_Asset_File.new
object = Pyjo_Asset_File
