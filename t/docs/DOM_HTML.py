from Pyjo.Test import *


with subtest('Synopsis'):
    from Pyjo.DOM.HTML import HTML

    # Turn HTML into DOM tree
    html = HTML()
    html.parse('<div><p id="a">Test</p><p id="b">123</p></div>')
    tree = html.tree
    is_ok(tree[1][1], 'div', 'tree')

    import Pyjo.DOM.HTML

    # Turn HTML into DOM tree
    html = Pyjo.DOM.HTML.new()
    html.parse('<div><p id="a">Test</p><p id="b">123</p></div>')
    tree = html.tree
    is_ok(tree[1][1], 'div', 'tree')

with subtest('tag_to_html'):
    from Pyjo.DOM.HTML import tag_to_html

    string = tag_to_html('div', 'safe content', id='foo')
    is_ok(string, '<div id="foo">safe content</div>', 'string')

with subtest('tree'):
    tree = html.tree
    html.tree = ['root']
    is_deeply_ok(html.tree, ['root'], 'tree')

with subtest('xml'):
    boolean = html.xml
    none_ok(boolean, 'auto-detection')
    html.xml = True
    ok(html.xml, 'xml')

with subtest('parse'):
    html = html.parse('<foo bar="baz">I ♥ Pyjoyment!</foo>')
    is_ok(html.render(), '<foo bar="baz">I ♥ Pyjoyment!</foo>', 'parse')

with subtest('render'):
    string = html.render()
    is_ok(string, '<foo bar="baz">I ♥ Pyjoyment!</foo>', 'string')

with subtest('tag'):
    html = html.tag('div', 'safe content', id='foo')
    is_ok(html.render(), '<div id="foo">safe content</div>', 'tag')

done_testing()
