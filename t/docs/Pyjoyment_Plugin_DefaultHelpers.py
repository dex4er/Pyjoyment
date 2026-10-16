import Pyjo.Collection
import Pyjo.Exception
import Pyjo.String.Bytes
import Pyjo.Transaction.HTTP
import Pyjoyment

from Pyjo.Test import *

import re


# The applications are kept, as a controller refers to its application weakly
apps = []


def controller():
    app = Pyjoyment.new(secrets=['works'])
    app.log.level = 'fatal'
    apps.append(app)
    return app.build_controller()


with subtest('Synopsis'):
    app = Pyjoyment.new()

    # Pyjoyment
    app.plugin('DefaultHelpers')
    ok(app.renderer.get_helper('url_with'), 'helpers')

with subtest('accepts'):
    c = controller()
    c.req.headers.accept = 'application/json'
    formats = c.accepts()
    format = c.accepts('html', 'json', 'txt')
    is_deeply_ok([formats, format], [['json'], 'json'], 'formats')

    # Check if JSON is acceptable
    if c.accepts('json'):
        c.render(json={'hello': 'world'})

    c = controller()

    # Check if JSON was specifically requested
    if c.accepts('', 'json'):
        c.render(json={'hello': 'world'})

    # Unsupported representation
    if not (format := c.accepts('html', 'json')):
        c.render(data=b'', status=204)

    # Detected representations to select from
    formats = c.accepts()

    is_ok(format, 'html', 'default representation')

with subtest('app'):
    c = controller()
    secret = c.helpers.app().secrets[0]
    is_ok(secret, 'works', 'application')

with subtest('b'):
    c = controller()
    slug = c.b(b'Joel is a slug').slugify()
    isa_ok(c.b(b'test'), Pyjo.String.Bytes.object, 'bytes')
    is_ok(slug, b'joel-is-a-slug', 'slug')

with subtest('c'):
    c = controller()
    string = c.c('a', 'b', 'c').shuffle().join()
    isa_ok(c.c('a'), Pyjo.Collection.object, 'collection')
    is_ok(len(string), 3, 'joined')

with subtest('config'):
    c = controller()
    c.app.config(something='value')
    something = c.config('something')
    is_ok(something, 'value', 'config')

with subtest('content'):
    c = controller()
    c.content('foo', lambda: 'test')
    c.content('bar', 'Hello World!')
    foo = c.content('foo')
    bar = c.content('bar')
    content = c.content()
    is_deeply_ok([foo, bar, content], ['test', 'Hello World!', ''], 'named buffers')

with subtest('content_for'):
    c = controller()
    c.content_for('foo', lambda: 'test')
    foo = c.content_for('foo')
    is_ok(foo, 'test', 'content')

    c.content_for('message', 'Hello ')
    c.content_for('message', 'world!')
    message = c.content('message')
    is_ok(message, 'Hello world!', 'appended')

with subtest('content_with'):
    c = controller()
    c.content_with('foo', lambda: 'test')
    foo = c.content_with('foo')
    is_ok(foo, 'test', 'content')

    c.content('message', 'world!')
    c.content_with('message', lambda: f'Hello {c.content("message")}')
    message = c.content('message')
    is_ok(message, 'Hello world!', 'replaced')

with subtest('csrf_token'):
    c = controller()
    token = c.csrf_token()
    like_ok(token, r'^[0-9a-f]{80}$', 'masked token')
    isnt_ok(c.csrf_token(), token, 'masked again')

with subtest('current_route'):
    c = controller()
    c.app.routes.get('/login').set(name='login')
    c.req.url.parse('/login')
    c.app.routes.match(c)
    if c.current_route('login'):
        pass
    name = c.current_route()
    is_ok(name, 'login', 'name')
    ok(c.current_route('login'), 'check')

with subtest('dumper'):
    c = controller()
    dump = c.dumper({'some': 'data'})
    is_ok(dump, "{'some': 'data'}\n", 'dump')

with subtest('exception_format'):
    c = controller()
    format = c.exception_format()
    is_ok(format, 'html', 'default')
    c = c.exception_format('txt')
    is_ok(c.exception_format(), 'txt', 'set')

with subtest('extends'):
    c = controller()
    c.extends('blue')
    c.extends('blue', title='Blue!')
    is_deeply_ok([c.stash('extends'), c.stash('title')], ['blue', 'Blue!'], 'stash')

with subtest('flash'):
    c = controller()
    c.app.routes.get('/user/:id').set(name='show_user')
    foo = c.flash('foo')
    is_ok(foo, None, 'no value')
    c = c.flash({'foo': 'bar'})
    c = c.flash(foo='bar')

    # Show message after redirect
    c.flash(message='User created successfully!')
    c.redirect_to('show_user', id=23)

    is_deeply_ok(c.session('new_flash'), {'foo': 'bar', 'message': 'User created successfully!'}, 'new flash')
    is_ok(c.res.headers.location, '/user/23', 'redirect')

