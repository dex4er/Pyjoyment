import Pyjo.Path
import Pyjo.String.HTML
import Pyjo.String.Template

from Pyjo.Collection import c
from Pyjo.String.HTML import html
from Pyjo.String.Template import Interpolation, escape, is_template, raw, t
from Pyjo.String.Unicode import u
from Pyjo.Test import *
from Pyjo.Util import xml_escape

import re


# Markup of another library, with the __html__ protocol of markupsafe
class Markup(str):
    def __html__(self):
        return str(self)


class User:
    name = '<b>'
    _secret = 'secret'


name = '<script>'
width = 6

with subtest('Constructor'):
    template = Pyjo.String.Template.new('<p>', Interpolation('<b>', 'name'), '</p>')
    isa_ok(template, Pyjo.String.Template.object, 'new')
    is_ok(template.strings, ('<p>', '</p>'), 'strings')
    is_ok(len(template.interpolations), 1, 'one interpolation')
    is_ok(template.interpolations[0].value, '<b>', 'value of the interpolation')
    is_ok(template.interpolations[0].expression, 'name', 'expression of the interpolation')
    is_ok(template.interpolations[0].conversion, None, 'conversion of the interpolation')
    is_ok(template.interpolations[0].format_spec, '', 'format_spec of the interpolation')
    is_ok(template.values, ('<b>',), 'values')
    is_ok(Pyjo.String.Template.new().strings, ('',), 'empty')
    is_ok(Pyjo.String.Template.new('a', 'b').strings, ('ab',), 'strings are joined')
    template = Pyjo.String.Template.new(Interpolation(1), Interpolation(2))
    is_ok(template.strings, ('', '', ''), 'empty strings around interpolations')
    is_ok(template.values, (1, 2), 'values of interpolations')
    throws_ok(
        lambda: Pyjo.String.Template.new(1),
        TypeError,
        "Template.__init__ *args need to be of type 'str' or 'Interpolation', got int",
    )
    throws_ok(lambda: Interpolation(1, 'x', 'x'), ValueError, 'right error')

with subtest('Iteration'):
    template = Pyjo.String.Template.new('a', Interpolation(1, 'x'), Interpolation(2, 'y'), 'b')
    is_deeply_ok([i if isinstance(i, str) else i.value for i in template], ['a', 1, 2, 'b'], 'without empty strings')
    is_deeply_ok(list(Pyjo.String.Template.new()), [], 'empty')

with subtest('repr'):
    template = Pyjo.String.Template.new('<p>', Interpolation('<b>', 'name'), '</p>')
    is_ok(
        repr(template),
        "Pyjo.String.Template.new('<p>', Interpolation('<b>', 'name', None, ''), '</p>')",
        'repr',
    )
    is_ok(repr(Interpolation(1, 'x', 'r', '>5')), "Interpolation(1, 'x', 'r', '>5')", 'repr of an interpolation')

with subtest('Rendering'):
    isa_ok(t('<p>').render(), Pyjo.String.HTML.object, 'markup')
    is_ok(t('<p>{name}</p>').render(), '<p>&lt;script&gt;</p>', 'string is escaped')
    is_ok(t('{value}', value=u('<b>')), '&lt;b&gt;', 'Pyjo.String.Unicode is escaped')
    is_ok(t('{value}', value=c('<b>', '<i>').join(', ')), '&lt;b&gt;, &lt;i&gt;', 'joined collection is escaped')
    is_ok(t('{value}', value=html('<b>')), '<b>', 'markup')
    is_ok(t('{value}', value=Markup('<b>')), '<b>', 'markup of another library')
    is_ok(t('<p>{value}</p>', value=None), '<p></p>', 'None')
    is_ok(t('{value}', value=0), '0', 'zero')
    is_ok(t('{value}', value=1.5), '1.5', 'number')
    is_ok(t('{value}', value=False), 'False', 'boolean')
    is_ok(t('{value}', value=b'<b>'), 'b&#39;&lt;b&gt;&#39;', 'bytes')
    is_ok(t('{value}', value={'a': '<b>'}), '{&#39;a&#39;: &#39;&lt;b&gt;&#39;}', 'mapping')
    is_ok(t('{value}', value=Pyjo.Path.new('/a/b')), '/a/b', 'object with a string form is not iterated')
    is_ok(t('{value}', value=t('<i>{name}</i>')), '<i>&lt;script&gt;</i>', 'template')

with subtest('Iterables'):
    is_ok(t('{value}', value=['<b>', html('<i>'), None, 1]), '&lt;b&gt;<i>1', 'list')
    is_ok(t('{value}', value=('<b>', '<i>')), '&lt;b&gt;&lt;i&gt;', 'tuple')
    is_ok(t('{value}', value=c('<b>', '<i>')), '&lt;b&gt;&lt;i&gt;', 'collection')
    is_ok(t('{value}', value=(x for x in ['<b>', '<i>'])), '&lt;b&gt;&lt;i&gt;', 'generator')
    is_ok(
        t('{value}', value=[t('<li>{x}</li>', x=x) for x in ['<b>', '<i>']]),
        '<li>&lt;b&gt;</li><li>&lt;i&gt;</li>',
        'templates',
    )
    is_ok(t('{value}', value=[['<b>'], [['<i>']]]), '&lt;b&gt;&lt;i&gt;', 'nested')
    is_ok(t('{value}', value=[]), '', 'empty')

