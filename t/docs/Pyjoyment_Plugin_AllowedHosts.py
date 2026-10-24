import Pyjo.Test.Pyjo
import Pyjoyment
import Pyjoyment.Plugin.AllowedHosts

from Pyjo.Test import *
from Pyjoyment.Lite import app as lite
from Pyjoyment.Lite import get, plugin

import re


lite.log.level = 'fatal'


def application():
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    app.routes.get('/', lambda c: c.render(text='Hello!'))
    return app


with subtest('Synopsis'):
    # Pyjoyment
    app = application()
    app.plugin('AllowedHosts')
    t = Pyjo.Test.Pyjo.new(app)
    t.get_ok('/').status_is(200)
    t.get_ok('/', {'Host': 'evil.com'}).status_is(421).content_is('Host not allowed')
    t.get_ok('/', {'Origin': 'http://evil.com'}).status_is(403).content_is('Origin not allowed')

    # Pyjoyment.Lite
    plugin('AllowedHosts')
    get('/', {'text': 'Hello!'})
    t = Pyjo.Test.Pyjo.new()
    t.get_ok('/').status_is(200)
    t.get_ok('/', {'Host': 'evil.com'}).status_is(421)

    # The hosts of a deployment, and the origins of its pages
    app = application()
    app.plugin('AllowedHosts', hosts=['example.com', '.example.com'], origins=['https://app.example.com'])
    t = Pyjo.Test.Pyjo.new(app)
    t.get_ok('/', {'Host': 'www.example.com', 'Origin': 'https://app.example.com'}).status_is(200)
    t.get_ok('/', {'Host': 'example.com', 'Origin': 'https://example.com'}).status_is(403)

    # Only for some routes, under the helper "allowed_hosts"
    app = application()
    app.plugin('AllowedHosts', hook=False)
    mcp = app.routes.under('/mcp', lambda c: c.allowed_hosts())
    mcp.post('/').to(cb=lambda c: c.render(json={'jsonrpc': '2.0'}))
    t = Pyjo.Test.Pyjo.new(app)
    t.get_ok('/', {'Host': 'evil.com'}).status_is(200)
    t.post_ok('/mcp').status_is(200).json_is({'jsonrpc': '2.0'})
    t.post_ok('/mcp', {'Origin': 'http://evil.com'}).status_is(403)

with subtest('hook'):
    app = application()
    app.plugin('AllowedHosts', hook=False)
    Pyjo.Test.Pyjo.new(app).get_ok('/', {'Host': 'evil.com'}).status_is(200)

with subtest('hosts'):
    app = application()
    app.plugin('AllowedHosts', hosts=['example.com', 'localhost:3000', '.example.org'])
    t = Pyjo.Test.Pyjo.new(app)
    t.get_ok('/', {'Host': 'example.com:8080'}).status_is(200)
    t.get_ok('/', {'Host': 'localhost:3000'}).status_is(200)
    t.get_ok('/', {'Host': 'www.example.org'}).status_is(200)
    t.get_ok('/', {'Host': 'localhost'}).status_is(421)
    app = application()
    app.plugin('AllowedHosts', hosts=[re.compile(r'^pr-\d+\.example\.com$')])
    Pyjo.Test.Pyjo.new(app).get_ok('/', {'Host': 'pr-1.example.com'}).status_is(200)
    app = application()
    app.plugin('AllowedHosts', hosts=lambda c, host: host.endswith('.internal'))
    Pyjo.Test.Pyjo.new(app).get_ok('/', {'Host': 'app.internal'}).status_is(200)
    is_deeply_ok(Pyjoyment.Plugin.AllowedHosts.HOSTS, ('localhost', '127.0.0.1', '[::1]'), 'defaults')

with subtest('origins'):
    app = application()
    app.plugin('AllowedHosts', origins=['https://app.example.com', 'http://localhost:5173'])
    t = Pyjo.Test.Pyjo.new(app)
    t.get_ok('/', {'Origin': 'http://localhost:5173'}).status_is(200)
    t.get_ok('/', {'Origin': 'http://localhost:3000'}).status_is(403)
    app = application()
    app.plugin('AllowedHosts', origins=lambda c, origin: origin.startswith('https://'))
    Pyjo.Test.Pyjo.new(app).get_ok('/', {'Origin': 'https://localhost'}).status_is(200)

with subtest('allowed_hosts'):
    app = application()
    app.plugin('AllowedHosts', hook=False)
    t = Pyjo.Test.Pyjo.new(app)
    # The helper renders the response of a request that is not allowed itself
    app.routes.get('/check', lambda c: c.allowed_hosts() and c.render(text='Allowed'))
    t.get_ok('/check').status_is(200).content_is('Allowed')
    t.get_ok('/check', {'Host': 'evil.com'}).status_is(421).content_is('Host not allowed')
    mcp = app.routes.under('/mcp', lambda c: c.allowed_hosts(hosts=['mcp.example.com']))
    mcp.post('/').to(cb=lambda c: c.render(json={'jsonrpc': '2.0'}))
    t.post_ok('/mcp', {'Host': 'mcp.example.com'}).status_is(200).json_is({'jsonrpc': '2.0'})
    t.post_ok('/mcp').status_is(421)

with subtest('register'):
    app = application()
    plugin = app.plugins.load_plugin('AllowedHosts')
    plugin.register(app)
    ok(app.renderer.get_helper('allowed_hosts'), 'helper')
    Pyjo.Test.Pyjo.new(app).get_ok('/', {'Host': 'evil.com'}).status_is(421)
    app = application()
    plugin.register(app, {'hosts': ['example.com']})
    Pyjo.Test.Pyjo.new(app).get_ok('/', {'Host': 'example.com'}).status_is(200)

done_testing()
