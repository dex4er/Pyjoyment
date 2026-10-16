import Pyjoyment.Routes
import Pyjoyment.Routes.Match
import Pyjoyment.Routes.Pattern

from Pyjo.Test import *

import gc
import re


def match(r, path, method='GET', websocket=False):
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(None, method=method, path=path, websocket=websocket)
    return m


with subtest('Synopsis'):
    import Pyjoyment.Routes.Route

    r = Pyjoyment.Routes.Route.new()
    isa_ok(r, Pyjoyment.Routes.Route.object, 'route')

with subtest('Shortcuts'):
    r = Pyjoyment.Routes.new()

    # Add a "firefox" shortcut
    r.root.add_shortcut('firefox', lambda r, path: r.get(path).requires(agent=re.compile(r'Firefox')))

    # Use "firefox" shortcut to generate routes
    r.firefox('/welcome').to('firefox#welcome')
    r.firefox('/bye').to('firefox#bye')
    is_deeply_ok(r.find('welcome').requires(), [('agent', re.compile(r'Firefox'))], 'condition')
    is_deeply_ok(r.find('bye').to(), {'controller': 'firefox', 'action': 'bye'}, 'destination')

with subtest('children'):
    r = Pyjoyment.Routes.Route.new()
    children = r.children
    is_deeply_ok(children, [], 'default')
    r.children = [Pyjoyment.Routes.Route.new()]
    is_ok(len(r.children), 1, 'set')

with subtest('inline'):
    r = Pyjoyment.Routes.Route.new()
    boolean = r.inline
    is_ok(boolean, None, 'default')
    r.inline = True
    is_ok(r.inline, True, 'set')

with subtest('partial'):
    r = Pyjoyment.Routes.Route.new()
    boolean = r.partial
    is_ok(boolean, None, 'default')
    r.partial = True
    is_ok(r.partial, True, 'set')

with subtest('pattern'):
    r = Pyjoyment.Routes.Route.new()
    pattern = r.pattern
    isa_ok(pattern, Pyjoyment.Routes.Pattern.object, 'default')
    r.pattern = Pyjoyment.Routes.Pattern.new()
    isnt_ok(r.pattern, pattern, 'set')

with subtest('parent'):
    r = Pyjoyment.Routes.Route.new()
    parent = r.parent
    is_ok(parent, None, 'default')
    other = Pyjoyment.Routes.Route.new()
    r.parent = other
    is_ok(r.parent, other, 'set')
    del other
    gc.collect()
    is_ok(r.parent, None, 'weakened')

with subtest('add_child'):
    r = Pyjoyment.Routes.new()
    child = Pyjoyment.Routes.Route.new()
    r = r.add_child(child)
    is_ok(child.parent, r, 'added')

    # Reattach route
    r.get('/foo').get('/bar').set(name='foo')
    r.add_child(r.find('foo'))
    is_ok(r.find('foo').parent, r, 'reattached')

with subtest('any'):
    r = Pyjoyment.Routes.new()
    route = r.any()
    route = r.any('/:foo')
    route = r.any('/:foo', lambda c: ...)
    route = r.any('/:foo', lambda c: ..., 'name')
    is_ok(route.name, 'name', 'name')
    route = r.any('/:foo', {'foo': 'bar'}, lambda c: ...)
    is_ok(route.to()['foo'], 'bar', 'defaults')
    route = r.any('/:foo', lambda c: ..., foo=re.compile(r'\w+'))
    route = r.any(['GET', 'POST'], '/:foo', lambda c: ...)
    is_deeply_ok(route.methods(), ['GET', 'POST'], 'methods')
    route = r.any(['GET', 'POST'], '/:foo', foo=re.compile(r'\w+'))
    is_ok(route.pattern.constraints['foo'], re.compile(r'\w+'), 'constraint')

    r = Pyjoyment.Routes.new()

    # Route with pattern and destination
    r.any('/user').to('user#whatever')

    # Route with HTTP methods, pattern, restrictive placeholders and destination
    r.any(['DELETE', 'PUT'], '/:foo', foo=re.compile(r'\w+')).to('foo#bar')

    # Route with pattern, name and destination
    r.any('/:foo', 'foo_route').to('foo#bar')

    # Route with pattern, condition and destination
    r.any('/').requires(agent=re.compile(r'Firefox')).to('foo#bar')

    # Route with pattern, optional placeholder and destination
    r.any('/:foo', {'foo': 'bar'}).to('foo#bar')

    # Route with pattern and a closure as destination
    r.any('/:foo', lambda c: c.render(text='Hello World!'))

    is_deeply_ok(match(r, '/user').stack, [{'controller': 'user', 'action': 'whatever'}], 'destination')
    is_deeply_ok(match(r, '/baz', 'PUT').stack, [{'controller': 'foo', 'action': 'bar', 'foo': 'baz'}], 'methods')
    is_ok(r.find('foo_route').to_str(), '/:foo', 'name')

