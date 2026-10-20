import Pyjo.Test.Pyjo

from Pyjo.File import curfile
from Pyjo.Test import *


# The application of examples/title.py, which the test loads without starting a server
t = Pyjo.Test.Pyjo.new(curfile().dirname().dirname().dirname().sibling('examples', 'pyjoyment', 'title.py'))

# A page with a title, in the place of the website of the example, as a test does not request remote hosts
t.app.routes.get('/page', lambda c: c.render(data='<html><head><title>I ♥ Pyjoyment!</title></head></html>'))

with subtest('Template'):
    (
        t.get_ok('/')
        .status_is(200)
        .content_like(r"new WebSocket\('ws://127\.0\.0\.1:\d+/title'\)")
        .content_like(r"ws\.send\('https://mojolicious\.org'\)")
    )

with subtest('Title of a website'):
    page = t.ua.server.url().set(path='/page')
    t.websocket_ok('/title').send_ok(str(page)).message_ok().message_is('I ♥ Pyjoyment!').finish_ok()

done_testing()
