r"""
__DATA__
@@ layouts/default.html.ep
Default<%= c.title() %><%= content() %>

@@ layouts/green.html.ep
Green<%= c.title() %><%= content() %>

@@ layouts/mixed.txt.ep
Mixed <%= content() %>

@@ blue.html.ep
% c.layout(None)
Blue<%= c.title() %><%= content() %>

@@ works.html.ep
% c.title('Just works')
% if param('green'):
%   c.layout('green')
% end
% if param('blue'):
%   c.extends('blue')
% end
This <template> just works!

@@ mixed.html.ep
% c.layout('mixed', format='txt')
formats

@@ exception.html.ep
% c.title('Exception happened')
% if param('green'):
%   c.layout('green')
% end
% if param('blue'):
%   c.extends('blue')
% end
Exception happened!

@@ not_found.html.ep
% c.title('Not found happened')
% if param('green'):
%   c.layout('green')
% end
% if param('blue'):
%   c.extends('blue')
% end
Not found happened!

@@ first.html.ep
%= content('header', begin
  Default header
% end)
Stuff
%= content('footer', begin
  Default footer
% end)

@@ second.html.ep
% c.extends('first')
% content('header', begin
  New header
% end)

@@ third.html.ep
% c.extends('second')
% content('footer', begin
  New footer
% end)

@@ template_inheritance.html.ep
% from Pyjo.String.HTML import html
% c.layout('template_inheritance')
% c.title('Works!')
<% content('header', begin =%>
<%= html('<br>') %>
<% end) =%>
<% content('sidebar', begin =%>
Sidebar!
<% end) =%>
Hello World!

@@ layouts/template_inheritance.html.ep
<title><%= c.title() %></title>
% stash(foo='Default')
<%= content('header', begin =%>
Default header!
<% end) =%>
<%= content('sidebar', begin =%>
<%= stash('foo') %> sidebar!
<% end) =%>
%= content()
<%= content('footer', begin =%>
Default footer!
<% end) =%>

@@ double_inheritance.html.ep
% c.extends('template_inheritance')
<% content('sidebar', begin =%>
Sidebar too!
<% end) =%>

@@ triple_inheritance.html.ep
% c.extends('double_inheritance')
New <content>.
%= content_for('stuff')

@@ layouts/plugin_with_template.html.ep
layout_with_template
<%= content() %>

@@ nested-includes.html.ep
Nested <%= include('outerlayout') %>

@@ localized.html.ep
% c.extends('localized1')
% c.layout(None)
<%= test %>
<%= include('localized_include', test=321, extends='localized2') %>
<%= test %>

@@ localized_include.html.ep
<%= test %>

@@ localized1.html.ep
localized1 <%= content() %>

@@ localized2.html.ep
localized2 <%= content() %>

@@ outerlayout.html.ep
%== c.c('>', 'o', 'l', 'l', 'e', 'H', '<').reverse().join()
<%= c.render_to_string('outermenu') %>

@@ outermenu.html.ep
% stash(test='there')
<%= dumper([1, 2]) %><%= stash('test') %><br>!

@@ outerinnerlayout.html.ep
Hello
<%= include('outermenu', layout='layout') %>

@@ layouts/layout.html.ep
layouted <%== content() %>

@@ index.html.epl
Just works!\

@@ layouts/with_block.html.epl
<% block = begin %>
<% one, two = args %>
One: <%= one %>
Two: <%= two %>
<% end %>
with_block <%= block('one', 'two') %>

@@ layouts/content_for.html.ep
Content<%= c.title() %><%= content_for('more') %><%= content() %>

@@ content_for.html.ep
% c.layout('content_for')
This
<% content_for('message', begin =%>Hello<% end) %>
seems
% content_for('message', begin
    World!
% end)
to
<%= content_for('message') %>
%= include('content_for_partial')
%= content_for('stuff')

@@ content_for_partial.html.ep
<% content_for('more', begin %>!<% end) %>work!

@@ content_with.html.ep
<% content('first', begin %>Something<% end) %>
<% content_for('first', begin %> <b>else<% end) %>
% content_for('first', '</b>!')
%= content_with('first')
% content_with('first', '')
%= content_with('first')
<% content('second', begin %>World<% end) %>
<%= content_with('second', begin %><br>Hello <%= content('second') %>!<% end) %>
% content_with('second')

@@ layouts/variants.txt.ep
Variant: <%= content() %>\

@@ layouts/variants.txt+0.ep
Another variant: <%= content() %>\

@@ variants.txt.ep
Desktop!\

@@ variants.txt+tablet.epl
Tablet!\
"""

