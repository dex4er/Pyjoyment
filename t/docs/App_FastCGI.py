import Pyjo.Server.Daemon
import Pyjo.Test.Pyjo
import Pyjoyment

from Pyjo.Test import *


# The FastCGI server of Pyjo, which answers the requests of the examples
inner = Pyjoyment.new()
inner.log.level = 'fatal'
inner.routes.get('/').to(cb=lambda c: c.render(text='Hello FastCGI!'))
daemon = Pyjo.Server.Daemon.new(app=inner, listen=['fcgi://127.0.0.1'], silent=True).start()
url = f'fcgi://127.0.0.1:{daemon.ports()[0]}'

with subtest('Synopsis'):
    from Pyjo.App.FastCGI import FastCGI

    app = FastCGI(url='fcgi://127.0.0.1:9000')
    is_ok(app.url, 'fcgi://127.0.0.1:9000', 'location')

    # Or import the module, as in Google Python Style Guide

    import Pyjo.App.FastCGI

    app = Pyjo.App.FastCGI.new(url='fcgi://127.0.0.1:9000')
    is_ok(app.url, 'fcgi://127.0.0.1:9000', 'location')

    # PHP on php-fpm, on a UNIX domain socket, with its script
    app = Pyjo.App.FastCGI.new(
        url='fcgi+unix://%2Frun%2Fphp%2Ffpm.sock',
        env={'SCRIPT_FILENAME': '/var/www/index.php', 'DOCUMENT_ROOT': '/var/www'},
    )
    is_ok(app.env['SCRIPT_FILENAME'], '/var/www/index.php', 'parameter')

    # Mount it in an application of Pyjoyment
    import Pyjoyment

    pyjoyment = Pyjoyment.new()
    pyjoyment.log.level = 'fatal'
    pyjoyment.plugin('Mount', {'/php': app})
    pyjoyment.plugin('Mount', {'/fcgi': url})
    Pyjo.Test.Pyjo.new(pyjoyment).get_ok('/fcgi').status_is(200).content_is('Hello FastCGI!')

with subtest('document_root'):
    app = Pyjo.App.FastCGI.new()
    root = app.document_root
    is_ok(root, None, 'no directory')
    app.document_root = '/var/www'
    is_ok(app.document_root, '/var/www', 'directory')

with subtest('env'):
    app = Pyjo.App.FastCGI.new()
    env = app.env
    is_deeply_ok(env, {}, 'no parameters')
    app.env = {'SCRIPT_FILENAME': '/var/www/index.php'}
    is_deeply_ok(app.env, {'SCRIPT_FILENAME': '/var/www/index.php'}, 'parameters')

with subtest('inactivity_timeout'):
    app = Pyjo.App.FastCGI.new()
    timeout = app.inactivity_timeout
    is_ok(timeout, 60, 'default')
    app.inactivity_timeout = 300
    is_ok(app.inactivity_timeout, 300, 'timeout')

with subtest('url'):
    app = Pyjo.App.FastCGI.new()
    url_ = app.url
    is_ok(url_, None, 'no location')
    app.url = 'fcgi://127.0.0.1:9000'
    is_ok(app.url, 'fcgi://127.0.0.1:9000', 'TCP/IP')
    app.url = 'fcgi+unix://%2Frun%2Fphp%2Ffpm.sock'
    is_ok(app.url, 'fcgi+unix://%2Frun%2Fphp%2Ffpm.sock', 'UNIX domain socket')

with subtest('new'):
    app = Pyjo.App.FastCGI.new(url='fcgi://127.0.0.1:9000')
    is_ok(app.url, 'fcgi://127.0.0.1:9000', 'location')

with subtest('handler'):
    with Pyjo.App.FastCGI.new(url=url) as app:
        Pyjo.Test.Pyjo.new(app).get_ok('/').status_is(200).content_is('Hello FastCGI!')

daemon.close()

done_testing()
