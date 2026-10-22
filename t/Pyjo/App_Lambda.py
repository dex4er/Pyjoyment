import Pyjo.App.Lambda
import Pyjo.File
import Pyjo.IOLoop
import Pyjo.Test.Pyjo
import Pyjo.Transaction.HTTP
import Pyjoyment

from Pyjo.Test import *

import base64
import os
import re
import sys


if os.name == 'nt':
    plan(skip_all='Lambda functions run in processes whose pipes the reactor watches, which Windows does not have')

# The functions of the tests, in their directory, and an application of Pyjoyment on Pyjo.Server.Lambda as one of them
TMP = Pyjo.File.tempdir()
TMP.child('handlers.py').spew(
    b"""import base64
import json
import os
import time

import Pyjo.Server.Lambda
import Pyjoyment


def echo(event, context):
    names = ('AWS_LAMBDA_FUNCTION_NAME', 'AWS_LAMBDA_FUNCTION_MEMORY_SIZE', '_HANDLER', 'LAMBDA_TASK_ROOT', 'FOO')
    body = {
        'event': event,
        'request_id': context.aws_request_id,
        'arn': context.invoked_function_arn,
        'env': {name: os.environ.get(name) for name in names},
    }
    return {'statusCode': 200, 'headers': {'content-type': 'application/json'}, 'body': json.dumps(body)}


def value(event, context):
    return {'hello': 'world'}


def text(event, context):
    return 'Hello Lambda!'


def binary(event, context):
    body = base64.b64encode(b'\\x89PNG\\x00').decode()
    return {'statusCode': 201, 'headers': {'content-type': 'image/png'}, 'body': body, 'isBase64Encoded': True}


def multi(event, context):
    return {
        'statusCode': 200,
        'headers': {'X-One': 'single', 'X-Two': 'single'},
        'multiValueHeaders': {'X-Two': ['a', 'b']},
        'cookies': ['a=1', 'b=2'],
        'body': 'multi',
    }


def printing(event, context):
    print('Hello from the function')
    return {'statusCode': 200, 'body': 'printed'}


def fail(event, context):
    raise ValueError('Something went wrong')


def invalid(event, context):
    return {'statusCode': 'many'}


def slow(event, context):
    time.sleep(10)
    return {'statusCode': 200, 'body': 'slow'}


def crash(event, context):
    os._exit(3)


def pid(event, context):
    return {'statusCode': 200, 'body': str(os.getpid())}


app = Pyjoyment.new()
app.log.level = 'fatal'


def index(c):
    c.render(json={'url': c.url_for('/').to_str(), 'path': c.req.url.path.to_abs_str(), 'query': c.param('q'),
                   'body': c.req.body.decode('latin-1'), 'cookie': c.cookie('foo')})


app.routes.any('/*rest', {'rest': ''}).to(cb=index)
pyjoyment = Pyjo.Server.Lambda.new(app=app).to_lambda_app()
"""
)
TMP.child('broken.py').spew(b"raise ImportError('No module named oops')\n")
ROOT = TMP.to_str()


def function(name, **attrs):
    app = Pyjo.App.Lambda.new(function=f'handlers.{name}', task_root=ROOT, **attrs)
    app.log.level = 'fatal'
    return app


def mounted(fcn, path='/fn'):
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    app.plugin('Mount', {path: fcn})
    return Pyjo.Test.Pyjo.new(app)


