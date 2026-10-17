"""
__DATA__

@@ works.html.ep
Hello from the main app!
"""

import Pyjo.File
import Pyjo.Test.Pyjo
import Pyjoyment

from Pyjo.Test import *
from Pyjoyment.Lite import app, get, plugin

import os
import sys


# BEGIN { $ENV{MOJO_MODE} = 'testing' }, before the mode of the application is read
os.environ['PYJO_MODE'] = 'testing'

# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# Renamed from Mojolicious: the modules of the tests are in tt/lib, where Mojo has them in t/mojolicious/lib
sys.path.insert(0, Pyjo.File.path(__file__).to_abs().dirname().dirname().dirname().child('tt', 'lib').to_str())

# Unlike Mojolicious: the packages TestApp, MyTestApp::Test1 and MyTestApp::Test2 of the Perl test are modules of
# tt/lib, as an application of Pyjoyment.Lite is one of a module, in the directory that sys.path has from above
import TestApp  # noqa: E402  # pyright: ignore[reportMissingImports]


# Renamed from Mojolicious: the package MyTestApp::Basic, a subclass of Mojolicious, is a class of the test
class MyTestApp_Basic(Pyjoyment.object):
    def handler(self, c):
        c.res.code = 200
        test = c.param('test')
        c.res.body = f'Hello {test}!'.encode()
        c.rendered()


# Plugin app
plugin('PluginWithEmbeddedApp')

app.routes.namespaces = ['MyTestApp']

# Mount full external application a few times
# Renamed from Mojolicious: the external applications are in tt/external, where Mojo has them in t/mojolicious/external
external = Pyjo.File.path(__file__).to_abs().dirname().dirname().dirname().child('tt', 'external', 'myapp.py')
plugin('Mount', {'/x/1': external})
route = plugin('Mount', {'/x/♥': external}).to(message='works 2!')
is_ok(route.to()['message'], 'works 2!', 'right message')
is_ok(route.pattern.defaults['app'].same_name(), 'myapp', 'right name')
plugin('Mount', {'/y/1': external.sibling('myapp2.py')})
plugin('Mount', {'mojolicious.org': external})
plugin('Mount', {'/y/♥': external.sibling('myapp2.py')}).to(message='works 3!')
plugin('Mount', {'MOJOLICIOUS.ORG/': external})
plugin('Mount', {'*.example.com': external})
plugin('Mount', {'*.foo-bar.de/♥/123': external}).to(message='works 3!')

get('/hello', 'works')

get('/bye', {'name': 'second embedded'}).set(partial=True).to('MyTestApp.Test1')

get('/bar', {'name': 'third embedded'}).set(partial=True).to(app='MyTestApp.Test1')

get('/baz').set(partial=True).to('test1#', name='fourth embedded')

get('/yada').to('test1#', name='fifth embedded')

get('/yada/yada/yada').to('test1#', path='/yada', name='sixth embedded')

get('/basic').set(partial=True).to(MyTestApp_Basic.new(), test='lalala')

get('/third', {'app': 'MyTestApp.Test2', 'name': 'third embedded'}).set(partial=True)

app.routes.any('/hello').set(partial=True).to(TestApp.app).to(name='embedded')

get('/just', {'name': 'working'}).set(partial=True).to('EmbeddedTestApp')

get('/host', {'text': 'main application!'})

t = Pyjo.Test.Pyjo.new()

# Renamed from Mojolicious: the package of a configuration file, Mojolicious::Plugin::Config::Sandbox, is the module
# Pyjoyment.Plugin.Config.Sandbox in the templates below

with subtest('PluginWithEmbeddedApp'):
    t.get_ok('/plugin/foo').status_is(200).content_is('plugin works!')

with subtest('main'):
    t.get_ok('/hello').status_is(200).content_is('Hello from the main app!\n')

with subtest('TestApp'):
    t.get_ok('/hello/hello').status_is(200).content_is('Hello from the embedded (1) app!')

with subtest('TestApp again'):
    t.get_ok('/hello/hello').status_is(200).content_is('Hello from the embedded (2) app!')

with subtest('TestApp again'):
    t.get_ok('/hello/hello').status_is(200).content_is('Hello from the embedded (3) app!')

