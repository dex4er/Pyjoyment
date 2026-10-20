"""
Pyjo.Home - Home sweet home
===========================
::

    from Pyjo.Home import Home

    # Find and manage the project root directory
    home = Home()
    home.detect()
    print(home.child('templates', 'layouts', 'default.html.ep'))
    print(f'{home}')

    # Or import the module, as in Google Python Style Guide
    import Pyjo.Home

    # Find and manage the project root directory
    home = Pyjo.Home.new()
    home.detect()
    print(home.child('templates', 'layouts', 'default.html.ep'))
    print(f'{home}')

:mod:`Pyjo.Home` is a container for home directories based on
:mod:`Pyjo.File`.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Home <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Home.pm>`_
of Mojolicious 9.49.
"""

import Pyjo.File

import os
import sys

from types import ModuleType
from typing import Self


class Pyjo_Home(Pyjo.File.object):
    """
    :mod:`Pyjo.Home` inherits all methods from :mod:`Pyjo.File` and
    implements the following new ones.
    """

    def detect(self, cls: type | ModuleType | str | None = None) -> Self:
        """::

            home = home.detect()
            home = home.detect(MyApp)
            home = home.detect('My.App')

        Detect home directory from the value of the ``PYJO_HOME`` environment
        variable or the location of the application class: a class, its
        module, or the dotted name of a module that is loaded. The directory
        of the module's file, less the parts of the name of the module and a
        ``lib``, ``blib/lib`` or ``src`` directory, is the home.
        """
        # Environment variable
        home: list[str] | None = None
        if os.environ.get('PYJO_HOME'):
            home = Pyjo.File.new(os.environ['PYJO_HOME']).to_list()

        # Location of the application class
        elif cls is not None and (module := _module(cls)) is not None and (file := getattr(module, '__file__', None)):
            home = Pyjo.File.new(file).to_list()
            parts = len(module.__name__.split('.')) + (Pyjo.File.new(file).basename() == '__init__.py')
            del home[-parts:]
            for name in ('lib', 'blib'):
                if home and home[-1] == name:
                    home.pop()
            # Not in Mojolicious: the src directory of a Python project, as lib is of a Perl one
            if home and home[-1] == 'src':
                home.pop()

        if home is not None:
            self._path = Pyjo.File.new(*home).to_abs().to_str()
        return self

    def rel_file(self, path: str) -> Self:
        """::

            path = home.rel_file('foo/bar.html')

        Return a new :mod:`Pyjo.Home` object relative to the home directory.
        """
        return self.child(*path.split('/'))


# The module of a class, a module, or the longest prefix of a dotted name that is loaded
def _module(cls: type | ModuleType | str) -> ModuleType | None:
    if isinstance(cls, ModuleType):
        return cls
    name = cls.__module__ if isinstance(cls, type) else cls
    parts = name.split('.')
    for i in range(len(parts), 0, -1):
        if (module := sys.modules.get('.'.join(parts[:i]))) is not None:
            return module
    return None


new = Pyjo_Home.new
object = Pyjo_Home
Home = Pyjo_Home
