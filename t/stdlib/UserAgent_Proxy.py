import Pyjo.UserAgent.Proxy

from Pyjo.Test import *

import os

from unittest.mock import patch
from urllib.request import getproxies_environment, proxy_bypass_environment


env = {
    'http_proxy': 'http://127.0.0.1:8080',
    'https_proxy': 'http://127.0.0.1:8443',
    'no_proxy': 'localhost,example.com',
}

with subtest('The same proxies as urllib.request'):
    with patch.dict(os.environ, env, clear=True):
        proxy = Pyjo.UserAgent.Proxy.new().detect()
        proxies = getproxies_environment()
        is_ok(proxy.http, proxies['http'], 'HTTP proxy')
        is_ok(proxy.https, proxies['https'], 'HTTPS proxy')

with subtest('The same domains without a proxy as urllib.request'):
    with patch.dict(os.environ, env, clear=True):
        proxy = Pyjo.UserAgent.Proxy.new().detect()
        for host in ('localhost', 'example.com', 'www.example.com', 'mojolicious.org'):
            is_ok(proxy.is_needed(host), not proxy_bypass_environment(host), host)

done_testing()