with subtest('MyTestApp::Test1'):
    t.get_ok('/bye/bye').status_is(200).content_is('Hello from the embedded (1) app!second embedded! success!')

with subtest('MyTestApp::Test1 with different prefix'):
    t.get_ok('/bar/bye').status_is(200).content_is('Hello from the embedded (2) app!third embedded! success!')

with subtest('MyTestApp::Test1 with yet another prefix'):
    t.get_ok('/baz/bye').status_is(200).content_is('Hello from the embedded (3) app!fourth embedded! success!')

with subtest('::Test1 without prefix'):
    t.get_ok('/yada').status_is(200).content_is('yada fifth embedded works!')

with subtest('404 from MyTestApp::Test1'):
    t.get_ok('/yada/yada').status_is(404)

with subtest('MyTestApp::Test1 with a long prefix'):
    t.get_ok('/yada/yada/yada').status_is(200).content_is('yada sixth embedded works!')

with subtest('MyTestApp::Basic'):
    t.get_ok('/basic').status_is(200).content_is('Hello lalala!')

with subtest('MyTestApp::Test2'):
    t.get_ok('/third').status_is(200).content_is('Bye from the third embedded app! /third!')

with subtest('EmbeddedTestApp'):
    t.get_ok('/just/works').status_is(200).content_is('It is working!\n')

with subtest('EmbeddedTestApp again'):
    t.get_ok('/just/works/too').status_is(200).content_is('It just works!\n')

with subtest('Template from myapp.pl'):
    t.get_ok('/x/1/').status_is(200).content_is(
        """\
myapp
works ♥!Insecure!Insecure!

too!works!!!Pyjoyment.Plugin.Config.Sandbox
<a href="/x/1/">Test</a>
<form action="/x/1/%E2%98%83">
  <input type="submit" value="☃">
</form>
"""
    )

with subtest('Template from myapp.pl (no trailing slash)'):
    t.get_ok('/x/1').status_is(200).content_is(
        """\
myapp
works ♥!Insecure!Insecure!

too!works!!!Pyjoyment.Plugin.Config.Sandbox
<a href="/x/1/">Test</a>
<form action="/x/1/%E2%98%83">
  <input type="submit" value="☃">
</form>
"""
    )

with subtest('Static file from myapp.pl'):
    t.get_ok('/x/1/index.html').status_is(200).content_is('External static file!\n')

with subtest('Echo from myapp.pl'):
    t.get_ok('/x/1/echo').status_is(200).content_is('echo: nothing!')

with subtest('Stream from myapp.pl'):
    t.get_ok('/x/1/stream').status_is(200).content_is('hello!')

with subtest('URL from myapp.pl'):
    t.get_ok('/x/1/url/☃').status_is(200).content_is('/x/1/url/%E2%98%83.json -> /x/1/%E2%98%83/stream!')

with subtest('Route to template from myapp.pl'):
    t.get_ok('/x/1/template/menubar').status_is(200).content_is('myapp\nworks ♥!Insecure!Insecure!\n')

with subtest('Missing template from myapp.pl'):
    t.get_ok('/x/1/template/does_not_exist').status_is(500).content_like(r'Server Error')

with subtest('Template from myapp.pl with Unicode prefix'):
    t.get_ok('/x/♥/').status_is(200).content_is(
        """\
myapp
works ♥!Insecure!Insecure!

too!works!!!Pyjoyment.Plugin.Config.Sandbox
<a href="/x/%E2%99%A5/">Test</a>
<form action="/x/%E2%99%A5/%E2%98%83">
  <input type="submit" value="☃">
</form>
"""
    )

with subtest('Template from myapp.pl with Unicode prefix (no trailing slash)'):
    t.get_ok('/x/♥').status_is(200).content_is(
        """\
myapp
works ♥!Insecure!Insecure!

too!works!!!Pyjoyment.Plugin.Config.Sandbox
<a href="/x/%E2%99%A5/">Test</a>
<form action="/x/%E2%99%A5/%E2%98%83">
  <input type="submit" value="☃">
</form>
"""
    )

with subtest('Static file from myapp.pl with Unicode prefix'):
    t.get_ok('/x/♥/index.html').status_is(200).content_is('External static file!\n')

