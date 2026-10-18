r"""
__DATA__
@@ empty.html.ep

@@ with-format.html.ep
<%= url_for('without-format') %>

@@ without-format.html.ep
<%= url_for('without-format') %>

@@ dies.html.ep
test
% raise Exception('Died')
123

@@ foo/bar.html.ep
controller and action!

@@ dead_template.html.ep
<%= dead('works too!') %>

@@ static.txt
Just some
text!

@@ template.txt.epl
<div id="☃">Redirect works!</div>

@@ test(test)(\Qtest\E)(.html.ep
<%= c.match.endpoint.name %>

@@ with_header_condition.html.ep
Test ok!

@@ root.html.epl
% c = args[0]
<% if (err := c.req.error): =%><%= err['message'] + '\n' %><% end =%>
%== c.url_for('root_path')
%== c.url_for('root_path')
%== c.url_for('root_path')
%== c.url_for('root_path')
%== c.url_for('root_path')

@@ root_path.html.epl
%== args[0].url_for('root')

@@ not_found.html.epl
Oops!

@@ continue.html.ep
% for i in range(1, 4):
%=  i
%   continue
% end

@@ index.html.epl
Just works!\

@@ form.html.epl
<%= args[0].param('name') %> ангел

@@ layouts/layout.html.epl
% c = args[0]
<%= c.title() %><%= c.content() %> with layout

@@ autostash.html.ep
% c.layout('layout')
%= foo
%= self.test_helper('bar')
% foo = 42
%= foo
%= self.match.endpoint.name

@@ layouts/layout.html.ep
layouted <%== content() %>

@@ layouts/app23.html.ep
app layout <%= content() %><%= c.app.mode %>

@@ layout.html.epl
Yea baby!\

@@ app.html.ep
<% c.layout(layout + '23') %><%= c.layout() %>

@@ helper.html.ep
%= default
%== '<br>'
%= '<...'
%= url_for('index')
(<%= agent() %>)\

@@ eperror.html.ep
%= unknown.foo('bar')

@@ favicon.ico
Not a favicon!

@@ 0.html.ep
%== url_with().set(query={'foo': 'bar'})
%== url_with('http://mojolicious.org/test')
%== url_with('/test').set(query={'foo': None})
%== url_with('bartest', test=23).set(query={'foo': 'yada'})

__END__
This is not a template!
lalala
test
"""

import Pyjo.Cookie.Response
import Pyjo.IOLoop
import Pyjo.Test.Pyjo
import Pyjoyment.Controller

from Pyjo.String.Bytes import b
from Pyjo.String.Unicode import u
from Pyjo.Test import *
from Pyjo.Util import md5_sum
from Pyjoyment.Lite import any, app, del_, get, helper, hook, patch, plugin, post, query

import contextlib
import os
import re
import time


# BEGIN { $ENV{MOJO_MODE} = 'development' }, before the mode of the application is read
os.environ['PYJO_MODE'] = 'development'

# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# Not in Mojolicious: the templates of the DATA section are in the docstring, as the requests come before the end of the
# script

# Unlike Mojolicious: the "Server" header is "Pyjoyment (Python)", and Perl's die is raise, as in Pyjo.Template the
# code is Python


# Not in Mojolicious: local of the environment
@contextlib.contextmanager
def local(**env):
    saved = {name: os.environ.get(name) for name in env}
    for name, value in env.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
    try:
        yield
    finally:
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


# Missing plugin
try:
    plugin('does_not_exist')
    e = None
except Exception as error:
    e = error
is_ok(str(e), 'Plugin "does_not_exist" missing, maybe you need to install it?\n', 'right error')

# Default
app.defaults(default=23)

# Secret
app.log.level = 'trace'
app.log.unsubscribe('message')
with app.log.capture('trace') as logs:
    is_ok(app.secrets[0], app.moniker, 'secret defaults to moniker')
like_ok(str(logs), r'Your secret passphrase needs to be changed', 'right message')
del logs

# Unlike Mojolicious: controller_class is the class, where Mojo has the name of the class
# Test helpers
helper('test_helper', lambda c, *args: c.param(*args))
helper('test_helper2', lambda c: c.app.controller_class)
cache = {}
helper('test_helper3', lambda c: cache)


@helper('dead')
def dead(c, msg=None):
    raise Exception(msg or 'works!')


is_ok(app.test_helper('foo'), None, 'no value yet')
is_ok(app.test_helper2(), Pyjoyment.Controller.object, 'right value')
app.test_helper3()['foo'] = 'bar'
is_ok(app.test_helper3()['foo'], 'bar', 'right result')

# Nested helpers
helper('test.helper', lambda c: c.app.controller_class)
is_ok(app.test.helper(), Pyjoyment.Controller.object, 'right value')
is_ok(app.build_controller().test.helper(), Pyjoyment.Controller.object, 'right value')


# Test renderer
def dead_handler(renderer, c, output, options):
    raise Exception('renderer works!')


app.renderer.add_handler('dead', dead_handler)


def change_status(renderer, c, output, options):
    c.stash(status=500)
    output.write('Bad\n')


app.renderer.add_handler('change_status', change_status)


# Rewrite when rendering to string
@hook('before_render')
def before_render(c, args):
    if c.stash().get('to_string'):
        args['test'] = 'after'


get('/empty')


@get('/☃')
def snowman(c):
    c.render(text=f'{c.url_for()}{c.url_for({})}{c.url_for("current")}')


@get('/uni/aäb')
def uni(c):
    c.render(text=c.url_for())


