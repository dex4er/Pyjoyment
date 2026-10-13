if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    from Pyjo.Util import setenv

    import Pyjo.UserAgent.Proxy

    # Proxy detection
    proxy = Pyjo.UserAgent.Proxy.new()

    setenv('HTTP_PROXY', 'http://127.0.0.1')
    setenv('HTTPS_PROXY', 'http://127.0.0.1:8080')
    setenv('NO_PROXY', 'mojolicio.us')

    proxy.detect()
    is_ok(proxy.http, 'http://127.0.0.1', 'right proxy')
    is_ok(proxy.https, 'http://127.0.0.1:8080', 'right proxy')
    proxy.http = None
    proxy.https = None
    none_ok(proxy.http, 'right proxy')
    none_ok(proxy.https, 'right proxy')
    ok(not proxy.is_needed('dummy.mojolicio.us'), 'no proxy needed')
    ok(proxy.is_needed('icio.us'), 'proxy needed')
    ok(proxy.is_needed('localhost'), 'proxy needed')

    setenv('HTTP_PROXY', None)
    setenv('HTTPS_PROXY', None)
    setenv('NO_PROXY', None)

    setenv('http_proxy', 'proxy.example.com')
    setenv('https_proxy', 'tunnel.example.com')
    setenv('no_proxy', 'localhost,localdomain,foo.com,example.com')

    proxy.detect()
    is_deeply_ok(proxy.no, ['localhost', 'localdomain', 'foo.com', 'example.com'], 'right list')
    is_ok(proxy.http, 'proxy.example.com', 'right proxy')
    is_ok(proxy.https, 'tunnel.example.com', 'right proxy')
    ok(proxy.is_needed('dummy.mojolicio.us'), 'proxy needed')
    ok(proxy.is_needed('icio.us'), 'proxy needed')
    ok(not proxy.is_needed('localhost'), 'proxy needed')
    ok(not proxy.is_needed('localhost.localdomain'), 'no proxy needed')
    ok(not proxy.is_needed('foo.com'), 'no proxy needed')
    ok(not proxy.is_needed('example.com'), 'no proxy needed')
    ok(not proxy.is_needed('www.example.com'), 'no proxy needed')
    ok(proxy.is_needed('www.example.com.com'), 'proxy needed')

    setenv('http_proxy', None)
    setenv('https_proxy', None)
    setenv('no_proxy', None)

    done_testing()
