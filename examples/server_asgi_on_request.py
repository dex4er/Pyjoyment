import Pyjo.Server.ASGI

import uvicorn


asgi = Pyjo.Server.ASGI.new()
asgi.unsubscribe('request')


@asgi.on('request')
def request(asgi, tx):
    # Request
    method = tx.req.method
    path = tx.req.url.path

    # Response
    tx.res.code = 200
    tx.res.headers.content_type = 'text/plain'
    tx.res.body = f'{method} request for {path}\n'.encode()

    # Resume transaction
    tx.resume()


app = asgi.to_asgi_app()

uvicorn.run(app, port=3000)
