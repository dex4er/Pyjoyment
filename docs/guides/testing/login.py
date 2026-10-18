import Pyjo.Test.Pyjo

from Pyjo.Test import *

import re


t = Pyjo.Test.Pyjo.new('MyApp')

# No authorization cookie
t.get_ok('/').status_is(401).content_is('Please log in')

# Application sets an authorization cookie
t.post_ok('/login', form={'password': 'let me in'}).status_is(200).content_is('You are logged in')

# Sends the cookie from the previous transaction
t.get_ok('/').status_is(200).content_like(re.compile(r'You logged in at \d+'))

# Clear the cookies
t.reset_session()

# No authorization cookie again
t.get_ok('/').status_is(401).content_is('Please log in')

done_testing()
