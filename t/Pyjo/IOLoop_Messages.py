import Pyjo.IOLoop
import Pyjo.IOLoop.ChildProcess
import Pyjo.IOLoop.Messages
import Pyjo.IOLoop.Stream

from Pyjo.Test import *

import os
import re
import socket
import sys


# Not in Mojolicious: messages on a stream
PYTHON = sys.executable


# The messages of a framing in a buffer, until there is none
def take(framing, buffer, max_size=0):
    decoded = []
    while (message := framing.decode(buffer, max_size)) is not None:
        decoded.append(message)
    return decoded


# Each message of what has been read, a byte at a time, and all at once
def decode(framing_class, data, max_size=0, **kwargs):
    framing, decoded, buffer = framing_class(**kwargs), [], bytearray()
    for byte in data:
        buffer.append(byte)
        decoded += take(framing, buffer, max_size)
    framing, buffer = framing_class(**kwargs), bytearray(data)
    return decoded, take(framing, buffer, max_size), bytes(buffer)


def failure(framing, data, max_size):
    try:
        take(framing, bytearray(data), max_size)
    except Exception as e:
        return e.message
    return None


# Two streams of a pair of sockets, which the singleton watches
def pair():
    a, b = socket.socketpair()
    a.setblocking(False)
    b.setblocking(False)
    streams = Pyjo.IOLoop.Stream.new(a), Pyjo.IOLoop.Stream.new(b)
    for stream in streams:
        stream.start()
    return streams


def run(timeout=10):
    timer = Pyjo.IOLoop.timer(timeout, lambda loop: Pyjo.IOLoop.stop())
    Pyjo.IOLoop.start()
    Pyjo.IOLoop.remove(timer)


with subtest('Lines'):
    messages, whole, rest = decode(Pyjo.IOLoop.Messages.Lines, b'one\ntwo\r\n\nthree')
    is_deeply_ok(messages, [b'one', b'two', b''], 'split across reads')
    is_deeply_ok(whole, [b'one', b'two', b''], 'several in one read')
    is_ok(rest, b'three', 'rest')
    framing = Pyjo.IOLoop.Messages.Lines.new()
    is_ok(framing.encode(b'one'), b'one\n', 'line feed')
    is_ok(Pyjo.IOLoop.Messages.Lines.new(terminator=b'\r\n').encode(b'one'), b'one\r\n', 'carriage return')
    is_ok(failure(framing, b'12345\n', 5), None, 'line of the maximum size')
    is_ok(failure(Pyjo.IOLoop.Messages.Lines(), b'12345\r\n', 5), None, 'carriage return of the maximum size')
    is_ok(failure(Pyjo.IOLoop.Messages.Lines(), b'123456\n', 5), 'Maximum message size exceeded', 'too long')
    is_ok(failure(Pyjo.IOLoop.Messages.Lines(), b'123456', 5), 'Maximum message size exceeded', 'too long already')
    is_ok(failure(Pyjo.IOLoop.Messages.Lines(), b'12345\r', 5), None, 'carriage return still to end')
    throws_ok(lambda: framing.encode(b'one\ntwo'), re.compile(r'^Message with a line feed$'), 'no line feed')

with subtest('Lines in a long buffer'):
    framing = Pyjo.IOLoop.Messages.Lines()
    buffer = bytearray()
    decoded = []
    for _ in range(100):
        buffer += b'x' * 1000
        decoded += take(framing, buffer)
    is_deeply_ok(decoded, [], 'no line yet')
    buffer += b'\nnext'
    is_deeply_ok(take(framing, buffer), [b'x' * 100000], 'whole line')
    is_ok(bytes(buffer), b'next', 'rest')

