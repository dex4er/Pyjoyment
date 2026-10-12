
"""
Pyjo.DOM.HTML - HTML/XML engine
===============================
::

    import Pyjo.DOM.HTML

    html = Pyjo.DOM.HTML.new()
    html.parse('<div><p id="a">Test</p><p id="b">123</p></div>')
    tree = html.tree

Classes
-------
"""


import Pyjo.Base
import Pyjo.DOM

from Pyjo.Regexp import r
from Pyjo.Util import html_unescape, xml_escape


# HTML elements that only contain raw text
RAW = {'script', 'style'}

# HTML elements that only contain raw text and entities
RCDATA = {'title', 'textarea'}

# HTML elements with optional end tags
END = {'body': 'head', 'optgroup': 'optgroup', 'option': 'option'}

# HTML elements that break paragraphs
for _ in ('address', 'article', 'aside', 'blockquote', 'dir', 'div', 'dl',
          'fieldset', 'footer', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
          'header', 'hr', 'main', 'menu', 'nav', 'ol', 'p', 'pre', 'section',
          'table', 'ul'):
    END[_] = 'p'

# HTML table elements with optional end tags
TABLE = {'colgroup', 'tbody', 'td', 'tfoot', 'th', 'thead', 'tr'}

# HTML elements with optional end tags and scoping rules
CLOSE = {'li': ({'li'}, {'ul', 'ol'}),
         'tr': ({'tr'}, {'table'}),
         'colgroup': (TABLE, {'table'}),
         'tbody': (TABLE, {'table'}),
         'tfoot': (TABLE, {'table'}),
         'thead': (TABLE, {'table'}),
         'dd': ({'dd', 'dt'}, {'dl'}),
         'dt': ({'dd', 'dt'}, {'dl'}),
         'rp': ({'rp', 'rt'}, {'ruby'}),
         'rt': ({'rp', 'rt'}, {'ruby'}),
         'td': ({'th', 'td'}, {'table'}),
         'th': ({'th', 'td'}, {'table'}),
         }

# HTML elements without end tags
EMPTY = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
         'keygen', 'link', 'menuitem', 'meta' 'param', 'source', 'track',
         'wbr'}

# HTML elements categorized as phrasing content (and obsolete inline elements)
PHRASING = {'a', 'abbr', 'area', 'audio', 'b', 'bdi', 'bdo', 'br', 'button',
            'canvas', 'cite', 'code', 'data', 'datalist', 'del', 'dfn', 'em',
            'embed', 'i', 'iframe', 'img', 'input', 'ins', 'kbd', 'keygen',
            'label', 'link', 'map', 'mark', 'math', 'meta', 'meter',
            'noscript', 'object', 'output', 'picture', 'progress', 'q',
            'ruby', 's', 'samp', 'script', 'select', 'small', 'span',
            'strong', 'sub', 'sup', 'svg', 'template', 'textarea', 'time',
            'u', 'var', 'video', 'wbr'}

OBSOLETE = {'acronym', 'applet', 'basefont', 'big', 'font', 'strike', 'tt'}
PHRASING = OBSOLETE | PHRASING

# HTML elements that don't get their self-closing flag acknowledged
BLOCK = {'a', 'address', 'applet', 'article', 'aside', 'b', 'big',
         'blockquote', 'body', 'button', 'caption', 'center', 'code', 'col',
         'colgroup', 'dd', 'details', 'dialog', 'dir', 'div', 'dl', 'dt',
         'em', 'fieldset', 'figcaption', 'figure', 'font', 'footer', 'form',
         'frameset', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'head', 'header',
         'hgroup', 'html', 'i', 'iframe', 'li', 'listing', 'main', 'marquee',
         'menu', 'nav', 'nobr', 'noembed', 'noframes', 'noscript', 'object',
         'ol', 'optgroup', 'option', 'p', 'plaintext', 'pre', 'rp', 'rt',
         's', 'script', 'section', 'select', 'small', 'strike', 'strong',
         'style', 'summary', 'table', 'tbody', 'td', 'template', 'textarea',
         'tfoot', 'th', 'thead', 'title', 'tr', 'tt', 'u', 'ul', 'xmp'}

ATTR_PAT = r'''
  ([^<>=\s\/]+|\/)   # Key
  (?:
    \s*=\s*
    (?:
      "([^"]*?)"     # Quotation marks
    |
      '([^']*?)'     # Apostrophes
    |
      ([^>\s]*)      # Unquoted
    )
  )?
  \s*
'''

