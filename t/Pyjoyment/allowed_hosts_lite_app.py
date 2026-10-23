import os


os.environ['PYJO_MODE'] = 'development'

import Pyjo.Test.Pyjo
import Pyjoyment

from Pyjo.Test import *
from Pyjoyment.Lite import app, get, plugin

import contextlib
import re


# Not in Mojolicious: Pyjoyment.Plugin.AllowedHosts, the validation of Host and Origin against DNS rebinding

app.log.level = 'fatal'

plugin('AllowedHosts')

get('/', {'text': 'Hello!'})


def application(conf, public=False):
    # An application of its own, with the options of the plugin
    other = Pyjoyment.new()
    other.log.level = 'fatal'
    other.plugin('AllowedHosts', conf)
    other.routes.get('/', lambda c: c.render(text='Hello!'))
    if public:
        other.routes.get('/public', lambda c: c.render(text='Public!'))
        mcp = other.routes.under('/mcp', lambda c: c.allowed_hosts())
        mcp.post('/').to(cb=lambda c: c.render(text='MCP!'))
        other.routes.post('/mcp', lambda c: c.render(text='Other!'))
        own = other.routes.under('/own', lambda c: c.allowed_hosts(hosts=['mcp.example.com']))
        own.post('/').to(cb=lambda c: c.render(text='Own!'))
    return Pyjo.Test.Pyjo.new(other)


@contextlib.contextmanager
def local(**env):
    saved = {name: os.environ.get(name) for name in env}
    os.environ.update(env)
    try:
        yield
    finally:
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


t = Pyjo.Test.Pyjo.new()

with subtest('Hosts of localhost'):
    t.get_ok('/').status_is(200).content_is('Hello!')
    t.get_ok('/', {'Host': 'localhost'}).status_is(200).content_is('Hello!')
    t.get_ok('/', {'Host': 'localhost:3000'}).status_is(200).content_is('Hello!')
    t.get_ok('/', {'Host': 'LocalHost:3000'}).status_is(200).content_is('Hello!')
    t.get_ok('/', {'Host': '[::1]:3000'}).status_is(200).content_is('Hello!')
    t.get_ok('/', {'Host': 'evil.com'}).status_is(421).content_is('Host not allowed')
    t.get_ok('/', {'Host': 'localhost.evil.com'}).status_is(421).content_is('Host not allowed')
    t.get_ok('/', {'Host': '127.0.0.2'}).status_is(421).content_is('Host not allowed')

with subtest('Origins of localhost'):
    t.get_ok('/', {'Origin': 'http://localhost:5173'}).status_is(200).content_is('Hello!')
    t.get_ok('/', {'Origin': 'https://127.0.0.1'}).status_is(200).content_is('Hello!')
    t.get_ok('/', {'Origin': 'http://[::1]:8080'}).status_is(200).content_is('Hello!')
    t.get_ok('/', {'Origin': 'http://evil.com'}).status_is(403).content_is('Origin not allowed')
    t.get_ok('/', {'Origin': 'null'}).status_is(403).content_is('Origin not allowed')
    t.get_ok('/', {'Origin': ''}).status_is(403).content_is('Origin not allowed')

with subtest('DNS rebinding'):
    # A page of evil.com, whose name is an address of 127.0.0.1, requests the server as its own site
    t.get_ok('/', {'Host': 'evil.com:3000', 'Origin': 'http://evil.com:3000'}).status_is(421)

with subtest('Hosts'):
    hosts = ['example.com', 'localhost:3000', '.example.org', re.compile(r'^pr-\d+\.example\.net$'), '127.0.0.1']
    other = application({'hosts': hosts})
    other.get_ok('/', {'Host': 'example.com'}).status_is(200)
    other.get_ok('/', {'Host': 'Example.COM:8080'}).status_is(200)
    other.get_ok('/', {'Host': 'www.example.com'}).status_is(421)
    other.get_ok('/', {'Host': 'localhost:3000'}).status_is(200)
    other.get_ok('/', {'Host': 'localhost:3001'}).status_is(421)
    other.get_ok('/', {'Host': 'localhost'}).status_is(421)
    other.get_ok('/', {'Host': 'example.org'}).status_is(200)
    other.get_ok('/', {'Host': 'a.b.example.org'}).status_is(200)
    other.get_ok('/', {'Host': 'evilexample.org'}).status_is(421)
    other.get_ok('/', {'Host': 'pr-42.example.net'}).status_is(200)
    other.get_ok('/', {'Host': 'pr-x.example.net'}).status_is(421)
    other = application({'hosts': ['localhost:80']})
    other.get_ok('/', {'Host': 'localhost'}).status_is(200)
    other = application({'hosts': lambda c, host: host.endswith('.internal')})
    other.get_ok('/', {'Host': 'app.internal'}).status_is(200)
    other.get_ok('/', {'Host': 'app.external'}).status_is(421)

with subtest('Origins'):
    other = application({'hosts': ['example.com', '127.0.0.1']})
    other.get_ok('/', {'Origin': 'https://example.com'}).status_is(200)
    other.get_ok('/', {'Origin': 'http://localhost:5173'}).status_is(403)
    origins = ['https://app.example.com', 'http://localhost:5173']
    other = application({'hosts': ['example.com', '127.0.0.1'], 'origins': origins})
    other.get_ok('/', {'Origin': 'https://app.example.com'}).status_is(200)
    other.get_ok('/', {'Origin': 'HTTP://LOCALHOST:5173'}).status_is(200)
    other.get_ok('/', {'Origin': 'https://example.com'}).status_is(403)
    other.get_ok('/', {'Origin': 'http://app.example.com'}).status_is(403)
    other = application({'origins': lambda c, origin: origin.startswith('https://')})
    other.get_ok('/', {'Origin': 'https://anything.example'}).status_is(200)
    other.get_ok('/', {'Origin': 'http://localhost'}).status_is(403)

with subtest('Helper'):
    other = application({'hook': False}, public=True)
    other.get_ok('/', {'Host': 'evil.com'}).status_is(200).content_is('Hello!')
    other.get_ok('/public', {'Origin': 'http://evil.com'}).status_is(200).content_is('Public!')
    other.post_ok('/mcp').status_is(200).content_is('MCP!')
    other.post_ok('/mcp', {'Host': 'evil.com'}).status_is(421).content_is('Host not allowed')
    other.post_ok('/mcp', {'Origin': 'http://evil.com'}).status_is(403).content_is('Origin not allowed')
    other.post_ok('/own', {'Host': 'mcp.example.com'}).status_is(200).content_is('Own!')
    other.post_ok('/own', {'Host': 'mcp.example.com', 'Origin': 'https://mcp.example.com'}).status_is(200)
    other.post_ok('/own').status_is(421).content_is('Host not allowed')

with subtest('Reverse proxy'), local(PYJO_REVERSE_PROXY='1'):
    # The host is the one of Host, which the proxy passes on, not of X-Forwarded-Host, which Pyjoyment does not read
    other = application({'hosts': ['example.com']})
    other.get_ok('/', {'Host': 'example.com', 'X-Forwarded-Proto': 'https'}).status_is(200)
    other.get_ok('/', {'Host': 'evil.com', 'X-Forwarded-Host': 'example.com'}).status_is(421)

done_testing()