with subtest('inactivity_timeout'):
    c = controller()
    c = c.inactivity_timeout(3600)
    # The longer version needs a connection, so it is not run
    ok(c, 'no connection')

with subtest('include'):
    c = controller()
    menubar = c.include('menubar')
    menubar = c.include('menubar', format='txt')
    is_ok(menubar, None, 'no template')

with subtest('layout'):
    c = controller()
    c.layout('green')
    c.layout('green', title='Green!')
    is_deeply_ok([c.layout(), c.title()], ['green', 'Green!'], 'stash')

with subtest('log'):
    c = controller()
    with c.app.log.capture('debug') as messages:
        log = c.log()

        # Log message with context
        c.log().debug('This is a log message with request id')
    like_ok(str(messages), rf'\[{re.escape(c.req.request_id)}\] This is a log message', 'context')
    # The example of a model needs one, so it is not run

with subtest('param'):
    c = controller()
    c.param('foo', 'bar')
    foo = c.helpers.param('foo')
    is_ok(foo, 'bar', 'alias')

with subtest('redirect_to'):
    c = controller()
    c.app.routes.get('/named/:foo').set(name='named')
    c = c.redirect_to('named', foo='bar')
    is_ok(c.res.code, 302, 'status')
    is_ok(c.res.headers.location, '/named/bar', 'location')
    for target in ([{'foo': 'bar'}], ['/index.html'], ['http://example.com/index.html']):
        c = controller()
        c.app.routes.get('/named/:foo').set(name='named')
        c.redirect_to('named', *target) if isinstance(target[0], dict) else c.redirect_to(*target)

    c = controller()
    c.app.routes.get('/some').set(name='some_route')

    # Moved Permanently
    c.res.code = 301
    c.redirect_to('some_route')

    is_ok(c.res.code, 301, 'status kept')

    c = controller()
    c.app.routes.get('/some').set(name='some_route')

    # Temporary Redirect
    c.res.code = 307
    c.redirect_to('some_route')

    is_ok(c.res.code, 307, 'status kept')

with subtest('reply.exception'):
    c = controller()
    c.exception_format('txt')
    c.reply.exception('Oops!')
    is_ok(c.res.code, 500, 'exception')
    c = controller()
    c.exception_format('json')
    c.reply.exception(Pyjo.Exception.new('Oops!'))
    is_deeply_ok(c.res.json(), {'error': 'Oops!\n'}, 'JSON of the exception, which ends with a newline')

with subtest('reply.html_exception'):
    c = controller()
    c.reply.html_exception('Oops!')
    c.reply.html_exception(Pyjo.Exception.new())
    isa_ok(c.stash('exception'), Pyjo.Exception.object, 'exception in the stash')
    ok('snapshot' in c.stash(), 'snapshot')
    # TODO: the rendered exception page, when Pyjoyment.Plugin.EPRenderer is ported

with subtest('reply.html_not_found'):
    c = controller()
    c.reply.html_not_found()
    ok('snapshot' in c.stash(), 'snapshot')
    # TODO: the rendered not found page, when Pyjoyment.Plugin.EPRenderer is ported

with subtest('reply.json_exception'):
    c = controller()
    c.reply.json_exception('Oops!')
    is_deeply_ok([c.res.code, c.res.json()], [500, {'error': 'Oops!'}], 'response')
    c = controller()
    c.reply.json_exception(Pyjo.Exception.new())

with subtest('reply.json_not_found'):
    c = controller()
    c.reply.json_not_found()
    is_deeply_ok([c.res.code, c.res.json()], [404, {'error': 'Not Found'}], 'response')

with subtest('reply.not_found'):
    c = controller()
    c.exception_format('txt')
    c.reply.not_found()
    is_ok(c.res.code, 404, 'not found')

with subtest('reply.txt_exception'):
    c = controller()
    c.reply.txt_exception('Oops!')
    is_deeply_ok([c.res.code, c.res.body], [500, b'Oops!'], 'response')
    c = controller()
    c.reply.txt_exception(Pyjo.Exception.new())

with subtest('reply.txt_not_found'):
    c = controller()
    c.reply.txt_not_found()
    is_deeply_ok([c.res.code, c.res.body], [404, b'Not Found'], 'response')

with subtest('respond_to'):
    c = controller()
    c.req.headers.accept = 'application/json'
    c = c.respond_to(json={'json': {'message': 'Welcome!'}}, html={'template': 'welcome'}, any=lambda c: ...)
    is_deeply_ok(c.res.json(), {'message': 'Welcome!'}, 'JSON')

    c = controller()
    c.req.headers.accept = 'text/plain'

    # Everything else than "json" and "xml" gets a 204 response
    c.respond_to(
        json=lambda c: c.render(json={'just': 'works'}),
        xml={'text': '<just>works</just>'},
        any={'data': b'', 'status': 204},
    )

    is_ok(c.res.code, 204, 'everything else')