TOKEN_1_PAT = r'''
  (?P<text>[^<]+)?                                     # Text
  (?:
    <(?:
      !(?:
        DOCTYPE(?P<doctype>
        \s+\w+                                        # Doctype
        (?:(?:\s+\w+)?(?:\s+(?:"[^"]*"|'[^']*'))+)?   # External ID
        (?:\s+\[.+?\])?                               # Int Subset
        \s*)
      |
        --(?P<comment>.*?)--\s*                       # Comment
      |
        \[CDATA\[(?P<cdata>.*?)\]\]                   # CDATA
      )
    |
      \?(?P<pi>.*?)\?                                 # Processing Instruction
    |
'''

RAW_PAT = r'''
      \s*(?P<rawtag>
        (?P<rawtagname>''' + '|'.join(RAW | RCDATA) + r''')\s*
        (?:''' + ATTR_PAT + r''')*
      )>
      (?P<raw>.*?)                                    # Raw
      <\s*/\s*(?P=rawtagname)\s*
    |
'''

TOKEN_2_PAT = r'''
      \s*(?P<tag>[^<>\s]+\s*(?:''' + ATTR_PAT + ''')*) # Tag
    )>
    | (?P<runaway><)                                  # Runaway "<"
  )?
'''

XML_TOKEN_PAT = TOKEN_1_PAT + TOKEN_2_PAT

HTML_TOKEN_PAT = TOKEN_1_PAT + RAW_PAT + TOKEN_2_PAT


re_startswith_xml = r(r'<\?\s*xml\b', 'is')
re_xml_token = r(XML_TOKEN_PAT, 'isx')
re_html_token = r(HTML_TOKEN_PAT, 'isx')
re_end_tag = r(r'^\/\s*(\S+)')
re_start_tag = r(r'^([^\s/]+)([\s\S]*)')
re_attr = r(ATTR_PAT, 'x')


