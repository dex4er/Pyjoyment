import Pyjo.Cookie
import Pyjo.Cookie.Request
import Pyjo.Cookie.Response

from Pyjo.Test import *

import re


with subtest('Missing name'):
    is_ok(str(Pyjo.Cookie.Request.new()), '', 'right format')
    is_ok(str(Pyjo.Cookie.Response.new()), '', 'right format')

with subtest('Request cookie as string'):
    cookie = Pyjo.Cookie.Request.new()
    cookie.name = '0'
    cookie.value = 'ba =r'
    is_ok(cookie.to_str(), '0="ba =r"', 'right format')

with subtest('Request cookie without value as string'):
    cookie = Pyjo.Cookie.Request.new()
    cookie.name = 'foo'
    is_ok(cookie.to_str(), 'foo=', 'right format')
    cookie = Pyjo.Cookie.Request.new()
    cookie.name = 'foo'
    cookie.value = ''
    is_ok(cookie.to_str(), 'foo=', 'right format')

with subtest('Empty request cookie'):
    is_deeply_ok(Pyjo.Cookie.Request.parse(), [], 'no cookies')

with subtest('Parse normal request cookie (RFC 2965)'):
    cookies = Pyjo.Cookie.Request.parse('$Version=1; foo=bar; $Path="/test"')
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Parse request cookies from multiple header values (RFC 2965)'):
    cookies = Pyjo.Cookie.Request.parse('$Version=1; foo=bar; $Path="/test", $Version=0; baz=yada; $Path="/tset"')
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[1].name, 'baz', 'right name')
    is_ok(cookies[1].value, 'yada', 'right value')
    is_ok(len(cookies), 2, 'no more cookies')

with subtest('Parse request cookie (Netscape)'):
    cookies = Pyjo.Cookie.Request.parse('CUSTOMER=WILE_E_COYOTE')
    is_ok(cookies[0].name, 'CUSTOMER', 'right name')
    is_ok(cookies[0].value, 'WILE_E_COYOTE', 'right value')
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Parse multiple request cookies (Netscape)'):
    cookies = Pyjo.Cookie.Request.parse('CUSTOMER=WILE_E_COYOTE; PART_NUMBER=ROCKET_LAUNCHER_0001')
    is_ok(cookies[0].name, 'CUSTOMER', 'right name')
    is_ok(cookies[0].value, 'WILE_E_COYOTE', 'right value')
    is_ok(cookies[1].name, 'PART_NUMBER', 'right name')
    is_ok(cookies[1].value, 'ROCKET_LAUNCHER_0001', 'right value')
    is_ok(len(cookies), 2, 'no more cookies')

with subtest('Parse multiple request cookies from multiple header values (Netscape)'):
    cookies = Pyjo.Cookie.Request.parse('CUSTOMER=WILE_E_COYOTE, PART_NUMBER=ROCKET_LAUNCHER_0001')
    is_ok(cookies[0].name, 'CUSTOMER', 'right name')
    is_ok(cookies[0].value, 'WILE_E_COYOTE', 'right value')
    is_ok(cookies[1].name, 'PART_NUMBER', 'right name')
    is_ok(cookies[1].value, 'ROCKET_LAUNCHER_0001', 'right value')
    is_ok(len(cookies), 2, 'no more cookies')

