import Pyjo.UserAgent
import Pyjoyment

from Pyjo.Test import *

import re


app = Pyjoyment.new()
app.log.level = 'fatal'
# TODO: the not found page in HTML, when Pyjoyment.Plugin.EPRenderer is ported
app.exception_format = 'txt'

with subtest('Synopsis'):
    # Pyjoyment
    app.plugin('HeaderCondition')
    app.routes.get('/foo').requires(headers={'Referer': re.compile(r'example\.com')}).to(text='referer')

    # All headers need to match
    app.routes.get('/foo').requires(headers={'X-Secret-Header': 'Foo', 'Referer': re.compile(r'example\.com')})

    # The "agent" condition is a shortcut for the "User-Agent" header
    app.routes.get('/').requires(agent=re.compile(r'Firefox')).to(text='firefox')

    # The "host" condition is a shortcut for the detected host
    app.routes.get('/').requires(host=re.compile(r'mojolicious\.org')).to(text='mojolicious')

    ua = Pyjo.UserAgent.new()
    ua.server.app = app
    is_ok(ua.get('/foo', {'Referer': 'http://example.com/'}).res.text, 'referer', 'headers')
    is_ok(ua.get('/foo').res.code, 404, 'no header')
    is_ok(ua.get('/', {'User-Agent': 'Firefox'}).res.text, 'firefox', 'agent')
    is_ok(ua.get('/', {'Host': 'mojolicious.org'}).res.text, 'mojolicious', 'host')

with subtest('register'):
    plugin = app.plugins.load_plugin('HeaderCondition')
    plugin.register(Pyjoyment.new())
    ok('headers' in app.routes.conditions, 'registered')

done_testing()
