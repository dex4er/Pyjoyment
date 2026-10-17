import Pyjo.Asset.File
import Pyjo.Asset.Memory
import Pyjo.Collection
import Pyjo.Exception
import Pyjo.IOLoop
import Pyjo.Promise
import Pyjo.Server.Daemon
import Pyjo.String.Bytes
import Pyjo.Test.Pyjo
import Pyjo.Transaction.HTTP
import Pyjo.URL
import Pyjo.UserAgent.Transactor
import Pyjoyment

from Pyjo.File import tempdir
from Pyjo.Test import *

import re
import textwrap


# The applications are kept, as a controller refers to its application weakly
apps = []


def controller():
    app = Pyjoyment.new(secrets=['works'])
    app.log.level = 'fatal'
    apps.append(app)
    return app.build_controller()


def render(c, template):
    # The documented template, inline
    return str(c.render_to_string(inline=textwrap.dedent(template)))


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
    is_ok(render(c, '%= app().secrets[0]'), 'works\n', 'application')

with subtest('b'):
    c = controller()
    is_ok(render(c, "%= b(b'Joel is a slug').slugify()"), 'joel-is-a-slug\n', 'slug')
    isa_ok(c.b(b'test'), Pyjo.String.Bytes.object, 'bytes')

with subtest('c'):
    c = controller()
    like_ok(render(c, "%= c.c('a', 'b', 'c').shuffle().join()"), r'^[abc]{3}\n$', 'joined')
    isa_ok(c.c('a'), Pyjo.Collection.object, 'collection')

with subtest('config'):
    c = controller()
    c.app.config(something='value')
    is_ok(render(c, "%= config('something')"), 'value\n', 'config')

with subtest('content'):
    c = controller()
    output = render(
        c,
        """\
        %= content('foo', begin
          test
        % end)
        %= content('bar', 'Hello World!')
        %= content('foo')
        %= content('bar')
        %= content()
        """,
    )
    is_ok(output, '\n  test\nHello World!\n\n  test\n\nHello World!\n\n', 'named buffers')

with subtest('content_for'):
    c = controller()
    output = render(
        c,
        """\
        % content_for('foo', begin
          test
        % end)
        %= content_for('foo')
        """,
    )
    is_ok(output, '  test\n\n', 'content')

    c = controller()
    output = render(
        c,
        """\
        % content_for('message', begin
          Hello
        % end)
        % content_for('message', begin
          world!
        % end)
        %= content('message')
        """,
    )
    is_ok(output, '  Hello\n  world!\n\n', 'appended')

with subtest('content_with'):
    c = controller()
    output = render(
        c,
        """\
        % content_with('foo', begin
          test
        % end)
        %= content_with('foo')
        """,
    )
    is_ok(output, '  test\n\n', 'content')

    c = controller()
    output = render(
        c,
        """\
        % content('message', begin
          world!
        % end)
        % content_with('message', begin
          Hello <%= content('message') %>
        % end)
        %= content('message')
        """,
    )
    is_ok(output, '  Hello   world!\n\n\n', 'replaced')

with subtest('csrf_token'):
    c = controller()
    token = render(c, '%= csrf_token()')
    like_ok(token, r'^[0-9a-f]{80}\n$', 'masked token')
    isnt_ok(render(c, '%= csrf_token()'), token, 'masked again')

with subtest('current_route'):
    c = controller()
    c.app.routes.get('/login').set(name='login')
    c.req.url.parse('/login')
    c.app.routes.match(c)
    output = render(
        c,
        """\
        % if current_route('login'):
          Welcome to Pyjoyment!
        % end
        %= current_route()
        """,
    )
    is_ok(output, '  Welcome to Pyjoyment!\nlogin\n', 'check and name')

with subtest('dumper'):
    c = controller()
    is_ok(render(c, "%= dumper({'some': 'data'})"), '{&#39;some&#39;: &#39;data&#39;}\n\n', 'dump, escaped')

with subtest('exception_format'):
    c = controller()
    format = c.exception_format()
    is_ok(format, 'html', 'default')
    c = c.exception_format('txt')
    is_ok(c.exception_format(), 'txt', 'set')

