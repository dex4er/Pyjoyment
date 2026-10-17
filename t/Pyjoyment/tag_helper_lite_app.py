r"""
__DATA__
@@ assets.html.ep
<%= asset_tag('/foo.js') %>
<%= asset_tag('/foo.js', **{'async': 'async'}) %>
<%= asset_tag('/foo.css') %>
<%= asset_tag('/foo.css', media='foo') %>
<%= asset_tag('/foo.png') %>
<%= asset_tag('/foo.png', alt='test') %>

@@ tags.html.ep
<%= tag('foo') %>
<%= tag('foo', bar='baz') %>
<%= tag('foo', begin %>Hello<% end, one='t<wo', three='four') %>
<%= tag('div', 'some content', data={'my_test_ID': 1, 'naMe': 'test'}) %>
<%= tag('div', 'some content', data='bar') %>

@@ more_tags.html.ep
%= tag('bar', 'b<a>z')
%= tag('bar', 0)
%= tag('bar', 0, **{'class': 'test'})
%= tag('bar', '', **{'class': 'test'})

@@ small_tags.html.ep
% from Pyjo.String.HTML import html
%= t('div', 'test & 123', id='&lt;')
%= t('div', html('test&nbsp;321'), id=html('&lt;'), data={'foo': html('&gt;')})
%= t('div', begin
  %= t('p', 'just', id=0)
  %= t('p', 0)
%= end)
%= t('div', 'works')

@@ tags_with_error.html.ep
%= tag_with_error('bar', 0)
%= tag_with_error('bar', 0, **{'class': 'test'})
%= tag_with_error('bar', begin
  0
%= end, **{'class': 'test'})

@@ links.html.ep
% import Pyjo.URL
<%= link_to('Pa<th', '/path') %>
<%= link_to('http://example.com/', lambda: 'Foo', title='Foo') %>
<%= link_to('//example.com/', begin %><foo>Example</foo><% end) %>
<%= link_to('Contact', Pyjo.URL.new('mailto:sri@example.com')) %>
<%= link_to('Contact', 'mailto:sri@example.com') %>
<%= link_to('Home', 'links') %>
<%= link_to('Foo', 'form', {'test': 23}, title='Foo') %>
<%= link_to('Bar', '#') %>
<%= link_to('Baz', '#baz') %>
<%= link_to('form', {'test': 23}, begin %>Foo<% end, title='Foo') %>

@@ buttons.html.ep
%= button_to('First test', 'links')
%= button_to('Second', 'links', {'format': 'txt'})
%= button_to('Third', '/', **{'class': 'menu'})
%= button_to('Fourth', 'http://example.com')
%= button_to('Fifth', 'selection')

@@ script.html.ep
<%= javascript('/script.js') %>
<%= javascript('/script.js', **{'async': None}) %>
<%= javascript(begin %>
  const a = 'b';
<% end) %>
<%= javascript(begin %>
  const a = 'b';
<% end, type='foo') %>

@@ style.html.ep
<%= stylesheet('/foo.css') %>
<%= stylesheet('/foo.css', title='Test') %>
<%= stylesheet(begin %>
  body {color: #000}
<% end) %>
<%= stylesheet(begin %>
  body {color: #000}
<% end, type='foo') %>

@@ favicon.html.ep
<%= favicon() %>
<%= favicon('/foo.ico') %>

@@ basicform.html.ep
%= form_for('links', begin
  %= label_for('foo', '<Foo>')
  %= text_field('foo', 'bar', id='foo')
  %= label_for('bar', begin
    Bar<br>
  %= end)
  %= text_field('bar', 'baz', id='bar', **{'class': 'test'})
  %= text_field('yada', '')
  %= input_tag('baz', 'yada', **{'class': 'tset'})
  %= submit_button()
%= end)

@@ text.html.ep
%= form_for('text', begin
  %= color_field('color', '#ffffff', **{'class': 'foo'})
  %= date_field('date', '2012-12-12', **{'class': 'foo'})
  %= datetime_field('d', '2012-12-12T23:59:59', **{'class': 'foo'})
  %= email_field('email', 'nospam@example.com', **{'class': 'foo'})
  %= month_field('month', '2012-12', **{'class': 'foo'})
  %= number_field('number', 23, **{'class': 'foo'})
  %= range_field('range', 24, **{'class': 'foo'})
  %= search_field('search', 'perl', **{'class': 'foo'})
  %= tel_field('tel', '123456789', **{'class': 'foo'})
  %= time_field('time', '23:59:59', **{'class': 'foo'})
  %= url_field('url', 'http://mojolicious.org', **{'class': 'foo'})
  %= week_field('week', '2012-W16', **{'class': 'foo'})
  %= submit_button()
%= end)

@@ multibox.html.ep
%= form_for('multibox', begin
  %= check_box('foo')
  %= check_box('foo', 'one')
  %= check_box('foo', 'two')
  %= check_box('foo', 'three', checked=None)
  %= submit_button()
%= end)

@@ form.html.ep
<%= form_for('links', begin %>
  <%= input_tag('foo') %>
<% end, method='post') %>
%= form_for('form', {'test': 24}, begin
  %= text_field('foo')
  %= text_field('foo', 1, data={'id': 1, 'name': 'test'})
  %= text_field('foo', 1, data='ok')
  %= check_box('foo', 1)
  %= check_box('a', 2)
  %= radio_button('b')
  %= radio_button('b', '1')
  %= radio_button('b', '0')
  %= hidden_field('c', 'foo')
  %= file_field('d')
  %= text_area('e', begin
    default!
  %= end, cols=40, rows=50)
  %= text_area('f')
  %= password_field('g')
  %= password_field('h', id='foo')
  %= submit_button('Ok!')
  %= submit_button('Ok too!', id='bar')
%= end, method='post')
<%= form_for('/', begin %>
  <%= input_tag('foo') %>
<% end) %>
<%= input_tag('escaped') %>
<%= input_tag('a') %>
<%= input_tag('a', value='c') %>

@@ selection.html.ep
% if param('preselect'):
%   param('a', 'b', 'g')
% end
% if param('undef'):
%   param('foo', None)
% end
%= form_for('selection', begin
  %= select_field('a', ['b', c.c('c', ['<d', ['E', 'e'], 'f']), 'g'])
  %= select_field('foo', ['bar', 'baz'], multiple='multiple')
  %= select_field('bar', [['D', 'd', {'disabled': 'disabled'}], 'baz'])
  %= select_field('yada', [c.c('test', ['a', 'b'], {'class': 'x'})])
  %= select_field('h', [['I', 'i', {'selected': None}], ['J', 'j']])
  %= submit_button()
%= end)

@@ snowman.html.ep
%= form_for('snowman', begin
  %= text_area('foo', 'b<a>r', cols=40)
  %= submit_button('☃')
%= end)

@@ no_snowman.html.ep
% attrs = {'method': 'PATCH'} if param('foo') else {}
%= form_for('snowman', begin
  %= text_area('bar', cols=40)
  %= submit_button('whatever')
%= end, **attrs)
"""