@get('/unicode/:0')
def unicode(c):
    c.render(text=f'{c.param("0")}{c.url_for()}')


get('/', {'format': None}, 'root', format=['html'])


@get('/alternatives/:char', char=['☃', '♥'])
def alternatives(c):
    c.render(text=c.url_for())


get('/optional/:middle/placeholder', {'middle': 'none', 'inline': '<%= middle %>-<%= url_for() =%>'})

# Unlike Mojolicious: the helper param as a method of c, as the value "param" of the stash hides it
get('/optional/:param', {'param': None, 'inline': '%= c.param("param") if c.param("param") is not None else "undef"'})


@get('/alterformat', {'format': 'json'}, format=['json'])
def alterformat(c):
    c.render(text=c.stash('format'))


@get('/noformat', {'format': 'xml'}, format=False)
def noformat(c):
    c.render(text=f'{c.stash("format")}{c.url_for()}')


del_(lambda c: c.render(text='Hello!'))

any(lambda c: c.render(text='Bye!'))


@post('/multipart/form')
def multipart_form(c):
    test = c.every_param('test')
    c.render(text='\n'.join(test))


@get('/auto_name')
def auto_name(c):
    c.render(text=c.url_for('auto_name'))


@get('/query_string')
def query_string(c):
    c.render(text=c.req.url.query)


@get('/reserved')
def reserved(c):
    c.render(text=c.param('data'))


get('/custom_name', 'auto_name')

get('/inline/exception', lambda c: c.render(inline="% raise Exception('Died')"))

get('/data/exception', 'dies')

get('/template/exception', 'dies_too')

get('/with-format', {'format': 'html'}, 'with-format')

get('/without-format', {'format': None}, 'without-format', format=['html'])

any('/json_too', {'json': {'hello': 'world'}})


@get('/null/:null')
def null(c):
    c.render(text=c.param('null'))


@get('/action_template', {'controller': 'foo'})
def action_template(c):
    c.render(action='bar')
    c.rendered()


@get('/dead')
def dead_action(c):
    c.dead()
    c.render(text='failed!')


get('/dead_template', 'dead_template')

get('/dead_renderer', lambda c: c.render(handler='dead'))

get('/dead_auto_renderer', {'handler': 'dead'})

get('/handler_change_status', lambda c: c.render(handler='change_status', status=200))

get('/template_change_status', lambda c: c.render(inline='Bad<% stash(status=500) %>', status=200))

get('/regex/in/template', r'test(test)(\Qtest\E)(')


@get('/maybe/ajax')
def maybe_ajax(c):
    if c.req.is_xhr:
        return c.render(text='is ajax')
    c.render(text='not ajax')


@get('/stream')
def stream(c):
    # Not in Mojolicious: the chunks are bytes, which write_chunk writes
    chunks = [b'foo', b'bar', c.req.url.to_abs().userinfo.encode(), str(c.url_for().to_abs()).encode()]
    c.res.code = 200
    c.res.headers.content_type = 'text/plain'

    def cb(content, offset=None):
        chunk = (chunks.pop(0) if chunks else None) or b''
        content.write_chunk(chunk, cb if chunk else None)

    cb(c.res.content)
    c.rendered()


@get('/finished')
def finished(c):
    @c.on('finish')
    def finish(c):
        c.stash()['finished'] -= 1

    c.stash()['finished'] = 2
    c.render(text='so far so good!')


get('/привет/мир', lambda c: c.render(text='привет мир'))

get('/root.html', 'root_path')

get('/root', {'format': None}, lambda c: c.render(text='root fallback!'), format=['txt'])

get('/template.txt', {'template': 'template', 'format': 'txt'}, format=['epl'])


@get(':number', number=re.compile(r'0'))
def number(c):
    url = c.req.url.to_abs()
    c.res.headers.header('X-Original', c.tx.original_remote_address)
    address = c.tx.remote_address
    num = c.param('number')
    c.render(text=f'{url}-{address}-{num}')


get('/continue')

del_('/inline/epl', lambda c: c.render(inline='<%= 1 + 1 %> ☃'))

get('/inline/ep', lambda c: c.render(inline="<%= param('foo') %>works!", handler='ep'))

get('/inline/ep/too', lambda c: c.render(inline='0', handler='ep'))


@get('/inline/ep/include')
def inline_ep_include(c):
    c.stash(inline_template="♥<%= 'just ♥' %>")
    c.render(inline='<%= include(inline=inline_template) %>works!', handler='ep')


@get('/to_string')
def to_string(c):
    c.stash(to_string=1, test='before')
    str = c.render_to_string(inline='<%= test =%>')
    c.render(text=f'{c.stash("test")}{str}')


@get('/source')
def source(c):
    # Renamed from Mojolicious: lite_app.py, the name of this test, where Mojo has lite_app.t
    file = 'does_not_exist.txt' if c.param('fail') else '../lite_app.py'
    c.render_maybe('this_does_not_ever_exist') or c.reply.static(file)


@get('/foo_relaxed/#test')
def foo_relaxed(c):
    c.render(text=c.stash('test') + ('1' if c.req.headers.dnt else '0'))


@get('/foo_wildcard/<*test>')
def foo_wildcard(c):
    c.render(text=c.stash('test'))


@get('/foo_wildcard_too/*test')
def foo_wildcard_too(c):
    c.render(text=c.stash('test'))


get('/with/header/condition', 'with_header_condition').requires(
    [('headers', {'X-Secret-Header': 'bar'}), ('headers', {'X-Another-Header': 'baz'})]
)


