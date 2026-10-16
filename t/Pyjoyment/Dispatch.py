import Pyjo.Upload
import Pyjoyment
import Pyjoyment.Controller

from Pyjo.Test import *

import re
import sys
import types


class Test_Foo(Pyjoyment.Controller.object):
    def bar(self):
        return 1

    def home(self):
        return 1


class Test_Controller(Pyjoyment.Controller.object):
    render_called = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app.log.level = 'fatal'

    def render(self, *args, **kwargs):
        self.render_called = True


# Not in Mojolicious: the package Test of the Perl test is a module in sys.modules, where the routes find its classes
sys.modules['Test'] = types.ModuleType('Test')
sys.modules['Test'].Foo = Test_Foo
sys.modules['Test'].Controller = Test_Controller

# Fresh controller
app = Pyjoyment.new(secrets=['works'])
c = app.build_controller()
is_ok(c.url_for('/').to_str(), '/', 'routes are working')

# Set
c.stash(foo='bar')
is_ok(c.stash('foo'), 'bar', 'set and return a stash value')

# Ref value
stash = c.stash()
is_ok(type(stash), dict, 'return a dict')
is_ok(stash['foo'], 'bar', 'right value')

# Replace
c.stash(foo='baz')
is_ok(c.stash('foo'), 'baz', 'replace and return a stash value')

# Set 0
c.stash(zero=0)
is_ok(c.stash('zero'), 0, 'set and return 0 value')

# Replace with 0
c.stash(foo=0)
is_ok(c.stash('foo'), 0, 'replace and return 0 value')

# Use 0 as key
c.stash({'0': 'boo'})
is_ok(c.stash('0'), 'boo', 'set and get with 0 as key')

# Delete
stash = c.stash()
del stash['foo']
del stash['0']
del stash['zero']
is_ok(c.stash().get('foo'), None, 'element has been deleted')
is_ok(c.stash().get('0'), None, 'element has been deleted')
is_ok(c.stash().get('zero'), None, 'element has been deleted')
c.stash(foo='zoo')
del c.stash()['foo']
is_ok(c.stash().get('foo'), None, 'element has been deleted')

# Set via hash
c.stash({'a': 1, 'b': 2})
stash = c.stash()
is_ok(c.stash()['a'], 1, 'right value')
is_ok(c.stash()['b'], 2, 'right value')

# Override captures
is_ok(c.param('foo'), None, 'no value')
is_ok(c.param('foo', 'works').param('foo'), 'works', 'right value')
is_ok(c.param('foo', 'too').param('foo'), 'too', 'right value')
is_ok(c.param('foo', 'just', 'works').param('foo'), 'works', 'right value')
is_deeply_ok(c.every_param('foo'), ['just', 'works'], 'right values')
is_deeply_ok(c.every_param('bar'), [], 'no values')
is_ok(c.param('foo', None).param('foo'), None, 'no value')
is_ok(c.param('foo', Pyjo.Upload.new(name='bar')).param('foo').name, 'bar', 'right value')
is_ok(c.param('foo', ['ba;r', 'baz']).param('foo'), 'baz', 'right value')
is_deeply_ok(c.every_param('foo'), ['ba;r', 'baz'], 'right values')

# Reserved stash values are hidden
c = app.build_controller()
is_ok(c.param('action', 'test').param('action'), None, 'value is reserved')
is_ok(c.param('app', 'test').param('app'), None, 'value is reserved')
is_ok(c.param('cb', 'test').param('cb'), None, 'value is reserved')
is_ok(c.param('controller', 'test').param('controller'), None, 'value is reserved')
is_ok(c.param('data', 'test').param('data'), None, 'value is reserved')
is_ok(c.param('extends', 'test').param('extends'), None, 'value is reserved')
is_ok(c.param('format', 'test').param('format'), None, 'value is reserved')
is_ok(c.param('handler', 'test').param('handler'), None, 'value is reserved')
is_ok(c.param('inline', 'test').param('inline'), None, 'value is reserved')
is_ok(c.param('json', 'test').param('json'), None, 'value is reserved')
is_ok(c.param('layout', 'test').param('layout'), None, 'value is reserved')
is_ok(c.param('namespace', 'test').param('namespace'), None, 'value is reserved')
is_ok(c.param('path', 'test').param('path'), None, 'value is reserved')
is_ok(c.param('status', 'test').param('status'), None, 'value is reserved')
is_ok(c.param('template', 'test').param('template'), None, 'value is reserved')
is_ok(c.param('text', 'test').param('text'), None, 'value is reserved')
is_ok(c.param('variant', 'test').param('variant'), None, 'value is reserved')

# Controller with application and routes
c = app.set(controller_class=Test_Controller).build_controller()
d = c.app.routes
ok(d, 'initialized')
d.namespaces = ['Test']
d.any('/').requires([]).to(controller='foo', action='home')
d.any('/foo/<capture>').to(controller='foo', action='bar')

