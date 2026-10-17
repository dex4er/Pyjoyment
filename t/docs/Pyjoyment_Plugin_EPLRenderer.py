import Pyjoyment

from Pyjo.Test import *
from Pyjoyment.Lite import app as lite
from Pyjoyment.Lite import plugin


app = Pyjoyment.new(secrets=['works'])
app.log.level = 'fatal'

with subtest('Synopsis'):
    # Pyjoyment
    app.plugin('EPLRenderer')
    ok('epl' in app.renderer.handlers, 'handler')

    # Pyjoyment.Lite
    lite.renderer.handlers.pop('epl')
    plugin('EPLRenderer')
    ok('epl' in lite.renderer.handlers, 'handler of Lite')

with subtest('Description'):
    c = app.build_controller()
    c.param('name', 'Joe')
    template = """\
% c = args[0]
Hello <%= c.param('name') %>!
"""
    is_ok(c.render_to_string(inline=template, handler='epl'), 'Hello Joe!\n', 'controller as the first argument')
    is_ok(c.render_to_string(inline='<%= "<b>" %>', handler='epl'), '<b>\n', 'no automatic escaping')

with subtest('register'):
    plugin = app.plugins.load_plugin('EPLRenderer')
    other = Pyjoyment.new()
    other.renderer.handlers.pop('epl')
    plugin.register(other)
    ok('epl' in other.renderer.handlers, 'registered')

done_testing()
