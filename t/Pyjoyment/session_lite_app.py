import Pyjo.Test.Pyjo

from Pyjo.Test import *
from Pyjoyment.Lite import app, get


# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

app.secrets = ['test1']


@get('/login')
def login(c):
    c.session(user='sri')
    c.render(text='logged in')


@get('/session')
def session(c):
    user = c.session().get('user') or 'nobody'
    c.render(text=f'user:{user}')


@get('/logout')
def logout(c):
    del c.session()['user']
    c.render(text='logged out')


t = Pyjo.Test.Pyjo.new()

with subtest('User session (signed cookie)'):
    # Left out from Mojolicious: the assertion that sessions are not encrypted by default, as encrypted sessions are
    # left out with encrypt_cookie
    t.get_ok('/session').status_is(200).content_is('user:nobody')
    t.get_ok('/session').status_is(200).content_is('user:nobody')
    t.get_ok('/login').status_is(200).content_is('logged in')
    t.get_ok('/session').status_is(200).content_is('user:sri')
    like_ok(t.tx.res.cookies()[0].value, r'^[^-]+-+[^-]+$', 'signed cookie format')
    t.get_ok('/session').status_is(200).content_is('user:sri')
    t.get_ok('/logout').status_is(200).content_is('logged out')
    t.get_ok('/session').status_is(200).content_is('user:nobody')
    t.get_ok('/session').status_is(200).content_is('user:nobody')

# Left out from Mojolicious: the subtest "User session (encrypted cookie)", as encrypted sessions are left out with
# encrypt_cookie

with subtest('Rotating secrets'):
    with subtest('User session (signed cookie)'):
        t.reset_session()
        t.app.secrets = ['test1']
        # Left out from Mojolicious: encrypted(0) of the sessions, which are not encrypted
        t.get_ok('/session').status_is(200).content_is('user:nobody')
        t.get_ok('/session').status_is(200).content_is('user:nobody')
        t.get_ok('/login').status_is(200).content_is('logged in')
        t.get_ok('/session').status_is(200).content_is('user:sri')
        t.app.secrets = ['test2', 'test1']
        t.get_ok('/session').status_is(200).content_is('user:sri')
        t.get_ok('/logout').status_is(200).content_is('logged out')
        t.get_ok('/session').status_is(200).content_is('user:nobody')
        t.get_ok('/session').status_is(200).content_is('user:nobody')

    # Left out from Mojolicious: the subtest "User session (encrypted cookie)", as encrypted sessions are left out with
    # encrypt_cookie

done_testing()
