import Pyjoyment
import Pyjoyment.Plugin.TagHelpers

from Pyjo.Test import *

import re
import textwrap


# The applications are kept, as a controller refers to its application weakly
apps = []


def controller(query=''):
    # A controller of an application mounted at /path/to, with the routes of the examples
    app = Pyjoyment.new(secrets=['works'])
    app.log.level = 'fatal'
    apps.append(app)
    r = app.routes
    r.get('/get/route/:id', {'id': ''}).set(name='some_get_route')
    r.delete('/delete/route').set(name='some_delete_route')
    r.any('/login', format=['txt']).set(name='login')
    r.get('/index', format=['txt']).set(name='index')
    c = app.build_controller()
    c.req.url.parse(f'http://127.0.0.1:3000/current/path{query}')
    c.req.url.base.parse('http://127.0.0.1:3000/path/to/')
    return c


def render(c, template):
    # The documented template, inline
    return str(c.render_to_string(inline=textwrap.dedent(template)))


def lines(c, template):
    return render(c, template).splitlines()


with subtest('Synopsis'):
    app = Pyjoyment.new()

    # Pyjoyment
    app.plugin('TagHelpers')
    ok(app.renderer.get_helper('form_for'), 'helpers')

    # Pyjoyment.Lite
    from Pyjoyment.Lite import plugin

    plugin('TagHelpers')

with subtest('Description'):
    c = controller()
    is_ok(
        render(
            c,
            """\
            % if not param('country'):
            %   param('country', 'germany')
            % end
            <%= radio_button('country', 'germany') %> Germany
            <%= radio_button('country', 'france') %> France
            <%= radio_button('country', 'uk') %> UK
            """,
        ),
        '<input checked name="country" type="radio" value="germany"> Germany\n'
        '<input name="country" type="radio" value="france"> France\n'
        '<input name="country" type="radio" value="uk"> UK\n',
        'default value',
    )

    c = controller()
    c.req.url.parse('/?age=250')
    c.validation().required('age').num(0, 150)
    is_ok(
        render(c, "%= text_field('age')"),
        '<input class="field-with-error" name="age" type="text" value="250">\n',
        'field with error',
    )

    is_ok(
        render(c, "%= text_field('first_name', **{'class': 'user'}, required=None)"),
        '<input class="user" name="first_name" required type="text">\n',
        'attributes',
    )

    is_ok(
        render(
            c,
            """\
            %= label_for('first_name', begin
              First name
            %= end, **{'class': 'user'})
            """,
        ),
        '<label class="user" for="first_name">\n  First name\n</label>\n',
        'block',
    )

with subtest('asset_tag'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= asset_tag('/app.js')
            %= asset_tag('/app.js', **{'async': 'async'})
            """,
        ),
        [
            '<script src="/path/to/assets/app.js"></script>',
            '<script async="async" src="/path/to/assets/app.js"></script>',
        ],
        'script',
    )

with subtest('button_to'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= button_to('Test', 'some_get_route')
            %= button_to('Test', 'some_get_route', {'id': 23}, **{'class': 'menu'})
            %= button_to('Test', 'http://example.com/test', **{'class': 'menu'})
            %= button_to('Remove', 'some_delete_route')
            """,
        ),
        [
            '<form action="/path/to/get/route"><input type="submit" value="Test"></form>',
            '<form action="/path/to/get/route/23" class="menu"><input type="submit" value="Test"></form>',
            '<form action="http://example.com/test" class="menu"><input type="submit" value="Test"></form>',
            '<form action="/path/to/delete/route?_method=DELETE" method="POST"><input type="submit" value="Remove"></form>',
        ],
        'buttons',
    )

with subtest('check_box'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= check_box('employed')
            %= check_box('employed', 1)
            %= check_box('employed', 1, checked=None, id='foo')
            """,
        ),
        [
            '<input name="employed" type="checkbox">',
            '<input name="employed" type="checkbox" value="1">',
            '<input checked id="foo" name="employed" type="checkbox" value="1">',
        ],
        'check boxes',
    )

with subtest('color_field'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= color_field('background')
            %= color_field('background', '#ffffff')
            %= color_field('background', '#ffffff', id='foo')
            """,
        ),
        [
            '<input name="background" type="color">',
            '<input name="background" type="color" value="#ffffff">',
            '<input id="foo" name="background" type="color" value="#ffffff">',
        ],
        'color fields',
    )

