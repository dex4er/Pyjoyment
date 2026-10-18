import Pyjo.Test.Pyjo

from Pyjo.Test import *

import re


# Start a Pyjoyment app named "Celestial"
t = Pyjo.Test.Pyjo.new('Celestial')

# Post a JSON document
t.post_ok('/notifications', json={'event': 'full moon'}).status_is(201).json_is('/message', 'notification created')

# Perform GET requests and look at the responses
t.get_ok('/sunrise').status_is(200).content_like(re.compile(r' am$'))
t.get_ok('/sunset').status_is(200).content_like(re.compile(r' pm$'))

# Post a URL-encoded form
t.post_ok('/insurance', form={'name': 'Jimmy', 'amount': '€3.000.000'}).status_is(200)

# Use like_ok() of Pyjo.Test to check the response
like_ok(t.tx.res.dom().at('div#thanks').text, re.compile(r'thank you'), 'thanks')

done_testing()
