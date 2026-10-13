r"""
Pyjo.File - File system paths
=============================
::

    import Pyjo.File

    # Portably deal with file system paths
    path = Pyjo.File.new('/home/sri/.vimrc')
    print(path.slurp())
    print(path.dirname())
    print(path.basename())
    print(path.extname)
    print(path.sibling('.bashrc'))

    # Use the alternative constructor
    from Pyjo.File import path
    path = path('/tmp/foo/bar').make_path()
    path.child('test.txt').spew('Hello Pyjo!')

:mod:`Pyjo.File` is a container for file system paths that provides a
friendly API for dealing with different operating systems. It keeps the path
as it is given, and it is an :class:`os.PathLike`, so the standard library
takes it where it takes a path. ::

    # Use the path with the standard library
    path = Pyjo.File.new('/home/sri/test')
    with open(path) as f:
        print(f.read())

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::File <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/File.pm>`_
of Mojolicious 9.49.

Functions
---------
"""

import Pyjo.Base
import Pyjo.Collection
import Pyjo.String.Mixin

from Pyjo.Util import decode, encode

import builtins
import inspect
import os
import pathlib
import random
import re
import shutil
import string
import tempfile as _tempfile
import weakref

from collections.abc import Iterator
from typing import IO, Any, NoReturn, Self, cast


_random = random.SystemRandom()


type Anything = builtins.object