with subtest('Payload format 2.0'):
    with function('echo', env={'FOO': 'bar'}, function_name='myfunction', memory_size=256) as fcn:
        t = mounted(fcn)
        t.get_ok('/fn/hello?a=1&a=2&b=%C3%A9', {'Cookie': 'x=1; y=2', 'X-Foo': 'one'}).status_is(200)
        event = t.tx.res.json('/event')
        is_ok(event['version'], '2.0', 'version')
        is_ok(event['rawPath'], '/fn/hello', 'path with the mount')
        is_ok(event['rawQueryString'], 'a=1&a=2&b=%C3%A9', 'query')
        is_deeply_ok(event['queryStringParameters'], {'a': '1,2', 'b': 'é'}, 'parameters')
        is_deeply_ok(event['cookies'], ['x=1', 'y=2'], 'cookies')
        is_ok(event['headers']['x-foo'], 'one', 'header')
        ok('cookie' not in event['headers'], 'no Cookie header')
        is_ok(event['requestContext']['stage'], 'fn', 'stage of the mount')
        is_ok(event['requestContext']['http']['method'], 'GET', 'method')
        is_ok(event['requestContext']['http']['sourceIp'], '127.0.0.1', 'source address')
        is_ok(event['requestContext']['requestId'], t.tx.res.json('/request_id'), 'id of the request')
        is_ok(event['isBase64Encoded'], False, 'no body')
        is_ok(t.tx.res.json('/arn'), 'arn:aws:lambda:us-east-1:123456789012:function:myfunction', 'ARN')
        env = t.tx.res.json('/env')
        is_ok(env['AWS_LAMBDA_FUNCTION_NAME'], 'myfunction', 'AWS_LAMBDA_FUNCTION_NAME')
        is_ok(env['AWS_LAMBDA_FUNCTION_MEMORY_SIZE'], '256', 'AWS_LAMBDA_FUNCTION_MEMORY_SIZE')
        is_ok(env['_HANDLER'], 'handlers.echo', '_HANDLER')
        is_ok(os.path.realpath(env['LAMBDA_TASK_ROOT']), os.path.realpath(ROOT), 'LAMBDA_TASK_ROOT')
        is_ok(env['FOO'], 'bar', 'variable of the attribute')

        # A body of text, and one in Base64
        t.post_ok('/fn', {'Content-Type': 'application/json'}, b'{"a":1}').status_is(200)
        is_ok(t.tx.res.json('/event/body'), '{"a":1}', 'text')
        is_ok(t.tx.res.json('/event/isBase64Encoded'), False, 'not in Base64')
        is_ok(t.tx.res.json('/event/rawPath'), '/fn', 'path of the mount')
        t.post_ok('/fn', {'Content-Type': 'application/octet-stream'}, b'\x00\xff').status_is(200)
        is_ok(t.tx.res.json('/event/body'), base64.b64encode(b'\x00\xff').decode(), 'binary')
        is_ok(t.tx.res.json('/event/isBase64Encoded'), True, 'in Base64')

    # Not mounted, as the default stage
    with function('echo') as fcn:
        t = Pyjo.Test.Pyjo.new(fcn)
        t.get_ok('/foo').status_is(200).json_is('/event/rawPath', '/foo').json_is(
            '/event/requestContext/stage', '$default'
        )

with subtest('Payload format 1.0'):
    with function('echo', payload='1.0') as fcn:
        t = mounted(fcn)
        t.get_ok('/fn/hello?a=1&a=2&b=%C3%A9', {'X-Foo': 'one'}).status_is(200)
        event = t.tx.res.json('/event')
        is_ok(event['version'], '1.0', 'version')
        is_ok(event['path'], '/hello', 'path without the stage')
        is_ok(event['httpMethod'], 'GET', 'method')
        is_ok(event['requestContext']['path'], '/fn/hello', 'path with the stage')
        is_ok(event['requestContext']['stage'], 'fn', 'stage')
        is_deeply_ok(event['queryStringParameters'], {'a': '2', 'b': 'é'}, 'parameters')
        is_deeply_ok(event['multiValueQueryStringParameters'], {'a': ['1', '2'], 'b': ['é']}, 'parameters')
        is_ok(event['headers']['X-Foo'], 'one', 'header')
        is_deeply_ok(event['multiValueHeaders']['X-Foo'], ['one'], 'header of multiple values')
        is_ok(event['pathParameters']['proxy'], 'hello', 'proxy')

