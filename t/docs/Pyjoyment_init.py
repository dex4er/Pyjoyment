import Pyjo.Home
import Pyjo.Log
import Pyjo.Server
import Pyjo.Transaction.HTTP
import Pyjo.UserAgent
import Pyjoyment.Controller
import Pyjoyment.Plugins
import Pyjoyment.Renderer
import Pyjoyment.Routes
import Pyjoyment.Sessions
import Pyjoyment.Static
import Pyjoyment.Types

from Pyjo.String.Template import t
from Pyjo.Test import *

import re
import sys
import types


def request(app, path, method='GET'):
    ua = Pyjo.UserAgent.new()
    ua.server.app = app
    return ua.start(ua.build_tx(method, path))


with subtest('Synopsis'):
    # Application
    import Pyjoyment

    class MyApp(Pyjoyment.object):
        # Route
        def startup(self):
            self.routes.get('/hello').to('foo#hello')

    # Controller
    import Pyjoyment.Controller

    class MyApp_Controller_Foo(Pyjoyment.Controller.object):
        # Action
        def hello(self):
            self.render(text='Hello World!')

    # The modules of the application, where the routes find its controller
    for name in ('MyApp', 'MyApp.Controller', 'MyApp.Controller.Foo'):
        sys.modules[name] = types.ModuleType(name)
    sys.modules['MyApp.Controller.Foo'].object = MyApp_Controller_Foo

    app = MyApp.new()
    app.log.level = 'fatal'
    is_ok(request(app, '/hello').res.text, 'Hello World!', 'controller and action')

with subtest('Hooks'):
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    calls = []

    @app.hook('before_server_start')
    def before_server_start(server, app):
        calls.append('before_server_start')

    @app.hook('after_build_tx')
    def after_build_tx(tx, app):
        calls.append('after_build_tx')

    @app.hook('around_dispatch')
    def around_dispatch(next, c):
        calls.append('around_dispatch')
        next()
        calls.append('around_dispatch (after)')

    @app.hook('before_dispatch')
    def before_dispatch(c):
        calls.append('before_dispatch')

    @app.hook('before_routes')
    def before_routes(c):
        calls.append('before_routes')

    @app.hook('around_action')
    def around_action(next, c, action, last):
        calls.append('around_action')
        return next()

    @app.hook('before_render')
    def before_render(c, args):
        calls.append('before_render')

    @app.hook('after_render')
    def after_render(c, output, format):
        calls.append('after_render')

    @app.hook('after_dispatch')
    def after_dispatch(c):
        calls.append('after_dispatch')

    app.routes.get('/', lambda c: c.render(text='hooks'))
    is_ok(request(app, '/').res.text, 'hooks', 'right content')
    is_ok(calls[0], 'before_server_start', 'server hook first')
    is_deeply_ok(
        calls[calls.index('after_build_tx') :],
        [
            'after_build_tx',
            'around_dispatch',
            'before_dispatch',
            'before_routes',
            'around_action',
            'before_render',
            'after_render',
            'after_dispatch',
            'around_dispatch (after)',
        ],
        'hooks in order',
    )

with subtest('Helpers'):
    app = Pyjoyment.new()

    # Call helper
    is_ok(app.dumper({'foo': 'bar'}), "{'foo': 'bar'}\n", 'helper')

    # Longer version
    is_ok(app.build_controller().helpers.dumper({'foo': 'bar'}), "{'foo': 'bar'}\n", 'longer version')

with subtest('controller_class'):
    app = Pyjoyment.new()
    cls = app.controller_class
    is_ok(cls, Pyjoyment.Controller.object, 'default')
    app.controller_class = Pyjoyment.Controller.object
    isa_ok(app.build_controller(), Pyjoyment.Controller.object, 'controller')

with subtest('exception_format'):
    app = Pyjoyment.new()
    format = app.exception_format
    is_ok(format, 'html', 'default')
    app.exception_format = 'txt'
    is_ok(app.exception_format, 'txt', 'set')

