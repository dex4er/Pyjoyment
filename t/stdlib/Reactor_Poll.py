import Pyjo.Reactor.Poll

from Pyjo.Test import *

import socket

from unittest.mock import patch


def events(reactor, handle, read, write, timeout=5):
    # The events of the handle until the first one, or the timeout
    got = []

    def cb(reactor, writable):
        got.append('writable' if writable else 'readable')
        reactor.stop()

    reactor.io(handle, cb).watch(handle, read, write)
    reactor.timer(timeout, lambda reactor: reactor.stop())
    reactor.start()
    reactor.remove(handle)
    return got


# select, as Windows has it in the place of poll, on every system
with subtest('select in the place of poll'), patch.object(Pyjo.Reactor.Poll, '_poll', Pyjo.Reactor.Poll._select):
    reactor = Pyjo.Reactor.Poll.new()
    a, b = socket.socketpair()
    is_deeply_ok(events(reactor, a, False, True), ['writable'], 'writable')
    b.send(b'x')
    is_deeply_ok(events(reactor, a, True, False), ['readable'], 'readable')
    a.close()
    b.close()

    # A connection that failed is an exceptional condition of select on Windows
    with socket.socket() as listen:
        listen.bind(('127.0.0.1', 0))
        port = listen.getsockname()[1]
    client = socket.socket()
    client.setblocking(False)
    client.connect_ex(('127.0.0.1', port))
    ok(len(events(reactor, client, False, True)), 'refused connection')
    client.close()

    # A handle that is closed is invalid, as poll reports it
    a, b = socket.socketpair()
    fd = a.fileno()
    reactor.io(fd, lambda reactor, writable: (got.append(writable), reactor.stop())).watch(fd, True, False)
    got = []
    a.close()
    reactor.timer(5, lambda reactor: reactor.stop())
    reactor.start()
    is_deeply_ok(got, [False], 'closed handle')
    b.close()

done_testing()
