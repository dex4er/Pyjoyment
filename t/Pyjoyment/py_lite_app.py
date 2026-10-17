"""
__DATA__
@@ layouts/default.html.ep
<body><%= content() %></body>
"""

import Pyjo.String.HTML
import Pyjo.Test.Pyjo

from Pyjo.String.Template import t
from Pyjo.Test import *
from Pyjoyment.Lite import app, get


# The templates of the tests are of t() on any Python, as a t-string of Python 3.14 cannot be compiled on an older one;
# py_native_lite_app.py has them

# The test is "test", as t is the function of the templates


@get('/inline')
def inline(c):
    name = c.param('name')
    c.render(inline=t('<p>Hello {name}!</p>', name=name))


@get('/stash', {'name': 'stash'})
def stash(c):
    c.render(inline=t('<p>{name}</p>', name=c.stash('name')))


@get('/markup')
def markup(c):
    c.render(inline=t('<p>{link}</p>', link=c.link_to('Home', '/')))


@get('/nested')
def nested(c):
    tags = ['<b>', '<i>']
    c.render(inline=t('<ul>{items}</ul>', items=[t('<li>{tag}</li>', tag=tag) for tag in tags]))


@get('/handler')
def handler(c):
    c.render(inline=t('<p>{x}</p>', x='<handler>'), handler='py')


@get('/format')
def format(c):
    c.render(inline=t('{x}', x='a & b'), format='txt')


@get('/ep')
def ep(c):
    c.render(inline='<%= 1 + 1 %>')


@get('/layout')
def layout(c):
    c.render(inline=t('<p>{x}</p>', x='inline'), layout='default')


@get('/string')
def string(c):
    output = c.render_to_string(inline=t('<p>{x}</p>', x='<string>'))
    c.render(text=f'{type(output).__name__}: {output}')


test = Pyjo.Test.Pyjo.new()

with subtest('Inline template string'):
    (
        test.get_ok('/inline?name=<script>')
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .content_is('<p>Hello &lt;script&gt;!</p>')
    )

with subtest('Value of the stash'):
    test.get_ok('/stash').status_is(200).content_is('<p>stash</p>')

with subtest('Markup of a helper'):
    test.get_ok('/markup').status_is(200).content_is('<p><a href="/">Home</a></p>')

with subtest('Nested templates'):
    test.get_ok('/nested').status_is(200).content_is('<ul><li>&lt;b&gt;</li><li>&lt;i&gt;</li></ul>')

with subtest('Explicit handler'):
    test.get_ok('/handler').status_is(200).content_is('<p>&lt;handler&gt;</p>')

with subtest('Another format'):
    test.get_ok('/format').status_is(200).content_type_is('text/plain;charset=UTF-8').content_is('a &amp; b')

with subtest('Inline string is still EP'):
    test.get_ok('/ep').status_is(200).content_is('2\n')

with subtest('No layout for an inline template, as for EP'):
    test.get_ok('/layout').status_is(200).content_is('<p>inline</p>')

with subtest('Rendered to a string'):
    test.get_ok('/string').status_is(200).content_is('Pyjo_String_HTML: <p>&lt;string&gt;</p>')

with subtest('Handler'):
    ok('py' in app.renderer.handlers, 'handler py')
    is_ok(app.renderer.default_handler, 'ep', 'default handler')
    c = app.build_controller()
    isa_ok(c.render_to_string(inline=t('<p>{x}</p>', x='<b>')), Pyjo.String.HTML.object, 'markup')

done_testing()
