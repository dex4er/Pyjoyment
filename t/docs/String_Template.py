# /// script
# requires-python = ">=3.14"
# ///
import Pyjo.String.HTML

from Pyjo.Test import *

import contextlib
import io


with subtest('Synopsis'):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        from Pyjo.String.Template import t

        name = '<script>'

        # A t-string of Python 3.14
        print(t(t'<p>{name}</p>'))

        # The same on any Python
        print(t('<p>{name}</p>'))
        print(t('<p>{name}</p>', name=name))

        # A template in a template is markup
        def link_to(text, url):
            return t(t'<a href="{url}">{text}</a>')

        print(t(t'<li>{link_to(name, "/user")}</li>'))
    is_ok(
        output.getvalue(),
        '<p>&lt;script&gt;</p>\n' * 3 + '<li><a href="/user">&lt;script&gt;</a></li>\n',
        'output',
    )

with subtest('Description'):
    import Pyjo.String.Template

    from Pyjo.String.Template import Interpolation

    # "<p>&lt;script&gt;</p>"
    is_ok(
        Pyjo.String.Template.new('<p>', Interpolation(name, 'name'), '</p>'),
        '<p>&lt;script&gt;</p>',
        'new',
    )

    # "<ul><li>&lt;b&gt;</li><li>&lt;i&gt;</li></ul>"
    tags = ['<b>', '<i>']
    is_ok(
        t(t'<ul>{[t"<li>{tag}</li>" for tag in tags]}</ul>'),
        '<ul><li>&lt;b&gt;</li><li>&lt;i&gt;</li></ul>',
        'list of t-strings',
    )

    class User:
        name = '<b>'

    user = User()

    # "<p>&lt;b&gt;</p>"
    is_ok(t('<p>{user.name}</p>', user=user), '<p>&lt;b&gt;</p>', 'attribute')

    # "<p>&lt;b&gt;</p>"
    is_ok(t('<p>{user[name]}</p>', user={'name': '<b>'}), '<p>&lt;b&gt;</p>', 'key')

with subtest('Interpolation'):
    value = '<b>'
    interpolation = Interpolation(value, 'name', 'r', '>10')
    is_ok(interpolation.format_spec, '>10', 'format_spec')

with subtest('Pyjo_String_Template'):
    template = Pyjo.String.Template.new('<p>', Interpolation(name, 'name'), '</p>')
    is_ok(template, '<p>&lt;script&gt;</p>', 'template')

with subtest('__add__'):
    other = t'</p>'
    template = t(t'<p>{name}')
    template = template + other
    is_ok(template, '<p>&lt;script&gt;</p>', 'template')

with subtest('__html__'):
    markup = template.__html__()
    is_ok(markup, '<p>&lt;script&gt;</p>', 'markup')

with subtest('__iter__'):
    items = []
    for item in template:
        items.append(item)
    is_ok(len(items), 3, 'items')

with subtest('__radd__'):
    other = t'<div>'
    template = other + template
    is_ok(template, '<div><p>&lt;script&gt;</p>', 'template')

with subtest('__repr__'):
    string = repr(template)
    like_ok(string, r"^Pyjo\.String\.Template\.new\('<div><p>', Interpolation\(", 'string')

with subtest('interpolations'):
    interpolations = template.interpolations
    is_ok(interpolations[0].expression, 'name', 'interpolations')

with subtest('render'):
    string = template.render()
    isa_ok(string, Pyjo.String.HTML.object, 'markup')

with subtest('strings'):
    strings = template.strings
    is_ok(strings, ('<div><p>', '</p>'), 'strings')

with subtest('to_str'):
    string = template.to_str()
    is_ok(string, '<div><p>&lt;script&gt;</p>', 'string')

with subtest('values'):
    values = template.values
    is_ok(values, ('<script>',), 'values')

with subtest('t'):
    template = t(t'<p>{name}</p>')
    is_ok(template, '<p>&lt;script&gt;</p>', 't-string')
    template = t('<p>{name}</p>')
    is_ok(template, '<p>&lt;script&gt;</p>', 'string')
    template = t('<p>{name}</p>', name=name)
    is_ok(template, '<p>&lt;script&gt;</p>', 'keyword argument')

done_testing()
