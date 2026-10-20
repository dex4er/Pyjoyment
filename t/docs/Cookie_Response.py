from Pyjo.Test import *

import time


with subtest('Synopsis'):
    from Pyjo.Cookie.Response import Response

    cookie = Response()
    cookie.name = 'foo'
    cookie.value = 'bar'
    is_ok(str(cookie), 'foo=bar', 'print(cookie)')

    # Or import the module, as in Google Python Style Guide

    import Pyjo.Cookie.Response

    from http.cookies import SimpleCookie

    cookie = Pyjo.Cookie.Response.new()
    cookie.name = 'foo'
    cookie.value = 'bar'
    is_ok(str(cookie), 'foo=bar', 'print(cookie)')

with subtest('domain'):
    domain = cookie.domain
    is_ok(domain, None, 'domain')
    cookie.domain = 'localhost'
    is_ok(cookie.domain, 'localhost', 'cookie.domain')

with subtest('expires'):
    expires = cookie.expires
    is_ok(expires, None, 'expires')
    before = time.time()
    cookie.expires = time.time() + 60
    ok(cookie.expires > before, 'cookie.expires')

with subtest('host_only'):
    boolean = cookie.host_only
    is_ok(boolean, None, 'boolean')
    cookie.host_only = boolean
    is_ok(cookie.host_only, None, 'cookie.host_only')

with subtest('httponly'):
    boolean = cookie.httponly
    is_ok(boolean, None, 'boolean')
    cookie.httponly = boolean
    is_ok(cookie.httponly, None, 'cookie.httponly')

with subtest('max_age'):
    max_age = cookie.max_age
    is_ok(max_age, None, 'max_age')
    cookie.max_age = 60
    is_ok(cookie.max_age, 60, 'cookie.max_age')

with subtest('partitioned'):
    partitioned = cookie.partitioned
    is_ok(partitioned, None, 'partitioned')
    cookie.partitioned = True
    is_ok(cookie.partitioned, True, 'cookie.partitioned')

with subtest('path'):
    path = cookie.path
    is_ok(path, None, 'path')
    cookie.path = '/test'
    is_ok(cookie.path, '/test', 'cookie.path')

with subtest('samesite'):
    samesite = cookie.samesite
    is_ok(samesite, None, 'samesite')
    cookie.samesite = 'Lax'
    is_ok(cookie.samesite, 'Lax', 'cookie.samesite')

with subtest('secure'):
    boolean = cookie.secure
    is_ok(boolean, None, 'boolean')
    cookie.secure = boolean
    is_ok(cookie.secure, None, 'cookie.secure')

with subtest('parse'):
    cookies = Pyjo.Cookie.Response.parse('f=b; path=/')
    is_deeply_ok([(c.name, c.value, c.path) for c in cookies], [('f', 'b', '/')], 'cookies')
    cookies = Pyjo.Cookie.Response.parse(SimpleCookie('f=b; path=/'))
    is_deeply_ok([(c.name, c.value, c.path) for c in cookies], [('f', 'b', '/')], 'SimpleCookie')

with subtest('to_morsel'):
    morsel = cookie.to_morsel()
    is_ok(morsel['samesite'], 'Lax', 'morsel')

    # "foo=bar; Path=/; Secure"
    is_ok(
        Pyjo.Cookie.Response.new(name='foo', value='bar', path='/', secure=True).to_morsel().OutputString(),
        'foo=bar; Path=/; Secure',
        'OutputString()',
    )

with subtest('to_str'):
    string = cookie.to_str()
    like_ok(
        string,
        r'^foo=bar; expires=\w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2} GMT; domain=localhost; path=/test;'
        r' Partitioned; SameSite=Lax; Max-Age=60$',
        'string',
    )

done_testing()
