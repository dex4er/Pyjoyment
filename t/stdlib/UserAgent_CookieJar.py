import Pyjo.Cookie.Response
import Pyjo.URL
import Pyjo.UserAgent.CookieJar

from Pyjo.File import curfile, tempdir
from Pyjo.Test import *

from http.cookiejar import Cookie, MozillaCookieJar


with subtest('A file of the cookie jar is read by http.cookiejar'):
    file = tempdir().child('cookies.txt')
    jar = Pyjo.UserAgent.CookieJar.new(file=file.to_str())
    jar.add(
        Pyjo.Cookie.Response.new(domain='example.com', path='/foo', name='a', value='b'),
        Pyjo.Cookie.Response.new(
            domain='www.example.com', path='/', name='c', value='d', host_only=True, secure=True, expires=4732598797
        ),
    )
    jar.save()

    # Python 3.12 reads an expiry of 0 as expired, and newer versions as a session cookie
    mozilla = MozillaCookieJar(file.to_str())
    mozilla.load(ignore_discard=True, ignore_expires=True)
    cookies = sorted(mozilla, key=lambda cookie: cookie.name)
    is_deeply_ok(
        [(c.domain, c.domain_specified, c.path, c.secure, c.expires or None, c.name, c.value) for c in cookies],
        [
            ('.example.com', True, '/foo', False, None, 'a', 'b'),
            ('www.example.com', False, '/', True, 4732598797, 'c', 'd'),
        ],
        'same cookies',
    )

with subtest('A file of http.cookiejar is read by the cookie jar'):
    file = tempdir().child('cookies.txt')
    mozilla = MozillaCookieJar(file.to_str())
    mozilla.set_cookie(
        Cookie(0, 'a', 'b', None, False, '.example.com', True, True, '/foo', True, False, None, False, None, None, {})
    )
    mozilla.set_cookie(
        Cookie(
            0,
            'c',
            'd',
            None,
            False,
            'www.example.com',
            False,
            False,
            '/',
            True,
            True,
            4732598797,
            False,
            None,
            None,
            {},
        )
    )
    mozilla.save(ignore_discard=True)

    jar = Pyjo.UserAgent.CookieJar.new(file=file.to_str()).load()
    is_deeply_ok(
        [(c.domain, c.host_only, c.path, c.secure, c.expires, c.name, c.value) for c in jar.all()],
        [
            ('example.com', False, '/foo', False, None, 'a', 'b'),
            ('www.example.com', True, '/', True, 4732598797, 'c', 'd'),
        ],
        'same cookies',
    )
    is_deeply_ok(
        [(c.name, c.value) for c in jar.find(Pyjo.URL.new('https://www.example.com/foo'))],
        [('c', 'd'), ('a', 'b')],
        'found',
    )

with subtest('A cookie with an empty value is saved and loaded'):
    file = tempdir().child('cookies.txt')
    jar = Pyjo.UserAgent.CookieJar.new(file=file.to_str())
    jar.add(Pyjo.Cookie.Response.new(domain='example.com', path='/', name='a', value=''))
    jar.save()
    is_deeply_ok([(c.name, c.value) for c in jar.empty().load().all()], [('a', '')], 'loaded')
    mozilla = MozillaCookieJar(file.to_str())
    mozilla.load(ignore_discard=True, ignore_expires=True)
    is_deeply_ok([(c.name, c.value) for c in mozilla], [('a', '')], 'loaded by http.cookiejar')

with subtest('A file with the CRLF of Windows'):
    file = tempdir().child('cookies.txt')
    file.spew('# Netscape HTTP Cookie File\r\n\r\n.example.com\tTRUE\t/\tFALSE\t0\ta\tb\r\n')
    jar = Pyjo.UserAgent.CookieJar.new(file=file.to_str()).load()
    is_deeply_ok([(c.domain, c.name, c.value) for c in jar.all()], [('example.com', 'a', 'b')], 'without the CR')

with subtest('The file of curl in the tests is read by http.cookiejar'):
    mozilla = MozillaCookieJar(curfile().dirname().sibling('cookies').child('curl.txt').to_str())
    mozilla.load(ignore_discard=True, ignore_expires=True)
    is_ok(len(mozilla), 6, 'all cookies')

done_testing()