import Pyjo.Test.Pyjo

from Pyjo.Test import *
from Pyjoyment.Lite import any, app, get, options, patch, post, put


# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# Not in Mojolicious: the templates of the DATA section are in the docstring, as the requests come before the end of the
# script

get('/assets')

options('tags')

patch('more_tags')

get('small_tags')

get('tags_with_error')

any(['GET', 'POST'], 'links')

get('/buttons')

get('script')

get('style')

get('favicon')

get('/basicform')

post('/text')

get('/multibox')

get('form/:test', 'form')

put('selection')

any(['PATCH', 'POST'], '/☃', 'snowman')

post('/no_snowman')

t = Pyjo.Test.Pyjo.new()

with subtest('Assets'):
    t.get_ok('/assets').status_is(200).content_is("""\
<script src="/assets/foo.ab1234cd5678ef.js"></script>
<script async="async" src="/assets/foo.ab1234cd5678ef.js"></script>
<link href="/assets/foo.ab1234cd5678ef.css" rel="stylesheet">
<link href="/assets/foo.ab1234cd5678ef.css" media="foo" rel="stylesheet">
<img src="/assets/foo.png">
<img alt="test" src="/assets/foo.png">
""")

# Reuse values
values = [app.c('EU', ['de', 'en'])]
is_ok(
    app.select_field('country', values),
    '<select name="country"><optgroup label="EU">'
    + '<option value="de">de</option>'
    + '<option value="en">en</option>'
    + '</optgroup></select>',
    'right result',
)
is_ok(
    app.select_field('country', values),
    '<select name="country"><optgroup label="EU">'
    + '<option value="de">de</option>'
    + '<option value="en">en</option>'
    + '</optgroup></select>',
    'right result',
)

