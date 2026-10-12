import Pyjo.IOLoop


# Listen on port 3000
@Pyjo.IOLoop.server(port=3000)
def server(loop, stream, cid):

    @stream.on
    def read(stream, chunk):
        # Process input chunk
        print(f"Server: {chunk.decode('utf-8')}")

        # Write response
        stream.write(b"HTTP/1.1 200 OK\x0d\x0a\x0d\x0a")

        # Disconnect client
        stream.close_gracefully()


# Connect to port 3000
@Pyjo.IOLoop.client(port=3000)
def client(loop, err, stream):

    @stream.on
    def read(stream, chunk):
        # Process input
        print(f"Client: {chunk.decode('utf-8')}")

    # Write request
    stream.write(b"GET / HTTP/1.1\x0d\x0a\x0d\x0a")


# Add a timer
@Pyjo.IOLoop.timer(3)
def timeouter(loop):
    print("Timeout")
    # Shutdown server
    loop.remove(server)


# Start event loop
Pyjo.IOLoop.start()
