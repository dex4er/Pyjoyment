import Pyjo.File
import Pyjo.Test.Pyjo

from Pyjo.Test import *

import re


# Include application
script = Pyjo.File.curfile().dirname().sibling('myapp.py')

# Allow 302 redirect responses
t = Pyjo.Test.Pyjo.new(script)
t.ua.max_redirects = 1

# Test if the HTML login form exists
(
    t.get_ok('/')
    .status_is(200)
    .element_exists('form input[name="user"]')
    .element_exists('form input[name="pass"]')
    .element_exists('form input[type="submit"]')
)

# Test login with valid credentials
(
    t.post_ok('/', form={'user': 'sebastian', 'pass': 'secr3t'})
    .status_is(200)
    .text_like('html body', re.compile(r'Welcome sebastian'))
)

# Test accessing a protected page
t.get_ok('/protected').status_is(200).text_like('a', re.compile(r'Logout'))

# Test if HTML login form shows up again after logout
(
    t.get_ok('/logout')
    .status_is(200)
    .element_exists('form input[name="user"]')
    .element_exists('form input[name="pass"]')
    .element_exists('form input[type="submit"]')
)

done_testing()
