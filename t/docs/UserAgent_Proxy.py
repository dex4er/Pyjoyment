from Pyjo.Test import *

import os

from unittest.mock import patch


with subtest('Synopsis'):
    import Pyjo.UserAgent.Proxy

    with patch.dict(os.environ, {'HTTP_PROXY': 'http://127.0.0.1:8080'}):
        proxy = Pyjo.UserAgent.Proxy.new()
        proxy.detect()
        is_ok(proxy.http, 'http://127.0.0.1:8080', 'print(proxy.http)')

with subtest('new'):
    proxy = Pyjo.UserAgent.Proxy.new()
    is_ok(proxy.http, None, 'proxy')
    proxy = Pyjo.UserAgent.Proxy.new(http='http://127.0.0.1:8080')
    is_ok(proxy.http, 'http://127.0.0.1:8080', 'proxy.http')

with subtest('http'):
    http = proxy.http
    is_ok(http, 'http://127.0.0.1:8080', 'http')
    proxy.http = 'socks://sri:secret@127.0.0.1:8080'
    is_ok(proxy.http, 'socks://sri:secret@127.0.0.1:8080', 'proxy.http')

with subtest('https'):
    https = proxy.https
    is_ok(https, None, 'https')
    proxy.https = 'http://sri:secret@127.0.0.1:8080'
    is_ok(proxy.https, 'http://sri:secret@127.0.0.1:8080', 'proxy.https')

with subtest('not_'):
    not_ = proxy.not_
    is_ok(not_, None, 'not_')
    proxy.not_ = ['localhost', 'intranet.mojolicious.org']
    is_deeply_ok(proxy.not_, ['localhost', 'intranet.mojolicious.org'], 'proxy.not_')

with subtest('detect'):
    with patch.dict(os.environ, {'NO_PROXY': 'localhost'}):
        is_ok(proxy.detect(), proxy, 'proxy')
        is_deeply_ok(proxy.not_, ['localhost'], 'NO_PROXY')

with subtest('is_needed'):
    boolean = proxy.is_needed('intranet.example.com')
    is_ok(boolean, True, 'boolean')

with subtest('prepare'):
    import Pyjo.Transaction.HTTP

    proxy.http = 'http://127.0.0.1:8080'
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://example.com')
    proxy.prepare(tx)
    is_ok(str(tx.req.proxy), 'http://127.0.0.1:8080', 'proxy of the request')

done_testing()
