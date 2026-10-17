import Pyjo.File

from Pyjo.Test import *

import contextlib
import io
import os
import re
import sys
import types


# Renamed from Mojolicious: PYJO_WSGI, as WSGI has no environment variable of its own, where Mojo has PLACK_ENV
os.environ.pop('PYJO_WSGI', None)
# Not in Mojolicious: PYJO_ASGI, as ASGI has no environment variable of its own
os.environ.pop('PYJO_ASGI', None)
# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# Renamed from Mojolicious: the modules of the tests are in tt/lib, where Mojo has them in t/mojolicious/lib
sys.path.insert(0, Pyjo.File.path(__file__).to_abs().dirname().dirname().dirname().child('tt', 'lib').to_str())


# Not in Mojolicious: local of the environment
@contextlib.contextmanager
def local(**env):
    saved = {name: os.environ.get(name) for name in env}
    for name, value in env.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
    try:
        yield
    finally:
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


# Not in Mojolicious: local *STDOUT, with the output as bytes, which get writes as Mojo prints them
@contextlib.contextmanager
def stdout():
    buffer = io.BytesIO()
    wrapper = io.TextIOWrapper(buffer, write_through=True)
    try:
        with contextlib.redirect_stdout(wrapper):
            yield buffer
    finally:
        wrapper.detach()


# Make sure @ARGV is not changed
with local(PYJO_MODE=None):
    argv = sys.argv
    try:
        sys.argv = [argv[0], '-m', 'production', '-x', 'whatever']
        import Pyjoyment.Commands

        is_ok(os.environ.get('PYJO_MODE'), 'production', 'right mode')
        is_deeply_ok(sys.argv[1:], ['-m', 'production', '-x', 'whatever'], 'unchanged')
    finally:
        sys.argv = argv

# Not in Mojolicious: the packages Mojolicious::Command::my_fake_test_command and my_test_command of the Perl test are
# modules in sys.modules, where the commands find them, after the check of sys.argv, as importing Pyjoyment.Command
# imports Pyjoyment.Commands
import Pyjoyment.Command  # noqa: E402
import Pyjoyment.Command.asgi  # noqa: E402
import Pyjoyment.Command.Author.generate  # noqa: E402
import Pyjoyment.Command.Author.generate.app  # noqa: E402
import Pyjoyment.Command.Author.generate.dockerfile  # noqa: E402
import Pyjoyment.Command.Author.generate.lite_app  # noqa: E402
import Pyjoyment.Command.Author.generate.plugin  # noqa: E402
import Pyjoyment.Command.Author.generate.pyproject  # noqa: E402
import Pyjoyment.Command.Author.inflate  # noqa: E402
import Pyjoyment.Command.cgi  # noqa: E402
import Pyjoyment.Command.daemon  # noqa: E402
import Pyjoyment.Command.eval  # noqa: E402
import Pyjoyment.Command.get  # noqa: E402
import Pyjoyment.Command.prefork  # noqa: E402
import Pyjoyment.Command.routes  # noqa: E402
import Pyjoyment.Command.version  # noqa: E402
import Pyjoyment.Command.wsgi  # noqa: E402

import PyjoymentTest  # noqa: E402  # pyright: ignore[reportMissingImports]


sys.modules['Pyjoyment.Command.my_fake_test_command'] = types.ModuleType('Pyjoyment.Command.my_fake_test_command')


class Pyjoyment_Command_my_test_command(Pyjoyment.Command.object):
    description = 'See, it works'


sys.modules['Pyjoyment.Command.my_test_command'] = types.ModuleType('Pyjoyment.Command.my_test_command')
sys.modules['Pyjoyment.Command.my_test_command'].object = Pyjoyment_Command_my_test_command

# Environment detection
commands = Pyjoyment.Commands.new()
with local(PYJO_WSGI='production'):
    is_ok(commands.detect(), 'wsgi', 'right environment')
# Not in Mojolicious: ASGI
with local(PYJO_ASGI='production'):
    is_ok(commands.detect(), 'asgi', 'right environment')
with local(PATH_INFO='/test'):
    is_ok(commands.detect(), 'cgi', 'right environment')
with local(GATEWAY_INTERFACE='CGI/1.1'):
    is_ok(commands.detect(), 'cgi', 'right environment')
