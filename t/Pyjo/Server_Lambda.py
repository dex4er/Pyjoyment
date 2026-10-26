import Pyjo.File
import Pyjo.IOLoop
import Pyjo.Server.Lambda

from Pyjo.JSON import decode_json
from Pyjo.Test import *
from Pyjoyment.Lite import app, get, post, under

import base64
import importlib
import os
import sys


# Not in Mojolicious: Pyjo.Server.Lambda, for the events of AWS Lambda, which Mojolicious has no server for; the events
# are those of the payload formats of API Gateway, Function URLs and Application Load Balancer


def http_api(method='GET', path='/', query='', headers=None, cookies=None, body=None, encoded=False, stage='$default'):
    # The payload format 2.0, of HTTP APIs of API Gateway and of Function URLs
    event = {
        'version': '2.0',
        'routeKey': '$default',
        'rawPath': path,
        'rawQueryString': query,
        'headers': {
            'host': 'abc.execute-api.eu-central-1.amazonaws.com',
            'x-forwarded-proto': 'https',
            **(headers or {}),
        },
        'requestContext': {
            'domainName': 'abc.execute-api.eu-central-1.amazonaws.com',
            'http': {'method': method, 'path': path, 'protocol': 'HTTP/1.1', 'sourceIp': '192.0.2.1'},
            'stage': stage,
        },
        'isBase64Encoded': encoded,
    }
    if cookies is not None:
        event['cookies'] = cookies
    if body is not None:
        event['body'] = body
    return event


def rest_api(method='GET', path='/', query=None, headers=None, body=None, encoded=False, stage='prod'):
    # The payload format 1.0, of REST APIs of API Gateway, with the parameters of the query decoded
    headers = {'Host': 'abc.execute-api.eu-central-1.amazonaws.com', 'X-Forwarded-Proto': 'https', **(headers or {})}
    return {
        'resource': '/{proxy+}',
        'path': path,
        'httpMethod': method,
        'headers': {
            name: values[-1] for name, values in ((n, v if isinstance(v, list) else [v]) for n, v in headers.items())
        },
        'multiValueHeaders': {name: value if isinstance(value, list) else [value] for name, value in headers.items()},
        'queryStringParameters': {name: values[-1] for name, values in query.items()} if query else None,
        'multiValueQueryStringParameters': query,
        'requestContext': {
            'httpMethod': method,
            'identity': {'sourceIp': '192.0.2.2'},
            'path': f'/{stage}{path}',
            'protocol': 'HTTP/1.1',
            'stage': stage,
        },
        'body': body,
        'isBase64Encoded': encoded,
    }


def alb(method='GET', path='/', query=None, headers=None, body='', multi=False):
    # The event of an Application Load Balancer, with the parameters of the query as they were sent
    headers = {'host': 'my-alb-123.eu-central-1.elb.amazonaws.com', 'x-forwarded-for': '192.0.2.3', **(headers or {})}
    event = {
        'requestContext': {'elb': {'targetGroupArn': 'arn:aws:elasticloadbalancing:eu-central-1:123:targetgroup/t/1'}},
        'httpMethod': method,
        'path': path,
        'body': body,
        'isBase64Encoded': False,
    }
    if multi:
        event['multiValueHeaders'] = {name: [value] for name, value in headers.items()}
        event['multiValueQueryStringParameters'] = {name: [value] for name, value in (query or {}).items()}
    else:
        event['headers'] = headers
        event['queryStringParameters'] = query or {}
    return event


# Silence
app.log.level = 'fatal'


@under
def finish(c):
    c.on('finish', lambda c: finished.append(c.req.url.path.to_str()))
    return True


finished = []

get('/', {'text': 'Your Pyjoyment is working!'})


@get('/params')
def params(c):
    c.render(json=c.req.params.to_dict())


@post('/echo')
def echo(c):
    c.render(data=c.req.body, format='txt')


@get('/cookies')
def cookies(c):
    c.cookie('foo', 'bar')
    c.cookie('baz', 'yada')
    c.render(text=f'cookie {c.cookie("test")}')


@get('/info')
def info(c):
    c.render(
        json={
            'remote': c.tx.remote_address,
            'url': c.url_for('info').to_abs().to_str(),
            'path': c.req.url.path.to_str(),
            'agent': c.req.headers.user_agent,
            'function': c.req.env['lambda.context'],
            'event': 'requestContext' in c.req.env['lambda.event'],
        }
    )