with subtest('Application Load Balancer'):
    with function('echo', payload='alb') as fcn:
        t = mounted(fcn)
        t.get_ok('/fn/hello?a=1&a=2&b=%C3%A9', {'X-Foo': 'one'}).status_is(200)
        event = t.tx.res.json('/event')
        ok('elb' in event['requestContext'], 'target group')
        is_ok(event['path'], '/fn/hello', 'whole path')
        is_deeply_ok(event['queryStringParameters'], {'a': '2', 'b': '%C3%A9'}, 'parameters as they were sent')
        is_ok(event['headers']['x-foo'], 'one', 'header in lower case')
        ok('multiValueHeaders' not in event, 'no headers of multiple values')
    with function('echo', payload='alb', multi_value_headers=True) as fcn:
        t = mounted(fcn)
        t.get_ok('/fn/hello?a=1&a=2', {'X-Foo': 'one'}).status_is(200)
        event = t.tx.res.json('/event')
        is_deeply_ok(event['multiValueQueryStringParameters'], {'a': ['1', '2']}, 'parameters of multiple values')
        is_deeply_ok(event['multiValueHeaders']['x-foo'], ['one'], 'headers of multiple values')
        ok('headers' not in event, 'no headers of one value')

with subtest('Application of Pyjoyment on Pyjo.Server.Lambda'):
    for payload, url in (('2.0', '/fn'), ('1.0', '/fn'), ('alb', '/')):
        with function('pyjoyment', payload=payload) as fcn:
            t = mounted(fcn)
            t.get_ok('/fn/foo/bar?q=1', {'Cookie': 'foo=baz'}).status_is(200)
            t.json_is('/path', '/fn/foo/bar' if payload == 'alb' else '/foo/bar', f'path of {payload}')
            t.json_is('/url', url, f'base path of {payload}')
            t.json_is('/query', '1', f'query of {payload}')
            t.json_is('/cookie', 'baz', f'cookie of {payload}')
            t.post_ok('/fn', {'Content-Type': 'text/plain'}, b'Hello!').status_is(200)
            t.json_is('/body', 'Hello!', f'body of {payload}')

with subtest('Responses'):
    with function('value') as fcn:
        t = Pyjo.Test.Pyjo.new(fcn)
        t.get_ok('/').status_is(200).content_type_is('application/json').json_is({'hello': 'world'})
    with function('text') as fcn:
        t = Pyjo.Test.Pyjo.new(fcn)
        t.get_ok('/').status_is(200).content_is('Hello Lambda!')
    with function('binary') as fcn:
        t = Pyjo.Test.Pyjo.new(fcn)
        t.get_ok('/').status_is(201).content_type_is('image/png')
        is_ok(t.tx.res.body, b'\x89PNG\x00', 'body in Base64')
    with function('multi') as fcn:
        t = Pyjo.Test.Pyjo.new(fcn)
        t.get_ok('/').status_is(200).header_is('X-One', 'single').content_is('multi')
        is_deeply_ok(t.tx.res.headers.every_header('X-Two'), ['a', 'b'], 'headers of multiple values')
        is_deeply_ok(t.tx.res.headers.every_header('Set-Cookie'), ['a=1', 'b=2'], 'cookies')

    # A value without statusCode is not a response of the format 1.0
    with function('value', payload='1.0') as fcn:
        t = Pyjo.Test.Pyjo.new(fcn)
        with fcn.log.capture('error') as messages:
            t.get_ok('/').status_is(502).content_is('Bad Gateway')
        like_ok(str(messages), r'Lambda function returned no statusCode', 'right error')

with subtest('Output'):
    with function('printing') as fcn:
        with fcn.log.capture('info') as messages:
            Pyjo.Test.Pyjo.new(fcn).get_ok('/').status_is(200).content_is('printed')
            Pyjo.IOLoop.timer(0.2, lambda loop: loop.stop())
            Pyjo.IOLoop.start()
        like_ok(str(messages), r'Lambda function: Hello from the function', 'output logged')