class Pyjo_File(Pyjo.Base.object, Pyjo.String.Mixin.object):
    """
    :mod:`Pyjo.File` inherits all methods from :mod:`Pyjo.Base` and
    :mod:`Pyjo.String.Mixin` and implements the following new ones.
    """

    def __init__(self, *parts: Anything) -> None:
        """::

            path = Pyjo.File.new()
            path = Pyjo.File.new('/home/sri/.vimrc')
            path = Pyjo.File.new('/home', 'sri', '.vimrc')
            path = Pyjo.File.new(pathlib.Path('/home/sri/.vimrc'))
            path = Pyjo.File.new(tempfile.NamedTemporaryFile())
            path = Pyjo.File.new(tempfile.TemporaryDirectory())

        Construct a new :mod:`Pyjo.File` object, defaults to using the current
        working directory. A temporary file or directory is kept as long as the
        object is. ::

            # "foo/bar/baz.txt" (on UNIX)
            Pyjo.File.new('foo', 'bar', 'baz.txt')
        """
        if any(p is None for p in parts):
            raise ValueError('Invalid path')

        # Not in Mojolicious: a temporary file or directory of the standard
        # library, kept as Mojo keeps the object of File::Temp
        self._temp = parts[0] if len(parts) == 1 and _is_temp(parts[0]) else None
        self._path = (
            _str(parts[0])
            if len(parts) == 1
            else _catfile(*map(_str, parts))
            if len(parts)
            else _canonpath(os.getcwd())
        )

    def __bool__(self) -> bool:
        """::

            boolean = bool(path)

        Always true.
        """
        return True

    def __fspath__(self) -> str:
        """::

            string = os.fspath(path)

        The path for the standard library, as :meth:`to_str` gives it.
        """
        return self._path

    def __getitem__(self, index: int) -> str:
        """::

            part = path[0]

        A part of the path, as :meth:`to_list` gives it.
        """
        return self.to_list()[index]

    def __iter__(self) -> Iterator[str]:
        """::

            for part in path:
                ...

        Iterate the parts of the path, as :meth:`to_list` gives them.
        """
        return iter(self.to_list())

    def __len__(self) -> int:
        """::

            size = len(path)

        Number of the parts of the path.
        """
        return len(self.to_list())

    def basename(self, *suffixes: str) -> str:
        """::

            name = path.basename()
            name = path.basename('.txt')

        Return the last level of the path, as ``File::Basename`` of Perl does. ::

            # ".vimrc" (on UNIX)
            path('/home/sri/.vimrc').basename()

            # "test" (on UNIX)
            path('/home/sri/test.txt').basename('.txt')
        """
        return _basename(self._path, *suffixes)

    def child(self, *parts: Anything) -> Self:
        """::

            child = path.child('.vimrc')

        Return a new :mod:`Pyjo.File` object relative to the path. A child of
        a temporary directory keeps the directory as long as it is kept. ::

            # "/home/sri/.vimrc" (on UNIX)
            path('/home').child('sri', '.vimrc')
        """
        child = self.new(self._path, *parts)
        # Unlike Mojolicious: Perl keeps the temporary directory of
        # tempdir()->child(...) until the end of the statement, Python frees it
        # as soon as child() returns, so the child keeps it
        child._temp = self._temp
        return child

    def chmod(self, mode: int) -> Self:
        """::

            path = path.chmod(0o644)

        Change file permissions.
        """
        try:
            os.chmod(self._path, mode)
        except OSError as e:
            _croak(e, f'Can\'t chmod file "{self._path}"')
        return self

    def copy_to(self, to: Anything) -> Self:
        """::

            destination = path.copy_to('/home/sri')
            destination = path.copy_to('/home/sri/.vimrc.backup')

        Copy file with :mod:`shutil` and return the destination as a
        :mod:`Pyjo.File` object.
        """
        destination = self._destination(to)
        try:
            shutil.copyfile(self._path, destination)
        except OSError as e:
            _croak(e, f'Can\'t copy file "{self._path}" to "{_str(to)}"')
        return self.new(destination)

    def dirname(self) -> Self:
        """::

            name = path.dirname()

        Return all but the last level of the path, as ``File::Basename`` of Perl
        does, as a :mod:`Pyjo.File` object. ::

            # "/home/sri" (on UNIX)
            path('/home/sri/.vimrc').dirname()
        """
        return self.new(_dirname(self._path))

    # Left out from Mojolicious: download, until Pyjo.UserAgent is ported

    @property
    def extname(self) -> str:
        """::

            ext = path.extname

        Return file extension of the path. ::

            # "js"
            path('/home/sri/test.js').extname
        """
        return m[1] if (m := re.search(r'.+\.([^.]+)$', self.basename())) else ''

    @property
    def is_abs(self) -> bool:
        """::

            boolean = path.is_abs

        Check if the path is absolute. ::

            # True (on UNIX)
            path('/home/sri/.vimrc').is_abs

            # False (on UNIX)
            path('.vimrc').is_abs
        """
        return os.path.isabs(self._path)

    def list(self, *, dir: bool = False, hidden: bool = False) -> 'Pyjo.Collection.object[Self]':
        """::

            collection = path.list()
            collection = path.list(hidden=True)

        List all files in the directory and return a :mod:`Pyjo.Collection`
        object containing the results as :mod:`Pyjo.File` objects. The list does
        not include ``.`` and ``..``. ::

            # List files
            for file in path('/home/sri/myapp').list().each():
                print(file)

        These options are currently available:

        ``dir``
            Include directories.

        ``hidden``
            Include hidden files.
        """
        if not os.path.isdir(self._path):
            return Pyjo.Collection.new()
        try:
            names = os.listdir(self._path)
        except OSError as e:
            _croak(e, f'Can\'t open directory "{self._path}"')
        if not hidden:
            names = [n for n in names if not n.startswith('.')]
        files = [_catfile(self._path, n) for n in names]
        if not dir:
            files = [f for f in files if not os.path.isdir(f)]

        return Pyjo.Collection.object(self.new(f) for f in sorted(files))

    def list_tree(
        self, *, dir: bool = False, hidden: bool = False, max_depth: int | None = None
    ) -> 'Pyjo.Collection.object[Self]':
        """::

            collection = path.list_tree()
            collection = path.list_tree(hidden=True)

        List all files recursively in the directory and return a
        :mod:`Pyjo.Collection` object containing the results as
        :mod:`Pyjo.File` objects. The list does not include ``.`` and ``..``,
        and symbolic links to directories are not followed. ::

            # List all templates
            for file in path('/home/sri/myapp/templates').list_tree().each():
                print(file)

        These options are currently available:

        ``dir``
            Include directories.

        ``hidden``
            Include hidden files and directories.

        ``max_depth``
            Maximum number of levels to descend when searching for files.
        """
        if not os.path.isdir(self._path):
            return Pyjo.Collection.new()

        results: builtins.list[Self] = []

        def walk(path: str, depth: int) -> None:
            try:
                names = sorted(os.listdir(path))
            except OSError:
                return
            if not hidden:
                names = [n for n in names if not n.startswith('.')]
            for name in names:
                child = self.new(path, name)
                is_dir = os.path.isdir(child)
                if dir or not is_dir:
                    results.append(child)
                if is_dir and not os.path.islink(child) and (not max_depth or depth + 1 < max_depth):
                    walk(child._path, depth + 1)

        walk(self._path, 0)

        return Pyjo.Collection.object(results)

    def lstat(self) -> os.stat_result:
        """::

            stat = path.lstat()

        Return a :class:`os.stat_result` object for the symlink. ::

            # Get symlink size
            print(path('/usr/sbin/sendmail').lstat().st_size)

            # Get symlink modification time
            print(path('/usr/sbin/sendmail').lstat().st_mtime)
        """
        return os.lstat(self._path)

    def make_path(self, mode: int = 0o777) -> Self:
        """::

            path = path.make_path()
            path = path.make_path(mode=0o711)

        Create the directories if they don't already exist, with
        :func:`os.makedirs`.
        """
        os.makedirs(self._path, mode, exist_ok=True)
        return self

    def move_to(self, to: Anything) -> Self:
        """::

            destination = path.move_to('/home/sri')
            destination = path.move_to('/home/sri/.vimrc.backup')

        Move file with :mod:`shutil` and return the destination as a
        :mod:`Pyjo.File` object.
        """
        destination = self._destination(to)
        try:
            shutil.move(self._path, destination)
        except OSError as e:
            _croak(e, f'Can\'t move file "{self._path}" to "{_str(to)}"')
        return self.new(destination)

    def open(self, mode: str = 'r', *args: Any, **kwargs: Any) -> IO[Any]:
        """::

            handle = path.open('r+')
            handle = path.open('rb')
            handle = path.open('r', encoding='UTF-8')

        Open file with :func:`open`.
        """
        try:
            return builtins.open(self._path, mode, *args, **kwargs)
        except OSError as e:
            _croak(e, f'Can\'t open file "{self._path}"')

    def realpath(self) -> Self:
        """::

            realpath = path.realpath()

        Resolve the path with :func:`os.path.realpath` and return the result as
        a :mod:`Pyjo.File` object.
        """
        return self.new(os.path.realpath(self._path))

    def remove(self) -> Self:
        """::

            path = path.remove()

        Delete file.
        """
        if os.path.exists(self._path):
            try:
                os.unlink(self._path)
            except OSError as e:
                _croak(e, f'Can\'t remove file "{self._path}"')
        return self

    def remove_tree(self, *, keep_root: bool = False) -> Self:
        """::

            path = path.remove_tree()
            path = path.remove_tree(keep_root=True)

        Delete this directory and any files and subdirectories it may contain.
        """
        if not os.path.lexists(self._path):
            return self
        if not keep_root:
            shutil.rmtree(self._path)
            return self
        for name in os.listdir(self._path):
            child = os.path.join(self._path, name)
            if os.path.isdir(child) and not os.path.islink(child):
                shutil.rmtree(child)
            else:
                os.unlink(child)
        return self

    def sibling(self, *parts: Anything) -> Self:
        """::

            sibling = path.sibling('.vimrc')

        Return a new :mod:`Pyjo.File` object relative to the directory part of
        the path. ::

            # "/home/sri/.vimrc" (on UNIX)
            path('/home/sri/.bashrc').sibling('.vimrc')

            # "/home/sri/.ssh/known_hosts" (on UNIX)
            path('/home/sri/.bashrc').sibling('.ssh', 'known_hosts')
        """
        return self.new(_dirname(self._path), *parts)

    def slurp(self, encoding: str | None = None) -> bytes | str | None:
        """::

            data = path.slurp()
            chars = path.slurp('UTF-8')

        Read all data at once from the file. If an encoding is provided, an
        attempt will be made to decode the content, and ``None`` is returned if
        it fails.
        """
        try:
            fd = os.open(self._path, os.O_RDONLY)
        except OSError as e:
            _croak(e, f'Can\'t open file "{self._path}"')
        try:
            content = b''
            while buffer := os.read(fd, 131072):
                content += buffer
        except OSError as e:
            _croak(e, f'Can\'t read from file "{self._path}"')
        finally:
            os.close(fd)

        return decode(encoding, content) if encoding else content

    def spew(self, content: bytes | str, encoding: str | None = None) -> Self:
        """::

            path = path.spew(data)
            path = path.spew(chars, 'UTF-8')

        Write all data at once to the file. If an encoding is provided, an
        attempt to encode the content will be made prior to writing, and
        characters without one are encoded with ``UTF-8``.
        """
        if isinstance(content, str):
            # Unlike Mojolicious: characters without an encoding are UTF-8, where
            # Perl writes the characters 0-255 as bytes and dies of a wider one
            content = encode(encoding, content) if encoding else content.encode('UTF-8')
        try:
            fd = os.open(self._path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o666)
        except OSError as e:
            _croak(e, f'Can\'t open file "{self._path}"')
        try:
            if os.write(fd, content) != len(content):
                raise OSError(f'Can\'t write to file "{self._path}"')
        except OSError as e:
            _croak(e, f'Can\'t write to file "{self._path}"')
        finally:
            os.close(fd)
        return self

    def spurt(self, *chunks: bytes | str) -> Self:
        """::

            path = path.spurt(*chunks)

        Alias for :meth:`spew` that writes multiple chunks.
        """
        if all(isinstance(c, str) for c in chunks):
            return self.spew(''.join(str(c) for c in chunks))
        return self.spew(b''.join(c.encode('UTF-8') if isinstance(c, str) else c for c in chunks))

    def stat(self) -> os.stat_result:
        """::

            stat = path.stat()

        Return a :class:`os.stat_result` object for the path. ::

            # Get file size
            print(path('/home/sri/.bashrc').stat().st_size)

            # Get file modification time
            print(path('/home/sri/.bashrc').stat().st_mtime)
        """
        return os.stat(self._path)

    def to_abs(self) -> Self:
        """::

            absolute = path.to_abs()

        Return absolute path as a :mod:`Pyjo.File` object, the path does not
        need to exist on the file system.
        """
        if os.path.isabs(self._path):
            return self.new(_canonpath(self._path))
        return self.new(_catfile(os.getcwd(), self._path))

    def to_list(self) -> 'builtins.list[str]':
        """::

            parts = path.to_list()

        Split the path on directory separators. ::

            # "home:sri:.vimrc" (on UNIX)
            ':'.join(path('/home/sri/.vimrc').to_list())
        """
        return self._path.split(os.sep)

    # Not in Mojolicious: the conversion to pathlib
    def to_path(self) -> pathlib.Path:
        """::

            p = path.to_path()

        Turn the path into :class:`pathlib.Path`.
        """
        return pathlib.Path(self._path)

    def to_rel(self, base: Anything) -> Self:
        """::

            relative = path.to_rel('/some/base/path')

        Return a relative path from the original path to the destination path as
        a :mod:`Pyjo.File` object. ::

            # "sri/.vimrc" (on UNIX)
            path('/home/sri/.vimrc').to_rel('/home')
        """
        return self.new(os.path.relpath(self._path, _str(base)))

    # Renamed from Mojolicious: to_string
    def to_str(self) -> str:
        """::

            string = path.to_str()

        Stringify the path.
        """
        return self._path

    def touch(self) -> Self:
        """::

            path = path.touch()

        Create file if it does not exist or change the modification and access
        time to the current time. ::

            # Safely read file
            print(path('.bashrc').touch().slurp())
        """
        if not os.path.exists(self._path):
            self.open('w').close()
        try:
            os.utime(self._path)
        except OSError as e:
            _croak(e, f'Can\'t touch file "{self._path}"')
        return self

    # Left out from Mojolicious: with_roles, as Pyjoyment has no roles

    def _destination(self, to: Anything) -> str:
        to = _str(to)
        return _catfile(to, _basename(self._path)) if os.path.isdir(to) else to


