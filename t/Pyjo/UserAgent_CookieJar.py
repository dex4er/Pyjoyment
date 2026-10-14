import Pyjo.Cookie.Response
import Pyjo.File
import Pyjo.Transaction.HTTP
import Pyjo.URL
import Pyjo.UserAgent.CookieJar

from Pyjo.File import curfile, tempdir
from Pyjo.Test import *

import os
import time


with subtest('Missing values'):
    jar = Pyjo.UserAgent.CookieJar.new()
    jar.add(Pyjo.Cookie.Response.new(domain='example.com'))
    jar.add(Pyjo.Cookie.Response.new(name='foo'))
    jar.add(Pyjo.Cookie.Response.new(name='foo', domain='example.com'))
    jar.add(Pyjo.Cookie.Response.new(domain='example.com', path='/'))
    is_deeply_ok(jar.all(), [], 'no cookies')

with subtest('Session cookie'):
    jar = Pyjo.UserAgent.CookieJar.new()
    jar.add(
        Pyjo.Cookie.Response.new(domain='example.com', path='/foo', name='foo', value='bar'),
        Pyjo.Cookie.Response.new(domain='example.com', path='/', name='just', value='works'),
    )
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[1].name, 'just', 'right name')
    is_ok(cookies[1].value, 'works', 'right value')
    is_ok(len(cookies), 2, 'no third cookie')
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[1].name, 'just', 'right name')
    is_ok(cookies[1].value, 'works', 'right value')
    is_ok(len(cookies), 2, 'no third cookie')
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[1].name, 'just', 'right name')
    is_ok(cookies[1].value, 'works', 'right value')
    is_ok(len(cookies), 2, 'no third cookie')
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[1].name, 'just', 'right name')
    is_ok(cookies[1].value, 'works', 'right value')
    is_ok(len(cookies), 2, 'no third cookie')
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[1].name, 'just', 'right name')
    is_ok(cookies[1].value, 'works', 'right value')
    is_ok(len(cookies), 2, 'no third cookie')
    jar.empty()
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo'))
    is_ok(len(cookies), 0, 'no cookies')

