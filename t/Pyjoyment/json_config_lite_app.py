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


# BEGIN { $ENV{MOJO_MODE} = 'development' }, before the mode of the application is read
os.environ['PYJO_MODE'] = 'development'

# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# Renamed from Mojolicious: the modules of the tests are in tt/lib, where Mojo has them in t/mojolicious/lib
sys.path.insert(0, Pyjo.File.path(__file__).to_abs().dirname().dirname().dirname().child('tt', 'lib').to_str())

with subtest('Default'):
    app.config(it='works')
    is_deeply_ok(app.config(), {'it': 'works'}, 'right value')

with subtest('Invalid config file'):
    try:
        plugin('JSONConfig', file='public/hello.txt')
    except Exception as e:
        like_ok(str(e), r'JSON', 'right error')

with subtest('Load plugins'):
    config = plugin('j_s_o_n_config', default={'foo': 'baz', 'hello': 'there'})
    path = Pyjo.File.path(__file__).sibling('json_config_lite_app_abs.json')
    plugin('JSONConfig', file=path.to_str())
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
    config = plugin('JSONConfig', file='nonexistent', default={'foo': 'qux'})
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
    ok(not eval_(lambda: plugin('JSONConfig', file='nonexistent')), 'no config file')
    os.environ['PYJO_CONFIG'] = 'nonexistent'
    try:
        ok(not eval_(lambda: plugin('JSONConfig')), 'no config file')
    finally:
        del os.environ['PYJO_CONFIG']

done_testing()
