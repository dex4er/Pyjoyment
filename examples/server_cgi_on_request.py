import Pyjo.Server.CGI

from Pyjo.Util import b


cgi = Pyjo.Server.CGI.new()
cgi.unsubscribe('request')


@cgi.on
def request(cgi, tx):
    # Request
    method = tx.req.method
    path = tx.req.url.path

    # Response
    tx.res.code = 200
    tx.res.headers.content_type = 'text/plain'
    tx.res.body = b(f'{method} request for {path}\n')

    # Resume transaction
    tx.resume()


cgi.run()
