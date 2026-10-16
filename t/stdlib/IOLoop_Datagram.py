import Pyjo.IOLoop
import Pyjo.IOLoop.Datagram

from Pyjo.Test import *

import asyncio
import os
import socket
import threading


with subtest('A server for a client of the standard library'):
    loop = Pyjo.IOLoop.new()

    @loop.datagram(address='127.0.0.1')
    def id(loop, datagram, id):
        datagram.on('message', lambda datagram, data, peer: datagram.send(data.upper(), peer))

    port = loop.stream(id).port
    got = []

    def client():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(5)
            s.sendto(b'hello', ('127.0.0.1', port))
            got.append(s.recvfrom(100))

    thread = threading.Thread(target=client)
    thread.start()
    loop.recurring(0.01, lambda loop: loop.stop() if not thread.is_alive() else None)
    loop.start()
    thread.join()
    is_deeply_ok(got, [(b'HELLO', ('127.0.0.1', port))], 'echoed')
    loop.reset()

with subtest('A socket of the standard library'):
    loop = Pyjo.IOLoop.new()
    a = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    a.bind(('127.0.0.1', 0))
    b = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    b.bind(('127.0.0.1', 0))
    datagram = Pyjo.IOLoop.Datagram.new(a)
    datagram.reactor = loop.reactor
    got = []

    @datagram.on
    def message(datagram, data, peer):
        got.append((data, peer))
        loop.stop()

    datagram.start()
    b.sendto(b'from the other end', a.getsockname())
    loop.start()
    is_deeply_ok(got, [(b'from the other end', b.getsockname())], 'received')
    datagram.close()
    b.close()

with subtest('A client of asyncio'):
    got = []

    class Protocol(asyncio.DatagramProtocol):
        def connection_made(self, transport):
            self.transport = transport
            transport.sendto(b'asyncio')

        def datagram_received(self, data, addr):
            got.append(data)
            self.transport.close()

    async def main():
        loop = Pyjo.IOLoop.new()
        datagram = loop.stream(
            loop.datagram(
                lambda loop, datagram, id: datagram.on('message', lambda d, data, peer: d.send(data.upper(), peer)),
                address='127.0.0.1',
            )
        )
        transport, _ = await asyncio.get_running_loop().create_datagram_endpoint(
            Protocol, remote_addr=('127.0.0.1', datagram.port)
        )
        for _ in range(100):
            if got:
                break
            await asyncio.sleep(0.01)
        transport.close()
        loop.reset()

    os.environ.pop('PYJO_REACTOR', None)
    asyncio.run(main())
    is_deeply_ok(got, [b'ASYNCIO'], 'the reactor and asyncio in the same loop')

with subtest('Context manager'):
    with Pyjo.IOLoop.Datagram.new() as datagram:
        datagram.bind(address='127.0.0.1')
        handle = datagram.handle
        ok(handle.fileno() >= 0, 'bound')
    is_ok(handle.fileno(), -1, 'socket closed at the end of the block')

done_testing()
