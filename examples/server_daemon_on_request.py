import Pyjo.Server.Daemon


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
        tx.res.body = f'{method} request for {path}\n'.encode()

        # Resume transaction
        tx.resume()

    daemon.run()
