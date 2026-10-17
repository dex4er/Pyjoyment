#!/usr/bin/env python
"""
__DATA__

@@ menubar.html.ep
%= same_name()
<%= config()['just'] %><%= config()['one'] %><%= config()['two'] %>
"""

from Pyjoyment.Lite import app, get, helper, plugin, websocket


# Default for config file tests
app.defaults(secret='Insecure!')

# Helpers sharing the same name in different embedded applications
helper('same_name', lambda c: 'myapp')

# Load plugin
config = plugin('Config')
one = config.get('one')


# Message condition
def message(route, c, captures, msg):
    c.res.headers.header('X-Message', msg)
    return True


app.routes.add_condition('message', message)

get('/', 'index')

get('/startup', {'text': one})


@get('/echo')
def echo(c):
    c.render(text='echo: ' + (c.stash('message') or 'nothing!'))


@get('/stream')
def stream(c):
    c.write_chunk(b'he', lambda c: c.write_chunk(b'll', lambda c: c.finish(b'o!')))


@get('/url/☃')
def url(c):
    route = c.url_for({'format': 'json'})
    rel = c.url_for('/☃/stream')
    c.render(text=f'{route} -> {rel}!')


@get('/host')
def host(c):
    c.render(text=c.url_for().base.host)


host.requires(message='it works!')

get('/one', lambda c: c.render(text='One'))

get('/one/two', {'text': 'Two'})


@get('/template/:foo')
def template(c):
    c.render(c.param('foo'))


@websocket('/url_for', 'ws_test')
def url_for(c):
    @c.on('message')
    def message(c, msg):
        c.send(str(c.url_for(msg).to_abs()))


app.start()