import Pyjo.Exception
import Pyjo.Test.Pyjo

from Pyjo.File import tempdir
from Pyjo.Test import *
from Pyjo.Util import die
from Pyjoyment.Lite import app, get, hook, plugin

import io
import sys


# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# Unlike Mojolicious: Prove runs every .py file under t, so the plugin of the test is written into a temporary
# directory, where Mojo has it in t/mojolicious/lib
lib = tempdir()
lib.child('PluginWithTemplate.py').spew("""import Pyjoyment.Plugin


class PluginWithTemplate(Pyjoyment.Plugin.object):
    def register(self, app, conf=None):
        app.renderer.classes.append(__name__)
        app.routes.any('/plugin_with_template').to(cb=lambda c: c.render('plugin_with_template'))


object = PluginWithTemplate

__DATA__ = r\'\'\'
@@ plugin_with_template.html.ep
% c.layout('plugin_with_template')
with template
\'\'\'
""")
sys.path.insert(0, lib.to_str())

# Not in Mojolicious: the templates of the DATA section are in the docstring, as the requests come before the end of the
# script

# Unlike Mojolicious: dumper formats with pprint, which writes [1, 2] on one line, where Data::Dumper writes an item on
# each line

# Unlike Mojolicious: the template outerlayout renders the joined collection with %==, as join gives a string, which
# is escaped, where Mojo gives a Mojo::ByteStream, which is not, and the template template_inheritance makes the markup
# with html, where Mojo makes it with b

# Plugin with a template
plugin('PluginWithTemplate')

app.renderer.paths[0] = app.home.child('does_not_exist').to_str()


# Reverse filter
@hook('after_render')
def after_render(c, output, format):
    if not c.stash().get('reverse'):
        return
    value = output.getvalue() + (format.encode() if isinstance(output, io.BytesIO) else format)
    output.seek(0)
    output.truncate()
    output.write(value[::-1])


# Shared content
hook('before_dispatch', lambda c: c.content_for('stuff', 'Shared content!'))

# Default layout for whole application
app.defaults(layout='default')

get('/works')

get('/mixed')

get('/doesnotexist')

get('/dies', lambda c: die(Pyjo.Exception.new('Died')))

get('/template_inheritance', lambda c: c.render('template_inheritance'))

get(
    '/layout_without_inheritance',
    lambda c: c.render(template='layouts/template_inheritance', handler='ep', layout=None),
)

get('/double_inheritance', lambda c: c.render(template='double_inheritance'))

get('/triple_inheritance')

get('/mixed_inheritance/first', {'template': 'first'})

get('/mixed_inheritance/second', {'template': 'second', 'layout': 'green'})

get('/mixed_inheritance/third', {'template': 'third'})


@get('/nested-includes')
def nested_includes(c):
    c.render(template='nested-includes', layout='layout', handler='ep')


@get('/localized/include')
def localized_include(c):
    c.render('localized', test='foo', reverse=1)


get('/plain/reverse', {'text': 'Hello!', 'format': 'foo', 'reverse': 1})


@get('/outerlayout')
def outerlayout(c):
    c.render(template='outerlayout', layout='layout')


