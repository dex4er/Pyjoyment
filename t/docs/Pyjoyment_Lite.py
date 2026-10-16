import Pyjo.Test.Pyjo
import Pyjoyment
import Pyjoyment.Lite

from Pyjo.Test import *
from Pyjoyment.Lite import *

import re


app.log.level = 'fatal'
t = Pyjo.Test.Pyjo.new(app)


def route(r):
    # The methods and the pattern of a route
    return [r.methods(), r.pattern.unparsed]


with subtest('Synopsis'):
    # Route with placeholder
    @get('/:foo')
    def foo(c):
        foo = c.param('foo')
        c.render(text=f'Hello from {foo}.')

    # Start the Pyjoyment command system
    app.start()

    t.get_ok('/bar').content_is('Hello from bar.')

with subtest('Description'):
    isa_ok(app, Pyjoyment.Lite.object, 'application of the module')
    is_ok(app.moniker, 'Pyjoyment_Lite', 'named after its file')
    is_ok(app.renderer.classes[0], __name__, 'DATA templates of the module')
    isa_ok(foo, Pyjoyment.Routes.Route.object, 'a route is a decorator of its callback')

    app.routes.children.clear()
    get('/', {'text': 'Hello World!'})

    @get('/:foo')
    def foo2(c):
        c.render(text=f'Hello from {c.param("foo")}.')

    app.start()

    t.get_ok('/').content_is('Hello World!')
    t.get_ok('/baz').content_is('Hello from baz.')

with subtest('Routes'):
    app.routes.children.clear()

    # Pyjoyment.Lite
    @get('/foo')
    def foo3(c):
        c.render(text='Hello World!')

    # Pyjoyment
    class MyApp(Pyjoyment.object):
        def startup(self):
            routes = self.routes
            routes.get('/foo', lambda c: c.render(text='Hello World!'))

    t.get_ok('/foo').content_is('Hello World!')
    Pyjo.Test.Pyjo.new(MyApp.new()).get_ok('/foo').content_is('Hello World!')

with subtest('Application'):
    # Pyjoyment.Lite
    app.max_request_size = 16777216

    # Pyjoyment
    class MyApp2(Pyjoyment.object):
        def startup(self):
            self.max_request_size = 16777216

    is_ok(MyApp2.new().max_request_size, app.max_request_size, 'same')

with subtest('Plugins'):
    # TODO: the example of the plugin Config, when Pyjoyment.Plugin.Config is ported; until then HeaderCondition
    plugin('HeaderCondition')

    class MyApp3(Pyjoyment.object):
        def startup(self):
            self.plugin('HeaderCondition')

    ok('agent' in MyApp3.new().routes.conditions, 'plugin')

with subtest('Helpers'):
    # Pyjoyment.Lite
    @helper('two')
    def two(c):
        return 1 + 1

    # Pyjoyment
    class MyApp4(Pyjoyment.object):
        def startup(self):
            self.helper('two', lambda c: 1 + 1)

    # The controller refers to its application weakly, so the application is kept
    myapp = MyApp4.new()
    is_ok(app.build_controller().two(), myapp.build_controller().two(), 'same helper')

with subtest('Under'):
    app.routes.children.clear()

    # Pyjoyment.Lite
    with group():
        under('/foo')
        get('/bar', lambda c: c.render(text='bar'))

    # Pyjoyment
    class MyApp5(Pyjoyment.object):
        def startup(self):
            routes = self.routes
            foo = routes.under('/foo')
            foo.get('/bar', lambda c: c.render(text='bar'))

    t.get_ok('/foo/bar').content_is('bar')
    Pyjo.Test.Pyjo.new(MyApp5.new()).get_ok('/foo/bar').content_is('bar')

with subtest('any'):
    route_ = any('/:foo', lambda c: ...)
    is_deeply_ok(route(route_), [None, '/:foo'], 'all methods')
    route_ = any('/:foo', lambda c: ..., 'name')
    is_ok(route_.name, 'name', 'name')
    route_ = any('/:foo', {'foo': 'bar'}, lambda c: ...)
    is_ok(route_.to()['foo'], 'bar', 'defaults')
    route_ = any('/:foo', lambda c: ..., foo=re.compile(r'\w+'))
    ok(route_.pattern.constraints['foo'], 'constraints')
    route_ = any(['GET', 'POST'], '/:foo', lambda c: ...)
    is_deeply_ok(route(route_), [['GET', 'POST'], '/:foo'], 'methods')
    route_ = any(['GET', 'POST'], '/:foo', lambda c: ..., foo=re.compile(r'\w+'))
    route_ = any(['GET', 'POST'], '/:foo', lambda c: ...).requires(agent=re.compile(r'Firefox'))
    is_ok(route_.requires()[0][0], 'agent', 'condition')