def curfile() -> Pyjo_File:
    """::

        path = curfile()

    Construct a new :mod:`Pyjo.File` object for the absolute path to the
    current source file.
    """
    frame = inspect.currentframe()
    caller = frame.f_back if frame is not None else None
    return Pyjo_File(os.path.realpath(caller.f_code.co_filename if caller is not None else ''))


def path(*parts: Anything) -> Pyjo_File:
    """::

        path = path()
        path = path('/home/sri/.vimrc')
        path = path('/home', 'sri', '.vimrc')
        path = path(tempfile.TemporaryDirectory())

    Construct a new :mod:`Pyjo.File` object, defaults to using the current
    working directory. ::

        # "foo/bar/baz.txt" (on UNIX)
        path('foo', 'bar', 'baz.txt')
    """
    return Pyjo_File(*parts)


def tempdir(template: str | None = None, **kwargs: Any) -> Pyjo_File:
    """::

        path = tempdir()
        path = tempdir('tempXXXXX')

    Construct a new :mod:`Pyjo.File` object for a temporary directory with
    :class:`tempfile.TemporaryDirectory`, which is removed with the object.
    The ``X`` characters at the end of a template are random, and a directory
    with a template is made in the current working directory, as Perl's
    ``File::Temp`` makes it. ::

        # Longer version
        path = path(tempfile.TemporaryDirectory())
    """
    if template is not None:
        return Pyjo_File(_TempDir(template, **kwargs))
    return Pyjo_File(_tempfile.TemporaryDirectory(**kwargs))