with subtest('"localhost"'):
    jar = Pyjo.UserAgent.CookieJar.new()
    jar.add(
        Pyjo.Cookie.Response.new(domain='localhost', path='/foo', name='foo', value='bar'),
        Pyjo.Cookie.Response.new(domain='foo.localhost', path='/foo', name='bar', value='baz'),
    )
    cookies = jar.find(Pyjo.URL.new('http://localhost/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(len(cookies), 1, 'no second cookie')
    cookies = jar.find(Pyjo.URL.new('http://foo.localhost/foo'))
    is_ok(cookies[0].name, 'bar', 'right name')
    is_ok(cookies[0].value, 'baz', 'right value')
    is_ok(cookies[1].name, 'foo', 'right name')
    is_ok(cookies[1].value, 'bar', 'right value')
    is_ok(len(cookies), 2, 'no third cookie')
    cookies = jar.find(Pyjo.URL.new('http://foo.bar.localhost/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(len(cookies), 1, 'no second cookie')
    cookies = jar.find(Pyjo.URL.new('http://bar.foo.localhost/foo'))
    is_ok(cookies[0].name, 'bar', 'right name')
    is_ok(cookies[0].value, 'baz', 'right value')
    is_ok(cookies[1].name, 'foo', 'right name')
    is_ok(cookies[1].value, 'bar', 'right value')
    is_ok(len(cookies), 2, 'no third cookie')

with subtest('Huge cookie'):
    jar = Pyjo.UserAgent.CookieJar.new()
    jar.max_cookie_size = 1024
    jar.add(
        Pyjo.Cookie.Response.new(domain='example.com', path='/foo', name='small', value='x'),
        Pyjo.Cookie.Response.new(domain='example.com', path='/foo', name='big', value='x' * 1024),
        Pyjo.Cookie.Response.new(domain='example.com', path='/foo', name='huge', value='x' * 1025),
    )
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo'))
    is_ok(cookies[0].name, 'small', 'right name')
    is_ok(cookies[0].value, 'x', 'right value')
    is_ok(cookies[1].name, 'big', 'right name')
    is_ok(cookies[1].value, 'x' * 1024, 'right value')
    is_ok(len(cookies), 2, 'no second cookie')

with subtest('Expired cookies'):
    jar = Pyjo.UserAgent.CookieJar.new()
    jar.add(
        Pyjo.Cookie.Response.new(domain='example.com', path='/foo', name='foo', value='bar'),
        Pyjo.Cookie.Response.new(domain='labs.example.com', path='/', name='baz', value='24', max_age=-1),
        Pyjo.Cookie.Response.new(domain='labs.example.com', path='/', name='qux', value='qux', max_age=0),
    )
    expired = Pyjo.Cookie.Response.new(domain='labs.example.com', path='/', name='baz', value='23')
    expired.expires = int(time.time()) - 1
    jar.add(expired)
    cookies = jar.find(Pyjo.URL.new('http://labs.example.com/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(len(cookies), 1, 'no second cookie')

with subtest('Replace cookie'):
    jar = Pyjo.UserAgent.CookieJar.new()
    jar.add(
        Pyjo.Cookie.Response.new(domain='example.com', path='/foo', name='foo', value='bar1'),
        Pyjo.Cookie.Response.new(domain='example.com', path='/foo', name='foo', value='bar2'),
    )
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar2', 'right value')
    is_ok(len(cookies), 1, 'no second cookie')

with subtest('Switch between secure and normal cookies'):
    jar = Pyjo.UserAgent.CookieJar.new()
    jar.add(Pyjo.Cookie.Response.new(domain='example.com', path='/foo', name='foo', value='foo', secure=True))
    cookies = jar.find(Pyjo.URL.new('https://example.com/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'foo', 'right value')
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo'))
    is_ok(len(cookies), 0, 'no insecure cookie')
    jar.add(Pyjo.Cookie.Response.new(domain='example.com', path='/foo', name='foo', value='bar'))
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    cookies = jar.find(Pyjo.URL.new('https://example.com/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(len(cookies), 1, 'no second cookie')

with subtest('"(" in path'):
    jar = Pyjo.UserAgent.CookieJar.new()
    jar.add(Pyjo.Cookie.Response.new(domain='example.com', path='/foo(bar', name='foo', value='bar'))
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo(bar'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(len(cookies), 1, 'no second cookie')
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo(bar/baz'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(len(cookies), 1, 'no second cookie')

with subtest('Gather and prepare cookies without domain and path'):
    jar = Pyjo.UserAgent.CookieJar.new()
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://mojolicious.org/perldoc/Mojolicious')
    tx.res.cookies(Pyjo.Cookie.Response.new(name='foo', value='without'))
    jar.collect(tx)
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://mojolicious.org/perldoc')
    jar.prepare(tx)
    is_ok(tx.req.cookie('foo').name, 'foo', 'right name')
    is_ok(tx.req.cookie('foo').value, 'without', 'right value')
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://mojolicious.org/perldoc')
    jar.prepare(tx)
    is_ok(tx.req.cookie('foo').name, 'foo', 'right name')
    is_ok(tx.req.cookie('foo').value, 'without', 'right value')
    is_ok(jar.all()[0].name, 'foo', 'right name')
    is_ok(jar.all()[0].value, 'without', 'right value')
    is_ok(jar.all()[0].domain, 'mojolicious.org', 'right domain')
    is_ok(len(jar.all()), 1, 'no second cookie')
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://www.mojolicious.org/perldoc')
    jar.prepare(tx)
    is_ok(tx.req.cookie('foo'), None, 'no cookie')
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://mojolicious.org/whatever')
    jar.prepare(tx)
    is_ok(tx.req.cookie('foo'), None, 'no cookie')
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://...many...dots...')
    jar.prepare(tx)
    is_ok(tx.req.cookie('foo'), None, 'no cookie')

with subtest('Gather and prepare cookies with same name (with and without domain)'):
    jar = Pyjo.UserAgent.CookieJar.new()
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://example.com/test')
    tx.res.cookies(
        Pyjo.Cookie.Response.new(name='foo', value='without'),
        Pyjo.Cookie.Response.new(name='foo', value='with', domain='example.com'),
    )
    jar.collect(tx)
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://example.com/test')
    jar.prepare(tx)
    cookies = tx.req.every_cookie('foo')
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'with', 'right value')
    is_ok(len(cookies), 1, 'no second cookie')
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://www.example.com/test')
    jar.prepare(tx)
    cookies = tx.req.every_cookie('foo')
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'with', 'right value')
    is_ok(len(cookies), 1, 'no second cookie')

with subtest('Gather and prepare cookies for "localhost" (valid and invalid)'):
    jar = Pyjo.UserAgent.CookieJar.new()
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://localhost:3000')
    tx.res.cookies(
        Pyjo.Cookie.Response.new(name='foo', value='local', domain='localhost'),
        Pyjo.Cookie.Response.new(name='bar', value='local', domain='bar.localhost'),
    )
    jar.collect(tx)
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://localhost:8080')
    jar.prepare(tx)
    is_ok(tx.req.cookie('foo').name, 'foo', 'right name')
    is_ok(tx.req.cookie('foo').value, 'local', 'right value')
    is_ok(tx.req.cookie('bar'), None, 'no cookie')

with subtest('Gather and prepare cookies for unknown public suffix (with IDNA)'):
    jar = Pyjo.UserAgent.CookieJar.new()
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://bücher.com/foo')
    tx.res.cookies(
        Pyjo.Cookie.Response.new(domain='com', path='/foo', name='foo', value='bar'),
        Pyjo.Cookie.Response.new(domain='xn--bcher-kva.com', path='/foo', name='bar', value='baz'),
    )
    jar.collect(tx)
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://bücher.com/foo')
    jar.prepare(tx)
    is_ok(tx.req.cookie('foo').name, 'foo', 'right name')
    is_ok(tx.req.cookie('foo').value, 'bar', 'right value')
    is_ok(tx.req.cookie('bar').name, 'bar', 'right name')
    is_ok(tx.req.cookie('bar').value, 'baz', 'right value')

with subtest('Gather and prepare cookies for public suffix (with IDNA)'):
    jar = Pyjo.UserAgent.CookieJar.new()
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://bücher.com/foo')
    tx.res.cookies(
        Pyjo.Cookie.Response.new(domain='com', path='/foo', name='foo', value='bar'),
        Pyjo.Cookie.Response.new(domain='xn--bcher-kva.com', path='/foo', name='bar', value='baz'),
    )
    jar.ignore = lambda cookie: cookie.domain == 'com'
    jar.collect(tx)
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://bücher.com/foo')
    jar.prepare(tx)
    is_ok(tx.req.cookie('foo'), None, 'no cookie')
    is_ok(tx.req.cookie('bar').name, 'bar', 'right name')
    is_ok(tx.req.cookie('bar').value, 'baz', 'right value')

with subtest('Gather and prepare cookies with domain and path'):
    jar = Pyjo.UserAgent.CookieJar.new()
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://LABS.bücher.Com/perldoc/Mojolicious')
    tx.res.cookies(
        Pyjo.Cookie.Response.new(name='foo', value='with', domain='labs.xn--bcher-kva.com', path='/perldoc'),
        Pyjo.Cookie.Response.new(name='bar', value='with', domain='xn--bcher-kva.com', path='/'),
        Pyjo.Cookie.Response.new(name='0', value='with', domain='.xn--bcher-kva.cOm', path='/%70erldoc/Mojolicious/'),
    )
    jar.collect(tx)
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://labs.bücher.COM/perldoc/Mojolicious/Lite')
    jar.prepare(tx)
    is_ok(tx.req.cookie('foo').name, 'foo', 'right name')
    is_ok(tx.req.cookie('foo').value, 'with', 'right value')
    is_ok(tx.req.cookie('bar').name, 'bar', 'right name')
    is_ok(tx.req.cookie('bar').value, 'with', 'right value')
    is_ok(tx.req.cookie('0').name, '0', 'right name')
    is_ok(tx.req.cookie('0').value, 'with', 'right value')
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://bücher.COM/perldoc/Mojolicious/Lite')
    jar.prepare(tx)
    is_ok(tx.req.cookie('foo'), None, 'no cookie')
    is_ok(tx.req.cookie('bar').name, 'bar', 'right name')
    is_ok(tx.req.cookie('bar').value, 'with', 'right value')
    is_ok(tx.req.cookie('0').name, '0', 'right name')
    is_ok(tx.req.cookie('0').value, 'with', 'right value')
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://labs.bücher.COM/Perldoc')
    jar.prepare(tx)
    is_ok(tx.req.cookie('foo'), None, 'no cookie')
    is_ok(tx.req.cookie('bar').name, 'bar', 'right name')
    is_ok(tx.req.cookie('bar').value, 'with', 'right value')

with subtest('Gather and prepare cookies with IP address'):
    jar = Pyjo.UserAgent.CookieJar.new()
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://213.133.102.53/perldoc/Mojolicious')
    tx.res.cookies(
        Pyjo.Cookie.Response.new(name='foo', value='valid', domain='213.133.102.53'),
        Pyjo.Cookie.Response.new(name='bar', value='too'),
    )
    jar.collect(tx)
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://213.133.102.53/perldoc/Mojolicious')
    jar.prepare(tx)
    is_ok(tx.req.cookie('foo').name, 'foo', 'right name')
    is_ok(tx.req.cookie('foo').value, 'valid', 'right value')
    is_ok(tx.req.cookie('bar').name, 'bar', 'right name')
    is_ok(tx.req.cookie('bar').value, 'too', 'right value')

with subtest('Gather cookies with invalid expiration'):
    jar = Pyjo.UserAgent.CookieJar.new()
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://example.com')
    tx.res.cookies(
        Pyjo.Cookie.Response.new(name='foo', value='bar', max_age='invalid'),
        Pyjo.Cookie.Response.new(name='bar', value='baz', max_age=86400),
    )
    jar.collect(tx)
    is_ok(jar.all()[0].name, 'foo', 'right name')
    is_ok(jar.all()[0].value, 'bar', 'right value')
    ok(not jar.all()[0].expires, 'does not expire')
    is_ok(jar.all()[1].name, 'bar', 'right name')
    is_ok(jar.all()[1].value, 'baz', 'right value')
    ok(jar.all()[1].expires, 'expires')

with subtest('Gather cookies with invalid domain'):
    jar = Pyjo.UserAgent.CookieJar.new()
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://labs.example.com/perldoc/Mojolicious')
    tx.res.cookies(
        Pyjo.Cookie.Response.new(name='foo', value='invalid', domain='a.s.example.com'),
        Pyjo.Cookie.Response.new(name='foo', value='invalid', domain='mojolicious.org'),
    )
    jar.collect(tx)
    is_deeply_ok(jar.all(), [], 'no cookies')

with subtest('Gather cookies with invalid domain (IP address)'):
    jar = Pyjo.UserAgent.CookieJar.new()
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://213.133.102.53/perldoc/Mojolicious')
    tx.res.cookies(
        Pyjo.Cookie.Response.new(name='foo', value='valid', domain='213.133.102.53.'),
        Pyjo.Cookie.Response.new(name='foo', value='valid', domain='.133.102.53'),
        Pyjo.Cookie.Response.new(name='foo', value='invalid', domain='102.53'),
        Pyjo.Cookie.Response.new(name='foo', value='invalid', domain='53'),
    )
    jar.collect(tx)
    is_deeply_ok(jar.all(), [], 'no cookies')

with subtest('Gather cookies with invalid path'):
    jar = Pyjo.UserAgent.CookieJar.new()
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://labs.example.com/perldoc/Mojolicious')
    tx.res.cookies(
        Pyjo.Cookie.Response.new(name='foo', value='invalid', path='/perldoc/index.html'),
        Pyjo.Cookie.Response.new(name='foo', value='invalid', path='/perldocMojolicious'),
        Pyjo.Cookie.Response.new(name='foo', value='invalid', path='/perldoc.Mojolicious'),
    )
    jar.collect(tx)
    is_deeply_ok(jar.all(), [], 'no cookies')

with subtest('Load cookies from Netscape cookies.txt file'):
    # Unlike Mojolicious: the cookie files of the tests are in t/cookies, as the certificates are in t/certs
    cookies_dir = curfile().dirname().sibling('cookies')

    with subtest('Not configured'):
        jar = Pyjo.UserAgent.CookieJar.new()
        is_deeply_ok(jar.load().all(), [], 'no cookies')

    with subtest('Missing file'):
        jar = Pyjo.UserAgent.CookieJar.new()
        jar.file = cookies_dir.child('missing.txt').to_str()
        is_deeply_ok(jar.load().all(), [], 'no cookies')

    with subtest('Load file created by curl'):
        jar = Pyjo.UserAgent.CookieJar.new()
        jar.file = cookies_dir.child('curl.txt').to_str()
        cookies = jar.load().all()

        is_ok(cookies[0].name, 'AEC', 'right name')
        is_ok(cookies[0].value, 'Ack', 'right value')
        is_ok(cookies[0].domain, 'google.com', 'right domain')
        is_ok(cookies[0].path, '/', 'right path')
        is_ok(cookies[0].expires, 4713964099, 'expires')
        is_ok(cookies[0].secure, True, 'is secure')
        is_ok(cookies[0].httponly, True, 'is HttpOnly')
        is_ok(cookies[0].host_only, False, 'allows subdomains')

        is_ok(cookies[1].name, '__Secure-ENID', 'right name')
        is_ok(cookies[1].value, '15.SE', 'right value')
        is_ok(cookies[1].domain, 'google.com', 'right domain')
        is_ok(cookies[1].path, '/', 'right path')
        is_ok(cookies[1].expires, 4732598797, 'expires')
        is_ok(cookies[1].secure, True, 'is secure')
        is_ok(cookies[1].httponly, True, 'is HttpOnly')
        is_ok(cookies[1].host_only, False, 'allows subdomains')

        is_ok(cookies[2].name, 'csv', 'right name')
        is_ok(cookies[2].value, '2', 'right value')
        is_ok(cookies[2].domain, 'reddit.com', 'right domain')
        is_ok(cookies[2].path, '/', 'right path')
        is_ok(cookies[2].expires, 4761486052, 'expires')
        is_ok(cookies[2].secure, True, 'is secure')
        is_ok(cookies[2].httponly, False, 'not HttpOnly')
        is_ok(cookies[2].host_only, False, 'allows subdomains')

        is_ok(cookies[3].name, 'csrf_token', 'right name')
        is_ok(cookies[3].value, '3329d93c563f6a017045f516c5c515fc', 'right value')
        is_ok(cookies[3].domain, 'reddit.com', 'right domain')
        is_ok(cookies[3].path, '/', 'right path')
        ok(not cookies[3].expires, 'does not expire')
        is_ok(cookies[3].secure, True, 'is secure')
        is_ok(cookies[3].httponly, False, 'not HttpOnly')
        is_ok(cookies[3].host_only, False, 'allows subdomains')

        is_ok(cookies[4].name, 'CONSENT', 'right name')
        is_ok(cookies[4].value, 'PENDING+648', 'right value')
        is_ok(cookies[4].domain, 'whatever.youtube.com', 'right domain')
        is_ok(cookies[4].path, '/about', 'right path')
        is_ok(cookies[4].expires, 4761484436, 'expires')
        is_ok(cookies[4].secure, True, 'is secure')
        is_ok(cookies[4].httponly, False, 'not HttpOnly')
        is_ok(cookies[4].host_only, False, 'allows subdomains')

        is_ok(cookies[5].name, 'susecom-cookie', 'right name')
        is_ok(cookies[5].value, '50fbf56aa575290e', 'right value')
        is_ok(cookies[5].domain, 'www.suse.com', 'right domain')
        is_ok(cookies[5].path, '/', 'right path')
        ok(not cookies[5].expires, 'does not expire')
        is_ok(cookies[5].secure, False, 'not secure')
        is_ok(cookies[5].httponly, False, 'not HttpOnly')
        is_ok(cookies[5].host_only, True, 'does not allow subdomains')

with subtest('Save cookies to Netscape cookies.txt file'):
    tmp = tempdir()

    with subtest('Not configured'):
        jar = Pyjo.UserAgent.CookieJar.new()
        is_deeply_ok(jar.save().all(), [], 'no cookies')

    with subtest('Empty jar'):
        file = tmp.child('empty.txt')
        jar = Pyjo.UserAgent.CookieJar.new(file=file.to_str())

        ok(not os.path.exists(file), 'file does not exist')
        is_deeply_ok(jar.save().all(), [], 'no cookies')
        ok(os.path.exists(file), 'file exists')
        is_deeply_ok(jar.load().all(), [], 'no cookies')

        content = file.slurp('UTF-8')
        like_ok(content, r'# Netscape HTTP Cookie File', 'Netscape comment is present')
        # Unlike Mojolicious: the file says that Pyjoyment generated it
        like_ok(
            content, r'# This file was generated by Pyjoyment! Edit at your own risk.', 'warning comment is present'
        )

    with subtest('Store standard cookies'):
        file = tmp.child('session.txt')
        jar = Pyjo.UserAgent.CookieJar.new(file=file.to_str())

        jar.add(Pyjo.Cookie.Response.new(domain='example.com', path='/foo', name='a', value='b'))

        ok(not os.path.exists(file), 'file does not exist')
        jar.save()
        ok(os.path.exists(file), 'file exists')
        content = file.slurp('UTF-8')

        like_ok(content, r'# Netscape HTTP Cookie File', 'Netscape comment is present')
        # Unlike Mojolicious: the file says that Pyjoyment generated it
        like_ok(
            content, r'# This file was generated by Pyjoyment! Edit at your own risk.', 'warning comment is present'
        )
        like_ok(content, r'example\.com\tTRUE\t\/foo\tFALSE\t0\ta\tb', 'cookie is present')

        jar2 = Pyjo.UserAgent.CookieJar.new(file=file.to_str()).load()
        cookies = jar2.all()
        is_ok(cookies[0].name, 'a', 'right name')
        is_ok(cookies[0].value, 'b', 'right value')
        is_ok(cookies[0].domain, 'example.com', 'right domain')
        is_ok(cookies[0].path, '/foo', 'right path')
        ok(not cookies[0].expires, 'does not expire')
        is_ok(len(cookies), 1, 'no more cookies')

        jar2.empty().add(Pyjo.Cookie.Response.new(domain='mojolicious.org', path='/', name='c', value='d')).save()

        jar3 = Pyjo.UserAgent.CookieJar.new(file=file.to_str()).load()
        cookies = jar3.all()
        is_ok(cookies[0].name, 'c', 'right name')
        is_ok(cookies[0].value, 'd', 'right value')
        is_ok(cookies[0].domain, 'mojolicious.org', 'right domain')
        is_ok(cookies[0].path, '/', 'right path')
        ok(not cookies[0].expires, 'does not expire')
        is_ok(len(cookies), 1, 'no more cookies')

with subtest('Stringify cookies in Netscape format'):
    with subtest('Session cookies'):
        jar = Pyjo.UserAgent.CookieJar.new()
        jar.add(
            Pyjo.Cookie.Response.new(domain='mojolicious.org', path='/', name='c', value='d'),
            Pyjo.Cookie.Response.new(domain='example.com', path='/foo', name='foo', value='bar'),
        )
        content = jar.to_str()
        like_ok(content, r'mojolicious\.org\tTRUE\t\/\tFALSE\t0\tc\td', 'first cookie')
        like_ok(content, r'example\.com\tTRUE\t\/foo\tFALSE\t0\tfoo\tbar', 'second cookie')

    with subtest('Secure cookies'):
        jar = Pyjo.UserAgent.CookieJar.new()
        jar.add(
            Pyjo.Cookie.Response.new(
                domain='www.mojolicious.org',
                path='/',
                secure=True,
                host_only=True,
                expires=4732598797,
                name='one',
                value='One',
            )
        )
        content = jar.to_str()
        like_ok(content, r'www.mojolicious.org\tFALSE\t\/\tTRUE\t4732598797\tone\tOne', 'first cookie')

done_testing()
