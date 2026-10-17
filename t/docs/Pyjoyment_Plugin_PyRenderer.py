# /// script
# requires-python = ">=3.14"
# ///
import Pyjoyment

from Pyjo.String.Template import t
from Pyjo.Test import *


app = Pyjoyment.new(secrets=['works'])
app.log.level = 'fatal'

with subtest('Synopsis'):
    # Pyjoyment
    app.plugin('PyRenderer')
    ok('py' in app.renderer.handlers, 'handler')

    name = 'Joe'

    # A t-string of Python 3.14
    c = app.build_controller()
    c.render(inline=t'<p>Hello {name}!</p>')
    is_ok(c.res.text, '<p>Hello Joe!</p>', 't-string')

    # The same on any Python
    c = app.build_controller()
    c.render(inline=t('<p>Hello {name}!</p>', name=name))
    is_ok(c.res.text, '<p>Hello Joe!</p>', 'string')

with subtest('Description'):
    # "<p>Hello &lt;script&gt;!</p>"
    c = app.build_controller()
    name = '<script>'
    c.render(inline=t('<p>Hello {name}!</p>', name=name))
    is_ok(c.res.text, '<p>Hello &lt;script&gt;!</p>', 'escaped')

    # "<p><a href="/">Home</a></p>"
    c = app.build_controller()
    c.render(inline=t('<p>{link}</p>', link=c.link_to('Home', '/')))
    is_ok(c.res.text, '<p><a href="/">Home</a></p>', 'markup')

    c = app.build_controller()
    c.stash(name='stash')
    c.render(inline=t'<p>{c.stash("name")}</p>')
    is_ok(c.res.text, '<p>stash</p>', 'value of the stash')

with subtest('register'):
    plugin = app.plugins.load_plugin('PyRenderer')
    other = Pyjoyment.new()
    other.renderer.handlers.pop('py')
    plugin.register(other)
    ok('py' in other.renderer.handlers, 'registered')

done_testing()