with subtest('csrf_button_to'):
    c = controller()
    like_ok(
        render(c, "%= csrf_button_to('Remove', 'some_delete_route')"),
        r'^<form action="/path/to/delete/route\?_method=DELETE" method="POST">'
        r'<input name="csrf_token" type="hidden" value="[0-9a-f]+"><input type="submit" value="Remove"></form>$',
        'button with token',
    )

with subtest('csrf_field'):
    c = controller()
    like_ok(render(c, '%= csrf_field()'), r'^<input name="csrf_token" type="hidden" value="[0-9a-f]+">$', 'token')

with subtest('date_field'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= date_field('end')
            %= date_field('end', '2012-12-21')
            %= date_field('end', '2012-12-21', id='foo')
            """,
        ),
        [
            '<input name="end" type="date">',
            '<input name="end" type="date" value="2012-12-21">',
            '<input id="foo" name="end" type="date" value="2012-12-21">',
        ],
        'date fields',
    )

with subtest('datetime_field'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= datetime_field('end')
            %= datetime_field('end', '2012-12-21T23:59:59')
            %= datetime_field('end', '2012-12-21T23:59:59', id='foo')
            """,
        ),
        [
            '<input name="end" type="datetime-local">',
            '<input name="end" type="datetime-local" value="2012-12-21T23:59:59">',
            '<input id="foo" name="end" type="datetime-local" value="2012-12-21T23:59:59">',
        ],
        'datetime fields',
    )

with subtest('email_field'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= email_field('notify')
            %= email_field('notify', 'nospam@example.com')
            %= email_field('notify', 'nospam@example.com', id='foo')
            """,
        ),
        [
            '<input name="notify" type="email">',
            '<input name="notify" type="email" value="nospam@example.com">',
            '<input id="foo" name="notify" type="email" value="nospam@example.com">',
        ],
        'email fields',
    )

with subtest('favicon'):
    c = controller()
    c.req.url.base.parse('http://127.0.0.1:3000/')
    is_deeply_ok(
        lines(
            c,
            """\
            %= favicon()
            %= favicon('/favicon.ico')
            """,
        ),
        ['<link href="/favicon.ico" rel="icon">', '<link href="/favicon.ico" rel="icon">'],
        'favicons',
    )

with subtest('file_field'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= file_field('avatar')
            %= file_field('avatar', id='foo')
            """,
        ),
        ['<input name="avatar" type="file">', '<input id="foo" name="avatar" type="file">'],
        'file fields',
    )

with subtest('form_for'):
    c = controller()
    is_ok(
        render(
            c,
            """\
            %= form_for('login', begin
              %= text_field('first_name')
              %= submit_button()
            %= end)
            %= form_for('login', {'format': 'txt'}, begin
              %= text_field('first_name')
              %= submit_button()
            %= end, method='POST')
            %= form_for('/login', begin
              %= text_field('first_name', disabled='disabled')
              %= submit_button()
            %= end, enctype='multipart/form-data')
            %= form_for('http://example.com/login', begin
              %= text_field('first_name')
              %= submit_button()
            %= end, method='POST')
            %= form_for('some_delete_route', begin
              %= submit_button('Remove')
            %= end)
            """,
        ),
        """\
<form action="/path/to/login">
  <input name="first_name" type="text">
  <input type="submit" value="Ok">
</form>
<form action="/path/to/login.txt" method="POST">
  <input name="first_name" type="text">
  <input type="submit" value="Ok">
</form>
<form action="/path/to/login" enctype="multipart/form-data">
  <input disabled="disabled" name="first_name" type="text">
  <input type="submit" value="Ok">
</form>
<form action="http://example.com/login" method="POST">
  <input name="first_name" type="text">
  <input type="submit" value="Ok">
</form>
<form action="/path/to/delete/route?_method=DELETE" method="POST">
  <input type="submit" value="Remove">
</form>
""",
        'forms',
    )

