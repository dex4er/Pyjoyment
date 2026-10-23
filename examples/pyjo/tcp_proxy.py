import Pyjo.IOLoop

from Pyjo.Util import getopt

import sys


# A fully asynchronous TCP proxy: every incoming connection on --listen is
# tunneled to --target, both directions piped with backpressure. The event
# loop accepts and serves any number of connections at the same time.

opts = getopt({'l|listen=s': None, 't|target=s': None})

if not opts.listen or not opts.target:
    print(f'Usage: {sys.argv[0]} --listen ADDRESS:PORT --target ADDRESS:PORT', file=sys.stderr)
    sys.exit(1)


def address_port(value, default_address='127.0.0.1'):
    address, _, port = value.rpartition(':')
    return address or default_address, int(port)


listen_address, listen_port = address_port(opts.listen)
target_address, target_port = address_port(opts.target)


def pipe(src, dst):
    # Pause the source while a chunk is in flight and resume it once the
    # destination has drained, so a slow peer cannot flood memory

    @src.on
    def read(src, chunk):
        src.stop()
        dst.write(chunk, lambda dst: src.start())

    @src.on
    def close(src):
        dst.close_gracefully()

    @src.on
    def error(src, err):
        dst.close()


@Pyjo.IOLoop.server(address=listen_address, port=listen_port)
def server(loop, client, cid):
    # Do not read from the client until the target is connected, and let a
    # tunnel stay idle for as long as it likes
    client.stop()
    client.timeout = 0

    @loop.client(address=target_address, port=target_port)
    def tid(loop, err, target):
        if err:
            client.close()
            return

        target.timeout = 0

        pipe(client, target)
        pipe(target, client)

        client.start()


print(
    f'TCP proxy listening on {listen_address}:{listen_port}, tunneling to {target_address}:{target_port}',
    file=sys.stderr,
)

Pyjo.IOLoop.start()
