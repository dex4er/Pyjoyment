from Pyjo.Test import *

import contextlib
import io
import os
import tempfile


with subtest('Synopsis'):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        from Pyjo.Template import Template

        # Use Python modules
        mt = Template()
        print(
            mt.render("""
% import time
<div>
  % now = time.gmtime(0)
  Time: <%= time.strftime('%H:%M:%S', now) %>
</div>
""")
        )
    is_ok(output.getvalue(), '\n<div>\n  Time: 00:00:00\n</div>\n\n', 'output')

    # Or import the module, as in Google Python Style Guide
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        import Pyjo.Template

        # Use Python modules
        mt = Pyjo.Template.new()
        print(
            mt.render("""
% import time
<div>
  % now = time.gmtime(0)
  Time: <%= time.strftime('%H:%M:%S', now) %>
</div>
""")
        )

        # Render with arguments
        print(
            mt.render(
                """
% numbers, title = args
<div>
  <h1><%= title %></h1>
  % for i in numbers {
    Test <%= i %>
  % }
</div>
""",
                range(1, 14),
                'Hello World!',
            )
        )

        # Render with named variables
        print(
            Pyjo.Template.new(vars=True).render(
                """
<div>
  <h1><%= title %></h1>
  %= 5 + 5
</div>
""",
                {'title': 'Hello World!'},
            )
        )
    tests = ''.join(f'    Test {i}\n' for i in range(1, 14))
    is_ok(
        output.getvalue(),
        '\n<div>\n  Time: 00:00:00\n</div>\n\n'
        + f'\n<div>\n  <h1>Hello World!</h1>\n{tests}</div>\n\n'
        + '\n<div>\n  <h1>Hello World!</h1>\n  10\n</div>\n\n',
        'output',
    )

with subtest('Syntax'):
    mt = Pyjo.Template.new()
    is_ok(
        mt.render("""% from Pyjo.String.HTML import html
<%= html('<div>excluded!</div>') %>
"""),
        '<div>excluded!</div>\n',
        'markup',
    )
    is_ok(
        mt.render("""% for name in ['Baerbel', 'Wolfgang']:
  % if name.startswith('B'):
<b><%= name %></b>
  % else:
<i><%= name %></i>
  % end
% end
<% for i in range(3) { %><%= i %><% } %>
"""),
        '<b>Baerbel</b>\n<i>Wolfgang</i>\n012\n',
        'blocks',
    )
    is_ok(
        mt.render("""<% for i in range(1, 4) { %>
  <%= 'Trim all whitespace characters around this expression' =%>
<% } %>
"""),
        '\n' + 'Trim all whitespace characters around this expression\n' * 3,
        'trimmed',
    )
    is_ok(
        mt.render("""This is <%= 1 + 1 %> a\\
single line
"""),
        'This is 2 asingle line\n',
        'escaped newline',
    )
    is_ok(
        mt.render("""This will <%= 1 + 1 %> result\\\\
in multiple\\\\
lines
"""),
        'This will 2 result\\\nin multiple\\\nlines\n',
        'escaped backslash',
    )
    is_ok(
        mt.render("""There is <%= 1 + 1 %> no newline at the end here\\
"""),
        'There is 2 no newline at the end here',
        'no newline',
    )
    is_ok(
        mt.render("""<% block = begin %>
  <% name = args[0] =%>
  Hello <%= name %>.
<% end %>
<%= block('Baerbel') %>
<%= block('Wolfgang') %>
"""),
        '\n\n  Hello Baerbel.\n\n\n  Hello Wolfgang.\n\n',
        'capture',
    )
    is_ok(
        mt.render("""% block = begin
  % name = args[0]
  Hello <%= name %>.
% end
%= block('Baerbel')
%= block('Wolfgang')
"""),
        '  Hello Baerbel.\n\n  Hello Wolfgang.\n\n',
        'capture with python lines',
    )
    is_ok(
        mt.render(
            """% foo, bar = args
% x = args[0]
test 123 <%= foo %>
""",
            'a',
            'b',
        ),
        'test 123 a\n',
        'arguments',
    )
    output = mt.render("""<html>
</head>
<body>
% i = 2; xx
%= i * 2
</body>
""")
    like_ok(
        str(output),
        r"""^name 'xx' is not defined at template line 4\.
Context:
  1: <html>
  2: </head>
  3: <body>
  4: % i = 2; xx
  5: %= i \* 2
  6: </body>
Traceback \(most recent call first\):
  File "template", line 4, in "_template"
""",
        'exception',
    )

with subtest('auto_escape'):
    boolean = mt.auto_escape
    is_ok(boolean, None, 'boolean')
    mt.auto_escape = True
    is_ok(mt.auto_escape, True, 'auto_escape')

    # "&lt;html&gt;"
    is_ok(Pyjo.Template.new(auto_escape=True).render("<%= '<html>' %>"), '&lt;html&gt;\n', 'escaped')

with subtest('append'):
    code = mt.append
    is_ok(code, '', 'code')
    mt.append = 'print("Processed template")'
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        mt.render('test')
    is_ok(output.getvalue(), 'Processed template\n', 'appended')

with subtest('capture_end'):
    end = mt.capture_end
    is_ok(end, 'end', 'end')
    mt.capture_end = 'end'

with subtest('capture_start'):
    start = mt.capture_start
    is_ok(start, 'begin', 'start')
    mt.capture_start = 'begin'

with subtest('code'):
    code = mt.code
    like_ok(code, r'test', 'code')
    mt.code = code

with subtest('comment_mark'):
    mark = mt.comment_mark
    is_ok(mark, '#', 'mark')
    mt.comment_mark = '#'

with subtest('compiled'):
    compiled = mt.compiled
    ok(callable(compiled), 'compiled')
    mt.compiled = compiled