with subtest('hidden_field'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= hidden_field('foo', 'bar')
            %= hidden_field('foo', 'bar', id='bar')
            """,
        ),
        ['<input name="foo" type="hidden" value="bar">', '<input id="bar" name="foo" type="hidden" value="bar">'],
        'hidden fields',
    )

with subtest('image'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= image('/images/foo.png')
            %= image('/images/foo.png', alt='Foo')
            """,
        ),
        ['<img src="/path/to/images/foo.png">', '<img alt="Foo" src="/path/to/images/foo.png">'],
        'images',
    )

with subtest('input_tag'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= input_tag('first_name')
            %= input_tag('first_name', 'Default')
            %= input_tag('employed', type='checkbox')
            """,
        ),
        [
            '<input name="first_name">',
            '<input name="first_name" value="Default">',
            '<input name="employed" type="checkbox">',
        ],
        'input tags',
    )

with subtest('javascript'):
    c = controller()
    is_ok(
        render(
            c,
            """\
            %= javascript('/script.js')
            %= javascript('/script.js', defer=None)
            %= javascript(begin
              const a = 'b';
            %= end)
            """,
        ),
        '<script src="/path/to/script.js"></script>\n'
        '<script defer src="/path/to/script.js"></script>\n'
        "<script>//<![CDATA[\n\n  const a = 'b';\n\n//]]></script>\n",
        'scripts',
    )

with subtest('label_for'):
    c = controller()
    is_ok(
        render(
            c,
            """\
            %= label_for('first_name', 'First name')
            %= label_for('first_name', 'First name', **{'class': 'user'})
            %= label_for('first_name', begin
              First name
            %= end)
            %= label_for('first_name', begin
              First name
            %= end, **{'class': 'user'})
            """,
        ),
        """\
<label for="first_name">First name</label>
<label class="user" for="first_name">First name</label>
<label for="first_name">
  First name
</label>
<label class="user" for="first_name">
  First name
</label>
""",
        'labels',
    )

with subtest('link_to'):
    c = controller()
    is_ok(
        render(
            c,
            """\
            %= link_to('Home', 'index')
            %= link_to('Home', 'index', {'format': 'txt'}, **{'class': 'menu'})
            %= link_to('index', {'format': 'txt'}, begin
              Home
            %= end, **{'class': 'menu'})
            %= link_to('Contact', 'mailto:sri@example.com')
            <%= link_to('index', begin %>Home<% end) %>
            <%= link_to('/file.txt', begin %>File<% end) %>
            <%= link_to('https://mojolicious.org', begin %>Mojolicious<% end) %>
            <%= link_to(url_for().set(query={'foo': 'bar'}).to_abs(), begin %>Retry<% end) %>
            """,
        ),
        """\
<a href="/path/to/index">Home</a>
<a class="menu" href="/path/to/index.txt">Home</a>
<a class="menu" href="/path/to/index.txt">
  Home
</a>
<a href="mailto:sri@example.com">Contact</a>
<a href="/path/to/index">Home</a>
<a href="/path/to/file.txt">File</a>
<a href="https://mojolicious.org">Mojolicious</a>
<a href="http://127.0.0.1:3000/path/to?foo=bar">Retry</a>
""",
        'links',
    )

with subtest('month_field'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= month_field('vacation')
            %= month_field('vacation', '2012-12')
            %= month_field('vacation', '2012-12', id='foo')
            """,
        ),
        [
            '<input name="vacation" type="month">',
            '<input name="vacation" type="month" value="2012-12">',
            '<input id="foo" name="vacation" type="month" value="2012-12">',
        ],
        'month fields',
    )

