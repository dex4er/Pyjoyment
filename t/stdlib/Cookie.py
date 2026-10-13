import Pyjo.Cookie.Request
import Pyjo.Cookie.Response

from Pyjo.Test import *

from http.cookies import CookieError, Morsel, SimpleCookie


with subtest('Request cookie from http.cookies'):
    cookie = Pyjo.Cookie.Request.new(SimpleCookie('foo="b r"')['foo'])
    is_ok(cookie.name, 'foo', 'right name')
    is_ok(cookie.value, 'b r', 'right value')
    cookies = Pyjo.Cookie.Request.parse(SimpleCookie('f=b; g=a'))
    is_deeply_ok([(c.name, c.value) for c in cookies], [('f', 'b'), ('g', 'a')], 'parse')

with subtest('Request cookie to http.cookies'):
    morsel = Pyjo.Cookie.Request.new(name='foo', value='b r').to_morsel()
    isa_ok(morsel, Morsel, 'morsel')
    is_ok(morsel.key, 'foo', 'right key')
    is_ok(morsel.value, 'b r', 'right value')
    is_ok(morsel.OutputString(), 'foo="b r"', 'right format')

with subtest('Response cookie from http.cookies'):
    jar = SimpleCookie()
    jar.load('foo="b r"; Domain=.example.com; Path=/test; Max-Age=60; Secure; HttpOnly; SameSite=Lax')
    jar.load('bar=baz; Expires=Thu, 07 Aug 2008 07:07:59 GMT')
    cookie = Pyjo.Cookie.Response.new(jar['foo'])
    is_ok(cookie.name, 'foo', 'right name')
    is_ok(cookie.value, 'b r', 'right value')
    is_ok(cookie.domain, 'example.com', 'right domain, as parse gives it')
    is_ok(cookie.path, '/test', 'right path')
    is_ok(cookie.max_age, 60, 'right max age value')
    is_ok(cookie.secure, True, 'right secure flag')
    is_ok(cookie.httponly, True, 'right httponly flag')
    is_ok(cookie.samesite, 'Lax', 'right samesite value')
    cookies = Pyjo.Cookie.Response.parse(jar)
    is_deeply_ok(sorted(c.name for c in cookies), ['bar', 'foo'], 'parse')
    is_ok(next(c for c in cookies if c.name == 'bar').expires, 1218092879, 'right expires value')

with subtest('Response cookie to http.cookies'):
    cookie = Pyjo.Cookie.Response.new(
        name='foo', value='b r', domain='example.com', path='/test', expires=1218092879, max_age=60
    ).set(secure=True, httponly=True, samesite='Lax')
    morsel = cookie.to_morsel()
    is_ok(morsel['domain'], 'example.com', 'right domain')
    is_ok(morsel['path'], '/test', 'right path')
    is_ok(morsel['expires'], 'Thu, 07 Aug 2008 07:07:59 GMT', 'right expires value')
    is_ok(morsel['max-age'], '60', 'right max age value')
    is_ok(morsel['secure'], True, 'right secure flag')
    is_ok(morsel['httponly'], True, 'right httponly flag')
    is_ok(morsel['samesite'], 'Lax', 'right samesite value')

with subtest('Partitioned'):
    cookie = Pyjo.Cookie.Response.new(name='foo', value='bar', partitioned=True)
    morsel = cookie.to_morsel()
    try:
        Morsel()['partitioned'] = True
        supported = True
    except CookieError:
        supported = False
    if supported:
        like_ok(morsel.OutputString(), r'; Partitioned', 'partitioned flag')
    else:
        unlike_ok(morsel.OutputString(), r'Partitioned', 'no partitioned flag, Morsel has none before Python 3.14')

with subtest('Roundtrip'):
    cookie = Pyjo.Cookie.Response.new(
        name='foo', value='b r', domain='example.com', path='/x', expires=1218092879, max_age=60
    ).set(secure=True, httponly=True, samesite='Lax')
    is_deeply_ok(vars(Pyjo.Cookie.Response.new(cookie.to_morsel())), vars(cookie), 'Pyjo -> Morsel -> Pyjo')
    is_ok(SimpleCookie(str(cookie))['foo'].value, 'b r', 'SimpleCookie(str(cookie))')

done_testing()
