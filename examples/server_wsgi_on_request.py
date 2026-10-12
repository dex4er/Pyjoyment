import Pyjo.Server.WSGI
from Pyjo.Util import b

from wsgiref.simple_server import make_server

wsgi = Pyjo.Server.WSGI.new(listen=['http://*:3000'])
wsgi.unsubscribe('request')


@wsgi.on
def request(wsgi, tx):
    # Request
    method = tx.req.method
    path = tx.req.url.path

    # Response
    tx.res.code = 200
    tx.res.headers.content_type = 'text/plain'
    tx.res.body = b(f"{method} request for {path}\n")

    # Resume transaction
    tx.resume()


app = wsgi.to_wsgi_app()

httpd = make_server('', 3000, app)
httpd.serve_forever()
