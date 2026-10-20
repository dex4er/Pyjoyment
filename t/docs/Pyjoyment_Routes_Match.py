import Pyjoyment.Controller
import Pyjoyment.Routes.Route

from Pyjo.Test import *


with subtest('Synopsis'):
    import Pyjoyment.Controller
    import Pyjoyment.Routes

    from Pyjoyment.Routes.Match import Match

    # Routes
    r = Pyjoyment.Routes.new()
    r.get('/user/:id')
    r.put('/user/:id')

    # Match
    c = Pyjoyment.Controller.new()
    match = Match(root=r)
    match.find(c, method='PUT', path='/user/23')
    is_ok(match.stack[0]['id'], '23', 'captured')

    import Pyjoyment.Routes
    import Pyjoyment.Routes.Match

    # Routes
    r = Pyjoyment.Routes.new()
    r.get('/user/:id')
    r.put('/user/:id')

    # Match
    c = Pyjoyment.Controller.new()
    match = Pyjoyment.Routes.Match.new(root=r)
    match.find(c, method='PUT', path='/user/23')
    is_ok(match.stack[0]['id'], '23', 'captured')

    # Render
    is_ok(match.path_for()['path'], '/user/23', 'path')
    is_ok(match.path_for(id=24)['path'], '/user/24', 'path with values')

with subtest('endpoint'):
    match = Pyjoyment.Routes.Match.new()
    route = match.endpoint
    is_ok(route, None, 'default')
    match.endpoint = Pyjoyment.Routes.Route.new()
    isa_ok(match.endpoint, Pyjoyment.Routes.Route.object, 'set')

with subtest('position'):
    match = Pyjoyment.Routes.Match.new()
    position = match.position
    is_ok(position, 0, 'default')
    match.position = 2
    is_ok(match.position, 2, 'set')

with subtest('root'):
    match = Pyjoyment.Routes.Match.new()
    root = match.root
    is_ok(root, None, 'default')
    match.root = Pyjoyment.Routes.new()
    isa_ok(match.root, Pyjoyment.Routes.object, 'set')

with subtest('stack'):
    match = Pyjoyment.Routes.Match.new()
    stack = match.stack
    is_deeply_ok(stack, [], 'default')
    match.stack = [{'action': 'foo'}, {'action': 'bar'}]
    is_ok(len(match.stack), 2, 'set')

with subtest('new'):
    r = Pyjoyment.Routes.new()
    match = Pyjoyment.Routes.Match.new(root=r)
    is_ok(match.root, r, 'root')

with subtest('find'):
    r = Pyjoyment.Routes.new()
    r.get('/').to(foo='bar')
    match = Pyjoyment.Routes.Match.new(root=r)
    match.find(Pyjoyment.Controller.new(), method='GET', path='/')
    is_ok(match.endpoint, r.children[0], 'endpoint')

with subtest('path_for'):
    r = Pyjoyment.Routes.new()
    r.get('/:foo/:bar', 'named').to(bar='baz')
    match = Pyjoyment.Routes.Match.new(root=r)
    match.find(Pyjoyment.Controller.new(), method='GET', path='/a/b')
    info = match.path_for()
    is_deeply_ok(info, {'path': '/a/b', 'websocket': False}, 'current route')
    info = match.path_for(foo='bar')
    is_ok(info['path'], '/bar/b', 'values')
    info = match.path_for({'foo': 'bar'})
    is_ok(info['path'], '/bar/b', 'dict of values')
    info = match.path_for('named')
    is_ok(info['path'], '/a/b', 'named route')
    info = match.path_for('named', foo='bar')
    is_ok(info['path'], '/bar/b', 'named route with values')
    info = match.path_for('named', {'foo': 'bar'})
    is_ok(info['path'], '/bar/b', 'named route with a dict of values')

done_testing()
