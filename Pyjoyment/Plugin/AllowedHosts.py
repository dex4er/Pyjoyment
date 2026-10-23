"""
Pyjoyment.Plugin.AllowedHosts - Host and Origin validation plugin
=================================================================
::

    # Pyjoyment
    app.plugin('AllowedHosts')

    # Pyjoyment.Lite
    plugin('AllowedHosts')

    # The hosts of a deployment, and the origins of its pages
    app.plugin('AllowedHosts', hosts=['example.com', '.example.com'], origins=['https://app.example.com'])

    # Only for some routes, under the helper "allowed_hosts"
    app.plugin('AllowedHosts', hook=False)
    mcp = app.routes.under('/mcp', lambda c: c.allowed_hosts())
    mcp.post('/').to(cb=lambda c: c.render(json={'jsonrpc': '2.0'}))

:mod:`Pyjoyment.Plugin.AllowedHosts` rejects a request whose ``Host`` header
is not one of the hosts of the application, with ``421 Misdirected Request``,
and a request whose ``Origin`` header, which a browser sends with a request
of a page of another site, is not one of its origins, with
``403 Forbidden``. A request without ``Origin``, which a browser sends
without it only for a page of the same site, and a client that is not a
browser, passes.

It protects a server on ``localhost`` against DNS rebinding: a page of another
site whose host name the attacker makes an address of ``127.0.0.1`` requests
the server with its own host in ``Host``, which is not one of the hosts, and
with its own origin, which is not one of the origins, as for a server of
the Model Context Protocol, whose transport over HTTP requires it.

The host is the one of ``Host``, the host of
:meth:`Pyjo.URL.Pyjo_URL.to_abs` of the request, which a reverse proxy
passes on.

See :mod:`Pyjoyment.Plugins` for a list of plugins that are available by
default.

Options
-------

:mod:`Pyjoyment.Plugin.AllowedHosts` supports the following options.

``hook`` ::

    app.plugin('AllowedHosts', hook=False)

    Check every request of the application, in a hook of ``before_dispatch``,
    defaults to ``True``. With ``False``, only the routes under the helper
    ``allowed_hosts`` are checked.

``hosts`` ::

    app.plugin('AllowedHosts', hosts=['example.com', 'localhost:3000', '.example.org'])
    app.plugin('AllowedHosts', hosts=[re.compile(r'^pr-\\d+\\.example\\.com$')])
    app.plugin('AllowedHosts', hosts=lambda c, host: host.endswith('.internal'))

    The hosts of the application, defaults to ``localhost``, ``127.0.0.1``
    and ``[::1]``. A host without a port is of any port, one with a port of
    that port only, one that starts with a dot of the domain and its
    subdomains, a regular expression searches the host and its port, as
    ``Host`` has them, and a function takes the controller and the host and
    its port, and returns true for one of the application. The names of the
    hosts are compared without their case.

``origins`` ::

    app.plugin('AllowedHosts', origins=['https://app.example.com', 'http://localhost:5173'])
    app.plugin('AllowedHosts', origins=lambda c, origin: origin.startswith('https://'))

    The origins of the pages that request the application, defaults to the
    origins of the hosts of ``hosts``, of any scheme. An origin is a scheme, a
    host and a port, as a host of ``hosts`` with its scheme, and a function
    takes the controller and the origin, as ``Origin`` has it.

Helpers
-------

:mod:`Pyjoyment.Plugin.AllowedHosts` implements the following helpers.

``allowed_hosts`` ::

    boolean = c.allowed_hosts()
    boolean = c.allowed_hosts(hosts=['mcp.example.com'])

    mcp = app.routes.under('/mcp', lambda c: c.allowed_hosts(hosts=['mcp.example.com']))
    mcp.post('/').to(cb=lambda c: c.render(json={'jsonrpc': '2.0'}))

    Check the request, with the options of the plugin, or with ``hosts`` and
    ``origins`` of its own, and render the response of a request that is not
    allowed, so that it is false and ends the dispatch of :meth:`under
    <Pyjoyment.Routes.Route.Pyjoyment_Routes_Route.under>`, which a condition
    of a route would not do, as the next route would match the request.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

It has no counterpart in Mojolicious.

Classes
-------
"""