@post('/with/header/condition')
def with_header_condition(c):
    c.render(text='foo ' + c.req.headers.header('X-Secret-Header'))


with_header_condition.requires(headers={'X-Secret-Header': 'bar'})


@get('/session_cookie')
def session_cookie(c):
    c.render(text='Cookie set!')
    c.res.cookies(Pyjo.Cookie.Response.new(path='/session_cookie', name='session', value='23'))


@get('/session_cookie/2')
def session_cookie_2(c):
    session = c.req.cookie('session')
    value = session.value if session else 'missing'
    c.render(text=f'Session is {value}!')


@get('/foo')
def foo(c):
    c.render(text='Yea baby!')


get('/layout', lambda c: c.render(layout='layout', handler='epl', title='Layout'))

post('/template', 'index')


@any('/something')
def something(c):
    c.render(text='Just works!')


@any(['get', 'post', 'whatever'], '/something/else')
def something_else(c):
    c.render(text='Yay!')


@get('/regex/:test', test=re.compile(r'\d+'))
def regex(c):
    c.render(text=c.stash('test'))


@post('/bar/:test', {'test': 'default'})
def bar(c):
    c.render(text=c.stash('test'))


@patch('/firefox/:stuff', 'foxy')
def foxy(c):
    c.render(text=c.url_for('foxy', {'stuff': 'foo'}))


foxy.requires(agent=re.compile(r'Firefox'))


@query('/query')
def query_action(c):
    c.render(text=c.req.method)


@get('/url_for_foxy')
def url_for_foxy(c):
    c.render(text=c.url_for('foxy', stuff='#test'))


post('/utf8', 'form')


@post('/malformed_utf8')
def malformed_utf8(c):
    c.render(text=u(c.param('foo')).url_escape().to_str())


@get('/json')
def json(c):
    if (c.req.headers.content_type or '') == 'application/json':
        return c.render(json=c.req.json())
    c.render(json={'foo': [1, -2, 3, 'b☃r']}, layout='layout')


# Not in Mojolicious: YAML
get('/yaml', lambda c: c.render(yaml={'foo': [1, -2, 3, 'b☃r']}))

get('/autostash', lambda c: c.render(handler='ep', foo='bar'))

# Unlike Mojolicious: the template app.html.ep reads the layout with c.layout(), as the variable layout is the value
# of the stash when the template starts, where Mojo calls the helper layout
get('app', {'layout': 'app'})

get('/helper', lambda c: c.render(handler='ep'), 'helper')
app.helper('agent', lambda c: c.req.headers.user_agent)

get('/eperror', lambda c: c.render(handler='ep'), 'eperror')


# Unlike Mojolicious: the request is awaited, as asyncio does not nest event loops, where Mojo makes a blocking request
# in the action
@get('/subrequest')
async def subrequest(c):
    tx = await c.ua().post_p('/template')
    c.render(text=tx.result.text)


# Make sure hook runs non-blocking
hook('after_dispatch', lambda c: c.stash().update(nb='broken!'))

nb = None


@get('/subrequest_non_blocking')
def subrequest_non_blocking(c):
    def cb(ua, tx):
        global nb
        c.render(text=tx.res.text + c.stash()['nb'])
        nb = c.stash()['nb']

    c.ua().post('/template', cb)
    c.stash()['nb'] = 'success!'


get('/redirect_url', lambda c: c.redirect_to('http://127.0.0.1/foo'))

get('/redirect_path', lambda c: c.redirect_to('/foo/bar?foo=bar'))

get('/redirect_named', lambda c: c.redirect_to('index', format='txt'))

get('/redirect_twice', lambda c: c.redirect_to('/redirect_named'))


@get('/redirect_callback')
def redirect_callback(c):
    @Pyjo.IOLoop.next_tick
    def next_tick(loop):
        c.res.code = 301
        c.res.body = b'Whatever!'
        c.redirect_to('http://127.0.0.1/foo')


get('/static', lambda c: c.reply.static('hello.txt'))

app.types.type('koi8-r', 'text/html; charset=koi8-r')


@get('/koi8-r')
def koi8_r(c):
    app.renderer.encoding = 'koi8-r'
    c.render('encoding', format='koi8-r', handler='ep')
    app.renderer.encoding = None


@get('/captures/:foo/:bar')
def captures(c):
    c.render(text=c.url_for())


# Default condition
def default_condition(route, c, captures, num):
    captures['test'] = captures['foo'] + f'{num} works!'
    if c.stash()['default'] == num:
        return True
    return None


app.routes.add_condition('default', default_condition)


@get('/default/:foo')
def default(c):
    default = c.stash('default')
    test = c.stash('test')
    c.render(text=f'works {default} {test}')


default.requires(default=23)


@get('/foo/<bar:num>/baz')
def foo_num_baz(c):
    c.render(text=c.param('bar'))


# Custom placeholder type
app.routes.add_type('my_num', re.compile(r'[5-9]+'))

get('/type/<test:my_num>', {'inline': '%= test'})


# Redirect condition
def redirect_condition(route, c, captures, active):
    if not active:
        return True
    if not c.req.headers.header('X-Condition-Test'):
        c.redirect_to('index')
        return None
    return True


app.routes.add_condition('redirect', redirect_condition)

get('/redirect/condition/0', lambda c: c.render(text='condition works!')).requires(redirect=0)

get('/redirect/condition/1', {'text': 'condition works too!'}).requires(redirect=1)

get('/url_with', {'template': '0'})


@get('/url_with/:foo')
def url_with(c):
    c.render(text=c.url_with({'foo': 'bar'}).to_abs())


dynamic_inline = 1


