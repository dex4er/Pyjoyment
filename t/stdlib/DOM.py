import Pyjo.DOM

from Pyjo.Test import *

import html


with subtest('Attributes as a mapping'):
    dom = Pyjo.DOM.new('<a href="/foo" id="a">A</a>').at('a')
    is_ok(dom['href'], '/foo', 'dom[name]')
    none_ok(dom['title'], 'None for no attribute, as attr() gives it')
    ok('id' in dom, 'in')
    ok('title' not in dom, 'not in')
    dom['title'] = 'Foo'
    del dom['id']
    del dom['nothing']
    is_ok(str(dom), '<a href="/foo" title="Foo">A</a>', 'set and deleted')
    is_deeply_ok(dict(dom.attr()), {'href': '/foo', 'title': 'Foo'}, 'dict()')

with subtest('Child nodes as a sequence'):
    dom = Pyjo.DOM.new('<!-- A --><b>B</b>C')
    is_ok(len(dom), 3, 'len()')
    is_deeply_ok([node.type for node in dom], ['comment', 'tag', 'text'], 'iteration')
    is_ok(dom[1], '<b>B</b>', 'dom[index]')
    is_ok(dom[-1], 'C', 'from the end')
    is_deeply_ok(dom[1:].map('type').to_list(), ['tag', 'text'], 'a slice is a collection')
    throws_ok(lambda: dom[3], IndexError, 'IndexError')

with subtest('Always true'):
    dom = Pyjo.DOM.new()
    is_ok(len(dom), 0, 'no child nodes')
    is_ok(str(dom), '', 'empty')
    ok(bool(dom), 'still true')

with subtest('Entities'):
    dom = Pyjo.DOM.new('<p title="&lt;&amp;&#x2603;">&lt;&hearts;&gt;</p>').at('p')
    is_ok(dom.text, html.unescape('&lt;&hearts;&gt;'), 'text as html.unescape() gives it')
    is_ok(dom['title'], html.unescape('&lt;&amp;&#x2603;'), 'attribute as html.unescape() gives it')
    is_ok(str(dom), '<p title="&lt;&amp;☃">&lt;♥&gt;</p>', 'rendered escaped')
    is_ok(html.unescape(dom.content), dom.text, 'html.unescape() reads it back')

done_testing()