with subtest('home'):
    app = Pyjoyment.new()
    home = app.home
    isa_ok(home, Pyjo.Home.object, 'default')
    app.home = Pyjo.Home.new()

    # Portably generate path relative to home directory
    path = app.home.child('data', 'important.txt')
    like_ok(path.to_str(), r'data[/\\]important\.txt$', 'path')

with subtest('log'):
    app = Pyjoyment.new()
    log = app.log
    isa_ok(log, Pyjo.Log.object, 'default')
    app.log = Pyjo.Log.new()

    # Log debug message
    with app.log.capture('debug') as messages:
        app.log.debug('It works')
    like_ok(str(messages), r'It works', 'logged')

with subtest('max_request_size'):
    app = Pyjoyment.new()
    max = app.max_request_size
    is_ok(max, None, 'default')
    app.max_request_size = 16777216
    is_ok(app.build_tx().req.max_message_size, 16777216, 'set')

with subtest('mode'):
    app = Pyjoyment.new()
    mode = app.mode
    is_ok(mode, 'development', 'default')
    app.mode = 'production'
    is_ok(app.mode, 'production', 'set')

with subtest('moniker'):
    app = Pyjoyment.new()
    moniker = app.moniker
    is_ok(moniker, 'pyjoyment', 'default')
    app.moniker = 'foo_bar'
    is_ok(app.moniker, 'foo_bar', 'set')

with subtest('plugins'):
    app = Pyjoyment.new()
    plugins = app.plugins
    isa_ok(plugins, Pyjoyment.Plugins.object, 'default')
    app.plugins = Pyjoyment.Plugins.new()

    # Add another namespace to load plugins from
    app.plugins.namespaces.append('MyApp.Plugin')
    is_deeply_ok(app.plugins.namespaces, ['Pyjoyment.Plugin', 'MyApp.Plugin'], 'namespaces')

with subtest('preload_namespaces'):
    app = Pyjoyment.new()
    namespaces = app.preload_namespaces
    is_deeply_ok(namespaces, ['Pyjoyment.Controller'], 'default')
    app.preload_namespaces = ['MyApp.Controller']
    is_deeply_ok(app.preload_namespaces, ['MyApp.Controller'], 'set')

with subtest('renderer'):
    app = Pyjoyment.new()
    renderer = app.renderer
    isa_ok(renderer, Pyjoyment.Renderer.object, 'default')
    app.renderer = Pyjoyment.Renderer.new()

    # Enable compression
    app.renderer.compress = True

    # Add another "templates" directory
    app.renderer.paths.append('/home/sri/templates')

    # Add another "templates" directory with higher precedence
    app.renderer.paths.insert(0, '/home/sri/themes/blue/templates')

    # Add another class with templates in DATA section
    app.renderer.classes.append('Pyjoyment.Plugin.Fun')

    is_deeply_ok(app.renderer.paths, ['/home/sri/themes/blue/templates', '/home/sri/templates'], 'paths')
    is_deeply_ok(app.renderer.classes, ['__main__', 'Pyjoyment.Plugin.Fun'], 'classes')

with subtest('routes'):
    app = Pyjoyment.new()
    routes = app.routes
    isa_ok(routes, Pyjoyment.Routes.object, 'default')
    app.routes = Pyjoyment.Routes.new()

    # Add routes
    r = app.routes
    r.get('/foo/bar').to('test#foo', title='Hello Pyjo!')
    r.post('/baz').to('test#baz')

    # Add another namespace to load controllers from
    app.routes.namespaces.append('MyApp.MyController')

    is_ok(r.find('foobar').to()['title'], 'Hello Pyjo!', 'route')
    is_deeply_ok(app.routes.namespaces, ['MyApp.MyController'], 'namespaces')

with subtest('secrets'):
    app = Pyjoyment.new()
    with app.log.capture('trace') as messages:
        secrets = app.secrets
    is_deeply_ok(secrets, ['pyjoyment'], 'default')
    like_ok(str(messages), r'Your secret passphrase needs to be changed', 'insecure default')
    app.secrets = ['passphrase']

    # Rotate passphrases
    app.secrets = ['new_passw0rd', 'old_passw0rd', 'very_old_passw0rd']
    is_ok(app.secrets[0], 'new_passw0rd', 'rotated')

