import Pyjo.File
import Pyjo.Server.Daemon
import Pyjo.Test.Pyjo
import Pyjoyment

from Pyjo.Test import *

import importlib
import os
import sys


# The code of plugins/pyjoyment/skills/migration/SKILL.md, each application in a file of its own, as a coding agent
# writes it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
Skills = importlib.import_module('Skills')

code = Skills.blocks('migration')
is_ok(len(code), 3, 'three applications')

tmp = Pyjo.File.tempdir()


def load(n):
    file = tmp.child(f'app{n}.py').spew(code[n])
    t = Pyjo.Test.Pyjo.new(file)
    t.app.log.level = 'fatal'
    return t


# The remote service of the example, which an application of the test answers in its place, as the tests do not use
# the network
remote = Pyjoyment.new()
remote.log.level = 'fatal'
remote.routes.get('/').to(cb=lambda c: c.render(inline='<html><head><title>Example Domain</title></head></html>'))

with subtest('An application'):
    t = load(0)
    t.get_ok('/').status_is(200).content_is('Hello World!')
    t.get_ok('/users/23?full=1').status_is(200).json_is({'id': 23, 'full': True})
    t.get_ok('/users/23').status_is(200).json_is({'id': 23, 'full': False})
    t.get_ok('/users/joe').status_is(404)
    t.post_ok('/users', json={'name': 'Joe'}).status_is(201).json_is({'name': 'Joe'})
    t.get_ok('/me').status_is(302).header_is('Location', '/users/23')

with subtest('Validation, dependencies and middleware'):
    t = load(1)
    t.post_ok('/items', json={'name': 'Pen', 'price': 1.5}).status_is(401).json_is({'error': 'unauthorized'})
    t.post_ok('/items', {'X-User': 'joe'}, json={'name': 'Pen', 'price': 1.5}).status_is(201)
    t.json_is({'item': {'name': 'Pen', 'price': 1.5}, 'by': 'joe'})
    t.post_ok('/items', {'X-User': 'joe'}, json={'name': 'Pen'}).status_is(422).json_has('/errors/0')

with subtest('Requests of other services'):
    with Pyjo.Server.Daemon.new(app=remote, listen=['http://127.0.0.1'], silent=True) as daemon:
        port = daemon.start().ports()[0]
        t = load(2)

        # The requests of the user agent go to the application of the test
        @t.app.ua.on('start')
        def start(ua, tx):
            url = tx.req.url
            url.scheme, url.host, url.port = 'http', '127.0.0.1', port

        t.get_ok('/title').status_is(200).content_is('Example Domain')

done_testing()