with subtest('Conversion and format specification'):
    is_ok(t('{name!r}'), '&#39;&lt;script&gt;&#39;', 'repr')
    is_ok(t('{name!s}'), '&lt;script&gt;', 'str')
    is_ok(t('{value!a}', value='ż<'), '&#39;\\u017c&lt;&#39;', 'ascii')
    is_ok(t('{name:>10}'), '  &lt;script&gt;', 'format before escaping')
    is_ok(t('{value:03d}', value=7), '007', 'number')
    is_ok(t('{name!r:>{width}}'), '&#39;&lt;script&gt;&#39;', 'nested field')
    is_ok(t('{value:{fill}>{width}}', value=1, fill='*'), '*****1', 'nested fields')
    is_ok(t('{name:>{width!r}}'), '&lt;script&gt;', 'nested field with conversion')
    is_ok(t('{value:>5}', value=html('<b>')), '  &lt;b&gt;', 'markup with a format is escaped')
    is_ok(t('{value!s}', value=html('<b>')), '&lt;b&gt;', 'markup with a conversion is escaped')
    template = t('{name!r:>{width}}')
    is_ok(template.interpolations[0].conversion, 'r', 'conversion')
    is_ok(template.interpolations[0].format_spec, '>6', 'nested field is evaluated')

with subtest('Self-documenting fields'):
    template = t('{name=}')
    is_ok(template.strings, ('name=', ''), 'text of the field')
    is_ok(template.interpolations[0].expression, 'name', 'expression')
    is_ok(template.interpolations[0].conversion, 'r', 'repr')
    is_ok(template, 'name=&#39;&lt;script&gt;&#39;', 'rendered')
    template = t('{ name = }')
    is_ok(template.strings, (' name = ', ''), 'text of the field with spaces')
    is_ok(template.interpolations[0].expression, ' name ', 'expression with spaces')
    template = t('{name=:>10}')
    is_ok(template.interpolations[0].conversion, None, 'no repr with a format')
    is_ok(template, 'name=  &lt;script&gt;', 'rendered with a format')
    template = t('{name=!s}')
    is_ok(template.interpolations[0].conversion, 's', 'conversion')
    is_ok(template, 'name=&lt;script&gt;', 'rendered with a conversion')

with subtest('Fields'):
    is_ok(t('{{<p>}}'), '{<p>}', 'braces')
    is_ok(t('{user.name}', user=User()), '&lt;b&gt;', 'attribute')
    is_ok(t('{user[name]}', user={'name': '<b>'}), '&lt;b&gt;', 'key')
    is_ok(t('{user[0]}', user=['<b>']), '&lt;b&gt;', 'index')
    is_ok(t('{user[0].name}', user=[User()]), '&lt;b&gt;', 'index and attribute')
    is_ok(t('{ name }').interpolations[0].expression, ' name ', 'spaces in the expression')
    is_ok(t('{ name }'), '&lt;script&gt;', 'spaces around the name')
    is_ok(t('{zażółć}', zażółć='<b>'), '&lt;b&gt;', 'unicode name')
    is_ok(t('{_}', _='<b>'), '&lt;b&gt;', 'name that starts with _')

with subtest('Values'):
    is_ok(t('{name}', name='<b>'), '&lt;b&gt;', 'keyword argument')
    is_ok(t('{name}'), '&lt;script&gt;', 'global variable')
    is_ok(t('{len}'), '&lt;built-in function len&gt;', 'builtin')

    def local():
        # F841 "Local variable `name` is assigned to but never used": t() takes it from the frame
        name = '<i>'  # noqa: F841
        return t('{name}')

    is_ok(local(), '&lt;i&gt;', 'local variable')

    def keyword_first():
        name = '<i>'
        return t('{name}', name='<s>') + name

    is_ok(keyword_first(), '&lt;s&gt;&lt;i&gt;', 'keyword argument before a local variable')

    def closure():
        value = '<i>'

        def inner():
            return t('{value}', value=value)

        return inner()

    is_ok(closure(), '&lt;i&gt;', 'variable of a closure')

    def comprehension():
        return [t('<li>{item}</li>') for item in ['<b>', '<i>']]

    is_ok(comprehension(), ['<li>&lt;b&gt;</li>', '<li>&lt;i&gt;</li>'], 'variable of a comprehension')

    value = '<b>'
    template = t('{value}')
    value = '<i>'
    is_ok(template, '&lt;b&gt;', 'values are taken at once')

