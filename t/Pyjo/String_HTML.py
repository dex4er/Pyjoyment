import Pyjo.String.HTML

from Pyjo.Collection import c
from Pyjo.String.HTML import html
from Pyjo.String.Unicode import u
from Pyjo.Test import *
from Pyjo.Util import xml_escape

import pickle


# Markup of another library, with the __html__ protocol of markupsafe
class Markup(str):
    def __html__(self):
        return str(self)


with subtest('Constructor'):
    isa_ok(html('<p>'), Pyjo.String.HTML.object, 'html')
    isa_ok(html('<p>'), Pyjo.String.Unicode.object, 'a Pyjo.String.Unicode')
    isa_ok(Pyjo.String.HTML.new('<p>'), Pyjo.String.HTML.object, 'new')
    is_ok(html('<p>', 'Hello', b'!'), '<p>Hello!', 'parts are markup too')
    is_ok(html(), '', 'empty')
    is_ok(repr(html('<p>')), "Pyjo.String.HTML.new('<p>')", 'repr')

with subtest('xml_escape'):
    is_ok(xml_escape(html('<p>')), '<p>', 'markup')
    is_ok(xml_escape(Markup('<p>')), '<p>', 'markup of another library')
    is_ok(xml_escape(u('<p>')), '&lt;p&gt;', 'Pyjo.String.Unicode is escaped')
    is_ok(xml_escape(c('<b>', '<s>').join(', ')), '&lt;b&gt;, &lt;s&gt;', 'joined collection is escaped')
    is_ok(xml_escape(u('<p>').trim()), '&lt;p&gt;', 'chain of Pyjo.String.Unicode is escaped')

with subtest('Concatenation'):
    string = html('<p>') + '<b>' + html('</p>')
    isa_ok(string, Pyjo.String.HTML.object, 'markup')
    is_ok(string, '<p>&lt;b&gt;</p>', 'escaped from left to right')
    string = '<b>' + html('<p>')
    isa_ok(string, Pyjo.String.HTML.object, 'markup on the right')
    is_ok(string, '&lt;b&gt;<p>', 'escaped on the left')
    is_ok(u('<b>') + html('<p>'), '&lt;b&gt;<p>', 'Pyjo.String.Unicode on the left')
    is_ok(html('<p>') + u('<b>'), '<p>&lt;b&gt;', 'Pyjo.String.Unicode on the right')
    is_ok(html('<p>') + Markup('<b>'), '<p><b>', 'markup of another library')
    is_ok(html('<p>') + html('<b>'), '<p><b>', 'markup')
    is_ok(html('a') + '', 'a', 'empty')
    throws_ok(lambda: html('a') + 1, TypeError, 'not a string')
    throws_ok(lambda: 1 + html('a'), TypeError, 'not a string on the left')

with subtest('Repetition'):
    isa_ok(html('<hr>') * 2, Pyjo.String.HTML.object, 'markup')
    is_ok(html('<hr>') * 2, '<hr><hr>', 'repeated')
    is_ok(2 * html('<hr>'), '<hr><hr>', 'repeated on the right')
    is_ok(html('<hr>') * 0, '', 'none')

with subtest('Formatting with %'):
    isa_ok(html('%s') % 'a', Pyjo.String.HTML.object, 'markup')
    is_ok(html('<p>%s</p>') % '<b>', '<p>&lt;b&gt;</p>', 'value')
    is_ok(html('<p>%s</p>') % html('<b>'), '<p><b></p>', 'markup')
    is_ok(html('<p>%s %s</p>') % ('<b>', html('<i>')), '<p>&lt;b&gt; <i></p>', 'tuple')
    is_ok(html('<p>%(a)s</p>') % {'a': '<b>'}, '<p>&lt;b&gt;</p>', 'mapping')
    is_ok(html('<p>%r</p>') % '<b>', '<p>&#39;&lt;b&gt;&#39;</p>', 'repr')
    is_ok(html('<p>%d %.1f</p>') % (3, 1.25), '<p>3 1.2</p>', 'numbers')
    is_ok(html('<p>%s</p>') % ('<b>',), '<p>&lt;b&gt;</p>', 'tuple of one')

with subtest('format and format_map'):
    isa_ok(html('{}').format('a'), Pyjo.String.HTML.object, 'markup')
    is_ok(html('<p>{}</p>').format('<b>'), '<p>&lt;b&gt;</p>', 'positional')
    is_ok(html('<p>{a}</p>').format(a='<b>'), '<p>&lt;b&gt;</p>', 'keyword')
    is_ok(html('<p>{}</p>').format(html('<b>')), '<p><b></p>', 'markup')
    is_ok(html('<p>{}</p>').format(Markup('<b>')), '<p><b></p>', 'markup of another library')
    is_ok(html('<p>{!r}</p>').format('<b>'), '<p>&#39;&lt;b&gt;&#39;</p>', 'conversion')
    is_ok(html('<p>{:>5}</p>').format('<b>'), '<p>  &lt;b&gt;</p>', 'format spec before escaping')
    is_ok(html('<p>{:03d}</p>').format(7), '<p>007</p>', 'number')
    is_ok(html('<p>{0.real}</p>').format(5), '<p>5</p>', 'attribute')
    is_ok(html('{{<p>}}').format(), '{<p>}', 'braces')
    is_ok(html('<p>{a}</p>').format_map({'a': '<b>'}), '<p>&lt;b&gt;</p>', 'format_map')

with subtest('join'):
    isa_ok(html(', ').join(['a']), Pyjo.String.HTML.object, 'markup')
    is_ok(html('<br>').join(['<b>', html('<i>'), u('<s>')]), '&lt;b&gt;<br><i><br>&lt;s&gt;', 'escaped')
    is_ok(html('<br>').join([]), '', 'empty')
    is_ok(html('<br>').join(x for x in ['a', 'b']), 'a<br>b', 'generator')

with subtest('Methods of Pyjo.String.Unicode keep the markup'):
    isa_ok(html(' <p> ').trim(), Pyjo.String.HTML.object, 'trim')
    is_ok(html(' <p> ').trim(), '<p>', 'trimmed')
    isa_ok(html('<p>').xml_escape(), Pyjo.String.HTML.object, 'xml_escape')
    is_ok(html('<p>').xml_escape(), '&lt;p&gt;', 'escaped explicitly')
    isa_ok(html('%3Cp%3E').url_unescape(), Pyjo.String.HTML.object, 'url_unescape')

with subtest('Methods of str give a str'):
    is_ok(type(html('<p>').upper()), str, 'upper')
    is_ok(type(html('<p>')[1:]), str, 'slice')
    is_ok(type(str(html('<p>'))), str, 'str')

with subtest('__html__'):
    markup = html('<p>').__html__()
    is_ok(markup, '<p>', 'markup')

with subtest('Pickle'):
    string = pickle.loads(pickle.dumps(html('<p>')))
    isa_ok(string, Pyjo.String.HTML.object, 'markup')
    is_ok(string, '<p>', 'same')

done_testing()