# Basic tags
t.options_ok('/tags').status_is(200).content_is("""\
<foo></foo>
<foo bar="baz"></foo>
<foo one="t&lt;wo" three="four">Hello</foo>
<div data-my-test-id="1" data-name="test">some content</div>
<div data="bar">some content</div>
""")
t.patch_ok('/more_tags').status_is(200).content_is("""\
<bar>b&lt;a&gt;z</bar>
<bar>0</bar>
<bar class="test">0</bar>
<bar class="test"></bar>
""")

# Shortcut
t.get_ok('/small_tags').status_is(200).content_is("""\
<div id="&amp;lt;">test &amp; 123</div>
<div data-foo="&gt;" id="&lt;">test&nbsp;321</div>
<div>
  <p id="0">just</p>
  <p>0</p>
</div>
<div>works</div>
""")

# Tags with error
t.get_ok('/tags_with_error').status_is(200).content_is("""\
<bar class="field-with-error">0</bar>
<bar class="test field-with-error">0</bar>
<bar class="test field-with-error">
  0
</bar>
""")

# Links
t.get_ok('/links').status_is(200).content_is("""\
<a href="/path">Pa&lt;th</a>
<a href="http://example.com/" title="Foo">Foo</a>
<a href="//example.com/"><foo>Example</foo></a>
<a href="mailto:sri@example.com">Contact</a>
<a href="mailto:sri@example.com">Contact</a>
<a href="/links">Home</a>
<a href="/form/23" title="Foo">Foo</a>
<a href="#">Bar</a>
<a href="#baz">Baz</a>
<a href="/form/23" title="Foo">Foo</a>
""")
t.post_ok('/links').status_is(200).content_is("""\
<a href="/path">Pa&lt;th</a>
<a href="http://example.com/" title="Foo">Foo</a>
<a href="//example.com/"><foo>Example</foo></a>
<a href="mailto:sri@example.com">Contact</a>
<a href="mailto:sri@example.com">Contact</a>
<a href="/links">Home</a>
<a href="/form/23" title="Foo">Foo</a>
<a href="#">Bar</a>
<a href="#baz">Baz</a>
<a href="/form/23" title="Foo">Foo</a>
""")

# Buttons
(
    t.get_ok('/buttons')
    .status_is(200)
    .content_is(
        '<form action="/links">'
        + '<input type="submit" value="First test">'
        + '</form>\n'
        + '<form action="/links.txt">'
        + '<input type="submit" value="Second">'
        + '</form>\n'
        + '<form action="/" class="menu">'
        + '<input type="submit" value="Third">'
        + '</form>\n'
        + '<form action="http://example.com">'
        + '<input type="submit" value="Fourth">'
        + '</form>\n'
        + '<form action="/selection?_method=PUT" method="POST">'
        + '<input type="submit" value="Fifth">'
        + '</form>\n'
    )
)

# Scripts
t.get_ok('/script').status_is(200).content_is("""\
<script src="/script.js"></script>
<script async src="/script.js"></script>
<script>//<![CDATA[

  const a = 'b';

//]]></script>
<script type="foo">//<![CDATA[

  const a = 'b';

//]]></script>
""")

# Stylesheets
t.get_ok('/style').status_is(200).content_is("""\
<link href="/foo.css" rel="stylesheet">
<link href="/foo.css" rel="stylesheet" title="Test">
<style>/*<![CDATA[*/

  body {color: #000}

/*]]>*/</style>
<style type="foo">/*<![CDATA[*/

  body {color: #000}

/*]]>*/</style>
""")

# Favicon
t.get_ok('/favicon').status_is(200).content_is("""\
<link href="/favicon.ico" rel="icon">
<link href="/foo.ico" rel="icon">
""")

# Basic form
t.get_ok('/basicform').status_is(200).content_is("""\
<form action="/links">
  <label for="foo">&lt;Foo&gt;</label>
  <input id="foo" name="foo" type="text" value="bar">
  <label for="bar">
    Bar<br>
  </label>
  <input class="test" id="bar" name="bar" type="text" value="baz">
  <input name="yada" type="text" value="">
  <input class="tset" name="baz" value="yada">
  <input type="submit" value="Ok">
</form>
""")