with subtest('Errors'):
    with function('fail') as fcn:
        t = Pyjo.Test.Pyjo.new(fcn)
        with fcn.log.capture('error') as messages:
            t.get_ok('/').status_is(502).content_is('Bad Gateway')
        like_ok(str(messages), r'Lambda function error: ValueError: Something went wrong', 'error of the function')
        t.get_ok('/').status_is(502)

    with function('invalid') as fcn:
        t = Pyjo.Test.Pyjo.new(fcn)
        with fcn.log.capture('error') as messages:
            t.get_ok('/').status_is(502)
        like_ok(str(messages), r'Lambda function returned an invalid response', 'invalid response')

    with Pyjo.App.Lambda.new(function='broken.handler', task_root=ROOT) as fcn:
        fcn.log.level = 'fatal'
        t = Pyjo.Test.Pyjo.new(fcn)
        with fcn.log.capture('error') as messages:
            t.get_ok('/').status_is(502)
        like_ok(str(messages), r'initialization error: Runtime.ImportModuleError: No module named oops', 'init error')
        like_ok(str(messages), r'Lambda function ended with status 1', 'process ended')
        t.get_ok('/').status_is(502)

    # A process that ends during an invocation, and a new one for the next
    with function('crash') as fcn:
        t = Pyjo.Test.Pyjo.new(fcn)
        with fcn.log.capture('error') as messages:
            t.get_ok('/').status_is(502)
        like_ok(str(messages), r'Lambda function ended with status 3', 'process ended')

    # An invocation that takes longer than the timeout, whose process is killed, and a new one for the next
    with function('slow', timeout=0.5) as fcn:
        t = Pyjo.Test.Pyjo.new(fcn)
        with fcn.log.capture('error') as messages:
            t.get_ok('/').status_is(502)
        like_ok(str(messages), r'Lambda function timed out after 0\.5 seconds', 'timed out')

    throws_ok(
        lambda: Pyjo.App.Lambda.new().handler(Pyjo.Transaction.HTTP.new()),
        re.compile(r'^No Lambda function'),
        'no function',
    )
    throws_ok(
        lambda: Pyjo.App.Lambda.new(function='a.b', payload='3.0').handler(Pyjo.Transaction.HTTP.new()),
        re.compile(r'^Invalid Lambda payload format "3\.0"'),
        'invalid payload format',
    )

with subtest('Process kept'):
    with function('pid') as fcn:
        t = Pyjo.Test.Pyjo.new(fcn)
        first = t.get_ok('/').status_is(200).tx.res.text
        t.get_ok('/').status_is(200).content_is(first)
        isnt_ok(first, str(os.getpid()), 'a process of its own')

        # The child of a fork starts its own, and leaves the one of its parent
        if not hasattr(os, 'fork'):
            skip('no fork', 3)
        else:
            pid = os.fork()
            if pid == 0:
                code = 1
                try:
                    tx = t.ua.get('/')
                    code = 0 if tx.res.code == 200 and tx.res.text not in ('', first) else 1
                    fcn.close()
                finally:
                    sys.stdout.flush()
                    os._exit(code)
            status = []

            def reap(loop):
                if (waited := os.waitpid(pid, os.WNOHANG))[0]:
                    status.append(os.waitstatus_to_exitcode(waited[1]))
                    loop.stop()

            waiting = [Pyjo.IOLoop.recurring(0.01, reap), Pyjo.IOLoop.timer(30, lambda loop: loop.stop())]
            Pyjo.IOLoop.start()
            for id in waiting:
                Pyjo.IOLoop.remove(id)
            is_deeply_ok(status, [0], 'a process of the child')
            t.get_ok('/').status_is(200).content_is(first)
            is_ok(t.tx.res.text, first, 'the process of the parent')

with subtest('Command'):
    command = [sys.executable, '-m', 'Pyjo.Server.Lambda', 'handlers.text']
    checkout = Pyjo.File.curfile().dirname().dirname().dirname().to_abs().to_str()
    with Pyjo.App.Lambda.new(command=command, task_root=ROOT, env={'PYTHONPATH': checkout}) as fcn:
        fcn.log.level = 'fatal'
        Pyjo.Test.Pyjo.new(fcn).get_ok('/').status_is(200).content_is('Hello Lambda!')

done_testing()
