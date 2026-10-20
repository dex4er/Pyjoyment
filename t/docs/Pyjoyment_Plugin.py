import Pyjoyment

from Pyjo.Test import *


with subtest('Synopsis'):
    # CamelCase plugin name
    from Pyjoyment.Plugin import Plugin

    class Pyjoyment_Plugin_MyPlugin(Plugin):
        def register(self, app, conf):
            # Magic here! :)
            app.config(conf)

    app = Pyjoyment.new()
    Pyjoyment_Plugin_MyPlugin().register(app, {'foo': 'bar'})
    is_ok(app.config('foo'), 'bar', 'registered')

    # CamelCase plugin name
    import Pyjoyment.Plugin

    class Pyjoyment_Plugin_MyPlugin(Pyjoyment.Plugin.object):
        def register(self, app, conf):
            # Magic here! :)
            app.config(conf)

    app = Pyjoyment.new()
    Pyjoyment_Plugin_MyPlugin.new().register(app, {'foo': 'bar'})
    is_ok(app.config('foo'), 'bar', 'registered')

with subtest('register'):
    plugin = Pyjoyment.Plugin.new()
    throws_ok(lambda: plugin.register(Pyjoyment.new(), {}), NotImplementedError, 'meant to be overloaded')
    throws_ok(
        lambda: plugin.register(Pyjoyment.new(), {'foo': 'bar'}),
        'Method "register" not implemented by subclass',
        'right message',
    )

done_testing()