# Text input fields
t.post_ok('/text').status_is(200).content_is("""\
<form action="/text" method="POST">
  <input class="foo" name="color" type="color" value="#ffffff">
  <input class="foo" name="date" type="date" value="2012-12-12">
  <input class="foo" name="d" type="datetime-local" value="2012-12-12T23:59:59">
  <input class="foo" name="email" type="email" value="nospam@example.com">
  <input class="foo" name="month" type="month" value="2012-12">
  <input class="foo" name="number" type="number" value="23">
  <input class="foo" name="range" type="range" value="24">
  <input class="foo" name="search" type="search" value="perl">
  <input class="foo" name="tel" type="tel" value="123456789">
  <input class="foo" name="time" type="time" value="23:59:59">
  <input class="foo" name="url" type="url" value="http://mojolicious.org">
  <input class="foo" name="week" type="week" value="2012-W16">
  <input type="submit" value="Ok">
</form>
""")

# Text input fields with values
(
    t.post_ok(
        '/text',
        form={
            'color': '#000000',
            'date': '2012-12-13',
            'd': '2012-12-13T23:59:59',
            'email': 'spam@example.com',
            'month': '2012-11',
            'number': 25,
            'range': 26,
            'search': 'c',
            'tel': '987654321',
            'time': '23:59:58',
            'url': 'http://example.com',
            'week': '2012-W17',
        },
    )
    .status_is(200)
    .content_is("""\
<form action="/text" method="POST">
  <input class="foo" name="color" type="color" value="#000000">
  <input class="foo" name="date" type="date" value="2012-12-13">
  <input class="foo" name="d" type="datetime-local" value="2012-12-13T23:59:59">
  <input class="foo" name="email" type="email" value="spam@example.com">
  <input class="foo" name="month" type="month" value="2012-11">
  <input class="foo" name="number" type="number" value="25">
  <input class="foo" name="range" type="range" value="26">
  <input class="foo" name="search" type="search" value="c">
  <input class="foo" name="tel" type="tel" value="987654321">
  <input class="foo" name="time" type="time" value="23:59:58">
  <input class="foo" name="url" type="url" value="http://example.com">
  <input class="foo" name="week" type="week" value="2012-W17">
  <input type="submit" value="Ok">
</form>
""")
)

# Checkboxes
t.get_ok('/multibox').status_is(200).content_is("""\
<form action="/multibox">
  <input name="foo" type="checkbox">
  <input name="foo" type="checkbox" value="one">
  <input name="foo" type="checkbox" value="two">
  <input checked name="foo" type="checkbox" value="three">
  <input type="submit" value="Ok">
</form>
""")

# Checkboxes with one value
t.get_ok('/multibox?foo=two').status_is(200).content_is("""\
<form action="/multibox">
  <input name="foo" type="checkbox">
  <input name="foo" type="checkbox" value="one">
  <input checked name="foo" type="checkbox" value="two">
  <input name="foo" type="checkbox" value="three">
  <input type="submit" value="Ok">
</form>
""")

# Checkboxes with one right and one wrong value
t.get_ok('/multibox?foo=one&foo=four').status_is(200).content_is("""\
<form action="/multibox">
  <input name="foo" type="checkbox">
  <input checked name="foo" type="checkbox" value="one">
  <input name="foo" type="checkbox" value="two">
  <input name="foo" type="checkbox" value="three">
  <input type="submit" value="Ok">
</form>
""")

# Checkboxes with wrong value
t.get_ok('/multibox?foo=bar').status_is(200).content_is("""\
<form action="/multibox">
  <input name="foo" type="checkbox">
  <input name="foo" type="checkbox" value="one">
  <input name="foo" type="checkbox" value="two">
  <input name="foo" type="checkbox" value="three">
  <input type="submit" value="Ok">
</form>
""")

# Checkboxes with multiple values
t.get_ok('/multibox?foo=two&foo=one&foo=on').status_is(200).content_is("""\
<form action="/multibox">
  <input checked name="foo" type="checkbox">
  <input checked name="foo" type="checkbox" value="one">
  <input checked name="foo" type="checkbox" value="two">
  <input name="foo" type="checkbox" value="three">
  <input type="submit" value="Ok">
</form>
""")

