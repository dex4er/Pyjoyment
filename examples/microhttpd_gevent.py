import sys

from gevent.server import StreamServer


port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080


def connection_cb(socket, address):
    chunk = socket.recv(10240)

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

        socket.sendall(response)

        if not keepalive:
            socket.close()


if __name__ == '__main__':
    server = StreamServer(('0.0.0.0', port), connection_cb)
    server.serve_forever()
