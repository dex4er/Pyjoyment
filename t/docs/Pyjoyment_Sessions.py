import Pyjo.UserAgent
import Pyjoyment

from Pyjo.Test import *

import time


with subtest('Synopsis'):
    from Pyjoyment.Sessions import Sessions

    sessions = Sessions()
    sessions.cookie_name = 'myapp'
    sessions.default_expiration = 86400
    is_ok(sessions.cookie_name, 'myapp', 'cookie name')

    # Or import the module, as in Google Python Style Guide

    import Pyjoyment.Sessions

    sessions = Pyjoyment.Sessions.new()
    sessions.cookie_name = 'myapp'
    sessions.default_expiration = 86400
    is_ok(sessions.cookie_name, 'myapp', 'cookie name')

with subtest('cookie_domain'):
    sessions = Pyjoyment.Sessions.new()
    domain = sessions.cookie_domain
    is_ok(domain, None, 'default')
    sessions.cookie_domain = '.example.com'

with subtest('cookie_name'):
    sessions = Pyjoyment.Sessions.new()
    name = sessions.cookie_name
    is_ok(name, 'pyjoyment', 'default')
    sessions.cookie_name = 'session'

with subtest('cookie_path'):
    sessions = Pyjoyment.Sessions.new()
    path = sessions.cookie_path
    is_ok(path, '/', 'default')
    sessions.cookie_path = '/foo'

with subtest('default_expiration'):
    sessions = Pyjoyment.Sessions.new()
    time_ = sessions.default_expiration
    is_ok(time_, 3600, 'default')
    sessions.default_expiration = 3600

    app = Pyjoyment.new()
    app.log.level = 'fatal'
    c = app.build_controller()

    # Expiration date in seconds from now (persists between requests)
    c.session(expiration=604800)

    # Expiration date as absolute epoch time (only valid for one request)
    c.session(expires=time.time() + 604800)

    # Delete whole session by setting an expiration date in the past
    c.session(expires=1)

    is_ok(c.session('expires'), 1, 'expired')

with subtest('deserialize'):
    sessions = Pyjoyment.Sessions.new()
    cb = sessions.deserialize
    is_deeply_ok(cb(b'{"foo":"bar"}'), {'foo': 'bar'}, 'default')
    sessions.deserialize = lambda data: ...
    sessions.deserialize = lambda data: {}

with subtest('partitioned'):
    sessions = Pyjoyment.Sessions.new()
    boolean = sessions.partitioned
    is_ok(boolean, None, 'default')
    sessions.partitioned = True

with subtest('samesite'):
    sessions = Pyjoyment.Sessions.new()
    samesite = sessions.samesite
    is_ok(samesite, 'Lax', 'default')
    sessions.samesite = 'Strict'

    # Disable SameSite feature
    sessions.samesite = None

with subtest('secure'):
    sessions = Pyjoyment.Sessions.new()
    boolean = sessions.secure
    is_ok(boolean, None, 'default')
    sessions.secure = True

with subtest('serialize'):
    sessions = Pyjoyment.Sessions.new()
    cb = sessions.serialize
    is_ok(cb({'foo': 'bar'}), b'{"foo":"bar"}', 'default')
    sessions.serialize = lambda session: ...
    sessions.serialize = lambda session: b''

with subtest('load and store'):
    app = Pyjoyment.new(secrets=['works'])
    app.log.level = 'fatal'

    def counter(c):
        c.session(counter=(c.session('counter') or 0) + 1)
        c.render(text=str(c.session('counter')))

    app.routes.get('/', counter)
    ua = Pyjo.UserAgent.new()
    ua.server.app = app
    is_ok(ua.get('/').res.text, '1', 'stored')
    is_ok(ua.get('/').res.text, '2', 'loaded')
    c = app.build_controller()
    app.sessions.load(c)
    app.sessions.store(c)
    is_ok(c.res.cookies(), [], 'no session')

done_testing()