with subtest('number_field'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= number_field('age')
            %= number_field('age', 25)
            %= number_field('age', 25, id='foo', min=0, max=200)
            """,
        ),
        [
            '<input name="age" type="number">',
            '<input name="age" type="number" value="25">',
            '<input id="foo" max="200" min="0" name="age" type="number" value="25">',
        ],
        'number fields',
    )

with subtest('password_field'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= password_field('pass')
            %= password_field('pass', id='foo')
            """,
        ),
        ['<input name="pass" type="password">', '<input id="foo" name="pass" type="password">'],
        'password fields',
    )

with subtest('radio_button'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= radio_button('test')
            %= radio_button('country', 'germany')
            %= radio_button('country', 'germany', checked=None, id='foo')
            """,
        ),
        [
            '<input name="test" type="radio">',
            '<input name="country" type="radio" value="germany">',
            '<input checked id="foo" name="country" type="radio" value="germany">',
        ],
        'radio buttons',
    )

with subtest('range_field'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= range_field('age')
            %= range_field('age', 25)
            %= range_field('age', 25, id='foo', min=0, max=200)
            """,
        ),
        [
            '<input name="age" type="range">',
            '<input name="age" type="range" value="25">',
            '<input id="foo" max="200" min="0" name="age" type="range" value="25">',
        ],
        'range fields',
    )

with subtest('search_field'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= search_field('q')
            %= search_field('q', 'perl')
            %= search_field('q', 'perl', id='foo')
            """,
        ),
        [
            '<input name="q" type="search">',
            '<input name="q" type="search" value="perl">',
            '<input id="foo" name="q" type="search" value="perl">',
        ],
        'search fields',
    )

with subtest('select_field'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= select_field('country', ['de', 'en'])
            %= select_field('country', [['Germany', 'de'], 'en'], id='eu')
            %= select_field('country', [['Germany', 'de', {'selected': 'selected'}], 'en'])
            %= select_field('country', [c.c('EU', [['Germany', 'de'], 'en'], {'id': 'eu'})])
            %= select_field('country', [c.c('EU', ['de', 'en']), c.c('Asia', ['cn', 'jp'])])
            """,
        ),
        [
            '<select name="country"><option value="de">de</option><option value="en">en</option></select>',
            '<select id="eu" name="country"><option value="de">Germany</option><option value="en">en</option></select>',
            '<select name="country"><option selected="selected" value="de">Germany</option>'
            '<option value="en">en</option></select>',
            '<select name="country"><optgroup id="eu" label="EU"><option value="de">Germany</option>'
            '<option value="en">en</option></optgroup></select>',
            '<select name="country"><optgroup label="EU"><option value="de">de</option><option value="en">en</option>'
            '</optgroup><optgroup label="Asia"><option value="cn">cn</option><option value="jp">jp</option></optgroup>'
            '</select>',
        ],
        'select fields',
    )

with subtest('stylesheet'):
    c = controller()
    is_ok(
        render(
            c,
            """\
            %= stylesheet('/foo.css')
            %= stylesheet('/foo.css', title='Foo style')
            %= stylesheet(begin
              body {color: #000}
            %= end)
            """,
        ),
        '<link href="/path/to/foo.css" rel="stylesheet">\n'
        '<link href="/path/to/foo.css" rel="stylesheet" title="Foo style">\n'
        '<style>/*<![CDATA[*/\n\n  body {color: #000}\n\n/*]]>*/</style>\n',
        'stylesheets',
    )