with subtest('Content-Length'):
    data = b'Content-Length: 3\r\n\r\none' + b'content-type: application/json\r\nCONTENT-LENGTH:  2 \r\n\r\n{}'
    messages, whole, rest = decode(Pyjo.IOLoop.Messages.ContentLength, data + b'Content-Length: 5\r\n\r\nthr')
    is_deeply_ok(messages, [b'one', b'{}'], 'split across reads')
    is_deeply_ok(whole, [b'one', b'{}'], 'several in one read')
    is_ok(rest, b'thr', 'rest')
    messages, whole, rest = decode(Pyjo.IOLoop.Messages.ContentLength, b'Content-Length: 0\r\n\r\n')
    is_deeply_ok(whole, [b''], 'empty')
    framing = Pyjo.IOLoop.Messages.ContentLength.new()
    is_ok(framing.encode(b'{"a":1}'), b'Content-Length: 7\r\n\r\n{"a":1}', 'frame')
    is_ok(failure(framing, b'Content-Length: 6\r\n\r\n', 5), 'Maximum message size exceeded', 'too long')
    is_ok(failure(framing, b'Content-Length: 5\r\n\r\n', 5), None, 'maximum size')
    is_ok(failure(framing, b'Content-Type: text/plain\r\n\r\n', 5), 'Message without Content-Length', 'no length')
    is_ok(failure(framing, b'Content-Length: x\r\n\r\n', 5), 'Message without Content-Length', 'invalid length')
    is_ok(failure(framing, b'X: ' + b'x' * 8192, 0), 'Maximum header size exceeded', 'headers too long')

with subtest('Length prefix'):
    data = (3).to_bytes(4, sys.byteorder) + b'one' + (0).to_bytes(4, sys.byteorder) + (2).to_bytes(4, sys.byteorder)
    messages, whole, rest = decode(Pyjo.IOLoop.Messages.LengthPrefix, data + b'x')
    is_deeply_ok(messages, [b'one', b''], 'split across reads')
    is_deeply_ok(whole, [b'one', b''], 'several in one read')
    is_ok(rest, (2).to_bytes(4, sys.byteorder) + b'x', 'rest')
    messages, whole, rest = decode(Pyjo.IOLoop.Messages.LengthPrefix, b'\x00\x03one', size=2, byteorder='big')
    is_deeply_ok(whole, [b'one'], 'two bytes in big endian')
    framing = Pyjo.IOLoop.Messages.LengthPrefix.new()
    is_ok(framing.encode(b'one'), (3).to_bytes(4, sys.byteorder) + b'one', 'native byte order')
    is_ok(failure(framing, (6).to_bytes(4, sys.byteorder), 5), 'Maximum message size exceeded', 'too long')
    throws_ok(
        lambda: Pyjo.IOLoop.Messages.LengthPrefix.new(size=1).encode(b'x' * 256),
        re.compile(r'^Message too large for its length$'),
        'too long for its length',
    )

with subtest('Messages on a stream'):
    a, b = pair()
    server = Pyjo.IOLoop.Messages.new(a)
    client = Pyjo.IOLoop.Messages.new(b)
    is_ok(server.stream, a, 'stream')
    is_ok(server.output, a, 'output')
    isa_ok(server.framing, Pyjo.IOLoop.Messages.Lines, 'lines by default')
    got = []
    server.on('message', lambda messages, message: messages.send(message.upper()))
    client.on('message', lambda messages, message: (got.append(message), len(got) == 3 and Pyjo.IOLoop.stop()))
    drained = []
    client.send(b'one').send('zwei ü').send(b'three', lambda messages: drained.append(messages))
    run()
    is_deeply_ok(got, [b'ONE', b'ZWEI \xc3\xbc', b'THREE'], 'right messages')
    is_deeply_ok(drained, [client], 'drain callback with the messages')
    closed = []
    server.on('close', lambda messages: closed.append('server'))
    client.on('close', lambda messages: (closed.append('client'), Pyjo.IOLoop.stop()))
    server.close_gracefully()
    run()
    is_deeply_ok(closed, ['server', 'client'], 'closed')
    is_deeply_ok(a.subscribers('read'), [], 'no subscribers left')

