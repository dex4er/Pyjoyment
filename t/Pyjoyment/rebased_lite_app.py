"""
__DATA__
@@ root.html.ep
%= c.req.url.base
%= javascript('/mojo/jquery/jquery.js')
%= image('/images/test.png')
%= stylesheet('//example.com/base.css')
%= link_to('Contact', 'mailto:sri@example.com')
%= c.req.url.to_abs()
%= url_for('foo').to_abs()
%= url_for('foo')
%= url_for('foo').base
%= current_route()
% if current_route('root'):
  Welcome to the root!
% end

@@ foo.html.ep
<%= c.req.url.base %><%= flash('just') or '' %><%= flash('works') or '' %>
%= stylesheet('/b.css', media='test')
%= image('/images/test.png', alt='Test')
%= c.req.url.to_abs()
%= url_for('root').to_abs()
%= url_for('root')
%= url_for('root').base
%= current_route()
"""

import Pyjo.Test.Pyjo
import Pyjo.URL

from Pyjo.Test import *
from Pyjoyment.Lite import app, get


# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# Not in Mojolicious: the templates of the DATA section are in the docstring, as the requests come before the end of the
# script


# Rebase hook
@app.hook('before_dispatch')
def before_dispatch(c):
    c.req.url.base = Pyjo.URL.new('http://example.com/rebased/')
    c.req.url.path.leading_slash = False


# Current route hook
@app.hook('after_dispatch')
def after_dispatch(c):
    c.res.headers.header('X-Route', c.current_route())


get('/', 'root')

get('/foo')


@get('/bar')
def bar(c):
    c.flash(just='works!').flash({'works': 'too!'})
    c.redirect_to(c.url_for('foo'))


get('/baz', lambda c: c.render('root'))

t = Pyjo.Test.Pyjo.new()

with subtest('Rebased root'):
    t.get_ok('/').status_is(200).header_is('X-Route', 'root').content_is("""\
http://example.com/rebased/
<script src="/rebased/mojo/jquery/jquery.js"></script>
<img src="/rebased/images/test.png">
<link href="//example.com/base.css" rel="stylesheet">
<a href="mailto:sri@example.com">Contact</a>
http://example.com/rebased/
http://example.com/rebased/foo
/rebased/foo
http://example.com/
root
  Welcome to the root!
""")

with subtest('Rebased route'):
    t.get_ok('/foo').status_is(200).header_is('X-Route', 'foo').content_is("""\
http://example.com/rebased/
<link href="/rebased/b.css" media="test" rel="stylesheet">
<img alt="Test" src="/rebased/images/test.png">
http://example.com/rebased/foo
http://example.com/rebased
/rebased
http://example.com/
foo
""")

with subtest('Rebased route with flash'):
    ok(not t.ua.cookie_jar.find(t.ua.server.url().set(path='/foo')), 'no session cookie')
    t.get_ok('/bar').status_is(302).header_is('X-Route', 'bar').header_is('Location', '/rebased/foo')
    ok(t.ua.cookie_jar.find(t.ua.server.url().set(path='/foo'))[0], 'session cookie')

with subtest('Rebased route with message from flash'):
    t.get_ok('/foo').status_is(200).content_is("""\
http://example.com/rebased/works!too!
<link href="/rebased/b.css" media="test" rel="stylesheet">
<img alt="Test" src="/rebased/images/test.png">
http://example.com/rebased/foo
http://example.com/rebased
/rebased
http://example.com/
foo
""")

with subtest('Rebased route sharing a template'):
    t.get_ok('/baz').status_is(200).header_is('X-Route', 'baz').content_is("""\
http://example.com/rebased/
<script src="/rebased/mojo/jquery/jquery.js"></script>
<img src="/rebased/images/test.png">
<link href="//example.com/base.css" rel="stylesheet">
<a href="mailto:sri@example.com">Contact</a>
http://example.com/rebased/baz
http://example.com/rebased/foo
/rebased/foo
http://example.com/
baz
""")

with subtest('Does not exist'):
    t.get_ok('/yada').status_is(404).header_is('X-Route', '')

done_testing()
