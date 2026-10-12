import asyncio
import sys


opts = dict([['address', '0.0.0.0'], ['port', 8080]] + list(map(lambda a: a.split('='), sys.argv[1:])))


class MicrohttpdProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, chunk):
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

            self.transport.write(response)

            if not keepalive:
                self.transport.close()


loop = asyncio.get_event_loop()

# Each client connection will create a new protocol instance
coro = loop.create_server(MicrohttpdProtocol, opts['address'], opts['port'])
server = loop.run_until_complete(coro)

try:
    loop.run_forever()
except KeyboardInterrupt:
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
