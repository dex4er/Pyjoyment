import Pyjo.Test.Pyjo
import Pyjoyment

from Pyjo.Test import *
from Pyjoyment.Lite import app, get, plugin

import re


# Not in Mojolicious: applications mounted by a regular expression that matches the whole path, whose group path is the
# rest of the path for the application, and whose other named groups are captures


def wsgi(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [f'WSGI at {environ["SCRIPT_NAME"]!r} for {environ["PATH_INFO"]!r}'.encode()]


class MyApp(Pyjoyment.object):
    def startup(self):
        self.routes.get('/foo').to(cb=lambda c: c.render(text='MyApp for /foo'))


# Silence
app.log.level = 'fatal'

get('/', lambda c: c.render(text='Hello from the main app!'))

plugin('Mount', {re.compile(r'/php(?P<path>/.*)?'): wsgi})
plugin('Mount', {re.compile(r'/info\.php'): wsgi})
plugin('Mount', {re.compile(r'/(?P<user>\w+)/blog(?P<path>/.*)?'): wsgi})
route = plugin('Mount', {re.compile(r'/myapp(?P<path>/.*)?'): MyApp.new()})

t = Pyjo.Test.Pyjo.new()

with subtest('Main application'):
    t.get_ok('/').status_is(200).content_is('Hello from the main app!')

with subtest('Whole path'):
    t.get_ok('/php').status_is(200).content_is("WSGI at '/php' for ''")
    t.get_ok('/php/').status_is(200).content_is("WSGI at '/php' for '/'")
    t.get_ok('/php/foo/bar').status_is(200).content_is("WSGI at '/php' for '/foo/bar'")

    # Not a prefix of the characters of the path, as a regular expression of PromQL matches the whole value
    t.get_ok('/phpx').status_is(404)
    t.get_ok('/php.css').status_is(404)
    t.get_ok('/x/php').status_is(404)

with subtest('One path'):
    t.get_ok('/info.php').status_is(200).content_is("WSGI at '/info.php' for ''")
    t.get_ok('/info.php/x').status_is(404)
    t.get_ok('/infoxphp').status_is(404)

with subtest('Captures'):
    t.get_ok('/sri/blog/posts').status_is(200).content_is("WSGI at '/sri/blog' for '/posts'")
    t.get_ok('/s-ri/blog').status_is(404)

with subtest('Application of Pyjoyment'):
    is_ok(route.pattern.unparsed, r'/myapp(?P<path>/.*)?', 'the regular expression')
    # Its routes match the rest of the path
    t.get_ok('/myapp/foo').status_is(200).content_is('MyApp for /foo')
    t.get_ok('/myapp/bar').status_is(404)
    t.get_ok('/myappx').status_is(404)

done_testing()