# Cache
c = app.build_controller()
c.req.method = 'GET'
c.req.url.parse('/')
ok(d.dispatch(c), 'dispatched')
is_ok(c.stash()['controller'], 'foo', 'right value')
is_ok(c.stash()['action'], 'home', 'right value')
is_ok(c.match.stack[0]['controller'], 'foo', 'right value')
is_ok(c.match.stack[0]['action'], 'home', 'right value')
ok(c.render_called, 'rendered')
cache = d.cache.get('GET:/:0')
ok(cache, 'route has been cached')
c = app.build_controller()
c.req.method = 'GET'
c.req.url.parse('/')
d.match(c)
is_ok(c.stash().get('controller'), None, 'no value')
is_ok(c.stash().get('action'), None, 'no value')
is_ok(c.match.stack[0]['controller'], 'foo', 'right value')
is_ok(c.match.stack[0]['action'], 'home', 'right value')
ok(not c.render_called, 'not rendered')
c = app.build_controller()
c.req.method = 'GET'
c.req.url.parse('/')
ok(d.dispatch(c), 'dispatched')
is_ok(c.stash()['controller'], 'foo', 'right value')
is_ok(c.stash()['action'], 'home', 'right value')
is_ok(c.match.stack[0]['controller'], 'foo', 'right value')
is_ok(c.match.stack[0]['action'], 'home', 'right value')
ok(c.render_called, 'rendered')
is_deeply_ok(d.cache.get('GET:/:0'), cache, 'cached route has been reused')

# 404 clean stash
c = app.build_controller()
c.req.method = 'GET'
c.req.url.parse('/not_found')
ok(not d.dispatch(c), 'not dispatched')
ok(not c.render_called, 'nothing rendered')

# No escaping
c = app.build_controller()
c.req.method = 'POST'
c.req.url.parse('/foo/hello')
c.stash(test=23)
ok(d.dispatch(c), 'dispatched')
is_ok(c.stash()['controller'], 'foo', 'right value')
is_ok(c.stash()['action'], 'bar', 'right value')
is_ok(c.stash()['capture'], 'hello', 'right value')
is_ok(c.stash()['test'], 23, 'right value')
is_ok(c.param('controller'), None, 'no value')
is_ok(c.param('action'), None, 'no value')
is_ok(c.param('capture'), 'hello', 'right value')
c.param('capture', 'bye')
is_ok(c.param('controller'), None, 'no value')
is_ok(c.param('action'), None, 'no value')
is_ok(c.param('capture'), 'bye', 'right value')
c.param('capture', None)
is_ok(c.param('controller'), None, 'no value')
is_ok(c.param('action'), None, 'no value')
is_ok(c.param('capture'), None, 'no value')
c.req.param('foo', 'bar')
is_ok(c.param('controller'), None, 'no value')
is_ok(c.param('action'), None, 'no value')
is_ok(c.param('capture'), None, 'no value')
is_ok(c.param('foo'), 'bar', 'right value')
c.req.param('bar', 'baz')
is_ok(c.param('controller'), None, 'no value')
is_ok(c.param('action'), None, 'no value')
is_ok(c.param('capture'), None, 'no value')
is_ok(c.param('foo'), 'bar', 'right value')
is_ok(c.param('bar'), 'baz', 'right value')
c.req.param('action', 'baz')
is_ok(c.param('controller'), None, 'no value')
is_ok(c.param('action'), 'baz', 'no value')
is_ok(c.param('capture'), None, 'no value')
is_ok(c.param('foo'), 'bar', 'right value')
is_ok(c.param('bar'), 'baz', 'right value')
ok(c.render_called, 'rendered')

# Escaping
c = app.build_controller()
c.req.method = 'GET'
c.req.url.parse('/foo/hello%20there')
ok(d.dispatch(c), 'dispatched')
is_ok(c.stash()['controller'], 'foo', 'right value')
is_ok(c.stash()['action'], 'bar', 'right value')
is_ok(c.stash()['capture'], 'hello there', 'right value')
is_ok(c.param('controller'), None, 'no value')
is_ok(c.param('action'), None, 'no value')
is_ok(c.param('capture'), 'hello there', 'right value')
ok(c.render_called, 'rendered')

# Escaping UTF-8
c = app.build_controller()
c.req.method = 'GET'
c.req.url.parse('/foo/%D0%BF%D1%80%D0%B8%D0%B2%D0%B5%D1%82')
ok(d.dispatch(c), 'dispatched')
is_ok(c.stash()['controller'], 'foo', 'right value')
is_ok(c.stash()['action'], 'bar', 'right value')
is_ok(c.stash()['capture'], 'привет', 'right value')
is_ok(c.param('controller'), None, 'no value')
is_ok(c.param('action'), None, 'no value')
is_ok(c.param('capture'), 'привет', 'right value')
ok(c.render_called, 'rendered')

# Not a WebSocket transaction
throws_ok(lambda: c.send('test'), re.compile(r'^No WebSocket connection to send message to'), 'right error')

done_testing()