with subtest('Errors'):
    throws_ok(
        lambda: t('{len(name)}'),
        ValueError,
        "Field 'len(name)' is not a name with attributes and keys, pass its value as a keyword argument instead",
    )
    throws_ok(
        lambda: t('{user.__class__}', user=User()),
        ValueError,
        'Field \'user.__class__\' has an attribute that starts with "_"',
    )
    throws_ok(lambda: t('{user._secret}', user=User()), ValueError, re.compile('starts with "_"'))
    throws_ok(lambda: t('{name.__class__.__init__.__globals__}'), ValueError, re.compile('starts with "_"'))
    throws_ok(lambda: t('{}'), ValueError, "Field '' is positional, t() takes names only")
    throws_ok(lambda: t('{0}'), ValueError, "Field '0' is positional, t() takes names only")
    throws_ok(lambda: t('{name[}'), ValueError, re.compile('.'))
    throws_ok(lambda: t('{missing}'), NameError, "name 'missing' is not defined")
    throws_ok(lambda: t('{name!x}'), ValueError, "Field 'name' has an unknown conversion 'x'")
    throws_ok(lambda: t('{name:{width:{width}}}'), ValueError, 'Max string recursion exceeded')
    throws_ok(lambda: t('{user.missing}', user=User()), AttributeError, re.compile('missing'))
    throws_ok(lambda: t('{user[missing]}', user={}), KeyError, re.compile('missing'))
    throws_ok(lambda: t('{', name=1), ValueError, re.compile('.'))
    throws_ok(lambda: t(t('a'), name=1), TypeError, 't() takes keyword arguments only with a string')
    throws_ok(lambda: t(1), TypeError, 't() takes a string or a template, not int')

with subtest('escape and raw'):
    is_ok(escape('<b>'), '&lt;b&gt;', 'string')
    is_ok(raw('<b>'), '<b>', 'raw string')
    is_ok(type(escape(html('<b>'))), str, 'markup is a str')
    is_ok(escape(['<b>', html('<i>'), None, t('{x}', x='<s>')]), '&lt;b&gt;<i>&lt;s&gt;', 'escaped')
    is_ok(raw(['<b>', html('<i>'), None, t('{x}', x='<s>')]), '<b><i>&lt;s&gt;', 'not escaped')
    is_ok(raw(1.5), '1.5', 'number')

with subtest('is_template'):
    ok(is_template(t('<p>{name}</p>')), 'template')
    ok(not is_template('<p>{name}</p>'), 'string')
    ok(not is_template(html('<p>')), 'markup')
    ok(not is_template(None), 'None')

with subtest('Template'):
    template = t('<p>{name}</p>')
    ok(t(template) is template, 'same template')
    isa_ok(t(html('<p>{name}</p>')), Pyjo.String.Template.object, 'from markup')

with subtest('String'):
    template = t('<p>{name}</p>')
    is_ok(str(template), '<p>&lt;script&gt;</p>', 'str')
    is_ok(type(str(template)), str, 'str is a str')
    isa_ok(template.to_str(), Pyjo.String.HTML.object, 'to_str')
    is_ok(template.__html__(), '<p>&lt;script&gt;</p>', '__html__')
    is_ok(f'{template}', '<p>&lt;script&gt;</p>', 'f-string')
    is_ok(f'{template:>25}', '    <p>&lt;script&gt;</p>', 'f-string with a format')
    ok(template == '<p>&lt;script&gt;</p>', 'equal')
    ok(bool(template), 'true')
    ok(not t(''), 'false')
    is_ok(xml_escape(template), '<p>&lt;script&gt;</p>', 'xml_escape leaves it')
    is_ok(html('<div>').format(template), '<div>', 'format of markup')
    is_ok(html('{}').format(template), '<p>&lt;script&gt;</p>', 'markup in format of markup')
    is_ok(html('<br>').join([template, '<b>']), '<p>&lt;script&gt;</p><br>&lt;b&gt;', 'join of markup')

with subtest('Concatenation'):
    template = t('<p>{name}') + t('{name}</p>')
    isa_ok(template, Pyjo.String.Template.object, 'templates')
    is_ok(template.values, ('<script>', '<script>'), 'values')
    is_ok(template, '<p>&lt;script&gt;&lt;script&gt;</p>', 'rendered')
    string = t('<p>') + '<b>'
    isa_ok(string, Pyjo.String.HTML.object, 'markup')
    is_ok(string, '<p>&lt;b&gt;', 'string is escaped')
    string = '<b>' + t('<p>')
    isa_ok(string, Pyjo.String.HTML.object, 'markup on the right')
    is_ok(string, '&lt;b&gt;<p>', 'string on the left is escaped')
    is_ok(t('<p>') + html('<b>'), '<p><b>', 'markup')
    is_ok(html('<b>') + t('<p>'), '<b><p>', 'markup on the left')
    is_ok(t('<p>') + Markup('<b>'), '<p><b>', 'markup of another library')
    throws_ok(lambda: t('a') + 1, TypeError, re.compile('unsupported operand'))
    throws_ok(lambda: 1 + t('a'), TypeError, re.compile('unsupported operand'))

done_testing()
