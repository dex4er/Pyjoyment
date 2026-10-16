r"""
__DATA__
@@ not_found.html.epl
Oops!

@@ multi.html.ep
% one = c.cookie('unsigned1')
% three = c.cookie('unsigned2')
%= one or ''
%= three or ''
% unsigned1 = c.every_cookie('unsigned1')
%= unsigned1[0] if len(unsigned1) > 0 else ''
%= unsigned1[1] if len(unsigned1) > 1 else ''
% four = c.signed_cookie('signed1')
% six = c.signed_cookie('signed2')
%= four or ''
%= six or ''
% signed1 = c.every_signed_cookie('signed1')
%= signed1[0] if len(signed1) > 0 else ''
%= signed1[1] if len(signed1) > 1 else ''

@@ param_auth.html.epl
Bender!

@@ param_auth_denied.html.epl
Not Bender!

@@ bridge2stash.html.ep
% cookie = c.req.cookie('pyjoyment')
<%= stash('_name') %> too!<%= c.cookie('foo') %>!\
<%= c.signed_cookie('foo') %>!\
<%= c.signed_cookie('bar')%>!<%= c.signed_cookie('bad')%>!\
<%= c.cookie('bad') %>!<%= session('foo') %>!\
<%= flash('foo') %>!
% c.session(foo='session')
% headers = c.req.headers
% if headers.header('X-Flash'):
%   c.flash(foo='flash')
% end
% if headers.header('X-Flash2'):
%   c.session(expires=1)
% end

@@ withundercount.html.ep
counter
"""

import Pyjo.IOLoop
import Pyjo.Test.Pyjo

from Pyjo.String.Unicode import u
from Pyjo.Test import *
from Pyjoyment.Lite import app, get, group, hook, post, under

import time


# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# Not in Mojolicious: the templates of the DATA section are in the docstring, as the requests come before the end of the
# script

# Unlike Mojolicious: the session cookie is "pyjoyment", as Pyjoyment.Sessions names it

app.secrets = ['test1']


@get('/multi')
def multi(c):
    c.cookie('unsigned1', 'one')
    c.cookie('unsigned1', 'two', {'path': '/multi'})
    c.cookie('unsigned2', 'three')
    c.signed_cookie('signed1', 'four')
    c.signed_cookie('signed1', 'five', {'path': '/multi'})
    c.signed_cookie('signed2', 'six')


@get('/expiration')
def expiration(c):
    if c.param('redirect'):
        c.session(expiration=0)
        return c.redirect_to('expiration')
    c.render(text=c.session('expiration'))


under('/missing', lambda c: True).any().to('does_not_exist#not_at_all')


@under('/suspended')
def suspended(c):
    @Pyjo.IOLoop.next_tick
    def next_tick(loop):
        # The value "0" is false, as in Perl
        if c.param('ok') in (None, '', '0'):
            return c.render(text='stopped!')
        c.stash(suspended='suspended!')
        c.continue_()

    return False


get('/', {'inline': '<%= suspended %>\\'})


@under
def unauthorized(c):
    if not c.req.headers.header('X-Bender'):
        c.render(text='Unauthorized!', status=401)
        return None
    c.res.headers.add('X-Under', 23)
    c.res.headers.add('X-Under', 24)
    return True


@get('/with_under')
def with_under(c):
    c.render(text='Unders are cool!')


@get('/with_under_too')
def with_under_too(c):
    c.render(text='Unders are cool too!')


@under
def param_auth(c):
    # Authenticated
    name = c.param('name') or ''
    if name == 'Bender':
        return True

    # Not authenticated
    c.render('param_auth_denied')
    return None


get('/param_auth')

get('/param_auth/too', lambda c: c.render(text='You could be Bender too!'))


@under
def cookies(c):
    c.stash(_name='stash')
    c.cookie('foo', 'cookie', {'expires': time.time() + 60})
    c.signed_cookie('bar', 'signed_cookie', {'expires': time.time() + 120})
    c.cookie('bad', 'bad_cookie--12345678')
    return True


get('/bridge2stash', lambda c: c.render(template='bridge2stash', handler='ep'))


# Make sure after_dispatch can make session changes
@hook('after_dispatch')
def after_dispatch(c):
    if not c.req.url.path.contains('/late/session'):
        return
    c.session(late='works!')


