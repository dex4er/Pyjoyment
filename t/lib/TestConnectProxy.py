import Pyjo.IOLoop

import re


# A CONNECT proxy server for the tests, as Mojo::TestConnectProxy of Mojo's tests: it connects to the server and
# forwards the data in both directions, and answers a CONNECT to port 0 with an error


def proxy(from_, to, ok=None, zero=None):
    ok = ok or b'HTTP/1.1 200 OK\x0d\x0aServer: Test 1.0\x0d\x0a\x0d\x0a'
    zero = zero or (
        b'HTTP/1.1 404 NOT FOUND\x0d\x0aContent-Length: 20\x0d\x0aConnection: close\x0d\x0a\x0d\x0aSomething went wrong'
    )

    buffers = {}

    def server(loop, stream, id):
        # Connection to client
        @stream.on('read')
        def read(stream, chunk):
            # Write chunk from client to server
            buffer = buffers.setdefault(id, {'client': b''})
            if server := buffer.get('connection'):
                return Pyjo.IOLoop.stream(server).write(chunk)

            # Read connect request from client
            buffer['client'] += chunk
            if not re.search(rb'\x0d?\x0a\x0d?\x0a$', buffer['client']):
                return None
            request, buffer['client'] = buffer['client'], b''
            if not (m := re.search(rb'CONNECT \S+:(\d+)', request)):
                # Invalid request from client
                return Pyjo.IOLoop.remove(id)
            if int(m[1]) == 0:
                return Pyjo.IOLoop.stream(id).write(zero)

            # Connection to server
            def connected(loop, err, stream):
                # Connection to server failed
                if err:
                    Pyjo.IOLoop.remove(id)
                    return buffers.pop(id, None)

                # Start forwarding data in both directions
                Pyjo.IOLoop.stream(id).write(ok)
                stream.on('read', lambda stream, chunk: Pyjo.IOLoop.stream(id).write(chunk))

                # Server closed connection
                @stream.on('close')
                def close(stream):
                    Pyjo.IOLoop.remove(id)
                    buffers.pop(id, None)

            buffer['connection'] = Pyjo.IOLoop.client(connected, **to)

        # Client closed connection
        @stream.on('close')
        def close(stream):
            buffer = buffers.pop(id, {})
            if connection := buffer.get('connection'):
                Pyjo.IOLoop.remove(connection)

    return Pyjo.IOLoop.server(server, **from_)


if __name__ == '__main__':
    from Pyjo.Test import plan

    plan(skip_all='helper module, not a test')