with subtest('Parse request cookie without value (RFC 2965)'):
    cookies = Pyjo.Cookie.Request.parse('$Version=1; foo=; $Path="/test"')
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, '', 'no value')
    is_ok(len(cookies), 1, 'no more cookies')
    cookies = Pyjo.Cookie.Request.parse('$Version=1; foo=""; $Path="/test"')
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, '', 'no value')
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Parse quoted request cookie (RFC 2965)'):
    cookies = Pyjo.Cookie.Request.parse('$Version=1; foo="b ,a\\" r\\"\\\\"; $Path="/test"')
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'b ,a" r"\\', 'right value')
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Parse quoted request cookie roundtrip (RFC 2965)'):
    cookies = Pyjo.Cookie.Request.parse('$Version=1; foo="b ,a\\";= r\\"\\\\"; $Path="/test"')
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'b ,a";= r"\\', 'right value')
    is_ok(len(cookies), 1, 'no more cookies')
    cookies = Pyjo.Cookie.Request.parse(cookies[0].to_str())
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'b ,a";= r"\\', 'right value')
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Parse quoted request cookie roundtrip (RFC 2965, alternative)'):
    cookies = Pyjo.Cookie.Request.parse('$Version=1; foo="b ,a\\" r\\"\\\\"; $Path="/test"')
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'b ,a" r"\\', 'right value')
    is_ok(len(cookies), 1, 'no more cookies')
    cookies = Pyjo.Cookie.Request.parse(cookies[0].to_str())
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'b ,a" r"\\', 'right value')
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Parse quoted request cookie roundtrip (RFC 2965, another alternative)'):
    cookies = Pyjo.Cookie.Request.parse('$Version=1; foo="b ;a\\" r\\"\\\\"; $Path="/test"')
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'b ;a" r"\\', 'right value')
    is_ok(len(cookies), 1, 'no more cookies')
    cookies = Pyjo.Cookie.Request.parse(cookies[0].to_str())
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'b ;a" r"\\', 'right value')
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Parse quoted request cookie roundtrip (RFC 2965, yet another alternative)'):
    cookies = Pyjo.Cookie.Request.parse('$Version=1; foo="\\"b a\\" r\\""; $Path="/test"')
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, '"b a" r"', 'right value')
    is_ok(len(cookies), 1, 'no more cookies')
    cookies = Pyjo.Cookie.Request.parse(cookies[0].to_str())
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, '"b a" r"', 'right value')
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Parse multiple cookie request (RFC 2965)'):
    cookies = Pyjo.Cookie.Request.parse('$Version=1; foo=bar; $Path=/test; baz="la la"; $Path=/tset')
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[1].name, 'baz', 'right name')
    is_ok(cookies[1].value, 'la la', 'right value')
    is_ok(len(cookies), 2, 'no more cookies')

with subtest('Response cookie as string'):
    cookie = Pyjo.Cookie.Response.new()
    cookie.name = 'foo'
    cookie.value = 'ba r'
    cookie.path = '/test'
    is_ok(cookie.to_str(), 'foo="ba r"; path=/test', 'right format')

with subtest('Response cookie without value as string'):
    cookie = Pyjo.Cookie.Response.new()
    cookie.name = 'foo'
    cookie.path = '/test'
    is_ok(cookie.to_str(), 'foo=; path=/test', 'right format')
    cookie = Pyjo.Cookie.Response.new()
    cookie.name = 'foo'
    cookie.value = ''
    cookie.path = '/test'
    is_ok(cookie.to_str(), 'foo=; path=/test', 'right format')

with subtest('Full response cookie as string'):
    cookie = Pyjo.Cookie.Response.new()
    cookie.name = '0'
    cookie.value = 'ba r'
    cookie.domain = 'example.com'
    cookie.path = '/test'
    cookie.partitioned = True
    cookie.max_age = 60
    cookie.expires = 1218092879
    cookie.secure = True
    cookie.httponly = True
    cookie.samesite = 'Lax'
    is_ok(
        cookie.to_str(),
        '0="ba r"; expires=Thu, 07 Aug 2008 07:07:59 GMT; domain=example.com;'
        ' path=/test; Partitioned; secure; HttpOnly; SameSite=Lax; Max-Age=60',
        'right format',
    )

with subtest('Empty response cookie'):
    is_deeply_ok(Pyjo.Cookie.Response.parse(), [], 'no cookies')

with subtest('Parse response cookie (Netscape)'):
    cookies = Pyjo.Cookie.Response.parse('CUSTOMER=WILE_E_COYOTE; path=/; expires=Tuesday, 09-Nov-1999 23:12:40 GMT')
    is_ok(cookies[0].name, 'CUSTOMER', 'right name')
    is_ok(cookies[0].value, 'WILE_E_COYOTE', 'right value')
    is_ok(cookies[0].expires, 942189160, 'right expires value')
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Parse multiple response cookies (Netscape)'):
    cookies = Pyjo.Cookie.Response.parse(
        'CUSTOMER=WILE_E_COYOTE; expires=Tuesday, 09-Nov-1999 23:12:40 GMT; path=/'
        ',SHIPPING=FEDEX; path=/; expires=Tuesday, 09-Nov-1999 23:12:41 GMT'
    )
    is_ok(cookies[0].name, 'CUSTOMER', 'right name')
    is_ok(cookies[0].value, 'WILE_E_COYOTE', 'right value')
    is_ok(cookies[0].expires, 942189160, 'right expires value')
    is_ok(cookies[1].name, 'SHIPPING', 'right name')
    is_ok(cookies[1].value, 'FEDEX', 'right value')
    is_ok(cookies[1].expires, 942189161, 'right expires value')
    is_ok(len(cookies), 2, 'no more cookies')

