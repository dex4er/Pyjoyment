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
    import Pyjoyment

    app = Pyjoyment.new()
    app.log.level = 'fatal'
    app.routes.get('/foo', lambda c: c.render(text=f'{c.req.env["lambda.context"]}'))

    # The handler "myapp.handler" of an event function
    handler = Pyjo.Server.Lambda.new(app=app).to_lambda_app()
    is_ok(handler(event(), 'context')['body'], 'context', 'context')

with subtest('run'):
    server = Pyjo.Server.Lambda.new(app=app)
    response = server.run(event(), 'context')
    is_ok(response['statusCode'], 200, 'response')

with subtest('to_lambda_app'):
    handler = server.to_lambda_app()
    ok(callable(handler), 'handler')

done_testing()