def tempfile(**kwargs: Any) -> Pyjo_File:
    """::

        path = tempfile()
        path = tempfile(dir='/tmp')

    Construct a new :mod:`Pyjo.File` object for a temporary file with
    :func:`tempfile.NamedTemporaryFile`, which is removed with the object. ::

        # Longer version
        path = path(tempfile.NamedTemporaryFile(dir='/tmp'))
    """
    return Pyjo_File(cast(Anything, _tempfile.NamedTemporaryFile(**kwargs)))


# File::Temp's newdir with a template
class _TempDir:
    def __init__(self, template: str, dir: str = '.') -> None:
        prefix = template.rstrip('X')
        size = len(template) - len(prefix)
        chars = string.ascii_letters + string.digits
        while True:
            name = os.path.abspath(os.path.join(dir, prefix + ''.join(_random.choice(chars) for _ in range(size))))
            try:
                os.mkdir(name, 0o700)
                break
            except FileExistsError:
                continue
        self.name = name
        weakref.finalize(self, shutil.rmtree, name, ignore_errors=True)


# File::Basename's basename
def _basename(path: str, *suffixes: str) -> str:
    path = re.sub(r'(.)/*\Z', r'\1', path, flags=re.S)
    basename, dirname = _fileparse(path)
    tail = ''
    for suffix in suffixes:
        if basename.endswith(suffix):
            basename, tail = basename[: -len(suffix)], suffix + tail
    if len(tail) and not len(basename):
        basename = tail
    return basename if len(basename) else dirname


