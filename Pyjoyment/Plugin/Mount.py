"""
Pyjoyment.Plugin.Mount - Application mount plugin
=================================================
::

    # Pyjoyment
    route = app.plugin('Mount', {'/prefix': '/home/sri/foo/script/foo'})

    # Pyjoyment.Lite
    route = plugin('Mount', {'/prefix': '/home/sri/myapp.py'})

    # Adjust the generated route and mounted application
    example = plugin('Mount', {'/example': '/home/sri/example.py'})
    example.to(message='It works great!')
    embedded = example.pattern.defaults['app']
    embedded.config(foo='bar')
    embedded.log = app.log

    # Mount application with host
    plugin('Mount', {'example.com': '/home/sri/myapp.py'})

    # Host and path
    plugin('Mount', {'example.com/myapp': '/home/sri/myapp.py'})

    # Or even hosts with wildcard subdomains
    plugin('Mount', {'*.example.com/myapp': '/home/sri/myapp.py'})

:mod:`Pyjoyment.Plugin.Mount` is a plugin that allows you to mount whole
:mod:`Pyjoyment` applications.

The code of this plugin is a good example for learning to build new plugins,
you're welcome to fork it.

See :mod:`Pyjoyment.Plugins` for a list of plugins that are available by
default.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Plugin::Mount
<https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Plugin/Mount.pm>`_ of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.Server
import Pyjoyment.Plugin

import re

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    import Pyjoyment
    import Pyjoyment.Routes.Route


class Pyjoyment_Plugin_Mount(Pyjoyment.Plugin.object):
    """
    :mod:`Pyjoyment.Plugin.Mount` inherits all methods from
    :mod:`Pyjoyment.Plugin` and implements the following new ones.
    """

    def register(self, app: 'Pyjoyment.object', conf: dict[str, Any]) -> 'Pyjoyment.Routes.Route.object':
        """::

            route = plugin.register(Pyjoyment.new(), {'/foo': '/some/app.py'})

        Mount :mod:`Pyjoyment` application and return the generated route,
        which is usually a :mod:`Pyjoyment.Routes.Route` object.
        """
        path: str | None = next(iter(conf))
        embed: Any = Pyjo.Server.new().load_app(conf[path])
        embed.secrets = app.secrets
        embed.log = app.log

        # Extract host
        host = None
        if m := re.match(r'^(\*\.)?([^/]+)(/.*)?$', path):
            host = re.compile(rf'^(?:.*\.)?{re.escape(m[2])}$' if m[1] else rf'^{re.escape(m[2])}$', re.I)
            path = m[3]

        route = app.routes.any(path)
        route.partial = True
        route.to(app=embed)
        return route.requires(host=host) if host else route


new = Pyjoyment_Plugin_Mount.new
object = Pyjoyment_Plugin_Mount
Mount = Pyjoyment_Plugin_Mount