with subtest('submit_button'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= submit_button()
            %= submit_button('Ok!', id='foo')
            """,
        ),
        ['<input type="submit" value="Ok">', '<input id="foo" type="submit" value="Ok!">'],
        'submit buttons',
    )

with subtest('t'):
    c = controller()
    is_ok(render(c, "%= t('div', 'test & 123')"), '<div>test &amp; 123</div>\n', 'alias')

with subtest('tag'):
    c = controller()
    is_ok(
        render(
            c,
            """\
            %= tag('br')
            %= tag('div')
            %= tag('div', id='foo', hidden=None)
            %= tag('div', 'test & 123')
            %= tag('div', 'test & 123', id='foo')
            %= tag('div', 'test & 123', data={'my_id': 1, 'Name': 'test'})
            %= tag('div', begin
              test & 123
            %= end)
            <%= tag('div', begin %>test & 123<% end, id='foo') %>
            """,
        ),
        """\
<br>
<div></div>
<div hidden id="foo"></div>
<div>test &amp; 123</div>
<div id="foo">test &amp; 123</div>
<div data-my-id="1" data-name="test">test &amp; 123</div>
<div>
  test & 123
</div>
<div id="foo">test & 123</div>
""",
        'tags',
    )

    output = c.tag('meta')
    is_ok(output, '<meta>', 'meta')
    output = c.tag('meta', charset='UTF-8')
    is_ok(output, '<meta charset="UTF-8">', 'attribute')
    output = c.tag('div', '<p>This will be escaped</p>')
    is_ok(output, '<div>&lt;p&gt;This will be escaped&lt;/p&gt;</div>', 'escaped')
    output = c.tag('div', lambda: '<p>This will not be escaped</p>')
    is_ok(output, '<div><p>This will not be escaped</p></div>', 'not escaped')
    ok(hasattr(output, '__html__'), 'markup')

with subtest('tag_with_error'):
    c = controller()
    is_ok(
        render(c, "%= tag_with_error('input', **{'class': 'foo'})"), '<input class="foo field-with-error">\n', 'class'
    )

with subtest('tel_field'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= tel_field('work')
            %= tel_field('work', '123456789')
            %= tel_field('work', '123456789', id='foo')
            """,
        ),
        [
            '<input name="work" type="tel">',
            '<input name="work" type="tel" value="123456789">',
            '<input id="foo" name="work" type="tel" value="123456789">',
        ],
        'tel fields',
    )

with subtest('text_area'):
    c = controller()
    is_ok(
        render(
            c,
            """\
            %= text_area('story')
            %= text_area('story', cols=40)
            %= text_area('story', 'Default', cols=40)
            %= text_area('story', begin
              Default
            %= end, cols=40)
            """,
        ),
        """\
<textarea name="story"></textarea>
<textarea cols="40" name="story"></textarea>
<textarea cols="40" name="story">Default</textarea>
<textarea cols="40" name="story">
  Default
</textarea>
""",
        'text areas',
    )

with subtest('text_field'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= text_field('first_name')
            %= text_field('first_name', 'Default')
            %= text_field('first_name', 'Default', **{'class': 'user'})
            """,
        ),
        [
            '<input name="first_name" type="text">',
            '<input name="first_name" type="text" value="Default">',
            '<input class="user" name="first_name" type="text" value="Default">',
        ],
        'text fields',
    )

with subtest('time_field'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= time_field('start')
            %= time_field('start', '23:59:59')
            %= time_field('start', '23:59:59', id='foo')
            """,
        ),
        [
            '<input name="start" type="time">',
            '<input name="start" type="time" value="23:59:59">',
            '<input id="foo" name="start" type="time" value="23:59:59">',
        ],
        'time fields',
    )

with subtest('url_field'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= url_field('address')
            %= url_field('address', 'https://mojolicious.org')
            %= url_field('address', 'https://mojolicious.org', id='foo')
            """,
        ),
        [
            '<input name="address" type="url">',
            '<input name="address" type="url" value="https://mojolicious.org">',
            '<input id="foo" name="address" type="url" value="https://mojolicious.org">',
        ],
        'url fields',
    )

with subtest('week_field'):
    c = controller()
    is_deeply_ok(
        lines(
            c,
            """\
            %= week_field('vacation')
            %= week_field('vacation', '2012-W17')
            %= week_field('vacation', '2012-W17', id='foo')
            """,
        ),
        [
            '<input name="vacation" type="week">',
            '<input name="vacation" type="week" value="2012-W17">',
            '<input id="foo" name="vacation" type="week" value="2012-W17">',
        ],
        'week fields',
    )

with subtest('register'):
    plugin = Pyjoyment.Plugin.TagHelpers.new()
    app = Pyjoyment.new()
    plugin.register(app)
    ok(app.renderer.get_helper('select_field'), 'registered')
    ok(re.search(r'TagHelpers', type(plugin).__module__), 'module')

done_testing()
