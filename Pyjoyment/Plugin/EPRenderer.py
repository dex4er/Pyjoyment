"""
Pyjoyment.Plugin.EPRenderer - Embedded Python renderer plugin
=============================================================
::

    # Pyjoyment
    app.plugin('EPRenderer')
    app.plugin('EPRenderer', name='foo')
    app.plugin('EPRenderer', name='bar', template={'line_start': '.'})

:mod:`Pyjoyment.Plugin.EPRenderer` is a renderer for Embedded Python
templates, ``ep``, the default handler of :mod:`Pyjoyment`. They are
templates of :mod:`Pyjo.Template` with automatic escaping, in which the
values of the stash are variables, ``self`` and ``c`` are the current
controller, and the helpers are functions. ::

    % title('Welcome!')
    <p>Hello <%= name %>, this is <%= url_for('index') %>.</p>

A value of the stash hides a helper of the same name, which is still a
method of ``c``, as is the helper ``c``, which the variable ``c`` hides. ::

    % c.title('Welcome!')
    %= c.c('a', 'b', 'c').join(', ')

This is a core plugin, that means it is always enabled and its code a good
example for learning to build new plugins, you're welcome to fork it.

See :mod:`Pyjoyment.Plugins` for a list of plugins that are available by
default.

Options
-------

:mod:`Pyjoyment.Plugin.EPRenderer` supports the following options.

name ::

    app.plugin('EPRenderer', name='foo')

Handler name, defaults to ``ep``.

template ::

    app.plugin('EPRenderer', template={'line_start': '.'})

Attribute values passed to :mod:`Pyjo.Template` objects used to render
templates.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Plugin::EPRenderer
<https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Plugin/EPRenderer.pm>`_ of Mojolicious 9.49.
"""

# TODO: the examples of Pyjoyment.Lite in the synopsis and the options, when it is ported

import Pyjo.Base
import Pyjo.Template
import Pyjoyment.Plugin.EPLRenderer

from Pyjo.Util import encode, md5_sum

import io
import re
import sys
import types
import weakref

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast


if TYPE_CHECKING:
    import Pyjoyment
    import Pyjoyment.Controller
    import Pyjoyment.Renderer


class Pyjoyment_Plugin_EPRenderer(Pyjoyment.Plugin.EPLRenderer.object):
    """
    :mod:`Pyjoyment.Plugin.EPRenderer` inherits all methods from
    :mod:`Pyjoyment.Plugin.EPLRenderer` and implements the following new ones.
    """

    def register(self, app: 'Pyjoyment.object', conf: dict[str, Any] | None = None) -> None:
        """::

            plugin.register(Pyjoyment.new())
            plugin.register(Pyjoyment.new(), {'name': 'foo'})

        Register renderer in :mod:`Pyjoyment` application.
        """
        conf = conf or {}
        self._helpers = False

        # Auto escape by default to prevent XSS attacks
        ep: dict[str, Any] = {'auto_escape': True, **(conf.get('template') or {}), 'vars': True}
        ns = ep['namespace'] = ep.get('namespace') or f'Pyjo.Template.Sandbox.{md5_sum(repr(self).encode())}'

        # Unlike Mojolicious: the namespace is a module, which the plugin makes when it is not loaded, and the plugin
        # removes the names that it adds, where Mojo removes all the names of the package, even of one that the option
        # "template" names
        module = sys.modules.get(ns)
        if module is None:
            module = sys.modules[ns] = types.ModuleType(ns)

            # No spec, as the module has no source that linecache could read, which warns of a spec without a loader
            del module.__spec__
        else:
            ns = None
        names: list[str] = []
        weakref.finalize(self, _teardown, module, names, ns)

        # Make "self" and "c" available in templates
        ep['prepend'] = 'self = c = _C()' + (f'\n{ep["prepend"]}' if ep.get('prepend') else '')

        # Add "ep" handler and make it the default
        def handler(
            renderer: 'Pyjoyment.Renderer.object',
            c: 'Pyjoyment.Controller.object',
            output: io.StringIO,
            options: dict[str, Any],
        ) -> None:
            name = options.get('inline')
            if name is None:
                name = renderer.template_name(options)
            if name is None:
                return
            key = md5_sum(encode('UTF-8', name))

            cache = renderer.cache
            if (mt := cache.get(key)) is None:
                cache.set(key, mt := Pyjo.Template.new(**ep))

            # Export helpers only once
            if not self._helpers:
                self._helpers = True
                _helpers(module, renderer.helpers, names)

            # Make current controller available and render with "epl" handler
            saved = module.__dict__.get('_C', _MISSING)
            module.__dict__['_C'] = lambda: c
            try:
                Pyjoyment.Plugin.EPLRenderer._render(  # pyright: ignore[reportPrivateUsage]
                    renderer, c, output, options, cast(Pyjo.Template.object, mt), c.stash()
                )
            finally:
                if saved is _MISSING:
                    module.__dict__.pop('_C', None)
                else:
                    module.__dict__['_C'] = saved

        app.renderer.default_handler = 'ep'
        app.renderer.add_handler(conf.get('name') or 'ep', handler)


_MISSING: Any = Pyjo.Base.object()


def _helper(module: types.ModuleType, sub: Callable[..., Any]) -> Callable[..., Any]:
    def helper(*args: Any, **kwargs: Any) -> Any:
        return sub(module.__dict__['_C'](), *args, **kwargs)

    return helper


def _helpers(module: types.ModuleType, helpers: dict[str, Callable[..., Any]], names: list[str]) -> None:
    for method in [method for method in helpers if re.fullmatch(r'\w+', method)]:
        setattr(module, method, _helper(module, helpers[method]))
        names.append(method)


def _teardown(module: types.ModuleType, names: list[str], ns: str | None) -> None:
    for name in [*names, '_C']:
        module.__dict__.pop(name, None)
    if ns is not None and sys.modules.get(ns) is module:
        del sys.modules[ns]


new = Pyjoyment_Plugin_EPRenderer.new
object = Pyjoyment_Plugin_EPRenderer