@get('/dynamic/inline')
def dynamic(c):
    global dynamic_inline
    c.render(inline=f'dynamic inline {dynamic_inline}')
    dynamic_inline += 1


@get('/timing')
def timing(c):
    c.timing.begin('foo')
    c.timing.begin('bar')
    time.sleep(0.001)
    foo = c.timing.elapsed('foo')
    bar = c.timing.elapsed('bar')
    c.timing.server_timing('miss')
    c.timing.server_timing('dc', 'atl')
    c.timing.server_timing('test', 'Some Test', '0.002')
    c.timing.server_timing('app', None, '0.001')
    rps = c.timing.rps(bar)
    c.render(text=f'Foo: {foo}, Bar: {bar} ({rps})')


t = Pyjo.Test.Pyjo.new()

# Application is already available
is_ok(t.app.test_helper2(), Pyjoyment.Controller.object, 'right class')
# Renamed from Mojolicious: lite_app, the name of this test, as of Mojo's lite_app.t
is_ok(t.app.moniker, 'lite_app', 'right moniker')
is_ok(t.app.stash()['default'], 23, 'right value')
is_ok(t.app, app.build_controller().app.commands.app, 'applications are equal')
is_ok(str(t.app.build_controller().req.url), '', 'no URL')
is_ok(t.app.build_controller().stash()['default'], 23, 'right value')
# Not in Mojolicious: the transaction in a variable, as the controller refers to it weakly, and Python frees it at
# once, where Perl does at the end of the statement
tx = t.app.ua.build_tx('GET', '/foo')
is_ok(str(t.app.build_controller(tx).req.url), '/foo', 'right URL')
is_ok(t.app.build_controller().render_to_string('index', handler='epl'), 'Just works!', 'right result')
is_ok(t.app.build_controller().render_to_string(inline='0'), '0\n', 'right result')

# Empty template
t.get_ok('/empty').status_is(200).content_is('')

# Unicode snowman
t.get_ok('/☃').status_is(200).content_is('/%E2%98%83/%E2%98%83/%E2%98%83')

# Umlaut
t.get_ok('/uni/aäb').status_is(200).content_is('/uni/a%C3%A4b')
t.get_ok('/uni/a%E4b').status_is(200).content_is('/uni/a%C3%A4b')
t.get_ok('/uni/a%C3%A4b').status_is(200).content_is('/uni/a%C3%A4b')

# Captured snowman
t.get_ok('/unicode/☃').status_is(200).content_is('☃/unicode/%E2%98%83')

# Captured data with whitespace
t.get_ok('/unicode/a b').status_is(200).content_is('a b/unicode/a%20b')

# Captured data with backslash
t.get_ok('/unicode/a\\b').status_is(200).content_is('a\\b/unicode/a%5Cb')

# Root
(
    t.get_ok('/')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('/root.html\n/root.html\n/root.html\n/root.html\n/root.html\n')
)

# HEAD request
(
    t.head_ok('/')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .header_is('Content-Length', '55')
    .content_is('')
)

# HEAD request (lowercase)
tx = t.ua.build_tx('head', '/')
(
    t.request_ok(tx)
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .header_is('Content-Length', '55')
    .content_is('')
)

# Root with body
(t.get_ok('/', '1234' * 1024).status_is(200).content_is('/root.html\n/root.html\n/root.html\n/root.html\n/root.html\n'))

# DELETE request
t.delete_ok('/').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('Hello!')
t.post_ok('/?_method=DELETE').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('Hello!')

# POST request
t.post_ok('/').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('Bye!')

# Unicode alternatives
(
    t.get_ok('/alternatives/☃')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('/alternatives/%E2%98%83')
)
(
    t.get_ok('/alternatives/♥')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('/alternatives/%E2%99%A5')
)
t.get_ok('/alternatives/☃23').status_is(404).header_is('Server', 'Pyjoyment (Python)').content_is('Oops!\n')
t.get_ok('/alternatives').status_is(404).header_is('Server', 'Pyjoyment (Python)').content_is('Oops!\n')
t.get_ok('/alternatives/test').status_is(404).header_is('Server', 'Pyjoyment (Python)').content_is('Oops!\n')

# Optional placeholder in the middle
(
    t.get_ok('/optional/test/placeholder')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('test-/optional/test/placeholder')
)
(
    t.get_ok('/optional/placeholder')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('none-/optional/none/placeholder')
)

# Optional placeholder
t.get_ok('/optional').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('undef\n')
t.get_ok('/optional/test').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('test\n')
t.get_ok('/optional?param=test').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('undef\n')

# No format
t.get_ok('/alterformat').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('json')
t.get_ok('/alterformat.json').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('json')
t.get_ok('/alterformat.html').status_is(404).header_is('Server', 'Pyjoyment (Python)').content_is('Oops!\n')

# No format
t.get_ok('/noformat').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('xml/noformat')
t.get_ok('/noformat.xml').status_is(404).header_is('Server', 'Pyjoyment (Python)').content_is('Oops!\n')

# "application/x-www-form-urlencoded"
t.post_ok('/multipart/form', form={'test': [1, 2, 3, 4, 5]}).status_is(200).content_is('1\n2\n3\n4\n5')

# "multipart/form-data"
(
    t.post_ok('/multipart/form', form={'test': [1, 2, 3, 4, 5], 'file': {'content': '123'}})
    .status_is(200)
    .content_is('1\n2\n3\n4\n5')
)

# Generated name
t.get_ok('/auto_name').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('/custom_name')

