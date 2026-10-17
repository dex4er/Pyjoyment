import Pyjo.File
import Pyjo.Test.Pyjo
import Pyjoyment
import Pyjoyment.Plugin.Mount
import Pyjoyment.Routes.Route

from Pyjo.Test import *


# The applications of the examples are scripts in a temporary directory, as a test writes nothing into t
tmp = Pyjo.File.tempdir()
myapp = tmp.child('myapp.py').spew(b"""\
from Pyjoyment.Lite import app, get

get('/', lambda c: c.render(text=c.stash('message') or 'Hello from myapp!'))

app.start()
""")


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

with subtest('register'):
    app = application()
    route = Pyjoyment.Plugin.Mount.new().register(app, {'/foo': myapp.to_str()})
    ok(isinstance(route, Pyjoyment.Routes.Route.object), 'route')
    Pyjo.Test.Pyjo.new(app).get_ok('/foo').content_is('Hello from myapp!')

done_testing()
