"""
Pyjoyment.Plugin - Plugin base class
====================================
::

    # CamelCase plugin name
    from Pyjoyment.Plugin import Plugin

    class Pyjoyment_Plugin_MyPlugin(Plugin):
        def register(self, app, conf):
            # Magic here! :)
            ...

    object = Pyjoyment_Plugin_MyPlugin

    # Or import the module, as in Google Python Style Guide
    # CamelCase plugin name
    import Pyjoyment.Plugin

    class Pyjoyment_Plugin_MyPlugin(Pyjoyment.Plugin.object):
        def register(self, app, conf):
            # Magic here! :)
            ...

    object = Pyjoyment_Plugin_MyPlugin

:mod:`Pyjoyment.Plugin` is an abstract base class for :mod:`Pyjoyment`
plugins.

See :mod:`Pyjoyment.Plugins` for a list of plugins that are available by
default.

A plugin of another distribution is a module in the namespace
``Pyjoyment.Plugin``, which :func:`pkgutil.extend_path` keeps open, and the
class that the module names ``object``.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Plugin <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Plugin.pm>`_
of Mojolicious 9.49.
"""

import Pyjo.Base

from pkgutil import extend_path
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    import Pyjoyment


class Pyjoyment_Plugin(Pyjo.Base.object):
    """
    :mod:`Pyjoyment.Plugin` inherits all methods from :mod:`Pyjo.Base` and
    implements the following new ones.
    """

    def register(self, app: 'Pyjoyment.object', conf: dict[str, Any]) -> Any:
        """::

            plugin.register(Pyjoyment.new(), {})
            plugin.register(Pyjoyment.new(), {'foo': 'bar'})

        This method will be called by :mod:`Pyjoyment.Plugins` at startup time.
        Meant to be overloaded in a subclass.
        """
        raise NotImplementedError('Method "register" not implemented by subclass')


# Not in Mojolicious: a namespace that other distributions can add plugins to
__path__ = extend_path(__path__, __name__)

new = Pyjoyment_Plugin.new
object = Pyjoyment_Plugin
Plugin = Pyjoyment_Plugin
