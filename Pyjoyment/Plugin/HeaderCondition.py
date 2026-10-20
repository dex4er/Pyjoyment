"""
Pyjoyment.Plugin.HeaderCondition - Header condition plugin
==========================================================
::

    # Pyjoyment
    app.plugin('HeaderCondition')
    app.routes.get('/foo').requires(headers={'Referer': re.compile(r'example\\.com')})

    # Pyjoyment.Lite
    plugin('HeaderCondition')

    @get('/').requires(headers={'Referer': re.compile(r'example\\.com')})
    def index(c): ...

    # All headers need to match
    app.routes.get('/foo').requires(headers={'X-Secret-Header': 'Foo', 'Referer': re.compile(r'example\\.com')})

    # The "agent" condition is a shortcut for the "User-Agent" header
    @get('/').requires(agent=re.compile(r'Firefox'))
    def firefox(c): ...

    # The "host" condition is a shortcut for the detected host
    @get('/').requires(host=re.compile(r'mojolicious\\.org'))
    def mojolicious(c): ...

:mod:`Pyjoyment.Plugin.HeaderCondition` is a route condition for header-based
routes.

This is a core plugin, that means it is always enabled and its code a good
example for learning to build new plugins, you're welcome to fork it.

See :mod:`Pyjoyment.Plugins` for a list of plugins that are available by
default.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Plugin::HeaderCondition
<https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Plugin/HeaderCondition.pm>`_ of Mojolicious 9.49.
"""

import Pyjoyment.Plugin

import re

from typing import TYPE_CHECKING, Any, cast


if TYPE_CHECKING:
    import Pyjoyment
    import Pyjoyment.Controller
    import Pyjoyment.Routes.Route


class Pyjoyment_Plugin_HeaderCondition(Pyjoyment.Plugin.object):
    """
    :mod:`Pyjoyment.Plugin.HeaderCondition` inherits all methods from
    :mod:`Pyjoyment.Plugin` and implements the following new ones.
    """

    def register(self, app: 'Pyjoyment.object', conf: dict[str, Any] | None = None) -> None:
        """::

            plugin.register(Pyjoyment.new())

        Register conditions in :mod:`Pyjoyment` application.
        """
        app.routes.add_condition('headers', _headers)
        app.routes.add_condition('agent', lambda r, c, captures, agent: _headers(r, c, captures, {'User-Agent': agent}))
        app.routes.add_condition('host', lambda r, c, captures, host: _check(c.req.url.to_abs().host, host))


def _check(value: str | None, pattern: Any) -> bool:
    if value and isinstance(pattern, re.Pattern) and cast(re.Pattern[str], pattern).search(value):
        return True
    return bool(value) and pattern is not None and pattern == value


def _headers(
    route: 'Pyjoyment.Routes.Route.object', c: 'Pyjoyment.Controller.object', captures: dict[str, Any], patterns: Any
) -> bool:
    if not patterns or not isinstance(patterns, dict):
        return False

    # All headers need to match
    headers = c.req.headers
    for name, pattern in cast(dict[str, Any], patterns).items():
        if not _check(headers.header(name), pattern):
            return False
    return True


new = Pyjoyment_Plugin_HeaderCondition.new
object = Pyjoyment_Plugin_HeaderCondition
HeaderCondition = Pyjoyment_Plugin_HeaderCondition
