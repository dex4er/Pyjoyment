# coding: utf-8

import Pyjo.Test


class NoseTest(Pyjo.Test.NoseTest):
    script = __file__
    srcdir = '../..'


class UnitTest(Pyjo.Test.UnitTest):
    script = __file__


if __name__ == '__main__':

    from Pyjo.Test import *  # noqa

    import Pyjo.DOM

    # Empty
    is_ok(str(Pyjo.DOM.new()), '', 'right result')
    is_ok(str(Pyjo.DOM.new('')), '', 'right result')
    is_ok(str(Pyjo.DOM.new().parse('')), '', 'right result')

    # Simple (basics)
    dom = Pyjo.DOM.new('<div><div FOO="0" id="a">A</div><div id="b">B</div></div>')
    is_ok(dom.at('#b').text, 'B', 'right text')
    div = []
    div.extend(dom.find('div[id]').map('text'))
    is_deeply_ok(div, ['A', 'B'], 'found all div elements with id')
    div = []
    dom.find('div[id]').each(lambda i, n: div.append(i.text))
    is_deeply_ok(div, ['A', 'B'], 'found all div elements with id')
    is_ok(dom.at('#a').attr('foo'), '0', 'right attribute')
    is_ok(dom.at('#a').attr()['foo'], '0', 'right attribute')
    is_ok(dom, '<div><div foo="0" id="a">A</div><div id="b">B</div></div>', 'right result')

    # Tap into method chain
    dom = Pyjo.DOM.new().parse('<div id="a">A</div><div id="b">B</div>')
    is_deeply_ok(dom.find('[id]').map('attr', 'id'), ['a', 'b'], 'right result')
    is_ok(str(dom.tap(lambda i: i.at('#b').remove())), '<div id="a">A</div>', 'right result')

    # Simple nesting with healing (tree structure)
    dom = Pyjo.DOM.new('<foo><bar a="b&lt;c">ju<baz a23>s<bazz />t</bar>works</foo>')
    is_ok(dom.tree[0], 'root', 'right element')
    is_ok(dom.tree[1][0], 'tag', 'right element')
    is_ok(dom.tree[1][1], 'foo', 'right tag')
    is_deeply_ok(dom.tree[1][2], {}, 'empty attributes')
    is_ok(dom.tree[1][3], dom.tree, 'right parent')
    is_ok(dom.tree[1][4][0], 'tag', 'right element')
    is_ok(dom.tree[1][4][1], 'bar', 'right tag')
    is_deeply_ok(dom.tree[1][4][2], {'a': 'b<c'}, 'right attributes')
    is_ok(dom.tree[1][4][3], dom.tree[1], 'right parent')
    is_ok(dom.tree[1][4][4][0], 'text', 'right element')
    is_ok(dom.tree[1][4][4][1], 'ju', 'right text')
    is_ok(dom.tree[1][4][4][2], dom.tree[1][4], 'right parent')
    is_ok(dom.tree[1][4][5][0], 'tag', 'right element')
    is_ok(dom.tree[1][4][5][1], 'baz', 'right tag')
    is_deeply_ok(dom.tree[1][4][5][2], {'a23': None}, 'right attributes')
    is_ok(dom.tree[1][4][5][3], dom.tree[1][4], 'right parent')
    is_ok(dom.tree[1][4][5][4][0], 'text', 'right element')
    is_ok(dom.tree[1][4][5][4][1], 's', 'right text')
    is_ok(dom.tree[1][4][5][4][2], dom.tree[1][4][5], 'right parent')
    is_ok(dom.tree[1][4][5][5][0], 'tag', 'right element')
    is_ok(dom.tree[1][4][5][5][1], 'bazz', 'right tag')
    is_deeply_ok(dom.tree[1][4][5][5][2], {}, 'empty attributes')
    is_ok(dom.tree[1][4][5][5][3], dom.tree[1][4][5], 'right parent')
    is_ok(dom.tree[1][4][5][6][0], 'text', 'right element')
    is_ok(dom.tree[1][4][5][6][1], 't', 'right text')
    is_ok(dom.tree[1][4][5][6][2], dom.tree[1][4][5], 'right parent')
    is_ok(dom.tree[1][5][0], 'text', 'right element')
    is_ok(dom.tree[1][5][1], 'works', 'right text')
    is_ok(dom.tree[1][5][2], dom.tree[1], 'right parent')
    is_ok(dom, '<foo><bar a="b&lt;c">ju<baz a23>s<bazz></bazz>t</baz></bar>works</foo>', 'right result')

    # Select based on parent
    dom = Pyjo.DOM.new("""
    <body>
      <div>test1</div>
      <div><div>test2</div></div>
    <body>
    """)
    is_ok(dom.find('body > div')[0].text, 'test1', 'right text')
    is_ok(dom.find('body > div')[1].text, '', 'no content')
    throws_ok(lambda: dom.find('body > div')[2], IndexError, 'no result')
    is_ok(dom.find('body > div').size, 2, 'right number of elements')
    is_ok(dom.find('body > div > div')[0].text, 'test2', 'right text')
    throws_ok(lambda: dom.find('body > div > div')[1], IndexError, 'no result')
    is_ok(dom.find('body > div > div').size, 1, 'right number of elements')

    # A bit of everything (basic navigation)
    dom = Pyjo.DOM.new().parse("""<!doctype foo>
    <foo bar="ba&lt;z">
      test
      <simple class="working">easy</simple>
      <test foo="bar" id="test" />
      <!-- lala -->
      works well
      <![CDATA[ yada yada]]>
      <?boom lalalala ?>
      <a little bit broken>
      < very broken
      <br />
      more text
    </foo>""")
    ok(not dom.xml, 'XML mode not detected')
    is_ok(dom.tag, None, 'no tag')
    is_ok(dom.attr('foo'), None, 'no attribute')
    is_ok(dom.attr(foo='bar').attr('foo'), None, 'no attribute')
    is_ok(dom.tree[1][0], 'doctype', 'right element')
    is_ok(dom.tree[1][1], ' foo', 'right doctype')
    is_ok(dom, """<!DOCTYPE foo>
    <foo bar="ba&lt;z">
      test
      <simple class="working">easy</simple>
      <test foo="bar" id="test"></test>
      <!-- lala -->
      works well
      <![CDATA[ yada yada]]>
      <?boom lalalala ?>
      <a bit broken little>
      &lt; very broken
      <br>
      more text
    </a></foo>""", 'right result')
    simple = dom.at('foo simple.working[class^="wor"]')
    is_ok(simple.parent.all_text, 'test easy works well yada yada < very broken more text', 'right text')
    is_ok(simple.tag, 'simple', 'right tag')
    is_ok(simple.attr('class'), 'working', 'right class attribute')
    is_ok(simple.text, 'easy', 'right text')
    is_ok(simple.parent.tag, 'foo', 'right parent tag')
    is_ok(simple.parent.attr('bar'), 'ba<z', 'right parent attribute')
    is_ok(simple.parent.children()[1].tag, 'test', 'right sibling')
    is_ok(simple.to_str(), '<simple class="working">easy</simple>', 'stringified right')
    simple.parent.attr('bar', 'baz').attr(this='works', too='yea')
    is_ok(simple.parent.attr('bar'), 'baz', 'right parent attribute')
    is_ok(simple.parent.attr('this'), 'works', 'right parent attribute')
    is_ok(simple.parent.attr('too'), 'yea', 'right parent attribute')
    is_ok(dom.at('test#test').tag, 'test', 'right tag')
    is_ok(dom.at('[class$="ing"]').tag, 'simple', 'right tag')
    is_ok(dom.at('[class="working"]').tag, 'simple', 'right tag')
    is_ok(dom.at('[class$=ing]').tag, 'simple', 'right tag')
    is_ok(dom.at('[class=working][class]').tag, 'simple', 'right tag')
    is_ok(dom.at('foo > simple').next.tag, 'test', 'right tag')
    is_ok(dom.at('foo > simple').next.next.tag, 'a', 'right tag')
    is_ok(dom.at('foo > test').previous.tag, 'simple', 'right tag')
    is_ok(dom.next, None, 'no siblings')
    is_ok(dom.previous, None, 'no siblings')
    is_ok(dom.at('foo > a').next, None, 'no next sibling')
    is_ok(dom.at('foo > simple').previous, None, 'no previous sibling')
    is_deeply_ok(dom.at('simple').ancestors().map('tag'), ['foo'], 'right results')
    ok(not dom.at('simple').ancestors().first().xml, 'XML mode not active')

    # Nodes
    dom = Pyjo.DOM.new('<!DOCTYPE before><p>test<![CDATA[123]]><!-- 456 --></p><?after?>')
    is_ok(dom.at('p').preceding_nodes().first().content, ' before', 'right content')
    is_ok(dom.at('p').preceding_nodes().size, 1, 'right number of nodes')
    is_ok(dom.at('p').child_nodes.last().preceding_nodes().first().content, 'test', 'right content')
    is_ok(dom.at('p').child_nodes.last().preceding_nodes().last().content, '123', 'right content')
    is_ok(dom.at('p').child_nodes.last().preceding_nodes().size, 2, 'right number of nodes')
    is_ok(dom.preceding_nodes().size, 0, 'no preceding nodes')
    is_ok(dom.at('p').following_nodes().first().content, 'after', 'right content')
    is_ok(dom.at('p').following_nodes().size, 1, 'right number of nodes')
    is_ok(dom.child_nodes.first().following_nodes().first().tag, 'p', 'right tag')
    is_ok(dom.child_nodes.first().following_nodes().last().content, 'after', 'right content')
    is_ok(dom.child_nodes.first().following_nodes().size, 2, 'right number of nodes')
    is_ok(dom.following_nodes().size, 0, 'no following nodes')
    is_ok(dom.at('p').previous_node.content, ' before', 'right content')
    is_ok(dom.at('p').previous_node.previous_node, None, 'no more siblings')
    is_ok(dom.at('p').next_node.content, 'after', 'right content')
    is_ok(dom.at('p').next_node.next_node, None, 'no more siblings')
    is_ok(dom.at('p').child_nodes.last().previous_node.previous_node.content, 'test', 'right content')
    is_ok(dom.at('p').child_nodes.first().next_node.next_node.content, ' 456 ', 'right content')
    is_ok(dom.descendant_nodes[0].type, 'doctype', 'right node')
    is_ok(dom.descendant_nodes[0].content, ' before', 'right content')
    is_ok(dom.descendant_nodes[0], '<!DOCTYPE before>', 'right content')
    is_ok(dom.descendant_nodes[1].tag, 'p', 'right tag')
    is_ok(dom.descendant_nodes[2].type, 'text', 'right node')
    is_ok(dom.descendant_nodes[2].content, 'test', 'right content')
    is_ok(dom.descendant_nodes[5].type, 'pi', 'right node')
    is_ok(dom.descendant_nodes[5].content, 'after', 'right content')
    is_ok(dom.at('p').descendant_nodes[0].type, 'text', 'right node')
    is_ok(dom.at('p').descendant_nodes[0].content, 'test', 'right node')
    is_ok(dom.at('p').descendant_nodes.last().type, 'comment', 'right node')
    is_ok(dom.at('p').descendant_nodes.last().content, ' 456 ', 'right node')
    is_ok(dom.child_nodes[1].child_nodes.first().parent.tag, 'p', 'right tag')
    is_ok(dom.child_nodes[1].child_nodes.first().content, 'test', 'right content')
    is_ok(dom.child_nodes[1].child_nodes.first(), 'test', 'right content')
    is_ok(dom.at('p').child_nodes.first().type, 'text', 'right node')
    is_ok(dom.at('p').child_nodes.first().remove().tag, 'p', 'right tag')
    is_ok(dom.at('p').child_nodes.first().type, 'cdata', 'right node')
    is_ok(dom.at('p').child_nodes.first().content, '123', 'right content')
    is_ok(dom.at('p').child_nodes[1].type, 'comment', 'right node')
    is_ok(dom.at('p').child_nodes[1].content, ' 456 ', 'right content')
    is_ok(dom.child_nodes[0].type, 'doctype', 'right node')
    is_ok(dom.child_nodes[0].content, ' before', 'right content')
    is_ok(dom.child_nodes[2].type, 'pi', 'right node')
    is_ok(dom.child_nodes[2].content, 'after', 'right content')
    is_ok(dom.child_nodes.first().set(content=' again').content, ' again', 'right content')
    is_ok(dom.child_nodes.grep(lambda i: i.type == 'pi').map('remove').first().type, 'root', 'right node')
    is_ok(dom, '<!DOCTYPE again><p><![CDATA[123]]><!-- 456 --></p>', 'right result')

    # Modify nodes
    dom = Pyjo.DOM.new('<script>la<la>la</script>')
    is_ok(dom.at('script').type, 'tag', 'right node')
    is_ok(dom.at('script').child_nodes[0].type, 'raw', 'right node')
    is_ok(dom.at('script').child_nodes[0].content, 'la<la>la', 'right content')
    is_ok(dom, '<script>la<la>la</script>', 'right result')
    is_ok(dom.at('script').child_nodes.first().replace('a<b>c</b>1<b>d</b>').tag, 'script', 'right tag')
    is_ok(dom, '<script>a<b>c</b>1<b>d</b></script>', 'right result')
    is_ok(dom.at('b').child_nodes.first().append('e').content, 'c', 'right content')
    is_ok(dom.at('b').child_nodes.first().prepend('f').type, 'text', 'right node')
    is_ok(dom, '<script>a<b>fce</b>1<b>d</b></script>', 'right result')
    is_ok(dom.at('script').child_nodes.first().following().first().tag, 'b', 'right tag')
    is_ok(dom.at('script').child_nodes.first().next.content, 'fce', 'right content')
    is_ok(dom.at('script').child_nodes.first().previous, None, 'no siblings')
    is_ok(dom.at('script').child_nodes[2].previous.content, 'fce', 'right content')
    is_ok(dom.at('b').child_nodes[1].next, None, 'no siblings')
    is_ok(dom.at('script').child_nodes.first().wrap('<i>:)</i>').root, '<script><i>:)a</i><b>fce</b>1<b>d</b></script>', 'right result')
    is_ok(dom.at('i').child_nodes.first().wrap_content('<b></b>').root, '<script><i><b>:)</b>a</i><b>fce</b>1<b>d</b></script>', 'right result')
    is_ok(dom.at('b').child_nodes.first().ancestors().map('tag').join(','), 'b,i,script', 'right result')
    is_ok(dom.at('b').child_nodes.first().append_content('g').content, ':)g', 'right content')
    is_ok(dom.at('b').child_nodes.first().prepend_content('h').content, 'h:)g', 'right content')
    is_ok(dom, '<script><i><b>h:)g</b>a</i><b>fce</b>1<b>d</b></script>', 'right result')
    is_ok(dom.at('script > b:last-of-type').append('<!--y-->').following_nodes().first().content, 'y', 'right content')
    is_ok(dom.at('i').prepend('z').preceding_nodes().first().content, 'z', 'right content')
    is_ok(dom.at('i').following().last().text, 'd', 'right text')
    is_ok(dom.at('i').following().size, 2, 'right number of following elements')
    is_ok(dom.at('i').following('b:last-of-type').first().text, 'd', 'right text')
    is_ok(dom.at('i').following('b:last-of-type').size, 1, 'right number of following elements')
    is_ok(dom.following().size, 0, 'no following elements')
    is_ok(dom.at('script > b:last-of-type').preceding().first().tag, 'i', 'right tag')
    is_ok(dom.at('script > b:last-of-type').preceding().size, 2, 'right number of preceding elements')
    is_ok(dom.at('script > b:last-of-type').preceding('b').first().tag, 'b', 'right tag')
    is_ok(dom.at('script > b:last-of-type').preceding('b').size, 1, 'right number of preceding elements')
    is_ok(dom.preceding().size, 0, 'no preceding elements')
    is_ok(dom, '<script>z<i><b>h:)g</b>a</i><b>fce</b>1<b>d</b><!--y--></script>', 'right result')

    # XML nodes
    dom = Pyjo.DOM.new().set(xml=1).parse('<b>test<image /></b>')
    ok(dom.at('b').child_nodes.first().xml, 'XML mode active')
    ok(dom.at('b').child_nodes.first().replace('<br>').child_nodes.first().xml, 'XML mode active')
    is_ok(dom, '<b><br /><image /></b>', 'right result')

    # Treating nodes as elements
    dom = Pyjo.DOM.new('foo<b>bar</b>baz')
    is_ok(dom.child_nodes.first().child_nodes.size, 0, 'no child_nodes')
    is_ok(dom.child_nodes.first().descendant_nodes.size, 0, 'no contents')
    is_ok(dom.child_nodes.first().children().size, 0, 'no children')
    is_ok(dom.child_nodes.first().strip().parent, 'foo<b>bar</b>baz', 'no changes')
    is_ok(dom.child_nodes.first().at('b'), None, 'no result')
    is_ok(dom.child_nodes.first().find('*').size, 0, 'no results')
    is_ok(dom.child_nodes.first().matches('*'), None, 'no match')
    is_deeply_ok(dom.child_nodes.first().attr(), {}, 'no attributes')
    is_ok(dom.child_nodes.first().namespace, None, 'no namespace')
    is_ok(dom.child_nodes.first().tag, None, 'no tag')
    is_ok(dom.child_nodes.first().text, '', 'no text')
    is_ok(dom.child_nodes.first().all_text, '', 'no text')

    # Class and ID
    dom = Pyjo.DOM.new('<div id="id" class="class">a</div>')
    is_ok(dom.at('div#id.class').text, 'a', 'right text')

    # Deep nesting (parent combinator)
    dom = Pyjo.DOM.new("""
    <html>
      <head>
        <title>Foo</title>
      </head>
      <body>
        <div id="container">
          <div id="header">
            <div id="logo">Hello World</div>
            <div id="buttons">
              <p id="foo">Foo</p>
            </div>
          </div>
          <form>
            <div id="buttons">
              <p id="bar">Bar</p>
            </div>
          </form>
          <div id="content">More stuff</div>
        </div>
      </body>
    </html>
    """)
    p = dom.find('body > #container > div p[id]')
    is_ok(p[0].attr('id'), 'foo', 'right id attribute')
    throws_ok(lambda: p[1], IndexError, 'no second result')
    is_ok(p.size, 1, 'right number of elements')
    p = []
    div = []
    dom.find('div').each(lambda i, n: div.append(i.attr('id')))
    dom.find('p').each(lambda i, n: p.append(i.attr('id')))
    is_deeply_ok(p, ['foo', 'bar'], 'found all p elements')
    ids = ['container', 'header', 'logo', 'buttons', 'buttons', 'content']
    is_deeply_ok(div, ids, 'found all div elements')
    is_deeply_ok(dom.at('p').ancestors().map('tag'), ['div', 'div', 'div', 'body', 'html'], 'right results')
    is_deeply_ok(dom.at('html').ancestors(), [], 'no results')
    is_deeply_ok(dom.ancestors(), [], 'no results')

    # Script tag
    dom = Pyjo.DOM.new("""
    <script charset="utf-8">alert('lalala')</script>
    """)
    is_ok(dom.at('script').text, "alert('lalala')", 'right script content')

    # HTML5 (unquoted values)
    dom = Pyjo.DOM.new('<div id = test foo ="bar" class=tset bar=/baz/ baz=//>works</div>')
    is_ok(dom.at('#test').text, 'works', 'right text')
    is_ok(dom.at('div').text, 'works', 'right text')
    is_ok(dom.at('[foo=bar][foo="bar"]').text, 'works', 'right text')
    is_ok(dom.at('[foo="ba"]'), None, 'no result')
    is_ok(dom.at('[foo=bar]').text, 'works', 'right text')
    is_ok(dom.at('[foo=ba]'), None, 'no result')
    is_ok(dom.at('.tset').text, 'works', 'right text')
    is_ok(dom.at('[bar=/baz/]').text, 'works', 'right text')
    is_ok(dom.at('[baz=//]').text, 'works', 'right text')

    # HTML1 (single quotes, uppercase tags and whitespace in attributes)
    dom = Pyjo.DOM.new('''<DIV id = 'test' foo ='bar' class= "tset">works</DIV>''')
    is_ok(dom.at('#test').text, 'works', 'right text')
    is_ok(dom.at('div').text, 'works', 'right text')
    is_ok(dom.at('[foo="bar"]').text, 'works', 'right text')
    is_ok(dom.at('[foo="ba"]'), None, 'no result')
    is_ok(dom.at('[foo=bar]').text, 'works', 'right text')
    is_ok(dom.at('[foo=ba]'), None, 'no result')
    is_ok(dom.at('.tset').text, 'works', 'right text')

    # Already decoded Unicode snowman and quotes in selector
    dom = Pyjo.DOM.new(u'<div id="snowm&quot;an">☃</div>')
    is_ok(dom.at(r'[id="snowm\"an"]').text, u'☃', 'right text')
    is_ok(dom.at(r'[id="snowm\22 an"]').text, u'☃', 'right text')
    is_ok(dom.at(r'[id="snowm\000022an"]').text, u'☃', 'right text')
    is_ok(dom.at(r'[id="snowm\22an"]'), None, 'no result')
    is_ok(dom.at(r'[id="snowm\21 an"]'), None, 'no result')
    is_ok(dom.at(r'[id="snowm\000021an"]'), None, 'no result')
    is_ok(dom.at(r'[id="snowm\000021 an"]'), None, 'no result')

    # Unicode and escaped selectors
    html = u'<html><div id="☃x">Snowman</div><div class="x ♥">Heart</div></html>'
    dom = Pyjo.DOM.new(html)
    is_ok(dom.at("#\\\n\\002603x").text, 'Snowman', 'right text')
    is_ok(dom.at('#\\2603 x').text, 'Snowman', 'right text')
    is_ok(dom.at("#\\\n\\2603 x").text, 'Snowman', 'right text')
    is_ok(dom.at('[id="\\\n\\2603 x"]').text, 'Snowman', 'right text')
    is_ok(dom.at('[id="\\\n\\002603x"]').text, 'Snowman', 'right text')
    is_ok(dom.at('[id="\\\\2603 x"]').text, 'Snowman', 'right text')
    is_ok(dom.at("html #\\\n\\002603x").text, 'Snowman', 'right text')
    is_ok(dom.at('html #\\2603 x').text, 'Snowman', 'right text')
    is_ok(dom.at("html #\\\n\\2603 x").text, 'Snowman', 'right text')
    is_ok(dom.at('html [id="\\\n\\2603 x"]').text, 'Snowman', 'right text')
    is_ok(dom.at('html [id="\\\n\\002603x"]').text, 'Snowman', 'right text')
    is_ok(dom.at('html [id="\\\\2603 x"]').text, 'Snowman', 'right text')
    is_ok(dom.at(u'#☃x').text, 'Snowman', 'right text')
    is_ok(dom.at(u'div#☃x').text, 'Snowman', 'right text')
    is_ok(dom.at(u'html div#☃x').text, 'Snowman', 'right text')
    is_ok(dom.at(u'[id^="☃"]').text, 'Snowman', 'right text')
    is_ok(dom.at(u'div[id^="☃"]').text, 'Snowman', 'right text')
    is_ok(dom.at(u'html div[id^="☃"]').text, 'Snowman', 'right text')
    is_ok(dom.at(u'html > div[id^="☃"]').text, 'Snowman', 'right text')
    is_ok(dom.at(u'[id^=☃]').text, 'Snowman', 'right text')
    is_ok(dom.at(u'div[id^=☃]').text, 'Snowman', 'right text')
    is_ok(dom.at(u'html div[id^=☃]').text, 'Snowman', 'right text')
    is_ok(dom.at(u'html > div[id^=☃]').text, 'Snowman', 'right text')
    is_ok(dom.at(".\\\n\\002665").text, 'Heart', 'right text')
    is_ok(dom.at('.\\2665').text, 'Heart', 'right text')
    is_ok(dom.at("html .\\\n\\002665").text, 'Heart', 'right text')
    is_ok(dom.at('html .\\2665').text, 'Heart', 'right text')
    is_ok(dom.at('html [class$="\\\n\\002665"]').text, 'Heart', 'right text')
    is_ok(dom.at('html [class$="\\2665"]').text, 'Heart', 'right text')
    is_ok(dom.at('[class$="\\\n\\002665"]').text, 'Heart', 'right text')
    is_ok(dom.at('[class$="\\2665"]').text, 'Heart', 'right text')
    is_ok(dom.at('.x').text, 'Heart', 'right text')
    is_ok(dom.at('html .x').text, 'Heart', 'right text')
    is_ok(dom.at(u'.♥').text, 'Heart', 'right text')
    is_ok(dom.at(u'html .♥').text, 'Heart', 'right text')
    is_ok(dom.at(u'div.♥').text, 'Heart', 'right text')
    is_ok(dom.at(u'html div.♥').text, 'Heart', 'right text')
    is_ok(dom.at(u'[class$="♥"]').text, 'Heart', 'right text')
    is_ok(dom.at(u'div[class$="♥"]').text, 'Heart', 'right text')
    is_ok(dom.at(u'html div[class$="♥"]').text, 'Heart', 'right text')
    is_ok(dom.at(u'html > div[class$="♥"]').text, 'Heart', 'right text')
    is_ok(dom.at(u'[class$=♥]').text, 'Heart', 'right text')
    is_ok(dom.at(u'div[class$=♥]').text, 'Heart', 'right text')
    is_ok(dom.at(u'html div[class$=♥]').text, 'Heart', 'right text')
    is_ok(dom.at(u'html > div[class$=♥]').text, 'Heart', 'right text')
    is_ok(dom.at(u'[class~="♥"]').text, 'Heart', 'right text')
    is_ok(dom.at(u'div[class~="♥"]').text, 'Heart', 'right text')
    is_ok(dom.at(u'html div[class~="♥"]').text, 'Heart', 'right text')
    is_ok(dom.at(u'html > div[class~="♥"]').text, 'Heart', 'right text')
    is_ok(dom.at(u'[class~=♥]').text, 'Heart', 'right text')
    is_ok(dom.at(u'div[class~=♥]').text, 'Heart', 'right text')
    is_ok(dom.at(u'html div[class~=♥]').text, 'Heart', 'right text')
    is_ok(dom.at(u'html > div[class~=♥]').text, 'Heart', 'right text')
    is_ok(dom.at('[class~="x"]').text, 'Heart', 'right text')
    is_ok(dom.at('div[class~="x"]').text, 'Heart', 'right text')
    is_ok(dom.at('html div[class~="x"]').text, 'Heart', 'right text')
    is_ok(dom.at('html > div[class~="x"]').text, 'Heart', 'right text')
    is_ok(dom.at('[class~=x]').text, 'Heart', 'right text')
    is_ok(dom.at('div[class~=x]').text, 'Heart', 'right text')
    is_ok(dom.at('html div[class~=x]').text, 'Heart', 'right text')
    is_ok(dom.at('html > div[class~=x]').text, 'Heart', 'right text')
    is_ok(dom.at('html'), html, 'right result')
    is_ok(dom.at(u'#☃x').parent, html, 'right result')
    is_ok(dom.at(u'#☃x').root, html, 'right result')
    is_ok(dom.children('html').first(), html, 'right result')
    is_ok(dom.to_str(), html, 'right result')
    is_ok(dom.content, html, 'right result')

    # Looks remotely like HTML
    dom = Pyjo.DOM.new(u'<!DOCTYPE H "-/W/D HT 4/E">☃<title class=test>♥</title>☃')
    is_ok(dom.at('title').text, u'♥', 'right text')
    is_ok(dom.at('*').text, u'♥', 'right text')
    is_ok(dom.at('.test').text, u'♥', 'right text')

    # Replace elements
    dom = Pyjo.DOM.new('<div>foo<p>lalala</p>bar</div>')
    is_ok(dom.at('p').replace('<foo>bar</foo>'), '<div>foo<foo>bar</foo>bar</div>', 'right result')
    is_ok(dom, '<div>foo<foo>bar</foo>bar</div>', 'right result')
    dom.at('foo').replace(Pyjo.DOM.new('text'))
    is_ok(dom, '<div>footextbar</div>', 'right result')
    dom = Pyjo.DOM.new('<div>foo</div><div>bar</div>')
    dom.find('div').each(lambda i, n: i.replace('<p>test</p>'))
    is_ok(dom, '<p>test</p><p>test</p>', 'right result')
    dom = Pyjo.DOM.new('<div>foo<p>lalala</p>bar</div>')
    is_ok(dom.replace(u'♥'), u'♥', 'right result')
    is_ok(dom, u'♥', 'right result')
    dom.replace('<div>foo<p>lalala</p>bar</div>')
    is_ok(dom, '<div>foo<p>lalala</p>bar</div>', 'right result')
    is_ok(dom.at('p').replace(''), '<div>foobar</div>', 'right result')
    is_ok(dom, '<div>foobar</div>', 'right result')
    is_ok(dom.replace(''), '', 'no result')
    is_ok(dom, '', 'no result')
    dom.replace('<div>foo<p>lalala</p>bar</div>')
    is_ok(dom, '<div>foo<p>lalala</p>bar</div>', 'right result')
    dom.find('p').map('replace', '')
    is_ok(dom, '<div>foobar</div>', 'right result')
    dom = Pyjo.DOM.new(u'<div>♥</div>')
    dom.at('div').set(content=u'☃')
    is_ok(dom, u'<div>☃</div>', 'right result')
    dom = Pyjo.DOM.new(u'<div>♥</div>')
    dom.at('div').set(content=u"\u2603")
    is_ok(dom.to_str(), u'<div>☃</div>', 'right result')
    is_ok(dom.at('div').replace(u'<p>♥</p>').root, u'<p>♥</p>', 'right result')
    is_ok(dom.to_str(), u'<p>♥</p>', 'right result')
    is_ok(dom.replace('<b>whatever</b>').root, '<b>whatever</b>', 'right result')
    is_ok(dom.to_str(), '<b>whatever</b>', 'right result')
    dom.at('b').prepend('<p>foo</p>').append('<p>bar</p>')
    is_ok(dom, '<p>foo</p><b>whatever</b><p>bar</p>', 'right result')
    is_ok(dom.find('p').map('remove').first().root.at('b').text, 'whatever', 'right result')
    is_ok(dom, '<b>whatever</b>', 'right result')
    is_ok(dom.at('b').strip(), 'whatever', 'right result')
    is_ok(dom.strip(), 'whatever', 'right result')
    is_ok(dom.remove(), '', 'right result')
    dom.replace('A<div>B<p>C<b>D<i><u>E</u></i>F</b>G</p><div>H</div></div>I')
    is_ok(dom.find(':not(div):not(i):not(u)').map('strip').first().root, 'A<div>BCD<i><u>E</u></i>FG<div>H</div></div>I', 'right result')
    is_ok(dom.at('i').to_str(), '<i><u>E</u></i>', 'right result')
    dom = Pyjo.DOM.new('<div><div>A</div><div>B</div>C</div>')
    is_ok(dom.at('div').at('div').text, 'A', 'right text')
    dom.at('div').find('div').map('strip')
    is_ok(dom, '<div>ABC</div>', 'right result')

    # Replace element content
    dom = Pyjo.DOM.new('<div>foo<p>lalala</p>bar</div>')
    is_ok(dom.at('p').set(content='bar'), '<p>bar</p>', 'right result')
    is_ok(dom, '<div>foo<p>bar</p>bar</div>', 'right result')
    dom.at('p').set(content=Pyjo.DOM.new('text'))
    is_ok(dom, '<div>foo<p>text</p>bar</div>', 'right result')
    dom = Pyjo.DOM.new('<div>foo</div><div>bar</div>')
    dom.find('div').each(lambda i, n: i.set(content='<p>test</p>'))
    is_ok(dom, '<div><p>test</p></div><div><p>test</p></div>', 'right result')
    dom.find('p').each(lambda i, n: i.set(content=''))
    is_ok(dom, '<div><p></p></div><div><p></p></div>', 'right result')
    dom = Pyjo.DOM.new(u'<div><p id="☃" /></div>')
    dom.at(u'#☃').set(content=u'♥')
    is_ok(dom, u'<div><p id="☃">♥</p></div>', 'right result')
    dom = Pyjo.DOM.new('<div>foo<p>lalala</p>bar</div>')
    dom.set(content=u'♥')
    is_ok(dom, u'♥', 'right result')
    is_ok(dom.set(content='<div>foo<p>lalala</p>bar</div>'), '<div>foo<p>lalala</p>bar</div>', 'right result')
    is_ok(dom, '<div>foo<p>lalala</p>bar</div>', 'right result')
    is_ok(dom.set(content=''), '', 'no result')
    is_ok(dom, '', 'no result')
    dom.set(content='<div>foo<p>lalala</p>bar</div>')
    is_ok(dom, '<div>foo<p>lalala</p>bar</div>', 'right result')
    is_ok(dom.at('p').set(content=''), '<p></p>', 'right result')

    # Mixed search and tree walk
    dom = Pyjo.DOM.new("""
    <table>
      <tr>
        <td>text1</td>
        <td>text2</td>
      </tr>
    </table>
    """)
    data = []
    for tr in dom.find('table tr'):
        for td in tr.children():
            data.append(td.tag)
            data.append(td.all_text)
    is_ok(data[0], 'td', 'right tag')
    is_ok(data[1], 'text1', 'right text')
    is_ok(data[2], 'td', 'right tag')
    is_ok(data[3], 'text2', 'right text')
    throws_ok(lambda: data[4], IndexError, 'no tag')

    # RSS
    dom = Pyjo.DOM.new("""
    <?xml version="1.0" encoding="UTF-8"?>
    <rss xmlns:atom="http://www.w3.org/2005/Atom" version="2.0">
      <channel>
        <title>Test Blog</title>
        <link>http://blog.example.com</link>
        <description>lalala</description>
        <generator>Mojolicious</generator>
        <item>
          <pubDate>Mon, 12 Jul 2010 20:42:00</pubDate>
          <title>Works!</title>
          <link>http://blog.example.com/test</link>
          <guid>http://blog.example.com/test</guid>
          <description>
            <![CDATA[<p>trololololo>]]>
          </description>
          <my:extension foo:id="works">
            <![CDATA[
              [awesome]]
            ]]>
          </my:extension>
        </item>
      </channel>
    </rss>
    """)
    ok(dom.xml, 'XML mode detected')
    is_ok(dom.find('rss')[0].attr('version'), '2.0', 'right version')
    is_deeply_ok(dom.at('title').ancestors().map('tag'), ['channel', 'rss'], 'right results')
    is_ok(dom.at('extension').attr('foo:id'), 'works', 'right id')
    like_ok(dom.at('#works').text, r'\[awesome\]\]', 'right text')
    like_ok(dom.at('[id="works"]').text, r'\[awesome\]\]', 'right text')
    is_ok(dom.find('description')[1].text, '<p>trololololo>', 'right text')
    is_ok(dom.at('pubDate').text, 'Mon, 12 Jul 2010 20:42:00', 'right text')
    like_ok(dom.at('[id*="ork"]').text, r'\[awesome\]\]', 'right text')
    like_ok(dom.at('[id*="orks"]').text, r'\[awesome\]\]', 'right text')
    like_ok(dom.at('[id*="work"]').text, r'\[awesome\]\]', 'right text')
    like_ok(dom.at('[id*="or"]').text, r'\[awesome\]\]', 'right text')
    ok(dom.at('rss').xml, 'XML mode active')
    ok(dom.at('extension').parent.xml, 'XML mode active')
    ok(dom.at('extension').root.xml, 'XML mode active')
    ok(dom.children('rss').first().xml, 'XML mode active')
    ok(dom.at('title').ancestors().first().xml, 'XML mode active')

    # Namespace
    dom = Pyjo.DOM.new("""
    <?xml version="1.0"?>
    <bk:book xmlns='uri:default-ns'
             xmlns:bk='uri:book-ns'
             xmlns:isbn='uri:isbn-ns'>
      <bk:title>Programming Perl</bk:title>
      <comment>rocks!</comment>
      <nons xmlns=''>
        <section>Nothing</section>
      </nons>
      <meta xmlns='uri:meta-ns'>
        <isbn:number>978-0596000271</isbn:number>
      </meta>
    </bk:book>
    """)
    ok(dom.xml, 'XML mode detected')
    is_ok(dom.namespace, None, 'no namespace')
    is_ok(dom.at('book comment').namespace, 'uri:default-ns', 'right namespace')
    is_ok(dom.at('book comment').text, 'rocks!', 'right text')
    is_ok(dom.at('book nons section').namespace, '', 'no namespace')
    is_ok(dom.at('book nons section').text, 'Nothing', 'right text')
    is_ok(dom.at('book meta number').namespace, 'uri:isbn-ns', 'right namespace')
    is_ok(dom.at('book meta number').text, '978-0596000271', 'right text')
    is_ok(dom.children('bk\\:book').first().attr('xmlns'), 'uri:default-ns', 'right attribute')
    is_ok(dom.children('book').first().attr('xmlns'), 'uri:default-ns', 'right attribute')
    is_ok(dom.children('k\\:book').first(), None, 'no result')
    is_ok(dom.children('ook').first(), None, 'no result')
    is_ok(dom.at('k\\:book'), None, 'no result')
    is_ok(dom.at('ook'), None, 'no result')
    is_ok(dom.at('[xmlns\\:bk]').attr('xmlns:bk'), 'uri:book-ns', 'right attribute')
    is_ok(dom.at('[bk]').attr('xmlns:bk'), 'uri:book-ns', 'right attribute')
    is_ok(dom.at('[bk]').attr('xmlns:bk'), 'uri:book-ns', 'right attribute')
    is_ok(dom.at('[bk]').attr('s:bk'), None, 'no attribute')
    is_ok(dom.at('[bk]').attr('bk'), None, 'no attribute')
    is_ok(dom.at('[bk]').attr('k'), None, 'no attribute')
    is_ok(dom.at('[s\\:bk]'), None, 'no result')
    is_ok(dom.at('[k]'), None, 'no result')
    is_ok(dom.at('number').ancestors('meta').first().attr('xmlns'), 'uri:meta-ns', 'right attribute')
    ok(dom.at('nons').matches('book > nons'), 'element did match')
    ok(not dom.at('title').matches('book > nons > section'), 'element did not match')

    # Dots
    dom = Pyjo.DOM.new("""
    <?xml version="1.0"?>
    <foo xmlns:foo.bar="uri:first">
      <bar xmlns:fooxbar="uri:second">
        <foo.bar:baz>First</fooxbar:baz>
        <fooxbar:ya.da>Second</foo.bar:ya.da>
      </bar>
    </foo>
    """)
    is_ok(dom.at('foo bar baz').text, 'First', 'right text')
    is_ok(dom.at('baz').namespace, 'uri:first', 'right namespace')
    is_ok(dom.at('foo bar ya\\.da').text, 'Second', 'right text')
    is_ok(dom.at('ya\\.da').namespace, 'uri:second', 'right namespace')
    is_ok(dom.at('foo').namespace, None, 'no namespace')
    is_ok(dom.at('[xml\\.s]'), None, 'no result')
    is_ok(dom.at('b\\.z'), None, 'no result')

    # Yadis
    dom = Pyjo.DOM.new("""
    <?xml version="1.0" encoding="UTF-8"?>
    <XRDS xmlns="xri://$xrds">
      <XRD xmlns="xri://$xrd*($v*2.0)">
        <Service>
          <Type>http://o.r.g/sso/2.0</Type>
        </Service>
        <Service>
          <Type>http://o.r.g/sso/1.0</Type>
        </Service>
      </XRD>
    </XRDS>
    """)
    ok(dom.xml, 'XML mode detected')
    is_ok(dom.at('XRDS').namespace, 'xri://$xrds', 'right namespace')
    is_ok(dom.at('XRD').namespace, 'xri://$xrd*($v*2.0)', 'right namespace')
    s = dom.find('XRDS XRD Service')
    is_ok(s[0].at('Type').text, 'http://o.r.g/sso/2.0', 'right text')
    is_ok(s[0].namespace, 'xri://$xrd*($v*2.0)', 'right namespace')
    is_ok(s[1].at('Type').text, 'http://o.r.g/sso/1.0', 'right text')
    is_ok(s[1].namespace, 'xri://$xrd*($v*2.0)', 'right namespace')
    throws_ok(lambda: s[2], IndexError, 'no result')
    is_ok(s.size, 2, 'right number of elements')

    # Yadis (roundtrip with namespace)
    yadis = """
    <?xml version="1.0" encoding="UTF-8"?>
    <xrds:XRDS xmlns="xri://$xrd*($v*2.0)" xmlns:xrds="xri://$xrds">
      <XRD>
        <Service>
          <Type>http://o.r.g/sso/3.0</Type>
        </Service>
        <xrds:Service>
          <Type>http://o.r.g/sso/4.0</Type>
        </xrds:Service>
      </XRD>
      <XRD>
        <Service>
          <Type test="23">http://o.r.g/sso/2.0</Type>
        </Service>
        <Service>
          <Type Test="23" test="24">http://o.r.g/sso/1.0</Type>
        </Service>
      </XRD>
    </xrds:XRDS>
    """
    dom = Pyjo.DOM.new(yadis)
    ok(dom.xml, 'XML mode detected')
    is_ok(dom.at('XRDS').namespace, 'xri://$xrds', 'right namespace')
    is_ok(dom.at('XRD').namespace, 'xri://$xrd*($v*2.0)', 'right namespace')
    s = dom.find('XRDS XRD Service')
    is_ok(s[0].at('Type').text, 'http://o.r.g/sso/3.0', 'right text')
    is_ok(s[0].namespace, 'xri://$xrd*($v*2.0)', 'right namespace')
    is_ok(s[1].at('Type').text, 'http://o.r.g/sso/4.0', 'right text')
    is_ok(s[1].namespace, 'xri://$xrds', 'right namespace')
    is_ok(s[2].at('Type').text, 'http://o.r.g/sso/2.0', 'right text')
    is_ok(s[2].namespace, 'xri://$xrd*($v*2.0)', 'right namespace')
    is_ok(s[3].at('Type').text, 'http://o.r.g/sso/1.0', 'right text')
    is_ok(s[3].namespace, 'xri://$xrd*($v*2.0)', 'right namespace')
    throws_ok(lambda: s[4], IndexError, 'no result')
    is_ok(s.size, 4, 'right number of elements')
    is_ok(dom.at('[Test="23"]').text, 'http://o.r.g/sso/1.0', 'right text')
    is_ok(dom.at('[test="23"]').text, 'http://o.r.g/sso/2.0', 'right text')
    is_ok(dom.find(r'xrds\:Service > Type')[0].text, 'http://o.r.g/sso/4.0', 'right text')
    throws_ok(lambda: dom.find(r'xrds\:Service > Type')[1], IndexError, 'no result')
    is_ok(dom.find(r'xrds\3AService > Type')[0].text, 'http://o.r.g/sso/4.0', 'right text')
    throws_ok(lambda: dom.find(r'xrds\3AService > Type')[1], IndexError, 'no result')
    is_ok(dom.find(r'xrds\3A Service > Type')[0].text, 'http://o.r.g/sso/4.0', 'right text')
    throws_ok(lambda: dom.find(r'xrds\3A Service > Type')[1], IndexError, 'no result')
    is_ok(dom.find(r'xrds\00003AService > Type')[0].text, 'http://o.r.g/sso/4.0', 'right text')
    throws_ok(lambda: dom.find(r'xrds\00003AService > Type')[1], IndexError, 'no result')
    is_ok(dom.find(r'xrds\00003A Service > Type')[0].text, 'http://o.r.g/sso/4.0', 'right text')
    throws_ok(lambda: dom.find(r'xrds\00003A Service > Type')[1], IndexError, 'no result')
    is_ok(dom, yadis, 'successful roundtrip')

    # Result and iterator order
    dom = Pyjo.DOM.new('<a><b>1</b></a><b>2</b><b>3</b>')
    numbers = []
    dom.find('b').each(lambda i, n: numbers.append([n, i.text]))
    is_deeply_ok(numbers, [[1, '1'], [2, '2'], [3, '3']], 'right order')

    # Attributes on multiple lines
    dom = Pyjo.DOM.new("<div test=23 id='a' \n class='x' foo=bar />")
    is_ok(dom.at('div.x').attr('test'), '23', 'right attribute')
    is_ok(dom.at('[foo="bar"]').attr('class'), 'x', 'right attribute')
    is_ok(dom.at('div').attr('baz', None).root.to_str(), '<div baz class="x" foo="bar" id="a" test="23"></div>', 'right result')

    # Markup characters in attribute values
    dom = Pyjo.DOM.new("""<div id="<a>" \n test='='>Test<div id='><' /></div>""")
    is_ok(dom.at('div[id="<a>"]').attr('test'), '=', 'right attribute')
    is_ok(dom.at('[id="<a>"]').text, 'Test', 'right text')
    is_ok(dom.at('[id="><"]').attr('id'), '><', 'right attribute')

    # Empty attributes
    dom = Pyjo.DOM.new("""<div test="" test2='' />""")
    is_ok(dom.at('div').attr('test'), '', 'empty attribute value')
    is_ok(dom.at('div').attr('test2'), '', 'empty attribute value')
    is_ok(dom.at('[test]').tag, 'div', 'right tag')
    is_ok(dom.at('[test2]').tag, 'div', 'right tag')
    is_ok(dom.at('[test3]'), None, 'no result')
    is_ok(dom.at('[test=""]').tag, 'div', 'right tag')
    is_ok(dom.at('[test2=""]').tag, 'div', 'right tag')
    is_ok(dom.at('[test3=""]'), None, 'no result')

    # Whitespaces before closing bracket
    dom = Pyjo.DOM.new('<div >content</div>')
    ok(dom.at('div'), 'tag found')
    is_ok(dom.at('div').text, 'content', 'right text')
    is_ok(dom.at('div').content, 'content', 'right text')

    # Class with hyphen
    dom = Pyjo.DOM.new('<div class="a">A</div><div class="a-1">A1</div>')
    div = []
    dom.find('.a').each(lambda i, n: div.append(i.text))
    is_deeply_ok(div, ['A'], 'found first element only')
    div = []
    dom.find('.a-1').each(lambda i, n: div.append(i.text))
    is_deeply_ok(div, ['A1'], 'found last element only')

    # Defined but false text
    dom = Pyjo.DOM.new('<div><div id="a">A</div><div id="b">B</div></div><div id="0">0</div>')
    div = []
    dom.find('div[id]').each(lambda i, n: div.append(i.text))
    is_deeply_ok(div, ['A', 'B', '0'], 'found all div elements with id')

    # Empty tags
    dom = Pyjo.DOM.new('<hr /><br/><br id="br"/><br />')
    is_ok(dom, '<hr><br><br id="br"><br>', 'right result')
    is_ok(dom.at('br').content, '', 'empty result')

    # Inner XML
    dom = Pyjo.DOM.new('<a>xxx<x>x</x>xxx</a>')
    is_ok(dom.at('a').content, 'xxx<x>x</x>xxx', 'right result')
    is_ok(dom.content, '<a>xxx<x>x</x>xxx</a>', 'right result')

    # Multiple selectors
    dom = Pyjo.DOM.new('<div id="a">A</div><div id="b">B</div><div id="c">C</div>')
    div = []
    dom.find('#a, #c').each(lambda i, n: div.append(i.text))
    is_deeply_ok(div, ['A', 'C'], 'found all div elements with the right ids')
    div = []
    dom.find('div#a, div#b').each(lambda i, n: div.append(i.text))
    is_deeply_ok(div, ['A', 'B'], 'found all div elements with the right ids')
    div = []
    dom.find('div[id="a"], div[id="c"]').each(lambda i, n: div.append(i.text))
    is_deeply_ok(div, ['A', 'C'], 'found all div elements with the right ids')
    dom = Pyjo.DOM.new(u'<div id="☃">A</div><div id="b">B</div><div id="♥x">C</div>')
    div = []
    dom.find(u'#☃, #♥x').each(lambda i, n: div.append(i.text))
    is_deeply_ok(div, ['A', 'C'], 'found all div elements with the right ids')
    div = []
    dom.find(u'div#☃, div#b').each(lambda i, n: div.append(i.text))
    is_deeply_ok(div, ['A', 'B'], 'found all div elements with the right ids')
    div = []
    dom.find(u'div[id="☃"], div[id="♥x"]').each(lambda i, n: div.append(i.text))
    is_deeply_ok(div, ['A', 'C'], 'found all div elements with the right ids')

    # Multiple attributes
    dom = Pyjo.DOM.new("""
    <div foo="bar" bar="baz">A</div>
    <div foo="bar">B</div>
    <div foo="bar" bar="baz">C</div>
    <div foo="baz" bar="baz">D</div>
    """)
    div = []
    dom.find('div[foo="bar"][bar="baz"]').each(lambda i, n: div.append(i.text))
    is_deeply_ok(div, ['A', 'C'], 'found all div elements with the right atributes')
    div = []
    dom.find('div[foo^="b"][foo$="r"]').each(lambda i, n: div.append(i.text))
    is_deeply_ok(div, ['A', 'B', 'C'], 'found all div elements with the right atributes')
    is_ok(dom.at('[foo="bar"]').previous, None, 'no previous sibling')
    is_ok(dom.at('[foo="bar"]').next.text, 'B', 'right text')
    is_ok(dom.at('[foo="bar"]').next.previous.text, 'A', 'right text')
    is_ok(dom.at('[foo="bar"]').next.next.next.next, None, 'no next sibling')

    # Pseudo classes
    dom = Pyjo.DOM.new("""
    <form action="/foo">
        <input type="text" name="user" value="test" />
        <input type="checkbox" checked="checked" name="groovy">
        <select name="a">
            <option value="b">b</option>
            <optgroup label="c">
                <option value="d">d</option>
                <option selected="selected" value="e">E</option>
                <option value="f">f</option>
            </optgroup>
            <option value="g">g</option>
            <option selected value="h">H</option>
        </select>
        <input type="submit" value="Ok!" />
        <input type="checkbox" checked name="I">
        <p id="content">test 123</p>
        <p id="no_content"><? test ?><!-- 123 --></p>
    </form>
    """)
    is_ok(dom.find(':root')[0].tag, 'form', 'right tag')
    is_ok(dom.find('*:root')[0].tag, 'form', 'right tag')
    is_ok(dom.find('form:root')[0].tag, 'form', 'right tag')
    throws_ok(lambda: dom.find(':root')[1], IndexError, 'no result')
    is_ok(dom.find(':checked')[0].attr('name'), 'groovy', 'right name')
    is_ok(dom.find('option:checked')[0].attr('value'), 'e', 'right value')
    is_ok(dom.find(':checked')[1].text, 'E', 'right text')
    is_ok(dom.find('*:checked')[1].text, 'E', 'right text')
    is_ok(dom.find(':checked')[2].text, 'H', 'right name')
    is_ok(dom.find(':checked')[3].attr('name'), 'I', 'right name')
    throws_ok(lambda: dom.find(':checked')[4], IndexError, 'no result')
    is_ok(dom.find('option[selected]')[0].attr('value'), 'e', 'right value')
    is_ok(dom.find('option[selected]')[1].text, 'H', 'right text')
    throws_ok(lambda: dom.find('option[selected]')[2], IndexError, 'no result')
    is_ok(dom.find(':checked[value="e"]')[0].text, 'E', 'right text')
    is_ok(dom.find('*:checked[value="e"]')[0].text, 'E', 'right text')
    is_ok(dom.find('option:checked[value="e"]')[0].text, 'E', 'right text')
    is_ok(dom.at('optgroup option:checked[value="e"]').text, 'E', 'right text')
    is_ok(dom.at('select option:checked[value="e"]').text, 'E', 'right text')
    is_ok(dom.at('select :checked[value="e"]').text, 'E', 'right text')
    is_ok(dom.at('optgroup > :checked[value="e"]').text, 'E', 'right text')
    is_ok(dom.at('select *:checked[value="e"]').text, 'E', 'right text')
    is_ok(dom.at('optgroup > *:checked[value="e"]').text, 'E', 'right text')
    throws_ok(lambda: dom.find(':checked[value="e"]')[1], IndexError, 'no result')
    is_ok(dom.find(':empty')[0].attr('name'), 'user', 'right name')
    is_ok(dom.find('input:empty')[0].attr('name'), 'user', 'right name')
    is_ok(dom.at(':empty[type^="ch"]').attr('name'), 'groovy', 'right name')
    is_ok(dom.at('p').attr('id'), 'content', 'right attribute')
    is_ok(dom.at('p:empty').attr('id'), 'no_content', 'right attribute')

    # More pseudo classes
    dom = Pyjo.DOM.new("""
    <ul>
        <li>A</li>
        <li>B</li>
        <li>C</li>
        <li>D</li>
        <li>E</li>
        <li>F</li>
        <li>G</li>
        <li>H</li>
    </ul>
    """)
    li = []
    dom.find('li:nth-child(odd)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['A', 'C', 'E', 'G'], 'found all odd li elements')
    li = []
    dom.find('li:NTH-CHILD(ODD)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['A', 'C', 'E', 'G'], 'found all odd li elements')
    li = []
    dom.find('li:nth-last-child(odd)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['B', 'D', 'F', 'H'], 'found all odd li elements')
    is_ok(dom.find(':nth-child(odd)')[0].tag, 'ul', 'right tag')
    is_ok(dom.find(':nth-child(odd)')[1].text, 'A', 'right text')
    is_ok(dom.find(':nth-child(1)')[0].tag, 'ul', 'right tag')
    is_ok(dom.find(':nth-child(1)')[1].text, 'A', 'right text')
    is_ok(dom.find(':nth-last-child(odd)')[0].tag, 'ul', 'right tag')
    is_ok(dom.find(':nth-last-child(odd)').last().text, 'H', 'right text')
    is_ok(dom.find(':nth-last-child(1)')[0].tag, 'ul', 'right tag')
    is_ok(dom.find(':nth-last-child(1)')[1].text, 'H', 'right text')
    li = []
    dom.find('li:nth-child(2n+1)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['A', 'C', 'E', 'G'], 'found all odd li elements')
    li = []
    dom.find('li:nth-child(2n + 1)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['A', 'C', 'E', 'G'], 'found all odd li elements')
    li = []
    dom.find('li:nth-last-child(2n+1)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['B', 'D', 'F', 'H'], 'found all odd li elements')
    li = []
    dom.find('li:nth-child(even)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['B', 'D', 'F', 'H'], 'found all even li elements')
    li = []
    dom.find('li:NTH-CHILD(EVEN)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['B', 'D', 'F', 'H'], 'found all even li elements')
    li = []
    dom.find('li:nth-last-child( even )').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['A', 'C', 'E', 'G'], 'found all even li elements')
    li = []
    dom.find('li:nth-child(2n+2)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['B', 'D', 'F', 'H'], 'found all even li elements')
    li = []
    dom.find('li:nTh-chILd(2N+2)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['B', 'D', 'F', 'H'], 'found all even li elements')
    li = []
    dom.find('li:nth-child( 2n + 2 )').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['B', 'D', 'F', 'H'], 'found all even li elements')
    li = []
    dom.find('li:nth-last-child(2n+2)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['A', 'C', 'E', 'G'], 'found all even li elements')
    li = []
    dom.find('li:nth-child(4n+1)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['A', 'E'], 'found the right li elements')
    li = []
    dom.find('li:nth-last-child(4n+1)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['D', 'H'], 'found the right li elements')
    li = []
    dom.find('li:nth-child(4n+4)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['D', 'H'], 'found the right li element')
    li = []
    dom.find('li:nth-last-child(4n+4)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['A', 'E'], 'found the right li element')
    li = []
    dom.find('li:nth-child(4n)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['D', 'H'], 'found the right li element')
    li = []
    dom.find('li:nth-child( 4n )').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['D', 'H'], 'found the right li element')
    li = []
    dom.find('li:nth-last-child(4n)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['A', 'E'], 'found the right li element')
    li = []
    dom.find('li:nth-child(5n-2)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['C', 'H'], 'found the right li element')
    li = []
    dom.find('li:nth-child( 5n - 2 )').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['C', 'H'], 'found the right li element')
    li = []
    dom.find('li:nth-last-child(5n-2)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['A', 'F'], 'found the right li element')
    li = []
    dom.find('li:nth-child(-n+3)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['A', 'B', 'C'], 'found first three li elements')
    li = []
    dom.find('li:nth-child( -n + 3 )').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['A', 'B', 'C'], 'found first three li elements')
    li = []
    dom.find('li:nth-last-child(-n+3)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['F', 'G', 'H'], 'found last three li elements')
    li = []
    dom.find('li:nth-child(-1n+3)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['A', 'B', 'C'], 'found first three li elements')
    li = []
    dom.find('li:nth-last-child(-1n+3)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['F', 'G', 'H'], 'found first three li elements')
    li = []
    dom.find('li:nth-child(3n)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['C', 'F'], 'found every third li elements')
    li = []
    dom.find('li:nth-last-child(3n)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['C', 'F'], 'found every third li elements')
    li = []
    dom.find('li:NTH-LAST-CHILD(3N)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['C', 'F'], 'found every third li elements')
    li = []
    dom.find('li:Nth-Last-Child(3N)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['C', 'F'], 'found every third li elements')
    li = []
    dom.find('li:nth-child(3)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['C'], 'found third li element')
    li = []
    dom.find('li:nth-last-child(3)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['F'], 'found third last li element')
    li = []
    dom.find('li:nth-child(1n+0)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['A', 'B', 'C', 'D', 'E', 'F', 'G'], 'found first three li elements')
    li = []
    dom.find('li:nth-child(n+0)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['A', 'B', 'C', 'D', 'E', 'F', 'G'], 'found first three li elements')
    li = []
    dom.find('li:NTH-CHILD(N+0)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['A', 'B', 'C', 'D', 'E', 'F', 'G'], 'found first three li elements')
    li = []
    dom.find('li:Nth-Child(N+0)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['A', 'B', 'C', 'D', 'E', 'F', 'G'], 'found first three li elements')
    li = []
    dom.find('li:nth-child(n)').each(lambda i, n: li.append(i.text))
    is_deeply_ok(li, ['A', 'B', 'C', 'D', 'E', 'F', 'G'], 'found first three li elements')

    # Even more pseudo classes
    dom = Pyjo.DOM.new(u"""
    <ul>
        <li>A</li>
        <p>B</p>
        <li class="test ♥">C</li>
        <p>D</p>
        <li>E</li>
        <li>F</li>
        <p>G</p>
        <li>H</li>
        <li>I</li>
    </ul>
    <div>
        <div class="☃">J</div>
    </div>
    <div>
        <a href="http://mojolicio.us">Mojo!</a>
        <div class="☃">K</div>
        <a href="http://mojolicio.us">Mojolicious!</a>
    </div>
    """)
    e = []
    dom.find('ul :nth-child(odd)').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['A', 'C', 'E', 'G', 'I'], 'found all odd elements')
    e = []
    dom.find('li:nth-of-type(odd)').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['A', 'E', 'H'], 'found all odd li elements')
    e = []
    dom.find('li:nth-last-of-type( odd )').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['C', 'F', 'I'], 'found all odd li elements')
    e = []
    dom.find('p:nth-of-type(odd)').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['B', 'G'], 'found all odd p elements')
    e = []
    dom.find('p:nth-last-of-type(odd)').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['B', 'G'], 'found all odd li elements')
    e = []
    dom.find('ul :nth-child(1)').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['A'], 'found first child')
    e = []
    dom.find('ul :first-child').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['A'], 'found first child')
    e = []
    dom.find('p:nth-of-type(1)').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['B'], 'found first child')
    e = []
    dom.find('p:first-of-type').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['B'], 'found first child')
    e = []
    dom.find('li:nth-of-type(1)').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['A'], 'found first child')
    e = []
    dom.find('li:first-of-type').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['A'], 'found first child')
    e = []
    dom.find('ul :nth-last-child(-n+1)').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['I'], 'found last child')
    e = []
    dom.find('ul :last-child').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['I'], 'found last child')
    e = []
    dom.find('p:nth-last-of-type(-n+1)').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['G'], 'found last child')
    e = []
    dom.find('p:last-of-type').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['G'], 'found last child')
    e = []
    dom.find('li:nth-last-of-type(-n+1)').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['I'], 'found last child')
    e = []
    dom.find('li:last-of-type').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['I'], 'found last child')
    e = []
    dom.find('ul :nth-child(-n+3):not(li)').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['B'], 'found first p element')
    e = []
    dom.find('ul :nth-child(-n+3):not(:first-child)').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['B', 'C'], 'found second and third element')
    e = []
    dom.find(u'ul :nth-child(-n+3):not(.♥)').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['A', 'B'], 'found first and second element')
    e = []
    dom.find(u'ul :nth-child(-n+3):not([class$="♥"])').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['A', 'B'], 'found first and second element')
    e = []
    dom.find(u'ul :nth-child(-n+3):not(li[class$="♥"])').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['A', 'B'], 'found first and second element')
    e = []
    dom.find(u'ul :nth-child(-n+3):not([class$="♥"][class^="test"])').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['A', 'B'], 'found first and second element')
    e = []
    dom.find(u'ul :nth-child(-n+3):not(*[class$="♥"])').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['A', 'B'], 'found first and second element')
    e = []
    dom.find('ul :nth-child(-n+3):not(:nth-child(-n+2))').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['C'], 'found third element')
    e = []
    dom.find('ul :nth-child(-n+3):not(:nth-child(1)):not(:nth-child(2))').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['C'], 'found third element')
    e = []
    dom.find(':only-child').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['J'], 'found only child')
    e = []
    dom.find('div :only-of-type').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['J', 'K'], 'found only child')
    e = []
    dom.find('div:only-child').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['J'], 'found only child')
    e = []
    dom.find('div div:only-of-type').each(lambda i, n: e.append(i.text))
    is_deeply_ok(e, ['J', 'K'], 'found only child')

    # Sibling combinator
    dom = Pyjo.DOM.new(u"""
    <ul>
        <li>A</li>
        <p>B</p>
        <li>C</li>
    </ul>
    <h1>D</h1>
    <p id="♥">E</p>
    <p id="☃">F</p>
    <div>G</div>
    """)
    is_ok(dom.at('li ~ p').text, 'B', 'right text')
    is_ok(dom.at('li + p').text, 'B', 'right text')
    is_ok(dom.at('h1 ~ p ~ p').text, 'F', 'right text')
    is_ok(dom.at('h1 + p ~ p').text, 'F', 'right text')
    is_ok(dom.at('h1 ~ p + p').text, 'F', 'right text')
    is_ok(dom.at('h1 + p + p').text, 'F', 'right text')
    is_ok(dom.at('h1+p+p').text, 'F', 'right text')
    is_ok(dom.at('ul > li ~ li').text, 'C', 'right text')
    is_ok(dom.at('ul li ~ li').text, 'C', 'right text')
    is_ok(dom.at('ul>li~li').text, 'C', 'right text')
    is_ok(dom.at('ul li li'), None, 'no result')
    is_ok(dom.at('ul ~ li ~ li'), None, 'no result')
    is_ok(dom.at('ul + li ~ li'), None, 'no result')
    is_ok(dom.at('ul > li + li'), None, 'no result')
    is_ok(dom.at('h1 ~ div').text, 'G', 'right text')
    is_ok(dom.at('h1 + div'), None, 'no result')
    is_ok(dom.at('p + div').text, 'G', 'right text')
    is_ok(dom.at('ul + h1 + p + p + div').text, 'G', 'right text')
    is_ok(dom.at('ul + h1 ~ p + div').text, 'G', 'right text')
    is_ok(dom.at(u'h1 ~ #♥').text, 'E', 'right text')
    is_ok(dom.at(u'h1 + #♥').text, 'E', 'right text')
    is_ok(dom.at(u'#♥ ~ #☃').text, 'F', 'right text')
    is_ok(dom.at(u'#♥ + #☃').text, 'F', 'right text')
    is_ok(dom.at(u'#♥ > #☃'), None, 'no result')
    is_ok(dom.at(u'#♥ #☃'), None, 'no result')
    is_ok(dom.at(u'#♥ + #☃ + :nth-last-child(1)').text, 'G', 'right text')
    is_ok(dom.at(u'#♥ ~ #☃ + :nth-last-child(1)').text, 'G', 'right text')
    is_ok(dom.at(u'#♥ + #☃ ~ :nth-last-child(1)').text, 'G', 'right text')
    is_ok(dom.at(u'#♥ ~ #☃ ~ :nth-last-child(1)').text, 'G', 'right text')
    is_ok(dom.at(u'#♥ + :nth-last-child(2)').text, 'F', 'right text')
    is_ok(dom.at(u'#♥ ~ :nth-last-child(2)').text, 'F', 'right text')
    is_ok(dom.at(u'#♥ + #☃ + *:nth-last-child(1)').text, 'G', 'right text')
    is_ok(dom.at(u'#♥ ~ #☃ + *:nth-last-child(1)').text, 'G', 'right text')
    is_ok(dom.at(u'#♥ + #☃ ~ *:nth-last-child(1)').text, 'G', 'right text')
    is_ok(dom.at(u'#♥ ~ #☃ ~ *:nth-last-child(1)').text, 'G', 'right text')
    is_ok(dom.at(u'#♥ + *:nth-last-child(2)').text, 'F', 'right text')
    is_ok(dom.at(u'#♥ ~ *:nth-last-child(2)').text, 'F', 'right text')

    # Adding nodes
    dom = Pyjo.DOM.new("""
    <ul>
        <li>A</li>
        <p>B</p>
        <li>C</li>
    </ul>
    <div>D</div>
    """)
    dom.at('li').append('<p>A1</p>23')
    is_ok(dom, """
    <ul>
        <li>A</li><p>A1</p>23
        <p>B</p>
        <li>C</li>
    </ul>
    <div>D</div>
    """, 'right result')
    dom.at('li').prepend('24').prepend('<div>A-1</div>25')
    is_ok(dom, """
    <ul>
        24<div>A-1</div>25<li>A</li><p>A1</p>23
        <p>B</p>
        <li>C</li>
    </ul>
    <div>D</div>
    """, 'right result')
    is_ok(dom.at('div').text, 'A-1', 'right text')
    is_ok(dom.at('iv'), None, 'no result')
    dom.prepend('l').prepend('alal').prepend('a')
    is_ok(dom, """
    <ul>
        24<div>A-1</div>25<li>A</li><p>A1</p>23
        <p>B</p>
        <li>C</li>
    </ul>
    <div>D</div>
    """, 'no change')
    dom.append('lalala')
    is_ok(dom, """
    <ul>
        24<div>A-1</div>25<li>A</li><p>A1</p>23
        <p>B</p>
        <li>C</li>
    </ul>
    <div>D</div>
    """, 'no change')
    dom.find('div').each(lambda i, n: i.append('works'))
    is_ok(dom, """
    <ul>
        24<div>A-1</div>works25<li>A</li><p>A1</p>23
        <p>B</p>
        <li>C</li>
    </ul>
    <div>D</div>works
    """, 'right result')
    dom.at('li').prepend_content('A3<p>A2</p>').prepend_content('A4')
    is_ok(dom.at('li').text, 'A4A3 A', 'right text')
    is_ok(dom, """
    <ul>
        24<div>A-1</div>works25<li>A4A3<p>A2</p>A</li><p>A1</p>23
        <p>B</p>
        <li>C</li>
    </ul>
    <div>D</div>works
    """, 'right result')
    dom.find('li')[1].append_content('<p>C2</p>C3').append_content(' C4').append_content('C5')
    is_ok(dom.find('li')[1].text, 'C C3 C4C5', 'right text')
    is_ok(dom, """
    <ul>
        24<div>A-1</div>works25<li>A4A3<p>A2</p>A</li><p>A1</p>23
        <p>B</p>
        <li>C<p>C2</p>C3 C4C5</li>
    </ul>
    <div>D</div>works
    """, 'right result')

    # Optional "head" and "body" tags
    dom = Pyjo.DOM.new("""
    <html>
      <head>
        <title>foo</title>
      <body>bar
    """)
    is_ok(dom.at('html > head > title').text, 'foo', 'right text')
    is_ok(dom.at('html > body').text, 'bar', 'right text')

    # Optional "li" tag
    dom = Pyjo.DOM.new("""
    <ul>
      <li>
        <ol>
          <li>F
          <li>G
        </ol>
      <li>A</li>
      <LI>B
      <li>C</li>
      <li>D
      <li>E
    </ul>
    """)
    is_ok(dom.find('ul > li > ol > li')[0].text, 'F', 'right text')
    is_ok(dom.find('ul > li > ol > li')[1].text, 'G', 'right text')
    is_ok(dom.find('ul > li')[1].text, 'A', 'right text')
    is_ok(dom.find('ul > li')[2].text, 'B', 'right text')
    is_ok(dom.find('ul > li')[3].text, 'C', 'right text')
    is_ok(dom.find('ul > li')[4].text, 'D', 'right text')
    is_ok(dom.find('ul > li')[5].text, 'E', 'right text')

    # Optional "p" tag
    dom = Pyjo.DOM.new("""
    <div>
      <p>A</p>
      <P>B
      <p>C</p>
      <p>D<div>X</div>
      <p>E<img src="foo.png">
      <p>F<br>G
      <p>H
    </div>
    """)
    is_ok(dom.find('div > p')[0].text, 'A', 'right text')
    is_ok(dom.find('div > p')[1].text, 'B', 'right text')
    is_ok(dom.find('div > p')[2].text, 'C', 'right text')
    is_ok(dom.find('div > p')[3].text, 'D', 'right text')
    is_ok(dom.find('div > p')[4].text, 'E', 'right text')
    is_ok(dom.find('div > p')[5].text, 'F G', 'right text')
    is_ok(dom.find('div > p')[6].text, 'H', 'right text')
    is_ok(dom.find('div > p > p').size, 0, 'no results')
    is_ok(dom.at('div > p > img').attr('src'), 'foo.png', 'right attribute')
    is_ok(dom.at('div > div').text, 'X', 'right text')

    # Optional "dt" and "dd" tags
    dom = Pyjo.DOM.new("""
    <dl>
      <dt>A</dt>
      <DD>B
      <dt>C</dt>
      <dd>D
      <dt>E
      <dd>F
    </dl>
    """)
    is_ok(dom.find('dl > dt')[0].text, 'A', 'right text')
    is_ok(dom.find('dl > dd')[0].text, 'B', 'right text')
    is_ok(dom.find('dl > dt')[1].text, 'C', 'right text')
    is_ok(dom.find('dl > dd')[1].text, 'D', 'right text')
    is_ok(dom.find('dl > dt')[2].text, 'E', 'right text')
    is_ok(dom.find('dl > dd')[2].text, 'F', 'right text')

    # Optional "rp" and "rt" tags
    dom = Pyjo.DOM.new("""
    <ruby>
      <rp>A</rp>
      <RT>B
      <rp>C</rp>
      <rt>D
      <rp>E
      <rt>F
    </ruby>
    """)
    is_ok(dom.find('ruby > rp')[0].text, 'A', 'right text')
    is_ok(dom.find('ruby > rt')[0].text, 'B', 'right text')
    is_ok(dom.find('ruby > rp')[1].text, 'C', 'right text')
    is_ok(dom.find('ruby > rt')[1].text, 'D', 'right text')
    is_ok(dom.find('ruby > rp')[2].text, 'E', 'right text')
    is_ok(dom.find('ruby > rt')[2].text, 'F', 'right text')

    # Optional "optgroup" and "option" tags
    dom = Pyjo.DOM.new("""
    <div>
      <optgroup>A
        <option id="foo">B
        <option>C</option>
        <option>D
      <OPTGROUP>E
        <option>F
      <optgroup>G
        <option>H
    </div>
    """)
    is_ok(dom.find('div > optgroup')[0].text, 'A', 'right text')
    is_ok(dom.find('div > optgroup > #foo')[0].text, 'B', 'right text')
    is_ok(dom.find('div > optgroup > option')[1].text, 'C', 'right text')
    is_ok(dom.find('div > optgroup > option')[2].text, 'D', 'right text')
    is_ok(dom.find('div > optgroup')[1].text, 'E', 'right text')
    is_ok(dom.find('div > optgroup > option')[3].text, 'F', 'right text')
    is_ok(dom.find('div > optgroup')[2].text, 'G', 'right text')
    is_ok(dom.find('div > optgroup > option')[4].text, 'H', 'right text')

    # Optional "colgroup" tag
    dom = Pyjo.DOM.new("""
    <table>
      <col id=morefail>
      <col id=fail>
      <colgroup>
        <col id=foo>
        <col class=foo>
      <colgroup>
        <col id=bar>
    </table>
    """)
    is_ok(dom.find('table > col')[0].attr('id'), 'morefail', 'right attribute')
    is_ok(dom.find('table > col')[1].attr('id'), 'fail', 'right attribute')
    is_ok(dom.find('table > colgroup > col')[0].attr('id'), 'foo', 'right attribute')
    is_ok(dom.find('table > colgroup > col')[1].attr('class'), 'foo', 'right attribute')
    is_ok(dom.find('table > colgroup > col')[2].attr('id'), 'bar', 'right attribute')

    # Optional "thead", "tbody", "tfoot", "tr", "th" and "td" tags
    dom = Pyjo.DOM.new("""
    <table>
      <thead>
        <tr>
          <th>A</th>
          <th>D
      <tfoot>
        <tr>
          <td>C
      <tbody>
        <tr>
          <td>B
    </table>
    """)
    is_ok(dom.at('table > thead > tr > th').text, 'A', 'right text')
    is_ok(dom.find('table > thead > tr > th')[1].text, 'D', 'right text')
    is_ok(dom.at('table > tbody > tr > td').text, 'B', 'right text')
    is_ok(dom.at('table > tfoot > tr > td').text, 'C', 'right text')

    # Optional "colgroup", "thead", "tbody", "tr", "th" and "td" tags
    dom = Pyjo.DOM.new("""
    <table>
      <col id=morefail>
      <col id=fail>
      <colgroup>
        <col id=foo />
        <col class=foo>
      <colgroup>
        <col id=bar>
      </colgroup>
      <thead>
        <tr>
          <th>A</th>
          <th>D
      <tbody>
        <tr>
          <td>B
      <tbody>
        <tr>
          <td>E
    </table>
    """)
    is_ok(dom.find('table > col')[0].attr('id'), 'morefail', 'right attribute')
    is_ok(dom.find('table > col')[1].attr('id'), 'fail', 'right attribute')
    is_ok(dom.find('table > colgroup > col')[0].attr('id'), 'foo', 'right attribute')
    is_ok(dom.find('table > colgroup > col')[1].attr('class'), 'foo', 'right attribute')
    is_ok(dom.find('table > colgroup > col')[2].attr('id'), 'bar', 'right attribute')
    is_ok(dom.at('table > thead > tr > th').text, 'A', 'right text')
    is_ok(dom.find('table > thead > tr > th')[1].text, 'D', 'right text')
    is_ok(dom.at('table > tbody > tr > td').text, 'B', 'right text')
    is_ok(dom.find('table > tbody > tr > td').map('text').join("\n"), "B\nE", 'right text')

    # Optional "colgroup", "tbody", "tr", "th" and "td" tags
    dom = Pyjo.DOM.new("""
    <table>
      <colgroup>
        <col id=foo />
        <col class=foo>
      <colgroup>
        <col id=bar>
      </colgroup>
      <tbody>
        <tr>
          <td>B
    </table>
    """)
    is_ok(dom.find('table > colgroup > col')[0].attr('id'), 'foo', 'right attribute')
    is_ok(dom.find('table > colgroup > col')[1].attr('class'), 'foo', 'right attribute')
    is_ok(dom.find('table > colgroup > col')[2].attr('id'), 'bar', 'right attribute')
    is_ok(dom.at('table > tbody > tr > td').text, 'B', 'right text')

    # Optional "tr" and "td" tags
    dom = Pyjo.DOM.new("""
    <table>
        <tr>
          <td>A
          <td>B</td>
        <tr>
          <td>C
        </tr>
        <tr>
          <td>D
    </table>
    """)
    is_ok(dom.find('table > tr > td')[0].text, 'A', 'right text')
    is_ok(dom.find('table > tr > td')[1].text, 'B', 'right text')
    is_ok(dom.find('table > tr > td')[2].text, 'C', 'right text')
    is_ok(dom.find('table > tr > td')[3].text, 'D', 'right text')

    # Real world table
    dom = Pyjo.DOM.new("""
    <html>
      <head>
        <title>Real World!</title>
      <body>
        <p>Just a test
        <table class=RealWorld>
          <thead>
            <tr>
              <th class=one>One
              <th class=two>Two
              <th class=three>Three
              <th class=four>Four
          <tbody>
            <tr>
              <td class=alpha>Alpha
              <td class=beta>Beta
              <td class=gamma><a href="#gamma">Gamma</a>
              <td class=delta>Delta
            <tr>
              <td class=alpha>Alpha Two
              <td class=beta>Beta Two
              <td class=gamma><a href="#gamma-two">Gamma Two</a>
              <td class=delta>Delta Two
        </table>
    """)
    is_ok(dom.find('html > head > title')[0].text, 'Real World!', 'right text')
    is_ok(dom.find('html > body > p')[0].text, 'Just a test', 'right text')
    is_ok(dom.find('p')[0].text, 'Just a test', 'right text')
    is_ok(dom.find('thead > tr > .three')[0].text, 'Three', 'right text')
    is_ok(dom.find('thead > tr > .four')[0].text, 'Four', 'right text')
    is_ok(dom.find('tbody > tr > .beta')[0].text, 'Beta', 'right text')
    is_ok(dom.find('tbody > tr > .gamma')[0].text, '', 'no text')
    is_ok(dom.find('tbody > tr > .gamma > a')[0].text, 'Gamma', 'right text')
    is_ok(dom.find('tbody > tr > .alpha')[1].text, 'Alpha Two', 'right text')
    is_ok(dom.find('tbody > tr > .gamma > a')[1].text, 'Gamma Two', 'right text')
    following = dom.find('tr > td:nth-child(1)').map('following', ':nth-child(even)').flatten().map('all_text')
    is_deeply_ok(following, ['Beta', 'Delta', 'Beta Two', 'Delta Two'], 'right results')

    # Real world list
    dom = Pyjo.DOM.new("""
    <html>
      <head>
        <title>Real World!</title>
      <body>
        <ul>
          <li>
            Test
            <br>
            123
            <p>

          <li>
            Test
            <br>
            321
            <p>
          <li>
            Test
            3
            2
            1
            <p>
        </ul>
    """)
    is_ok(dom.find('html > head > title')[0].text, 'Real World!', 'right text')
    is_ok(dom.find('body > ul > li')[0].text, 'Test 123', 'right text')
    is_ok(dom.find('body > ul > li > p')[0].text, '', 'no text')
    is_ok(dom.find('body > ul > li')[1].text, 'Test 321', 'right text')
    is_ok(dom.find('body > ul > li > p')[1].text, '', 'no text')
    is_ok(dom.find('body > ul > li')[1].all_text, 'Test 321', 'right text')
    is_ok(dom.find('body > ul > li > p')[1].all_text, '', 'no text')
    is_ok(dom.find('body > ul > li')[2].text, 'Test 3 2 1', 'right text')
    is_ok(dom.find('body > ul > li > p')[2].text, '', 'no text')
    is_ok(dom.find('body > ul > li')[2].all_text, 'Test 3 2 1', 'right text')
    is_ok(dom.find('body > ul > li > p')[2].all_text, '', 'no text')

    # Advanced whitespace trimming (punctuation)
    dom = Pyjo.DOM.new("""
    <html>
      <head>
        <title>Real World!</title>
      <body>
        <div>foo <strong>bar</strong>.</div>
        <div>foo<strong>, bar</strong>baz<strong>; yada</strong>.</div>
        <div>foo<strong>: bar</strong>baz<strong>? yada</strong>!</div>
    """)
    is_ok(dom.find('html > head > title')[0].text, 'Real World!', 'right text')
    is_ok(dom.find('body > div')[0].all_text, 'foo bar.', 'right text')
    is_ok(dom.find('body > div')[1].all_text, 'foo, bar baz; yada.', 'right text')
    is_ok(dom.find('body > div')[1].text, 'foo baz.', 'right text')
    is_ok(dom.find('body > div')[2].all_text, 'foo: bar baz? yada!', 'right text')
    is_ok(dom.find('body > div')[2].text, 'foo baz!', 'right text')

    # Real world JavaScript and CSS
    dom = Pyjo.DOM.new("""
    <html>
      <head>
        <style test=works>#style { foo: style('<test>') }</style>
        <script>
          if (a < b) {
            alert('<123>')
          }
        </script>
        < sCriPt two="23" >if (b > c) { alert('&<ohoh>') }< / scRiPt >
      <body>Foo!</body>
    """)
    is_ok(dom.find('html > body')[0].text, 'Foo!', 'right text')
    is_ok(dom.find('html > head > style')[0].text, "#style { foo: style('<test>') }", 'right text')
    is_ok(dom.find('html > head > script')[0].text, "\n          if (a < b) {\n            alert('<123>')\n          }\n        ", 'right text')
    is_ok(dom.find('html > head > script')[1].text, "if (b > c) { alert('&<ohoh>') }", 'right text')

    # More real world JavaScript
    dom = Pyjo.DOM.new("""
    <!DOCTYPE html>
    <html>
      <head>
        <title>Foo</title>
        <script src="/js/one.js"></script>
        <script src="/js/two.js"></script>
        <script src="/js/three.js"></script>
      </head>
      <body>Bar</body>
    </html>
    """)
    is_ok(dom.at('title').text, 'Foo', 'right text')
    is_ok(dom.find('html > head > script')[0].attr('src'), '/js/one.js', 'right attribute')
    is_ok(dom.find('html > head > script')[1].attr('src'), '/js/two.js', 'right attribute')
    is_ok(dom.find('html > head > script')[2].attr('src'), '/js/three.js', 'right attribute')
    is_ok(dom.find('html > head > script')[2].text, '', 'no text')
    is_ok(dom.at('html > body').text, 'Bar', 'right text')

    # Even more real world JavaScript
    dom = Pyjo.DOM.new("""
    <!DOCTYPE html>
    <html>
      <head>
        <title>Foo</title>
        <script src="/js/one.js"></script>
        <script src="/js/two.js"></script>
        <script src="/js/three.js">
      </head>
      <body>Bar</body>
    </html>
    """)
    is_ok(dom.at('title').text, 'Foo', 'right text')
    is_ok(dom.find('html > head > script')[0].attr('src'), '/js/one.js', 'right attribute')
    is_ok(dom.find('html > head > script')[1].attr('src'), '/js/two.js', 'right attribute')
    is_ok(dom.find('html > head > script')[2].attr('src'), '/js/three.js', 'right attribute')
    is_ok(dom.find('html > head > script')[2].text, '', 'no text')
    is_ok(dom.at('html > body').text, 'Bar', 'right text')

    # Inline DTD
    dom = Pyjo.DOM.new("""
    <?xml version="1.0"?>
    <!-- This is a Test! -.
    <!DOCTYPE root [
      <!ELEMENT root (#PCDATA)>
      <!ATTLIST root att CDATA #REQUIRED>
    ]>
    <root att="test">
      <![CDATA[<hello>world</hello>]]>
    </root>
    """)
    ok(dom.xml, 'XML mode detected')
    is_ok(dom.at('root').attr('att'), 'test', 'right attribute')
    is_ok(dom.tree[5][1], """ root [
      <!ELEMENT root (#PCDATA)>
      <!ATTLIST root att CDATA #REQUIRED>
    ]""", 'right doctype')
    is_ok(dom.at('root').text, '<hello>world</hello>', 'right text')
    dom = Pyjo.DOM.new("""
    <!doctype book
    SYSTEM "usr.dtd"
    [
      <!ENTITY test "yeah">
    ]>
    <foo />
    """)
    is_ok(dom.tree[2][1], """ book
    SYSTEM "usr.dtd"
    [
      <!ENTITY test "yeah">
    ]""", 'right doctype')
    ok(not dom.xml, 'XML mode not detected')
    is_ok(dom.at('foo'), '<foo></foo>', 'right element')
    dom = Pyjo.DOM.new("""
    <?xml version="1.0" encoding = 'utf-8'?>
    <!DOCTYPE foo [
      <!ELEMENT foo ANY>
      <!ATTLIST foo xml:lang CDATA #IMPLIED>
      <!ENTITY % e SYSTEM "myentities.ent">
      %myentities;
    ]  >
    <foo xml:lang="de">Check!</fOo>
    """)
    ok(dom.xml, 'XML mode detected')
    is_ok(dom.tree[4][1], """ foo [
      <!ELEMENT foo ANY>
      <!ATTLIST foo xml:lang CDATA #IMPLIED>
      <!ENTITY % e SYSTEM "myentities.ent">
      %myentities;
    ]  """, 'right doctype')
    is_ok(dom.at('foo').attr('xml:lang'), 'de', 'right attribute')
    is_ok(dom.at('foo').text, 'Check!', 'right text')
    dom = Pyjo.DOM.new("""
    <!DOCTYPE TESTSUITE PUBLIC "my.dtd" 'mhhh' [
      <!ELEMENT foo ANY>
      <!ATTLIST foo bar ENTITY 'true'>
      <!ENTITY system_entities SYSTEM 'systems.xml'>
      <!ENTITY leertaste '&#32;'>
      <!-- This is a comment -.
      <!NOTATION hmmm SYSTEM "hmmm">
    ]   >
    <?check for-nothing?>
    <foo bar='false'>&leertaste;!!!</foo>
    """)
    is_ok(dom.tree[2][1], """ TESTSUITE PUBLIC "my.dtd" \'mhhh\' [
      <!ELEMENT foo ANY>
      <!ATTLIST foo bar ENTITY \'true\'>
      <!ENTITY system_entities SYSTEM \'systems.xml\'>
      <!ENTITY leertaste \'&#32;\'>
      <!-- This is a comment -.
      <!NOTATION hmmm SYSTEM "hmmm">
    ]   """, 'right doctype')
    is_ok(dom.at('foo').attr('bar'), 'false', 'right attribute')

    # Broken "font" block and useless end tags
    dom = Pyjo.DOM.new("""
    <html>
      <head><title>Test</title></head>
      <body>
        <table>
          <tr><td><font>test</td></font></tr>
          </tr>
        </table>
      </body>
    </html>
    """)
    is_ok(dom.at('html > head > title').text, 'Test', 'right text')
    is_ok(dom.at('html body table tr td > font').text, 'test', 'right text')

    # Different broken "font" block
    dom = Pyjo.DOM.new("""
    <html>
      <head><title>Test</title></head>
      <body>
        <font>
        <table>
          <tr>
            <td>test1<br></td></font>
            <td>test2<br>
        </table>
      </body>
    </html>
    """)
    is_ok(dom.at('html > head > title').text, 'Test', 'right text')
    is_ok(dom.find('html > body > font > table > tr > td')[0].text, 'test1', 'right text')
    is_ok(dom.find('html > body > font > table > tr > td')[1].text, 'test2', 'right text')

    # Broken "font" and "div" blocks
    dom = Pyjo.DOM.new("""
    <html>
      <head><title>Test</title></head>
      <body>
        <font>
        <div>test1<br>
          <div>test2<br></font>
        </div>
      </body>
    </html>
    """)
    is_ok(dom.at('html head title').text, 'Test', 'right text')
    is_ok(dom.at('html body font > div').text, 'test1', 'right text')
    is_ok(dom.at('html body font > div > div').text, 'test2', 'right text')

    # Broken "div" blocks
    dom = Pyjo.DOM.new("""
    <html>
      <head><title>Test</title></head>
      <body>
        <div>
        <table>
          <tr><td><div>test</td></div></tr>
          </div>
        </table>
      </body>
    </html>
    """)
    is_ok(dom.at('html head title').text, 'Test', 'right text')
    is_ok(dom.at('html body div table tr td > div').text, 'test', 'right text')

    # And another broken "font" block
    dom = Pyjo.DOM.new("""
    <html>
      <head><title>Test</title></head>
      <body>
        <table>
          <tr>
            <td><font><br>te<br>st<br>1</td></font>
            <td>x1<td><img>tes<br>t2</td>
            <td>x2<td><font>t<br>est3</font></td>
          </tr>
        </table>
      </body>
    </html>
    """)
    is_ok(dom.at('html > head > title').text, 'Test', 'right text')
    is_ok(dom.find('html body table tr > td > font')[0].text, 'te st 1', 'right text')
    is_ok(dom.find('html body table tr > td')[1].text, 'x1', 'right text')
    is_ok(dom.find('html body table tr > td')[2].text, 'tes t2', 'right text')
    is_ok(dom.find('html body table tr > td')[3].text, 'x2', 'right text')
    throws_ok(lambda: dom.find('html body table tr > td')[5], IndexError, 'no result')
    is_ok(dom.find('html body table tr > td').size, 5, 'right number of elements')
    is_ok(dom.find('html body table tr > td > font')[1].text, 't est3', 'right text')
    throws_ok(lambda: dom.find('html body table tr > td > font')[2], IndexError, 'no result')
    is_ok(dom.find('html body table tr > td > font').size, 2, 'right number of elements')
    is_ok(dom, """
    <html>
      <head><title>Test</title></head>
      <body>
        <table>
          <tr>
            <td><font><br>te<br>st<br>1</font></td>
            <td>x1</td><td><img>tes<br>t2</td>
            <td>x2</td><td><font>t<br>est3</font></td>
          </tr>
        </table>
      </body>
    </html>
    """, 'right result')

    # A collection of wonderful screwups
    dom = Pyjo.DOM.new("""
    <!DOCTYPE html>
    <html lang="en">
      <head><title>Wonderful Screwups</title></head>
      <body id="screw-up">
        <div>
          <div class="ewww">
            <a href="/test" target='_blank'><img src="/test.png"></a>
            <a href='/real bad' screwup: http://localhost/bad' target='_blank'>
              <img src="/test2.png">
          </div>
          </mt:If>
        </div>
        <b>>la<>la<<>>la<</b>
      </body>
    </html>
    """)
    is_ok(dom.at('#screw-up > b').text, '>la<>la<<>>la<', 'right text')
    is_ok(dom.at('#screw-up .ewww > a > img').attr('src'), '/test.png', 'right attribute')
    is_ok(dom.find('#screw-up .ewww > a > img')[1].attr('src'), '/test2.png', 'right attribute')
    throws_ok(lambda: dom.find('#screw-up .ewww > a > img')[2], IndexError, 'no result')
    is_ok(dom.find('#screw-up .ewww > a > img').size, 2, 'right number of elements')

    # Broken "br" tag
    dom = Pyjo.DOM.new('<br< abc abc abc abc abc abc abc abc<p>Test</p>')
    is_ok(dom.at('p').text, 'Test', 'right text')

    # Modifying an XML document
    dom = Pyjo.DOM.new("""
    <?xml version='1.0' encoding='UTF-8'?>
    <XMLTest />
    """)
    ok(dom.xml, 'XML mode detected')
    dom.at('XMLTest').set(content='<Element />')
    element = dom.at('Element')
    is_ok(element.tag, 'Element', 'right tag')
    ok(element.xml, 'XML mode active')
    element = dom.at('XMLTest').children()[0]
    is_ok(element.tag, 'Element', 'right child')
    is_ok(element.parent.tag, 'XMLTest', 'right parent')
    ok(element.root.xml, 'XML mode active')
    dom.replace('<XMLTest2 /><XMLTest3 just="works" />')
    ok(dom.xml, 'XML mode active')
    is_ok(dom, '<XMLTest2 /><XMLTest3 just="works" />', 'right result')

    # Ensure HTML semantics
    # TODO incompability with Mojo?
    ok(not Pyjo.DOM.new().set(xml=False).parse('<?xml version="1.0"?>').xml, 'XML mode not detected')
    dom = Pyjo.DOM.new().set(xml=False).parse('<?xml version="1.0"?><br><div>Test</div>')
    is_ok(dom.at('div:root').text, 'Test', 'right text')

    # Ensure XML semantics
    ok(Pyjo.DOM.new().set(xml=True).parse('<foo />').xml, 'XML mode active')
    dom = Pyjo.DOM.new("""
    <?xml version='1.0' encoding='UTF-8'?>
    <script>
      <table>
        <td>
          <tr><thead>foo</thead></tr>
        </td>
        <td>
          <tr><thead>bar</thead></tr>
        </td>
      </table>
    </script>
    """)
    is_ok(dom.find('table > td > tr > thead')[0].text, 'foo', 'right text')
    is_ok(dom.find('script > table > td > tr > thead')[1].text, 'bar', 'right text')
    throws_ok(lambda: dom.find('table > td > tr > thead')[2], IndexError, 'no result')
    is_ok(dom.find('table > td > tr > thead').size, 2, 'right number of elements')

    # Ensure XML semantics again
    dom = Pyjo.DOM.new().set(xml=True).parse("""
    <table>
      <td>
        <tr><thead>foo<thead></tr>
      </td>
      <td>
        <tr><thead>bar<thead></tr>
      </td>
    </table>
    """)
    is_ok(dom.find('table > td > tr > thead')[0].text, 'foo', 'right text')
    is_ok(dom.find('table > td > tr > thead')[1].text, 'bar', 'right text')
    throws_ok(lambda: dom.find('table > td > tr > thead')[2], IndexError, 'no result')
    is_ok(dom.find('table > td > tr > thead').size, 2, 'right number of elements')

    # Nested tables
    dom = Pyjo.DOM.new("""
    <table id="foo">
      <tr>
        <td>
          <table id="bar">
            <tr>
              <td>baz</td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
    """)
    is_ok(dom.find('#foo > tr > td > #bar > tr >td')[0].text, 'baz', 'right text')
    is_ok(dom.find('table > tr > td > table > tr >td')[0].text, 'baz', 'right text')

    # Nested find
    dom.parse("""
    <c>
      <a>foo</a>
      <b>
        <a>bar</a>
        <c>
          <a>baz</a>
          <d>
            <a>yada</a>
          </d>
        </c>
      </b>
    </c>
    """)
    results = []
    dom.find('b').each(lambda i, n:
                       i.find('a').each(lambda i, n: results.append(i.text)))
    is_deeply_ok(results, ['bar', 'baz', 'yada'], 'right results')
    results = []
    dom.find('a').each(lambda i, n: results.append(i.text))
    is_deeply_ok(results, ['foo', 'bar', 'baz', 'yada'], 'right results')
    results = []
    dom.find('b').each(lambda i, n:
                       i.find('c a').each(lambda i, n: results.append(i.text)))
    is_deeply_ok(results, ['baz', 'yada'], 'right results')
    is_ok(dom.at('b').at('a').text, 'bar', 'right text')
    is_ok(dom.at('c > b > a').text, 'bar', 'right text')
    is_ok(dom.at('b').at('c > b > a'), None, 'no result')

    # Append and prepend content
    dom = Pyjo.DOM.new('<a><b>Test<c /></b></a>')
    dom.at('b').append_content('<d />')
    is_ok(dom.children()[0].tag, 'a', 'right element')
    is_ok(dom.all_text, 'Test', 'right text')
    is_ok(dom.at('c').parent.tag, 'b', 'right element')
    is_ok(dom.at('d').parent.tag, 'b', 'right element')
    dom.at('b').prepend_content('<e>Mojo</e>')
    is_ok(dom.at('e').parent.tag, 'b', 'right element')
    is_ok(dom.all_text, 'Mojo Test', 'right text')

    # Wrap elements
    dom = Pyjo.DOM.new('<a>Test</a>')
    is_ok(dom.wrap('<b></b>').type, 'root', 'right node')
    is_ok(dom, '<b><a>Test</a></b>', 'right result')
    is_ok(dom.at('b').strip().at('a').wrap('A').tag, 'a', 'right element')
    is_ok(dom, '<a>Test</a>', 'right result')
    is_ok(dom.at('a').wrap('<b></b>').tag, 'a', 'right element')
    is_ok(dom, '<b><a>Test</a></b>', 'right result')
    is_ok(dom.at('a').wrap('C<c><d>D</d><e>E</e></c>F').parent.tag, 'd', 'right element')
    is_ok(dom, '<b>C<c><d>D<a>Test</a></d><e>E</e></c>F</b>', 'right result')

    # Wrap content
    dom = Pyjo.DOM.new('<a>Test</a>')
    is_ok(dom.at('a').wrap_content('A').tag, 'a', 'right element')
    is_ok(dom, '<a>Test</a>', 'right result')
    is_ok(dom.wrap_content('<b></b>').type, 'root', 'right node')
    is_ok(dom, '<b><a>Test</a></b>', 'right result')
    is_ok(dom.at('b').strip().at('a').set(tag='e:a').wrap_content('1<b c="d"></b>').tag, 'e:a', 'right element')
    is_ok(dom, '<e:a>1<b c="d">Test</b></e:a>', 'right result')
    is_ok(dom.at('a').wrap_content('C<c><d>D</d><e>E</e></c>F').parent.type, 'root', 'right node')
    is_ok(dom, '<e:a>C<c><d>D1<b c="d">Test</b></d><e>E</e></c>F</e:a>', 'right result')

    # Broken "div" in "td"
    dom = Pyjo.DOM.new("""
    <table>
      <tr>
        <td><div id="A"></td>
        <td><div id="B"></td>
      </tr>
    </table>
    """)
    is_ok(dom.find('table tr td')[0].at('div').attr('id'), 'A', 'right attribute')
    is_ok(dom.find('table tr td')[1].at('div').attr('id'), 'B', 'right attribute')
    throws_ok(lambda: dom.find('table tr td')[2], IndexError, 'no result')
    is_ok(dom.find('table tr td').size, 2, 'right number of elements')
    is_ok(dom, """
    <table>
      <tr>
        <td><div id="A"></div></td>
        <td><div id="B"></div></td>
      </tr>
    </table>
    """, 'right result')

    # Preformatted text
    dom = Pyjo.DOM.new("""
    <div>
      looks
      <pre><code>like
      it
        really</code>
      </pre>
      works
    </div>
    """)
    is_ok(dom.text, '', 'no text')
    is_ok(dom.raw_text, "\n    \n    ", 'right text')
    is_ok(dom.all_text, "looks like\n      it\n        really\n      works", 'right text')
    is_ok(dom.all_raw_text, "\n    \n      looks\n      like\n      it\n        really\n      \n      works\n    \n    ", 'right text')
    is_ok(dom.at('div').text, 'looks works', 'right text')
    is_ok(dom.at('div').raw_text, "\n      looks\n      \n      works\n    ", 'right text')
    is_ok(dom.at('div').all_text, "looks like\n      it\n        really\n      works", 'right text')
    is_ok(dom.at('div').all_raw_text, "\n      looks\n      like\n      it\n        really\n      \n      works\n    ", 'right text')
    is_ok(dom.at('div pre').text, "\n      ", 'right text')
    is_ok(dom.at('div pre').raw_text, "\n      ", 'right text')
    is_ok(dom.at('div pre').all_text, "like\n      it\n        really\n      ", 'right text')
    is_ok(dom.at('div pre').all_raw_text, "like\n      it\n        really\n      ", 'right text')
    is_ok(dom.at('div pre code').text, "like\n      it\n        really", 'right text')
    is_ok(dom.at('div pre code').raw_text, "like\n      it\n        really", 'right text')
    is_ok(dom.at('div pre code').all_text, "like\n      it\n        really", 'right text')
    is_ok(dom.at('div pre code').all_raw_text, "like\n      it\n        really", 'right text')

    # PoCo example with whitespace sensitive text
    dom = Pyjo.DOM.new("""
    <?xml version="1.0" encoding="UTF-8"?>
    <response>
      <entry>
        <id>1286823</id>
        <displayName>Homer Simpson</displayName>
        <addresses>
          <type>home</type>
          <formatted><![CDATA[742 Evergreen Terrace
    Springfield, VT 12345 USA]]></formatted>
        </addresses>
      </entry>
      <entry>
        <id>1286822</id>
        <displayName>Marge Simpson</displayName>
        <addresses>
          <type>home</type>
          <formatted>742 Evergreen Terrace
    Springfield, VT 12345 USA</formatted>
        </addresses>
      </entry>
    </response>
    """)
    is_ok(dom.find('entry')[0].at('displayName').text, 'Homer Simpson', 'right text')
    is_ok(dom.find('entry')[0].at('id').text, '1286823', 'right text')
    is_ok(dom.find('entry')[0].at('addresses').children('type')[0].text, 'home', 'right text')
    is_ok(dom.find('entry')[0].at('addresses formatted').text, "742 Evergreen Terrace\n    Springfield, VT 12345 USA", 'right text')
    is_ok(dom.find('entry')[0].at('addresses formatted').raw_text, "742 Evergreen Terrace\n    Springfield, VT 12345 USA", 'right text')
    is_ok(dom.find('entry')[1].at('displayName').text, 'Marge Simpson', 'right text')
    is_ok(dom.find('entry')[1].at('id').text, '1286822', 'right text')
    is_ok(dom.find('entry')[1].at('addresses').children('type')[0].text, 'home', 'right text')
    is_ok(dom.find('entry')[1].at('addresses formatted').text, '742 Evergreen Terrace Springfield, VT 12345 USA', 'right text')
    is_ok(dom.find('entry')[1].at('addresses formatted').raw_text, "742 Evergreen Terrace\n    Springfield, VT 12345 USA", 'right text')
    throws_ok(lambda: dom.find('entry')[2], IndexError, 'no result')
    is_ok(dom.find('entry').size, 2, 'right number of elements')

    # Find attribute with hyphen in name and value
    dom = Pyjo.DOM.new("""
    <html>
      <head><meta http-equiv="content-type" content="text/html"></head>
    </html>
    """)
    is_ok(dom.find('[http-equiv]')[0].attr('content'), 'text/html', 'right attribute')
    throws_ok(lambda: dom.find('[http-equiv]')[1], IndexError, 'no result')
    is_ok(dom.find('[http-equiv="content-type"]')[0].attr('content'), 'text/html', 'right attribute')
    throws_ok(lambda: dom.find('[http-equiv="content-type"]')[1], IndexError, 'no result')
    is_ok(dom.find('[http-equiv^="content-"]')[0].attr('content'), 'text/html', 'right attribute')
    throws_ok(lambda: dom.find('[http-equiv^="content-"]')[1], IndexError, 'no result')
    is_ok(dom.find('head > [http-equiv$="-type"]')[0].attr('content'), 'text/html', 'right attribute')
    throws_ok(lambda: dom.find('head > [http-equiv$="-type"]')[1], IndexError, 'no result')

    # Find "0" attribute value and unescape relaxed entity
    dom = Pyjo.DOM.new("""
    <a accesskey="0">Zero</a>
    <a accesskey="1">O&gTn&gte</a>
    """)
    is_ok(dom.find('a[accesskey]')[0].text, 'Zero', 'right text')
    is_ok(dom.find('a[accesskey]')[1].text, 'O&gTn>e', 'right text')
    throws_ok(lambda: dom.find('a[accesskey]')[2], IndexError, 'no result')
    is_ok(dom.find('a[accesskey=0]')[0].text, 'Zero', 'right text')
    throws_ok(lambda: dom.find('a[accesskey=0]')[1], IndexError, 'no result')
    is_ok(dom.find('a[accesskey^=0]')[0].text, 'Zero', 'right text')
    throws_ok(lambda: dom.find('a[accesskey^=0]')[1], IndexError, 'no result')
    is_ok(dom.find('a[accesskey$=0]')[0].text, 'Zero', 'right text')
    throws_ok(lambda: dom.find('a[accesskey$=0]')[1], IndexError, 'no result')
    is_ok(dom.find('a[accesskey~=0]')[0].text, 'Zero', 'right text')
    throws_ok(lambda: dom.find('a[accesskey~=0]')[1], IndexError, 'no result')
    is_ok(dom.find('a[accesskey*=0]')[0].text, 'Zero', 'right text')
    throws_ok(lambda: dom.find('a[accesskey*=0]')[1], IndexError, 'no result')
    is_ok(dom.find('a[accesskey=1]')[0].text, 'O&gTn>e', 'right text')
    throws_ok(lambda: dom.find('a[accesskey=1]')[1], IndexError, 'no result')
    is_ok(dom.find('a[accesskey^=1]')[0].text, 'O&gTn>e', 'right text')
    throws_ok(lambda: dom.find('a[accesskey^=1]')[1], IndexError, 'no result')
    is_ok(dom.find('a[accesskey$=1]')[0].text, 'O&gTn>e', 'right text')
    throws_ok(lambda: dom.find('a[accesskey$=1]')[1], IndexError, 'no result')
    is_ok(dom.find('a[accesskey~=1]')[0].text, 'O&gTn>e', 'right text')
    throws_ok(lambda: dom.find('a[accesskey~=1]')[1], IndexError, 'no result')
    is_ok(dom.find('a[accesskey*=1]')[0].text, 'O&gTn>e', 'right text')
    throws_ok(lambda: dom.find('a[accesskey*=1]')[1], IndexError, 'no result')
    is_ok(dom.at('a[accesskey*="."]'), None, 'no result')

    # Empty attribute value
    dom = Pyjo.DOM.new("""
    <foo bar=>
      test
    </foo>
    <bar>after</bar>
    """)
    is_ok(dom.tree[0], 'root', 'right element')
    is_ok(dom.tree[2][0], 'tag', 'right element')
    is_ok(dom.tree[2][1], 'foo', 'right tag')
    is_deeply_ok(dom.tree[2][2], {'bar': ''}, 'right attributes')
    is_ok(dom.tree[2][4][0], 'text', 'right element')
    is_ok(dom.tree[2][4][1], "\n      test\n    ", 'right text')
    is_ok(dom.tree[4][0], 'tag', 'right element')
    is_ok(dom.tree[4][1], 'bar', 'right tag')
    is_ok(dom.tree[4][4][0], 'text', 'right element')
    is_ok(dom.tree[4][4][1], 'after', 'right text')
    is_ok(dom, """
    <foo bar="">
      test
    </foo>
    <bar>after</bar>
    """, 'right result')

    # Case-insensitive attribute values
    dom = Pyjo.DOM.new("""
    <p class="foo">A</p>
    <p class="foo bAr">B</p>
    <p class="FOO">C</p>
    """)
    is_ok(dom.find('.foo').map('text').join(','), 'A,B', 'right result')
    is_ok(dom.find('.FOO').map('text').join(','), 'C', 'right result')
    is_ok(dom.find('[class=foo]').map('text').join(','), 'A', 'right result')
    is_ok(dom.find('[class=foo i]').map('text').join(','), 'A,C', 'right result')
    is_ok(dom.find('[class="foo" i]').map('text').join(','), 'A,C', 'right result')
    is_ok(dom.find('[class="foo bar"]').size, 0, 'no results')
    is_ok(dom.find('[class="foo bar" i]').map('text').join(','), 'B', 'right result')
    is_ok(dom.find('[class~=foo]').map('text').join(','), 'A,B', 'right result')
    is_ok(dom.find('[class~=foo i]').map('text').join(','), 'A,B,C', 'right result')
    is_ok(dom.find('[class*=f]').map('text').join(','), 'A,B', 'right result')
    is_ok(dom.find('[class*=f i]').map('text').join(','), 'A,B,C', 'right result')
    is_ok(dom.find('[class^=F]').map('text').join(','), 'C', 'right result')
    is_ok(dom.find('[class^=F i]').map('text').join(','), 'A,B,C', 'right result')
    is_ok(dom.find('[class$=O]').map('text').join(','), 'C', 'right result')
    is_ok(dom.find('[class$=O i]').map('text').join(','), 'A,C', 'right result')

    # Nested description lists
    dom = Pyjo.DOM.new("""
    <dl>
      <dt>A</dt>
      <DD>
        <dl>
          <dt>B
          <dd>C
        </dl>
      </dd>
    </dl>
    """)
    is_ok(dom.find('dl > dd > dl > dt')[0].text, 'B', 'right text')
    is_ok(dom.find('dl > dd > dl > dd')[0].text, 'C', 'right text')
    is_ok(dom.find('dl > dt')[0].text, 'A', 'right text')

    # Nested lists
    dom = Pyjo.DOM.new("""
    <div>
      <ul>
        <li>
          A
          <ul>
            <li>B</li>
            C
          </ul>
        </li>
      </ul>
    </div>
    """)
    is_ok(dom.find('div > ul > li')[0].text, 'A', 'right text')
    throws_ok(lambda: dom.find('div > ul > li')[1], IndexError, 'no result')
    is_ok(dom.find('div > ul li')[0].text, 'A', 'right text')
    is_ok(dom.find('div > ul li')[1].text, 'B', 'right text')
    throws_ok(lambda: dom.find('div > ul li')[2], IndexError, 'no result')
    is_ok(dom.find('div > ul ul')[0].text, 'C', 'right text')
    throws_ok(lambda: dom.find('div > ul ul')[1], IndexError, 'no result')

    # Slash between attributes
    dom = Pyjo.DOM.new('<input /type=checkbox / value="/a/" checked/><br/>')
    is_deeply_ok(dom.at('input').attr(), {'type': 'checkbox', 'value': '/a/', 'checked': None}, 'right attributes')
    is_ok(dom, '<input checked type="checkbox" value="/a/"><br>', 'right result')

    # Dot and hash in class and id attributes
    dom = Pyjo.DOM.new('<p class="a#b.c">A</p><p id="a#b.c">B</p>')
    is_ok(dom.at('p.a\\#b\\.c').text, 'A', 'right text')
    is_ok(dom.at(':not(p.a\\#b\\.c)').text, 'B', 'right text')
    is_ok(dom.at('p#a\\#b\\.c').text, 'B', 'right text')
    is_ok(dom.at(':not(p#a\\#b\\.c)').text, 'A', 'right text')

    # Extra whitespace
    dom = Pyjo.DOM.new('< span>a< /span><b >b</b><span >c</ span>')
    is_ok(dom.at('span').text, 'a', 'right text')
    is_ok(dom.at('span + b').text, 'b', 'right text')
    is_ok(dom.at('b + span').text, 'c', 'right text')
    is_ok(dom, '<span>a</span><b>b</b><span>c</span>', 'right result')

    # "0"
    dom = Pyjo.DOM.new('0')
    is_ok(dom, '0', 'right result')
    dom.append_content(u'☃')
    is_ok(dom, u'0☃', 'right result')
    is_ok(dom.parse('<!DOCTYPE 0>'), '<!DOCTYPE 0>', 'successful roundtrip')
    is_ok(dom.parse('<!--0-->'), '<!--0-->', 'successful roundtrip')
    is_ok(dom.parse('<![CDATA[0]]>'), '<![CDATA[0]]>', 'successful roundtrip')
    is_ok(dom.parse('<?0?>'), '<?0?>', 'successful roundtrip')

    # Not self-closing
    dom = Pyjo.DOM.new('<div />< div ><pre />test</div >123')
    is_ok(dom.at('div > div > pre').text, 'test', 'right text')
    is_ok(dom, '<div><div><pre>test</pre></div>123</div>', 'right result')
    dom = Pyjo.DOM.new('<p /><svg><circle /><circle /></svg>')
    is_ok(dom.find('p > svg > circle').size, 2, 'two circles')
    is_ok(dom, '<p><svg><circle></circle><circle></circle></svg></p>', 'right result')

    # "image"
    dom = Pyjo.DOM.new('<image src="foo.png">test')
    is_ok(dom.at('img').attr('src'), 'foo.png', 'right attribute')
    is_ok(dom, '<img src="foo.png">test', 'right result')

    # "title"
    dom = Pyjo.DOM.new('<title> <p>test&lt;</title>')
    is_ok(dom.at('title').text, ' <p>test<', 'right text')
    is_ok(dom, '<title> <p>test<</title>', 'right result')

    # "textarea"
    dom = Pyjo.DOM.new('<textarea id="a"> <p>test&lt;</textarea>')
    is_ok(dom.at('textarea#a').text, ' <p>test<', 'right text')
    is_ok(dom, '<textarea id="a"> <p>test<</textarea>', 'right result')

    # Comments
    dom = Pyjo.DOM.new("""
    <!-- HTML5 -->
    <!-- bad idea -- HTML5 -->
    <!-- HTML4 -- >
    <!-- bad idea -- HTML4 -- >
    """)
    is_ok(dom.tree[2][1], ' HTML5 ', 'right comment')
    is_ok(dom.tree[4][1], ' bad idea -- HTML5 ', 'right comment')
    is_ok(dom.tree[6][1], ' HTML4 ', 'right comment')
    is_ok(dom.tree[8][1], ' bad idea -- HTML4 ', 'right comment')

    # Huge number of attributes
    dom = Pyjo.DOM.new('<div ' + ('a=b ' * 32768) + '>Test</div>')
    is_ok(dom.at('div[a=b]').text, 'Test', 'right text')

    # Huge number of nested tags
    huge = ('<a>' * 100) + 'works' + ('</a>' * 100)
    dom = Pyjo.DOM.new(huge)
    is_ok(dom.all_text, 'works', 'right text')
    is_ok(dom, huge, 'right result')

    done_testing()