@get('/binary')
def binary(c):
    c.render(data=b'\x89PNG\x00\xff', format='png')


@get('/delayed')
def delayed(c):
    c.render_later()
    Pyjo.IOLoop.timer(0.01, lambda loop: c.render(text='Delayed!'))


@get('/stream')
def stream(c):
    c.res.headers.content_type = 'text/plain'
    c.write_chunk(b'one, ')
    Pyjo.IOLoop.timer(0.01, lambda loop: c.write_chunk(b'two', lambda c: c.finish()))


handler = Pyjo.Server.Lambda.new(app=app).to_lambda_app()

with subtest('HTTP API'):
    res = handler(http_api(headers={'user-agent': 'Bender'}), None)
    is_ok(res['statusCode'], 200, 'status')
    is_ok(res['headers']['content-type'], 'text/html;charset=UTF-8', 'content type')
    is_ok(res['body'], 'Your Pyjoyment is working!', 'body')
    is_ok(res['isBase64Encoded'], False, 'not encoded')
    ok('cookies' not in res, 'no cookies')
    is_deeply_ok(finished, ['/'], 'finished')

with subtest('Query'):
    res = handler(http_api(path='/params', query='foo=bar%20baz&foo=yada&x=%26'), None)
    is_ok(res['body'], '{"foo":["bar baz","yada"],"x":"&"}', 'parameters')

    res = handler(rest_api(path='/params', query={'foo': ['bar baz', 'yada'], 'x': ['&']}), None)
    is_ok(res['body'], '{"foo":["bar baz","yada"],"x":"&"}', 'decoded parameters')

    res = handler(alb(path='/params', query={'foo': 'bar%20baz', 'x': '%26'}), None)
    is_ok(res['body'], '{"foo":"bar baz","x":"&"}', 'parameters as they were sent')

with subtest('Body'):
    res = handler(http_api('POST', '/echo', body='Hello Lambda!'), None)
    is_ok(res['statusCode'], 200, 'status')
    is_ok(res['body'], 'Hello Lambda!', 'text')

    res = handler(http_api('POST', '/echo', body=base64.b64encode(b'\x00\xff').decode(), encoded=True), None)
    is_ok(res['isBase64Encoded'], True, 'encoded')
    is_ok(base64.b64decode(res['body']), b'\x00\xff', 'binary')

    res = handler(rest_api('POST', '/echo', body='I ♥ Pyjoyment!'), None)
    is_ok(res['body'], 'I ♥ Pyjoyment!', 'characters')

    res = handler(http_api('GET', '/binary'), None)
    is_ok(res['headers']['content-type'], 'image/png', 'binary type')
    is_ok(res['isBase64Encoded'], True, 'binary response')
    is_ok(base64.b64decode(res['body']), b'\x89PNG\x00\xff', 'binary content')

    res = handler(http_api('HEAD', '/'), None)
    is_ok(res['statusCode'], 200, 'status')
    is_ok(res['body'], '', 'no body')

with subtest('Cookies'):
    res = handler(http_api(path='/cookies', cookies=['test=works', 'other=1']), None)
    is_ok(res['body'], 'cookie works', 'request cookie')
    is_deeply_ok(res['cookies'], ['foo=bar', 'baz=yada'], 'response cookies')
    ok('set-cookie' not in res['headers'], 'not in the headers')

    res = handler(rest_api(path='/cookies', headers={'Cookie': 'test=works'}), None)
    is_ok(res['body'], 'cookie works', 'request cookie')
    is_deeply_ok(res['multiValueHeaders']['Set-Cookie'], ['foo=bar', 'baz=yada'], 'response cookies')

