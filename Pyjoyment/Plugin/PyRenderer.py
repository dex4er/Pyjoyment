"""
Pyjoyment.Plugin.PyRenderer - Template string renderer plugin
=============================================================
::

    # Pyjoyment
    app.plugin('PyRenderer')

    # A t-string of Python 3.14
    c.render(inline=t'<p>Hello {name}!</p>')

    # The same on any Python
    c.render(inline=t('<p>Hello {name}!</p>', name=name))

:mod:`Pyjoyment.Plugin.PyRenderer` is a renderer for ``py`` templates, which
are template strings, t-strings of
`PEP 750 <https://peps.python.org/pep-0750/>`_ or of
:func:`Pyjo.String.Template.t`, rendered by :mod:`Pyjo.String.Template`, which
escapes the values that they interpolate, unless they are markup, as the
helpers of :mod:`Pyjoyment.Plugin.TagHelpers` return. An inline template that
is a template string is rendered by it, unless another handler is given. ::

    from Pyjo.String.Template import t

    # "<p>Hello &lt;script&gt;!</p>"
    name = '<script>'
    c.render(inline=t('<p>Hello {name}!</p>', name=name))

    # "<p><a href="/">Home</a></p>"
    c.render(inline=t('<p>{link}</p>', link=c.link_to('Home', '/')))

The values of a t-string are evaluated where it is written, so a template
string gets the values of the stash as the code around it does,
``c.stash('name')``, and calls the helpers as methods of the controller.

This is a core plugin, that means it is always enabled and its code a good
example for learning to build new plugins, you're welcome to fork it.

See :mod:`Pyjoyment.Plugins` for a list of plugins that are available by
default.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Inspired by `Mojolicious::Plugin::EPLRenderer
<https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Plugin/EPLRenderer.pm>`_ of Mojolicious 9.49.
"""

# TODO: the templates of functions, with a decorator for Pyjoyment.Lite, and the templates of files, as
# "index.html.py", in the next steps of the renderer of t-strings

import Pyjo.String.Template
import Pyjoyment.Plugin

from Pyjo.Util import encode, md5_sum

import io

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    import Pyjoyment
    import Pyjoyment.Controller
    import Pyjoyment.Renderer


class Pyjoyment_Plugin_PyRenderer(Pyjoyment.Plugin.object):
    """
    :mod:`Pyjoyment.Plugin.PyRenderer` inherits all methods from
    :mod:`Pyjoyment.Plugin` and implements the following new ones.
    """

    def register(self, app: 'Pyjoyment.object', conf: dict[str, Any] | None = None) -> None:
        """::

            plugin.register(Pyjoyment.new())

        Register renderer in :mod:`Pyjoyment` application.
        """
        app.renderer.add_handler('py', _handler)


def _handler(
    renderer: 'Pyjoyment.Renderer.object',
    c: 'Pyjoyment.Controller.object',
    output: io.StringIO,
    options: dict[str, Any],
) -> None:
    inline = options.get('inline')
    if not Pyjo.String.Template.is_template(inline):
        return

    # Inline
    template = Pyjo.String.Template.t(inline)
    name = md5_sum(encode('UTF-8', '{}'.join(template.strings)))
    c.helpers.log().trace(f'Rendering inline template "{name}"')
    output.write(template.render())


new = Pyjoyment_Plugin_PyRenderer.new
object = Pyjoyment_Plugin_PyRenderer