with subtest('Echo from myapp.pl with Unicode prefix'):
    t.get_ok('/x/♥/echo').status_is(200).content_is('echo: works 2!')

with subtest('Stream from myapp.pl with Unicode prefix'):
    t.get_ok('/x/♥/stream').status_is(200).content_is('hello!')

with subtest('URL from myapp.pl with Unicode prefix'):
    (
        t.get_ok('/x/♥/url/☃')
        .status_is(200)
        .content_is('/x/%E2%99%A5/url/%E2%98%83.json -> /x/%E2%99%A5/%E2%98%83/stream!')
    )

with subtest('Route to template from myapp.pl with Unicode prefix'):
    t.get_ok('/x/♥/template/menubar').status_is(200).content_is('myapp\nworks ♥!Insecure!Insecure!\n')

with subtest('Missing template from myapp.pl with Unicode prefix'):
    t.get_ok('/x/♥/template/does_not_exist').status_is(500).content_like(r'Server Error')

with subtest('A little bit of everything from myapp2.pl'):
    t.get_ok('/y/1').status_is(200).content_is('myapp2\nworks 4!\nInsecure too!')

with subtest('Route to template from myapp.pl again (helpers sharing the same name)'):
    t.get_ok('/x/1/template/menubar').status_is(200).content_is('myapp\nworks ♥!Insecure!Insecure!\n')

with subtest('Caching helper from myapp2.pl'):
    t.get_ok('/y/1/cached?cache=foo').status_is(200).content_is('foo')

with subtest('Caching helper with cached value from myapp2.pl'):
    t.get_ok('/y/1/cached?cache=fail').status_is(200).content_is('foo')

with subtest('404 from myapp2.pl'):
    t.get_ok('/y/1/2').status_is(404)

with subtest('myapp2.pl with Unicode prefix'):
    t.get_ok('/y/♥').status_is(200).content_is('myapp2\nworks 3!\nInsecure too!')

with subtest('Caching helper from myapp2.pl with Unicode prefix'):
    t.get_ok('/y/♥/cached?cache=bar').status_is(200).content_is('bar')

with subtest('Caching helper with cached value from myapp2.pl with Unicode prefix'):
    t.get_ok('/y/♥/cached?cache=fail').status_is(200).content_is('bar')

with subtest('404 from myapp2.pl with Unicode prefix'):
    t.get_ok('/y/♥/2').status_is(404)

with subtest('main'):
    t.get_ok('/host').status_is(200).content_is('main application!')

with subtest('Template from myapp.pl with domain'):
    t.get_ok('/', {'Host': 'mojolicious.org'}).status_is(200).content_is(
        """\
myapp
works ♥!Insecure!Insecure!

too!works!!!Pyjoyment.Plugin.Config.Sandbox
<a href="/">Test</a>
<form action="/%E2%98%83">
  <input type="submit" value="☃">
</form>
"""
    )

with subtest('Host from myapp.pl with domain'):
    (
        t.get_ok('/host', {'Host': 'mojolicious.org'})
        .status_is(200)
        .header_is('X-Message', 'it works!')
        .content_is('mojolicious.org')
    )

with subtest('Template from myapp.pl with domain again'):
    t.get_ok('/', {'Host': 'mojolicious.org'}).status_is(200).content_is(
        """\
myapp
works ♥!Insecure!Insecure!

too!works!!!Pyjoyment.Plugin.Config.Sandbox
<a href="/">Test</a>
<form action="/%E2%98%83">
  <input type="submit" value="☃">
</form>
"""
    )

with subtest('Host from myapp.pl with domain again'):
    (
        t.get_ok('/host', {'Host': 'mojolicious.org'})
        .status_is(200)
        .header_is('X-Message', 'it works!')
        .content_is('mojolicious.org')
    )

with subtest('Template from myapp.pl with wildcard domain'):
    t.get_ok('/', {'Host': 'example.com'}).status_is(200).content_is(
        """\
myapp
works ♥!Insecure!Insecure!

too!works!!!Pyjoyment.Plugin.Config.Sandbox
<a href="/">Test</a>
<form action="/%E2%98%83">
  <input type="submit" value="☃">
</form>
"""
    )

