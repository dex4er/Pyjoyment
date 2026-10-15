# /// script
# requires-python = ">=3.14"
# ///
import Pyjo.String.HTML
import Pyjo.String.Template

from Pyjo.String.HTML import html
from Pyjo.String.Template import Interpolation, t
from Pyjo.Test import *

import string.templatelib


name = '<script>'
width = 10

with subtest('Interpolation'):
    ok(Interpolation is string.templatelib.Interpolation, 'Interpolation of Python')

with subtest('Constructor'):
    template = t(t'<p>{name}</p>')
    isa_ok(template, Pyjo.String.Template.object, 't-string')
    is_ok(template.strings, ('<p>', '</p>'), 'strings')
    is_ok(template.values, ('<script>',), 'values')
    is_ok(template.interpolations[0].expression, 'name', 'expression')
    is_ok(template, '<p>&lt;script&gt;</p>', 'rendered')
    is_ok(t(t''), '', 'empty')

with subtest('Same as the emulation'):
    for native, emulated in [
        (t'<p>{name}</p>', t('<p>{name}</p>')),
        (t'{name!r:>{width}}', t('{name!r:>{width}}')),
        (t'{name=}', t('{name=}')),
        (t'{ name = }', t('{ name = }')),
        (t'{name=:>{width}}', t('{name=:>{width}}')),
        (t'{name}{name}', t('{name}{name}')),
        (t'{{{name}}}', t('{{{name}}}')),
    ]:
        native = t(native)
        description = repr(emulated)
        is_ok(native.strings, emulated.strings, f'strings of {description}')
        is_deeply_ok(
            [(i.value, i.expression, i.conversion, i.format_spec) for i in native.interpolations],
            [(i.value, i.expression, i.conversion, i.format_spec) for i in emulated.interpolations],
            f'interpolations of {description}',
        )
        is_ok(native, emulated, f'rendered {description}')

with subtest('Expressions'):
    is_ok(t(t'{len(name)}'), '8', 'call')
    is_ok(t(t'{name.upper()}'), '&lt;SCRIPT&gt;', 'method')
    is_ok(t(t'{name if name else "-"}'), '&lt;script&gt;', 'conditional')
    is_ok(t(t'{html(name)}'), '<script>', 'markup')

with subtest('Nested templates'):

    def link_to(text, url):
        return t(t'<a href="{url}">{text}</a>')

    is_ok(t(t'<li>{link_to(name, "/user")}</li>'), '<li><a href="/user">&lt;script&gt;</a></li>', 'helper')
    is_ok(t(t'<p>{t"<b>{name}</b>"}</p>'), '<p><b>&lt;script&gt;</b></p>', 't-string in a t-string')
    tags = ['<b>', '<i>']
    is_ok(
        t(t'<ul>{[t"<li>{tag}</li>" for tag in tags]}</ul>'),
        '<ul><li>&lt;b&gt;</li><li>&lt;i&gt;</li></ul>',
        't-strings in a list',
    )
    is_ok(t(t'{(t"{tag}," for tag in tags)}'), '&lt;b&gt;,&lt;i&gt;,', 't-strings in a generator')

with subtest('Concatenation'):
    template = t(t'<p>{name}') + t'</p>'
    isa_ok(template, Pyjo.String.Template.object, 'with a t-string')
    is_ok(template, '<p>&lt;script&gt;</p>', 'rendered')
    template = t'<p>' + t(t'{name}</p>')
    isa_ok(template, Pyjo.String.Template.object, 'with a t-string on the left')
    is_ok(template, '<p>&lt;script&gt;</p>', 'rendered on the left')
    string = html('<p>') + t(t'{name}')
    isa_ok(string, Pyjo.String.HTML.object, 'markup')
    is_ok(string, '<p>&lt;script&gt;', 'markup rendered')

done_testing()