# Query string roundtrip
(
    t.get_ok('/query_string?http://mojolicious.org/perldoc?foo=%62ar')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('http://mojolicious.org/perldoc?foo=%62ar')
)

# Reserved stash values
(
    t.get_ok('/reserved?data=just-works')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('just-works')
)
(
    t.get_ok('/reserved?data=just-works&json=test')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('just-works')
)

# Unlike Mojolicious: the exceptions end with one newline, as the template exception.html.epl renders the first line of
# the exception, where the message of Mojo ends with the newline of the location that Perl's die adds

# Exception in inline template
inline = "% raise Exception('Died')"
(
    t.get_ok('/inline/exception')
    .status_is(500)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is(f'Died at inline template {md5_sum(inline.encode())} line 1.\n')
)

# Exception in template from data section
(
    t.get_ok('/data/exception')
    .status_is(500)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('Died at template dies.html.ep from DATA section line 2.\n')
)

# Exception in template
(
    t.get_ok('/template/exception')
    .status_is(500)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('Died at template dies_too.html.ep line 2.\n')
)

# Generate URL without format
t.get_ok('/with-format').content_is('/without-format\n')
t.get_ok('/without-format').content_is('/without-format\n')
t.get_ok('/without-format.html').content_is('/without-format\n')

# JSON response
t.get_ok('/json_too').status_is(200).json_is({'hello': 'world'})

# Static inline file
(
    t.get_ok('/static.txt')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .header_is('Accept-Ranges', 'bytes')
    .content_is('Just some\ntext!\n\n')
)

# Partial inline file
(
    t.get_ok('/static.txt', {'Range': 'bytes=2-5'})
    .status_is(206)
    .header_is('Server', 'Pyjoyment (Python)')
    .header_is('Accept-Ranges', 'bytes')
    .header_is('Content-Length', '4')
    .content_is('st s')
)

# Protected DATA template
(
    t.get_ok('/template.txt.epl')
    .status_is(500)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Route without action and nothing to render')
)

# Captured "0"
t.get_ok('/null/0').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('0')

# Render action
(
    t.get_ok('/action_template')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('controller and action!\n')
)

# Dead action
t.get_ok('/dead').status_is(500).header_is('Server', 'Pyjoyment (Python)').content_like(r'works!')

# Dead renderer
(t.get_ok('/dead_renderer').status_is(500).header_is('Server', 'Pyjoyment (Python)').content_like(r'renderer works!'))

# Dead renderer with auto rendering
(
    t.get_ok('/dead_auto_renderer')
    .status_is(500)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'renderer works!')
)

# Dead template
t.get_ok('/dead_template').status_is(500).header_is('Server', 'Pyjoyment (Python)').content_like(r'works too!')

# Handler that changes status
t.get_ok('/handler_change_status').status_is(500).content_is('Bad\n')

# Template that changes status
t.get_ok('/template_change_status').status_is(500).content_is('Bad\n')

# Regex in name
(
    t.get_ok('/regex/in/template')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('test(test)(\\Qtest\\E)(\n')
)

# Chunked response with basic auth
(
    t.get_ok('//sri:foo@/stream', form={'foo': 'bar'})
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'^foobarsri:foohttp://127\.0\.0\.1:\d+/stream$')
)

# Ajax
t.get_ok('/maybe/ajax').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('not ajax')
(
    t.get_ok('/maybe/ajax', {'X-Requested-With': 'XMLHttpRequest'})
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('is ajax')
)

# With finish event
stash = None


@t.app.plugins.once('before_dispatch')
def before_dispatch(c):
    global stash
    stash = c.stash()


t.get_ok('/finished').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('so far so good!')
while stash['finished'] != 1:
    Pyjo.IOLoop.one_tick()
is_ok(stash['finished'], 1, 'finish event has been emitted once')

# IRI
t.get_ok('/привет/мир').status_is(200).content_type_is('text/html;charset=UTF-8').content_is('привет мир')

# Route with format
t.get_ok('/root.html').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('/\n')

# Fallback route without format
t.get_ok('/root').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('root fallback!')
t.get_ok('/root.txt').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('root fallback!')

# Root with format
(
    t.get_ok('/.html')
    .status_is(200)
    .header_exists_not('Servers')
    .header_exists_not('Servers', 'the header is missing')
    .header_exists('Server')
    .header_exists('Server', 'the header exists')
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('/root.html\n/root.html\n/root.html\n/root.html\n/root.html\n')
)

with subtest('Reverse proxy with "X-Forwarded-For"'), local(PYJO_REVERSE_PROXY='1'):
    t = Pyjo.Test.Pyjo.new()
    (
        t.get_ok('/0', {'X-Forwarded-For': '192.0.2.2, 192.0.2.1'})
        .status_is(200)
        .header_unlike('X-Original', r'192\.0\.2\.1')
        .content_like(r'http://127\.0\.0\.1:\d+/0-192\.0\.2\.1-0$')
    )

with (
    subtest('Reverse proxy with "X-Forwarded-For" and trusted proxies'),
    local(PYJO_TRUSTED_PROXIES='127.0.0.1, 192.0.2.1'),
):
    t = Pyjo.Test.Pyjo.new()
    (
        t.get_ok('/0', {'X-Forwarded-For': '192.0.2.2, 192.0.2.1'})
        .status_is(200)
        .header_unlike('X-Original', r'192\.0\.2\.(?:2|1)')
        .content_like(r'http://127\.0\.0\.1:\d+/0-192\.0\.2\.2-0$')
    )

