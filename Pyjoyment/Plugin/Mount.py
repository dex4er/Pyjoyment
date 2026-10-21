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

    # Application object
    plugin('Mount', {'/prefix': MyApp.new()})

    # WSGI application, as an object or as the name of its module and its
    # attribute
    plugin('Mount', {'/flask': flask_app})
    plugin('Mount', {'/flask': 'myflask:app'})

:mod:`Pyjoyment.Plugin.Mount` is a plugin that allows you to mount whole
:mod:`Pyjoyment` applications, other applications of :mod:`Pyjo`, and
``WSGI`` applications, which :mod:`Pyjo.App.WSGI` runs, as an application of
:mod:`Pyjo` from a script, an object, or the name of a module and its
attribute. An application that is not one of :mod:`Pyjoyment` gets the server
that runs it with :meth:`~Pyjo.App.Pyjo_App.server` before the server starts,
as the application that mounts it does.

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

import Pyjo.App
import Pyjo.App.WSGI
import Pyjo.Exception
import Pyjo.Server
import Pyjoyment.Plugin

import importlib
import inspect
import os
import re

from typing import TYPE_CHECKING, Any, cast


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
            route = plugin.register(Pyjoyment.new(), {'/foo': 'some_app:app'})

        Mount application and return the generated route, which is usually a
        :mod:`Pyjoyment.Routes.Route` object.
        """
        import Pyjoyment

        path: str | None = next(iter(conf))
        embed: Any = _load(conf[path])
        if isinstance(embed, Pyjoyment.object):
            embed.secrets = app.secrets

        # Not in Mojolicious: another application of Pyjo, as one of Pyjo.App.WSGI, gets the server that runs it before it
        # starts, as the application that mounts it gets it
        else:

            def before_server_start(server: Pyjo.Server.object, app: Any) -> None:
                embed.server(server)

            app.hook('before_server_start', before_server_start)
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


# Not in Mojolicious: an application as an object, or as the name of a module and its attribute, as ASGI servers take
# it, and a WSGI application, which Pyjo.App.WSGI runs, where Mojolicious loads a script
def _load(value: Any) -> Pyjo.Server.Application:
    if isinstance(value, str) and re.fullmatch(r'[\w.]+:[\w.]+', value) and not os.path.exists(value):
        module, _, name = value.partition(':')
        try:
            value = importlib.import_module(module)
            for attr in name.split('.'):
                value = getattr(value, attr)
        except Exception as e:
            raise Pyjo.Exception.new(f'Can\'t load application "{module}:{name}": {e}') from e
    elif isinstance(value, str | os.PathLike):
        return Pyjo.Server.new().load_app(cast(str, value))

    if isinstance(value, Pyjo.App.object):
        return value
    if inspect.iscoroutinefunction(value) or inspect.iscoroutinefunction(type(value).__call__):
        # TODO: an ASGI application, which Pyjo.App.ASGI will run
        raise Pyjo.Exception.new(f'ASGI application "{value!r}" is not supported yet')
    if not callable(value):
        raise Pyjo.Exception.new(f'"{value!r}" is not an application')
    return Pyjo.App.WSGI.new(app=value)


new = Pyjoyment_Plugin_Mount.new
object = Pyjoyment_Plugin_Mount
Mount = Pyjoyment_Plugin_Mount