with subtest('Parse response cookie (RFC 6265)'):
    cookies = Pyjo.Cookie.Response.parse(
        'foo="ba r"; Domain=example.com; Path=/test; Max-Age=60; Expires=Thu, 07 Aug 2008 07:07:59 GMT; Secure;'
    )
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'ba r', 'right value')
    is_ok(cookies[0].domain, 'example.com', 'right domain')
    is_ok(cookies[0].path, '/test', 'right path')
    is_ok(cookies[0].max_age, 60, 'right max age value')
    is_ok(cookies[0].expires, 1218092879, 'right expires value')
    is_ok(cookies[0].secure, True, 'right secure flag')
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Partitioned cookie (RFC 6265 CHIPS)'):
    cookies = Pyjo.Cookie.Response.parse(
        'foo="bar"; Domain=example.com; Partitioned; Path=/test;'
        'Max-Age=60; Expires=Thu, 07 Aug 2008 07:07:59 GMT; Secure;'
    )
    is_ok(cookies[0].partitioned, True, 'right partitioned value')

    cookies = Pyjo.Cookie.Response.parse(
        'foo="bar"; Domain=example.com; Path=/test; Max-Age=60; Expires=Thu, 07 Aug 2008 07:07:59 GMT; Secure;'
    )
    is_ok(cookies[0].partitioned, None, 'no partitioned value')