with subtest('extends'):
    c = controller()
    output = render(
        c,
        """\
        % extends('blue')
        % extends('blue', title='Blue!')
        %= stash('extends')
        """,
    )
    is_ok(output, 'blue\n', 'stash')
    is_ok(c.stash('title'), 'Blue!', 'merged into the stash')

with subtest('flash'):
    c = controller()
    c.app.routes.get('/user/:id').set(name='show_user')
    foo = c.flash('foo')
    is_ok(foo, None, 'no value')
    c = c.flash({'foo': 'bar'})
    c = c.flash(foo='bar')
    is_ok(render(controller(), "%= flash('foo')"), '\n', 'no value in a template')

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
    tmp = tempdir()
    tmp.child('menubar.html.ep').spew(b'<a href="/">Home</a>\n')
    tmp.child('menubar.txt.ep').spew(b'Home\n')
    c.app.renderer.paths.append(str(tmp))
    is_ok(render(c, "%= include('menubar')"), '<a href="/">Home</a>\n\n', 'not escaped')
    is_ok(render(c, "%= include('menubar', format='txt')"), 'Home\n\n', 'format')

with subtest('is_fresh'):
    c = controller()
    boolean = c.is_fresh()
    ok(not boolean, 'stale')
    boolean = c.is_fresh(etag='abc')
    boolean = c.is_fresh(etag='W/"def"')
    boolean = c.is_fresh(last_modified=1424985708)
    ok(not boolean, 'stale')

    # Add ETag/Last-Modified headers and check freshness before rendering
    c = controller()
    c.req.headers.if_none_match = '"abc"'
    if c.is_fresh(etag='abc', last_modified=1424985708):
        c.rendered(304)
    else:
        c.render(text='I ♥ Pyjoyment!')
    is_ok(c.res.code, 304, 'fresh')

with subtest('layout'):
    c = controller()
    output = render(
        c,
        """\
        % layout('green')
        % layout('green', title='Green!')
        %= stash('layout')
        """,
    )
    is_ok(output, 'green\n', 'stash')
    is_ok(c.stash('title'), 'Green!', 'merged into the stash')

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
    is_ok(render(c, "%= param('foo')"), 'bar\n', 'alias')

# The hosts of the examples of the proxy helpers, as a test does not request remote hosts: a local server for the one
# that responds, and a server that closes every connection at once for the one that fails, as a port that nothing
# listens on could be taken by a server of another test before the request
backend = Pyjoyment.new()
backend.log.level = 'fatal'
backend.routes.any('/', lambda c: c.render(text=f'backend {c.req.method}'))
daemon = Pyjo.Server.Daemon.new(listen=['http://127.0.0.1'], silent=True, app=backend)
example = f'http://127.0.0.1:{daemon.start().ports()[0]}'
broken = Pyjo.IOLoop.server(lambda loop, stream, id: stream.close(), address='127.0.0.1')
nowhere = f'http://127.0.0.1:{Pyjo.IOLoop.acceptor(broken).port}'


def proxy(action):
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    apps.append(app)
    app.routes.any('/', action)
    return Pyjo.Test.Pyjo.new(app)


with subtest('proxy.get_p'):

    def action(c):
        promise = c.proxy.get_p(example, {'Accept': '*/*'})
        isa_ok(promise, Pyjo.Promise.object, 'promise')

    proxy(action).get_ok('/').status_is(200).content_is('backend GET')

    def action(c):
        # Forward with exception handling
        @c.proxy.get_p(nowhere).catch
        def catch(err):
            c.log().debug(f'Proxy error: {err}')
            c.render(text='Something went wrong!', status=400)

    proxy(action).get_ok('/').status_is(400).content_is('Something went wrong!')

with subtest('proxy.post_p'):

    def action(c):
        promise = c.proxy.post_p(example, {'Accept': '*/*'})
        isa_ok(promise, Pyjo.Promise.object, 'promise')

    proxy(action).get_ok('/').status_is(200).content_is('backend POST')

    def action(c):
        # Forward with exception handling
        @c.proxy.post_p(nowhere, form={'test': 'pass'}).catch
        def catch(err):
            c.log().debug(f'Proxy error: {err}')
            c.render(text='Something went wrong!', status=400)

    proxy(action).get_ok('/').status_is(400).content_is('Something went wrong!')

