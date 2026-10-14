"""
Pyjo.Server.Reload.Backend - Auto-restarting development server backend
=======================================================================
::

    import Pyjo.Server.Reload.Backend


    class Pyjo_Server_Reload_Backend_Inotify(Pyjo.Server.Reload.Backend.object):
        def modified_files(self):
            ...


    new = Pyjo_Server_Reload_Backend_Inotify.new
    object = Pyjo_Server_Reload_Backend_Inotify

:mod:`Pyjo.Server.Reload.Backend` is an abstract base class for
auto-restarting development server backends used by
:mod:`Pyjo.Server.Reload`.

A backend is a module named ``Pyjo.Server.Reload.Backend.<Name>``, with a
function ``new`` that constructs it and the class as ``object``, which
another distribution can add, as :func:`pkgutil.extend_path` keeps the
namespace open, and the ``PYJO_RELOAD_BACKEND`` environment variable selects
it.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Server::Morbo::Backend <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Server/Morbo/Backend.pm>`_
of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.Base

import os

from pkgutil import extend_path
from typing import Any


# Not in Mojolicious: a namespace that other distributions can add backends to
__path__ = extend_path(__path__, __name__)


# Renamed from Mojolicious: Mojo::Server::Morbo::Backend, as the names of Futurama are not ours
class Pyjo_Server_Reload_Backend(Pyjo.Base.object):
    """
    :mod:`Pyjo.Server.Reload.Backend` inherits all methods from
    :mod:`Pyjo.Base` and implements the following new ones.
    """

    def __init__(self, *, watch: list[Any] | None = None, watch_timeout: float | None = None) -> None:
        """::

            backend = Pyjo.Server.Reload.Backend.new()
            backend = Pyjo.Server.Reload.Backend.new(watch=['lib'], watch_timeout=2)

        Construct a new :mod:`Pyjo.Server.Reload.Backend` object.
        """
        super().__init__()

        self.watch: list[Any] = watch if watch is not None else ['lib', 'templates']
        """::

            watch = backend.watch
            backend.watch = ['/home/sri/my_app']

        Files and directories to watch for changes, defaults to the application
        script as well as the ``lib`` and ``templates`` directories in the
        current working directory.
        """

        self.watch_timeout: float = (
            watch_timeout if watch_timeout is not None else float(os.environ.get('PYJO_RELOAD_TIMEOUT') or 1)
        )
        """::

            timeout = backend.watch_timeout
            backend.watch_timeout = 10

        Maximum amount of time in seconds a backend may block when waiting for
        files to change, defaults to the value of the ``PYJO_RELOAD_TIMEOUT``
        environment variable or ``1``.
        """

    def modified_files(self) -> list[str]:
        """::

            files = backend.modified_files()

        Check if files from :attr:`watch` have been modified since the last
        check and return their names. Meant to be overloaded in a subclass.
        """
        raise NotImplementedError('Method "modified_files" not implemented by subclass')


new = Pyjo_Server_Reload_Backend.new
object = Pyjo_Server_Reload_Backend
