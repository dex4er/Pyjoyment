import Pyjo.Test.Pyjo
import Pyjoyment

from Pyjo.Test import *

import socket


with subtest('Context manager'):
    app = Pyjoyment.new()
    app.routes.any('/', {'text': 'works'})
    with Pyjo.Test.Pyjo.new(app) as t:
        t.get_ok('/').content_is('works')
        port = t.ua.server.url().port
    throws_ok(lambda: socket.create_connection(('127.0.0.1', port)), ConnectionRefusedError, 'server closed at the end')

done_testing()
