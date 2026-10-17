# /// script
# requires-python = ">=3.14"
# ///
"""
__DATA__
@@ layouts/default.html.ep
<body><%= content() %></body>
"""

import Pyjo.Test.Pyjo

from Pyjo.Test import *
from Pyjoyment.Lite import app, get, template


@get('/inline')
def inline(c):
    name = c.param('name')
    c.render(inline=t'<p>Hello {name}!</p>')


@get('/stash', {'name': 'stash'})
def stash(c):
    c.render(inline=t'<p>{c.stash("name")}</p>')


@get('/markup')
def markup(c):
    c.render(inline=t'<p>{c.link_to("Home", "/")}</p>')


@get('/nested')
def nested(c):
    tags = ['<b>', '<i>']
    c.render(inline=t'<ul>{[t"<li>{tag}</li>" for tag in tags]}</ul>')


@get('/format_spec')
def format_spec(c):
    price = 1.5
    c.render(inline=t'<p>{price:.2f} {"<b>"!r}</p>')


@template('hello.html')
def hello(c, name):
    c.layout('default')
    c.title('Hello')
    return t'<p>Hello {name}!</p>'


@template('layouts/default.html')
def default(c, **stash):
    return t'<title>{c.title()}</title><body>{c.content()}</body>'


@template('items.html')
def items(c, items):
    return t'<ul>{[t"<li>{item}</li>" for item in items]}</ul>'


get('/hello', lambda c: c.render('hello', name='<Joe>'))

get('/items', lambda c: c.render('items', items=['<a>', '<b>']))

# The templates of files, in tt, as the harness runs every Python file in t
app.renderer.paths.append(app.home.dirname().dirname().child('tt', 'templates_native').to_str())

get('/native', lambda c: c.render('native', items=['<a>', '<b>']))

t = Pyjo.Test.Pyjo.new()

with subtest('Inline t-string'):
    (
        t.get_ok('/inline?name=<script>')
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .content_is('<p>Hello &lt;script&gt;!</p>')
    )

with subtest('Value of the stash'):
    t.get_ok('/stash').status_is(200).content_is('<p>stash</p>')

with subtest('Markup of a helper'):
    t.get_ok('/markup').status_is(200).content_is('<p><a href="/">Home</a></p>')

with subtest('Nested t-strings'):
    t.get_ok('/nested').status_is(200).content_is('<ul><li>&lt;b&gt;</li><li>&lt;i&gt;</li></ul>')

with subtest('Conversion and format specification'):
    t.get_ok('/format_spec').status_is(200).content_is('<p>1.50 &#39;&lt;b&gt;&#39;</p>')

with subtest('Template of a function with a layout'):
    t.get_ok('/hello').status_is(200).content_is('<title>Hello</title><body><p>Hello &lt;Joe&gt;!</p></body>')

with subtest('Nested t-strings of a function'):
    t.get_ok('/items').status_is(200).content_is('<ul><li>&lt;a&gt;</li><li>&lt;b&gt;</li></ul>')

with subtest('Template of a file with t-strings'):
    t.get_ok('/native').status_is(200).content_is('<ul><li>&lt;a&gt;</li><li>&lt;b&gt;</li></ul>')

done_testing()
