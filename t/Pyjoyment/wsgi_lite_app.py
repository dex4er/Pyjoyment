import Pyjo.App.WSGI
import Pyjo.File
import Pyjo.Test.Pyjo
import Pyjoyment

from Pyjo.Test import *
from Pyjoyment.Lite import app, get, plugin

import re
import sys


# The modules of the applications are in a temporary directory, as a test writes nothing into t
tmp = Pyjo.File.tempdir()
tmp.child('wsgi_hello.py').spew(b"""\
def app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [f"Hello from {environ['SCRIPT_NAME']} and {environ['PATH_INFO']}!".encode()]


class handlers:
    @staticmethod
    def app(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [b'Hello from handlers!']
""")
sys.path.insert(0, tmp.to_str())


def hello(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [f'Hello from {environ["HTTP_HOST"]}{environ["SCRIPT_NAME"]}{environ["PATH_INFO"]}!'.encode()]


class MyApp(Pyjoyment.object):
    def startup(self):
        self.routes.get('/').to(cb=lambda c: c.render(text='Hello from MyApp!'))


async def asgi(scope, receive, send):
    pass


# Silence
app.log.level = 'fatal'

get('/', lambda c: c.render(text='Hello from the main app!'))

route = plugin('Mount', {'/object': hello})
embedded = route.pattern.defaults['app']
plugin('Mount', {'/module': 'wsgi_hello:app'})
plugin('Mount', {'/attribute': 'wsgi_hello:handlers.app'})
plugin('Mount', {'example.com/host': hello})
plugin('Mount', {'/wrapped': Pyjo.App.WSGI.new(app=hello, threads=1)})
plugin('Mount', {'/myapp': MyApp.new()})

t = Pyjo.Test.Pyjo.new()

with subtest('Main application'):
    t.get_ok('/').status_is(200).content_is('Hello from the main app!')

with subtest('WSGI application as an object'):
    ok(isinstance(embedded, Pyjo.App.WSGI.object), 'WSGI application')
    ok(embedded.app is hello, 'right application')
    ok(embedded.log is app.log, 'same log')
    t.get_ok('/object').status_is(200).content_like(r'^Hello from 127\.0\.0\.1:\d+/object!$')
    t.get_ok('/object/foo/bar').status_is(200).content_like(r'^Hello from 127\.0\.0\.1:\d+/object/foo/bar!$')

with subtest('WSGI application as the name of a module and its attribute'):
    t.get_ok('/module/foo').status_is(200).content_is('Hello from /module and /foo!')
    t.get_ok('/attribute').status_is(200).content_is('Hello from handlers!')

with subtest('WSGI application with host'):
    t.get_ok('/host/foo', {'Host': 'example.com'}).status_is(200).content_is('Hello from example.com/host/foo!')
    t.get_ok('/host/foo', {'Host': 'example.org'}).status_is(404)

with subtest('WSGI application in its adapter'):
    t.get_ok('/wrapped/foo').status_is(200).content_like(r'/wrapped/foo!$')

with subtest('Application object'):
    t.get_ok('/myapp').status_is(200).content_is('Hello from MyApp!')

with subtest('Errors'):
    throws_ok(
        lambda: plugin('Mount', {'/missing': 'wsgi_missing:app'}),
        re.compile(r'^Can\'t load application "wsgi_missing:app": No module named \'wsgi_missing\''),
        'missing module',
    )
    throws_ok(
        lambda: plugin('Mount', {'/missing': 'wsgi_hello:missing'}),
        re.compile(r'^Can\'t load application "wsgi_hello:missing": .*missing'),
        'missing attribute',
    )
    throws_ok(lambda: plugin('Mount', {'/asgi': asgi}), re.compile(r'^ASGI application .* is not supported'), 'ASGI')
    throws_ok(lambda: plugin('Mount', {'/number': 42}), re.compile(r'^"42" is not an application'), 'not callable')

done_testing()