@get('/late/session')
def late_session(c):
    late = c.session('late') or 'not yet!'
    c.render(text=late)


# Counter
counter = 0


@under
def count(c):
    global counter
    counter += 1
    c.res.headers.header('X-Under', counter)
    return True


get('/with/under/count')

# Prefix
under('/prefix')

get(lambda c: c.render(text='prefixed GET works!'))

post(lambda c: c.render(text='prefixed POST works!'))

get('/works', lambda c: c.render(text='prefix works!'))

under('/prefix2', {'msg': 'prefixed'})

get('/foo', {'inline': '<%= msg %>!'})

get('/bar', {'inline': 'also <%= msg %>!'})

# Reset
under('/', {'foo': 'one'})

get('/reset', {'text': 'reset works!'})

# Group
with group():
    under('/group', {'bar': 'two'})

    get({'inline': '<%= foo %><%= bar %>!'})

    # Nested group
    with group():
        under('/nested', {'baz': 'three'})

        get({'inline': '<%= baz %><%= bar %><%= foo %>!'})

        get('/whatever', {'inline': '<%= foo %><%= bar %><%= baz %>!'})

# Authentication group
with group():
    # Check "ok" parameter
    @under
    def ok_parameter(c):
        if c.req.param('ok'):
            return True
        c.render(text="You're not ok.")
        return False

    get('/authgroup', {'text': "You're ok.", 'format': None}, format=['txt'])

get('/noauthgroup', {'inline': 'Whatever <%= foo %>.'})

# Disable format detection
under(format=False)

get('/no_format', {'text': 'No format detection.'})

get('/some_formats', {'text': 'Some format detection.'}, format=['txt', 'json'])

get('/no_real_format.xml', {'text': 'No real format.'})

get('/one_format', {'text': 'One format.'}, format='xml')

t = Pyjo.Test.Pyjo.new()

# Preserve stash
stash = None


@t.app.hook('after_dispatch')
def preserve_stash(c):
    global stash
    stash = c.stash()


# Zero expiration persists
t.ua.max_redirects = 1
t.get_ok('/expiration?redirect=1').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('0')
ok(not t.tx.res.cookie('pyjoyment').expires, 'no expiration')
t.reset_session()

# Multiple cookies with same name
t.get_ok('/multi').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('\n\n\n\n\n\n\n\n')

# Multiple cookies with same name (again)
(
    t.get_ok('/multi')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('two\nthree\none\ntwo\nfive\nsix\nfour\nfive\n')
)

# Missing action behind bridge
t.get_ok('/missing').status_is(500).content_like(r'Route without action and nothing to render')

# Suspended bridge
with t.app.log.capture('trace') as logs:
    t.get_ok('/suspended?ok=1').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('suspended!')
    like_ok(str(logs), r'GET "/suspended"', 'right message')
    like_ok(str(logs), r'Routing to a callback', 'right message')
    like_ok(str(logs), r'Nothing has been rendered, expecting delayed response', 'right message')
    # Unlike Mojolicious: the name is the MD5 sum of the template of Python
    like_ok(str(logs), r'Rendering inline template "4f2c392370a7161007d603b890866ed8"', 'right message')

# Suspended bridge (stopped)
t.get_ok('/suspended?ok=0').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('stopped!')

# Authenticated with header
(
    t.get_ok('/with_under', {'X-Bender': 'Rodriguez'})
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .header_is('X-Under', '23, 24')
    .header_like('X-Under', r'23, 24')
    .content_is('Unders are cool!')
)

# Authenticated with header too
(
    t.get_ok('/with_under_too', {'X-Bender': 'Rodriguez'})
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .header_is('X-Under', '23, 24')
    .header_like('X-Under', r'23, 24')
    .content_is('Unders are cool too!')
)

# Not authenticated with header
(t.get_ok('/with_under_too').status_is(401).header_is('Server', 'Pyjoyment (Python)').content_like(r'Unauthorized'))

# Not authenticated with parameter
t.get_ok('/param_auth').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('Not Bender!\n')
is_ok(stash.get('_name'), None, 'no "_name" value')

# Authenticated with parameter
(t.get_ok('/param_auth?name=Bender').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('Bender!\n'))

