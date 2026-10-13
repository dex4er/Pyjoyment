from Pyjo.Test import *


with subtest('Synopsis'):
    import Pyjo.Cookie

    class MyCookie(Pyjo.Cookie.object):
        @classmethod
        def parse(cls, string=None): ...

        def to_str(self): ...

    isa_ok(MyCookie.new(), Pyjo.Cookie.object, 'MyCookie.new()')

with subtest('new'):
    import Pyjo.Cookie.Request

    from http.cookies import Morsel, SimpleCookie

    cookie = Pyjo.Cookie.Request.new()
    is_ok(cookie.name, None, 'new()')
    cookie = Pyjo.Cookie.Request.new(name='foo', value='bar')
    is_ok(str(cookie), 'foo=bar', 'name and value')
    cookie = Pyjo.Cookie.Request.new(SimpleCookie('foo=bar')['foo'])
    is_ok(str(cookie), 'foo=bar', 'Morsel')

with subtest('name'):
    cookie = Pyjo.Cookie.new()
    name = cookie.name
    is_ok(name, None, 'name')
    cookie.name = 'foo'
    is_ok(cookie.name, 'foo', 'cookie.name')

with subtest('value'):
    value = cookie.value
    is_ok(value, None, 'value')
    cookie.value = '/test'
    is_ok(cookie.value, '/test', 'cookie.value')

with subtest('__bool__'):
    boolean = bool(cookie)
    is_ok(boolean, True, 'boolean')

with subtest('__str__'):
    throws_ok(lambda: str(cookie), NotImplementedError, 'string = str(cookie)')

with subtest('parse'):
    string = 'foo=bar'
    throws_ok(lambda: cookie.parse(string), NotImplementedError, 'cookies = cookie.parse(string)')

with subtest('to_morsel'):
    morsel = cookie.to_morsel()
    isa_ok(morsel, Morsel, 'morsel')

    # "foo=\"b r\""
    is_ok(Pyjo.Cookie.Request.new(name='foo', value='b r').to_morsel().OutputString(), 'foo="b r"', 'OutputString()')

with subtest('to_str'):
    throws_ok(lambda: cookie.to_str(), NotImplementedError, 'string = cookie.to_str()')

done_testing()