with local(PYJO_WSGI=None, PYJO_ASGI=None, PATH_INFO=None, GATEWAY_INTERFACE=None):
    is_ok(commands.detect(), None, 'no environment')
with local(PYJO_WSGI='production'):
    ok(callable(Pyjoyment.Commands.new().run()), 'right reference')
    with local(PYJO_NO_DETECT='1'):
        ok(not callable(Pyjoyment.Commands.new().run()), 'not a CODE reference')

# Run command
ok(callable(Pyjoyment.Commands.new().run('wsgi')), 'right reference')
# Not in Mojolicious: ASGI
ok(callable(Pyjoyment.Commands.new().run('asgi')), 'right reference')

# Start application
with local(PYJO_APP_LOADER='1'):
    is_ok(type(Pyjoyment.Commands.start_app('PyjoymentTest')), PyjoymentTest.object, 'right class')

# Start application with command
ok(callable(Pyjoyment.Commands.start_app('PyjoymentTest', 'wsgi')), 'right reference')

# Start application with application specific commands
with local(PYJO_APP_LOADER='1'):
    app = Pyjoyment.Commands.start_app('PyjoymentTest')
is_ok(app.start('test_command'), 'works!', 'right result')
is_ok(app.start('test-command'), 'works!', 'right result')
is_ok(app.start('_test2-command'), 'works 2!', 'right result')
is_ok(Pyjoyment.Commands.start_app('PyjoymentTest', 'test_command'), 'works!', 'right result')
is_ok(Pyjoyment.Commands.start_app('PyjoymentTest', 'test-command'), 'works!', 'right result')
is_ok(Pyjoyment.Commands.start_app('PyjoymentTest', '_test2-command'), 'works 2!', 'right result')

# Application specific help
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer), local(PYJO_HARNESS_ACTIVE='0'):
    app.start()
like_ok(
    buffer.getvalue(), r'(?s)Usage: APPLICATION COMMAND \[OPTIONS\].*_test2-command.*cgi.*test-comm', 'right output'
)

with subtest('Commands starting with a dash are not allowed'), local(PYJO_HARNESS_ACTIVE='0'):
    throws_ok(lambda: app.start('-test2-command'), re.compile(r'Invalid command "-test2-command"\.'), 'not allowed')

# Do not pick up options for detected environments
with local(PYJO_MODE=None, PYJO_WSGI='testing'):
    argv = sys.argv
    try:
        sys.argv = [argv[0], 'wsgi', '-m', 'production']
        ok(callable(Pyjoyment.Commands.start_app('PyjoymentTest')), 'right reference')
        is_ok(os.environ.get('PYJO_MODE'), None, 'no mode')
    finally:
        sys.argv = argv

# mojo
is_deeply_ok(commands.namespaces, ['Pyjoyment.Command.Author', 'Pyjoyment.Command'], 'right namespaces')
ok(commands.description, 'has a description')
like_ok(commands.message, r'COMMAND', 'has a message')
like_ok(commands.hint, r'help', 'has a hint')
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer), local(PYJO_HARNESS_ACTIVE='0'):
    commands.run()
like_ok(
    buffer.getvalue(), r'(?s)Usage: APPLICATION COMMAND \[OPTIONS\].*daemon.*my-test-command.*version', 'right output'
)
like_ok(buffer.getvalue(), r'See, it works', 'description has been picked up')
unlike_ok(buffer.getvalue(), r'my-fake-test-command', 'fake command has been ignored')

# help
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    commands.run('help', 'generate', 'lite-app')
like_ok(buffer.getvalue(), r'Usage: APPLICATION generate lite-app \[OPTIONS\] \[NAME\]', 'right output')
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    commands.run('generate', 'help', 'lite-app')
like_ok(buffer.getvalue(), r'Usage: APPLICATION generate lite-app \[OPTIONS\] \[NAME\]', 'right output')
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    commands.run('generate', 'app', '-h')
like_ok(buffer.getvalue(), r'Usage: APPLICATION generate app \[OPTIONS\] \[NAME\]', 'right output')
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    commands.run('generate', 'lite-app', '--help')
like_ok(buffer.getvalue(), r'Usage: APPLICATION generate lite-app \[OPTIONS\] \[NAME\]', 'right output')
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer), local(PYJO_HARNESS_ACTIVE='0'):
    commands.run('help')