with (
    subtest('Reverse proxy with "X-Forwarded-For" and trusted proxies (untrusted original)'),
    local(PYJO_TRUSTED_PROXIES='192.0.2.1'),
):
    t = Pyjo.Test.Pyjo.new()
    (
        t.get_ok('/0', {'X-Forwarded-For': '192.0.2.2, 192.0.2.1'})
        .status_is(200)
        .header_unlike('X-Original', r'192\.0\.2\.(?:2|1)')
        .content_like(r'http://127\.0\.0\.1:\d+/0-127\.0\.0\.1-0$')
    )

with (
    subtest('Reverse proxy with "X-Forwarded-For" and trusted proxy networks'),
    local(PYJO_TRUSTED_PROXIES='127.0.0.0/8, 192.0.2.1/32'),
):
    t = Pyjo.Test.Pyjo.new()
    (
        t.get_ok('/0', {'X-Forwarded-For': '192.0.2.2, 192.0.2.1'})
        .status_is(200)
        .header_unlike('X-Original', r'192\.0\.2\.(?:2|1)')
        .content_like(r'http://127\.0\.0\.1:\d+/0-192\.0\.2\.2-0$')
    )

with (
    subtest('Reverse proxy with "X-Forwarded-For" and trusted proxies (all addresses trusted)'),
    local(PYJO_TRUSTED_PROXIES='0.0.0.0/0'),
):
    t = Pyjo.Test.Pyjo.new()
    (
        t.get_ok('/0', {'X-Forwarded-For': '192.0.2.2, 192.0.2.1'})
        .status_is(200)
        .header_unlike('X-Original', r'192\.0\.2\.(?:2|1)')
        .content_like(r'http://127\.0\.0\.1:\d+/0-192\.0\.2\.2-0$')
    )

with (
    subtest('Reverse proxy with "X-Forwarded-For" and trusted proxies (unexpected leading address)'),
    local(PYJO_TRUSTED_PROXIES='127.0.0.0/8, 192.0.2.1'),
):
    t = Pyjo.Test.Pyjo.new()
    (
        t.get_ok('/0', {'X-Forwarded-For': '7.7.7.7, 192.0.2.2, 192.0.2.1'})
        .status_is(200)
        .header_unlike('X-Original', r'192\.0\.2\.(?:2|1)')
        .content_like(r'http://127\.0\.0\.1:\d+/0-192\.0\.2\.2-0$')
    )

with subtest('Reverse proxy with "X-Forwarded-Proto"'), local(PYJO_REVERSE_PROXY='1'):
    t = Pyjo.Test.Pyjo.new()
    (
        t.get_ok('/0', {'X-Forwarded-Proto': 'https'})
        .status_is(200)
        .content_like(r'^https://127\.0\.0\.1:\d+/0-')
        .content_like(r'-0$')
        .content_unlike(r'-192\.0\.2\.1-0$')
    )

# "X-Forwarded-For"
t.ua.server.restart()
(
    t.get_ok('/0', {'X-Forwarded-For': '192.0.2.2, 192.0.2.1'})
    .status_is(200)
    .content_like(r'^http://127\.0\.0\.1:\d+/0-')
    .content_like(r'-0$')
    .content_unlike(r'-192\.0\.2\.1-0$')
)

# "X-Forwarded-Proto"
(
    t.get_ok('/0', {'X-Forwarded-Proto': 'https'})
    .status_is(200)
    .content_like(r'^http://127\.0\.0\.1:\d+/0-')
    .content_like(r'-0$')
    .content_unlike(r'-192\.0\.2\.1-0$')
)

# "continue" keyword in template
t.get_ok('/continue').status_is(200).content_like(r'(?s)1.+2.+3')

# Inline "epl" template
t.delete_ok('/inline/epl').status_is(200).content_is('2 ☃\n')

# Inline "ep" template
t.get_ok('/inline/ep?foo=bar').status_is(200).content_is('barworks!\n')

# Inline "ep" template "0"
t.get_ok('/inline/ep/too').status_is(200).content_is('0\n')

# Inline template with include
t.get_ok('/inline/ep/include').status_is(200).content_is('♥just ♥\nworks!\n')

# Rewritten localized arguments
t.get_ok('/to_string').status_is(200).content_is('beforeafter')

# Render static file outside of public directory
(t.get_ok('/source').status_is(200).content_type_is('application/octet-stream').content_like(r"get_ok\('/source"))

# File does not exist
with app.log.capture('trace') as logs:
    t.get_ok('/source?fail=1').status_is(500).content_like(r'Static file "does_not_exist.txt" not found')
like_ok(str(logs), r'Static file "does_not_exist.txt" not found', 'right message')
del logs

# With body and max message size
with local(PYJO_MAX_MESSAGE_SIZE='1024'):
    with app.log.capture('trace') as logs:
        (
            t.get_ok('/', '1234' * 1024)
            .status_is(200)
            .header_is('Connection', 'close')
            .content_is(
                'Maximum message size exceeded\n' + '/root.html\n/root.html\n/root.html\n/root.html\n/root.html\n'
            )
        )
    like_ok(str(logs), r'Maximum message size exceeded', 'right message')
    del logs

# Relaxed placeholder
t.get_ok('/foo_relaxed/123').status_is(200).content_is('1230')
t.get_ok('/foo_relaxed/123.html').status_is(200).content_is('123.html0')
t.get_ok('/foo_relaxed/123', {'DNT': 1}).status_is(200).content_is('1231')
t.get_ok('/foo_relaxed/').status_is(404)

