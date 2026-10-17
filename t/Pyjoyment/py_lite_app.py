"""
__DATA__
@@ layouts/default.html.ep
<body><%= content() %></body>

@@ both.html.ep
EP

@@ include.html.ep
<ul><%= include('item', item='<ep>') %></ul>
"""

import Pyjo.File
import Pyjo.String.HTML
import Pyjo.Test.Pyjo

from Pyjo.String.Template import t
from Pyjo.Test import *
from Pyjoyment.Lite import app, get, template


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


@template('hello.html')
def hello(c, name):
    return t('<p>Hello {name}!</p>')


@template('defaults.html')
def defaults(c, name, greeting='Hello'):
    return t('<p>{greeting} {name}!</p>')


@template('all.html')
def all_(c, **stash):
    return t('<p>{names}</p>', names=', '.join(sorted(k for k in stash if k in ('a', 'b'))))


@template('layouted.html')
def layouted(c, name):
    c.layout('green')
    c.title('Green')
    return t('<p>{name}</p>')


@template('layouts/green.html')
def green(c, **stash):
    return t('<title>{title}</title><body>{content}</body>', title=c.title(), content=c.content())


@template('item.html')
def item(c, item):
    return t('<li>{item}</li>')


@template('items.html')
def items(c, items):
    return t('<ul>{list}</ul>', list=[c.include('item', item=item) for item in items])


@template('both.html')
def both(c):
    return t('py')


@template('text.txt')
def text(c, name):
    return t('Hello {name}!')


@template('markup.html')
def markup_function(c):
    return Pyjo.String.HTML.html('<b>markup</b>')


@template('plain.html')
def plain(c):
    return '<plain>'


app.template('lambda.html', lambda c, name: t('<p>{name}</p>', name=name))

get('/hello', {'name': '<Joe>'}, lambda c: c.render('hello'))

get('/hello/:name', lambda c: c.render('hello'))

get('/defaults', lambda c: c.render('defaults', name='Joe'))

get('/all', lambda c: c.render('all', a=1, b=2))

get('/layouted', lambda c: c.render('layouted', name='layouted'))

get('/items', lambda c: c.render('items', items=['<a>', '<b>']))

get('/include', lambda c: c.render('include'))

get('/both', lambda c: c.render('both'))

get('/text', {'format': 'txt'}, lambda c: c.render('text', name='Joe'))

get('/markup_function', lambda c: c.render('markup'))

get('/plain', lambda c: c.render('plain'))

get('/lambda', lambda c: c.render('lambda', name='<lambda>'))

get('/later', lambda c: c.render('later'))

# The templates of files, in tt, as the harness runs every Python file in t
app.renderer.paths.append(app.home.dirname().dirname().child('tt', 'templates').to_str())

get('/files/hello', lambda c: c.render('files/hello', name='<Joe>'))

get('/files/items', lambda c: c.render('files/items', items=['<a>', '<b>']))

get('/files/text', {'format': 'txt'}, lambda c: c.render('files/text', name='Joe'))

get('/files/dies', lambda c: c.render('files/dies'))

get('/files/no_render', lambda c: c.render('files/no_render'))

get('/files/broken', lambda c: c.render('broken'))

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

with subtest('Template of a function'):
    test.get_ok('/hello').status_is(200).content_type_is('text/html;charset=UTF-8').content_is(
        '<p>Hello &lt;Joe&gt;!</p>'
    )
    test.get_ok('/hello/Jane').status_is(200).content_is('<p>Hello Jane!</p>')

with subtest('Default of a parameter'):
    test.get_ok('/defaults').status_is(200).content_is('<p>Hello Joe!</p>')

with subtest('All the values of the stash'):
    test.get_ok('/all').status_is(200).content_is('<p>a, b</p>')

with subtest('Layout of a function'):
    test.get_ok('/layouted').status_is(200).content_is('<title>Green</title><body><p>layouted</p></body>')

with subtest('Include of a function'):
    test.get_ok('/items').status_is(200).content_is('<ul><li>&lt;a&gt;</li><li>&lt;b&gt;</li></ul>')

with subtest('Include of a function in an EP template'):
    test.get_ok('/include').status_is(200).content_is('<ul><li>&lt;ep&gt;</li></ul>\n')

with subtest('Function before the DATA section'):
    test.get_ok('/both').status_is(200).content_is('py')

with subtest('Another format'):
    test.get_ok('/text').status_is(200).content_type_is('text/plain;charset=UTF-8').content_is('Hello Joe!')

with subtest('Markup and a string'):
    test.get_ok('/markup_function').status_is(200).content_is('<b>markup</b>')
    test.get_ok('/plain').status_is(200).content_is('&lt;plain&gt;')

with subtest('Function of a call'):
    test.get_ok('/lambda').status_is(200).content_is('<p>&lt;lambda&gt;</p>')

with subtest('Template added after the first request'):
    test.get_ok('/later').status_is(500)
    app.template('later.html', lambda c: t('later'))
    test.get_ok('/later').status_is(200).content_is('later')

with subtest('Template of a file with a layout'):
    (
        test.get_ok('/files/hello')
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .content_is('<title>Hello</title><body><p>Hello &lt;Joe&gt;!</p></body>')
    )
    is_ok(app.renderer.template_handler({'template': 'files/hello', 'format': 'html'}), 'py', 'handler')

with subtest('Cached template of a file'):
    test.get_ok('/files/hello').status_is(200).content_is('<title>Hello</title><body><p>Hello &lt;Joe&gt;!</p></body>')

with subtest('Include of a file'):
    test.get_ok('/files/items').status_is(200).content_is('<ul><li>&lt;a&gt;</li><li>&lt;b&gt;</li></ul>')

with subtest('File of another format'):
    test.get_ok('/files/text').status_is(200).content_type_is('text/plain;charset=UTF-8').content_is('Hello Joe!')

with subtest('Exception in a file, with the line of the file'):
    (
        test.get_ok('/files/dies')
        .status_is(500)
        .content_like(r'dead file template!')
        .content_like(r'raise Exception\(&#39;dead file template!&#39;\)')
    )

with subtest('File without a function "render"'):
    test.get_ok('/files/no_render').status_is(500).content_like(r'has no function &quot;render&quot;')

with subtest('Syntax error in a file, with the line of the file'):
    tmp = Pyjo.File.tempdir()
    tmp.child('broken.html.py').spew(b'def render(c):\n    return (\n')
    app.renderer.paths.append(tmp.to_str())
    app.renderer.warmup()
    (test.get_ok('/files/broken').status_is(500).content_like(r'broken\.html\.py line \d').content_like(r'return \('))
    app.renderer.paths.pop()

with subtest('Registration'):
    is_ok(app.template('registered.html', hello), hello, 'function returned')
    is_ok(app.renderer.templates['hello.html'], hello, 'template')
    is_ok(app.renderer.template_handler({'template': 'hello', 'format': 'html'}), 'py', 'handler')
    c = app.build_controller()
    output = c.render_to_string('hello', name='<x>')
    isa_ok(output, Pyjo.String.HTML.object, 'markup')
    is_ok(output, '<p>Hello &lt;x&gt;!</p>', 'rendered to a string')

done_testing()
