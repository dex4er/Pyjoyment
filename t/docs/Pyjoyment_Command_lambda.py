import Pyjoyment

from Pyjo.Test import *

import importlib
import os


# The module has the name of a keyword of Python
command = importlib.import_module('Pyjoyment.Command.lambda')

event = {
    'version': '2.0',
    'rawPath': '/',
    'rawQueryString': '',
    'headers': {'host': 'example.com'},
    'requestContext': {'http': {'method': 'GET'}, 'stage': '$default'},
    'isBase64Encoded': False,
}

with subtest('Synopsis'):
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    app.routes.get('/', {'text': 'Hello Lambda!'})
    like_ok(
        command.new(app=app).usage,
        r"^Usage: APPLICATION lambda \[OPTIONS\]\n\n  handler = app\.start\('lambda'\)\n",
        'usage',
    )

    handler = app.start('lambda')
    response = handler(event, None)
    is_ok(response['statusCode'], 200, 'status')
    is_ok(response['body'], 'Hello Lambda!', 'body')

with subtest('Description'):
    app = Pyjoyment.new()
    os.environ['AWS_LAMBDA_RUNTIME_API'] = '127.0.0.1:9001'
    try:
        ok(callable(app.start('daemon', '--whatever')), 'detected, whatever the arguments are')
    finally:
        del os.environ['AWS_LAMBDA_RUNTIME_API']

with subtest('Attributes'):
    is_ok(command.new().description, 'Start application with AWS Lambda', 'description')

with subtest('run'):
    ok(callable(command.new(app=app).run()), 'handler')

done_testing()
