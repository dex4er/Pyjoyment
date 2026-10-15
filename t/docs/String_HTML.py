from Pyjo.Test import *

import contextlib
import io


with subtest('Synopsis'):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        from Pyjo.String.HTML import html

        # Markup that is not escaped again
        link = html('<a href="/">Home</a>')

        # What is added to markup is escaped
        name = '<script>'
        print(html('<p>') + name + html('</p>'))

        # And what goes into it
        print(html('<p>{}</p>').format(name))
        print(html('<br>').join(['Hello', name]))
    is_ok(
        output.getvalue(),
        '<p>&lt;script&gt;</p>\n<p>&lt;script&gt;</p>\nHello<br>&lt;script&gt;\n',
        'output',
    )
    is_ok(link, '<a href="/">Home</a>', 'link')

with subtest('Description'):
    # "&lt;p&gt;"
    is_ok(html('<p>').xml_escape(), '&lt;p&gt;', 'xml_escape')

with subtest('html'):
    string = html('<p>Hello</p>')
    is_ok(string, '<p>Hello</p>', 'string')

with subtest('__add__'):
    other = '<b>'
    string = html('<p>')
    string = string + other
    is_ok(string, '<p>&lt;b&gt;', 'escaped')

with subtest('__html__'):
    markup = string.__html__()
    is_ok(markup, '<p>&lt;b&gt;', 'markup')

with subtest('__mod__'):
    value = '<b>'
    string = html('<p>%s</p>')
    string = string % value
    is_ok(string, '<p>&lt;b&gt;</p>', 'value')
    string = html('<p>%s %s</p>') % (value, value)
    is_ok(string, '<p>&lt;b&gt; &lt;b&gt;</p>', 'tuple')
    string = html('<p>%(name)s</p>') % {'name': value}
    is_ok(string, '<p>&lt;b&gt;</p>', 'mapping')

with subtest('__mul__'):
    string = html('<hr>')
    string = string * 3
    is_ok(string, '<hr><hr><hr>', 'repeated')

with subtest('__radd__'):
    other = '<b>'
    string = html('<p>')
    string = other + string
    is_ok(string, '&lt;b&gt;<p>', 'escaped')

with subtest('__rmul__'):
    string = html('<hr>')
    string = 3 * string
    is_ok(string, '<hr><hr><hr>', 'repeated')

with subtest('format'):
    value = '<b>'
    string = html('<p>{} {name}</p>').format(value, name=value)
    is_ok(string, '<p>&lt;b&gt; &lt;b&gt;</p>', 'escaped')

with subtest('format_map'):
    value = '<b>'
    string = html('<p>{name}</p>').format_map({'name': value})
    is_ok(string, '<p>&lt;b&gt;</p>', 'escaped')

with subtest('join'):
    string = html('<br>').join(['Hello', 'World'])
    is_ok(string, 'Hello<br>World', 'joined')

done_testing()
