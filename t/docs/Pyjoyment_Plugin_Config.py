import Pyjo.File
import Pyjoyment
import Pyjoyment.Plugin.Config

from Pyjo.Test import *

import os
import re


# The configuration files of the examples are in a temporary directory, the home of the application, as a test writes
# nothing into t
def application(**files):
    tmp = Pyjo.File.tempdir()
    for name, content in files.items():
        tmp.child(name.replace('_', '.')).spew(content.encode())
    app = Pyjoyment.new(home=tmp, moniker='myapp')
    app.log.level = 'fatal'
    app._tmp = tmp
    return app


SYNOPSIS = """\
# myapp.conf (it's just Python ending with a dict)
{
    # Just a value
    'foo': 'bar',

    # Nested data structures are fine too
    'baz': ['♥'],

    # You have full access to the application
    'music_dir': app.home.child('music'),
}
"""

with subtest('Synopsis'):
    app = application(myapp_conf=SYNOPSIS)

    # Pyjoyment
    config = app.plugin('Config')
    is_ok(config['foo'], 'bar', 'value')
    is_deeply_ok(config['baz'], ['♥'], 'nested data structure')
    is_ok(config['music_dir'], app.home.child('music'), 'application')

    # foo.html.ep
    is_ok(app.build_controller().render_to_string(inline="%= config()['foo']"), 'bar\n', 'template')

    # The configuration is available application-wide
    config = app.config()
    is_ok(config['foo'], 'bar', 'application-wide')

    # Everything can be customized with options
    app = application(myapp_stuff="{'foo': 'stuff'}")
    config = app.plugin('Config', file=app.home.child('myapp.stuff').to_str())
    is_ok(config['foo'], 'stuff', 'options')

with subtest('Description'):
    app = application(myapp_conf="import os\nname = app.moniker\n{'name': name, 'sep': os.sep}")
    is_deeply_ok(app.plugin('Config'), {'name': 'myapp', 'sep': os.sep}, 'statements before the last expression')

    app = application(myapp_conf="{'foo': 'bar', 'baz': 1}", myapp_development_conf="{'baz': 2}")
    is_deeply_ok(app.plugin('Config'), {'foo': 'bar', 'baz': 2}, 'mode specific')

    app = application(myapp_conf="{'foo': 'bar'}")
    app.config(config_override=1, foo='baz')
    is_ok(app.plugin('Config')['foo'], 'baz', 'config_override')

    app = application(myapp_conf="{'plugins': [{'HeaderCondition': {}}]}")
    app.plugin('Config')
    ok('headers' in app.routes.conditions, 'plugins')

    app = application(myapp_conf="{'plugins': 'fail'}")
    throws_ok(lambda: app.plugin('Config'), re.compile(r'^Configuration value "plugins" is not a list'), 'not a list')
    app = application(myapp_conf="{'plugins': ['fail']}")
    throws_ok(
        lambda: app.plugin('Config'),
        re.compile(r'^Configuration value "plugins" contains an entry that is not a dict'),
        'plugin not a dict',
    )

    app = application(myapp_conf="['foo']")
    throws_ok(lambda: app.plugin('Config'), re.compile(r'myapp\.conf" did not return a dict'), 'not a dict')
    app = application(myapp_conf='{')
    throws_ok(
        lambda: app.plugin('Config'), re.compile(r"^Can't load configuration from file .+ was never closed"), 'syntax'
    )
    app = application()
    throws_ok(
        lambda: app.plugin('Config'), re.compile(r'myapp\.conf" missing, maybe you need to create it\?'), 'missing'
    )

with subtest('default'):
    app = application()

    # Pyjoyment.Lite
    is_ok(app.plugin('Config', default={'foo': 'bar'})['foo'], 'bar', 'default')

with subtest('ext'):
    app = application(myapp_stuff="{'foo': 'stuff'}")

    # Pyjoyment.Lite
    is_ok(app.plugin('Config', ext='stuff')['foo'], 'stuff', 'ext')

with subtest('file'):
    app = application(myapp_conf="{'foo': 'relative'}", foo_stuff="{'foo': 'absolute'}")

    # Pyjoyment.Lite
    is_ok(app.plugin('Config', file='myapp.conf')['foo'], 'relative', 'relative')
    is_ok(app.plugin('Config', file=app.home.child('foo.stuff').to_str())['foo'], 'absolute', 'absolute')

    os.environ['PYJO_CONFIG'] = app.home.child('myapp.conf').to_str()
    try:
        is_ok(app.plugin('Config')['foo'], 'relative', 'PYJO_CONFIG')
    finally:
        del os.environ['PYJO_CONFIG']

with subtest('load'):
    app = application(myapp_conf="{'foo': 'bar'}")
    plugin = Pyjoyment.Plugin.Config.new()
    file = app.home.child('myapp.conf').to_str()
    conf = {}
    is_deeply_ok(plugin.load(file, conf, app), {'foo': 'bar'}, 'loaded')

    class Plugin(Pyjoyment.Plugin.Config.object):
        def load(self, file, conf, app):
            content = "{'foo': 'custom'}"
            return self.parse(content, file, conf, app)

    is_deeply_ok(Plugin.new().load(file, conf, app), {'foo': 'custom'}, 'custom load')

with subtest('parse'):
    app = application()
    plugin = Pyjoyment.Plugin.Config.new()
    is_deeply_ok(plugin.parse("{'foo': app.moniker}", 'myapp.conf', {}, app), {'foo': 'myapp'}, 'parsed')

with subtest('register'):
    app = application(myapp_conf="{'foo': 'bar'}", app_conf="{'foo': 'app'}")
    config = Pyjoyment.Plugin.Config.new().register(app)
    is_ok(config['foo'], 'bar', 'registered')
    config = Pyjoyment.Plugin.Config.new().register(app, {'file': app.home.child('app.conf').to_str()})
    is_ok(config['foo'], 'app', 'registered with file')

done_testing()