# Not authenticated with parameter
t.get_ok('/param_auth/too').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('Not Bender!\n')

# Authenticated with parameter too
(
    t.get_ok('/param_auth/too?name=Bender')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('You could be Bender too!')
)

# No cookies, session or flash
t.get_ok('/bridge2stash', {'X-Flash': 1}).status_is(200).content_is('stash too!!!!!!!!\n')
ok(t.tx.res.cookie('pyjoyment').expires, 'has expiration')
is_ok(stash.get('_name'), 'stash', 'right "_name" value')

# Cookies, session and flash
with t.app.log.capture('trace') as logs:
    (
        t.get_ok('/bridge2stash')
        .status_is(200)
        .content_is('stash too!cookie!!signed_cookie!!bad_cookie--12345678!session!flash!\n')
    )
    like_ok(str(logs), r'Cookie "foo" is not signed', 'right message')
    like_ok(str(logs), r'Cookie "bad" has bad signature', 'right message')
    ok(t.tx.res.cookie('pyjoyment').httponly, 'session cookie has HttpOnly flag')
    is_ok(t.tx.res.cookie('pyjoyment').samesite, 'Lax', 'right SameSite value')
t.app.sessions.samesite = 'Strict'
t.get_ok('/bridge2stash').status_is(200)
is_ok(t.tx.res.cookie('pyjoyment').samesite, 'Strict', 'right SameSite value')
t.app.sessions.samesite = None
t.get_ok('/bridge2stash').status_is(200)
is_ok(t.tx.res.cookie('pyjoyment').samesite, None, 'no SameSite value')

# Broken session cookie
t.reset_session()
session = u('☃☃☃☃☃').encode().b64_encode('')
hmac = session.clone().hmac_sha1_sum(t.app.secrets[0])
(t.get_ok('/bridge2stash', {'Cookie': f'pyjoyment={session}--{hmac}'}).status_is(200).content_is('stash too!!!!!!!!\n'))

# Not collecting cookies
t.reset_session().ua.cookie_jar.ignore = lambda cookie: True
t.get_ok('/bridge2stash', {'X-Flash': 1}).status_is(200).content_is('stash too!!!!!!!!\n')

# Still not collecting cookies
t.get_ok('/bridge2stash', {'X-Flash': 1}).status_is(200).content_is('stash too!!!!!!!!\n')
t.ua.cookie_jar.ignore = lambda cookie: False

# Fresh start without cookies, session or flash
t.get_ok('/bridge2stash', {'X-Flash': 1}).status_is(200).content_is('stash too!!!!!!!!\n')

# Random static requests
t.get_ok('/mojo/logo-white.png').status_is(200)
t.get_ok('/mojo/logo-white.png').status_is(200)

# With cookies, session and flash again
(
    t.get_ok('/bridge2stash')
    .status_is(200)
    .content_is('stash too!cookie!!signed_cookie!!bad_cookie--12345678!session!flash!\n')
)

# With cookies and session but no flash (rotating secrets)
t.app.secrets = ['test2', 'test1']
(
    t.get_ok('/bridge2stash', {'X-Flash2': 1})
    .status_is(200)
    .content_is('stash too!cookie!!signed_cookie!!bad_cookie--12345678!session!!\n')
)
ok(t.tx.res.cookie('pyjoyment').expires < time.time(), 'session cookie expires')

# With cookies and session cleared (rotating secrets)
t.app.secrets = ['test3', 'test2']
t.get_ok('/bridge2stash').status_is(200).content_is('stash too!cookie!!signed_cookie!!bad_cookie--12345678!!!\n')

# Late session does not affect rendering
t.get_ok('/late/session').status_is(200).content_is('not yet!')

# Previous late session does affect rendering
t.get_ok('/late/session').status_is(200).content_is('works!')

# Previous late session does affect rendering again
t.get_ok('/late/session').status_is(200).content_is('works!')

# Counter
(
    t.get_ok('/with/under/count', {'X-Bender': 'Rodriguez'})
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .header_is('X-Under', '1')
    .content_is('counter\n')
)
is_ok(stash.get('_name'), None, 'no "_name" value')

# Cookies, session and no flash again
(
    t.get_ok('/bridge2stash', {'X-Flash': 1})
    .status_is(200)
    .content_is('stash too!cookie!!signed_cookie!!bad_cookie--12345678!session!!\n')
)