like_ok(buffer.getvalue(), r'Usage: APPLICATION COMMAND \[OPTIONS\]', 'right output')
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer), local(PYJO_HARNESS_ACTIVE='0'):
    commands.run('--help')
like_ok(buffer.getvalue(), r'Usage: APPLICATION COMMAND \[OPTIONS\]', 'right output')
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer), local(PYJO_HARNESS_ACTIVE='0'):
    commands.run('-h')
like_ok(buffer.getvalue(), r'Usage: APPLICATION COMMAND \[OPTIONS\]', 'right output')

# get
get = Pyjoyment.Command.get.new()
ok(get.description, 'has a description')
like_ok(get.usage, r'get', 'has usage information')
with stdout() as buffer:
    get.run('/')
like_ok(buffer.getvalue().decode(), r'Your Pyjoyment is working!', 'right output')
template = "<p></p><p><%= param('just') %> <%= c.req.headers.header('X-Test') %></p>"
get.app.plugins.once('before_dispatch', lambda c: c.render(inline=template))
with stdout() as buffer:
    get.run('-f', 'just=works', '-H', 'X-Test: fine', '/html', 'p', '1', 'text')
like_ok(buffer.getvalue().decode(), r'works fine', 'right output')
get.app.plugins.once('before_dispatch', lambda c: c.render(json={'works': 'too'}))
with stdout() as buffer:
    get.run('/json', '/works')
like_ok(buffer.getvalue().decode(), r'too', 'right output')
buffer = io.StringIO()
with contextlib.redirect_stderr(buffer):
    throws_ok(lambda: get.run('--unknown'), re.compile(r'Usage: APPLICATION get'), 'unknown option')
like_ok(buffer.getvalue(), r'Unknown option: unknown', 'right output')

# cgi
cgi = Pyjoyment.Command.cgi.new()
ok(cgi.description, 'has a description')
like_ok(cgi.usage, r'cgi', 'has usage information')
buffer = io.StringIO()
with contextlib.redirect_stderr(buffer):
    throws_ok(lambda: cgi.run('--unknown'), re.compile(r'Usage: APPLICATION cgi'), 'unknown option')
like_ok(buffer.getvalue(), r'Unknown option: unknown', 'right output')

# cpanify
# Left out from Mojolicious: the command cpanify, as uv publish uploads distributions to PyPI

with subtest('daemon'):
    with subtest('Description'):
        command = Pyjoyment.Command.daemon.new()
        ok(command.description, 'has a description')
        like_ok(command.usage, r'daemon', 'has usage information')

    with subtest('Unknown option'):
        command = Pyjoyment.Command.daemon.new()
        buffer = io.StringIO()
        with contextlib.redirect_stderr(buffer):
            throws_ok(lambda: command.run('--unknown'), re.compile(r'Usage: APPLICATION daemon'), 'unknown option')
        like_ok(buffer.getvalue(), r'Unknown option: unknown', 'right output')

    with subtest('Proxy boolean'):
        command = Pyjoyment.Command.daemon.new()
        daemon = command.build_server('-p')
        ok(daemon.reverse_proxy, 'right value')
        is_deeply_ok(daemon.trusted_proxies, [], 'right value')

    with subtest('Trusted proxies'):
        command = Pyjoyment.Command.daemon.new()
        daemon = command.build_server('-p', '127.0.0.0/8', '-p', '10.0.0.0/8')
        ok(daemon.reverse_proxy, 'right value')
        is_deeply_ok(daemon.trusted_proxies, ['127.0.0.0/8', '10.0.0.0/8'], 'right value')

    with subtest('Trusted proxies from environment'), local(PYJO_TRUSTED_PROXIES='127.0.0.0/8,10.0.0.0/8'):
        command = Pyjoyment.Command.daemon.new()
        daemon = command.build_server()
        ok(daemon.reverse_proxy, 'right value')
        is_deeply_ok(daemon.trusted_proxies, ['127.0.0.0/8', '10.0.0.0/8'], 'right value')

    with subtest('Proxy boolean and trusted'):
        command = Pyjoyment.Command.daemon.new()
        daemon = command.build_server('-p', '-p', '127.0.0.0/8', '-p', '10.0.0.0/8')
        ok(daemon.reverse_proxy, 'right value')
        is_deeply_ok(daemon.trusted_proxies, ['127.0.0.0/8', '10.0.0.0/8'], 'right value')

