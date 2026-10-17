"""
__DATA__

@@ works.html.ep
Hello from the main app!
"""

import Pyjo.File
import Pyjo.Test.Pyjo

from Pyjo.Test import *
from Pyjoyment.Lite import app, get, hook, plugin

import os


# BEGIN { $ENV{MOJO_MODE} = 'testing' }, before the mode of the application is read
os.environ['PYJO_MODE'] = 'testing'

# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# Custom secret
app.secrets = ['very secr3t!']

# Mount full external application a few times
# Renamed from Mojolicious: the external application is in tt/external, where Mojo has it in t/mojolicious/external
external = Pyjo.File.path(__file__).to_abs().dirname().dirname().dirname().child('tt', 'external', 'script', 'my_app')
plugin('Mount', {'/x/1': external})
plugin('Mount', {'/x/♥': external})
plugin('Mount', {'MOJOLICIOUS.ORG/': external})
plugin('Mount', {'*.foo-bar.de/♥/123': external})


# Make sure session can be modified from both apps
@hook('before_routes')
def before_routes(c):
    if not c.req.url.path.contains('/x/1/secondary'):
        return
    session = c.session()
    session['secondary'] = session.get('secondary', 0) + 10


get('/hello', 'works')


@get('/primary')
def primary(c):
    session = c.session()
    session['primary'] = session.get('primary', 0) + 1
    c.render(text=str(session['primary']))


t = Pyjo.Test.Pyjo.new()

with subtest('Normal request'):
    t.get_ok('/hello').status_is(200).content_is('Hello from the main app!\n')

with subtest('Session'):
    t.get_ok('/primary').status_is(200).content_is('1')
    t.get_ok('/primary').status_is(200).content_is('2')

with subtest('Session in external app'):
    t.get_ok('/x/1/secondary').status_is(200).content_is('11')

with subtest('Session again'):
    t.get_ok('/primary').status_is(200).content_is('3')

with subtest('Session in external app again'):
    t.get_ok('/x/1/secondary').status_is(200).content_is('22')

with subtest('External app'):
    t.get_ok('/x/1').status_is(200).content_is('too%21')

with subtest('Static file from external app'):
    t.get_ok('/x/1/index.html').status_is(200).content_is('External static file!\n')

with subtest('External app with different prefix'):
    t.get_ok('/x/1/test').status_is(200).content_is('works%21')

with subtest('External app with Unicode prefix'):
    t.get_ok('/x/♥').status_is(200).content_is('too%21')

with subtest('Static file from external app with Unicode prefix'):
    t.get_ok('/x/♥/index.html').status_is(200).content_is('External static file!\n')

with subtest('External app with Unicode prefix again'):
    t.get_ok('/x/♥/test').status_is(200).content_is('works%21')

with subtest('External app with domain'):
    t.get_ok('/', {'Host': 'mojolicious.org'}).status_is(200).content_is('too%21')

with subtest('Static file from external app with domain'):
    t.get_ok('/index.html', {'Host': 'mojolicious.org'}).status_is(200).content_is('External static file!\n')

with subtest('External app with domain again'):
    t.get_ok('/test', {'Host': 'mojolicious.org'}).status_is(200).content_is('works%21')

with subtest('External app with a bit of everything'):
    t.get_ok('/♥/123/', {'Host': 'test.foo-bar.de'}).status_is(200).content_is('too%21')

with subtest('Static file from external app with a bit of everything'):
    t.get_ok('/♥/123/index.html', {'Host': 'test.foo-bar.de'}).status_is(200).content_is('External static file!\n')

with subtest('External app with a bit of everything again'):
    t.get_ok('/♥/123/test', {'Host': 'test.foo-bar.de'}).status_is(200).content_is('works%21')

done_testing()