with subtest('Request information'):
    res = handler(http_api(path='/info', headers={'user-agent': 'Bender'}), 'context')
    is_ok(res['headers']['content-type'], 'application/json;charset=UTF-8', 'content type')
    data = decode_json(res['body'])
    is_ok(data['remote'], '192.0.2.1', 'remote address')
    is_ok(data['url'], 'https://abc.execute-api.eu-central-1.amazonaws.com/info', 'absolute URL')
    is_ok(data['agent'], 'Bender', 'header')
    is_ok(data['function'], 'context', 'context in the environment')
    is_ok(data['event'], True, 'event in the environment')

    res = handler(rest_api(path='/info'), None)
    data = decode_json(res['body'])
    is_ok(data['remote'], '192.0.2.2', 'remote address')
    is_ok(data['url'], 'https://abc.execute-api.eu-central-1.amazonaws.com/prod/info', 'stage as the base path')
    is_ok(data['path'], 'info', 'path relative to the stage')

    res = handler(http_api(path='/prod/info', stage='prod'), None)
    data = decode_json(res['body'])
    is_ok(data['url'], 'https://abc.execute-api.eu-central-1.amazonaws.com/prod/info', 'named stage as the base path')
    is_ok(data['path'], 'info', 'path relative to the named stage')

    res = handler(alb(path='/info'), None)
    data = decode_json(res['body'])
    is_ok(data['remote'], None, 'no remote address')
    is_ok(data['url'], 'http://my-alb-123.eu-central-1.elb.amazonaws.com/info', 'URL')

with subtest('Application Load Balancer'):
    res = handler(alb(path='/cookies'), None)
    is_ok(res['statusCode'], 200, 'status')
    is_ok(res['statusDescription'], '200 OK', 'status description')
    is_ok(res['headers']['Set-Cookie'], 'baz=yada', 'last cookie of single values')
    ok('multiValueHeaders' not in res, 'single values')

    res = handler(alb(path='/cookies', multi=True), None)
    is_deeply_ok(res['multiValueHeaders']['Set-Cookie'], ['foo=bar', 'baz=yada'], 'multiple values')
    ok('headers' not in res, 'no single values')

with subtest('Not found'):
    res = handler(http_api(path='/missing'), None)
    is_ok(res['statusCode'], 404, 'status')

with subtest('Delayed response'):
    res = handler(http_api(path='/delayed'), None)
    is_ok(res['statusCode'], 200, 'status')
    is_ok(res['body'], 'Delayed!', 'body')

with subtest('Chunked response'):
    res = handler(http_api(path='/stream'), None)
    is_ok(res['statusCode'], 200, 'status')
    is_ok(res['body'], 'one, two', 'body without the framing')
    ok('transfer-encoding' not in res['headers'], 'no hop-by-hop headers')

with subtest('Invoke mode'):
    is_ok(Pyjo.Server.Lambda.new().invoke_mode, 'BUFFERED', 'default')
    os.environ['PYJO_LAMBDA_INVOKE_MODE'] = 'RESPONSE_STREAM'
    try:
        is_ok(Pyjo.Server.Lambda.new().invoke_mode, 'RESPONSE_STREAM', 'from the environment')
    finally:
        del os.environ['PYJO_LAMBDA_INVOKE_MODE']
    is_ok(Pyjo.Server.Lambda.new(invoke_mode='RESPONSE_STREAM').invoke_mode, 'RESPONSE_STREAM', 'attribute')


def streamed(res):
    # The prelude of the status and the headers, and the chunks of the body
    try:
        chunks = list(res)
    finally:
        res.close()
    prelude, delimiter, rest = chunks[0].partition(b'\x00' * 8)
    is_ok((delimiter, rest), (b'\x00' * 8, b''), 'prelude in a chunk of its own')
    return decode_json(prelude), chunks[1:]


streaming = Pyjo.Server.Lambda.new(app=app, invoke_mode='RESPONSE_STREAM').to_lambda_app()

with subtest('Streaming response'):
    finished.clear()
    res = streaming(http_api(path='/stream'), None)
    is_ok(res.content_type, 'application/vnd.awslambda.http-integration-response', 'content type')
    prelude, chunks = streamed(res)
    is_ok(prelude['statusCode'], 200, 'status')
    is_ok(prelude['headers']['content-type'], 'text/plain', 'content type of the body')
    ok('transfer-encoding' not in prelude['headers'], 'no hop-by-hop headers')
    ok('body' not in prelude and 'isBase64Encoded' not in prelude, 'no body in the prelude')
    is_deeply_ok(chunks, [b'one, ', b'two'], 'chunks without the framing')
    is_deeply_ok(finished, ['/stream'], 'finished')

    prelude, chunks = streamed(streaming(http_api(path='/cookies'), None))
    is_deeply_ok(prelude['cookies'], ['foo=bar', 'baz=yada'], 'cookies of the format 2.0')
    is_ok(b''.join(chunks), b'cookie None', 'body')

    prelude, chunks = streamed(streaming(http_api(path='/binary'), None))
    is_ok(b''.join(chunks), b'\x89PNG\x00\xff', 'binary body as it is')

    prelude, chunks = streamed(streaming(rest_api(path='/cookies'), None))
    is_deeply_ok(prelude['multiValueHeaders']['Set-Cookie'], ['foo=bar', 'baz=yada'], 'headers of the format 1.0')

    prelude, chunks = streamed(streaming(http_api(path='/missing'), None))
    is_ok(prelude['statusCode'], 404, 'not found')

    # An Application Load Balancer, which has no streaming
    res = streaming(alb(path='/cookies'), None)
    is_ok(res['statusCode'], 200, 'buffered response')
    is_ok(res['statusDescription'], '200 OK', 'status description')