class Pyjo_DOM_HTML(Pyjo.Base.object):
    """
    :mod:`Pyjo.DOM.HTML` inherits all attributes and methods from
    :mod:`Pyjo.Base` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        self.tree = kwargs.get('tree', ['root'])
        """::

            tree = html.tree
            html.tree = ['root']

        Document Object Model. Note that this structure should only be used very
        carefully since it is very dynamic.
        """

        self.xml = kwargs.get('xml')
        """::

            bool = html.xml
            html.xml = bool

        Disable HTML semantics in parser and activate case sensitivity, defaults to
        auto detection based on processing instructions.
        """

    def parse(self, html):
        """::

            html = html.parse(u'<foo bar="baz">I ♥ Pyjo!</foo>')

        Parse HTML/XML fragment.
        """
        xml = self.xml
        tree = ['root']
        current = tree
        text = None

        if isinstance(html, Pyjo.DOM.object):
            html = html.to_str()

        if xml is None and re_startswith_xml.search(html[:1024]):
            xml = True
            self.xml = xml

        if xml:
            re_token = re_xml_token
        else:
            re_token = re_html_token

        for m in re_token.finditer(html):
            text, doctype, comment, cdata, pi, tag, runaway = m.group('text', 'doctype', 'comment', 'cdata', 'pi', 'tag', 'runaway')
            raw = m.group('raw') if not xml else None
            rawtag = m.group('rawtag') if not xml else None
            if rawtag is not None:
                tag = rawtag

            if runaway is not None:
                if text is not None:
                    text += '<'
                else:
                    text = '<'

            if text is not None:
                node = self._node(current, 'text', html_unescape(text))
                if node:
                    current = node

            # Tag
            if tag is not None:

                # End
                m = re_end_tag.search(tag)
                if m:
                    node = self._end(m.group(1) if xml else m.group(1).lower(), xml, current)
                    if node:
                        current = node

                # Start
                else:
                    m = re_start_tag.search(tag)
                    if m:
                        start, attr = m.group(1, 2)
                        if not xml:
                            start = start.lower()

                        attrs = {}
                        closing = False

                        # Attributes
                        for m in re_attr.finditer(attr):
                            if xml:
                                key = m.group(1)
                            else:
                                key = m.group(1).lower()

                            if m.group(2) is not None:
                                value = m.group(2)
                            elif m.group(3) is not None:
                                value = m.group(3)
                            else:
                                value = m.group(4)

                            # Empty tag
                            if key == '/':
                                closing = True
                                continue

                            if value is not None:
                                attrs[key] = html_unescape(value)
                            else:
                                attrs[key] = value

                        # "image" is an alias for "img"
                        if not xml and start == 'image':
                            start = 'img'

                        current = self._start(start, attrs, xml, current)

                        # Element without end tag (self-closing)
                        if not xml and start in EMPTY or (xml or start not in BLOCK) and closing:
                            current = self._end(start, xml, current)

                        # Raw text elements
                        if xml or start not in RAW and start not in RCDATA:
                            continue
                        if rawtag is None:
                            continue
                        current = self._node(current, 'raw', html_unescape(raw) if start in RCDATA else raw)
                        node = self._end(start, 0, current)
                        if node:
                            current = node

            # DOCTYPE
            elif doctype is not None:
                node = self._node(current, 'doctype', doctype)
                if node:
                    current = node

            # Comment
            elif comment is not None:
                node = self._node(current, 'comment', comment)
                if node:
                    current = node

            # CDATA
            elif cdata is not None:
                node = self._node(current, 'cdata', cdata)
                if node:
                    current = node

            # Processing instruction
            elif pi is not None:
                node = self._node(current, 'pi', pi)
                if node:
                    current = node

        self.tree = tree
        return self

    def render(self):
        """::

            string = html.render()

        Render DOM to HTML/XML.
        """
        return self._render(self.tree, self.xml)

    def _end(self, end, xml, current):

        # Search stack for start tag
        nextnode = current
        while nextnode is not None:
            # Ignore useless end tag
            if nextnode[0] == 'root':
                return

            # Right tag
            if nextnode[1] == end:
                return nextnode[3]

            # Phrasing content can only cross phrasing content
            if not xml and end in PHRASING and nextnode[1] not in PHRASING:
                return

            nextnode = nextnode[3]
            if nextnode is None:
                break

    def _node(self, current, nodetype, content):
        new = [nodetype, content, current]
        current.append(new)
        return current

    def _render(self, tree, xml):
        nodetype = tree[0]

        # Text (escaped)
        if nodetype == 'text':
            return xml_escape(tree[1])

        # Raw text
        if nodetype == 'raw':
            return tree[1]

        # DOCTYPE
        if nodetype == 'doctype':
            return '<!DOCTYPE' + tree[1] + '>'

        # Comment
        if nodetype == 'comment':
            return '<!--' + tree[1] + '-->'

        # CDATA
        if nodetype == 'cdata':
            return '<![CDATA[' + tree[1] + ']]>'

        # Processing instruction
        if nodetype == 'pi':
            return '<?' + tree[1] + '?>'

        # Start tag
        result = ''
        if nodetype == 'tag':
            # Open tag
            tag = tree[1]
            result += '<' + tag

            # Attributes
            attrs = []

            for key in sorted(tree[2].keys()):
                # No value
                if key not in tree[2] or tree[2][key] is None:
                    attrs.append(key)
                else:
                    value = tree[2][key]
                    attrs.append(key + '="' + xml_escape(value) + '"')

            if attrs:
                result += ' ' + ' '.join(attrs)

            # Element without end tag
            if len(tree) <= 4:
                if xml:
                    return result + ' />'
                elif tag in EMPTY:
                    return result + '>'
                else:
                    return result + '></' + tag + '>'

            # Close tag
            result += '>'

        # Render whole tree
        if nodetype == 'root':
            start = 1
        else:
            start = 4
        for t in tree[start:]:
            result += self._render(t, xml)

        # End tag
        if nodetype == 'tag':
            result += '</' + tree[1] + '>'

        return result

    def _start(self, start, attrs, xml, current):
        # Autoclose optional HTML elements
        if not xml and current[0] != 'root':
            if start in END:
                node = self._end(END[start], 0, current)
                if node:
                    current = node
            elif start in CLOSE:
                allowed, scope = CLOSE[start]

                # Close allowed parent elements in scope
                parent = current
                while parent[0] != 'root' and parent[1] not in scope:
                    if parent[1] in allowed:
                        node = self._end(parent[1], 0, current)
                        if node:
                            current = node
                    parent = parent[3]

        # New tag
        new = ['tag', start, attrs, current]
        current.append(new)
        return new


new = Pyjo_DOM_HTML.new
object = Pyjo_DOM_HTML
