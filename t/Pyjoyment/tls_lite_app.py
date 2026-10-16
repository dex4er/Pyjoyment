import Pyjo.Test.Pyjo

from Pyjo.Test import *
from Pyjoyment.Lite import app, get


# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# Left out from Mojolicious: plan skip_all unless TEST_TLS, as the ssl module comes with Python, and unless can_tls

# Unlike Mojolicious: the session cookie is "pyjoyment", as Pyjoyment.Sessions names it

# Silence
app.log.level = 'fatal'

# Secure sessions
app.sessions.secure = True


@get('/login')
def login(c):
    name = c.param('name') or 'anonymous'
    c.session(name=name)
    c.render(text=f'Welcome {name}!')


@get('/again')
def again(c):
    name = c.session('name') or 'anonymous'
    c.render(text=f'Welcome back {name}!')


@get('/logout')
def logout(c):
    c.session(expires=1)
    c.redirect_to('login')


# Use HTTPS
t = Pyjo.Test.Pyjo.new()
t.ua.max_redirects = 5
t.reset_session().ua.server.url('https')

# Login
t.get_ok('/login?name=sri', {'X-Forwarded-Proto': 'https'}).status_is(200).content_is('Welcome sri!')
ok(t.tx.res.cookie('pyjoyment').expires, 'session cookie expires')
ok(t.tx.res.cookie('pyjoyment').secure, 'session cookie is secure')

# Return
t.get_ok('/again', {'X-Forwarded-Proto': 'https'}).status_is(200).content_is('Welcome back sri!')

# Logout
t.get_ok('/logout', {'X-Forwarded-Proto': 'https'}).status_is(200).content_is('Welcome anonymous!')

# Expired session
t.get_ok('/again', {'X-Forwarded-Proto': 'https'}).status_is(200).content_is('Welcome back anonymous!')

# No session
t.get_ok('/logout', {'X-Forwarded-Proto': 'https'}).status_is(200).content_is('Welcome anonymous!')

# Use HTTP
t.reset_session().ua.server.url('http')

# Login again
t.reset_session().get_ok('/login?name=sri').status_is(200).content_is('Welcome sri!')

# Return
t.get_ok('/again').status_is(200).content_is('Welcome back anonymous!')

# Use HTTPS again (without expiration)
t.reset_session().ua.server.url('https')
app.sessions.default_expiration = 0

# Login again
t.get_ok('/login?name=sri', {'X-Forwarded-Proto': 'https'}).status_is(200).content_is('Welcome sri!')
ok(not t.tx.res.cookie('pyjoyment').expires, 'session cookie does not expire')
ok(t.tx.res.cookie('pyjoyment').secure, 'session cookie is secure')

# Return
t.get_ok('/again', {'X-Forwarded-Proto': 'https'}).status_is(200).content_is('Welcome back sri!')

# Logout
t.get_ok('/logout', {'X-Forwarded-Proto': 'https'}).status_is(200).content_is('Welcome anonymous!')

# Expired session
t.get_ok('/again', {'X-Forwarded-Proto': 'https'}).status_is(200).content_is('Welcome back anonymous!')

# No session
t.get_ok('/logout', {'X-Forwarded-Proto': 'https'}).status_is(200).content_is('Welcome anonymous!')

done_testing()
