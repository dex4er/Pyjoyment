import Pyjo.App

from Pyjo.Test import *

import socket


with subtest('Context manager'):
    with Pyjo.App.new() as app:
        port = app.ua.server.url().port
        socket.create_connection(('127.0.0.1', port)).close()
    throws_ok(lambda: socket.create_connection(('127.0.0.1', port)), ConnectionRefusedError, 'server closed at the end')

with subtest('close'):
    app = Pyjo.App.new()
    port = app.ua.server.url().port
    socket.create_connection(('127.0.0.1', port)).close()
    app.close()
    throws_ok(lambda: socket.create_connection(('127.0.0.1', port)), ConnectionRefusedError, 'server closed')

done_testing()
