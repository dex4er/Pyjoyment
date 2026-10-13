import Pyjo.Reactor
import Pyjo.Reactor.Asyncio

from Pyjo.Test import *

import os
import sys
import types


# Dummy reactor
class Pyjo_Reactor_Test(Pyjo.Reactor.Asyncio.object):
    pass


sys.modules['Pyjo.Reactor.Test'] = types.ModuleType('Pyjo.Reactor.Test')
sys.modules['Pyjo.Reactor.Test'].new = Pyjo_Reactor_Test.new

with subtest('Detection (success)'):
    os.environ['PYJO_REACTOR'] = 'Pyjo.Reactor.Test'
    is_ok(Pyjo.Reactor.detect(), 'Pyjo.Reactor.Test', 'right class')
    del os.environ['PYJO_REACTOR']

with subtest('Detection (fail)'):
    os.environ['PYJO_REACTOR'] = 'Pyjo.Reactor.DoesNotExist'
    is_ok(Pyjo.Reactor.detect(), 'Pyjo.Reactor.Asyncio', 'right class')
    del os.environ['PYJO_REACTOR']

with subtest('Event loop detection'):
    os.environ['PYJO_REACTOR'] = 'Pyjo.Reactor.Test'
    import Pyjo.IOLoop

    is_ok(type(Pyjo.IOLoop.new().reactor), Pyjo_Reactor_Test, 'right class')
    del os.environ['PYJO_REACTOR']

done_testing()