with subtest('delete'):
    r = Pyjoyment.Routes.new()
    route = r.delete()
    route = r.delete('/:foo')
    route = r.delete('/:foo', lambda c: ...)
    route = r.delete('/:foo', lambda c: ..., 'name')
    route = r.delete('/:foo', {'foo': 'bar'}, lambda c: ...)
    route = r.delete('/:foo', lambda c: ..., foo=re.compile(r'\w+'))
    is_deeply_ok(route.methods(), ['DELETE'], 'method')

    r = Pyjoyment.Routes.new()

    # Route with destination
    r.delete('/user').to('user#remove')
    is_deeply_ok(match(r, '/user', 'DELETE').stack, [{'controller': 'user', 'action': 'remove'}], 'destination')

with subtest('find'):
    r = Pyjoyment.Routes.new()
    r.get('/user/:id').set(name='show_user')
    route = r.find('foo')
    is_ok(route, None, 'not found')

    # Change default parameters of a named route
    r.find('show_user').to(foo='bar')
    is_deeply_ok(r.find('show_user').to(), {'foo': 'bar'}, 'defaults')

with subtest('get'):
    r = Pyjoyment.Routes.new()
    route = r.get()
    route = r.get('/:foo')
    route = r.get('/:foo', lambda c: ...)
    route = r.get('/:foo', lambda c: ..., 'name')
    route = r.get('/:foo', {'foo': 'bar'}, lambda c: ...)
    route = r.get('/:foo', lambda c: ..., foo=re.compile(r'\w+'))
    is_deeply_ok(route.methods(), ['GET'], 'method')

    r = Pyjoyment.Routes.new()

    # Route with destination
    r.get('/user').to('user#show')
    is_deeply_ok(match(r, '/user').stack, [{'controller': 'user', 'action': 'show'}], 'destination')

with subtest('has_custom_name'):
    r = Pyjoyment.Routes.new()
    boolean = r.get('/foo').has_custom_name
    is_ok(boolean, False, 'generated name')
    is_ok(r.get('/foo', 'bar').has_custom_name, True, 'custom name')

with subtest('has_websocket'):
    r = Pyjoyment.Routes.new()
    boolean = r.websocket('/foo').any('/bar').has_websocket
    is_ok(boolean, True, 'WebSocket ancestor')
    is_ok(r.get('/bar').has_websocket, False, 'no WebSocket')

with subtest('is_endpoint'):
    r = Pyjoyment.Routes.new()
    boolean = r.get('/foo').is_endpoint
    is_ok(boolean, True, 'endpoint')
    is_ok(r.under('/bar').is_endpoint, False, 'not an endpoint')

with subtest('is_reserved'):
    r = Pyjoyment.Routes.new()
    boolean = r.is_reserved('controller')
    is_ok(boolean, True, 'reserved')
    is_ok(r.is_reserved('foo'), False, 'not reserved')

with subtest('is_websocket'):
    r = Pyjoyment.Routes.new()
    boolean = r.websocket('/foo').is_websocket
    is_ok(boolean, True, 'WebSocket')
    is_ok(r.get('/foo').is_websocket, False, 'not a WebSocket')

with subtest('methods'):
    r = Pyjoyment.Routes.new()
    methods = r.methods()
    is_ok(methods, None, 'no restrictions')
    r = r.methods('GET')
    is_deeply_ok(r.methods(), ['GET'], 'one method')
    r = r.methods('GET', 'POST')
    is_deeply_ok(r.methods(), ['GET', 'POST'], 'two methods')
    r = r.methods(['GET', 'POST'])
    is_deeply_ok(r.methods(), ['GET', 'POST'], 'list of methods')

    r = Pyjoyment.Routes.new()

    # Route with two methods and destination
    r.any('/foo').methods('GET', 'POST').to('foo#bar')
    is_deeply_ok(match(r, '/foo', 'POST').stack, [{'controller': 'foo', 'action': 'bar'}], 'POST')

with subtest('name'):
    r = Pyjoyment.Routes.new()
    route = r.get('/user/:id')
    name = route.name
    is_ok(name, 'userid', 'generated name')
    route.name = 'foo'
    is_ok(route.name, 'foo', 'set')

    # Route with destination and custom name
    r.get('/user').to('user#show').set(name='show_user')
    is_ok(r.find('show_user').to_str(), '/user', 'custom name')