with subtest('Parse response cookie with invalid flag (RFC 6265)'):
    cookies = Pyjo.Cookie.Response.parse(
        'foo="ba r"; Domain=.example.com; Path=/test; Max-Age=60; Expires=Thu, 07 Aug 2008 07:07:59 GMT; InSecure;'
    )
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'ba r', 'right value')
    is_ok(cookies[0].domain, 'example.com', 'right domain')
    is_ok(cookies[0].path, '/test', 'right path')
    is_ok(cookies[0].max_age, 60, 'right max age value')
    is_ok(cookies[0].expires, 1218092879, 'right expires value')
    is_ok(cookies[0].secure, None, 'no secure flag')
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Parse quoted response cookie (RFC 6265)'):
    cookies = Pyjo.Cookie.Response.parse(
        'foo="b a\\" r\\"\\\\"; Domain=example.com; Path=/test; Max-Age=60;'
        ' Expires=Thu, 07 Aug 2008 07:07:59 GMT; Secure'
    )
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'b a" r"\\', 'right value')
    is_ok(cookies[0].domain, 'example.com', 'right domain')
    is_ok(cookies[0].path, '/test', 'right path')
    is_ok(cookies[0].max_age, 60, 'right max age value')
    is_ok(cookies[0].expires, 1218092879, 'right expires value')
    is_ok(cookies[0].secure, True, 'right secure flag')
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Parse quoted response cookie (RFC 6265, alternative)'):
    cookies = Pyjo.Cookie.Response.parse(
        'foo="b a\\" ;r\\"\\\\" ; domain=example.com ; path=/test ; Max-Age=60'
        ' ; expires=Thu, 07 Aug 2008 07:07:59 GMT ; secure'
    )
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'b a" ;r"\\', 'right value')
    is_ok(cookies[0].domain, 'example.com', 'right domain')
    is_ok(cookies[0].path, '/test', 'right path')
    is_ok(cookies[0].max_age, 60, 'right max age value')
    is_ok(cookies[0].expires, 1218092879, 'right expires value')
    is_ok(cookies[0].secure, True, 'right secure flag')
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Parse quoted response cookie roundtrip (RFC 6265)'):
    cookies = Pyjo.Cookie.Response.parse(
        'foo="b ,a\\";= r\\"\\\\"; Domain=example.com; Path=/test; Max-Age=60;'
        ' Expires=Thu, 07 Aug 2008 07:07:59 GMT; Secure'
    )
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'b ,a";= r"\\', 'right value')
    is_ok(cookies[0].domain, 'example.com', 'right domain')
    is_ok(cookies[0].path, '/test', 'right path')
    is_ok(cookies[0].max_age, 60, 'right max age value')
    is_ok(cookies[0].expires, 1218092879, 'right expires value')
    is_ok(cookies[0].secure, True, 'right secure flag')
    is_ok(len(cookies), 1, 'no more cookies')
    cookies = Pyjo.Cookie.Response.parse(cookies[0].to_str())
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'b ,a";= r"\\', 'right value')
    is_ok(cookies[0].domain, 'example.com', 'right domain')
    is_ok(cookies[0].path, '/test', 'right path')
    is_ok(cookies[0].max_age, 60, 'right max age value')
    is_ok(cookies[0].expires, 1218092879, 'right expires value')
    is_ok(cookies[0].secure, True, 'right secure flag')
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Parse quoted response cookie roundtrip (RFC 6265, alternative)'):
    cookies = Pyjo.Cookie.Response.parse(
        'foo="b ,a\\" r\\"\\\\"; Domain=example.com; Path=/test; Max-Age=60;'
        ' Expires=Thu, 07 Aug 2008 07:07:59 GMT; Secure'
    )
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'b ,a" r"\\', 'right value')
    is_ok(cookies[0].domain, 'example.com', 'right domain')
    is_ok(cookies[0].path, '/test', 'right path')
    is_ok(cookies[0].max_age, 60, 'right max age value')
    is_ok(cookies[0].expires, 1218092879, 'right expires value')
    is_ok(cookies[0].secure, True, 'right secure flag')
    is_ok(len(cookies), 1, 'no more cookies')
    cookies = Pyjo.Cookie.Response.parse(cookies[0].to_str())
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'b ,a" r"\\', 'right value')
    is_ok(cookies[0].domain, 'example.com', 'right domain')
    is_ok(cookies[0].path, '/test', 'right path')
    is_ok(cookies[0].max_age, 60, 'right max age value')
    is_ok(cookies[0].expires, 1218092879, 'right expires value')
    is_ok(cookies[0].secure, True, 'right secure flag')
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Parse quoted response cookie roundtrip (RFC 6265, another alternative)'):
    cookies = Pyjo.Cookie.Response.parse(
        'foo="b ;a\\" r\\"\\\\"; Domain=example.com; Path=/test; Max-Age=60;'
        ' Expires=Thu, 07 Aug 2008 07:07:59 GMT;  Secure'
    )
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'b ;a" r"\\', 'right value')
    is_ok(cookies[0].domain, 'example.com', 'right domain')
    is_ok(cookies[0].path, '/test', 'right path')
    is_ok(cookies[0].max_age, 60, 'right max age value')
    is_ok(cookies[0].expires, 1218092879, 'right expires value')
    is_ok(cookies[0].secure, True, 'right secure flag')
    is_ok(len(cookies), 1, 'no more cookies')
    cookies = Pyjo.Cookie.Response.parse(cookies[0].to_str())
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'b ;a" r"\\', 'right value')
    is_ok(cookies[0].domain, 'example.com', 'right domain')
    is_ok(cookies[0].path, '/test', 'right path')
    is_ok(cookies[0].max_age, 60, 'right max age value')
    is_ok(cookies[0].expires, 1218092879, 'right expires value')
    is_ok(cookies[0].secure, True, 'right secure flag')
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Parse quoted response cookie roundtrip (RFC 6265, yet another alternative)'):
    cookies = Pyjo.Cookie.Response.parse(
        'foo="\\"b a\\" r\\""; Domain=example.com; Path=/test; Max-Age=60;'
        ' Expires=Thu, 07 Aug 2008 07:07:59 GMT; Secure'
    )
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, '"b a" r"', 'right value')
    is_ok(cookies[0].domain, 'example.com', 'right domain')
    is_ok(cookies[0].path, '/test', 'right path')
    is_ok(cookies[0].max_age, 60, 'right max age value')
    is_ok(cookies[0].expires, 1218092879, 'right expires value')
    is_ok(cookies[0].secure, True, 'right secure flag')
    is_ok(len(cookies), 1, 'no more cookies')
    cookies = Pyjo.Cookie.Response.parse(cookies[0].to_str())
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, '"b a" r"', 'right value')
    is_ok(cookies[0].domain, 'example.com', 'right domain')
    is_ok(cookies[0].path, '/test', 'right path')
    is_ok(cookies[0].max_age, 60, 'right max age value')
    is_ok(cookies[0].expires, 1218092879, 'right expires value')
    is_ok(cookies[0].secure, True, 'right secure flag')
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Parse response cookie without value (RFC 2965)'):
    cookies = Pyjo.Cookie.Response.parse(
        'foo=""; Version=1; Domain=example.com; Path=/test; Max-Age=60; expires=Thu, 07 Aug 2008 07:07:59 GMT; Secure'
    )
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, '', 'no value')
    is_ok(cookies[0].domain, 'example.com', 'right domain')
    is_ok(cookies[0].path, '/test', 'right path')
    is_ok(cookies[0].max_age, 60, 'right max age value')
    is_ok(cookies[0].expires, 1218092879, 'right expires value')
    is_ok(cookies[0].secure, True, 'right secure flag')
    is_ok(
        cookies[0].to_str(),
        'foo=; expires=Thu, 07 Aug 2008 07:07:59 GMT; domain=example.com; path=/test; secure; Max-Age=60',
        'right result',
    )
    is_ok(len(cookies), 1, 'no more cookies')
    cookies = Pyjo.Cookie.Response.parse(
        'foo=; Version=1; domain=example.com; path=/test; Max-Age=60; expires=Thu, 07 Aug 2008 07:07:59 GMT; secure'
    )
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, '', 'no value')
    is_ok(cookies[0].domain, 'example.com', 'right domain')
    is_ok(cookies[0].path, '/test', 'right path')
    is_ok(cookies[0].max_age, 60, 'right max age value')
    is_ok(cookies[0].expires, 1218092879, 'right expires value')
    is_ok(cookies[0].secure, True, 'right secure flag')
    is_ok(
        cookies[0].to_str(),
        'foo=; expires=Thu, 07 Aug 2008 07:07:59 GMT; domain=example.com; path=/test; secure; Max-Age=60',
        'right result',
    )
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Parse response cookie with SameSite value'):
    cookies = Pyjo.Cookie.Response.parse('foo=bar; Path=/; Expires=Tuesday, 09-Nov-99 23:12:40 GMT; SameSite=Lax')
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[0].domain, None, 'no domain')
    is_ok(cookies[0].path, '/', 'right path')
    is_ok(cookies[0].max_age, None, 'no max age value')
    is_ok(cookies[0].expires, 942189160, 'right expires value')
    is_ok(cookies[0].samesite, 'Lax', 'right samesite value')
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Parse response cookie with broken Expires and Domain values'):
    cookies = Pyjo.Cookie.Response.parse('foo="ba r"; Expires=Th')
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'ba r', 'right value')
    is_ok(cookies[0].expires, None, 'no expires value')
    is_ok(cookies[0].domain, None, 'no domain value')
    is_ok(len(cookies), 1, 'no more cookies')
    cookies = Pyjo.Cookie.Response.parse('foo="ba r"; Expires=Th; Domain=; Path=/test')
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'ba r', 'right value')
    is_ok(cookies[0].expires, None, 'no expires value')
    is_ok(cookies[0].domain, '', 'no domain value')
    is_ok(len(cookies), 1, 'no more cookies')
    cookies = Pyjo.Cookie.Response.parse('foo="ba r"; Expires; Domain; Path=/test')
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'ba r', 'right value')
    is_ok(cookies[0].expires, None, 'no expires value')
    is_ok(cookies[0].domain, None, 'no domain value')
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Response cookie with Max-Age 0 and Expires 0'):
    cookie = Pyjo.Cookie.Response.new()
    cookie.name = 'foo'
    cookie.value = 'bar'
    cookie.path = '/'
    cookie.max_age = 0
    cookie.expires = 0
    is_ok(cookie.to_str(), 'foo=bar; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; Max-Age=0', 'right format')

