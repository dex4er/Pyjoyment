r"""
Pyjo.DOM - Minimalistic HTML/XML DOM parser with CSS selectors
==============================================================
::

    import Pyjo.DOM

    # Parse
    dom = Pyjo.DOM.new('<div><p id="a">Test</p><p id="b">123</p></div>')

    # Find
    print(dom.at('#b').text)
    print(dom.find('p').map('text').join("\n"))
    dom.find('[id]').map('attr', 'id').join("\n")

    # Iterate
    dom.find('p[id]').reverse().each(lambda i: print(i.attr('id')))

    # Loop
    for i in dom.find('p[id]').each():
        print(i.attr('id') + ':' + i.text)

    # Modify
    dom.find('div p').last().append('<p id="c">456</p>')
    dom.find(':not(p)').map('strip')

    # Render
    print(dom)

:mod:`Pyjo.DOM` is a minimalistic and relaxed HTML/XML DOM parser with CSS
selector support. It will even try to interpret broken HTML and XML, so you
should not use it for validation.

Classes
-------
"""

import Pyjo.Base
import Pyjo.Collection
import Pyjo.DOM.CSS
import Pyjo.DOM.HTML
import Pyjo.String.Mixin
import Pyjo.String.Unicode

from Pyjo.Regexp import r
from Pyjo.Util import squish, u


re_namespace_prefix = r(r'^(.*?):')
re_no_space_ending = r(r'\S\Z')
re_good_punctuation = r(r'^[^.!?,;:\s]+')
re_no_whitespace = r(r'\S+')


