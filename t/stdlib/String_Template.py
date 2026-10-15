import Pyjo.String.Template

from Pyjo.String.Template import Interpolation, t
from Pyjo.Test import *

import html
import sys


name = '<script>'
width = 12

with subtest('Fields of str.format'):
    for source in ['<p>{name}</p>', '{name!r}', '{name!a:>{width}}', '{name:*^{width}}', '{{{name}}}']:
        is_ok(html.unescape(str(t(source))), source.format(name=name, width=width), source)

with subtest('Pattern matching'):
    match t('<p>{name!r:>{width}}</p>').interpolations[0]:
        case Interpolation(value, expression, conversion, format_spec):
            is_deeply_ok((value, expression, conversion, format_spec), (name, 'name', 'r', '>12'), 'positional')
        case _:
            fail_ok('positional')

with subtest('Template of Python'):
    if sys.version_info < (3, 14):
        skip('string.templatelib needs Python 3.14', 4)
    else:
        from string.templatelib import Template, convert

        template = t(Template('<p>', Interpolation(name, 'name'), '</p>'))
        isa_ok(template, Pyjo.String.Template.object, 'wrapped')
        is_ok(template, '<p>&lt;script&gt;</p>', 'rendered')
        template = Template(*t('<p>{name!r}</p>'))
        is_ok(template.strings, ('<p>', '</p>'), 'strings of the emulation')
        interpolation = template.interpolations[0]
        is_ok(
            convert(interpolation.value, interpolation.conversion),
            repr(name),
            'interpolation of the emulation is converted',
        )

done_testing()
