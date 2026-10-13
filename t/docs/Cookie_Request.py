from Pyjo.Test import *


with subtest('Synopsis'):
    import Pyjo.Cookie.Request

    from http.cookies import SimpleCookie

    cookie = Pyjo.Cookie.Request.new()
    cookie.name = 'foo'
    cookie.value = 'bar'
    is_ok(str(cookie), 'foo=bar', 'print(cookie)')

with subtest('parse'):
    cookies = Pyjo.Cookie.Request.parse('f=b; g=a')
    is_deeply_ok([(c.name, c.value) for c in cookies], [('f', 'b'), ('g', 'a')], 'cookies')
    cookies = Pyjo.Cookie.Request.parse(SimpleCookie('f=b; g=a'))
    is_deeply_ok([(c.name, c.value) for c in cookies], [('f', 'b'), ('g', 'a')], 'SimpleCookie')

with subtest('to_str'):
    string = cookie.to_str()
    is_ok(string, 'foo=bar', 'string')

done_testing()
