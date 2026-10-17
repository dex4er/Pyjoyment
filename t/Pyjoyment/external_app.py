import Pyjo.Test.Pyjo

from Pyjo.File import curfile
from Pyjo.Test import *

import os
import sys


# BEGIN { $ENV{MOJO_MODE} = 'testing' }, before the mode of the application is read
os.environ['PYJO_MODE'] = 'testing'

# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# Renamed from Mojolicious: the external applications are in tt/external, where Mojo has them in t/mojolicious/external
sys.path.insert(0, curfile().dirname().dirname().dirname().child('tt', 'external', 'lib').to_str())

t = Pyjo.Test.Pyjo.new('MyApp')

with subtest('Text from config file'):
    t.get_ok('/').status_is(200).content_is('too%21')

with subtest('Static file'):
    t.get_ok('/index.html').status_is(200).content_is('External static file!\n')

with subtest('More text from config file'):
    t.get_ok('/test').status_is(200).content_is('works%21')

# Config override
t = Pyjo.Test.Pyjo.new('MyApp', {'whatever': 'override!', 'works': 'override two!'})

with subtest('Text from config override'):
    t.get_ok('/').status_is(200).content_is('override two!')

with subtest('Static file again'):
    t.get_ok('/index.html').status_is(200).content_is('External static file!\n')

with subtest('More text from config override'):
    t.get_ok('/test').status_is(200).content_is('override!')

with subtest('Config stash value from template'):
    t.get_ok('/inline').status_is(200).content_is('override!')

done_testing()
