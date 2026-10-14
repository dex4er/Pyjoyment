import Pyjo.UserAgent.Proxy

from Pyjo.Test import *

import os

from unittest.mock import patch


# Proxy detection
with subtest('Proxy detection with uppercase variable names'):
    proxy = Pyjo.UserAgent.Proxy.new()
    with patch.dict(
        os.environ,
        {'HTTP_PROXY': 'http://127.0.0.1', 'HTTPS_PROXY': 'http://127.0.0.1:8080', 'NO_PROXY': 'mojolicious.org'},
    ):
        proxy.detect()
        is_ok(proxy.http, 'http://127.0.0.1', 'right proxy')
        is_ok(proxy.https, 'http://127.0.0.1:8080', 'right proxy')
        proxy.http = None
        proxy.https = None
        is_ok(proxy.http, None, 'right proxy')
        is_ok(proxy.https, None, 'right proxy')
        ok(not proxy.is_needed('dummy.mojolicious.org'), 'no proxy needed')
        ok(proxy.is_needed('icious.org'), 'proxy needed')
        ok(proxy.is_needed('localhost'), 'proxy needed')

with subtest('Proxy detection with lowercase variable names'):
    with patch.dict(os.environ):
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('HTTPS_PROXY', None)
        os.environ.pop('NO_PROXY', None)

        os.environ['http_proxy'] = 'proxy.example.com'
        os.environ['https_proxy'] = 'tunnel.example.com'
        os.environ['no_proxy'] = 'localhost,localdomain,foo.com,example.com'

        proxy = Pyjo.UserAgent.Proxy.new()
        proxy.detect()
        # Renamed from Mojolicious: not
        is_deeply_ok(proxy.no, ['localhost', 'localdomain', 'foo.com', 'example.com'], 'right list')
        is_ok(proxy.http, 'proxy.example.com', 'right proxy')
        is_ok(proxy.https, 'tunnel.example.com', 'right proxy')
        ok(proxy.is_needed('dummy.mojolicious.org'), 'proxy needed')
        ok(proxy.is_needed('icious.org'), 'proxy needed')
        ok(not proxy.is_needed('localhost'), 'proxy needed')
        ok(not proxy.is_needed('localhost.localdomain'), 'no proxy needed')
        ok(not proxy.is_needed('foo.com'), 'no proxy needed')
        ok(not proxy.is_needed('example.com'), 'no proxy needed')
        ok(not proxy.is_needed('www.example.com'), 'no proxy needed')
        ok(proxy.is_needed('www.example.com.com'), 'proxy needed')

done_testing()
