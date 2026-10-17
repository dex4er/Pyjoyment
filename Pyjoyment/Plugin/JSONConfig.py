"""
Pyjoyment.Plugin.JSONConfig - JSON configuration plugin
=======================================================
::

    # myapp.json (it's just JSON with embedded Python)
    {
      %# Just a value
      "foo": "bar",

      %# Nested data structures are fine too
      "baz": ["♥"],

      %# You have full access to the application
      "music_dir": "<%= app.home.child('music') %>"
    }

    # Pyjoyment
    config = app.plugin('JSONConfig')
    print(config['foo'])

    # Pyjoyment.Lite
    config = plugin('JSONConfig')
    print(config['foo'])

    # foo.html.ep
    %= config()['foo']

    # The configuration is available application-wide
    config = app.config()
    print(config['foo'])

    # Everything can be customized with options
    config = plugin('JSONConfig', file='/etc/myapp.conf')

:mod:`Pyjoyment.Plugin.JSONConfig` is a JSON configuration plugin that
preprocesses its input with :mod:`Pyjo.Template`.

The application object can be accessed via ``app``. A default configuration
filename in the application home directory will be generated from the value
of :attr:`Pyjoyment.Pyjoyment_App.moniker` (``$moniker.json``). You can extend
the normal configuration file ``$moniker.json`` with ``mode`` specific ones
like ``$moniker.$mode.json``, which will be detected automatically.

These configuration values are currently reserved:

``config_override``
    If this configuration value has been set in
    :meth:`Pyjoyment.Pyjoyment_App.config` when this plugin is loaded, it will
    not do anything besides loading deployment specific plugins.

``plugins`` ::

    "plugins": [{"SetUserGroup": {"user": "sri", "group": "staff"}}]

    One or more deployment specific plugins that should be loaded right after
    this plugin has been loaded.

The code of this plugin is a good example for learning to build new plugins,
you're welcome to fork it.

See :mod:`Pyjoyment.Plugins` for a list of plugins that are available by
default.

Options
-------

:mod:`Pyjoyment.Plugin.JSONConfig` inherits all options from
:mod:`Pyjoyment.Plugin.Config` and supports the following new ones.

template ::

    # Pyjoyment.Lite
    plugin('JSONConfig', template={'line_start': '.'})

Attribute values passed to :mod:`Pyjo.Template` object used to preprocess
configuration files.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Plugin::JSONConfig
<https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Plugin/JSONConfig.pm>`_ of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.Exception
import Pyjo.Template
import Pyjoyment.Plugin.Config

from Pyjo.JSON import from_json

from typing import TYPE_CHECKING, Any, cast


if TYPE_CHECKING:
    import Pyjoyment


class Pyjoyment_Plugin_JSONConfig(Pyjoyment.Plugin.Config.object):
    """
    :mod:`Pyjoyment.Plugin.JSONConfig` inherits all methods from
    :mod:`Pyjoyment.Plugin.Config` and implements the following new ones.
    """

    def parse(self, content: str, file: str, conf: dict[str, Any], app: 'Pyjoyment.object') -> dict[str, Any]:
        """::

            plugin.parse(content, file, conf, app)

        Process content with :meth:`render` and parse it with
        :mod:`Pyjo.JSON`. ::

            def parse(self, content, file, conf, app):
                ...
                content = self.render(content, file, conf, app)
                ...
                return config
        """
        try:
            config = from_json(self.render(content, file, conf, app))
        except Exception as e:
            raise Pyjo.Exception.new(f'Can\'t load configuration from file "{file}": {e}') from e
        if not isinstance(config, dict):
            raise Pyjo.Exception.new(f'Configuration file "{file}" did not return a JSON object')

        return cast(dict[str, Any], config)

    def register(self, app: 'Pyjoyment.object', conf: dict[str, Any] | None = None) -> dict[str, Any]:
        """::

            config = plugin.register(Pyjoyment.new())
            config = plugin.register(Pyjoyment.new(), {'file': '/etc/foo.conf'})

        Register plugin in :mod:`Pyjoyment` application and merge
        configuration.
        """
        return super().register(app, {'ext': 'json', **(conf or {})})

    def render(self, content: str, file: str, conf: dict[str, Any], app: 'Pyjoyment.object') -> str:
        """::

            plugin.render(content, file, conf, app)

        Process configuration file with :mod:`Pyjo.Template`. ::

            def render(self, content, file, conf, app):
                ...
                return content
        """
        # Application instance
        mt = Pyjo.Template.new(**(conf.get('template') or {}))
        mt.name = file
        mt.prepend = 'app = args[0]' + (f'\n{mt.prepend}' if mt.prepend else '')
        output = mt.render(content, app)
        if isinstance(output, Exception):
            raise output
        return str(output)


new = Pyjoyment_Plugin_JSONConfig.new
object = Pyjoyment_Plugin_JSONConfig
