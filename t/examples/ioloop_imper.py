if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import Pyjo.IOLoop

    plan_tests(4)

    # Listen on random port
    def server_cb(loop, stream, cid):

        def on_read_cb(stream, chunk):
            # Process input chunk
            is_ok(chunk.decode('utf-8'), 'GET / HTTP/1.1\x0d\x0a\x0d\x0a', "server's input chunk")

            # Write response
            stream.write(b'HTTP/1.1 200 OK\x0d\x0a\x0d\x0a')

            # Disconnect client
            stream.close_gracefully()

        stream.on('read', on_read_cb)

    server_id = Pyjo.IOLoop.server(server_cb)

    port = Pyjo.IOLoop.acceptor(server_id).port

    # Connect to server
    def client_cb(loop, err, stream):

        def on_read_cb(stream, chunk):
            # Process input
            is_ok(chunk.decode('utf-8'), 'HTTP/1.1 200 OK\x0d\x0a\x0d\x0a', "client's input chunk")

        # Write request
        stream.write(b'GET / HTTP/1.1\x0d\x0a\x0d\x0a')

        stream.on('read', on_read_cb)

    Pyjo.IOLoop.client(client_cb, port=port)

    # Add a timer
    def timeouter_cb(loop):
        pass_ok('Timeout')
        # Shutdown server
        loop.remove(server_id)

    Pyjo.IOLoop.timer(timeouter_cb, 1)

    # Start event loop
    Pyjo.IOLoop.start()

    pass_ok('Event loop ended')

    done_testing()