# File::Spec's canonpath
def _canonpath(path: str) -> str:
    path = re.sub(r'/{2,}', '/', path)
    path = re.sub(r'(?:/\.)+(?:/|\Z)', '/', path)
    if path != './':
        path = re.sub(r'^(?:\./)+', '', path, flags=re.S)
    path = re.sub(r'^/(?:\.\./)+', '/', path)
    path = re.sub(r'^/\.\.$', '/', path)
    if path != '/':
        path = re.sub(r'/\Z', '', path)
    return path


# File::Spec's catfile
def _catfile(*parts: str) -> str:
    return _canonpath('/'.join(parts))


def _croak(e: OSError, message: str) -> NoReturn:
    error = type(e)(f'{message}: {e.strerror}' if e.strerror else message)
    error.errno = e.errno
    raise error from e


# File::Basename's dirname
def _dirname(path: str) -> str:
    basename, dirname = _fileparse(path)
    dirname = re.sub(r'(.)/*\Z', r'\1', dirname, flags=re.S)
    if not len(basename):
        basename, dirname = _fileparse(dirname)
        dirname = re.sub(r'(.)/*\Z', r'\1', dirname, flags=re.S)
    return dirname


# File::Basename's fileparse
def _fileparse(path: str) -> tuple[str, str]:
    m = re.match(r'^(.*/)?(.*)$', path, re.S)
    assert m is not None
    return m[2], m[1] or './'


def _is_temp(value: Anything) -> bool:
    return (
        isinstance(value, (_TempDir, _tempfile.TemporaryDirectory)) or type(value).__name__ == '_TemporaryFileWrapper'
    )


def _str(value: Anything) -> str:
    if _is_temp(value):
        return str(cast(Any, value).name)
    if isinstance(value, os.PathLike):
        return str(os.fspath(value))  # pyright: ignore[reportUnknownArgumentType]
    return str(value)


new = Pyjo_File.new
object = Pyjo_File