# eval
eval_ = Pyjoyment.Command.eval.new()
ok(eval_.description, 'has a description')
like_ok(eval_.usage, r'eval', 'has usage information')
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    eval_.run('-v', 'app.controller_class')
like_ok(buffer.getvalue(), r'Pyjoyment\.Controller', 'right output')
throws_ok(lambda: eval_.run('-v', "raise Exception('TEST')"), re.compile(r'TEST'), 'right output')
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    eval_.run('-v', "import Pyjo.Promise; Pyjo.Promise.new().resolve('Zoidberg')")
like_ok(buffer.getvalue(), r'Zoidberg', 'right output')
throws_ok(
    lambda: eval_.run('-v', "import Pyjo.Promise; Pyjo.Promise.new().reject('DOOM')"),
    re.compile(r'DOOM'),
    'right output',
)
buffer = io.StringIO()
with contextlib.redirect_stderr(buffer):
    throws_ok(lambda: eval_.run('--unknown'), re.compile(r'Usage: APPLICATION eval'), 'unknown option')
like_ok(buffer.getvalue(), r'Unknown option: unknown', 'right output')

# generate
generator = Pyjoyment.Command.Author.generate.new()
is_deeply_ok(generator.namespaces, ['Pyjoyment.Command.Author.generate'], 'right namespaces')
ok(generator.description, 'has a description')
like_ok(generator.message, r'generate', 'has a message')
like_ok(generator.hint, r'help', 'has a hint')
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer), local(PYJO_HARNESS_ACTIVE='0'):
    generator.run()
like_ok(buffer.getvalue(), r'(?s)Usage: APPLICATION generate GENERATOR \[OPTIONS\].*lite-app.*plugin', 'right output')

# generate app
app = Pyjoyment.Command.Author.generate.app.new()
ok(app.description, 'has a description')
like_ok(app.usage, r'app', 'has usage information')
cwd = Pyjo.File.path()
dir = Pyjo.File.tempdir()
os.chdir(dir)
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    app.run()
like_ok(buffer.getvalue(), r'my_app', 'right output')
# Renamed from Mojolicious: the __main__ module of the package, where Mojo has script/my_app
ok(os.path.exists(app.rel_file('my_app/MyApp/__main__.py').to_str()), 'script exists')
# Unlike Mojolicious: the package in the directory of the project, where Mojo has lib/MyApp.pm
ok(os.path.exists(app.rel_file('my_app/MyApp/__init__.py').to_str()), 'application class exists')
ok(os.path.exists(app.rel_file('my_app/MyApp/Controller/Example.py').to_str()), 'controller exists')
ok(os.path.exists(app.rel_file('my_app/my_app.yml').to_str()), 'config file exists')
# Renamed from Mojolicious: t/basic.py, where Mojo has t/basic.t
ok(os.path.exists(app.rel_file('my_app/t/basic.py').to_str()), 'test exists')
# Not in Mojolicious: pyproject.toml of the application
ok(os.path.exists(app.rel_file('my_app/pyproject.toml').to_str()), 'pyproject.toml exists')
ok(os.path.isdir(app.rel_file('my_app/public/assets').to_str()), 'assets directory exists')
ok(os.path.exists(app.rel_file('my_app/public/index.html').to_str()), 'static file exists')
ok(os.path.exists(app.rel_file('my_app/templates/layouts/default.html.ep').to_str()), 'layout exists')
ok(os.path.exists(app.rel_file('my_app/templates/example/welcome.html.ep').to_str()), 'template exists')
os.chdir(cwd)

