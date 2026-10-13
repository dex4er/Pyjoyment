from Pyjo.Test import *


with subtest('Synopsis'):
    import Pyjo.Cookie.Request

    cookie = Pyjo.Cookie.Request.new()
    cookie.name = 'foo'
    cookie.value = 'bar'
    is_ok(str(cookie), 'foo=bar', 'print(cookie)')

with subtest('parse'):
    cookies = Pyjo.Cookie.Request.parse('f=b; g=a')
    is_deeply_ok([(c.name, c.value) for c in cookies], [('f', 'b'), ('g', 'a')], 'cookies')

with subtest('to_str'):
    string = cookie.to_str()
    is_ok(string, 'foo=bar', 'string')

done_testing()
