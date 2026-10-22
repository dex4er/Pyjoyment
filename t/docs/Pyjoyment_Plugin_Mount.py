import Pyjo.App.CGI
import Pyjo.App.FastCGI
import Pyjo.App.Lambda
import Pyjo.File
import Pyjo.Server.Daemon
import Pyjo.Test.Pyjo
import Pyjoyment
import Pyjoyment.Plugin.Mount
import Pyjoyment.Routes.Route

from Pyjo.Test import *

import re
import sys


# The applications of the examples are scripts in a temporary directory, as a test writes nothing into t
tmp = Pyjo.File.tempdir()
myapp = tmp.child('myapp.py').spew(b"""\
from Pyjoyment.Lite import app, get

get('/', lambda c: c.render(text=c.stash('message') or 'Hello from myapp!'))

app.start()
""")

# The module of the WSGI application, in the temporary directory, which sys.path has
tmp.child('myflask.py').spew(b"""\
def app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b'Hello from myflask!']
""")

# The module of the ASGI application
tmp.child('mystarlette.py').spew(b"""\
async def app(scope, receive, send):
    await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/plain')]})
    await send({'type': 'http.response.body', 'body': b'Hello from mystarlette!'})
""")
sys.path.insert(0, tmp.to_str())


def flask_app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b'Hello from flask_app!']


async def starlette_app(scope, receive, send):
    await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/plain')]})
    await send({'type': 'http.response.body', 'body': b'Hello from starlette_app!'})


class MyApp(Pyjoyment.object):
    def startup(self):
        self.routes.get('/').to(cb=lambda c: c.render(text='Hello from MyApp!'))


def application():
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    return app


