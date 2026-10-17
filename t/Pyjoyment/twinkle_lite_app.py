r"""
__DATA__
@@ index.foo.twinkle
. c.layout('twinkle')
Hello *** name **!\
*** prepended ** *** __name__ **\

@@ layouts/twinkle.foo.ep
test<%= content() %>123\

@@ advanced.foo.twinkle
.** "<escape me>"
. numbers = [1, 2, 3, 4]
 ** for i in numbers { ***
 *** i ***
 ** } ***
 ** foo = (+*** 23 **-)();*** *** foo ***

@@ exception.foo.ep
foo exception!

@@ not_found.foo.ep
foo not found!
"""

import Pyjo.Test.Pyjo

from Pyjo.Test import *
from Pyjoyment.Lite import app, get, plugin

import re


# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# Not in Mojolicious: the templates of the DATA section are in the docstring, as the requests come before the end of
# the script

# Custom format
app.renderer.default_format = 'foo'

# Twinkle template syntax
twinkle = {
    'append': "self.res.headers.header('X-Append', prepended)",
    'auto_escape': False,
    'capture_end': '-',
    'capture_start': '+',
    'escape': lambda string: re.sub(r'<', '&LT;', str(string)),
    'escape_mark': '*',
    'expression_mark': '*',
    'line_start': '.',
    'namespace': 'TwinkleSandBoxTest',
    'prepend': "prepended = self.config('foo')",
    'tag_end': '**',
    'tag_start': '**',
    'trim_mark': '*',
}

# Renderer
plugin('EPRenderer', name='twinkle', template=twinkle)

with subtest('Configuration'):
    app.defaults(foo_test=23)
    config = plugin(
        'JSONConfig',
        default={'foo': 'bar'},
        ext='conf',
        template={**twinkle, 'append': 'app.defaults(foo_test=24)', 'prepend': "foo = app.defaults('foo_test')"},
    )
    is_ok(config['foo'], 'bar', 'right value')
    is_ok(config['test'], 23, 'right value')
    is_ok(app.defaults('foo_test'), 24, 'right value')

get('/', {'name': '<sebastian>'}, 'index')

get('/advanced', 'advanced')


@get('/rest', {'format': None}, format=['html'])
def rest(c):
    c.respond_to(foo={'text': 'foo works!'}, html={'text': 'html works!'}).res.headers.header('X-Rest', 1)


@get('/dead')
def dead(c):
    raise Exception('Died')


t = Pyjo.Test.Pyjo.new()

with subtest('Basic template with "twinkle" syntax and "ep" layout'):
    (
        t.get_ok('/')
        .status_is(200)
        .header_is('X-Append', 'bar')
        .content_like(r'testHello <sebastian>!bar TwinkleSandBoxTest123')
    )

with subtest('Advanced template with "twinkle" syntax'):
    t.get_ok('/advanced').status_is(200).header_is('X-Append', 'bar').content_is('&LT;escape me>\n123423')

with subtest('REST request for "foo" format'):
    t.get_ok('/rest').status_is(200).header_is('X-Rest', '1').content_is('foo works!')

with subtest('REST request for "html" format'):
    t.get_ok('/rest.html').status_is(200).header_is('X-Rest', '1').content_is('html works!')

with subtest('Exception template with custom format'):
    t.get_ok('/dead').status_is(500).content_is('foo exception!\n')

done_testing()