with subtest('generate dockerfile'):
    dockerfile = Pyjoyment.Command.Author.generate.dockerfile.new()
    ok(dockerfile.description, 'has a description')
    like_ok(dockerfile.usage, r'dockerfile', 'has usage information')
    dir = Pyjo.File.tempdir()
    os.chdir(dir)
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        dockerfile.run()
    like_ok(buffer.getvalue(), r'Dockerfile', 'right output')
    ok(os.path.exists(app.rel_file('Dockerfile').to_str()), 'Dockerfile exists')
    # Not in Mojolicious: .dockerignore and the user
    ok(os.path.exists(app.rel_file('.dockerignore').to_str()), '.dockerignore exists')
    unlike_ok(app.rel_file('Dockerfile').slurp().decode(), r'USER', 'no user')
    app.rel_file('Dockerfile').remove()
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        dockerfile.run('-u', 'app')
    like_ok(app.rel_file('Dockerfile').slurp().decode(), r'(?m)^USER app$', 'right user')
    buffer = io.StringIO()
    with contextlib.redirect_stderr(buffer):
        throws_ok(
            lambda: dockerfile.run('--unknown'), re.compile(r'Usage: APPLICATION generate dockerfile'), 'unknown option'
        )
    like_ok(buffer.getvalue(), r'Unknown option: unknown', 'right output')
    os.chdir(cwd)

# generate lite_app
app = Pyjoyment.Command.Author.generate.lite_app.new()
ok(app.description, 'has a description')
like_ok(app.usage, r'lite-app', 'has usage information')
dir = Pyjo.File.tempdir()
os.chdir(dir)
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    app.run()
like_ok(buffer.getvalue(), r'myapp\.py', 'right output')
ok(os.path.exists(app.rel_file('myapp.py').to_str()), 'app exists')
os.chdir(cwd)

# generate makefile
# Renamed from Mojolicious: generate pyproject, where Mojo has generate makefile
pyproject = Pyjoyment.Command.Author.generate.pyproject.new()
ok(pyproject.description, 'has a description')
like_ok(pyproject.usage, r'pyproject', 'has usage information')
dir = Pyjo.File.tempdir()
os.chdir(dir)
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    pyproject.run()
like_ok(buffer.getvalue(), r'pyproject\.toml', 'right output')
ok(os.path.exists(app.rel_file('pyproject.toml').to_str()), 'pyproject.toml exists')
os.chdir(cwd)

# generate plugin
plugin = Pyjoyment.Command.Author.generate.plugin.new()
ok(plugin.description, 'has a description')
like_ok(plugin.usage, r'plugin', 'has usage information')
dir = Pyjo.File.tempdir()
os.chdir(dir)
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    plugin.run()
like_ok(buffer.getvalue(), r'MyPlugin\.py', 'right output')
ok(os.path.exists(app.rel_file('Pyjoyment-Plugin-MyPlugin/Pyjoyment/Plugin/MyPlugin.py').to_str()), 'class exists')
ok(os.path.exists(app.rel_file('Pyjoyment-Plugin-MyPlugin/t/basic.py').to_str()), 'test exists')
ok(os.path.exists(app.rel_file('Pyjoyment-Plugin-MyPlugin/pyproject.toml').to_str()), 'pyproject.toml exists')
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    plugin.run('-f', 'MyApp.Ext.Test')
like_ok(buffer.getvalue(), r'Test\.py', 'right output')
ok(os.path.exists(app.rel_file('MyApp-Ext-Test/MyApp/Ext/Test.py').to_str()), 'class exists')
ok(os.path.exists(app.rel_file('MyApp-Ext-Test/t/basic.py').to_str()), 'test exists')
ok(os.path.exists(app.rel_file('MyApp-Ext-Test/pyproject.toml').to_str()), 'pyproject.toml exists')
buffer = io.StringIO()
with contextlib.redirect_stderr(buffer):
    throws_ok(lambda: plugin.run('--unknown'), re.compile(r'Usage: APPLICATION generate plugin'), 'unknown option')
like_ok(buffer.getvalue(), r'Unknown option: unknown', 'right output')
os.chdir(cwd)

# inflate
inflate = Pyjoyment.Command.Author.inflate.new()
ok(inflate.description, 'has a description')
like_ok(inflate.usage, r'inflate', 'has usage information')