with subtest('Parse response cookie with Max-Age 0 and Expires 0 (RFC 6265)'):
    cookies = Pyjo.Cookie.Response.parse(
        'foo=bar; Domain=example.com; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Secure'
    )
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[0].domain, 'example.com', 'right domain')
    is_ok(cookies[0].path, '/', 'right path')
    is_ok(cookies[0].max_age, 0, 'right max age value')
    is_ok(cookies[0].expires, 0, 'right expires value')
    is_ok(cookies[0].secure, True, 'right secure flag')
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Parse response cookie with two digit year (RFC 6265)'):
    cookies = Pyjo.Cookie.Response.parse('foo=bar; Path=/; Expires=Saturday, 09-Nov-19 23:12:40 GMT; Secure')
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[0].path, '/', 'right path')
    is_ok(cookies[0].expires, 1573341160, 'right expires value')
    is_ok(cookies[0].secure, True, 'right secure flag')
    is_ok(len(cookies), 1, 'no more cookies')
    cookies = Pyjo.Cookie.Response.parse('foo=bar; Path=/; Expires=Tuesday, 09-Nov-99 23:12:40 GMT; Secure')
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[0].path, '/', 'right path')
    is_ok(cookies[0].expires, 942189160, 'right expires value')
    is_ok(cookies[0].secure, True, 'right secure flag')
    is_ok(len(cookies), 1, 'no more cookies')

with subtest('Abstract methods'):
    throws_ok(
        lambda: Pyjo.Cookie.object.parse(''),
        re.compile(r'Method "parse" not implemented by subclass'),
        'right error',
    )
    throws_ok(
        lambda: Pyjo.Cookie.new().to_str(),
        re.compile(r'Method "to_str" not implemented by subclass'),
        'right error',
    )

done_testing()