with subtest('session'):
    c = controller()
    c.session(foo='bar')
    foo = c.helpers.session('foo')
    is_ok(foo, 'bar', 'alias')

with subtest('stash'):
    c = controller()
    foo = c.helpers.stash('foo')
    c.helpers.stash(foo='bar')

    name = c.helpers.stash('name') or 'Somebody'

    is_deeply_ok([c.stash('foo'), name], ['bar', 'Somebody'], 'alias')

with subtest('timing.begin'):
    c = controller()
    c.timing.begin('foo')
    ok(c.timing.elapsed('foo') is not None, 'timestamp')

with subtest('timing.elapsed'):
    c = controller()
    elapsed = c.timing.elapsed('foo')
    is_ok(elapsed, None, 'no timestamp')

    # Log timing information
    c.timing.begin('database_stuff')
    ...
    elapsed = c.timing.elapsed('database_stuff')
    c.app.log.debug(f'Database stuff took {elapsed} seconds')

    ok(elapsed >= 0, 'elapsed')

with subtest('timing.rps'):
    c = controller()
    rps = c.timing.rps(0.001)
    is_ok(rps, '1000.000', 'requests per second')
    is_ok(c.timing.rps(0), None, 'too low')

    # Log more timing information
    c.timing.begin('web_stuff')
    ...
    elapsed = c.timing.elapsed('web_stuff') or 0.001
    rps = c.timing.rps(elapsed)
    c.app.log.debug(f'Web stuff took {elapsed} seconds ({rps} per second)')

with subtest('timing.server_timing'):
    c = controller()
    c.timing.server_timing('metric')
    c.timing.server_timing('metric', 'Some Description')
    c.timing.server_timing('metric', 'Some Description', 0.001)
    is_ok(
        c.res.headers.header('Server-Timing'),
        'metric, metric;desc="Some Description", metric;desc="Some Description";dur=0.001',
        'header',
    )

    c = controller()

    # "Server-Timing: miss"
    c.timing.server_timing('miss')

    is_ok(c.res.headers.header('Server-Timing'), 'miss', 'miss')

    c = controller()

    # "Server-Timing: dc;desc=atl"
    c.timing.server_timing('dc', 'atl')

    is_ok(c.res.headers.header('Server-Timing'), 'dc;desc="atl"', 'description')

    c = controller()

    # "Server-Timing: db;desc=Database;dur=0.0001"
    c.timing.begin('database_stuff')
    ...
    elapsed = c.timing.elapsed('database_stuff')
    c.timing.server_timing('db', 'Database', elapsed)

    like_ok(c.res.headers.header('Server-Timing'), r'^db;desc="Database";dur=', 'duration')

    c = controller()

    # "Server-Timing: miss, dc;desc=atl"
    c.timing.server_timing('miss')
    c.timing.server_timing('dc', 'atl')

    is_ok(c.res.headers.header('Server-Timing'), 'miss, dc;desc="atl"', 'two metrics')

with subtest('title'):
    c = controller()
    title = c.title()
    is_ok(title, None, 'no title')
    c.title('Welcome!')
    c.title('Welcome!', foo='bar')
    is_deeply_ok([c.title(), c.stash('foo')], ['Welcome!', 'bar'], 'stash')

with subtest('ua'):
    c = controller()
    is_ok(c.ua(), c.app.ua, 'alias')
    # The example needs the network, so it is not run

with subtest('url_for'):
    c = controller()
    c.app.routes.get('/named/:foo/:baz').set(name='named')
    url = c.helpers.url_for('named', foo='bar', baz='yada')
    is_ok(url.to_str(), '/named/bar/yada', 'alias')

    url = c.helpers.url_for('/index.html').set(query={'foo': 'bar'})
    is_ok(url.to_str(), '/index.html?foo=bar', 'query')

with subtest('url_with'):
    c = controller()
    c.app.routes.get('/named/:foo/:baz').set(name='named')
    c.req.url.parse('/?page=1')
    url = c.url_with('named', foo='bar', baz='yada')
    is_ok(url.to_str(), '/named/bar/yada?page=1', 'inherited query')

    url = c.url_with().set(query={'page': 2})
    is_ok(url.query.param('page'), '2', 'replaced')

with subtest('register'):
    plugin = Pyjoyment.new().plugins.load_plugin('DefaultHelpers')
    app = Pyjoyment.new()
    plugin.register(app)
    ok(app.renderer.get_helper('reply.not_found'), 'registered')

done_testing()