with subtest('options'):
    r = Pyjoyment.Routes.new()
    route = r.options()
    route = r.options('/:foo')
    route = r.options('/:foo', lambda c: ...)
    route = r.options('/:foo', lambda c: ..., 'name')
    route = r.options('/:foo', {'foo': 'bar'}, lambda c: ...)
    route = r.options('/:foo', lambda c: ..., foo=re.compile(r'\w+'))
    is_deeply_ok(route.methods(), ['OPTIONS'], 'method')

    r = Pyjoyment.Routes.new()

    # Route with destination
    r.options('/user').to('user#overview')
    is_deeply_ok(match(r, '/user', 'OPTIONS').stack, [{'controller': 'user', 'action': 'overview'}], 'destination')

with subtest('parse'):
    r = Pyjoyment.Routes.Route.new()
    r = r.parse('/user/:id')
    is_ok(r.name, 'userid', 'name')
    r = r.parse('/user/:id', id=re.compile(r'\d+'))
    is_ok(r.pattern.constraints['id'], re.compile(r'\d+'), 'constraint')
    r = r.parse(format=['json', 'yaml'])
    is_deeply_ok(r.pattern.constraints, {'format': ['json', 'yaml']}, 'format')

with subtest('patch'):
    r = Pyjoyment.Routes.new()
    route = r.patch()
    route = r.patch('/:foo')
    route = r.patch('/:foo', lambda c: ...)
    route = r.patch('/:foo', lambda c: ..., 'name')
    route = r.patch('/:foo', {'foo': 'bar'}, lambda c: ...)
    route = r.patch('/:foo', lambda c: ..., foo=re.compile(r'\w+'))
    is_deeply_ok(route.methods(), ['PATCH'], 'method')

    r = Pyjoyment.Routes.new()

    # Route with destination
    r.patch('/user').to('user#update')
    is_deeply_ok(match(r, '/user', 'PATCH').stack, [{'controller': 'user', 'action': 'update'}], 'destination')

with subtest('post'):
    r = Pyjoyment.Routes.new()
    route = r.post()
    route = r.post('/:foo')
    route = r.post('/:foo', lambda c: ...)
    route = r.post('/:foo', lambda c: ..., 'name')
    route = r.post('/:foo', {'foo': 'bar'}, lambda c: ...)
    route = r.post('/:foo', lambda c: ..., foo=re.compile(r'\w+'))
    is_deeply_ok(route.methods(), ['POST'], 'method')

    r = Pyjoyment.Routes.new()

    # Route with destination
    r.post('/user').to('user#create')
    is_deeply_ok(match(r, '/user', 'POST').stack, [{'controller': 'user', 'action': 'create'}], 'destination')

with subtest('put'):
    r = Pyjoyment.Routes.new()
    route = r.put()
    route = r.put('/:foo')
    route = r.put('/:foo', lambda c: ...)
    route = r.put('/:foo', lambda c: ..., 'name')
    route = r.put('/:foo', {'foo': 'bar'}, lambda c: ...)
    route = r.put('/:foo', lambda c: ..., foo=re.compile(r'\w+'))
    is_deeply_ok(route.methods(), ['PUT'], 'method')

    r = Pyjoyment.Routes.new()

    # Route with destination
    r.put('/user').to('user#replace')
    is_deeply_ok(match(r, '/user', 'PUT').stack, [{'controller': 'user', 'action': 'replace'}], 'destination')

with subtest('query'):
    r = Pyjoyment.Routes.new()
    route = r.query()
    route = r.query('/:foo')
    route = r.query('/:foo', lambda c: ...)
    route = r.query('/:foo', lambda c: ..., 'name')
    route = r.query('/:foo', {'foo': 'bar'}, lambda c: ...)
    route = r.query('/:foo', lambda c: ..., foo=re.compile(r'\w+'))
    is_deeply_ok(route.methods(), ['QUERY'], 'method')

    r = Pyjoyment.Routes.new()

    # Route with destination
    r.query('/user').to('user#search')
    is_deeply_ok(match(r, '/user', 'QUERY').stack, [{'controller': 'user', 'action': 'search'}], 'destination')

with subtest('remove'):
    r = Pyjoyment.Routes.new()
    route = r.get('/foo')
    is_ok(route.remove(), route, 'returns the route')
    is_deeply_ok(r.children, [], 'removed')
    r.get('/foo', 'foo')
    r.get('/bar', 'bar')

    # Remove route completely
    r.find('foo').remove()
    is_ok(r.find('foo'), None, 'removed completely')

    # Reattach route to new parent
    r.any('/foo').add_child(r.find('bar').remove())
    is_ok(r.find('bar').to_str(), '/foo/bar', 'reattached')