with subtest('proxy.start_p'):

    def action(c):
        # A new transaction, with the URL of the local server
        tx = Pyjo.Transaction.HTTP.new()
        tx.req.url = Pyjo.URL.new(example)
        promise = c.proxy.start_p(tx)
        isa_ok(promise, Pyjo.Promise.object, 'promise')

    proxy(action).get_ok('/').status_is(200).content_is('backend GET')

    def action(c):
        # Forward with exception handling
        tx = c.ua().build_tx('GET', nowhere)

        @c.proxy.start_p(tx).catch
        def catch(err):
            c.log().debug(f'Proxy error: {err}')
            c.render(text='Something went wrong!', status=400)

    proxy(action).get_ok('/').status_is(400).content_is('Something went wrong!')

    def action(c):
        # Forward with custom request and response headers
        headers = c.req.headers.clone().dehop()
        headers.header('X-Proxy', 'Pyjo')
        tx = c.ua().build_tx('GET', example, headers.to_dict())
        c.proxy.start_p(tx)
        tx.res.content.once('body', lambda content: c.res.headers.header('X-Proxy', 'Pyjo'))

    proxy(action).get_ok('/').status_is(200).header_is('X-Proxy', 'Pyjo').content_is('backend GET')

daemon.stop()
Pyjo.IOLoop.remove(broken)

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

with subtest('reply.asset'):
    c = controller()
    c.reply.asset(Pyjo.Asset.File.new())
    is_ok(c.res.code, 200, 'empty file')

    # Serve asset with custom modification time
    c = controller()
    asset = Pyjo.Asset.Memory.new()
    asset.add_chunk(b'Hello World!').mtime = 784111777
    c.res.headers.content_type = 'text/plain'
    c.reply.asset(asset)
    is_ok(c.res.headers.last_modified, 'Sun, 06 Nov 1994 08:49:37 GMT', 'right "Last-Modified" value')

    # Serve static file if it exists
    c = controller()
    tmp = tempdir()
    tmp.child('images').make_path().child('logo.png').spew(b'PNG')
    c.app.static.paths.append(str(tmp))
    if asset := c.app.static.file('images/logo.png'):
        c.res.headers.content_type = 'image/png'
        c.reply.asset(asset)
    is_ok(c.res.content.asset.slurp(), b'PNG', 'served')

with subtest('reply.exception'):
    c = controller()
    c.exception_format('txt')
    c.reply.exception('Oops!')
    is_ok(c.res.code, 500, 'exception')
    c = controller()
    c.exception_format('json')
    c.reply.exception(Pyjo.Exception.new('Oops!'))
    is_deeply_ok(c.res.json(), {'error': 'Oops!\n'}, 'JSON of the exception, which ends with a newline')

with subtest('reply.file'):
    tmp = tempdir()
    tmp.child('passwd').spew(b'root')
    c = controller()
    c.reply.file(tmp.child('passwd').to_str())
    is_ok(c.res.content.asset.slurp(), b'root', 'served')

    # Longer version
    c = controller()
    c.reply.asset(Pyjo.Asset.File.new(path=tmp.child('passwd').to_str()))
    is_ok(c.res.content.asset.slurp(), b'root', 'served')

    # Serve file from an absolute path with a custom content type
    tmp.child('foo.txt').spew(b'foo')
    c = controller()
    c.res.headers.content_type = 'application/myapp'
    c.reply.file(tmp.child('foo.txt').to_str())
    is_ok(c.res.headers.content_type, 'application/myapp', 'custom content type')

    # Serve file from a secret application directory
    c = controller()
    c.app.home = tmp
    tmp.child('secret').make_path().child('file.txt').spew(b'secret')
    c.reply.file(c.app.home.child('secret', 'file.txt'))
    is_ok(c.res.content.asset.slurp(), b'secret', 'served')

with subtest('reply.html_exception'):
    c = controller()
    c.reply.html_exception('Oops!')
    c = controller()
    c.reply.html_exception(Pyjo.Exception.new())
    isa_ok(c.stash('exception'), Pyjo.Exception.object, 'exception in the stash')
    ok('snapshot' in c.stash(), 'snapshot')
    is_ok(c.res.code, 500, 'status')
    like_ok(c.res.text, r'<title>Server Error', 'exception page')