with subtest('Synopsis'):
    # Pyjoyment
    app = application()
    route = app.plugin('Mount', {'/prefix': myapp.to_str()})
    ok(isinstance(route, Pyjoyment.Routes.Route.object), 'route')
    Pyjo.Test.Pyjo.new(app).get_ok('/prefix').content_is('Hello from myapp!')

    # Adjust the generated route and mounted application
    app = application()
    example = app.plugin('Mount', {'/example': myapp.to_str()})
    example.to(message='It works great!')
    embedded = example.pattern.defaults['app']
    embedded.config(foo='bar')
    embedded.log = app.log
    is_ok(embedded.config('foo'), 'bar', 'config')
    ok(embedded.log is app.log, 'log')
    Pyjo.Test.Pyjo.new(app).get_ok('/example').content_is('It works great!')

    # Mount application with host
    app = application()
    app.plugin('Mount', {'example.com': myapp.to_str()})
    t = Pyjo.Test.Pyjo.new(app)
    t.get_ok('/', {'Host': 'example.com'}).status_is(200).content_is('Hello from myapp!')
    t.get_ok('/', {'Host': 'example.org'}).status_is(404)

    # Host and path
    app = application()
    app.plugin('Mount', {'example.com/myapp': myapp.to_str()})
    t = Pyjo.Test.Pyjo.new(app)
    t.get_ok('/myapp', {'Host': 'example.com'}).status_is(200).content_is('Hello from myapp!')
    t.get_ok('/', {'Host': 'example.com'}).status_is(404)

    # Or even hosts with wildcard subdomains
    app = application()
    app.plugin('Mount', {'*.example.com/myapp': myapp.to_str()})
    t = Pyjo.Test.Pyjo.new(app)
    t.get_ok('/myapp', {'Host': 'www.example.com'}).status_is(200).content_is('Hello from myapp!')
    t.get_ok('/myapp', {'Host': 'example.com'}).status_is(200).content_is('Hello from myapp!')
    t.get_ok('/myapp', {'Host': 'example.org'}).status_is(404)

    # Application object
    app = application()
    app.plugin('Mount', {'/prefix': MyApp.new()})
    Pyjo.Test.Pyjo.new(app).get_ok('/prefix').content_is('Hello from MyApp!')

    # WSGI application, as an object or as the name of its module and its
    # attribute
    app = application()
    app.plugin('Mount', {'/flask': flask_app})
    Pyjo.Test.Pyjo.new(app).get_ok('/flask').content_is('Hello from flask_app!')
    app = application()
    app.plugin('Mount', {'/flask': 'myflask:app'})
    Pyjo.Test.Pyjo.new(app).get_ok('/flask').content_is('Hello from myflask!')

    # ASGI application, as an object or as the name of its module and its
    # attribute
    app = application()
    app.plugin('Mount', {'/starlette': starlette_app})
    Pyjo.Test.Pyjo.new(app).get_ok('/starlette').content_is('Hello from starlette_app!')
    app = application()
    app.plugin('Mount', {'/starlette': 'mystarlette:app'})
    Pyjo.Test.Pyjo.new(app).get_ok('/starlette').content_is('Hello from mystarlette!')

    # FastCGI application, as PHP on php-fpm, by its location, which the FastCGI server of Pyjo answers here
    php = application()
    php.routes.get('/').to(cb=lambda c: c.render(text='Hello from FastCGI!'))
    daemon = Pyjo.Server.Daemon.new(app=php, listen=['fcgi://127.0.0.1'], silent=True).start()
    app = application()
    route = app.plugin('Mount', {'/php': f'fcgi://127.0.0.1:{daemon.ports()[0]}'})
    ok(isinstance(route.pattern.defaults['app'], Pyjo.App.FastCGI.object), 'FastCGI application')
    Pyjo.Test.Pyjo.new(app).get_ok('/php').content_is('Hello from FastCGI!')
    route = app.plugin('Mount', {'/php': 'fcgi+unix://%2Frun%2Fphp%2Ffpm.sock'})
    is_ok(route.pattern.defaults['app'].url, 'fcgi+unix://%2Frun%2Fphp%2Ffpm.sock', 'location')
    route = app.plugin('Mount', {'/blog': 'fcgi://127.0.0.1:9000?document_root=%2Fvar%2Fwww&script=index.php'})
    like_ok(route.pattern.defaults['app'].url, r'\?document_root=%2Fvar%2Fwww&script=index\.php$', 'with its query')
    daemon.close()

    # CGI application, as an object, as a string is the path of a script
    app = application()
    route = app.plugin('Mount', {'/cgi-bin': Pyjo.App.CGI.new(document_root='/usr/lib/cgi-bin')})
    ok(isinstance(route.pattern.defaults['app'], Pyjo.App.CGI.object), 'CGI application')
    is_ok(route.pattern.defaults['app'].document_root, '/usr/lib/cgi-bin', 'directory of the programs')

    # Event function of AWS Lambda, as an object, in a process of its own
    app = application()
    route = app.plugin('Mount', {'/function': Pyjo.App.Lambda.new(function='myfunction.handler')})
    ok(isinstance(route.pattern.defaults['app'], Pyjo.App.Lambda.object), 'Lambda function')
    is_ok(route.pattern.defaults['app'].function, 'myfunction.handler', 'handler of the function')

    # A regular expression of the whole path, whose group path is the rest of
    # the path for the application, and whose other named groups are captures
    app = application()
    app.plugin('Mount', {re.compile(r'/php(?P<path>/.*)?'): flask_app})
    app.plugin('Mount', {re.compile(r'/(?P<user>\w+)/blog(?P<path>/.*)?'): flask_app})
    t = Pyjo.Test.Pyjo.new(app)
    t.get_ok('/php/foo').status_is(200).content_is('Hello from flask_app!')
    t.get_ok('/phpx').status_is(404)
    t.get_ok('/sri/blog').status_is(200).content_is('Hello from flask_app!')

with subtest('register'):
    app = application()
    route = Pyjoyment.Plugin.Mount.new().register(app, {'/foo': myapp.to_str()})
    ok(isinstance(route, Pyjoyment.Routes.Route.object), 'route')
    Pyjo.Test.Pyjo.new(app).get_ok('/foo').content_is('Hello from myapp!')
    app = application()
    route = Pyjoyment.Plugin.Mount.new().register(app, {'/foo': 'myflask:app'})
    Pyjo.Test.Pyjo.new(app).get_ok('/foo').content_is('Hello from myflask!')

done_testing()