class Pyjo_DOM(Pyjo.Base.object, Pyjo.String.Mixin.object):
    """
    :mod:`Pyjo.DOM` inherits all attributes and methods from
    :mod:`Pyjo.Base` and :mod:`Pyjo.String.Mixin` and implements the following new ones.
    """

    def __init__(self, html=None):
        """::

            dom = Pyjo.DOM.new()

        Construct a new :mod:`Pyjo.DOM` object.
        """

        self.html = Pyjo.DOM.HTML.new()

        if html is not None:
            self.parse(html)

    @property
    def all_text(self, trim=True):
        r"""::

            trimmed   = dom.all_text

        Extract all text content from DOM structure, smart whitespace trimming is
        enabled. ::

            # "foo bar baz"
            dom.parse("<div>foo\n<p>bar</p>baz\n</div>").at('div').all_text
        """
        return self._all_text(True, True)

    @property
    def all_raw_text(self):
        r"""::

            untrimmed = dom.all_raw_text

        Extract all text content from DOM structure, smart whitespace trimming is
        disabled. ::

            # "foo\nbar baz\n"
            dom.parse("<div>foo\n<p>bar</p>baz\n</div>").at('div').all_raw_text
        """
        return self._all_text(True, False)

    def ancestors(self, pattern=None):
        r"""::

            collection = dom.ancestors()
            collection = dom.ancestors('div > p')

        Find all ancestors of this node matching the CSS selector and return a
        :mod:`Pyjo.Collection` object containing these elements as :mod:`Pyjo.DOM` objects.
        All selectors from :mod:`Pyjo.DOM.CSS` are supported. ::

            # "div > p > i"
            dom.parse('<div><p><i>bar</i></p></div>').at('i').child_nodes[0] \
               .ancestors() \
               .map('tag').reverse().join(" > ").say()
        """
        return self._select(self._collect(self._ancestors()), pattern)

    def append(self, string):
        r"""::

            dom = dom.append(u'<p>I ♥ Pyjo!</p>')

        Append HTML/XML fragment to this node. ::

            # "<div><h1>Test</h1><h2>123</h2></div>"
            dom.parse('<div><h1>Test</h1></div>') \
               .at('h1').append('<h2>123</h2>').root

            # "<p>Test 123</p>"
            dom.parse('<p>Test</p>').at('p').child_nodes.first().append(' 123').root
        """
        return self._add(1, string)

    def append_content(self, string):
        r"""::

            dom = dom.append_content(u'<p>I ♥ Pyjo!</p>')

        Append HTML/XML fragment (for ``root`` and ``tag`` nodes) or raw content to this
        node's content. ::

            # "<div><h1>Test123</h1></div>"
            dom.parse('<div><h1>Test</h1></div>') \
               .at('h1').append_content('123').root

            # "<!-- Test 123 --><br>"
            dom.parse('<!-- Test --><br>') \
               .child_nodes.first().append_content('123 ').root

            # "<p>Test<i>123</i></p>"
            dom.parse('<p>Test</p>').at('p').append_content('<i>123</i>').root
        """
        return self._content(True, False, string)

    def at(self, pattern):
        r"""::

            result = dom.at('div > p')

        Find first element in DOM structure matching the CSS selector and return it as
        a :mod:`Pyjo.DOM` object or return :class:`None` if none could be found. All selectors
        from :mod:`Pyjo.DOM.CSS` are supported. ::

            # Find first element with ``svg`` namespace definition
            namespace = dom.at('[xmlns\:svg]').attr('xmlns:svg')
        """
        result = self._css.select_one(pattern)
        if result:
            return self._build(result, self.xml)

    def attr(self, *args, **kwargs):
        r"""::

            my_dict = dom.attr()
            foo = dom.attr('foo')
            dom = dom.attr('foo', 'bar')
            dom = dom.attr(foo='bar')

        This element's attributes. Returns :class:`None` if attribute is missing.
        Setting value to :class:`None` deletes attribute. ::

            # List id attributes
            dom.parse('<div id="a">foo</div><p>bar</p><div id="b">baz</div>') \
               .find('*').map('attr', 'id').compact().join("\n").say()
        """
        tree = self.tree

        if tree[0] != 'tag':
            attrs = {}
        else:
            attrs = tree[2]

        # Dict
        if not args and not kwargs:
            return attrs

        # Get
        if len(args) == 1:
            attrs = self.to_dict()
            if args[0] in attrs:
                return attrs[args[0]]
            else:
                return

        # Set
        if len(args) == 2:
            attrs[args[0]] = args[1]

        for k, v in kwargs.items():
            if v is None:
                if k in attrs:
                    del attrs[k]
            else:
                attrs[k] = u(v)

        return self

    @property
    def child_nodes(self):
        """::

            collection = dom.child_nodes

        Return a :mod:`Pyjo.Collection` object containing the child nodes of this element
        as :mod:`Pyjo.DOM` objects. ::

            # "<p><b>123</b></p>"
            dom.parse('<p>Test<b>123</b></p>').at('p').child_nodes.first().remove()

            # "<!-- Test -->"
            dom.parse('<!-- Test --><b>123</b>').child_nodes.first()
        """
        return self._collect(self._nodes(self.tree))

    def children(self, pattern=None):
        r"""::

            collection = dom.children()
            collection = dom.children('div > p')

        Find all children of this element matching the CSS selector and return a
        :mod:`Pyjo.Collection` object containing these elements as :mod:`Pyjo.DOM` objects.
        All selectors from :mod:`Pyjo.DOM.CSS` are supported. ::

            # Show type of random child element
            print(dom.parse('<b>foo</b><i>bar</i><p>baz</p>') \
                .children().shuffle().first().type)
        """
        return self._select(self._collect(self._nodes(self.tree, True)), pattern)

    @property
    def content(self):
        r"""::

            string = dom.content
            dom.content = u'<p>I ♥ Pyjo!</p>'

        Return this node's content or replace it with HTML/XML fragment (for ``root``
        and ``tag`` nodes) or raw content. ::

            # "<b>Test</b>"
            dom.parse('<div><b>Test</b></div>').at('div').content

            # "<div><h1>123</h1></div>"
            dom.parse('<div><h1>Test</h1></div>').at('h1').set(content='123').root

            # "<p><i>123</i></p>"
            dom.parse('<p>Test</p>').at('p').set(content='<i>123</i>').root

            # "<div><h1></h1></div>"
            dom.parse('<div><h1>Test</h1></div>').at('h1').set(content='').root

            # " Test "
            dom.parse('<!-- Test --><br>').child_nodes.first().content

            # "<div><!-- 123 -->456</div>"
            dom.parse('<div><!-- Test -->456</div>') \
               .at('div').child_nodes.first().set(content=' 123 ').root
        """
        nodetype = self.type
        if nodetype == 'root' or nodetype == 'tag':
            html = Pyjo.DOM.HTML.new(xml=self.xml)
            return ''.join(map(lambda i: html.set(tree=i).render(), self._nodes(self.tree)))
        else:
            return self.tree[1]

    @content.setter
    def content(self, value):
        nodetype = self.type
        if nodetype == 'root' or nodetype == 'tag':
            self._content(0, 1, value)
        else:
            self.tree[1] = value

    def find(self, pattern):
        r"""::

            collection = dom.find('div > p')

        Find all elements in DOM structure matching the CSS selector and return a
        :mod:`Pyjo.Collection` object containing these elements as :mod:`Pyjo.DOM` objects.
        All selectors from :mod:`Pyjo.DOM.CSS` are supported. ::

            # Find a specific element and extract information
            div_id = dom.find('div')[2].attr('id')

            # Extract information from multiple elements
            headers = dom.find('h1, h2, h3').map('text').to_list()

            # Find elements with a class that contains dots
            divs = dom.find('div.foo\.bar').to_list()
        """
        return self._collect(self._css.select(pattern))

    @property
    def descendant_nodes(self):
        r"""::

            collection = dom.descendant_nodes

        Return a :mod:`Pyjo.Collection` object containing all descendant nodes of this
        element as :mod:`Pyjo.DOM` objects. ::

            # "<p><b>123</b></p>"
            dom.parse('<p><!-- Test --><b>123<!-- 456 --></b></p>') \
               .descendant_nodes \
               .grep(lambda i: i.type == 'comment').map('remove').first()
        """
        return self._collect(self._all(self._nodes(self.tree)))

    def following(self, pattern=None):
        r"""::

            collection = dom.following()
            collection = dom.following('div > p')

        Find all sibling elements after this node matching the CSS selector and
        return a :mod:`Pyjo.Collection` object containing these elements as :mod:`Pyjo.DOM`
        objects. All selectors from :mod:`Pyjo.DOM.CSS` are supported. ::

            # List types of sibling elements before this node
            dom.parse('<b>foo</b><i>bar</i><p>baz</p>').at('b') \
               .following().map('tag').join("\n").say()
        """
        return self._select(self._collect(self._siblings(True)[1]), pattern)

    def following_nodes(self):
        """::
            collection = dom.following_nodes()

        Return a :mod:`Pyjo.Collection` object containing all sibling nodes after this
        node as :mod:`Pyjo.DOM` objects. ::

            # "C"
            dom.parse('<p>A</p><!-- B -->C')
               .at('p').following_nodes().last().content
        """
        return self._collect(self._siblings(False)[1])

    def matches(self, pattern):
        """::

            result = dom.matches('div > p')

        Check if this element matches the CSS selector. All selectors from
        :mod:`Pyjo.DOM.CSS` are supported. ::

            # True
            bool(dom.parse('<p class="a">A</p>').at('p').matches('.a'))
            bool(dom.parse('<p class="a">A</p>').at('p').matches('p[class]'))

            # False
            bool(dom.parse('<p class="a">A</p>').at('p').matches('.b'))
            bool(dom.parse('<p class="a">A</p>').at('p').matches('p[id]'))
        """
        if self._css.matches(pattern):
            return self
        else:
            return None

    @property
    def namespace(self):
        r"""::

            namespace = dom.namespace

        Find this element's namespace or return :class:`None` if none could be found. ::

            # Find namespace for an element with namespace prefix
            namespace = dom.at('svg > svg\:circle').namespace

            # Find namespace for an element that may or may not have a namespace prefix
            namespace = dom.at('svg > circle').namespace
        """
        tree = self.tree
        if tree[0] != 'tag':
            return

        # Extract namespace prefix and search parents
        m = re_namespace_prefix.search(tree[1])
        if m:
            ns = 'xmlns:' + m.group(1)
        else:
            ns = None

        for i in ([tree], self._ancestors()):
            for node in i:
                # Namespace for prefix
                attrs = node[2]
                if ns:
                    for k in attrs.keys():
                        if k == ns:
                            return attrs[k]

                # Namespace attribute
                elif 'xmlns' in attrs:
                    return attrs['xmlns']

        return

    @property
    def next(self):
        """::

            sibling = dom.next

        Return :mod:`Pyjo.DOM` object for next sibling element or :class:`None` if there are
        no more siblings. ::

            # "<h2>123</h2>"
            dom.parse('<div><h1>Test</h1><h2>123</h2></div>').at('h1').next
        """
        return self._maybe(self._siblings(True, 0)[1])

    @property
    def next_node(self):
        r"""::

            sibling = dom.next_node

        Return :mod:`Pyjo.DOM` object for next sibling node or :class:`None` if there are
        no more siblings. ::

            # "456"
            dom.parse('<p><b>123</b><!-- Test -->456</p>') \
               .at('b').next_node.next_node

            # " Test "
            dom.parse('<p><b>123</b><!-- Test -->456</p>') \
               .at('b').next_node.content
        """
        return self._maybe(self._siblings(False, 0)[1])

    @property
    def parent(self):
        """::

            parent = dom.parent

        Return :mod:`Pyjo.DOM` object for parent of this node or :obj:`None` if this node
        has no parent.
        """
        if self.tree[0] == 'root':
            return
        else:
            return self._build(self._parent(), self.xml)

    def parse(self, html):
        """::

            dom = dom.parse(u'<foo bar="baz">I ♥ Pyjo!</foo>')

        Parse HTML/XML fragment with :mod:`Pyjo.DOM.HTML`. ::

            # Parse XML
            dom = Pyjo.DOM.new().set(xml=True).parse(xml)
        """
        self.html.parse(html)
        return self

    def preceding(self, pattern=None):
        r"""::

            collection = dom.preceding()
            collection = dom.preceding('div > p')

        Find all sibling elements before this node matching the CSS selector and
        return a :mod:`Pyjo.Collection` object containing these elements as :mod:`Pyjo.DOM`
        objects. All selectors from :mod:`Pyjo.DOM.CSS` are supported. ::

            # List types of sibling elements before this node
            dom.preceding().map('tag').join("\n").say()
        """
        return self._select(self._collect(self._siblings(True)[0]), pattern)

    def preceding_nodes(self):
        r"""::
            collection = dom.preceding_nodes()

        Return a :mod:`Pyjo.Collection` object containing all sibling nodes before this
        node as :mod:`Pyjo.DOM` objects. ::

            # "A"
            dom.parse('A<!-- B --><p>C</p>') \
               .at('p').preceding_nodes().first().content
        """
        return self._collect(self._siblings(False)[0])

    def prepend(self, string):
        r"""::

            dom = dom.prepend(u'<p>I ♥ Pyjo!</p>')

        Prepend HTML/XML fragment to this node. ::

            # "<div><h1>123</h1><h2>Test</h2></div>"
            dom.parse('<div><h2>Test</h2></div>') \
               .at('h2').prepend('<h1>123</h1>').root

            # "<p>Test 123</p>"
            dom.parse('<p>123</p>').at('p').child_nodes.first().prepend('Test ').root
        """
        return self._add(0, string)

    def prepend_content(self, string):
        r"""::

            dom = dom.prepend_content(u'<p>I ♥ Pyjo!</p>')

        Prepend HTML/XML fragment (for ``root`` and ``tag`` nodes) or raw content to this
        node's content. ::

            # "<div><h2>Test 123</h2></div>"
            dom.parse('<div><h2>123</h2></div>') \
               .at('h2').prepend_content('Test ').root

            # "<!-- Test 123 --><br>"
            dom.parse('<!-- 123 --><br>') \
               .child_nodes.first().prepend_content(' Test').root

            # "<p><i>123</i>Test</p>"
            dom.parse('<p>Test</p>').at('p').prepend_content('<i>123</i>').root
        """
        return self._content(False, False, string)

    @property
    def previous(self):
        """::

            sibling = dom.previous

        Return :mod:`Pyjo.DOM` object for previous sibling element or :class:`None` if there
        are no more siblings. ::

            # "<h1>Test</h1>"
            dom.parse('<div><h1>Test</h1><h2>123</h2></div>').at('h2').previous
        """
        return self._maybe(self._siblings(True, -1)[0])

    @property
    def previous_node(self):
        r"""::

            sibling = dom.previous_node

        Return :mod:`Pyjo.DOM` object for previous sibling node or :class:`None` if there
        are no more siblings. ::

            # "123"
            dom.parse('<p>123<!-- Test --><b>456</b></p>') \
               .at('b').previous_node.previous_node

            # " Test "
            dom.parse('<p>123<!-- Test --><b>456</b></p>') \
               .at('b').previous_node.content
        """
        return self._maybe(self._siblings(False, -1)[0])

    @property
    def raw_text(self):
        r"""::

            untrimmed = dom.raw_text

        Extract text content from this element only (not including child elements),
        smart whitespace trimming is disabled. ::

            # "foo\nbaz\n"
            dom.parse("<div>foo\n<p>bar</p>baz\n</div>").at('div').raw_text
        """
        return self._all_text(False, False)

    def remove(self):
        """::

            parent = dom.remove()

        Remove this node and return :meth:`parent`. ::

            # "<div></div>"
            dom.parse('<div><h1>Test</h1></div>').at('h1').remove()

            # "<p><b>456</b></p>"
            dom.parse('<p>123<b>456</b></p>').at('p').child_nodes.first().remove().root
        """
        return self.replace('')

    def replace(self, new):
        r"""::

            parent = dom.replace(u'<div>I ♥ Pyjo!</div>')

        Replace this node with HTML/XML fragment and return :meth:`parent`. ::

            # "<div><h2>123</h2></div>"
            dom.parse('<div><h1>Test</h1></div>').at('h1').replace('<h2>123</h2>')

            # "<p><b>123</b></p>"
            dom.parse('<p>Test</p>') \
               .at('p').child_nodes.item(0).replace('<b>123</b>').root
        """
        tree = self.tree
        if tree[0] == 'root':
            return self.parse(new)
        else:
            return self._replace(self._parent(), tree, self._parse(new))

    @property
    def root(self):
        """::

            root = dom.root

        Return :mod:`Pyjo.DOM` object for root node.
        """
        tree = None
        for tree in self._ancestors(True):
            break

        if not tree:
            return self
        else:
            return self._build(tree, self.xml)

    def strip(self):
        """::

            parent = dom.strip()

        Remove this element while preserving its content and return :meth:`parent`. ::

            # "<div>Test</div>"
            dom.parse('<div><h1>Test</h1></div>').at('h1').strip()
        """
        tree = self.tree
        if tree[0] != 'tag':
            return self
        else:
            new = list(self._nodes(tree))
            new.insert(0, 'root')
            return self._replace(tree[3], tree, new)

    @property
    def tag(self):
        r"""::

            tag = dom.tag
            dom.tag = 'div'

        This element's tag name. ::

            # List tag names of child elements
            dom.children().map('tag').join("\n").say()
        """
        tree = self.tree
        if tree[0] != 'tag':
            return
        else:
            return tree[1]

    @tag.setter
    def tag(self, value):
        tree = self.tree
        if tree[0] == 'tag':
            tree[1] = value

    @property
    def text(self):
        r"""::

            trimmed = dom.text

        Extract text content from this element only (not including child elements),
        smart whitespace trimming is enabled. ::

            # "foo baz"
            dom.parse("<div>foo\n<p>bar</p>baz\n</div>").at('div').text
        """
        return self._all_text(False, True)

    def to_dict(self):
        return self.attr()

    def to_str(self):
        return self.html.render()

    @property
    def tree(self):
        return self.html.tree

    @tree.setter
    def tree(self, value):
        self.html.tree = value

    @property
    def type(self):
        """::

            nodetype = dom.type

        This node's type, usually ``cdata``, ``comment``, ``doctype``, ``pi``, ``raw``,
        ``root``, ``tag`` or ``text``.
        """
        return self.tree[0]

    def wrap(self, string):
        """::

            dom = dom.wrap('<div></div>')

        Wrap HTML/XML fragment around this node, placing it as the last child of the
        first innermost element. ::

            # "<p>123<b>Test</b></p>"
            dom.parse('<b>Test</b>').at('b').wrap('<p>123</p>').root

            # "<div><p><b>Test</b></p>123</div>"
            dom.parse('<b>Test</b>').at('b').wrap('<div><p></p>123</div>').root

            # "<p><b>Test</b></p><p>123</p>"
            dom.parse('<b>Test</b>').at('b').wrap('<p></p><p>123</p>').root

            # "<p><b>Test</b></p>"
            dom.parse('<p>Test</p>').at('p').child_nodes.first().wrap('<b>').root
        """
        return self._wrap(False, string)

    def wrap_content(self, string):
        """::

            dom = dom.wrap_content('<div></div>')

        Wrap HTML/XML fragment around this node's content, placing it as the last
        children of the first innermost element. ::

            # "<p><b>123Test</b></p>"
            dom.parse('<p>Test</p>').at('p').wrap_content('<b>123</b>').root

            # "<p><b>Test</b></p><p>123</p>"
            dom.parse('<b>Test</b>').wrap_content('<p></p><p>123</p>')
        """
        return self._wrap(True, string)

    @property
    def xml(self):
        return self.html.xml

    @xml.setter
    def xml(self, value):
        self.html.xml = value

    def _add(self, offset, new):
        tree = self.tree

        if tree[0] == 'root':
            return self

        parent = self._parent()
        n = self._offset(parent, tree) + offset
        for link in self._link(self._parse(new), parent):
            parent.insert(n, link)
            n += 1

        return self

    def _all(self, nodes):
        for n in nodes:
            if n[0] == 'tag':
                yield n
                yield from self._all(self._nodes(n))
            else:
                yield n

    def _all_text(self, recurse, trim):
        # Detect "pre" tag
        tree = self.tree
        if trim:
            for i in self._ancestors(), (tree,):
                for n in i:
                    if n[1] == 'pre':
                        trim = False

        return self._text(self._nodes(tree), recurse, trim)

    def _ancestors(self, isroot=False):
        if self.type == 'root':
            return

        ancestors = []
        tree = self._parent()

        while True:
            ancestors.append(tree)
            if tree[0] != 'tag':
                break
            tree = tree[3]

        if isroot:
            yield ancestors[-1]
        else:
            yield from ancestors[:-1]

    def _build(self, tree, xml):
        return self.new().set(tree=tree, xml=xml)

    def _collect(self, results):
        xml = self.xml
        return Pyjo.Collection.new(map(lambda a: self._build(a, xml), results) if results else [])

    def _content(self, start, offset, new):
        tree = self.tree

        if tree[0] == 'root' or tree[0] == 'tag':
            if start:
                start = len(tree) + 1
            else:
                start = self._start(tree)
            if offset:
                for _ in range(start, len(tree)):
                    tree.pop(-1)
            for link in self._link(self._parse(new), tree):
                tree.insert(start, link)
                start += 1

        else:
            old = self.content
            if start:
                self.content = old + new
            else:
                self.content = new + old

        return self

    @property
    def _css(self):
        return Pyjo.DOM.CSS.new(tree=self.tree)

    def _link(self, children, parent):
        # Link parent to children
        for n in children[1:]:
            yield n
            if n[0] == 'tag':
                offset = 3
            else:
                offset = 2
            n[offset] = parent
            # TODO weakref n[offset]

    def _maybe(self, tree):
        if tree:
            return self._build(tree, self.xml)
        else:
            return None

    def _nodes(self, tree=None, tags=False):
        if not tree:
            return []
        nodes = tree[self._start(tree) :]
        if tags:
            return filter(lambda n: n[0] == 'tag', nodes)
        else:
            return nodes

    def _offset(self, parent, child):
        i = self._start(parent)
        for n in parent[i:]:
            if n == child:
                break
            else:
                i += 1
        return i

    def _parent(self):
        return self.tree[3 if self.type == 'tag' else 2]

    def _parse(self, new):
        return Pyjo.DOM.HTML.new(xml=self.xml).parse(new).tree

    def _replace(self, parent, tree, new):
        offset = self._offset(parent, tree)
        parent.pop(offset)
        for n in self._link(new, parent):
            parent.insert(offset, n)
            offset += 1
        return self.parent

    def _select(self, collection, selector=None):
        if selector is None:
            return collection
        else:
            return collection.new(filter(lambda i: i.matches(selector), collection))

    def _siblings(self, tags, i=None):
        parent = self.parent
        if parent is None:
            return [None, None]

        tree = self.tree
        before = []
        after = []
        match = 0
        for node in self._nodes(parent.tree):
            if not match and node == tree:
                match += 1
                continue
            if tags and node[0] != 'tag':
                continue
            if match:
                after.append(node)
            else:
                before.append(node)

        if i is not None:
            if i >= 0:
                return [before[i] if len(before) > i else None, after[i] if len(after) > i else None]
            else:
                return [before[i] if len(before) >= -i else None, after[i] if len(after) >= -i else None]
        else:
            return [before, after]

    def _start(self, tree):
        if tree[0] == 'root':
            return 1
        else:
            return 4

    def _text(self, nodes, recurse, trim):
        # Merge successive text nodes
        i = 0
        while len(nodes) > i + 1:
            nextnode = nodes[i + 1]
            if nodes[i][0] == 'text' and nextnode[0] == 'text':
                text = nodes[i][1] + nextnode[1]
                nodes.pop(i)
                nodes.pop(i)
                nodes.insert(i, ['text', text])
            else:
                i += 1
                continue

        text = ''
        for node in nodes:
            nodetype = node[0]

            # Text
            chunk = ''
            if nodetype == 'text':
                if trim:
                    chunk = squish(node[1])
                else:
                    chunk = node[1]

            # CDATA or raw text
            elif nodetype == 'cdata' or nodetype == 'raw':
                chunk = node[1]

            # Nested tag
            elif nodetype == 'tag' and recurse:
                chunk = self._text(self._nodes(node), True, False if node[1] == 'pre' else trim)

            # Add leading whitespace if punctuation allows it
            if re_no_space_ending.search(text) and re_good_punctuation.search(chunk):
                chunk = ' ' + chunk

            # Trim whitespace blocks
            if re_no_whitespace.search(chunk) or not trim:
                text += chunk

        return text

    def _wrap(self, content, new):
        tree = self.tree

        if tree[0] == 'root':
            content = True
        if tree[0] != 'root' and tree[0] != 'tag':
            content = False

        # Find innermost tag
        current = None
        new = self._parse(new)
        first = new
        while True:
            node = None
            for node in self._nodes(first, True):
                break
            first = node
            if not first:
                break
            current = first
        if current is None:
            return self

        # Wrap content
        if content:
            root = list(self._nodes(tree))
            root.insert(0, 'root')
            for link in self._link(root, current):
                current.append(link)
            start = self._start(tree)
            for _ in range(start, len(tree)):
                tree.pop(-1)
            for link in self._link(new, tree):
                tree.insert(start, link)
                start += 1

        # Wrap element
        else:
            self._replace(self._parent(), tree, new)
            for link in self._link(['root', tree], current):
                current.append(link)

        return self


new = Pyjo_DOM.new
object = Pyjo_DOM
