import Pyjo.File
import Pyjo.YAML
import Pyjoyment
import Pyjoyment.Plugin.YAMLConfig

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
# myapp.yml (it's just YAML with embedded Python)
---
foo: bar
baz:
  - ♥
music_dir: <%= app.home.child('music') %>
"""

with subtest('Synopsis'):
    app = application(myapp_yml=SYNOPSIS)

    # Pyjoyment
    config = app.plugin('YAMLConfig')
    is_ok(config['foo'], 'bar', 'value')
    is_deeply_ok(config['baz'], ['♥'], 'nested data structure')
    is_ok(config['music_dir'], app.home.child('music').to_str(), 'application')

    # foo.html.ep
    is_ok(app.build_controller().render_to_string(inline="%= config()['foo']"), 'bar\n', 'template')

    # The configuration is available application-wide
    config = app.config()
    is_ok(config['foo'], 'bar', 'application-wide')

    # Everything can be customized with options
    app = application(myapp_conf='foo: conf')
    config = app.plugin('YAMLConfig', file=app.home.child('myapp.conf').to_str())
    is_ok(config['foo'], 'conf', 'options')

with subtest('Description'):
    app = application(myapp_yml='foo: bar\nbaz: 1', myapp_development_yml='baz: 2')
    is_deeply_ok(app.plugin('YAMLConfig'), {'foo': 'bar', 'baz': '2'}, 'mode specific')

    app = application(myapp_yml='plugins:\n  - HeaderCondition: {}\n')
    app.plugin('YAMLConfig')
    ok('headers' in app.routes.conditions, 'plugins')

    app = application(myapp_yml='- foo\n')
    throws_ok(lambda: app.plugin('YAMLConfig'), re.compile(r'did not return a YAML mapping'), 'not a mapping')

with subtest('module'):
    app = application(myapp_yml='foo: bar')

    # Pyjoyment.Lite
    is_ok(app.plugin('YAMLConfig', module=Pyjo.YAML.load)['foo'], 'bar', 'function')
    is_ok(app.plugin('YAMLConfig', module='Pyjo.YAML')['foo'], 'bar', 'module')
    throws_ok(
        lambda: app.plugin('YAMLConfig', module='Pyjo.YAML.NotThere'),
        re.compile(r'YAML module Pyjo.YAML.NotThere has no Load function'),
        'missing module',
    )

with subtest('parse'):
    app = application()
    plugin = Pyjoyment.Plugin.YAMLConfig.new()
    is_deeply_ok(plugin.parse('foo: <%= app.moniker %>', 'myapp.yml', {}, app), {'foo': 'myapp'}, 'parsed')

    class Plugin(Pyjoyment.Plugin.YAMLConfig.object):
        def parse(self, content, file, conf, app):
            content = self.render(content, file, conf, app)
            return {'rendered': content}

    is_deeply_ok(Plugin.new().parse('<%= 1 + 1 %>', 'myapp.yml', {}, app), {'rendered': '2\n'}, 'custom parse')

with subtest('register'):
    app = application(myapp_yml='foo: bar', foo_conf='foo: conf')
    config = Pyjoyment.Plugin.YAMLConfig.new().register(app)
    is_ok(config['foo'], 'bar', 'registered')
    config = Pyjoyment.Plugin.YAMLConfig.new().register(app, {'file': app.home.child('foo.conf').to_str()})
    is_ok(config['foo'], 'conf', 'registered with file')

done_testing()
