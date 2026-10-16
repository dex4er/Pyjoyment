import Pyjo.Test.Pyjo

from Pyjo.Test import *
from Pyjoyment.Lite import app, get


# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# More paths with higher precedence
app.renderer.paths.insert(0, app.home.child('templates2').to_str())
app.static.paths.insert(0, app.home.child('public2').to_str())

get('/twenty_three', '23')

get('/fourty_two', '42')

get('/fourty_two_again', {'template': '42', 'variant': 'test'})

get('/yada', {'template': 'foo/yada'})

t = Pyjo.Test.Pyjo.new()

with subtest('"templates" directory'):
    t.get_ok('/twenty_three').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('23\n')

with subtest('"templates2" directory'):
    (t.get_ok('/fourty_two').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('The answer is 42.\n'))

with subtest('"templates2" directory (variant)'):
    (
        t.get_ok('/fourty_two_again')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_is('The answer is 43!\n')
    )

with subtest('"public2" directory'):
    (
        t.get_ok('/hello.txt')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_is('Also higher precedence!\n')
    )

with subtest('"public" directory'):
    t.get_ok('/hello2.txt').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('X')

with subtest('"public2" directory'):
    (
        t.get_ok('/hello3.txt')
        .status_is(200)
        .header_is('Server', 'Pyjoyment (Python)')
        .content_is('Hello Mojo from... ALL GLORY TO THE HYPNOTOAD!\n')
    )

with subtest('"templates2" directory'):
    t.get_ok('/yada').status_is(200).header_is('Server', 'Pyjoyment (Python)').content_is('Higher precedence!\n')

done_testing()
