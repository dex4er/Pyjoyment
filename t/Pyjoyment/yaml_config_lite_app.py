"""
__DATA__
@@ index.html.ep
<%= config()['foo'] %><%= config('foo') %>
"""

import Pyjo.File
import Pyjo.Test.Pyjo

from Pyjo.Test import *
from Pyjoyment.Lite import app, get, plugin

import importlib.util
import os
import sys


# BEGIN { $ENV{MOJO_MODE} = 'development' }, before the mode of the application is read
os.environ['PYJO_MODE'] = 'development'

# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# Renamed from Mojolicious: the plugin is YAMLConfig, where Mojo has NotYAMLConfig

# Renamed from Mojolicious: the modules of the tests are in tt/lib, where Mojo has them in t/mojolicious/lib
sys.path.insert(0, Pyjo.File.path(__file__).to_abs().dirname().dirname().dirname().child('tt', 'lib').to_str())

with subtest('Default'):
    app.config(it='works')
    is_deeply_ok(app.config(), {'it': 'works'}, 'right value')

with subtest('Invalid config file'):
    try:
        plugin('YAMLConfig', file='public/hello.txt')
    except Exception as e:
        like_ok(str(e), r"Can't load configuration from file", 'right error')

with subtest('Load plugins'):
    config = plugin('YAMLConfig', default={'foo': 'baz', 'hello': 'there'})
    path = Pyjo.File.path(__file__).sibling('yaml_config_lite_app_abs.yml')
    plugin('YAMLConfig', file=path.to_str())
    is_ok(config['foo'], 'barbaz', 'right value')
    is_ok(config['hello'], 'there', 'right value')
    is_ok(config['utf'], 'утф', 'right value')
    is_ok(config['absolute'], 'works too!!!', 'right value')
    is_ok(config['absolute_dev'], 'dev works too yaml_config_lite_app!!!', 'right value')
    is_ok(app.config()['foo'], 'barbaz', 'right value')
    is_ok(app.config()['hello'], 'there', 'right value')
    is_ok(app.config()['utf'], 'утф', 'right value')
    is_ok(app.config()['absolute'], 'works too!!!', 'right value')
    is_ok(app.config()['absolute_dev'], 'dev works too yaml_config_lite_app!!!', 'right value')
    is_ok(app.config('foo'), 'barbaz', 'right value')
    is_ok(app.config('hello'), 'there', 'right value')
    is_ok(app.config('utf'), 'утф', 'right value')
    is_ok(app.config('absolute'), 'works too!!!', 'right value')
    is_ok(app.config('absolute_dev'), 'dev works too yaml_config_lite_app!!!', 'right value')
    is_ok(app.config('it'), 'works', 'right value')
    is_ok(app.deployment_helper(), 'deployment plugins work!', 'right value')
    is_ok(app.another_helper(), 'works too!', 'right value')

get('/', 'index')

t = Pyjo.Test.Pyjo.new()

t.get_ok('/').status_is(200).content_is('barbazbarbaz\n')

with subtest('No config file, default only'):
    config = plugin('YAMLConfig', file='nonexistent', default={'foo': 'qux'})
    is_ok(config['foo'], 'qux', 'right value')
    is_ok(app.config()['foo'], 'qux', 'right value')
    is_ok(app.config('foo'), 'qux', 'right value')
    is_ok(app.config('it'), 'works', 'right value')


def eval_(cb):
    try:
        return cb()
    except Exception:
        return None


with subtest('No config file, no default'):
    ok(not eval_(lambda: plugin('YAMLConfig', file='nonexistent')), 'no config file')
    os.environ['PYJO_CONFIG'] = 'nonexistent'
    try:
        ok(not eval_(lambda: plugin('YAMLConfig')), 'no config file')
    finally:
        del os.environ['PYJO_CONFIG']

with subtest('PyYAML'):
    # Renamed from Mojolicious: the module PyYAML, yaml, where Mojo has YAML::XS
    if importlib.util.find_spec('yaml') is None:
        skip('PyYAML required!', 6)
    else:
        config = plugin('YAMLConfig', module='yaml', ext='yaml', default={'foo': 'baz', 'hello': 'there'})
        is_ok(config['foo'], 'yada', 'right value')
        is_ok(config['hello'], 'there', 'right value')
        is_ok(config['utf8'], 'утф', 'right value')
        is_ok(app.config()['foo'], 'yada', 'right value')
        is_ok(app.config()['hello'], 'there', 'right value')
        is_ok(app.config()['utf8'], 'утф', 'right value')

with subtest('Missing YAML parser'):
    try:
        plugin('YAMLConfig', module='ThisYAMLModuleDoesNotExist')
    except Exception as e:
        like_ok(str(e), r'YAML module ThisYAMLModuleDoesNotExist has no Load function', 'right error')

done_testing()
