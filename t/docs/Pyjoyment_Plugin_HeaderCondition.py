import Pyjo.UserAgent
import Pyjoyment

from Pyjo.Test import *
from Pyjoyment.Lite import app as lite
from Pyjoyment.Lite import get, plugin

import re


app = Pyjoyment.new()
app.log.level = 'fatal'
lite.log.level = 'fatal'

with subtest('Synopsis'):
    # Pyjoyment
    app.plugin('HeaderCondition')
    app.routes.get('/foo').requires(headers={'Referer': re.compile(r'example\.com')}).to(text='referer')

    # Pyjoyment.Lite
    plugin('HeaderCondition')

    @get('/').requires(headers={'Referer': re.compile(r'example\.com')})
    def index(c):
        c.render(text='referer')

    # All headers need to match
    app.routes.get('/foo').requires(headers={'X-Secret-Header': 'Foo', 'Referer': re.compile(r'example\.com')})

    # The "agent" condition is a shortcut for the "User-Agent" header
    @get('/').requires(agent=re.compile(r'Firefox'))
    def firefox(c):
        c.render(text='firefox')

    # The "host" condition is a shortcut for the detected host
    @get('/').requires(host=re.compile(r'mojolicious\.org'))
    def mojolicious(c):
        c.render(text='mojolicious')

    ua = Pyjo.UserAgent.new()
    ua.server.app = app
    is_ok(ua.get('/foo', {'Referer': 'http://example.com/'}).res.text, 'referer', 'headers')
    is_ok(ua.get('/foo').res.code, 404, 'no header')
    ua = Pyjo.UserAgent.new()
    ua.server.app = lite
    is_ok(ua.get('/', {'Referer': 'http://example.com/'}).res.text, 'referer', 'headers of Lite')
    is_ok(ua.get('/', {'User-Agent': 'Firefox'}).res.text, 'firefox', 'agent')
    is_ok(ua.get('/', {'Host': 'mojolicious.org'}).res.text, 'mojolicious', 'host')
    is_ok(ua.get('/').res.code, 404, 'no condition')

with subtest('register'):
    plugin = app.plugins.load_plugin('HeaderCondition')
    plugin.register(Pyjoyment.new())
    ok('headers' in app.routes.conditions, 'registered')

done_testing()