with subtest('Message over the maximum size'):
    a, b = pair()
    server = Pyjo.IOLoop.Messages.new(a, framing=Pyjo.IOLoop.Messages.ContentLength())
    is_ok(server.max_message_size, 16777216, 'default')
    server.max_message_size = 5
    events = []
    server.on('message', lambda messages, message: events.append(message))
    server.on('error', lambda messages, err: events.append(err.message))
    server.on('close', lambda messages: (events.append('close'), Pyjo.IOLoop.stop()))
    b.write(b'Content-Length: 5\r\n\r\n12345Content-Length: 6\r\n\r\n123456')
    run()
    is_deeply_ok(events, [b'12345', 'Maximum message size exceeded', 'close'], 'right events')
    b.close()

with subtest('Maximum size from the environment'):
    os.environ['PYJO_MAX_MESSAGE_SIZE'] = '10'
    try:
        a, b = pair()
        is_ok(Pyjo.IOLoop.Messages.new(a).max_message_size, 10, 'right size')
    finally:
        del os.environ['PYJO_MAX_MESSAGE_SIZE']
    a.close()
    b.close()

with subtest('Framing of its own'):

    class Netstrings:
        def decode(self, buffer, max_size):
            if (colon := buffer.find(b':')) < 0:
                return None
            length = int(buffer[:colon])
            if len(buffer) < colon + length + 2:
                return None
            message = bytes(buffer[colon + 1 : colon + 1 + length])
            del buffer[: colon + length + 2]
            return message

        def encode(self, message):
            return b'%d:%s,' % (len(message), message)

    a, b = pair()
    server = Pyjo.IOLoop.Messages.new(a, framing=Netstrings())
    client = Pyjo.IOLoop.Messages.new(b, framing=Netstrings())
    got = []
    server.on('message', lambda messages, message: messages.send(message[::-1]))
    client.on('message', lambda messages, message: (got.append(message), Pyjo.IOLoop.stop()))
    client.send(b'abc')
    run()
    is_deeply_ok(got, [b'cba'], 'right message')
    a.close()
    b.close()

if os.name != 'nt':
    with subtest('Standard output and input of a child process'):
        code = 'import sys\nfor line in sys.stdin:\n    print(line.strip().upper(), flush=True)\n'
        child = Pyjo.IOLoop.ChildProcess.new().spawn([PYTHON, '-c', code])
        messages = Pyjo.IOLoop.Messages.new(child.stdout, output=child.stdin)
        is_ok(messages.output, child.stdin, 'output')
        got = []
        messages.on('message', lambda messages, message: (got.append(message), messages.close_gracefully()))
        messages.on('close', lambda messages: got.append('close'))
        child.on('close', lambda child, code, signal: Pyjo.IOLoop.stop())
        messages.send('hello')
        run()
        is_deeply_ok(got, [b'HELLO', 'close'], 'right messages')
        is_ok(child.exit_code, 0, 'child process has ended')

    with subtest('Output of a child process closed before its responses'):
        code = 'import sys, time\nlines = list(sys.stdin)\ntime.sleep(0.2)\nprint("".join(lines).upper(), end="")\n'
        child = Pyjo.IOLoop.ChildProcess.new().spawn([PYTHON, '-c', code])
        messages = Pyjo.IOLoop.Messages.new(child.stdout, output=child.stdin)
        got = []
        messages.on('message', lambda messages, message: got.append(message))
        messages.on('close', lambda messages: got.append('close'))
        child.on('close', lambda child, code, signal: Pyjo.IOLoop.stop())
        messages.send('one').send('two').close_gracefully()
        run()
        is_deeply_ok(got, [b'ONE', b'TWO', 'close'], 'responses after the end of the requests')

    with subtest('End of the output of a child process'):
        child = Pyjo.IOLoop.ChildProcess.new().spawn([PYTHON, '-c', 'print("one")'])
        messages = Pyjo.IOLoop.Messages.new(child.stdout, output=child.stdin)
        got = []
        messages.on('message', lambda messages, message: got.append(message))
        messages.on('close', lambda messages: got.append('close'))
        child.on('close', lambda child, code, signal: Pyjo.IOLoop.stop())
        run()
        is_deeply_ok(got, [b'one', 'close'], 'right messages')
        is_ok(child.stdin.handle, None, 'input closed')

done_testing()