with subtest('sessions'):
    app = Pyjoyment.new()
    sessions = app.sessions
    isa_ok(sessions, Pyjoyment.Sessions.object, 'default')
    app.sessions = Pyjoyment.Sessions.new()

    # Change name of cookie used for all sessions
    app.sessions.cookie_name = 'mysession'

    # Disable SameSite feature
    app.sessions.samesite = None

    is_ok(app.sessions.cookie_name, 'mysession', 'cookie name')
    is_ok(app.sessions.samesite, None, 'no SameSite')

with subtest('static'):
    app = Pyjoyment.new()
    static = app.static
    isa_ok(static, Pyjoyment.Static.object, 'default')
    app.static = Pyjoyment.Static.new()

    # Serve static files only with a "/static" prefix
    app.static.prefix = '/static'

    # Add another "public" directory
    app.static.paths.append('/home/sri/public')

    # Add another "public" directory with higher precedence
    app.static.paths.insert(0, '/home/sri/themes/blue/public')

    # Add another class with static files in DATA section
    app.static.classes.append('Pyjoyment.Plugin.Fun')

    # Remove built-in favicon
    del app.static.extra['favicon.ico']

    is_deeply_ok(app.static.paths, ['/home/sri/themes/blue/public', '/home/sri/public'], 'paths')
    ok('favicon.ico' not in app.static.extra, 'no favicon')

with subtest('types'):
    app = Pyjoyment.new()
    types_ = app.types
    isa_ok(types_, Pyjoyment.Types.object, 'default')
    app.types = Pyjoyment.Types.new()

    # Add custom MIME type
    app.types.type('twt', 'text/tweet')
    is_ok(app.types.type('twt'), 'text/tweet', 'custom type')

with subtest('ua'):
    app = Pyjoyment.new()
    ua = app.ua
    isa_ok(ua, Pyjo.UserAgent.object, 'default')
    app.ua = Pyjo.UserAgent.new()
    # The example of a blocking request needs the network, so it is not run

with subtest('build_controller'):
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    c = app.build_controller()
    isa_ok(c, Pyjoyment.Controller.object, 'controller')
    tx = Pyjo.Transaction.HTTP.new()
    c = app.build_controller(tx)
    is_ok(c.tx, tx, 'with a transaction, which the controller keeps weakly')
    c = app.build_controller(Pyjoyment.Controller.new(stash={'foo': 'bar'}, tx=c.tx))
    is_ok(c.stash('foo'), 'bar', 'embedded')

    # Render template from application
    foo = app.build_controller().render_to_string(template='foo')
    is_ok(foo, None, 'no template')

with subtest('build_tx'):
    app = Pyjoyment.new()
    tx = app.build_tx()
    isa_ok(tx, Pyjo.Transaction.HTTP.object, 'transaction')

with subtest('config'):
    app = Pyjoyment.new()
    hash = app.config()
    is_deeply_ok(hash, {}, 'empty')
    app = app.config({'foo': 'bar', 'baz': 23})
    app = app.config(foo='bar', baz=23)
    foo = app.config('foo')
    is_ok(foo, 'bar', 'value')

    # Remove value
    foo = app.config().pop('foo')

    # Assign multiple values at once
    app.config(foo='test', bar=23)
    is_deeply_ok(app.config(), {'baz': 23, 'foo': 'test', 'bar': 23}, 'values')

with subtest('defaults'):
    app = Pyjoyment.new()
    hash = app.defaults()
    is_deeply_ok(hash, {}, 'empty')
    app = app.defaults({'foo': 'bar', 'baz': 23})
    app = app.defaults(foo='bar', baz=23)
    foo = app.defaults('foo')
    is_ok(foo, 'bar', 'value')

    # Remove value
    foo = app.defaults().pop('foo')

    # Assign multiple values at once
    app.defaults(foo='test', bar=23)
    is_ok(app.build_controller().stash('bar'), 23, 'stash of a new controller')

