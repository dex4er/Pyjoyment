import Pyjoyment
import Pyjoyment.Plugin.HeaderCondition

from Pyjo.Test import *


with subtest('Synopsis'):
    from Pyjoyment.Plugins import Plugins

    plugins = Plugins()
    plugins.namespaces.append('MyApp.Plugin')
    is_deeply_ok(plugins.namespaces, ['Pyjoyment.Plugin', 'MyApp.Plugin'], 'namespaces')

    import Pyjoyment.Plugins

    plugins = Pyjoyment.Plugins.new()
    plugins.namespaces.append('MyApp.Plugin')
    is_deeply_ok(plugins.namespaces, ['Pyjoyment.Plugin', 'MyApp.Plugin'], 'namespaces')

with subtest('namespaces'):
    plugins = Pyjoyment.Plugins.new()
    namespaces = plugins.namespaces
    is_deeply_ok(namespaces, ['Pyjoyment.Plugin'], 'default')
    plugins.namespaces = ['Pyjoyment.Plugin']

    # Add another namespace to load plugins from
    plugins.namespaces.append('MyApp.Plugin')
    is_deeply_ok(plugins.namespaces, ['Pyjoyment.Plugin', 'MyApp.Plugin'], 'appended')

with subtest('emit_chain'):
    plugins = Pyjoyment.Plugins.new()
    calls = []
    plugins.on('foo', lambda next, *args: calls.append(('first', args)) or next())
    plugins.on('foo', lambda next, *args: calls.append(('second', args)))
    plugins.emit_chain('foo')
    plugins.emit_chain('foo', 123)
    is_deeply_ok(calls, [('first', ()), ('second', ()), ('first', (123,)), ('second', (123,))], 'chained')

with subtest('emit_hook'):
    plugins = Pyjoyment.Plugins.new()
    calls = []
    plugins.on('foo', lambda *args: calls.append(('first', args)))
    plugins.on('foo', lambda *args: calls.append(('second', args)))
    plugins = plugins.emit_hook('foo')
    plugins = plugins.emit_hook('foo', 123)
    is_deeply_ok(calls, [('first', ()), ('second', ()), ('first', (123,)), ('second', (123,))], 'hooks')

with subtest('emit_hook_reverse'):
    plugins = Pyjoyment.Plugins.new()
    calls = []
    plugins.on('foo', lambda *args: calls.append(('first', args)))
    plugins.on('foo', lambda *args: calls.append(('second', args)))
    plugins = plugins.emit_hook_reverse('foo')
    plugins = plugins.emit_hook_reverse('foo', 123)
    is_deeply_ok(calls, [('second', ()), ('first', ()), ('second', (123,)), ('first', (123,))], 'reverse order')

with subtest('load_plugin'):
    plugins = Pyjoyment.Plugins.new()
    plugin = plugins.load_plugin('header_condition')
    plugin = plugins.load_plugin('HeaderCondition')
    plugin = plugins.load_plugin('Pyjoyment.Plugin.HeaderCondition')
    isa_ok(plugin, Pyjoyment.Plugin.HeaderCondition.object, 'plugin')

with subtest('register_plugin'):
    plugins = Pyjoyment.Plugins.new()
    app = Pyjoyment.new()
    plugins.register_plugin('header_condition', app)
    plugins.register_plugin('header_condition', app, foo=23)
    plugins.register_plugin('header_condition', app, {'foo': 23})
    plugins.register_plugin('HeaderCondition', app)
    plugins.register_plugin('Pyjoyment.Plugin.HeaderCondition', app, {'foo': 23})
    ok('host' in app.routes.conditions, 'registered')

done_testing()
