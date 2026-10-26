from Pyjo.Test import *


def event(path='/foo'):
    return {
        'version': '2.0',
        'rawPath': path,
        'rawQueryString': '',
        'headers': {'host': 'example.com'},
        'requestContext': {'http': {'method': 'GET', 'sourceIp': '192.0.2.1'}, 'stage': '$default'},
        'isBase64Encoded': False,
    }


with subtest('Synopsis'):
    from Pyjo.Server.Lambda import Lambda

    server = Lambda()

    @server.unsubscribe('request').on('request')
    def request(server, tx):
        # Request
        method = tx.req.method
        path = tx.req.url.path

        # Response
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = f'{method} request for {path}!'.encode()

        # Resume transaction
        tx.resume()

    handler = server.to_lambda_app()

    response = handler(event(), None)
    is_ok(response['statusCode'], 200, 'status')
    is_ok(response['headers']['content-type'], 'text/plain', 'header')
    is_ok(response['body'], 'GET request for /foo!', 'body')
    is_ok(response['isBase64Encoded'], False, 'text')

    # Or import the module, as in Google Python Style Guide

    import Pyjo.Server.Lambda

    server = Pyjo.Server.Lambda.new()

    # F811 "Redefinition of unused `request`": the synopsis defines it in both forms
    @server.unsubscribe('request').on('request')
    def request(server, tx):  # noqa: F811
        # Request
        method = tx.req.method
        path = tx.req.url.path

        # Response
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = f'{method} request for {path}!'.encode()

        # Resume transaction
        tx.resume()

    handler = server.to_lambda_app()

    response = handler(event(), None)
    is_ok(response['statusCode'], 200, 'status')
    is_ok(response['headers']['content-type'], 'text/plain', 'header')
    is_ok(response['body'], 'GET request for /foo!', 'body')
    is_ok(response['isBase64Encoded'], False, 'text')

with subtest('Description'):
    import Pyjo.JSON
    import Pyjoyment

    app = Pyjoyment.new()
    app.log.level = 'fatal'
    app.routes.get('/foo', lambda c: c.render(text=f'{c.req.env["lambda.context"]}'))

    # The handler "myapp.handler" of an event function
    handler = Pyjo.Server.Lambda.new(app=app).to_lambda_app()
    is_ok(handler(event(), 'context')['body'], 'context', 'context')

    import os

    os.environ['PYJO_LAMBDA_INVOKE_MODE'] = 'RESPONSE_STREAM'
    try:
        # PYJO_LAMBDA_INVOKE_MODE=RESPONSE_STREAM in the environment of the function
        handler = Pyjo.Server.Lambda.new(app=app).to_lambda_app()
        response = handler(event(), 'context')
    finally:
        del os.environ['PYJO_LAMBDA_INVOKE_MODE']
    is_ok(response.content_type, 'application/vnd.awslambda.http-integration-response', 'content type')
    prelude, delimiter, body = b''.join(response).partition(b'\x00' * 8)
    response.close()
    is_ok(Pyjo.JSON.decode_json(prelude)['statusCode'], 200, 'status in the prelude')
    is_ok(body, b'context', 'body after 8 null bytes')


# What the runtime client of a command posts for an invocation of a Runtime API of the test, of an application of
# Pyjoyment as "myapp.handler"
def invoke(command, env=None):
    import Pyjo.File

    import importlib
    import sys

    sys.path.insert(0, Pyjo.File.curfile().dirname().sibling('lib').to_str())
    tmp = Pyjo.File.tempdir()
    tmp.child('myapp.py').spew(
        b'from Pyjoyment.Lite import app, get\n'
        b'import Pyjo.Server.Lambda\n\n'
        b"get('/', lambda c: c.render(text='Hello Lambda!'))\n"
        b"app.log.level = 'fatal'\n"
        b'handler = Pyjo.Server.Lambda.new(app=app).to_lambda_app()\n'
    )
    event = {'version': '2.0', 'rawPath': '/', 'requestContext': {'http': {'method': 'GET'}}}
    got, code = importlib.import_module('RuntimeAPI').invoke(command, [('a1', event)], 1, tmp.to_str(), env)
    return got[0][3] if got else None


with subtest('Runtime client'):
    from Pyjo.Util import extract_usage

    import contextlib
    import io
    import sys

    with contextlib.redirect_stderr(io.StringIO()):
        try:
            Pyjo.Server.Lambda.main(['-h'])
        except SystemExit as e:
            message = str(e)
    is_ok(message + '\n', extract_usage(Pyjo.Server.Lambda.__file__, section='Runtime client'), 'usage')

    response = invoke([sys.executable, '-m', 'Pyjo.Server.Lambda', 'myapp.handler'])
    is_ok(response['body'], 'Hello Lambda!', 'python -m Pyjo.Server.Lambda myapp.handler')

    # The bootstrap of a custom runtime, with the Python of the test
    if sys.platform == 'win32':
        skip('no shell of POSIX on Windows', 1)
    else:
        bootstrap = f'#!/bin/sh\n# The bootstrap of a custom runtime, as provided.al2023\nexec {sys.executable} -m Pyjo.Server.Lambda\n'
        response = invoke(['sh', '-c', bootstrap], {'_HANDLER': 'myapp.handler'})
        is_ok(response['body'], 'Hello Lambda!', 'bootstrap')

with subtest('new'):
    server = Pyjo.Server.Lambda.new()
    is_ok(server.invoke_mode, 'BUFFERED', 'server')
    server = Pyjo.Server.Lambda.new(invoke_mode='RESPONSE_STREAM')
    is_ok(server.invoke_mode, 'RESPONSE_STREAM', 'server.invoke_mode')

with subtest('invoke_mode'):
    mode = server.invoke_mode
    is_ok(mode, 'RESPONSE_STREAM', 'mode')
    server.invoke_mode = 'BUFFERED'
    is_ok(server.invoke_mode, 'BUFFERED', 'server.invoke_mode')

with subtest('run'):
    server = Pyjo.Server.Lambda.new(app=app)
    response = server.run(event(), 'context')
    is_ok(response['statusCode'], 200, 'response')

with subtest('to_lambda_app'):
    handler = server.to_lambda_app()
    ok(callable(handler), 'handler')

with subtest('main'):
    import sys

    response = invoke([sys.executable, '-c', "import Pyjo.Server.Lambda; Pyjo.Server.Lambda.main(['myapp.handler'])"])
    is_ok(response['statusCode'], 200, 'command line interface')

done_testing()
