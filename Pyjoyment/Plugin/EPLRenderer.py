"""
Pyjoyment.Plugin.EPLRenderer - Embedded Python Lite renderer plugin
===================================================================
::

    # Pyjoyment
    app.plugin('EPLRenderer')

:mod:`Pyjoyment.Plugin.EPLRenderer` is a renderer for ``epl`` templates,
which are pretty much just raw :mod:`Pyjo.Template`. The template gets the
controller as its first argument. ::

    % c = args[0]
    Hello <%= c.param('name') %>!

This is a core plugin, that means it is always enabled and its code a good
example for learning to build new plugins, you're welcome to fork it.

See :mod:`Pyjoyment.Plugins` for a list of plugins that are available by
default.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Plugin::EPLRenderer
<https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Plugin/EPLRenderer.pm>`_ of Mojolicious 9.49.
"""

# TODO: the examples of Pyjoyment.Lite in the synopsis, when it is ported

import Pyjo.Exception
import Pyjo.Template
import Pyjoyment.Plugin

from Pyjo.Util import encode, md5_sum

import io

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    import Pyjoyment
    import Pyjoyment.Controller
    import Pyjoyment.Renderer


class Pyjoyment_Plugin_EPLRenderer(Pyjoyment.Plugin.object):
    """
    :mod:`Pyjoyment.Plugin.EPLRenderer` inherits all methods from
    :mod:`Pyjoyment.Plugin` and implements the following new ones.
    """

    def register(self, app: 'Pyjoyment.object', conf: dict[str, Any] | None = None) -> None:
        """::

            plugin.register(Pyjoyment.new())

        Register renderer in :mod:`Pyjoyment` application.
        """
        app.renderer.add_handler('epl', _handler)


def _handler(
    renderer: 'Pyjoyment.Renderer.object',
    c: 'Pyjoyment.Controller.object',
    output: io.StringIO,
    options: dict[str, Any],
) -> None:
    _render(renderer, c, output, options, Pyjo.Template.new(), c)


def _render(
    renderer: 'Pyjoyment.Renderer.object',
    c: 'Pyjoyment.Controller.object',
    output: io.StringIO,
    options: dict[str, Any],
    mt: Pyjo.Template.object,
    *args: Any,
) -> None:
    log = c.helpers.log()

    # Cached
    if mt.compiled is not None:
        log.trace(f'Rendering cached {mt.name}')
        result = mt.process(*args)

    # Not cached
    else:
        inline = options.get('inline')
        name = md5_sum(encode('UTF-8', inline)) if inline is not None else renderer.template_name(options)
        if name is None:
            return

        # Inline
        if inline is not None:
            log.trace(f'Rendering inline template "{name}"')
            mt.name = f'inline template "{name}"'
            result = mt.render(inline, *args)

        # File
        else:
            if encoding := renderer.encoding:
                mt.encoding = encoding

            # Try template
            if (path := renderer.template_path(options)) is not None:
                log.trace(f'Rendering template "{name}"')
                mt.name = f'template "{name}"'
                result = mt.render_file(path, *args)

            # Try DATA section
            elif (d := renderer.get_data_template(options)) is not None:
                log.trace(f'Rendering template "{name}" from DATA section')
                mt.name = f'template "{name}" from DATA section'
                result = mt.render(d if isinstance(d, str) else d.decode('latin-1'), *args)

            # No template
            else:
                log.trace(f'Template "{name}" not found')
                return

    # Exception
    if isinstance(result, Pyjo.Exception.object):
        raise result
    output.write(result)


new = Pyjoyment_Plugin_EPLRenderer.new
object = Pyjoyment_Plugin_EPLRenderer
