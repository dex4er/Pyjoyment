from __future__ import print_function

import sys

import Pyjo.IOLoop

from Pyjo.IOLoop import on


port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080


@Pyjo.IOLoop.client(address='127.0.0.1', port=port)
def client_cb(loop, err, stream):

    @on(stream, 'read')
    def read_cb(stream, chunk):
        print(chunk.decode('utf-8'), end='')
        stream.close()

    stream.write(b"GET / HTTP/1.0\x0d\x0a\x0d\x0a")


Pyjo.IOLoop.start()
