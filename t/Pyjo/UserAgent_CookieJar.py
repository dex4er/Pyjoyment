if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import Pyjo.Cookie.Response
    import Pyjo.URL

    import time

    import Pyjo.Transaction.HTTP
    import Pyjo.UserAgent.CookieJar

    # Missing values
    jar = Pyjo.UserAgent.CookieJar.new()
    jar.add(Pyjo.Cookie.Response.new(domain='example.com'))
    jar.add(Pyjo.Cookie.Response.new(name='foo'))
    jar.add(Pyjo.Cookie.Response.new(name='foo', domain='example.com'))
    jar.add(Pyjo.Cookie.Response.new(domain='example.com', path='/'))
    is_deeply_ok(jar.all, [], 'no cookies')

    # Session cookie
    jar.add(
        Pyjo.Cookie.Response.new(domain='example.com', path='/foo', name='foo', value='bar'),
        Pyjo.Cookie.Response.new(domain='example.com', path='/', name='just', value='works'),
    )
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[1].name, 'just', 'right name')
    is_ok(cookies[1].value, 'works', 'right value')
    throws_ok(lambda: cookies[2], IndexError, 'no third cookie')
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[1].name, 'just', 'right name')
    is_ok(cookies[1].value, 'works', 'right value')
    throws_ok(lambda: cookies[2], IndexError, 'no third cookie')
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[1].name, 'just', 'right name')
    is_ok(cookies[1].value, 'works', 'right value')
    throws_ok(lambda: cookies[2], IndexError, 'no third cookie')
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[1].name, 'just', 'right name')
    is_ok(cookies[1].value, 'works', 'right value')
    throws_ok(lambda: cookies[2], IndexError, 'no third cookie')
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[1].name, 'just', 'right name')
    is_ok(cookies[1].value, 'works', 'right value')
    throws_ok(lambda: cookies[2], IndexError, 'no third cookie')
    jar.empty()
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo'))
    throws_ok(lambda: cookies[0], IndexError, 'no cookies')

    # "localhost"
    jar = Pyjo.UserAgent.CookieJar.new()
    jar.add(
        Pyjo.Cookie.Response.new(domain='localhost', path='/foo', name='foo', value='bar'),
        Pyjo.Cookie.Response.new(domain='foo.localhost', path='/foo', name='bar', value='baz'),
    )
    cookies = jar.find(Pyjo.URL.new('http://localhost/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    throws_ok(lambda: cookies[1], IndexError, 'no second cookie')
    cookies = jar.find(Pyjo.URL.new('http://foo.localhost/foo'))
    is_ok(cookies[0].name, 'bar', 'right name')
    is_ok(cookies[0].value, 'baz', 'right value')
    is_ok(cookies[1].name, 'foo', 'right name')
    is_ok(cookies[1].value, 'bar', 'right value')
    throws_ok(lambda: cookies[2], IndexError, 'no third cookie')
    cookies = jar.find(Pyjo.URL.new('http://foo.bar.localhost/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    throws_ok(lambda: cookies[1], IndexError, 'no second cookie')
    cookies = jar.find(Pyjo.URL.new('http://bar.foo.localhost/foo'))
    is_ok(cookies[0].name, 'bar', 'right name')
    is_ok(cookies[0].value, 'baz', 'right value')
    is_ok(cookies[1].name, 'foo', 'right name')
    is_ok(cookies[1].value, 'bar', 'right value')
    throws_ok(lambda: cookies[2], IndexError, 'no third cookie')

    # Random top-level domain and IDNA
    jar = Pyjo.UserAgent.CookieJar.new()
    jar.add(
        Pyjo.Cookie.Response.new(domain='com', path='/foo', name='foo', value='bar'),
        Pyjo.Cookie.Response.new(domain='xn--bcher-kva.com', path='/foo', name='bar', value='baz'),
    )
    cookies = jar.find(Pyjo.URL.new('http://bücher.com/foo'))
    is_ok(cookies[0].name, 'bar', 'right name')
    is_ok(cookies[0].value, 'baz', 'right value')
    throws_ok(lambda: cookies[1], IndexError, 'no second cookie')
    cookies = jar.find(Pyjo.URL.new('http://bücher.com/foo'))
    is_ok(cookies[0].name, 'bar', 'right name')
    is_ok(cookies[0].value, 'baz', 'right value')
    throws_ok(lambda: cookies[1], IndexError, 'no second cookie')
    cookies = jar.all
    is_ok(cookies[0].domain, 'com', 'right domain')
    is_ok(cookies[0].path, '/foo', 'right path')
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[1].domain, 'xn--bcher-kva.com', 'right domain')
    is_ok(cookies[1].path, '/foo', 'right path')
    is_ok(cookies[1].name, 'bar', 'right name')
    is_ok(cookies[1].value, 'baz', 'right value')
    throws_ok(lambda: cookies[2], IndexError, 'no third cookie')

    # Huge cookie
    jar = Pyjo.UserAgent.CookieJar.new(max_cookie_size=1024)
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
    throws_ok(lambda: cookies[2], IndexError, 'no second cookie')

    # Expired cookies
    jar = Pyjo.UserAgent.CookieJar.new()
    jar.add(
        Pyjo.Cookie.Response.new(domain='example.com', path='/foo', name='foo', value='bar'),
        Pyjo.Cookie.Response.new(domain='labs.example.com', path='/', name='baz', value='24', max_age=-1),
    )
    expired = Pyjo.Cookie.Response.new(domain='labs.example.com', path='/', name='baz', value='23')
    jar.add(expired.set(expires=time.time() - 1))
    cookies = jar.find(Pyjo.URL.new('http://labs.example.com/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    throws_ok(lambda: cookies[1], IndexError, 'no second cookie')

    # Replace cookie
    jar = Pyjo.UserAgent.CookieJar.new()
    jar.add(
        Pyjo.Cookie.Response.new(domain='example.com', path='/foo', name='foo', value='bar1'),
        Pyjo.Cookie.Response.new(domain='example.com', path='/foo', name='foo', value='bar2'),
    )
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar2', 'right value')
    throws_ok(lambda: cookies[1], IndexError, 'no second cookie')

    # Switch between secure and normal cookies
    jar = Pyjo.UserAgent.CookieJar.new()
    jar.add(Pyjo.Cookie.Response.new(domain='example.com', path='/foo', name='foo', value='foo', secure=1))
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
    throws_ok(lambda: cookies[1], IndexError, 'no second cookie')

    # Ignore leading dot
    jar = Pyjo.UserAgent.CookieJar.new()
    jar.add(
        Pyjo.Cookie.Response.new(domain='.example.com', path='/foo', name='foo', value='bar'),
        Pyjo.Cookie.Response.new(domain='example.com', path='/foo', name='bar', value='baz'),
    )
    cookies = jar.find(Pyjo.URL.new('http://www.labs.example.com/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[1].name, 'bar', 'right name')
    is_ok(cookies[1].value, 'baz', 'right value')
    throws_ok(lambda: cookies[2], IndexError, 'no third cookie')
    cookies = jar.find(Pyjo.URL.new('http://labs.example.com/foo'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[1].name, 'bar', 'right name')
    is_ok(cookies[1].value, 'baz', 'right value')
    throws_ok(lambda: cookies[2], IndexError, 'no third cookie')
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo/bar'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[1].name, 'bar', 'right name')
    is_ok(cookies[1].value, 'baz', 'right value')
    throws_ok(lambda: cookies[2], IndexError, 'no third cookie')
    cookies = jar.find(Pyjo.URL.new('http://example.com/foobar'))
    throws_ok(lambda: cookies[0], IndexError, 'no cookies')

    # "(" in path
    jar = Pyjo.UserAgent.CookieJar.new()
    jar.add(Pyjo.Cookie.Response.new(domain='example.com', path='/foo(bar', name='foo', value='bar'))
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo(bar'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    throws_ok(lambda: cookies[1], IndexError, 'no second cookie')
    cookies = jar.find(Pyjo.URL.new('http://example.com/foo(bar/baz'))
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    throws_ok(lambda: cookies[1], IndexError, 'no second cookie')

    # Gather and prepare cookies without domain and path
    jar = Pyjo.UserAgent.CookieJar.new()
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://mojolicio.us/perldoc/Mojolicious')
    tx.res.cookies(Pyjo.Cookie.Response.new(name='foo', value='without'))
    jar.collect(tx)
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://mojolicio.us/perldoc')
    jar.prepare(tx)
    is_ok(tx.req.cookie('foo').name, 'foo', 'right name')
    is_ok(tx.req.cookie('foo').value, 'without', 'right value')
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://mojolicio.us/perldoc')
    jar.prepare(tx)
    is_ok(tx.req.cookie('foo').name, 'foo', 'right name')
    is_ok(tx.req.cookie('foo').value, 'without', 'right value')
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://www.mojolicio.us/perldoc')
    jar.prepare(tx)
    none_ok(tx.req.cookie('foo'), 'no cookie')
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://mojolicio.us/whatever')
    jar.prepare(tx)
    none_ok(tx.req.cookie('foo'), 'no cookie')

    # Gather and prepare cookies with same name (with and without domain)
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
    throws_ok(lambda: cookies[1], IndexError, 'no second cookie')
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://www.example.com/test')
    jar.prepare(tx)
    cookies = tx.req.every_cookie('foo')
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'with', 'right value')
    throws_ok(lambda: cookies[1], IndexError, 'no second cookie')

    # Gather and prepare cookies for "localhost" (valid and invalid)
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
    none_ok(tx.req.cookie('bar'), 'no cookie')

    # Gather and prepare cookies with domain and path
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
    none_ok(tx.req.cookie('foo'), 'no cookie')
    is_ok(tx.req.cookie('bar').name, 'bar', 'right name')
    is_ok(tx.req.cookie('bar').value, 'with', 'right value')
    is_ok(tx.req.cookie('0').name, '0', 'right name')
    is_ok(tx.req.cookie('0').value, 'with', 'right value')
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://labs.bücher.COM/Perldoc')
    jar.prepare(tx)
    none_ok(tx.req.cookie('foo'), 'no cookie')
    is_ok(tx.req.cookie('bar').name, 'bar', 'right name')
    is_ok(tx.req.cookie('bar').value, 'with', 'right value')

    # Gather and prepare cookies with IP address
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

    # Gather cookies with invalid domain
    jar = Pyjo.UserAgent.CookieJar.new()
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://labs.example.com/perldoc/Mojolicious')
    tx.res.cookies(
        Pyjo.Cookie.Response.new(name='foo', value='invalid', domain='a.s.example.com'),
        Pyjo.Cookie.Response.new(name='foo', value='invalid', domain='mojolicio.us'),
    )
    jar.collect(tx)
    is_deeply_ok(jar.all, [], 'no cookies')

    # Gather cookies with invalid domain (IP address)
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
    is_deeply_ok(jar.all, [], 'no cookies')

    # Gather cookies with invalid path
    jar = Pyjo.UserAgent.CookieJar.new()
    tx = Pyjo.Transaction.HTTP.new()
    tx.req.url.parse('http://labs.example.com/perldoc/Mojolicious')
    tx.res.cookies(
        Pyjo.Cookie.Response.new(name='foo', value='invalid', path='/perldoc/index.html'),
        Pyjo.Cookie.Response.new(name='foo', value='invalid', path='/perldocMojolicious'),
        Pyjo.Cookie.Response.new(name='foo', value='invalid', path='/perldoc.Mojolicious'),
    )
    jar.collect(tx)
    is_deeply_ok(jar.all, [], 'no cookies')

    done_testing()
