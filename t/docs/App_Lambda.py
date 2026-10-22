import Pyjo.File
import Pyjo.Test.Pyjo

from Pyjo.Test import *

import os


# A function of the examples, in its directory, which answers with its path
TMP = Pyjo.File.tempdir()
TMP.child('myfunction.py').spew(
    b"def handler(event, context):\n    return {'statusCode': 200, 'body': f'Hello Lambda at {event[\"rawPath\"]}!'}\n"
)

with subtest('Synopsis'):
    from Pyjo.App.Lambda import Lambda

    app = Lambda(function='myfunction.handler')
    is_ok(app.function, 'myfunction.handler', 'function')

    # Or import the module, as in Google Python Style Guide

    import Pyjo.App.Lambda

    app = Pyjo.App.Lambda.new(function='myfunction.handler')
    is_ok(app.function, 'myfunction.handler', 'function')

    # Another runtime, with the events of a REST API
    app = Pyjo.App.Lambda.new(command=['node', 'runtime.js'], payload='1.0')
    is_deeply_ok(app.command, ['node', 'runtime.js'], 'command')
    is_ok(app.payload, '1.0', 'payload format')

    # Mount it in an application of Pyjoyment
    import Pyjoyment

    pyjoyment = Pyjoyment.new()
    pyjoyment.log.level = 'fatal'

    # The function of the test, where the event loop watches pipes
    if os.name == 'nt':
        skip('Lambda functions need pipes that the event loop watches', 2)
    else:
        app = Pyjo.App.Lambda.new(function='myfunction.handler', task_root=TMP.to_str())
        pyjoyment.plugin('Mount', {'/function': app})
        Pyjo.Test.Pyjo.new(pyjoyment).get_ok('/function/foo').status_is(200).content_is(
            'Hello Lambda at /function/foo!'
        )
        app.close()

with subtest('command'):
    app = Pyjo.App.Lambda.new()
    command = app.command
    is_ok(command, None, 'the runtime client of Pyjo.Server.Lambda')
    app.command = ['python', '-m', 'awslambdaric', 'myfunction.handler']
    is_deeply_ok(app.command, ['python', '-m', 'awslambdaric', 'myfunction.handler'], 'command')
    app.command = ['./bootstrap']
    is_deeply_ok(app.command, ['./bootstrap'], 'bootstrap')

with subtest('env'):
    app = Pyjo.App.Lambda.new()
    env = app.env
    is_deeply_ok(env, {}, 'no variables')
    app.env = {'TABLE_NAME': 'users'}
    is_deeply_ok(app.env, {'TABLE_NAME': 'users'}, 'variables')

with subtest('function'):
    app = Pyjo.App.Lambda.new()
    handler = app.function
    is_ok(handler, None, 'no handler')
    app.function = 'myfunction.handler'
    is_ok(app.function, 'myfunction.handler', 'handler')

with subtest('function_name'):
    app = Pyjo.App.Lambda.new()
    name = app.function_name
    is_ok(name, 'pyjo', 'default')
    app.function_name = 'myfunction'
    is_ok(app.function_name, 'myfunction', 'name')

with subtest('memory_size'):
    app = Pyjo.App.Lambda.new()
    size = app.memory_size
    is_ok(size, 128, 'default')
    app.memory_size = 512
    is_ok(app.memory_size, 512, 'memory')

with subtest('multi_value_headers'):
    app = Pyjo.App.Lambda.new()
    boolean = app.multi_value_headers
    is_ok(boolean, False, 'default')
    app.multi_value_headers = True
    is_ok(app.multi_value_headers, True, 'headers of multiple values')

with subtest('payload'):
    app = Pyjo.App.Lambda.new()
    payload = app.payload
    is_ok(payload, '2.0', 'default')
    app.payload = '1.0'
    is_ok(app.payload, '1.0', 'REST API')
    app.payload = 'alb'
    is_ok(app.payload, 'alb', 'Application Load Balancer')

with subtest('task_root'):
    app = Pyjo.App.Lambda.new()
    root = app.task_root
    is_ok(root, None, 'the current directory')
    app.task_root = '/var/task'
    is_ok(app.task_root, '/var/task', 'directory')

with subtest('timeout'):
    app = Pyjo.App.Lambda.new()
    timeout = app.timeout
    is_ok(timeout, 30, 'default')
    app.timeout = 3
    is_ok(app.timeout, 3, 'timeout')

with subtest('new'):
    app = Pyjo.App.Lambda.new(function='myfunction.handler')
    is_ok(app.function, 'myfunction.handler', 'function')

with subtest('close'):
    if os.name == 'nt':
        skip('Lambda functions need pipes that the event loop watches', 2)
    else:
        app = Pyjo.App.Lambda.new(function='myfunction.handler', task_root=TMP.to_str())
        Pyjo.Test.Pyjo.new(app).get_ok('/').status_is(200)
        app.close()
        is_ok(len(app._environments), 0, 'process ended')

with subtest('handler'):
    if os.name == 'nt':
        skip('Lambda functions need pipes that the event loop watches', 1)
    else:
        with Pyjo.App.Lambda.new(function='myfunction.handler', task_root=TMP.to_str()) as app:
            Pyjo.Test.Pyjo.new(app).get_ok('/').status_is(200).content_is('Hello Lambda at /!')

done_testing()
