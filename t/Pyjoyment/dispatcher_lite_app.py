"""
__DATA__
@@ res.txt
Static response!
@@ test.txt
Normal static file!
@@ hello-delay.txt
This is never rendered and overloaded by before_dispatch
"""

import Pyjo.IOLoop
import Pyjo.Message.Response
import Pyjo.Test.Pyjo

from Pyjo.File import tempdir
from Pyjo.Test import *
from Pyjoyment.Lite import app, get, hook, plugin, under

import sys


# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# Unlike Mojolicious: Prove runs every .py file under t, so the plugin of the test is written into a temporary
# directory, where Mojo has it in t/mojolicious/lib
lib = tempdir()
lib.child('AroundPlugin.py').spew("""import Pyjoyment.Plugin


class AroundPlugin(Pyjoyment.Plugin.object):
    def register(self, app, conf=None):
        # Render return value
        @app.hook('around_action')
        def around_action(next, c, action, last):
            value = next()
            if last and c.stash().get('return'):
                c.render(text=value)
            return value


object = AroundPlugin
""")
sys.path.insert(0, lib.to_str())

# Not in Mojolicious: the templates of the DATA section are in the docstring, as the requests come before the end of the
# script


# Internal redirect
@hook('around_dispatch')
def internal_redirect(next, c):
    next()
    if c.res.code and c.res.code == 404:
        c.req.url.path = '/wrap/again' if c.param('wrap') else '/'
        c.stash().clear()
        c.tx.res = Pyjo.Message.Response.new()
        next()


# Wrap whole application
@hook('around_dispatch')
def wrap_again(next, c):
    if c.req.url.path.contains('/wrap/again'):
        return c.render(text='Wrapped again!')
    next()


# Wrap whole application again
@hook('around_dispatch')
def wrap(next, c):
    if c.req.url.path.contains('/wrap'):
        return c.render(text='Wrapped!')
    next()


# Custom dispatcher /hello.txt
@hook('before_dispatch')
def hello(c):
    if c.req.url.path.contains('/hello.txt'):
        c.render(text='Custom static file works!')


# Custom dispatcher /hello-delay.txt
@hook('before_dispatch')
def hello_delay(c):
    if c.req.url.path.contains('/hello-delay.txt'):
        c.render_later()
        Pyjo.IOLoop.next_tick(lambda loop: c.render(text='Delayed!'))


# Custom dispatcher /custom
@hook('before_dispatch')
def custom(c):
    if c.req.url.path.contains('/custom'):
        c.render_maybe() or c.render(text=c.param('a'), status=205)


# Custom dispatcher /custom_too
@hook('before_routes')
def custom_too(c):
    if c.req.url.path.contains('/custom_too'):
        c.render(text='this works too')


# Cleared response for /res.txt
@hook('before_routes')
def res_txt(c):
    if not (c.req.url.path.contains('/res.txt') and c.param('route')):
        return
    c.tx.res = Pyjo.Message.Response.new()


# Set additional headers for static files
@hook('after_static')
def after_static(c):
    c.res.headers.cache_control = 'max-age=3600, must-revalidate'


# Make controller available as _
_ = None


@hook('around_action')
def around_action(next, c, action, last):
    global _
    # The value of local, which is set back
    saved, _ = _, c
    try:
        return next()
    finally:
        _ = saved


# Plugin for rendering return values
plugin('AroundPlugin')


# Pass argument to action
@hook('around_action')
def pass_argument(next, c, action, last):
    return action(c, c.current_route())


# Response generating condition "res" for /res.txt
def res(route, c, captures, arg):
    if not c.param('res'):
        return True
    res = Pyjo.Message.Response.new(code=201)
    res.body = b'Conditional response!'
    c.tx.res = res
    c.rendered()
    return None


app.routes.add_condition('res', res)


# Never called if custom dispatchers work
get('/custom', lambda c: c.render(text='does not work'))


# Custom response
def res_txt_action(c, *args):
    res = Pyjo.Message.Response.new(code=202)
    res.body = b'Custom response!'
    _.tx.res = res
    _.rendered()


get('/res.txt', res_txt_action).requires(res=1)


# Allow rendering of return value
under('/', {'return': 1}, lambda c, *args: True)

# Return and render argument
get('/', lambda c, *args: args[-1], 'works')

t = Pyjo.Test.Pyjo.new()

with subtest('Normal route'):
    (t.get_ok('/').status_is(200).header_isnt('Cache-Control', 'max-age=3600, must-revalidate').content_is('works'))

with subtest('Normal static file'):
    (
        t.get_ok('/test.txt')
        .status_is(200)
        .header_is('Cache-Control', 'max-age=3600, must-revalidate')
        .content_is('Normal static file!\n')
    )

with subtest('Override static file'):
    t.get_ok('/hello.txt').status_is(200).content_is('Custom static file works!')

with subtest('render_later from before_dispatch'):
    t.get_ok('/hello-delay.txt').status_is(200).content_is('Delayed!')

with subtest('Custom dispatcher'):
    t.get_ok('/custom?a=works+too').status_is(205).content_is('works too')

with subtest('Static file'):
    (
        t.get_ok('/res.txt')
        .status_is(200)
        .header_is('Cache-Control', 'max-age=3600, must-revalidate')
        .content_is('Static response!\n')
    )

with subtest(' Custom response'):
    (
        t.get_ok('/res.txt?route=1')
        .status_is(202)
        .header_isnt('Cache-Control', 'max-age=3600, must-revalidate')
        .content_is('Custom response!')
    )

with subtest('Conditional response'):
    (
        t.get_ok('/res.txt?route=1&res=1')
        .status_is(201)
        .header_isnt('Cache-Control', 'max-age=3600, must-revalidate')
        .content_is('Conditional response!')
    )

with subtest('Another custom dispatcher'):
    (
        t.get_ok('/custom_too')
        .status_is(200)
        .header_isnt('Cache-Control', 'max-age=3600, must-revalidate')
        .content_is('this works too')
    )

with subtest('First wrapper'):
    t.get_ok('/wrap').status_is(200).content_is('Wrapped!')

with subtest('Second wrapper'):
    t.get_ok('/wrap/again').status_is(200).content_is('Wrapped again!')

with subtest('Internal redirect to root'):
    t.get_ok('/not_found').status_is(200).content_is('works')

with subtest('Internal redirect to second wrapper'):
    t.get_ok('/not_found?wrap=1').status_is(200).content_is('Wrapped again!')

done_testing()
