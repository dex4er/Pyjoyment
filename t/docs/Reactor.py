from Pyjo.Test import *

import contextlib
import io
import sys


with subtest('Synopsis'):
    import Pyjo.Reactor

    class MyEventLoop(Pyjo.Reactor.object):
        def again(self, id, after=None): ...
        def io(self, handle, cb): ...
        @property
        def is_running(self): ...
        def next_tick(self, cb): ...
        def one_tick(self): ...
        def recurring(self, after, cb): ...
        def remove(self, remove): ...
        def reset(self): ...
        def start(self): ...
        def stop(self): ...
        def timer(self, after, cb): ...
        def watch(self, handle, read, write): ...

    isa_ok(MyEventLoop.new(), Pyjo.Reactor.object, 'subclass')

with subtest('error'):
    reactor = Pyjo.Reactor.new()
    reactor.on('error', lambda reactor, err: ...)
    ok(reactor.has_subscribers('error'), 'subscribed')

    reactor = Pyjo.Reactor.new()
    reactor.on('error', lambda reactor, err: print(f'Something very bad happened: {err}'))
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        reactor.emit('error', 'Oops')
    is_ok(output.getvalue(), 'Something very bad happened: Oops\n', 'handled')

with subtest('detect'):
    name = Pyjo.Reactor.detect()
    is_ok(name, 'Pyjo.Reactor.Asyncio', 'default')

    # Instantiate best reactor implementation available
    reactor = sys.modules[Pyjo.Reactor.detect()].new()
    isa_ok(reactor, Pyjo.Reactor.object, 'reactor')

with subtest('Abstract methods'):
    reactor = Pyjo.Reactor.new()
    for call in (
        lambda: reactor.again('id'),
        lambda: reactor.again('id', 0.5),
        lambda: reactor.io(
            0, lambda reactor, writable: print('Handle is writable' if writable else 'Handle is readable')
        ),
        lambda: reactor.is_running,
        lambda: reactor.next_tick(lambda reactor: None),
        lambda: reactor.one_tick(),
        lambda: reactor.recurring(0.25, lambda reactor: None),
        lambda: reactor.remove(0),
        lambda: reactor.remove('id'),
        lambda: reactor.reset(),
        lambda: reactor.start(),
        lambda: reactor.stop(),
        lambda: reactor.timer(0.5, lambda reactor: None),
        lambda: reactor.watch(0, True, False),
    ):
        throws_ok(call, NotImplementedError, 'meant to be overloaded')

done_testing()