with subtest('Host from myapp.pl with wildcard domain'):
    (
        t.get_ok('/host', {'Host': 'ExAmPlE.CoM'})
        .status_is(200)
        .header_is('X-Message', 'it works!')
        .content_is('ExAmPlE.CoM')
    )

with subtest('Host from myapp.pl with wildcard domain again'):
    (
        t.get_ok('/host', {'Host': 'www.example.com'})
        .status_is(200)
        .header_is('X-Message', 'it works!')
        .content_is('www.example.com')
    )

with subtest('Host from myapp.pl with wildcard domain again'):
    (
        t.get_ok('/host', {'Host': 'foo.bar.example.com'})
        .status_is(200)
        .header_is('X-Message', 'it works!')
        .content_is('foo.bar.example.com')
    )

with subtest('Template from myapp.pl with wildcard domain and Unicode prefix'):
    t.get_ok('/♥/123/', {'Host': 'foo-bar.de'}).status_is(200).content_is(
        """\
myapp
works ♥!Insecure!Insecure!

too!works!!!Pyjoyment.Plugin.Config.Sandbox
<a href="/%E2%99%A5/123/">Test</a>
<form action="/%E2%99%A5/123/%E2%98%83">
  <input type="submit" value="☃">
</form>
"""
    )

with subtest('Host from myapp.pl with wildcard domain and Unicode prefix'):
    (
        t.get_ok('/♥/123/host', {'Host': 'foo-bar.de'})
        .status_is(200)
        .header_is('X-Message', 'it works!')
        .content_is('foo-bar.de')
    )

with subtest('Echo from myapp.pl with wildcard domain and Unicode prefix'):
    t.get_ok('/♥/123/echo', {'Host': 'foo-bar.de'}).status_is(200).content_is('echo: works 3!')

with subtest('Host from myapp.pl with wildcard domain and Unicode prefix again'):
    (
        t.get_ok('/♥/123/host', {'Host': 'www.foo-bar.de'})
        .status_is(200)
        .header_is('X-Message', 'it works!')
        .content_is('www.foo-bar.de')
    )

with subtest('Host from myapp.pl with wildcard domain and Unicode prefix again'):
    t.get_ok('/♥/123/echo', {'Host': 'www.foo-bar.de'}).status_is(200).content_is('echo: works 3!')

with subtest('Text from myapp.pl with wildcard domain and Unicode prefix'):
    t.get_ok('/♥/123/one', {'Host': 'www.foo-bar.de'}).status_is(200).content_is('One')

with subtest('Another text from myapp.pl with wildcard domain and Unicode prefix'):
    t.get_ok('/♥/123/one/two', {'Host': 'www.foo-bar.de'}).status_is(200).content_is('Two')

with subtest('Invalid domain'):
    t.get_ok('/', {'Host': 'mojoliciousxorg'}).status_is(404)

with subtest('Another invalid domain'):
    t.get_ok('/', {'Host': 'www.kraihxcom'}).status_is(404)

with subtest('Embedded WebSocket'):
    (
        t.websocket_ok('/x/♥/url_for')
        .send_ok('ws_test')
        .message_ok()
        .message_like(r'^ws://127\.0\.0\.1:\d+/x/%E2%99%A5/url_for$')
        .send_ok('index')
        .message_ok()
        .message_like(r'^http://127\.0\.0\.1:\d+/x/%E2%99%A5$')
        .finish_ok()
    )

with subtest('Template from myapp.pl (shared logger)'):
    with t.app.log.capture('trace') as logs:
        t.get_ok('/x/1').status_is(200).content_is(
            """\
myapp
works ♥!Insecure!Insecure!

too!works!!!Pyjoyment.Plugin.Config.Sandbox
<a href="/x/1/">Test</a>
<form action="/x/1/%E2%98%83">
  <input type="submit" value="☃">
</form>
"""
        )
        # Renamed from Mojolicious: the class of the application is Pyjoyment.Lite.Pyjoyment_Lite
        like_ok(str(logs), r'Routing to application "Pyjoyment\.Lite\.Pyjoyment_Lite"', 'right message')
        like_ok(str(logs), r'Rendering cached template "menubar.html.ep" from DATA section', 'right message')

done_testing()
