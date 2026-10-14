from Pyjo.File import tempdir
from Pyjo.Test import *

import os


with subtest('Synopsis'):
    import Pyjo.Cookie.Response
    import Pyjo.URL
    import Pyjo.UserAgent.CookieJar

    # Add response cookies
    jar = Pyjo.UserAgent.CookieJar.new()
    jar.add(
        Pyjo.Cookie.Response.new(
            name='foo',
            value='bar',
            domain='localhost',
            path='/test',
        )
    )

    # Find request cookies
    found = []
    for cookie in jar.find(Pyjo.URL.new('http://localhost/test')):
        found.append((cookie.name, cookie.value))
    is_deeply_ok(found, [('foo', 'bar')], 'print(cookie.name), print(cookie.value)')

with subtest('new'):
    jar = Pyjo.UserAgent.CookieJar.new()
    is_ok(jar.file, None, 'jar')
    jar = Pyjo.UserAgent.CookieJar.new(file='cookies.txt')
    is_ok(jar.file, 'cookies.txt', 'jar.file')

with subtest('file'):
    cwd = os.getcwd()
    tmp = tempdir()
    os.chdir(tmp)
    try:
        jar = Pyjo.UserAgent.CookieJar.new()
        file = jar.file
        is_ok(file, None, 'file')
        jar.file = '/home/sri/cookies.txt'
        is_ok(jar.file, '/home/sri/cookies.txt', 'jar.file')

        jar.add(Pyjo.Cookie.Response.new(name='foo', value='bar', domain='localhost', path='/'))

        # Save cookies to file
        jar.file = 'cookies.txt'
        jar.save()
        ok(os.path.exists('cookies.txt'), 'saved')

        # Empty cookie jar and load cookies from file
        jar.file = 'cookies.txt'
        jar.empty().load()
        is_ok(jar.all()[0].name, 'foo', 'loaded')
    finally:
        os.chdir(cwd)

with subtest('ignore'):
    ignore = jar.ignore
    is_ok(ignore, None, 'ignore')
    jar.ignore = lambda cookie: ...
    ok(callable(jar.ignore), 'jar.ignore')

    # Ignore all cookies
    jar.ignore = lambda cookie: True
    ok(jar.ignore(Pyjo.Cookie.Response.new()), 'all cookies')

    # Ignore cookies for domains "com", "net" and "org"
    jar.ignore = lambda cookie: cookie.domain in ('com', 'net', 'org')
    ok(jar.ignore(Pyjo.Cookie.Response.new(domain='com')), 'com')
    ok(not jar.ignore(Pyjo.Cookie.Response.new(domain='mojolicious.org')), 'mojolicious.org')

with subtest('max_cookie_size'):
    size = jar.max_cookie_size
    is_ok(size, 4096, 'size')
    jar.max_cookie_size = 4096
    is_ok(jar.max_cookie_size, 4096, 'jar.max_cookie_size')

with subtest('add'):
    jar = Pyjo.UserAgent.CookieJar.new()
    cookies = [Pyjo.Cookie.Response.new(name='a', value='b', domain='localhost', path='/')]
    is_ok(jar.add(*cookies), jar, 'jar')

with subtest('all'):
    cookies = jar.all()
    is_ok(len(cookies), 1, 'cookies')

    # Names of all cookies
    names = []
    for cookie in jar.all():
        names.append(cookie.name)
    is_deeply_ok(names, ['a'], 'print(cookie.name)')

with subtest('collect'):
    import Pyjo.Transaction.HTTP

    jar.collect(Pyjo.Transaction.HTTP.new())
    is_ok(len(jar.all()), 1, 'nothing collected')

with subtest('empty'):
    is_ok(jar.empty(), jar, 'jar')
    is_deeply_ok(jar.all(), [], 'empty')

with subtest('find'):
    cookies = jar.find(Pyjo.URL.new())
    is_deeply_ok(cookies, [], 'cookies')

    # Names of all cookies found
    jar.add(Pyjo.Cookie.Response.new(name='a', value='b', domain='example.com', path='/foo'))
    names = []
    for cookie in jar.find(Pyjo.URL.new('http://example.com/foo')):
        names.append(cookie.name)
    is_deeply_ok(names, ['a'], 'print(cookie.name)')

with subtest('load'):
    is_ok(jar.load(), jar, 'jar')

with subtest('prepare'):
    tx = Pyjo.Transaction.HTTP.new()
    jar.prepare(tx)
    is_deeply_ok(tx.req.cookies(), [], 'no cookies for no URL')

with subtest('save'):
    is_ok(jar.save(), jar, 'jar')

with subtest('to_str'):
    string = jar.to_str()
    is_ok(string, '.example.com\tTRUE\t/foo\tFALSE\t0\ta\tb\n', 'string')

done_testing()