# Wildcard placeholder
t.get_ok('/foo_wildcard/123').status_is(200).content_is('123')
t.get_ok('/foo_wildcard/IQ==%0A').status_is(200).content_is('IQ==\x0a')
t.get_ok('/foo_wildcard/').status_is(404)
t.get_ok('/foo_wildcard_too/123').status_is(200).content_is('123')
t.get_ok('/foo_wildcard_too/').status_is(404)

# Header conditions
(
    t.get_ok('/with/header/condition', {'X-Secret-Header': 'bar', 'X-Another-Header': 'baz'})
    .status_is(200)
    .content_is('Test ok!\n')
)
t.get_ok('/with/header/condition').status_is(404).content_like(r'Oops!')
t.get_ok('/with/header/condition', {'X-Secret-Header': 'bar'}).status_is(404).content_like(r'Oops!')

# Single header condition
t.post_ok('/with/header/condition', {'X-Secret-Header': 'bar'}, 'bar').status_is(200).content_is('foo bar')
t.post_ok('/with/header/condition', {}, 'bar').status_is(404).content_like(r'Oops!')

# Session cookie
t.get_ok('/session_cookie').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('Cookie set!')
(t.get_ok('/session_cookie/2').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('Session is 23!'))
(t.get_ok('/session_cookie/2').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('Session is 23!'))

# Session reset
t.reset_session()
ok(not t.tx, 'session reset')
(
    t.get_ok('/session_cookie/2')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('Session is missing!')
)

# Text
t.get_ok('/foo').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('Yea baby!')

# Template
t.post_ok('/template').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('Just works!')

# All methods
t.get_ok('/something').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('Just works!')
t.post_ok('/something').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('Just works!')
t.delete_ok('/something').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('Just works!')

# Only GET, POST and a custom request method
t.get_ok('/something/else').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('Yay!')
t.post_ok('/something/else').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('Yay!')
(
    t.request_ok(t.ua.build_tx('WHATEVER', '/something/else'))
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('Yay!')
)
t.delete_ok('/something/else').status_is(404).header_is('Server', 'Pyjoyment (Python)').content_like(r'Oops!')

# Regex constraint
t.get_ok('/regex/23').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('23')
t.get_ok('/regex/foo').status_is(404).header_is('Server', 'Pyjoyment (Python)').content_like(r'Oops!')

# Default value
t.post_ok('/bar').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('default')
t.post_ok('/bar/baz').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('baz')

# Layout
(
    t.get_ok('/layout')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('LayoutYea baby! with layout\n')
)

# User agent condition
(
    t.patch_ok('/firefox/bar', {'User-Agent': 'Firefox'})
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('/firefox/foo')
)
(
    t.patch_ok('/firefox/bar', {'User-Agent': 'Explorer'})
    .status_is(404)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Oops!')
)

# QUERY request
t.query_ok('/query').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('QUERY')

# URL for route with condition
t.get_ok('/url_for_foxy').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('/firefox/%23test')

# UTF-8 form
(
    t.post_ok('/utf8', form={'name': 'табак'})
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .header_is('Content-Length', '22')
    .content_type_is('text/html;charset=UTF-8')
    .content_is('табак ангел\n')
)

# UTF-8 "multipart/form-data" form
(
    t.post_ok('/utf8', {'Content-Type': 'multipart/form-data'}, form={'name': 'табак'})
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .header_is('Content-Length', '22')
    .content_type_is('text/html;charset=UTF-8')
    .content_is('табак ангел\n')
)

# Malformed UTF-8
(
    t.post_ok('/malformed_utf8', {'Content-Type': 'application/x-www-form-urlencoded'}, 'foo=%E1')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('%E1')
)

# JSON (with a lot of different tests)
(
    t.get_ok('/json')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_type_is('application/json;charset=UTF-8')
    .json_is({'foo': [1, -2, 3, 'b☃r']})
    .json_is('/foo', [1, -2, 3, 'b☃r'])
    .json_is('/foo/3', 'b☃r', 'with description')
    .json_has('/foo')
    .json_has('/foo', 'with description')
    .json_hasnt('/bar')
    .json_hasnt('/bar', 'with description')
    .json_like('/foo/3', r'r$')
    .json_like('/foo/3', r'r$', 'with description')
    .json_unlike('/foo/3', r'b$')
    .json_unlike('/foo/3', r'^r', 'with description')
)

# JSON ("null")
(
    t.get_ok('/json', json=None)
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_type_is('application/json;charset=UTF-8')
    .json_is(None)
    .content_is('null')
)

# Not in Mojolicious: YAML
(
    t.get_ok('/yaml')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_type_is('application/yaml;charset=UTF-8')
    .content_is('foo:\n- 1\n- -2\n- 3\n- b☃r\n')
)

# Stash values in template
(
    t.get_ok('/autostash?bar=23')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('layouted bar\n23\n42\nautostash\n\n')
)

# Route without slash
(
    t.get_ok('/app')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('app layout app23\ndevelopment\n')
)

# Helper
(
    t.get_ok('/helper')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('23\n<br>\n&lt;...\n/template\n(Pyjoyment (Python))')
)
(
    t.get_ok('/helper', {'User-Agent': 'Explorer'})
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('23\n<br>\n&lt;...\n/template\n(Explorer)')
)

# Exception in EP template
# Unlike Mojolicious: the name of the variable, as Python names it in its NameError, where Perl has $unknown
t.get_ok('/eperror').status_is(500).header_is('Server', 'Pyjoyment (Python)').content_like(r"'unknown'")

# Subrequest
t.get_ok('/subrequest').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('Just works!')
t.get_ok('/subrequest').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('Just works!')

