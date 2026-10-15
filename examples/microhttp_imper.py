import Pyjo.IOLoop

import sys


port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080


def client_cb(loop, err, stream):
    if err:
        print(f'Connection error: {err}', file=sys.stderr)
        return

    def read_cb(stream, chunk):
        print(chunk.decode('utf-8'), end='')
        stream.close()

    stream.on('read', read_cb)
    stream.write(b'GET / HTTP/1.0\x0d\x0a\x0d\x0a')


Pyjo.IOLoop.client(client_cb, address='127.0.0.1', port=port)

Pyjo.IOLoop.start()
