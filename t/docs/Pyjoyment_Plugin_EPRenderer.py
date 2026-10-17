import Pyjoyment

from Pyjo.Test import *
from Pyjoyment.Lite import app as lite
from Pyjoyment.Lite import plugin


app = Pyjoyment.new(secrets=['works'])
app.log.level = 'fatal'
lite.log.level = 'fatal'

with subtest('Synopsis'):
    # Pyjoyment
    app.plugin('EPRenderer')
    app.plugin('EPRenderer', name='foo')
    app.plugin('EPRenderer', name='bar', template={'line_start': '.'})
    ok('foo' in app.renderer.handlers, 'name')
    c = app.build_controller()
    is_ok(c.render_to_string(inline='.= 1 + 1', handler='bar'), '2\n', 'template')
    is_ok(app.renderer.default_handler, 'ep', 'default handler')

    # Pyjoyment.Lite
    plugin('EPRenderer')
    plugin('EPRenderer', name='foo')
    plugin('EPRenderer', name='bar', template={'line_start': '.'})
    ok('foo' in lite.renderer.handlers, 'name of Lite')
    c = lite.build_controller()
    is_ok(c.render_to_string(inline='.= 1 + 1', handler='bar'), '2\n', 'template of Lite')

with subtest('Description'):
    app.routes.get('/').set(name='index')
    c = app.build_controller()
    template = """\
% title('Welcome!')
<p>Hello <%= name %>, this is <%= url_for('index') %>.</p>
"""
    is_ok(c.render_to_string(inline=template, name='<Joe>'), '<p>Hello &lt;Joe&gt;, this is /.</p>\n', 'output')
    is_ok(c.stash('title'), 'Welcome!', 'helper')
    is_ok(c.render_to_string(inline='<%= self is c %>'), 'True\n', 'controller')

    c = app.build_controller()
    c.stash(title='Hello')
    template = """\
% c.title('Welcome!')
%= c.c('a', 'b', 'c').join(', ')
"""
    is_ok(c.render_to_string(inline=template), 'a, b, c\n', 'methods of the controller')
    is_ok(c.stash('title'), 'Welcome!', 'helper hidden by a value of the stash')

with subtest('name'):
    # Pyjoyment.Lite
    plugin('EPRenderer', name='foo')
    ok('foo' in lite.renderer.handlers, 'handler name')

with subtest('template'):
    # Pyjoyment.Lite
    plugin('EPRenderer', template={'line_start': '.'})
    c = lite.build_controller()
    is_ok(c.render_to_string(inline='.= 2 + 2'), '4\n', 'attribute values')

with subtest('register'):
    plugin = app.plugins.load_plugin('EPRenderer')
    other = Pyjoyment.new()
    plugin.register(other)
    plugin = app.plugins.load_plugin('EPRenderer')
    plugin.register(other, {'name': 'foo'})
    ok('foo' in other.renderer.handlers, 'registered')

done_testing()