with subtest('app'):
    app = app
    is_ok(app, Pyjo.UserAgent.Server.app(), 'default application of the servers')

    # Use all the available attributes and methods
    app.log.level = 'error'
    app.defaults(foo='bar')
    is_ok(app.defaults('foo'), 'bar', 'defaults')
    app.log.level = 'fatal'


def methods(function):
    # The forms of the arguments of a function, which the examples share
    routes = [
        function('/:foo', lambda c: ...),
        function('/:foo', lambda c: ..., 'name'),
        function('/:foo', {'foo': 'bar'}, lambda c: ...),
        function('/:foo', lambda c: ..., foo=re.compile(r'\w+')),
        function('/:foo', lambda c: ...).requires(agent=re.compile(r'Firefox')),
    ]
    return [route(r) for r in routes]


with subtest('delete'):
    is_deeply_ok(methods(delete), [[['DELETE'], '/:foo']] * 5, 'DELETE')
    is_ok(del_, delete, 'alias')

with subtest('get'):
    is_deeply_ok(methods(get), [[['GET'], '/:foo']] * 5, 'GET')

with subtest('group'):
    app.routes.children.clear()
    with group():
        under('/group')
        get('/in', lambda c: c.render(text='in'))
    get('/out', lambda c: c.render(text='out'))
    t.get_ok('/group/in').content_is('in')
    t.get_ok('/out').content_is('out')

    group(lambda: get('/function', lambda c: c.render(text='function')))
    t.get_ok('/function').content_is('function')

with subtest('helper'):
    helper('foo', lambda c, *args: list(args))
    is_ok(app.build_controller().foo(1, 2), [1, 2], 'helper')

with subtest('hook'):
    hook('after_dispatch', lambda c: c.res.headers.header('X-Hook', 'works'))
    t.get_ok('/out').header_is('X-Hook', 'works')

with subtest('options'):
    is_deeply_ok(methods(options), [[['OPTIONS'], '/:foo']] * 5, 'OPTIONS')

with subtest('patch'):
    is_deeply_ok(methods(patch), [[['PATCH'], '/:foo']] * 5, 'PATCH')

with subtest('plugin'):
    # A plugin of Pyjoyment in place of SomePlugin
    plugin('HeaderCondition', foo=23)
    ok('headers' in app.routes.conditions, 'plugin')

with subtest('post'):
    is_deeply_ok(methods(post), [[['POST'], '/:foo']] * 5, 'POST')

with subtest('put'):
    is_deeply_ok(methods(put), [[['PUT'], '/:foo']] * 5, 'PUT')

with subtest('query'):
    is_deeply_ok(methods(query), [[['QUERY'], '/:foo']] * 5, 'QUERY')

with subtest('under'):
    with group():
        route_ = under(lambda c: ...)
        ok(route_.inline, 'nested route')
        route_ = under('/:foo', lambda c: ...)
        route_ = under('/:foo', {'foo': 'bar'})
        route_ = under('/:foo', foo=re.compile(r'\w+'))
        route_ = under('/:foo').requires(agent=re.compile(r'Firefox'))
        route_ = under(format=['json', 'yaml'])
        is_deeply_ok(route_.pattern.constraints['format'], ['json', 'yaml'], 'format')

with subtest('websocket'):
    routes = [
        websocket('/:foo', lambda c: ...),
        websocket('/:foo', lambda c: ..., 'name'),
        websocket('/:foo', {'foo': 'bar'}, lambda c: ...),
        websocket('/:foo', lambda c: ..., foo=re.compile(r'\w+')),
        websocket('/:foo', lambda c: ...).requires(agent=re.compile(r'Firefox')),
    ]
    ok(all(r.is_websocket for r in routes), 'WebSocket handshakes')

done_testing()
