"""
__DATA__
@@ index.html.ep
<%= config()['foo'] %><%= config()['bar'] %>
"""

import Pyjo.Test.Pyjo

from Pyjo.Test import *
from Pyjoyment.Lite import get, plugin

import os


# BEGIN { $ENV{MOJO_MODE} = 'testing' }, before the mode of the application is read
os.environ['PYJO_MODE'] = 'testing'

# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# Load plugin
plugin('JSONConfig')

get('/', 'index')

t = Pyjo.Test.Pyjo.new()

with subtest('Template with config information'):
    t.get_ok('/').status_is(200).content_like(r'bazfoo')

done_testing()