with subtest('prefork'):
    with subtest('Description'):
        command = Pyjoyment.Command.prefork.new()
        ok(command.description, 'has a description')
        like_ok(command.usage, r'prefork', 'has usage information')

    with subtest('Unknown option'):
        command = Pyjoyment.Command.prefork.new()
        buffer = io.StringIO()
        with contextlib.redirect_stderr(buffer):
            throws_ok(lambda: command.run('--unknown'), re.compile(r'Usage: APPLICATION prefork'), 'unknown option')
        like_ok(buffer.getvalue(), r'Unknown option: unknown', 'right output')

    with subtest('Proxy boolean'):
        command = Pyjoyment.Command.prefork.new()
        prefork = command.build_server('-p')
        ok(prefork.reverse_proxy, 'right value')
        is_deeply_ok(prefork.trusted_proxies, [], 'right value')

    with subtest('Trusted proxies'):
        command = Pyjoyment.Command.prefork.new()
        prefork = command.build_server('-p', '127.0.0.0/8', '-p', '10.0.0.0/8')
        ok(prefork.reverse_proxy, 'right value')
        is_deeply_ok(prefork.trusted_proxies, ['127.0.0.0/8', '10.0.0.0/8'], 'right value')

    with subtest('Trusted proxies from environment'), local(PYJO_TRUSTED_PROXIES='127.0.0.0/8,10.0.0.0/8'):
        command = Pyjoyment.Command.prefork.new()
        prefork = command.build_server()
        ok(prefork.reverse_proxy, 'right value')
        is_deeply_ok(prefork.trusted_proxies, ['127.0.0.0/8', '10.0.0.0/8'], 'right value')

    with subtest('Proxy boolean and trusted'):
        command = Pyjoyment.Command.prefork.new()
        prefork = command.build_server('-p', '-p', '127.0.0.0/8', '-p', '10.0.0.0/8')
        ok(prefork.reverse_proxy, 'right value')
        is_deeply_ok(prefork.trusted_proxies, ['127.0.0.0/8', '10.0.0.0/8'], 'right value')

# psgi
# Renamed from Mojolicious: wsgi, where Mojo has psgi
wsgi = Pyjoyment.Command.wsgi.new()
ok(wsgi.description, 'has a description')
like_ok(wsgi.usage, r'wsgi', 'has usage information')
# Not in Mojolicious: ASGI
asgi = Pyjoyment.Command.asgi.new()
ok(asgi.description, 'has a description')
like_ok(asgi.usage, r'asgi', 'has usage information')

# routes
routes = Pyjoyment.Command.routes.new()
ok(routes.description, 'has a description')
like_ok(routes.usage, r'routes', 'has usage information')
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    routes.run()
like_ok(buffer.getvalue(), r'/\*whatever', 'right output')
unlike_ok(buffer.getvalue(), r'/\(\.\+\)\?', 'not verbose')
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    routes.run('-v')
like_ok(buffer.getvalue(), r'/\*whatever', 'right output')
like_ok(buffer.getvalue(), r'/\(\.\+\)\?', 'verbose')
buffer = io.StringIO()
with contextlib.redirect_stderr(buffer):
    throws_ok(lambda: routes.run('--unknown'), re.compile(r'Usage: APPLICATION routes'), 'unknown option')
like_ok(buffer.getvalue(), r'Unknown option: unknown', 'right output')

# version
version = Pyjoyment.Command.version.new()
ok(version.description, 'has a description')
like_ok(version.usage, r'version', 'has usage information')
version.app.ua.server.app = version.app


@version.app.ua.once('start')
def start(ua, tx):
    tx.req.via_proxy = False
    tx.req.url = ua.server.url().set(path='/')


# Unlike Mojolicious: the JSON API of PyPI, where Mojo asks MetaCPAN for the version
version.app.plugins.once('before_dispatch', lambda c: c.render(json={'info': {'version': 1000}}))
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    version.run()
# Renamed from Mojolicious: Python, where Mojo shows Perl
like_ok(buffer.getvalue(), r'Python', 'right output')
like_ok(buffer.getvalue(), r'You might want to update your Pyjoyment to 1000!', 'right output')

# Hooks
app = Pyjoyment.new()


@app.hook('before_command')
def before_command(command, args):
    if not isinstance(command, Pyjoyment.Command.eval.object):
        return
    command.app.config()['test'] = 'works!'
    args.insert(0, '-v')


buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    app.start('eval', "app.config()['test']")
like_ok(buffer.getvalue(), r'works!', 'right output')

done_testing()