with subtest('reply.html_not_found'):
    c = controller()
    c.reply.html_not_found()
    ok('snapshot' in c.stash(), 'snapshot')
    is_ok(c.res.code, 404, 'status')
    like_ok(c.res.text, r'<title>Page Not Found', 'not found page')

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

with subtest('reply.static'):
    c = controller()
    c.reply.static('pyjo/logo.png')
    is_ok(c.res.code, 200, 'served')
    throws_ok(
        lambda: c.reply.static('../lib/MyApp.py'),
        re.compile(r'Static file "\.\./lib/MyApp\.py" not found'),
        'not found',
    )

    # Serve file from a relative path with a custom content type
    c = controller()
    tmp = tempdir()
    tmp.child('foo.txt').spew(b'foo')
    c.app.static.paths.append(str(tmp))
    c.res.headers.content_type = 'application/myapp'
    c.reply.static('foo.txt')
    is_ok(c.res.headers.content_type, 'application/myapp', 'custom content type')

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
    is_ok(render(c, "%= session('foo')"), 'bar\n', 'alias')

with subtest('stash'):
    c = controller()
    output = render(
        c,
        """\
        %= stash('foo')
        % stash(foo='bar')
        """,
    )
    is_ok(output, '\n', 'no value')
    is_ok(c.stash('foo'), 'bar', 'alias')

    is_ok(render(c, "%= stash('name') or 'Somebody'"), 'Somebody\n', 'default')

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
    output = render(
        c,
        """\
        %= title()
        % title('Welcome!')
        % title('Welcome!', foo='bar')
        """,
    )
    is_ok(output, '\n', 'no title')
    is_deeply_ok([c.title(), c.stash('foo')], ['Welcome!', 'bar'], 'stash')

with subtest('ua'):
    c = controller()
    is_ok(c.ua(), c.app.ua, 'alias')
    # The example needs the network, so it is not run

with subtest('url_for'):
    c = controller()
    c.app.routes.get('/named/:foo/:baz').set(name='named')
    is_ok(render(c, "%= url_for('named', foo='bar', baz='yada')"), '/named/bar/yada\n', 'alias')

    is_ok(render(c, "%= url_for('/index.html').set(query={'foo': 'bar'})"), '/index.html?foo=bar\n', 'query')

with subtest('url_for_asset'):
    c = controller()
    is_ok(render(c, "%= url_for_asset('/app.js')"), '/assets/app.js\n', 'alias')

with subtest('url_for_file'):
    c = controller()
    is_ok(render(c, "%= url_for_file('/index.html')"), '/index.html\n', 'alias')

with subtest('url_with'):
    c = controller()
    c.app.routes.get('/named/:foo/:baz').set(name='named')
    c.req.url.parse('/?page=1')
    is_ok(render(c, "%= url_with('named', foo='bar', baz='yada')"), '/named/bar/yada?page=1\n', 'inherited query')

    is_ok(render(c, "%= url_with().set(query={'page': 2})"), '?page=2\n', 'replaced')

with subtest('validation'):
    c = controller()
    c.req.url.parse('/?title=+Hello+')
    v = c.validation()

    # Validate GET/POST parameter
    v = c.validation()
    v.required('title', 'trim').size(3, 50)
    title = v.param('title')
    is_ok(title, 'Hello', 'parameter')

    # Validate file upload
    tx = Pyjo.UserAgent.Transactor.new().tx('POST', '/', form={'tarball': {'content': 'data', 'filename': 'a.tar'}})
    c = controller().app.build_controller(tx)
    v = c.validation()
    v.required('tarball').upload().size(1, 1048576)
    tarball = v.param('tarball')
    is_ok(tarball.filename, 'a.tar', 'upload')

with subtest('register'):
    plugin = Pyjoyment.new().plugins.load_plugin('DefaultHelpers')
    app = Pyjoyment.new()
    plugin.register(app)
    ok(app.renderer.get_helper('reply.not_found'), 'registered')

done_testing()
