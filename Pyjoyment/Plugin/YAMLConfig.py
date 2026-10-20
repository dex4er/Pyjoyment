"""
Pyjoyment.Plugin.YAMLConfig - YAML configuration plugin
=======================================================
::

    # myapp.yml (it's just YAML with embedded Python)
    ---
    foo: bar
    baz:
      - ♥
    music_dir: <%= app.home.child('music') %>

    # Pyjoyment
    config = app.plugin('YAMLConfig')
    print(config['foo'])

    # Pyjoyment.Lite
    config = plugin('YAMLConfig')
    print(config['foo'])

    # foo.html.ep
    %= config()['foo']

    # The configuration is available application-wide
    config = app.config()
    print(config['foo'])

    # Everything can be customized with options
    config = plugin('YAMLConfig', file='/etc/myapp.conf')

:mod:`Pyjoyment.Plugin.YAMLConfig` is a YAML configuration plugin that
preprocesses its input with :mod:`Pyjo.Template`. By default it uses
:mod:`Pyjo.YAML` for parsing, which is not the best YAML module available, but
good enough for most config files. If you need something more correct you can
use a different module like PyYAML with the ``module`` option.

The application object can be accessed via ``app``. A default configuration
filename in the application home directory will be generated from the value
of :attr:`Pyjoyment.Pyjoyment_App.moniker` (``$moniker.yml``). You can extend
the normal configuration file ``$moniker.yml`` with ``mode`` specific ones
like ``$moniker.$mode.yml``, which will be detected automatically.

These configuration values are currently reserved:

``config_override``
    If this configuration value has been set in
    :meth:`Pyjoyment.Pyjoyment_App.config` when this plugin is loaded, it will
    not do anything besides loading deployment specific plugins.

``plugins`` ::

    plugins:
      - SetUserGroup:
          user: sri
          group: staff

    One or more deployment specific plugins that should be loaded right after
    this plugin has been loaded.

The code of this plugin is a good example for learning to build new plugins,
you're welcome to fork it.

See :mod:`Pyjoyment.Plugins` for a list of plugins that are available by
default.

Options
-------

:mod:`Pyjoyment.Plugin.YAMLConfig` inherits all options from
:mod:`Pyjoyment.Plugin.JSONConfig` and supports the following new ones.

module ::

    # Pyjoyment.Lite
    plugin('YAMLConfig', module='yaml')
    plugin('YAMLConfig', module=yaml.safe_load)

Alternative YAML module to use for parsing, whose function ``safe_load``, or
``load``, takes a string, or such a function.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Plugin::NotYAMLConfig
<https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Plugin/NotYAMLConfig.pm>`_ of Mojolicious 9.49.

Classes
-------
"""

# Renamed from Mojolicious: YAMLConfig, where Mojo has NotYAMLConfig, as the file is YAML once its template is rendered,
# as the files of JSONConfig and TOMLConfig are JSON and TOML

import Pyjo.Exception
import Pyjo.YAML
import Pyjoyment.Plugin.JSONConfig

import importlib

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast


if TYPE_CHECKING:
    import Pyjoyment


class Pyjoyment_Plugin_YAMLConfig(Pyjoyment.Plugin.JSONConfig.object):
    """
    :mod:`Pyjoyment.Plugin.YAMLConfig` inherits all methods from
    :mod:`Pyjoyment.Plugin.JSONConfig` and implements the following new ones.
    """

    def __init__(self) -> None:
        super().__init__()
        self._yaml: Callable[[str], Any] = Pyjo.YAML.load

    def parse(self, content: str, file: str, conf: dict[str, Any], app: 'Pyjoyment.object') -> dict[str, Any]:
        """::

            plugin.parse(content, file, conf, app)

        Process content with
        :meth:`~Pyjoyment.Plugin.JSONConfig.Pyjoyment_Plugin_JSONConfig.render`
        and parse it with :mod:`Pyjo.YAML`. ::

            def parse(self, content, file, conf, app):
                ...
                content = self.render(content, file, conf, app)
                ...
                return config
        """
        try:
            config = self._yaml(self.render(content, file, conf, app))
        except Exception as e:
            raise Pyjo.Exception.new(f'Can\'t load configuration from file "{file}": {e}') from e
        if not isinstance(config, dict):
            raise Pyjo.Exception.new(f'Configuration file "{file}" did not return a YAML mapping')
        return cast(dict[str, Any], config)

    def register(self, app: 'Pyjoyment.object', conf: dict[str, Any] | None = None) -> dict[str, Any]:
        """::

            config = plugin.register(Pyjoyment.new())
            config = plugin.register(Pyjoyment.new(), {'file': '/etc/foo.conf'})

        Register plugin in :mod:`Pyjoyment` application and merge
        configuration.
        """
        conf = {'ext': 'yml', **(conf or {})}

        self._yaml = Pyjo.YAML.load
        if module := conf.get('module'):
            if (load := _load(module)) is None:
                raise Pyjo.Exception.new(f'YAML module {module} has no Load function')
            self._yaml = load

        return super().register(app, conf)


# Not in Mojolicious: a function of a module, safe_load or load, as the YAML modules of Python name it, or the function
# itself, where Mojo takes the function Load of a module
def _load(module: Any) -> Callable[[str], Any] | None:
    if callable(module):
        return cast(Callable[[str], Any], module)
    try:
        mod = importlib.import_module(str(module))
    except ImportError:
        return None
    load = getattr(mod, 'safe_load', None) or getattr(mod, 'load', None)
    return cast(Callable[[str], Any], load) if callable(load) else None


new = Pyjoyment_Plugin_YAMLConfig.new
object = Pyjoyment_Plugin_YAMLConfig
YAMLConfig = Pyjoyment_Plugin_YAMLConfig
