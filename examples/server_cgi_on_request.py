import Pyjo.Server.CGI


cgi = Pyjo.Server.CGI.new()


@cgi.unsubscribe('request').on('request')
def request(cgi, tx):
    # Request
    method = tx.req.method
    path = tx.req.url.path

    # Response
    tx.res.code = 200
    tx.res.headers.content_type = 'text/plain'
    tx.res.body = f'{method} request for {path}!'.encode()

    # Resume transaction
    tx.resume()


cgi.run()
