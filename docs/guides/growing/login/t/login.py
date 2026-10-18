import Pyjo.Test.Pyjo

from Pyjo.Test import *

import re


t = Pyjo.Test.Pyjo.new('MyApp')
t.ua.max_redirects = 1

with subtest('Test login workflow'):
    (
        t.get_ok('/')
        .status_is(200)
        .element_exists('form input[name="user"]')
        .element_exists('form input[name="pass"]')
        .element_exists('form input[type="submit"]')
    )

    (
        t.post_ok('/', form={'user': 'sebastian', 'pass': 'secr3t'})
        .status_is(200)
        .text_like('html body', re.compile(r'Welcome sebastian'))
    )

    t.get_ok('/protected').status_is(200).text_like('a', re.compile(r'Logout'))

    (
        t.get_ok('/logout')
        .status_is(200)
        .element_exists('form input[name="user"]')
        .element_exists('form input[name="pass"]')
        .element_exists('form input[type="submit"]')
    )

done_testing()
