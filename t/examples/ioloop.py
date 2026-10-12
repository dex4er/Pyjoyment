import Pyjo.Test


class NoseTest(Pyjo.Test.NoseTest):
    script = __file__
    srcdir = '../..'


class UnitTest(Pyjo.Test.UnitTest):
    script = __file__


if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import Pyjo.IOLoop

    plan_tests(4)

    # Listen on random port
    @Pyjo.IOLoop.server
    def server(loop, stream, cid):

        @stream.on
        def read(stream, chunk):
            # Process input chunk
            is_ok(chunk.decode('utf-8'), 'GET / HTTP/1.1\x0d\x0a\x0d\x0a', "server's input chunk")

            # Write response
            stream.write(b'HTTP/1.1 200 OK\x0d\x0a\x0d\x0a')

            # Disconnect client
            stream.close_gracefully()

    port = Pyjo.IOLoop.acceptor(server).port

    # Prevent race with server
    @Pyjo.IOLoop.timer(0.2)
    def client_delay(loop):

        # Connect to server
        @Pyjo.IOLoop.client(port=port)
        def client(loop, err, stream):

            @stream.on
            def read(stream, chunk):
                # Process input
                is_ok(chunk.decode('utf-8'), 'HTTP/1.1 200 OK\x0d\x0a\x0d\x0a', "client's input chunk")

            # Write request
            stream.write(b'GET / HTTP/1.1\x0d\x0a\x0d\x0a')

    # Add a timer
    @Pyjo.IOLoop.timer(1)
    def timeouter(loop):
        pass_ok('Timeout')
        # Shutdown server
        loop.remove(server)

    # Start event loop
    Pyjo.IOLoop.start()

    pass_ok('Event loop ended')

    done_testing()
