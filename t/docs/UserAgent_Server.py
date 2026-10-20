from Pyjo.Test import *


with subtest('Synopsis'):
    import Pyjo.UserAgent.Server

    server = Pyjo.UserAgent.Server.new()
    like_ok(str(server.url()), r'^http://127\.0\.0\.1:\d+/$', 'print(server.url())')

with subtest('new'):
    import Pyjo.IOLoop

    server = Pyjo.UserAgent.Server.new()
    is_ok(server.ioloop, Pyjo.IOLoop.singleton, 'server')
    loop = Pyjo.IOLoop.new()
    server = Pyjo.UserAgent.Server.new(ioloop=loop)
    is_ok(server.ioloop, loop, 'server.ioloop')

with subtest('ioloop'):
    loop = server.ioloop
    server.ioloop = Pyjo.IOLoop.new()
    ok(server.ioloop is not loop, 'server.ioloop')

with subtest('app'):
    import Pyjo.HelloWorld

    app = server.app
    is_ok(app, None, 'app')
    server.app = Pyjo.HelloWorld.new()
    ok(isinstance(server.app, Pyjo.HelloWorld.object), 'server.app')

with subtest('close'):
    import Pyjo.UserAgent.Server

    server = Pyjo.UserAgent.Server.new()
    before = server.url().port
    server.close()
    isnt_ok(server.url().port, before, 'started again on a new port')
    server.close()


with subtest('nb_url'):
    url = server.nb_url()
    is_ok(url.protocol, 'http', 'url')
    url = server.nb_url('http')
    is_ok(url.protocol, 'http', 'url')

with subtest('restart'):
    port = server.url().port
    server.restart()
    ok(server.url().port, 'new server')

with subtest('url'):
    url = server.url()
    is_ok(url.host, '127.0.0.1', 'url')
    url = server.url('http')
    is_ok(url.protocol, 'http', 'url')

with subtest('app of the module'):
    app = Pyjo.UserAgent.Server.app()
    is_ok(app, None, 'app')
    hello = Pyjo.HelloWorld.new()
    Pyjo.UserAgent.Server.app(hello)
    is_ok(Pyjo.UserAgent.Server.app(), hello, 'global default')

    # Change application behavior
    Pyjo.UserAgent.Server.app().log.level = 'fatal'
    is_ok(hello.log.level, 'fatal', 'changed')

done_testing()
