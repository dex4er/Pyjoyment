import Pyjo.IOLoop

import sys


port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080


def server_cb(loop, stream, cid):

    def on_read_cb(stream, chunk):
        # Check if we got start line and headers (no body support)
        if chunk.find(b'\x0d\x0a\x0d\x0a') >= 0:
            if chunk.find(b'\x0d\x0aConnection: Keep-Alive\x0d\x0a') >= 0:
                keepalive = True
            else:
                keepalive = False

            # Write a minimal HTTP response
            # (the "Hello World!" message has been optimized away!)
            response = b'HTTP/1.1 200 OK\x0d\x0aContent-Length: 0\x0d\x0a'
            if keepalive:
                response += b'Connection: keep-alive\x0d\x0a'
            response += b'\x0d\x0a'

            stream.write(response)

            if not keepalive:
                stream.close_gracefully()

    stream.on(on_read_cb, 'read')


Pyjo.IOLoop.server(server_cb, address='0.0.0.0', port=port)


Pyjo.IOLoop.start()