import Pyjo.URL
import Pyjoyment.Plugin

import re

from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    import Pyjoyment
    import Pyjoyment.Controller

# The hosts of the loopback interface, of a server on localhost
HOSTS = ('localhost', '127.0.0.1', '[::1]')

_PORTS = {'http': 80, 'https': 443, 'ws': 80, 'wss': 443}

type _Hosts = Iterable[str | re.Pattern[str]] | Callable[['Pyjoyment.Controller.object', str], bool]
type _Origins = Iterable[str] | Callable[['Pyjoyment.Controller.object', str], bool] | None


class Pyjoyment_Plugin_AllowedHosts(Pyjoyment.Plugin.object):
    """
    :mod:`Pyjoyment.Plugin.AllowedHosts` inherits all methods from
    :mod:`Pyjoyment.Plugin` and implements the following new ones.
    """

    def register(self, app: 'Pyjoyment.object', conf: dict[str, Any] | None = None) -> None:
        """::

            plugin.register(Pyjoyment.new())
            plugin.register(Pyjoyment.new(), {'hosts': ['example.com']})

        Register the hook and the helper in :mod:`Pyjoyment` application.
        """
        conf = conf or {}
        hosts: _Hosts = conf.get('hosts', HOSTS)
        origins: _Origins = conf.get('origins')

        def allowed_hosts(c: 'Pyjoyment.Controller.object', **own: Any) -> bool:
            return _allowed(c, own.get('hosts', hosts), own.get('origins', origins if 'hosts' not in own else None))

        app.helper('allowed_hosts', allowed_hosts)
        if conf.get('hook', True):
            app.hook('before_dispatch', allowed_hosts)


def _allowed(c: 'Pyjoyment.Controller.object', hosts: _Hosts, origins: _Origins) -> bool:
    # The response of a request that is not allowed, which the hook and the helper render
    url = c.req.url.to_abs()
    host = url.host_port
    if not host or not _host(c, hosts, url):
        c.helpers.log().debug(f'Host "{host}" not allowed')
        c.render(text='Host not allowed', status=421)
        return False
    origin = c.req.headers.header('Origin')
    if origin is not None and not _origin(c, hosts, origins, origin):
        c.helpers.log().debug(f'Origin "{origin}" not allowed')
        c.render(text='Origin not allowed', status=403)
        return False
    return True


def _host(c: 'Pyjoyment.Controller.object', hosts: _Hosts, url: Pyjo.URL.object) -> bool:
    host = url.host_port or ''
    if callable(hosts):
        return hosts(c, host)
    name, port = (url.host or '').lower(), url.port or _PORTS.get(url.scheme or '')
    for allowed in hosts:
        if isinstance(allowed, re.Pattern):
            if allowed.search(host):
                return True
            continue
        allowed = allowed.lower()
        if allowed.startswith('.'):
            if name == allowed[1:] or name.endswith(allowed):
                return True
            continue
        expected = Pyjo.URL.new(f'http://{allowed}')
        if expected.host == name and (expected.port is None or expected.port == port):
            return True
    return False


def _origin(c: 'Pyjoyment.Controller.object', hosts: _Hosts, origins: _Origins, origin: str) -> bool:
    if callable(origins):
        return origins(c, origin)
    if origins is not None:
        return origin.lower() in (allowed.lower() for allowed in origins)
    # The origins of the hosts, of a page of the application
    url = Pyjo.URL.new(origin)
    return bool(url.scheme and url.host) and _host(c, hosts, url)


new = Pyjoyment_Plugin_AllowedHosts.new
object = Pyjoyment_Plugin_AllowedHosts
AllowedHosts = Pyjoyment_Plugin_AllowedHosts
