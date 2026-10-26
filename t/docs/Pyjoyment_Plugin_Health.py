import Pyjo.Promise
import Pyjo.Test.Pyjo
import Pyjoyment

from Pyjo.Test import *
from Pyjoyment.Lite import app as lite
from Pyjoyment.Lite import get, plugin


lite.log.level = 'fatal'


class Service:
    # A service of the application, as a database, a queue or a cache
    def __init__(self, up=True):
        self.up = up

    def ping(self):
        if not self.up:
            raise ConnectionError('Connection refused')
        return 'pong'

    @property
    def connected(self):
        return self.up


db, cache = Service(), Service()


async def queue_ready_p(c):
    await Pyjo.Promise.timer(0.01)
    return True


def search_ready_p(c):
    return Pyjo.Promise.timer(0.01, True)


def application():
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    app.routes.get('/', lambda c: c.render(text='Hello!'))
    return app


with subtest('Synopsis'):
    # Pyjoyment
    app = application()
    app.plugin('Health')
    t = Pyjo.Test.Pyjo.new(app)
    t.get_ok('/livez').status_is(200).content_is('ok')
    t.get_ok('/readyz').status_is(200).content_is('ok')

    # Pyjoyment.Lite
    plugin('Health')
    get('/', {'text': 'Hello!'})
    t = Pyjo.Test.Pyjo.new()
    t.get_ok('/livez').status_is(200).content_is('ok')
    t.get_ok('/').status_is(200).content_is('Hello!')

    # The checks of readiness, of a function, a coroutine function or one that returns a promise
    app = application()
    app.plugin('Health', checks={'db': lambda c: db.ping(), 'queue': queue_ready_p}, timeout=2)
    t = Pyjo.Test.Pyjo.new(app)
    t.get_ok('/readyz').status_is(200).content_is('ok')

    # A check that another plugin adds
    app.health.check('cache', lambda c: cache.connected)
    t.get_ok('/readyz?verbose').status_is(200).content_like(r'\[\+\]cache ok\n')
    cache.up = False
    t.get_ok('/readyz').status_is(503).content_like(r'\[-\]cache failed: reason withheld\n')
    cache.up = True

with subtest('Endpoints'):
    app = application()
    app.plugin('Health', checks={'db': lambda c: db.ping()})
    t = Pyjo.Test.Pyjo.new(app)
    t.get_ok('/livez').status_is(200).content_is('ok')
    t.get_ok('/healthz').status_is(200).content_is('ok')
    t.get_ok('/readyz').status_is(200).content_is('ok')

    t.get_ok('/readyz?verbose').status_is(200).content_is('[+]shutdown ok\n[+]db ok\nreadyz check passed\n')
    db.up = False
    with app.log.capture('warn') as logs:
        t.get_ok('/readyz?exclude=db').status_is(200).content_is('ok')
        t.get_ok('/readyz/db').status_is(503).content_is('[-]db failed: reason withheld\nreadyz check failed\n')
        t.get_ok('/livez').status_is(200).content_is('ok')
    like_ok(str(logs), r'\[warn\] .*Health check "db" failed: Connection refused', 'right message')
    db.up = True

with subtest('checks'):
    app = application()
    app.plugin('Health', checks={'db': lambda c: db.ping()})
    Pyjo.Test.Pyjo.new(app).get_ok('/readyz/db').status_is(200)

with subtest('healthz'):
    app = application()
    app.plugin('Health', healthz='/health')
    Pyjo.Test.Pyjo.new(app).get_ok('/health').status_is(200).content_is('ok')
    app = application()
    app.plugin('Health', healthz=None)
    Pyjo.Test.Pyjo.new(app).get_ok('/healthz').status_is(404)

with subtest('livez'):
    app = application()
    app.plugin('Health', livez='/-/live')
    Pyjo.Test.Pyjo.new(app).get_ok('/-/live').status_is(200).content_is('ok')

with subtest('readyz'):
    app = application()
    app.plugin('Health', readyz='/-/ready')
    Pyjo.Test.Pyjo.new(app).get_ok('/-/ready').status_is(200).content_is('ok')

with subtest('timeout'):
    app = application()
    app.plugin('Health', checks={'slow': lambda c: Pyjo.Promise.timer(1)}, timeout=0.5)
    Pyjo.Test.Pyjo.new(app).get_ok('/readyz').status_is(503)

with subtest('health.check'):
    app = application()
    app.plugin('Health')
    app.health.check('db', lambda c: db.ping())
    app.health.check('search', search_ready_p, timeout=5)
    t = Pyjo.Test.Pyjo.new(app)
    t.get_ok('/readyz?verbose').status_is(200).content_is(
        '[+]shutdown ok\n[+]db ok\n[+]search ok\nreadyz check passed\n'
    )

with subtest('health.path'):
    app = application()
    app.plugin('Health')
    c = app.build_controller()
    path = c.health.path('livez')
    is_ok(path, '/livez', 'right path')

with subtest('register'):
    app = application()
    plugin = app.plugins.load_plugin('Health')
    plugin.register(app)
    ok(app.renderer.get_helper('health.check'), 'helper')
    Pyjo.Test.Pyjo.new(app).get_ok('/readyz').status_is(200)
    app = application()
    plugin.register(app, {'checks': {'db': lambda c: True}})
    Pyjo.Test.Pyjo.new(app).get_ok('/readyz/db').status_is(200)

done_testing()
