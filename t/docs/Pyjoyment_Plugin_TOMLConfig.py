import Pyjo.File
import Pyjoyment
import Pyjoyment.Plugin.TOMLConfig

from Pyjo.Test import *

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
# myapp.toml (it's just TOML with embedded Python)
%# Just a value
foo = "bar"

%# Nested data structures are fine too
baz = ["♥"]

%# You have full access to the application
music_dir = "<%= app.home.child('music') %>"

[db]
host = "localhost"
"""

with subtest('Synopsis'):
    app = application(myapp_toml=SYNOPSIS)

    # Pyjoyment
    config = app.plugin('TOMLConfig')
    is_ok(config['foo'], 'bar', 'value')
    is_deeply_ok(config['baz'], ['♥'], 'nested data structure')
    is_ok(config['music_dir'], app.home.child('music').to_str(), 'application')
    is_deeply_ok(config['db'], {'host': 'localhost'}, 'table')

    # foo.html.ep
    is_ok(app.build_controller().render_to_string(inline="%= config()['foo']"), 'bar\n', 'template')

    # The configuration is available application-wide
    config = app.config()
    is_ok(config['foo'], 'bar', 'application-wide')

    # Everything can be customized with options
    app = application(myapp_conf='foo = "conf"')
    config = app.plugin('TOMLConfig', file=app.home.child('myapp.conf').to_str())
    is_ok(config['foo'], 'conf', 'options')

with subtest('Description'):
    app = application(myapp_toml='foo = "bar"\nbaz = 1', myapp_development_toml='baz = 2')
    is_deeply_ok(app.plugin('TOMLConfig'), {'foo': 'bar', 'baz': 2}, 'mode specific')

    app = application(myapp_toml='plugins = [{ HeaderCondition = {} }]')
    app.plugin('TOMLConfig')
    ok('headers' in app.routes.conditions, 'plugins')

    app = application(myapp_toml='foo = ')
    throws_ok(lambda: app.plugin('TOMLConfig'), re.compile(r"^Can't load configuration from file"), 'TOML')

with subtest('parse'):
    app = application()
    plugin = Pyjoyment.Plugin.TOMLConfig.new()
    is_deeply_ok(plugin.parse('foo = "<%= app.moniker %>"', 'myapp.toml', {}, app), {'foo': 'myapp'}, 'parsed')

    class Plugin(Pyjoyment.Plugin.TOMLConfig.object):
        def parse(self, content, file, conf, app):
            content = self.render(content, file, conf, app)
            return {'rendered': content}

    is_deeply_ok(Plugin.new().parse('<%= 1 + 1 %>', 'myapp.toml', {}, app), {'rendered': '2\n'}, 'custom parse')

with subtest('register'):
    app = application(myapp_toml='foo = "bar"', foo_conf='foo = "conf"')
    config = Pyjoyment.Plugin.TOMLConfig.new().register(app)
    is_ok(config['foo'], 'bar', 'registered')
    config = Pyjoyment.Plugin.TOMLConfig.new().register(app, {'file': app.home.child('foo.conf').to_str()})
    is_ok(config['foo'], 'conf', 'registered with file')

done_testing()
