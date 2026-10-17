"""
Pyjoyment.Plugin.TOMLConfig - TOML configuration plugin
=======================================================
::

    # myapp.toml (it's just TOML with embedded Python)
    %# Just a value
    foo = "bar"

    %# Nested data structures are fine too
    baz = ["♥"]

    %# You have full access to the application
    music_dir = "<%= app.home.child('music') %>"

    [db]
    host = "localhost"

    # Pyjoyment
    config = app.plugin('TOMLConfig')
    print(config['foo'])

    # Pyjoyment.Lite
    config = plugin('TOMLConfig')
    print(config['foo'])

    # foo.html.ep
    %= config()['foo']

    # The configuration is available application-wide
    config = app.config()
    print(config['foo'])

    # Everything can be customized with options
    config = plugin('TOMLConfig', file='/etc/myapp.conf')

:mod:`Pyjoyment.Plugin.TOMLConfig` is a TOML configuration plugin that
preprocesses its input with :mod:`Pyjo.Template` and parses it with
:mod:`tomllib` of the standard library.

The application object can be accessed via ``app``. A default configuration
filename in the application home directory will be generated from the value
of :attr:`Pyjoyment.Pyjoyment_App.moniker` (``$moniker.toml``). You can extend
the normal configuration file ``$moniker.toml`` with ``mode`` specific ones
like ``$moniker.$mode.toml``, which will be detected automatically.

These configuration values are currently reserved:

``config_override``
    If this configuration value has been set in
    :meth:`Pyjoyment.Pyjoyment_App.config` when this plugin is loaded, it will
    not do anything besides loading deployment specific plugins.

``plugins`` ::

    plugins = [{ SetUserGroup = { user = "sri", group = "staff" } }]

    One or more deployment specific plugins that should be loaded right after
    this plugin has been loaded.

The code of this plugin is a good example for learning to build new plugins,
you're welcome to fork it.

See :mod:`Pyjoyment.Plugins` for a list of plugins that are available by
default.

Options
-------

:mod:`Pyjoyment.Plugin.TOMLConfig` inherits all options from
:mod:`Pyjoyment.Plugin.JSONConfig`.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Inspired by `Mojolicious::Plugin::NotYAMLConfig
<https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Plugin/NotYAMLConfig.pm>`_ of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.Exception
import Pyjoyment.Plugin.JSONConfig

import tomllib

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    import Pyjoyment


class Pyjoyment_Plugin_TOMLConfig(Pyjoyment.Plugin.JSONConfig.object):
    """
    :mod:`Pyjoyment.Plugin.TOMLConfig` inherits all methods from
    :mod:`Pyjoyment.Plugin.JSONConfig` and implements the following new ones.
    """

    def parse(self, content: str, file: str, conf: dict[str, Any], app: 'Pyjoyment.object') -> dict[str, Any]:
        """::

            plugin.parse(content, file, conf, app)

        Process content with
        :meth:`~Pyjoyment.Plugin.JSONConfig.Pyjoyment_Plugin_JSONConfig.render`
        and parse it with :mod:`tomllib`. ::

            def parse(self, content, file, conf, app):
                ...
                content = self.render(content, file, conf, app)
                ...
                return config
        """
        try:
            return tomllib.loads(self.render(content, file, conf, app))
        except Exception as e:
            raise Pyjo.Exception.new(f'Can\'t load configuration from file "{file}": {e}') from e

    def register(self, app: 'Pyjoyment.object', conf: dict[str, Any] | None = None) -> dict[str, Any]:
        """::

            config = plugin.register(Pyjoyment.new())
            config = plugin.register(Pyjoyment.new(), {'file': '/etc/foo.conf'})

        Register plugin in :mod:`Pyjoyment` application and merge
        configuration.
        """
        return super().register(app, {'ext': 'toml', **(conf or {})})


new = Pyjoyment_Plugin_TOMLConfig.new
object = Pyjoyment_Plugin_TOMLConfig
