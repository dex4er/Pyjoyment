"""
__DATA__
@@ index.html.ep
<%= config()['foo'] %><%= config('foo') %>
"""

import Pyjo.File
import Pyjo.Test.Pyjo

from Pyjo.Test import *
from Pyjoyment.Lite import app, get, plugin

import os
import sys


# Not in Mojolicious: the test of Pyjoyment.Plugin.TOMLConfig, after json_config_lite_app.t

# The mode of the application, before it is read
os.environ['PYJO_MODE'] = 'development'

# The modules of the tests
sys.path.insert(0, Pyjo.File.path(__file__).to_abs().dirname().dirname().dirname().child('tt', 'lib').to_str())

with subtest('Default'):
    app.config(it='works')
    is_deeply_ok(app.config(), {'it': 'works'}, 'right value')

with subtest('Invalid config file'):
    try:
        plugin('TOMLConfig', file='public/hello.txt')
    except Exception as e:
        like_ok(str(e), r'Can.t load configuration', 'right error')

with subtest('Load plugins'):
    config = plugin('t_o_m_l_config', default={'foo': 'baz', 'hello': 'there'})
    path = Pyjo.File.path(__file__).sibling('toml_config_lite_app_abs.toml')
    plugin('TOMLConfig', file=path.to_str())
    is_ok(config['foo'], 'bar', 'right value')
    is_ok(config['hello'], 'there', 'right value')
    is_ok(config['utf'], 'утф', 'right value')
    is_ok(config['absolute'], 'works too!', 'right value')
    is_ok(config['absolute_dev'], 'dev works too!', 'right value')
    is_ok(app.config()['foo'], 'bar', 'right value')
    is_ok(app.config()['hello'], 'there', 'right value')
    is_ok(app.config()['utf'], 'утф', 'right value')
    is_ok(app.config()['absolute'], 'works too!', 'right value')
    is_ok(app.config()['absolute_dev'], 'dev works too!', 'right value')
    is_ok(app.config('foo'), 'bar', 'right value')
    is_ok(app.config('hello'), 'there', 'right value')
    is_ok(app.config('utf'), 'утф', 'right value')
    is_ok(app.config('absolute'), 'works too!', 'right value')
    is_ok(app.config('absolute_dev'), 'dev works too!', 'right value')
    is_ok(app.config('it'), 'works', 'right value')
    is_ok(app.deployment_helper(), 'deployment plugins work!', 'right value')
    is_ok(app.another_helper(), 'works too!', 'right value')

get('/', 'index')

t = Pyjo.Test.Pyjo.new()

t.get_ok('/').status_is(200).content_is('barbar\n')

with subtest('No config file, default only'):
    config = plugin('TOMLConfig', file='nonexistent', default={'foo': 'qux'})
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
    ok(not eval_(lambda: plugin('TOMLConfig', file='nonexistent')), 'no config file')
    os.environ['PYJO_CONFIG'] = 'nonexistent'
    try:
        ok(not eval_(lambda: plugin('TOMLConfig')), 'no config file')
    finally:
        del os.environ['PYJO_CONFIG']

done_testing()
