import Pyjo.File
import Pyjoyment
import Pyjoyment.Plugin.JSONConfig

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
# myapp.json (it's just JSON with embedded Python)
{
  %# Just a value
  "foo": "bar",

  %# Nested data structures are fine too
  "baz": ["♥"],

  %# You have full access to the application
  "music_dir": "<%= app.home.child('music') %>"
}
"""

with subtest('Synopsis'):
    # The comment that names the file is not JSON
    app = application(myapp_json=SYNOPSIS.split('\n', 1)[1])

    # Pyjoyment
    config = app.plugin('JSONConfig')
    is_ok(config['foo'], 'bar', 'value')
    is_deeply_ok(config['baz'], ['♥'], 'nested data structure')
    is_ok(config['music_dir'], app.home.child('music').to_str(), 'application')

    # foo.html.ep
    is_ok(app.build_controller().render_to_string(inline="%= config()['foo']"), 'bar\n', 'template')

    # The configuration is available application-wide
    config = app.config()
    is_ok(config['foo'], 'bar', 'application-wide')

    # Everything can be customized with options
    app = application(myapp_conf='{"foo": "conf"}')
    config = app.plugin('JSONConfig', file=app.home.child('myapp.conf').to_str())
    is_ok(config['foo'], 'conf', 'options')

with subtest('Description'):
    app = application(myapp_json='{"foo": "bar", "baz": 1}', myapp_development_json='{"baz": 2}')
    is_deeply_ok(app.plugin('JSONConfig'), {'foo': 'bar', 'baz': 2}, 'mode specific')

    app = application(myapp_json='{"plugins": [{"HeaderCondition": {}}]}')
    app.plugin('JSONConfig')
    ok('headers' in app.routes.conditions, 'plugins')

    app = application(myapp_json='["foo"]')
    throws_ok(lambda: app.plugin('JSONConfig'), re.compile(r'did not return a JSON object'), 'not a JSON object')
    app = application(myapp_json='{')
    throws_ok(lambda: app.plugin('JSONConfig'), re.compile(r"^Can't load configuration .+ Malformed JSON"), 'JSON')

with subtest('template'):
    app = application(myapp_json='. name = app.moniker\n{"name": "<%= name %>"}')

    # Pyjoyment.Lite
    is_ok(app.plugin('JSONConfig', template={'line_start': '.'})['name'], 'myapp', 'template')

with subtest('parse'):
    app = application()
    plugin = Pyjoyment.Plugin.JSONConfig.new()
    is_deeply_ok(plugin.parse('{"foo": "<%= app.moniker %>"}', 'myapp.json', {}, app), {'foo': 'myapp'}, 'parsed')

    class Plugin(Pyjoyment.Plugin.JSONConfig.object):
        def parse(self, content, file, conf, app):
            content = self.render(content, file, conf, app)
            return {'rendered': content}

    is_deeply_ok(Plugin.new().parse('<%= 1 + 1 %>', 'myapp.json', {}, app), {'rendered': '2\n'}, 'custom parse')

with subtest('register'):
    app = application(myapp_json='{"foo": "bar"}', foo_conf='{"foo": "conf"}')
    config = Pyjoyment.Plugin.JSONConfig.new().register(app)
    is_ok(config['foo'], 'bar', 'registered')
    config = Pyjoyment.Plugin.JSONConfig.new().register(app, {'file': app.home.child('foo.conf').to_str()})
    is_ok(config['foo'], 'conf', 'registered with file')

with subtest('render'):
    app = application()
    plugin = Pyjoyment.Plugin.JSONConfig.new()
    is_ok(plugin.render('<%= app.moniker %>', 'myapp.json', {}, app), 'myapp\n', 'rendered')

    class Plugin(Pyjoyment.Plugin.JSONConfig.object):
        def render(self, content, file, conf, app):
            content = '{"foo": "custom"}'
            return content

    is_deeply_ok(Plugin.new().parse('', 'myapp.json', {}, app), {'foo': 'custom'}, 'custom render')

done_testing()
