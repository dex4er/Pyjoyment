import Pyjo.IOLoop


# Listen on port 3000
def server_cb(loop, stream, cid):

    def on_read_cb(stream, chunk):
        # Process input chunk
        print(f'Server: {chunk.decode("utf-8")}')

        # Write response
        stream.write(b'HTTP/1.1 200 OK\x0d\x0a\x0d\x0a')

        # Disconnect client
        stream.close_gracefully()

    stream.on(on_read_cb, 'read')


server = Pyjo.IOLoop.server(port=3000, cb=server_cb)


# Connect to port 3000
def client_cb(loop, err, stream):

    def on_read_cb(stream, chunk):
        # Process input
        print(f'Client: {chunk.decode("utf-8")}')

    stream.on(on_read_cb, 'read')

    # Write request
    stream.write(b'GET / HTTP/1.1\x0d\x0a\x0d\x0a')


Pyjo.IOLoop.client(port=3000, cb=client_cb)


# Add a timer
def timeouter_cb(loop):
    print('Timeout')
    # Shutdown server
    loop.remove(server)


Pyjo.IOLoop.timer(timeouter_cb, 3)


# Start event loop
Pyjo.IOLoop.start()
