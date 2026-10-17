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
from Pyjoyment.Lite import get


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

done_testing()