# The runtime client of a handler, or of _HANDLER, for the events of a Runtime API of the test
def runtime(handler, events, posts, env=None, ends=False):
    command = [sys.executable, '-m', 'Pyjo.Server.Lambda', *([handler] if handler else [])]
    return RuntimeAPI.invoke(command, events, posts, TMP.to_str(), env, ends)


sys.path.insert(0, Pyjo.File.curfile().dirname().sibling('lib').to_str())
RuntimeAPI = importlib.import_module('RuntimeAPI')
TMP = Pyjo.File.tempdir()
TMP.child('handlers.py').spew(
    b"""import json
import os

from Pyjoyment.Lite import app, get

import Pyjo.IOLoop
import Pyjo.Server.Lambda


def context(event, context):
    return {
        'event': event,
        'aws_request_id': context.aws_request_id,
        'invoked_function_arn': context.invoked_function_arn,
        'function_name': context.function_name,
        'memory_limit_in_mb': context.memory_limit_in_mb,
        'remaining': 0 < context.get_remaining_time_in_millis() <= 60000,
        'trace': os.environ.get('_X_AMZN_TRACE_ID'),
    }


def fail(event, context):
    raise ValueError('Something went wrong')


def unserializable(event, context):
    return object()


@get('/')
def index(c):
    c.render(text='Hello Lambda!')


@get('/parts')
def parts(c):
    c.res.headers.content_type = 'text/plain'
    c.write_chunk(b'one, ')
    Pyjo.IOLoop.timer(0.5, lambda loop: c.write_chunk(b'two', lambda c: c.finish()))


def generator(event, context):
    yield b'first'
    yield b''
    yield b'second'


def broken_stream(event, context):
    yield b'first'
    raise ValueError('Stream broke')


def broken_start(event, context):
    raise ValueError('Not started')
    yield b''


app.log.level = 'fatal'
pyjoyment = Pyjo.Server.Lambda.new(app=app).to_lambda_app()
"""
)
TMP.child('broken.py').spew(b"raise ImportError('No module named oops')\n")