@get('/outerextends')
def outerextends(c):
    c.render(template='outerlayout', extends='layouts/layout', layout=None)


def outerlayouttwo(c):
    is_ok(c.stash()['layout'], 'layout', 'right value')
    c.render(handler='ep')
    is_ok(c.stash()['layout'], 'layout', 'right value')


get('/outerlayouttwo', {'layout': 'layout'}, outerlayouttwo, 'outerlayout')


@get('/outerinnerlayout')
def outerinnerlayout(c):
    c.render(template='outerinnerlayout', layout='layout', handler='ep')


@get('/withblocklayout')
def withblocklayout(c):
    c.render(template='index', layout='with_block', handler='epl')


get('/content_for')

get('/content_with')

get('/inline', {'inline': '<%= "inline!" %>'})

get('/inline/again', {'inline': '0'})

get('/data', {'data': b'0'})


def variants(c):
    c.stash()['variant'] = c.param('device')
    c.render('variants')


get('/variants', {'layout': 'variants', 'format': None}, variants, format=['txt'])

t = Pyjo.Test.Pyjo.new()

with subtest('"0" content reassignment'):
    c = t.app.build_controller()
    c.content('foo', '0')
    is_ok(c.content('foo'), '0', 'right content')
    c.content('foo', '1')
    is_ok(c.content('foo'), '0', 'right content')

with subtest('Template with layout'):
    (
        t.get_ok('/works')
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .content_is('DefaultJust worksThis <template> just works!\n\n')
    )

with subtest('Different layout'):
    (
        t.get_ok('/works?green=1')
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .content_is('GreenJust worksThis <template> just works!\n\n')
    )

with subtest('Extended'):
    (
        t.get_ok('/works?blue=1')
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .content_is('BlueJust worksThis <template> just works!\n\n')
    )

with subtest('Mixed formats'):
    t.get_ok('/mixed').status_is(200).content_type_is('text/plain;charset=UTF-8').content_is('Mixed formats\n\n')

with subtest('Missing template'):
    t.get_ok('/doesnotexist').status_is(500).content_is('DefaultException happenedException happened!\n\n')

with subtest('Missing template with different layout'):
    t.get_ok('/doesnotexist?green=1').status_is(500).content_is('GreenException happenedException happened!\n\n')

with subtest('Extended missing template'):
    t.get_ok('/doesnotexist?blue=1').status_is(500).content_is('BlueException happenedException happened!\n\n')

with subtest('Extended missing template (not found)'):
    (
        t.get_ok('/doesreallynotexist?green=1')
        .status_is(404)
        .content_is('GreenNot found happenedNot found happened!\n\n')
    )

with subtest('Extended missing template (not found)'):
    t.get_ok('/doesreallynotexist?blue=1').status_is(404).content_is('BlueNot found happenedNot found happened!\n\n')

with subtest('Dead action'):
    t.get_ok('/dies').status_is(500).content_is('DefaultException happenedException happened!\n\n')

with subtest('Dead action with different layout'):
    t.get_ok('/dies?green=1').status_is(500).content_is('GreenException happenedException happened!\n\n')

with subtest('Extended dead action'):
    t.get_ok('/dies?blue=1').status_is(500).content_is('BlueException happenedException happened!\n\n')

with subtest('Template inheritance'):
    (
        t.get_ok('/template_inheritance')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_is('<title>Works!</title>\n<br>\nSidebar!\nHello World!\n\nDefault footer!\n')
    )

with subtest('Just the layout'):
    (
        t.get_ok('/layout_without_inheritance')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_is('<title></title>\nDefault header!\nDefault sidebar!\n\nDefault footer!\n')
    )

with subtest('Double inheritance'):
    (
        t.get_ok('/double_inheritance')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_is('<title>Works!</title>\n<br>\nSidebar too!\n' + 'Hello World!\n\nDefault footer!\n')
    )