# Advanced form with values
t.get_ok('/form/lala?a=3&a=2&b=0&c=2&d=3&escaped=1%22+%222').status_is(200).content_is("""\
<form action="/links" method="post">
  <input name="foo">
</form>
<form action="/form/24" method="post">
  <input name="foo" type="text">
  <input data-id="1" data-name="test" name="foo" type="text" value="1">
  <input data="ok" name="foo" type="text" value="1">
  <input name="foo" type="checkbox" value="1">
  <input checked name="a" type="checkbox" value="2">
  <input name="b" type="radio">
  <input name="b" type="radio" value="1">
  <input checked name="b" type="radio" value="0">
  <input name="c" type="hidden" value="foo">
  <input name="d" type="file">
  <textarea cols="40" name="e" rows="50">
    default!
  </textarea>
  <textarea name="f"></textarea>
  <input name="g" type="password">
  <input id="foo" name="h" type="password">
  <input type="submit" value="Ok!">
  <input id="bar" type="submit" value="Ok too!">
</form>
<form action="/">
  <input name="foo">
</form>
<input name="escaped" value="1&quot; &quot;2">
<input name="a" value="2">
<input name="a" value="2">
""")

# Advanced form with different values
t.get_ok('/form/lala?c=b&d=3&e=4&f=<5&b=on').status_is(200).content_is("""\
<form action="/links" method="post">
  <input name="foo">
</form>
<form action="/form/24" method="post">
  <input name="foo" type="text">
  <input data-id="1" data-name="test" name="foo" type="text" value="1">
  <input data="ok" name="foo" type="text" value="1">
  <input name="foo" type="checkbox" value="1">
  <input name="a" type="checkbox" value="2">
  <input checked name="b" type="radio">
  <input name="b" type="radio" value="1">
  <input name="b" type="radio" value="0">
  <input name="c" type="hidden" value="foo">
  <input name="d" type="file">
  <textarea cols="40" name="e" rows="50">4</textarea>
  <textarea name="f">&lt;5</textarea>
  <input name="g" type="password">
  <input id="foo" name="h" type="password">
  <input type="submit" value="Ok!">
  <input id="bar" type="submit" value="Ok too!">
</form>
<form action="/">
  <input name="foo">
</form>
<input name="escaped">
<input name="a">
<input name="a" value="c">
""")

# Empty selection
(
    t.put_ok('/selection')
    .status_is(200)
    .content_is(
        '<form action="/selection?_method=PUT" method="POST">\n  '
        + '<select name="a">'
        + '<option value="b">b</option>'
        + '<optgroup label="c">'
        + '<option value="&lt;d">&lt;d</option>'
        + '<option value="e">E</option>'
        + '<option value="f">f</option>'
        + '</optgroup>'
        + '<option value="g">g</option>'
        + '</select>\n  '
        + '<select multiple="multiple" name="foo">'
        + '<option value="bar">bar</option>'
        + '<option value="baz">baz</option>'
        + '</select>\n  '
        + '<select name="bar">'
        + '<option disabled="disabled" value="d">D</option>'
        + '<option value="baz">baz</option>'
        + '</select>\n  '
        + '<select name="yada">'
        + '<optgroup class="x" label="test">'
        + '<option value="a">a</option>'
        + '<option value="b">b</option>'
        + '</optgroup>'
        + '</select>\n  '
        + '<select name="h">'
        + '<option selected value="i">I</option>'
        + '<option value="j">J</option>'
        + '</select>\n  '
        + '<input type="submit" value="Ok">'
        + '\n</form>\n'
    )
)

# Selection with values
(
    t.put_ok('/selection?a=e&foo=bar&bar=baz&yada=b&h=j')
    .status_is(200)
    .content_is(
        '<form action="/selection?_method=PUT" method="POST">\n  '
        + '<select name="a">'
        + '<option value="b">b</option>'
        + '<optgroup label="c">'
        + '<option value="&lt;d">&lt;d</option>'
        + '<option selected value="e">E</option>'
        + '<option value="f">f</option>'
        + '</optgroup>'
        + '<option value="g">g</option>'
        + '</select>\n  '
        + '<select multiple="multiple" name="foo">'
        + '<option selected value="bar">bar</option>'
        + '<option value="baz">baz</option>'
        + '</select>\n  '
        + '<select name="bar">'
        + '<option disabled="disabled" value="d">D</option>'
        + '<option selected value="baz">baz</option>'
        + '</select>\n  '
        + '<select name="yada">'
        + '<optgroup class="x" label="test">'
        + '<option value="a">a</option>'
        + '<option selected value="b">b</option>'
        + '</optgroup>'
        + '</select>\n  '
        + '<select name="h">'
        + '<option value="i">I</option>'
        + '<option selected value="j">J</option>'
        + '</select>\n  '
        + '<input type="submit" value="Ok">'
        + '\n</form>\n'
    )
)

