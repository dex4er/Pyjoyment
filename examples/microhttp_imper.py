import Pyjo.IOLoop

import sys


port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080


def client_cb(loop, err, stream):
    def read_cb(stream, chunk):
        print(chunk.decode('utf-8'), end='')
        stream.close()

    stream.on('read', read_cb)
    stream.write(b'GET / HTTP/1.0\x0d\x0a\x0d\x0a')


Pyjo.IOLoop.client(address='127.0.0.1', port=port, cb=client_cb)

Pyjo.IOLoop.start()