with subtest('dispatch'):
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    app.routes.get('/', lambda c: c.render(text='dispatched'))
    # The handler of the first request puts the action dispatcher last in the hook around_action
    app.handler(Pyjo.Transaction.HTTP.new())
    c = app.build_controller()
    c.req.method = 'GET'
    c.req.url.parse('/')
    app.dispatch(c)
    is_ok(c.res.body, b'dispatched', 'dispatched')

with subtest('handler'):
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    app.routes.get('/', lambda c: c.render(text='handled'))
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.method = 'GET'
    tx.req.url.parse('/')
    app.handler(tx)
    is_ok(tx.res.body, b'handled', 'handled')
    c = app.build_controller(tx)
    app.handler(c)
    is_ok(c.res.code, 200, 'handled with a controller')

with subtest('helper'):
    app = Pyjoyment.new()
    app.helper('foo', lambda c, *args: 'foo')

    @app.helper('bar')
    def bar(c, *args):
        return 'bar'

    is_ok(app.foo(), 'foo', 'helper')
    is_ok(app.bar(), 'bar', 'decorated helper')

    # Helper
    cache = {}
    app.helper('cache', lambda c: cache)

    # Application
    app.cache()['foo'] = 'bar'
    result = app.cache()['foo']
    is_ok(result, 'bar', 'application')

    # Controller
    c = app.build_controller()
    c.cache()['foo'] = 'bar'
    result = c.cache()['foo']
    is_ok(result, 'bar', 'controller')

with subtest('hook'):
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    app.hook('after_dispatch', lambda c: ...)

    @app.hook('after_dispatch')
    def after_dispatch(c): ...

    # Dispatchers will not run if there's already a response code defined
    @app.hook('before_dispatch')
    def before_dispatch(c):
        if re.search(r'do_not_dispatch', c.req.url.path.to_route()):
            c.render(text='Skipped static file server and router!')

    is_ok(request(app, '/do_not_dispatch').res.text, 'Skipped static file server and router!', 'skipped')

with subtest('new'):
    app = Pyjoyment.new()
    isa_ok(app, Pyjoyment.object, 'application')
    app = Pyjoyment.new(moniker='foo_bar')
    is_ok(app.moniker, 'foo_bar', 'keyword argument')
    app = Pyjoyment.new({'moniker': 'foo_bar'})
    is_ok(app.moniker, 'foo_bar', 'dict')

with subtest('plugin'):
    app = Pyjoyment.new()
    app.plugin('header_condition')
    app.plugin('header_condition', foo=23)
    app.plugin('header_condition', {'foo': 23})
    app.plugin('HeaderCondition')
    app.plugin('HeaderCondition', foo=23)
    app.plugin('HeaderCondition', {'foo': 23})
    app.plugin('Pyjoyment.Plugin.HeaderCondition')
    app.plugin('Pyjoyment.Plugin.HeaderCondition', foo=23)
    app.plugin('Pyjoyment.Plugin.HeaderCondition', {'foo': 23})
    ok('agent' in app.routes.conditions, 'plugin registered')

with subtest('server'):
    app = Pyjoyment.new()
    servers = []
    app.hook('before_server_start', lambda server, app: servers.append(server))
    server = Pyjo.Server.new()
    app.server(server)
    is_ok(servers[0], server, 'hook emitted')

with subtest('start'):
    app = Pyjoyment.new()
    is_ok(app.start(), app, 'started')

with subtest('startup'):

    class App(Pyjoyment.object):
        def startup(self):
            self.started = True

    ok(App.new().started, 'called at startup')

with subtest('template'):
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    app.template('index.html', lambda c: t('<p>Hello!</p>'))

    @app.template('index.html')
    def index(c): ...

    is_ok(app.renderer.templates['index.html'], index, 'decorator')

    # Template
    @app.template('hello.html')
    def hello(c, name):
        return t('<p>Hello {name}!</p>')

    # Controller
    c = app.build_controller()
    c.render('hello', name='Joe')
    is_ok(c.res.text, '<p>Hello Joe!</p>', 'rendered')

with subtest('warmup'):
    app = Pyjoyment.new()
    app.preload_namespaces = ['Pyjoyment.Plugin']
    app.warmup()
    ok('Pyjoyment.Plugin.DefaultHelpers' in sys.modules, 'preloaded')

done_testing()