with subtest('Triple inheritance'):
    (
        t.get_ok('/triple_inheritance')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_is(
            '<title>Works!</title>\n<br>\nSidebar too!\n' + 'New <content>.\nShared content!\n\nDefault footer!\n'
        )
    )

with subtest('Mixed inheritance (with layout)'):
    (
        t.get_ok('/mixed_inheritance/first')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_is('Default\n  Default header\nStuff\n\n  Default footer\n\n')
    )
    (
        t.get_ok('/mixed_inheritance/second')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_is('Green  New header\nStuff\n\n  Default footer\n\n')
    )
    (
        t.get_ok('/mixed_inheritance/third')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_is('Default  New header\nStuff\n  New footer\n\n')
    )

with subtest('Template from plugin'):
    t.get_ok('/plugin_with_template').status_is(200).content_is('layout_with_template\nwith template\n\n')

with subtest('Nested included templates'):
    (
        t.get_ok('/nested-includes')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_is('layouted Nested <Hello>\n[1, 2]\nthere<br>!\n\n\n\n')
    )

with subtest('Included template with localized stash values'):
    (
        t.get_ok('/localized/include')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_type_is('text/html;charset=UTF-8')
        .content_is('lmth\n\noof\n\n\n123 2dezilacol\noof 1dezilacol')
    )

with subtest('Filter'):
    (
        t.get_ok('/plain/reverse')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_type_is('application/octet-stream')
        .content_is('oof!olleH')
    )

with subtest('Layout in render call'):
    (
        t.get_ok('/outerlayout')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_is('layouted <Hello>\n[1, 2]\nthere<br>!\n\n\n')
    )

with subtest('Extends in render call'):
    (
        t.get_ok('/outerextends')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_is('layouted <Hello>\n[1, 2]\nthere<br>!\n\n\n')
    )

with subtest('Layout in route'):
    (
        t.get_ok('/outerlayouttwo')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_is('layouted <Hello>\n[1, 2]\nthere<br>!\n\n\n')
    )

with subtest('Included template with layout'):
    (
        t.get_ok('/outerinnerlayout')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_is('layouted Hello\nlayouted [1, 2]\nthere<br>!\n\n\n\n')
    )

with subtest('Layout with block'):
    (
        t.get_ok('/withblocklayout')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_is('\nwith_block \n\nOne: one\nTwo: two\n\n')
    )

with subtest('Content blocks'):
    (
        t.get_ok('/content_for')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_is('Content!This\n\nseems\nto\nHello    World!\n\nwork!\n\nShared content!\n\n')
    )
    (
        t.get_ok('/content_with')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_is('Default\n\nSomething <b>else</b>!\n\n\n<br>Hello World!\n\n')
    )

with subtest('Inline template'):
    t.get_ok('/inline').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('inline!\n')

with subtest('"0" inline template'):
    t.get_ok('/inline/again').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('0\n')

with subtest('"0" data'):
    t.get_ok('/data').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('0')

with subtest('Variants (desktop)'):
    (
        t.get_ok('/variants.txt')
        .status_is(200)
        .content_type_is('text/plain;charset=UTF-8')
        .content_is('Variant: Desktop!')
    )

with subtest('Variants (tablet)'):
    (
        t.get_ok('/variants.txt?device=tablet')
        .status_is(200)
        .content_type_is('text/plain;charset=UTF-8')
        .content_is('Variant: Tablet!')
    )

with subtest('Variants (desktop fallback)'):
    (
        t.get_ok('/variants.txt?device=phone')
        .status_is(200)
        .content_type_is('text/plain;charset=UTF-8')
        .content_is('Variant: Desktop!')
    )

with subtest('Variants ("0")'):
    (
        t.get_ok('/variants.txt?device=0')
        .status_is(200)
        .content_type_is('text/plain;charset=UTF-8')
        .content_is('Another variant: Desktop!')
    )

done_testing()