with subtest('Runtime client'):
    got, code = runtime('handlers.context', [('a1', {'n': 1}), ('a2', {'n': 2})], 2)
    is_ok(len(got), 2, 'two invocations')
    kind, id, error, body = got[0]
    is_ok(kind, 'response', 'response')
    is_ok(id, 'a1', 'id of the invocation')
    is_deeply_ok(body['event'], {'n': 1}, 'event')
    is_ok(body['aws_request_id'], 'a1', 'aws_request_id')
    is_ok(body['invoked_function_arn'], 'arn:aws:lambda:eu-central-1:123456789012:function:test', 'ARN')
    is_ok(body['function_name'], 'test', 'function_name')
    is_ok(body['memory_limit_in_mb'], '128', 'memory_limit_in_mb')
    is_ok(body['remaining'], True, 'get_remaining_time_in_millis')
    is_ok(body['trace'], 'Root=1-a1', 'trace id')
    is_deeply_ok(got[1][3]['event'], {'n': 2}, 'next event')

    # An exception of the handler, and the next invocation
    got, code = runtime('handlers.fail', [('b1', {}), ('b2', {})], 2)
    kind, id, error, body = got[0]
    is_ok(kind, 'error', 'error')
    is_ok(id, 'b1', 'id of the invocation')
    is_ok(error, 'Unhandled', 'type of the function error')
    is_ok(body['errorMessage'], 'Something went wrong', 'message')
    is_ok(body['errorType'], 'ValueError', 'type')
    like_ok(''.join(body['stackTrace']), r'handlers\.py', 'stack trace')
    is_ok(got[1][:2], ('error', 'b2'), 'next invocation')

    # A value that is not JSON
    got, code = runtime('handlers.unserializable', [('c1', {})], 1)
    is_ok(got[0][0], 'error', 'error')
    is_ok(got[0][3]['errorType'], 'TypeError', 'type')

    # An application of Pyjoyment, and _HANDLER
    got, code = runtime(None, [('d1', http_api())], 1, {'_HANDLER': 'handlers.pyjoyment'})
    kind, id, error, body = got[0]
    is_ok(kind, 'response', 'response')
    is_ok(body['statusCode'], 200, 'status')
    is_ok(body['body'], 'Hello Lambda!', 'body')

    # An error of the initialization, which ends the client
    got, code = runtime('broken.handler', [], 1, ends=True)
    kind, id, error, body = got[0]
    is_ok(kind, 'init', 'init error')
    is_ok(error, 'Runtime.ImportModuleError', 'type of the function error')
    is_ok(body['errorType'], 'Runtime.ImportModuleError', 'type')
    like_ok(body['errorMessage'], r'No module named oops', 'message')
    is_ok(code, 1, 'exit status')

    got, code = runtime('handlers', [], 1, ends=True)
    like_ok(got[0][3]['errorMessage'], r'^Bad handler "handlers"', 'bad handler')
    got, code = runtime('handlers.missing', [], 1, ends=True)
    like_ok(got[0][3]['errorMessage'], r'^Handler "missing" missing on module "handlers"', 'missing handler')

with subtest('Streaming runtime client'):
    # An application of Pyjoyment, whose chunks come as they are written, and the next invocation on a new connection
    env = {'_HANDLER': 'handlers.pyjoyment', 'PYJO_LAMBDA_INVOKE_MODE': 'RESPONSE_STREAM'}
    got, code = runtime(None, [('f1', http_api(path='/parts')), ('f2', http_api())], 2, env)
    kind, id, error, body = got[0]
    is_ok((kind, id, error), ('response', 'f1', None), 'response')
    is_ok(body['content_type'], 'application/vnd.awslambda.http-integration-response', 'content type')
    prelude, _, content = body['body'].partition(b'\x00' * 8)
    is_ok(decode_json(prelude)['statusCode'], 200, 'status')
    is_ok(content, b'one, two', 'body')
    # The times the parts are there, as a read can take several chunks
    times, received = {}, b''
    for at, chunk in body['chunks']:
        received += chunk
        for part in (b'one, ', b'two'):
            if part in received:
                times.setdefault(part, at)
    ok(times[b'two'] - times[b'one, '] >= 0.4, 'chunks as they are written')
    is_ok(body['error_body'], None, 'no error')
    kind, id, error, body = got[1]
    is_ok((kind, id), ('response', 'f2'), 'next invocation')
    is_ok(body['body'].partition(b'\x00' * 8)[2], b'Hello Lambda!', 'body of the next invocation')

    # Any handler that returns an iterator, with empty chunks left out
    got, code = runtime('handlers.generator', [('g1', {})], 1)
    kind, id, error, body = got[0]
    is_ok((kind, error), ('response', None), 'response')
    is_ok(body['content_type'], 'application/octet-stream', 'content type')
    is_ok(body['body'], b'firstsecond', 'body')

    # An exception in the middle of the stream, in the trailers
    got, code = runtime('handlers.broken_stream', [('h1', {}), ('h2', {})], 2)
    kind, id, error, body = got[0]
    is_ok((kind, id, error), ('response', 'h1', 'Unhandled'), 'error in the trailers')
    is_ok(body['body'], b'first', 'body before the error')
    error = decode_json(base64.b64decode(body['error_body']))
    is_ok(error['errorMessage'], 'Stream broke', 'message')
    is_ok(error['errorType'], 'ValueError', 'type')
    is_ok(got[1][:3], ('response', 'h2', 'Unhandled'), 'next invocation')

    # An exception before the first chunk, as the error of the invocation
    got, code = runtime('handlers.broken_start', [('i1', {})], 1)
    kind, id, error, body = got[0]
    is_ok((kind, id, error), ('error', 'i1', 'Unhandled'), 'error of the invocation')
    is_ok(body['errorMessage'], 'Not started', 'message')

done_testing()