# Non-blocking subrequest
(
    t.get_ok('/subrequest_non_blocking')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('Just works!success!')
)
is_ok(nb, 'broken!', 'right text')

# Redirect to URL
(
    t.get_ok('/redirect_url')
    .status_is(302)
    .header_is('Server', 'Pyjoyment (Python)')
    .header_is('Location', 'http://127.0.0.1/foo')
    .content_is('')
)

# Redirect to path
(
    t.get_ok('/redirect_path')
    .status_is(302)
    .header_is('Server', 'Pyjoyment (Python)')
    .header_like('Location', r'/foo/bar\?foo=bar$')
    .content_is('')
)

# Redirect to named route
(
    t.get_ok('/redirect_named')
    .status_is(302)
    .header_is('Server', 'Pyjoyment (Python)')
    .header_like('Location', r'/template.txt$')
    .content_is('')
)

# Redirect twice
t.ua.max_redirects = 3
(
    t.get_ok('/redirect_twice')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .text_is('div#☃', 'Redirect works!')
)
redirects = t.tx.redirects()
is_ok(len(redirects), 2, 'two redirects')
is_ok(redirects[0].req.url.path, '/redirect_twice', 'right path')
is_ok(redirects[1].req.url.path, '/redirect_named', 'right path')
t.ua.max_redirects = 0

# Non-blocking redirect
(
    t.get_ok('/redirect_callback')
    .status_is(301)
    .header_is('Server', 'Pyjoyment (Python)')
    .header_is('Content-Length', '9')
    .header_is('Location', 'http://127.0.0.1/foo')
    .content_is('Whatever!')
)

# Static file
(
    t.get_ok('/static')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .header_is('Content-Length', '31')
    .content_is('Hello Mojo from a static file!\n')
)

# Redirect to named route with redirecting enabled in user agent
t.ua.max_redirects = 3
(
    t.get_ok('/redirect_named')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .header_is('Location', None)
    .element_exists('#☃')
    .element_exists_not('#foo')
    .text_isnt('#foo', 'whatever')
    .text_isnt('div#☃', 'Redirect')
    .text_is('div#☃', 'Redirect works!')
    .text_unlike('div#☃', r'Foo')
    .text_like('div#☃', r'^Redirect')
)
t.ua.max_redirects = 0
is_ok(t.tx.previous.res.code, 302, 'right status')
like_ok(t.tx.previous.res.headers.location, r'/template.txt$', 'right "Location" value')
is_ok(t.tx.previous.res.body, b'', 'right content')

# Request with koi8-r content
koi8 = (
    'Этот человек наполняет меня надеждой. Ну, и некоторыми другими глубокими и приводящими в замешательство эмоциями.'
)
(
    t.get_ok('/koi8-r')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_type_is('text/html; charset=koi8-r')
    .content_like(f'^{koi8}')
)

# Custom condition
(
    t.get_ok('/default/condition')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('works 23 condition23 works!')
)

# Placeholder type
t.get_ok('/foo/23/baz').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('23')
t.get_ok('/foo/bar/baz').status_is(404).header_is('Server', 'Pyjoyment (Python)')

# Custom placeholder type
t.get_ok('/type/56').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('56\n')
t.get_ok('/type/12').status_is(404).header_is('Server', 'Pyjoyment (Python)')

# Redirect from condition
(
    t.get_ok('/redirect/condition/0')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('condition works!')
)
(
    t.get_ok('/redirect/condition/1')
    .status_is(302)
    .header_is('Server', 'Pyjoyment (Python)')
    .header_like('Location', r'/template$')
    .content_is('')
)
(
    t.get_ok('/redirect/condition/1', {'X-Condition-Test': 1})
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('condition works too!')
)

# Multiple placeholders
(t.get_ok('/captures/foo/bar').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('/captures/foo/bar'))
(t.get_ok('/captures/bar/baz').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('/captures/bar/baz'))
(
    t.get_ok('/captures/♥/☃')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('/captures/%E2%99%A5/%E2%98%83')
)
is_ok(b(t.tx.res.body).url_unescape().decode('UTF-8'), '/captures/♥/☃', 'right result')

# Bundled file in DATA section
t.get_ok('/favicon.ico').status_is(200).content_is('Not a favicon!\n\n')

# Generate URL with query parameters
t.get_ok('/url_with?foo=23&bar=24&baz=25').status_is(200).content_is("""\
/url_with?bar=24&baz=25&foo=bar
http://mojolicious.org/test?foo=23&bar=24&baz=25
/test?bar=24&baz=25
/bar/23?bar=24&baz=25&foo=yada
""")
t.get_ok('/url_with/foo?foo=bar').status_is(200).content_like(r'http://127\.0\.0\.1:\d+/url_with/bar\?foo\=bar')

# Dynamic inline template
t.get_ok('/dynamic/inline').status_is(200).content_is('dynamic inline 1\n')
t.get_ok('/dynamic/inline').status_is(200).content_is('dynamic inline 2\n')

# Timing
(
    t.get_ok('/timing')
    .status_is(200)
    .header_like('Server-Timing', r'miss, dc;desc="atl", test;desc="Some Test";dur=0.002, app;dur=0.001')
    .content_like(r'Foo: [0-9.]+, Bar: [0-9.]+ \([0-9.?]+\)')
)
is_ok(t.app.timing.elapsed('does_not_exist'), None, 'no timing data')
is_ok(t.app.timing.rps('0.1'), '10.000', 'right number')
is_ok(t.app.timing.rps(1), '1.000', 'right number')
is_ok(t.app.timing.rps(0), None, 'number too small')

done_testing()
