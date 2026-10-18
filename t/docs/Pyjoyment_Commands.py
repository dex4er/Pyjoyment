import Pyjo.Server
import Pyjoyment
import Pyjoyment.Commands

from Pyjo.Test import *

import contextlib
import io
import os


with subtest('Synopsis'):
    usage = Pyjoyment.Commands.new().extract_usage()
    like_ok(Pyjoyment.Commands.new().message, r'^Usage: APPLICATION COMMAND \[OPTIONS\]\n', 'usage')
    like_ok(Pyjoyment.Commands.new().message, r'Options \(for all commands\):', 'options')
    is_ok(usage, '', 'no synopsis in this file')

with subtest('Description'):
    import Pyjoyment.Commands as module

    buffer = io.StringIO()
    os.environ['PYJO_HARNESS_ACTIVE'] = '0'
    try:
        with contextlib.redirect_stdout(buffer):
            module.main([])
    finally:
        os.environ['PYJO_HARNESS_ACTIVE'] = '1'
    like_ok(buffer.getvalue(), r'(?s)Commands:\n.* daemon .* version ', 'pyjo')

with subtest('Commands'):
    app = Pyjoyment.new()
    app.routes.get('/foo').set(name='foo')
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        app.start('routes')
    like_ok(buffer.getvalue(), r'/foo', 'routes')
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        app.start('eval', 'print(app.home)')
    like_ok(buffer.getvalue(), r'\S', 'eval')
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        app.start('help', 'daemon')
    like_ok(buffer.getvalue(), r'^Usage: APPLICATION daemon \[OPTIONS\]', 'help')

with subtest('Attributes'):
    commands = Pyjoyment.Commands.new()
    like_ok(commands.hint, r"See 'APPLICATION help COMMAND'", 'hint')
    commands.hint = 'Foo'
    is_ok(commands.hint, 'Foo', 'hint changed')
    commands.message = 'Hello World!'
    is_ok(commands.message, 'Hello World!', 'message')
    is_deeply_ok(commands.namespaces, ['Pyjoyment.Command.Author', 'Pyjoyment.Command'], 'namespaces')

    # Add another namespace to load commands from
    commands.namespaces.append('MyApp.Command')
    is_ok(commands.namespaces[-1], 'MyApp.Command', 'namespace added')

with subtest('detect'):
    commands = Pyjoyment.Commands.new()
    is_ok(commands.detect(), None, 'no environment')
    os.environ['GATEWAY_INTERFACE'] = 'CGI/1.1'
    try:
        is_ok(commands.detect(), 'cgi', 'CGI')
    finally:
        del os.environ['GATEWAY_INTERFACE']
    for name in ('wsgi', 'asgi'):
        os.environ[f'PYJO_{name.upper()}'] = '1'
        try:
            is_ok(commands.detect(), name, name.upper())
        finally:
            del os.environ[f'PYJO_{name.upper()}']
    os.environ['AWS_LAMBDA_RUNTIME_API'] = '127.0.0.1:9001'
    try:
        is_ok(commands.detect(), 'lambda', 'AWS Lambda')
    finally:
        del os.environ['AWS_LAMBDA_RUNTIME_API']

with subtest('run'):
    commands = Pyjoyment.Commands.new()
    is_ok(commands.run(), True, 'list hidden from the tests')

    # The WSGI application of a script, for PYJO_WSGI=1 gunicorn myapp:application
    os.environ['PYJO_WSGI'] = '1'
    try:
        application = Pyjoyment.new().start()
    finally:
        del os.environ['PYJO_WSGI']
    ok(callable(application), 'WSGI application')

with subtest('start_app'):
    os.environ['PYJO_APP_LOADER'] = '1'
    try:
        app = Pyjoyment.Commands.start_app('Pyjoyment.HelloWorld')
    finally:
        del os.environ['PYJO_APP_LOADER']
    is_ok(Pyjo.Server.loaded_app, app, 'application')
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        Pyjoyment.Commands.start_app('Pyjoyment.HelloWorld', 'routes')
    like_ok(buffer.getvalue(), r'/\*whatever', 'command')

done_testing()
