# ka.py PORT N: GET / on one connection, one request at a time, N requests after a warmup
#
# Reads the response by Content-Length and opens a new connection when the server closes it
# (Connection: close, or HTTP/1.0 without keep-alive). RECONNECT=1 opens a new connection for
# every request, WARMUP sets the number of requests before the measurement (default 1000).
import os
import socket
import sys
import time


port, n = int(sys.argv[1]), int(sys.argv[2])
reconnect = bool(os.environ.get('RECONNECT'))
req = b'GET / HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n'
sock = None
connections = 0


def connect():
    global sock, connections
    if sock is not None:
        sock.close()
    sock = socket.create_connection(('127.0.0.1', port))
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    connections += 1


def one():
    sock.sendall(req)
    buf = b''
    while b'\r\n\r\n' not in buf:
        buf += sock.recv(65536)
    head, _, body = buf.partition(b'\r\n\r\n')
    head = head.lower()
    length = int(head.split(b'content-length: ')[1].split(b'\r\n')[0])
    while len(body) < length:
        body += sock.recv(65536)
    if (
        reconnect
        or b'connection: close' in head
        or (head.startswith(b'http/1.0') and b'connection: keep-alive' not in head)
    ):
        connect()


connect()
for _ in range(int(os.environ.get('WARMUP', 1000))):
    one()
connections = 0
start = time.perf_counter()
for _ in range(n):
    one()
elapsed = time.perf_counter() - start
mode = 'new connection' if reconnect else 'keep-alive'
print(f'{mode}: {n / elapsed:.0f} req/s, {elapsed / n * 1e6:.0f} us/req, {connections} connections')
