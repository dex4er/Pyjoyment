"""
__DATA__

@@ hidden.html.ep
%= include('menu')

@@ menu.html.ep
<p>Menu</p>

@@ helper_in_template.html.ep
%= ua.get_p('/')

@@ stashed.html.ep
<p><%= name %></p>
"""

import Pyjo.Test.Pyjo
import Pyjo.Transaction.HTTP

from Pyjo.Test import *
from Pyjoyment.Lite import *


# Not in Mojolicious: the hints of the messages of the mistakes that Python makes likely, as a helper without its call
# or the response that an action returns, as a view of another framework does, which Perl does not have


@get('/helper')
def helper(c):
    c.ua.get_p('/')


@get('/helper_in_template')
def helper_in_template(c):
    c.render('helper_in_template')


@get('/attribute')
def attribute(c):
    c.request.url


@get('/nested')
def nested(c):
    c.reply.notfound()


@get('/placeholder/:id')
def placeholder(c, id):
    c.render(text=id)


@get('/without')
def without():
    pass


@get('/text')
def text(c):
    return 'Hello'


@get('/dict')
def dict_(c):
    return {'hello': 'world'}


@get('/stashed')
def stashed(c):
    return c.stash(name='works')


@get('/rendered')
def rendered(c):
    c.render(text='rendered')
    return 'ignored'


@get('/hidden')
def hidden(c):
    c.render('hidden', include='x')


t = Pyjo.Test.Pyjo.new()

with subtest('Helper without its call'):
    t.get_ok('/helper').status_is(500)
    t.content_like(r'^Helper "ua" has no attribute "get_p", call the helper first: ua\(\)\.get_p')
    t.get_ok('/helper_in_template').status_is(500)
    t.content_like(r'^Helper "ua" has no attribute "get_p", call the helper first: ua\(\)\.get_p')
    try:
        app.validation.required
    except AttributeError as e:
        err = e
    like_ok(
        str(err),
        r'^Helper "validation" has no attribute "required", call the helper first: validation\(\)\.required$',
        'application',
    )

with subtest('Name of another framework'):
    t.get_ok('/attribute').status_is(500)
    t.content_like(r'^Can\'t locate object method "request" via package .* Did you mean "req"\?')
    t.get_ok('/nested').status_is(500)
    t.content_like(r'^Can\'t locate object method "notfound" via package .* Did you mean "not_found"\?')
    try:
        app.rotes
    except AttributeError as e:
        err = e
    like_ok(str(err), r'^Can\'t locate object method "rotes" via package .* Did you mean "routes"\?', 'application')

with subtest('Arguments of an action'):
    t.get_ok('/placeholder/23').status_is(500)
    t.content_like(r"missing 1 required positional argument: 'id': an action gets the controller only")
    t.get_ok('/without').status_is(500)
    t.content_like(r'takes 0 positional arguments but 1 was given: an action gets the controller only')

with subtest('Response that an action returns'):
    t.get_ok('/text').status_is(500)
    t.content_like(r'^Action returned a str, which is not a response: c\.render\(text=\.\.\.\) renders a text')
    t.get_ok('/dict').status_is(500).content_like(r'^Action returned a dict, which is not a response')
    t.get_ok('/stashed').status_is(200).content_is('<p>works</p>\n')
    t.get_ok('/rendered').status_is(200).content_is('rendered')

with subtest('Value of the stash that hides a helper'):
    t.get_ok('/hidden').status_is(500)
    t.content_like(r'not callable, the value "include" of the stash hides the helper include\(\)')

with subtest('Arguments of a callback of an event'):
    tx = Pyjo.Transaction.HTTP.new()
    c = app.build_controller(tx)
    c.on('finish', lambda: None)
    try:
        c.tx.emit('finish')
    except TypeError as e:
        err = e
    like_ok(str(err), r'given: the callbacks of the event "finish" get the controller first$', 'hint')

done_testing()
