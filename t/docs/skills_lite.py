import Pyjo.File
import Pyjo.Test.Pyjo

from Pyjo.Test import *

import importlib
import os
import sys


# The code of plugins/pyjoyment/skills/lite/SKILL.md, each application in a file of its own, as a coding agent writes
# it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
Skills = importlib.import_module('Skills')

code = Skills.blocks('lite')
is_ok(len(code), 4, 'four applications')

tmp = Pyjo.File.tempdir()


def load(n):
    file = tmp.child(f'app{n}.py').spew(code[n])
    t = Pyjo.Test.Pyjo.new(file)
    t.app.log.level = 'fatal'
    return t


with subtest('Routes and responses'):
    t = load(0)
    t.get_ok('/').status_is(200).content_is('Hello World!').header_is('X-Powered-By', 'Pyjoyment')
    t.get_ok('/hello').status_is(200).json_is({'hello': 'World'})
    t.get_ok('/hello/Sara').status_is(200).json_is({'hello': 'Sara'})
    t.get_ok('/users/23').status_is(200).json_is({'id': 23})
    t.get_ok('/users/joe').status_is(404)
    t.get_ok('/files/a/b.txt').status_is(200).content_is('a/b.txt')
    t.get_ok('/report.json').status_is(200).json_is({'total': 1})
    t.get_ok('/report.txt').status_is(200).content_is('total: 1')
    t.get_ok('/report.xml').status_is(404)
    t.post_ok('/users', json={'name': 'Joe'}).status_is(201).json_is({'name': 'Joe'})
    t.get_ok('/old').status_is(302).header_is('Location', '/users/23')

with subtest('Templates, layouts and helpers'):
    t = load(1)
    t.get_ok('/?name=Joe').status_is(200).text_is('title', 'Welcome').text_is('p', 'Hello Joe, welcome!')
    t.get_ok('/').status_is(200).text_is('p', 'Hello stranger, welcome!')

with subtest('Sessions, under and groups'):
    t = load(2)
    t.get_ok('/admin/dashboard').status_is(401).content_is('Log in first')
    t.post_ok('/login', form={'user': 'joe', 'password': 'wrong'}).status_is(403)
    t.post_ok('/login', form={'user': 'joe', 'password': 'secret'}).status_is(302)
    t.header_is('Location', '/admin/dashboard')
    t.get_ok('/admin/dashboard').status_is(200).content_is('Logged in, joe')
    t.get_ok('/admin/dashboard').status_is(200).content_is('Hello, joe')
    t.get_ok('/logout').status_is(302)
    t.get_ok('/admin/dashboard').status_is(401)

with subtest('WebSockets and Server-Sent Events'):
    t = load(3)
    t.websocket_ok('/echo').send_ok('hi').message_ok().message_is('echo: hi').finish_ok()
    t.get_sse_ok('/count').status_is(200).content_type_is('text/event-stream')
    t.sse_ok().sse_text_is('1').sse_ok().sse_text_is('2').sse_ok().sse_text_is('3').sse_finished_ok()

done_testing()