with subtest('encoding'):
    encoding = mt.encoding
    is_ok(encoding, 'UTF-8', 'encoding')
    mt.encoding = 'UTF-8'

with subtest('escape'):
    cb = mt.escape
    is_ok(cb('<b>'), '&lt;b&gt;', 'cb')
    mt.escape = lambda value: str(value)[::-1]
    is_ok(mt.render('<%= "abc" %>'), 'cba\n', 'reversed')
    mt.escape = cb

with subtest('escape_mark'):
    mark = mt.escape_mark
    is_ok(mark, '=', 'mark')
    mt.escape_mark = '='

with subtest('expression_mark'):
    mark = mt.expression_mark
    is_ok(mark, '=', 'mark')
    mt.expression_mark = '='

with subtest('line_start'):
    start = mt.line_start
    is_ok(start, '%', 'start')
    mt.line_start = '%'

with subtest('name'):
    name = mt.name
    is_ok(name, 'template', 'name')
    mt.name = 'foo.ep'
    is_ok(mt.name, 'foo.ep', 'name')

with subtest('namespace'):
    namespace = mt.namespace
    is_ok(namespace, 'Pyjo.Template.Sandbox', 'namespace')
    mt.namespace = 'main'
    is_ok(mt.render('<%= __name__ %>'), 'main\n', 'module of its own')

with subtest('prepend'):
    code = mt.prepend
    is_ok(code, '', 'code')
    mt.prepend = 'this = args[0]'
    mt.append = ''
    is_ok(mt.render('<%= this %>', 'that'), 'that\n', 'prepended')
    mt.prepend = ''

with subtest('replace_mark'):
    mark = mt.replace_mark
    is_ok(mark, '%', 'mark')
    mt.replace_mark = '%'

with subtest('tag_start'):
    start = mt.tag_start
    is_ok(start, '<%', 'start')
    mt.tag_start = '<%'

with subtest('tag_end'):
    end = mt.tag_end
    is_ok(end, '%>', 'end')
    mt.tag_end = '%>'

with subtest('tree'):
    tree = mt.tree
    is_deeply_ok(tree, [], 'tree')
    mt.tree = [['text', 'foo'], ['line']]

with subtest('trim_mark'):
    mark = mt.trim_mark
    is_ok(mark, '=', 'mark')
    mt.trim_mark = '-'
    is_ok(mt.render(' <%= 1 -%> '), '1', 'trimmed')

with subtest('unparsed'):
    unparsed = mt.unparsed
    is_ok(unparsed, ' <%= 1 -%> ', 'unparsed')
    mt.unparsed = '<%= 1 + 1 %>'

with subtest('vars'):
    boolean = mt.vars
    is_ok(boolean, None, 'boolean')
    mt.vars = True

    # "works!"
    is_ok(Pyjo.Template.new(vars=True).render('<%= test %>!', {'test': 'works'}), 'works!\n', 'works')

with subtest('parse'):
    mt = Pyjo.Template.new()
    mt = mt.parse('<%= 1 + 1 %>')
    is_ok(mt.tree[1], ['expr', ' 1 + 1 '], 'tree')

with subtest('process'):
    output = mt.process()
    is_ok(output, '2\n', 'output')
    output = Pyjo.Template.new().parse('<%= args[0] %>').process('bar')
    is_ok(output, 'bar\n', 'output with arguments')
    output = Pyjo.Template.new(vars=True).parse('<%= foo %>').process({'foo': 'bar'})
    is_ok(output, 'bar\n', 'output with named variables')

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        # Parse and process
        print(Pyjo.Template.new().parse('Hello <%= args[0] %>').process('Bender'))

        # Reuse template (for much better performance)
        mt = Pyjo.Template.new()
        print(mt.render('Hello <%= args[0] %>!', 'Bender'))
        print(mt.process('Fry'))
        print(mt.process('Leela'))
    is_ok(output.getvalue(), 'Hello Bender\n\nHello Bender!\n\nHello Fry!\n\nHello Leela!\n\n', 'output')

with subtest('render'):
    output = mt.render('<%= 1 + 1 %>')
    is_ok(output, '2\n', 'output')
    args = (1, 2)
    output = mt.render('<%= args[0] + args[1] %>', *args)
    is_ok(output, '3\n', 'output with arguments')
    output = Pyjo.Template.new(vars=True).render('<%= foo %>', {'foo': 'bar'})
    is_ok(output, 'bar\n', 'output with named variables')

    # Longer version
    output = mt.parse('<%= 1 + 1 %>').process()
    is_ok(output, '2\n', 'longer version')

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        # Render with arguments
        print(Pyjo.Template.new().render('<%= args[0] %>', 'bar'))

        # Render with named variables
        print(Pyjo.Template.new(vars=True).render('<%= foo %>', {'foo': 'bar'}))
    is_ok(output.getvalue(), 'bar\n\nbar\n\n', 'output')

with subtest('render_file'):
    with tempfile.TemporaryDirectory() as tmp:
        for name, content in {'foo.ep': '<%= 1 + 1 %>', 'bar.ep': '<%= foo %>'}.items():
            with open(os.path.join(tmp, name), 'w') as f:
                f.write(content)
        output = Pyjo.Template.new().render_file(os.path.join(tmp, 'foo.ep'))
        is_ok(output, '2\n', 'output')
        output = Pyjo.Template.new().render_file(os.path.join(tmp, 'foo.ep'), 'a')
        is_ok(output, '2\n', 'output with arguments')
        output = Pyjo.Template.new(vars=True).render_file(os.path.join(tmp, 'bar.ep'), {'foo': 'bar'})
        is_ok(output, 'bar\n', 'output with named variables')

done_testing()
