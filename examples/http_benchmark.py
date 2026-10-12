
import sys

import Pyjo.IOLoop
import Pyjo.URL

from Pyjo.Regexp import r
from Pyjo.Util import steady_time


argv = sys.argv[1:]

if len(argv) > 0 and (argv[0] == '-v' or argv[0] == '--verbose'):
    argv.pop(0)
    verbose = True
else:
    verbose = False

if len(argv) > 0:
    url = argv[0]
else:
    url = 'http://localhost/bigfile.bin'
url = Pyjo.URL.new(url)

if len(argv) > 1:
    n = int(argv[1])
else:
    n = 1


speeds = []

t0 = steady_time()


print(url)

for i in range(n):

    @Pyjo.IOLoop.client(address=url.host, port=(url.port or 80))
    def client(loop, err, stream):
        class context:
            size = 0

        if err:
            return

        @stream.on
        def read(stream, chunk):
            context.size += len(chunk)
            if verbose:
                print(f"{context.size}\r", end='')

        @stream.on
        def close(stream):
            t1 = steady_time()
            delta = t1 - t0
            speeds.append(int(context.size * 8 / 1024 / delta / 1000))

            if verbose:
                print(context.size)

        # Write request
        stream.write(f"GET {url.path} HTTP/1.1\x0d\x0aHost: {url.host}:{url.port or 80}\x0d\x0a\x0d\x0a".encode('ascii'))


Pyjo.IOLoop.start()


speed = str(sum(speeds))
while r(r'(?<=\d)(\d{3})(,|$)').search(speed):
    speed = r(r'(?<=\d)(\d{3})(,|$)').sub(r',\1', speed)
print(f'{speed} Mb/s')
