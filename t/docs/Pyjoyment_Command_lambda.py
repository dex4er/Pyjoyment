import Pyjo.File
import Pyjoyment

from Pyjo.Test import *

import importlib
import os
import sys


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

# The script of an application, "myapp.handler", and the Runtime API of the test
TMP = Pyjo.File.tempdir()
TMP.child('myapp.py').spew(
    b'from Pyjoyment.Lite import app, get\n\n'
    b"get('/', {'text': 'Hello Lambda!'})\n"
    b"app.log.level = 'fatal'\n"
    b"handler = app.start('daemon', '--whatever')\n"
)
sys.path.insert(0, Pyjo.File.curfile().dirname().sibling('lib').to_str())
RuntimeAPI = importlib.import_module('RuntimeAPI')

with subtest('Description'):
    # A runtime that imports the script, whatever the arguments are
    os.environ['AWS_LAMBDA_RUNTIME_API'] = '127.0.0.1:9001'
    sys.path.insert(0, TMP.to_str())
    try:
        myapp = importlib.import_module('myapp')
        ok(callable(myapp.handler), 'detected, whatever the arguments are')
        is_ok(myapp.handler(event, None)['body'], 'Hello Lambda!', 'handler')
    finally:
        del os.environ['AWS_LAMBDA_RUNTIME_API']
        sys.path.remove(TMP.to_str())
        del sys.modules['myapp']

    # The bootstrap of a custom runtime, with the Python of the test
    if sys.platform == 'win32':
        skip('no shell of POSIX on Windows', 2)
    else:
        bootstrap = f'#!/bin/sh\n# The bootstrap of a custom runtime, as provided.al2023\nexec {sys.executable} "$LAMBDA_TASK_ROOT/myapp.py"\n'
        env = {'LAMBDA_TASK_ROOT': TMP.to_str()}
        got, code = RuntimeAPI.invoke(['sh', '-c', bootstrap], [('a1', event), ('a2', event)], 2, TMP.to_str(), env)
        is_ok([kind for kind, *_ in got], ['response', 'response'], 'the script is the runtime')
        is_ok(got[1][3]['body'], 'Hello Lambda!', 'body')

with subtest('Attributes'):
    is_ok(command.new().description, 'Start application with AWS Lambda', 'description')

with subtest('run'):
    ok(callable(command.new(app=app).run()), 'handler')

done_testing()