# Selection with multiple values
(
    t.put_ok('/selection?foo=bar&a=e&foo=baz&bar=d&yada=a&yada=b&h=i&h=j')
    .status_is(200)
    .content_is(
        '<form action="/selection?_method=PUT" method="POST">\n  '
        + '<select name="a">'
        + '<option value="b">b</option>'
        + '<optgroup label="c">'
        + '<option value="&lt;d">&lt;d</option>'
        + '<option selected value="e">E</option>'
        + '<option value="f">f</option>'
        + '</optgroup>'
        + '<option value="g">g</option>'
        + '</select>\n  '
        + '<select multiple="multiple" name="foo">'
        + '<option selected value="bar">bar</option>'
        + '<option selected value="baz">baz</option>'
        + '</select>\n  '
        + '<select name="bar">'
        + '<option disabled="disabled" selected value="d">D</option>'
        + '<option value="baz">baz</option>'
        + '</select>\n  '
        + '<select name="yada">'
        + '<optgroup class="x" label="test">'
        + '<option selected value="a">a</option>'
        + '<option selected value="b">b</option>'
        + '</optgroup>'
        + '</select>\n  '
        + '<select name="h">'
        + '<option selected value="i">I</option>'
        + '<option selected value="j">J</option>'
        + '</select>\n  '
        + '<input type="submit" value="Ok">'
        + '\n</form>\n'
    )
)

# Selection with multiple values preselected
(
    t.put_ok('/selection?preselect=1&undef=1')
    .status_is(200)
    .content_is(
        '<form action="/selection?_method=PUT" method="POST">\n  '
        + '<select name="a">'
        + '<option selected value="b">b</option>'
        + '<optgroup label="c">'
        + '<option value="&lt;d">&lt;d</option>'
        + '<option value="e">E</option>'
        + '<option value="f">f</option>'
        + '</optgroup>'
        + '<option selected value="g">g</option>'
        + '</select>\n  '
        + '<select multiple="multiple" name="foo">'
        + '<option value="bar">bar</option>'
        + '<option value="baz">baz</option>'
        + '</select>\n  '
        + '<select name="bar">'
        + '<option disabled="disabled" value="d">D</option>'
        + '<option value="baz">baz</option>'
        + '</select>\n  '
        + '<select name="yada">'
        + '<optgroup class="x" label="test">'
        + '<option value="a">a</option>'
        + '<option value="b">b</option>'
        + '</optgroup>'
        + '</select>\n  '
        + '<select name="h">'
        + '<option selected value="i">I</option>'
        + '<option value="j">J</option>'
        + '</select>\n  '
        + '<input type="submit" value="Ok">'
        + '\n</form>\n'
    )
)

# Snowman form
t.post_ok('/☃').status_is(200).content_is("""\
<form action="/%E2%98%83" method="POST">
  <textarea cols="40" name="foo">b&lt;a&gt;r</textarea>
  <input type="submit" value="☃">
</form>
""")

# Snowman form with value
t.post_ok('/☃?foo=ba<z').status_is(200).content_is("""\
<form action="/%E2%98%83" method="POST">
  <textarea cols="40" name="foo">ba&lt;z</textarea>
  <input type="submit" value="☃">
</form>
""")

# Snowman form with empty value
t.patch_ok('/☃?foo=').status_is(200).content_is("""\
<form action="/%E2%98%83" method="POST">
  <textarea cols="40" name="foo"></textarea>
  <input type="submit" value="☃">
</form>
""")

# Snowman POST form
t.post_ok('/no_snowman').status_is(200).content_is("""\
<form action="/%E2%98%83" method="POST">
  <textarea cols="40" name="bar"></textarea>
  <input type="submit" value="whatever">
</form>
""")

# Form with alternative method
t.post_ok('/no_snowman?foo=1').status_is(200).content_is("""\
<form action="/%E2%98%83" method="PATCH">
  <textarea cols="40" name="bar"></textarea>
  <input type="submit" value="whatever">
</form>
""")

done_testing()