with subtest('render'):
    r = Pyjoyment.Routes.new()
    path = r.get('/:foo').render({'foo': 'bar'})
    is_ok(path, '/bar', 'path')

with subtest('root'):
    r = Pyjoyment.Routes.new()
    root = r.get('/foo').get('/bar').root
    is_ok(root, r, 'root')

with subtest('requires'):
    routes = Pyjoyment.Routes.new()
    r = routes.get('/foo')
    requires = r.requires()
    is_ok(requires, None, 'no conditions')
    r = r.requires(foo=1)
    is_deeply_ok(r.requires(), [('foo', 1)], 'one condition')
    r = r.requires(foo=1, bar={'baz': 'yada'})
    is_deeply_ok(r.requires(), [('foo', 1), ('bar', {'baz': 'yada'})], 'two conditions')
    r = r.requires([('foo', 1), ('bar', {'baz': 'yada'})])
    is_deeply_ok(r.requires(), [('foo', 1), ('bar', {'baz': 'yada'})], 'list of conditions')
    is_ok(r.root.cache.max_keys, 0, 'cache disabled')

    r = Pyjoyment.Routes.new()

    # Route with condition and destination
    r.get('/foo').requires(host=re.compile(r'mojolicious\.org')).to('foo#bar')
    is_deeply_ok(r.find('foo').requires(), [('host', re.compile(r'mojolicious\.org'))], 'condition')

with subtest('suggested_method'):
    r = Pyjoyment.Routes.new()
    method = r.any('/foo').methods('PUT', 'POST').suggested_method
    is_ok(method, 'POST', 'POST is preferred')
    is_ok(r.any('/bar').suggested_method, 'GET', 'GET is the default')

with subtest('to'):
    r = Pyjoyment.Routes.new().get('/foo')
    defaults = r.to()
    is_deeply_ok(defaults, {}, 'no defaults')
    r = r.to(action='foo')
    r = r.to({'action': 'foo'})
    is_deeply_ok(r.to(), {'action': 'foo'}, 'action')
    r = r.to('controller#action')
    is_deeply_ok(r.to(), {'controller': 'controller', 'action': 'action'}, 'controller and action')
    r = r.to('controller#action', foo='bar')
    r = r.to('controller#action', {'foo': 'bar'})
    is_ok(r.to()['foo'], 'bar', 'with defaults')
    # TODO: the examples of Pyjoyment.new(), when Pyjoyment is ported
    r = r.to('MyApp')
    r = r.to('MyApp', foo='bar')
    r = r.to('MyApp', {'foo': 'bar'})
    is_ok(r.to()['app'], 'MyApp', 'application')

with subtest('to_str'):
    r = Pyjoyment.Routes.new()
    string = r.any('/foo').get('/:bar').to_str()
    is_ok(string, '/foo/:bar', 'whole route')

with subtest('under'):
    r = Pyjoyment.Routes.new()
    route = r.under(lambda c: ...)
    route = r.under('/:foo', lambda c: ...)
    route = r.under('/:foo', {'foo': 'bar'})
    route = r.under('/:foo', foo=re.compile(r'\w+'))
    route = r.under(format=['json', 'yaml'])
    is_ok(route.inline, True, 'inline')

    # Longer version
    route = r.any('/:foo', lambda c: ...).set(inline=True)
    is_ok(route.inline, True, 'inline')

    r = Pyjoyment.Routes.new()

    # Intermediate destination and prefix shared between two routes
    auth = r.under('/user').to('user#auth')
    auth.get('/show').to('#show')
    auth.post('/create').to('#create')
    stack = [{'controller': 'user', 'action': 'auth'}, {'controller': 'user', 'action': 'create'}]
    is_deeply_ok(match(r, '/user/create', 'POST').stack, stack, 'intermediate destination')

with subtest('websocket'):
    r = Pyjoyment.Routes.new()
    route = r.websocket()
    route = r.websocket('/:foo')
    route = r.websocket('/:foo', lambda c: ...)
    route = r.websocket('/:foo', lambda c: ..., 'name')
    route = r.websocket('/:foo', {'foo': 'bar'}, lambda c: ...)
    route = r.websocket('/:foo', lambda c: ..., foo=re.compile(r'\w+'))
    is_ok(route.is_websocket, True, 'WebSocket')

    r = Pyjoyment.Routes.new()

    # Route with destination
    r.websocket('/echo').to('example#echo')
    is_deeply_ok(match(r, '/echo').stack, [], 'no handshake')
    is_deeply_ok(match(r, '/echo', websocket=True).stack, [{'controller': 'example', 'action': 'echo'}], 'handshake')

done_testing()