# With cookies, session and flash
(
    t.get_ok('/bridge2stash')
    .status_is(200)
    .content_is('stash too!cookie!!signed_cookie!!bad_cookie--12345678!session!flash!\n')
)

# With cookies and session but no flash
(
    t.get_ok('/bridge2stash', {'X-Flash2': 1})
    .status_is(200)
    .content_is('stash too!cookie!!signed_cookie!!bad_cookie--12345678!session!!\n')
)

# Prefix
t.get_ok('/prefix').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('prefixed GET works!')

# POST request with prefix
t.post_ok('/prefix').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('prefixed POST works!')

# GET request with prefix
t.get_ok('/prefix/works').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('prefix works!')

# Another prefix
t.get_ok('/prefix2/foo').status_is(200).content_is('prefixed!\n')

# Another prefix again
t.get_ok('/prefix2/bar').status_is(200).content_is('also prefixed!\n')

# Reset under statements
t.get_ok('/reset').status_is(200).content_is('reset works!')

# Not reachable with prefix
t.get_ok('/prefix/reset').status_is(404).content_is('Oops!\n')

# Group
t.get_ok('/group').status_is(200).content_is('onetwo!\n')

# Nested group
t.get_ok('/group/nested').status_is(200).content_is('threetwoone!\n')

# GET request to nested group
t.get_ok('/group/nested/whatever').status_is(200).content_is('onetwothree!\n')

# Another GET request to nested group
t.get_ok('/group/nested/something').status_is(404).content_is('Oops!\n')

# Authenticated by group
t.get_ok('/authgroup?ok=1').status_is(200).content_type_is('text/html;charset=UTF-8').content_is("You're ok.")

# Not authenticated by group
t.get_ok('/authgroup').status_is(200).content_type_is('text/html;charset=UTF-8').content_is("You're not ok.")

# Authenticated by group (with format)
(t.get_ok('/authgroup.txt?ok=1').status_is(200).content_type_is('text/plain;charset=UTF-8').content_is("You're ok."))

# Not authenticated by group (with format)
t.get_ok('/authgroup.txt').status_is(200).content_type_is('text/plain;charset=UTF-8').content_is("You're not ok.")

# Bypassed group authentication
t.get_ok('/noauthgroup').status_is(200).content_is('Whatever one.\n')

# Disabled format detection
(t.get_ok('/no_format').status_is(200).content_type_is('text/html;charset=UTF-8').content_is('No format detection.'))

# Invalid format
t.get_ok('/no_format.txt').status_is(404).content_type_is('text/html;charset=UTF-8').content_is('Oops!\n')

# Invalid format
t.get_ok('/some_formats').status_is(404).content_type_is('text/html;charset=UTF-8').content_is('Oops!\n')

# Format "txt" has been detected
(
    t.get_ok('/some_formats.txt')
    .status_is(200)
    .content_type_is('text/plain;charset=UTF-8')
    .content_is('Some format detection.')
)

# Format "json" has been detected
(
    t.get_ok('/some_formats.json')
    .status_is(200)
    .content_type_is('application/json;charset=UTF-8')
    .content_is('Some format detection.')
)

# Invalid format
t.get_ok('/some_formats.xml').status_is(404).content_type_is('text/html;charset=UTF-8').content_is('Oops!\n')

# Invalid format
t.get_ok('/no_real_format').status_is(404).content_type_is('text/html;charset=UTF-8').content_is('Oops!\n')

# No format detected
(
    t.get_ok('/no_real_format.xml')
    .status_is(200)
    .content_type_is('text/html;charset=UTF-8')
    .content_is('No real format.')
)

# Invalid format
t.get_ok('/no_real_format.txt').status_is(404).content_type_is('text/html;charset=UTF-8').content_is('Oops!\n')

# Invalid format
t.get_ok('/one_format').status_is(404).content_type_is('text/html;charset=UTF-8').content_is('Oops!\n')

# Format "xml" detected
t.get_ok('/one_format.xml').status_is(200).content_type_is('application/xml').content_is('One format.')

# Invalid format
t.get_ok('/one_format.txt').status_is(404).content_type_is('text/html;charset=UTF-8').content_is('Oops!\n')

done_testing()
