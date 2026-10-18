import Pyjo.IOLoop
import Pyjoyment
import Pyjoyment.Command.fastcgi

from Pyjo.Test import *

import os
import signal
import socket
import struct
import threading


def record(type, id, content=b''):
    padding = -len(content) % 8
    return struct.pack('>BBHHBx', 1, type, id, len(content), padding) + content + b'\0' * padding


def fastcgi(port, results):
    # A request of a web server, in a thread of its own, as the command runs the event loop
    params = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1'}
    pairs = b''.join(bytes([len(n), len(v)]) + n.encode() + v.encode() for n, v in params.items())
    data = record(1, 1, struct.pack('>HB5x', 1, 0)) + record(4, 1, pairs) + record(4, 1) + record(5, 1)
    with socket.create_connection(('127.0.0.1', port), timeout=10) as conn:
        conn.sendall(data)
        output = b''
        while chunk := conn.recv(65536):
            output += chunk
    results.append(output)


with subtest('Synopsis'):
    fastcgi_command = Pyjoyment.Command.fastcgi.new()
    like_ok(fastcgi_command.usage, r'^Usage: APPLICATION fastcgi \[OPTIONS\]\n\n  \./myapp\.py fastcgi\n', 'usage')

with subtest('Attributes'):
    fastcgi_command = Pyjoyment.Command.fastcgi.new()
    is_ok(fastcgi_command.description, 'Start application with FastCGI of the web server', 'description')

with subtest('run'):
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    app.routes.get('/', {'text': 'Hello FastCGI!'})

    # The listen socket of the web server as the file descriptor 0
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        listener.listen()
        results = []
        worker = threading.Thread(target=fastcgi, args=(listener.getsockname()[1], results))
        stdin = os.dup(0)
        try:
            os.dup2(listener.fileno(), 0)
            worker.start()
            Pyjo.IOLoop.recurring(0.05, lambda loop: worker.is_alive() or os.kill(os.getpid(), signal.SIGQUIT))
            Pyjoyment.Command.fastcgi.new(app=app).run()
        finally:
            os.dup2(stdin, 0)
            os.close(stdin)
        worker.join()
    is_ok(len(results), 1, 'served')
    like_ok(results[0], rb'Status: 200 OK\r\n', 'status')
    like_ok(results[0], rb'Hello FastCGI!', 'output')

done_testing()
