import Pyjo.Server.Daemon
from Pyjo.Util import b

with Pyjo.Server.Daemon.new(listen=['http://*:3000']) as daemon:
    daemon.unsubscribe('request')

    @daemon.on
    def request(daemon, tx):
        # Request
        method = tx.req.method
        path = tx.req.url.path

        # Response
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = b(f"{method} request for {path}\n")

        # Resume transaction
        tx.resume()

    daemon.run()
