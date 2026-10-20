"""
Pyjo.Server.Reload.Backend.Poll - Auto-restarting development server backend using stat
=======================================================================================
::

    from Pyjo.Server.Reload.Backend.Poll import Poll

    backend = Poll()
    if files := backend.modified_files():
        print('Files have been changed')

    import Pyjo.Server.Reload.Backend.Poll

    backend = Pyjo.Server.Reload.Backend.Poll.new()
    if files := backend.modified_files():
        print('Files have been changed')

:mod:`Pyjo.Server.Reload.Backend.Poll` is a backend for
:mod:`Pyjo.Server.Reload` that checks the size and the modification time
of the files with :func:`os.stat`, and waits for
:attr:`~Pyjo.Server.Reload.Backend.Pyjo_Server_Reload_Backend.watch_timeout`
when none has changed.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Server::Morbo::Backend::Poll <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Server/Morbo/Backend/Poll.pm>`_
of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.File
import Pyjo.Server.Reload.Backend

import os
import time

from typing import Any, cast


# The time the program started, as Perl's $^T
_START = time.time()


# Renamed from Mojolicious: Mojo::Server::Morbo::Backend::Poll, as the names of Futurama are not ours
class Pyjo_Server_Reload_Backend_Poll(Pyjo.Server.Reload.Backend.object):
    """
    :mod:`Pyjo.Server.Reload.Backend.Poll` inherits all attributes and methods
    from :mod:`Pyjo.Server.Reload.Backend` and implements the following new
    ones.
    """

    def __init__(self, **kwargs: Any) -> None:
        """::

            backend = Pyjo.Server.Reload.Backend.Poll.new()

        Construct a new :mod:`Pyjo.Server.Reload.Backend.Poll` object.
        """
        super().__init__(**kwargs)
        self._cache: dict[str, list[float]] = {}

    def modified_files(self) -> list[str]:
        """::

            files = backend.modified_files()

        Check file size and mtime to determine which files have changed, this
        is not particularly efficient, but very robust.
        """
        cache = self._cache
        known = set(cache)
        files: list[str] = []
        for file in (f for watch in self.watch for f in _files(os.fspath(cast(str, watch)))):
            known.discard(file)
            try:
                stat = os.stat(file)
            except OSError:
                continue
            stats = cache.setdefault(file, [_START, stat.st_size])
            if stat.st_mtime <= stats[0] and stat.st_size == stats[1]:
                continue
            stats[:] = [stat.st_mtime, stat.st_size]
            files.append(file)

        # Any leftover file means they were deleted
        for file in sorted(known):
            files.append(file)
            del cache[file]

        if not len(files):
            time.sleep(self.watch_timeout)

        return files


# A readable file, or the files of a directory
def _files(path: str) -> list[str]:
    if os.path.isfile(path) and os.access(path, os.R_OK):
        return [path]
    return [file.to_str() for file in Pyjo.File.new(path).list_tree()]


new = Pyjo_Server_Reload_Backend_Poll.new
object = Pyjo_Server_Reload_Backend_Poll
Poll = Pyjo_Server_Reload_Backend_Poll
