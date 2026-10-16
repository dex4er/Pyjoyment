import Pyjo.Cache
import Pyjoyment.Routes.Match

from Pyjo.Test import *

import re


def match(r, path, method='GET'):
    m = Pyjoyment.Routes.Match.new(root=r)
    m.find(None, method=method, path=path)
    return m.stack


with subtest('Synopsis'):
    import Pyjoyment.Routes

    # Simple route
    r = Pyjoyment.Routes.new()
    r.any('/').to(controller='blog', action='welcome')

    # More advanced routes
    blog = r.under('/blog')
    blog.get('/list').to('blog#list')
    blog.get('/:id', id=re.compile(r'\d+')).to('blog#show', id=23)
    blog.patch(lambda c: c.render(text='Go away!', status=405))

    is_deeply_ok(match(r, '/'), [{'controller': 'blog', 'action': 'welcome'}], 'simple route')
    is_deeply_ok(match(r, '/blog/list'), [{}, {'controller': 'blog', 'action': 'list'}], 'nested route')
    is_deeply_ok(match(r, '/blog/24'), [{}, {'controller': 'blog', 'action': 'show', 'id': '24'}], 'placeholder')
    is_deeply_ok(match(r, '/blog/foo'), [], 'restrictive placeholder')
    ok(callable(match(r, '/blog', 'PATCH')[1]['cb']), 'callback')

with subtest('num'):
    r = Pyjoyment.Routes.new()
    r.get('/article/<id:num>')
    is_deeply_ok(match(r, '/article/23'), [{'id': '23'}], 'number')
    is_deeply_ok(match(r, '/article/2.3'), [], 'not a number')

with subtest('base_classes'):
    r = Pyjoyment.Routes.new()
    classes = r.base_classes
    is_deeply_ok(classes, ['Pyjoyment.Controller', 'Pyjoyment'], 'default')
    r.base_classes = ['MyApp.Controller']
    is_deeply_ok(r.base_classes, ['MyApp.Controller'], 'set')

with subtest('cache'):
    r = Pyjoyment.Routes.new()
    cache = r.cache
    isa_ok(cache, Pyjo.Cache.object, 'default')
    r.cache = Pyjo.Cache.new()
    isnt_ok(r.cache, cache, 'set')

with subtest('conditions'):
    r = Pyjoyment.Routes.new()
    conditions = r.conditions
    is_deeply_ok(conditions, {}, 'default')
    r.conditions = {'foo': lambda route, c, captures, arg: ...}
    ok('foo' in r.conditions, 'set')

with subtest('namespaces'):
    r = Pyjoyment.Routes.new()
    namespaces = r.namespaces
    is_deeply_ok(namespaces, [], 'default')
    r.namespaces = ['MyApp.Controller', 'MyApp']

    # Add another namespace to load controllers from
    r.namespaces.append('MyApp.MyController')
    is_deeply_ok(r.namespaces, ['MyApp.Controller', 'MyApp', 'MyApp.MyController'], 'appended')

with subtest('shortcuts'):
    r = Pyjoyment.Routes.new()
    shortcuts = r.shortcuts
    is_deeply_ok(shortcuts, {}, 'default')
    r.shortcuts = {'foo': lambda route, *args: ...}
    ok('foo' in r.shortcuts, 'set')

with subtest('types'):
    r = Pyjoyment.Routes.new()
    types = r.types
    is_deeply_ok(list(types), ['num'], 'default')
    r.types = {'lower': re.compile(r'[a-z]+')}
    r.get('/<name:lower>')
    is_deeply_ok(match(r, '/foo'), [{'name': 'foo'}], 'set')

with subtest('add_condition'):
    r = Pyjoyment.Routes.new()
    is_ok(r.add_condition('foo', lambda route, c, captures, arg: ...), r, 'returns the routes')

    def foo(route, c, captures, arg):
        ...
        return True

    r.add_condition('foo', foo)
    r.get('/').requires(foo=1)
    is_deeply_ok(match(r, '/'), [{}], 'condition')

with subtest('add_shortcut'):
    r = Pyjoyment.Routes.new()
    is_ok(r.add_shortcut('foo', lambda route, *args: ...), r, 'returns the routes')

    r.add_shortcut('foo', lambda route, *args: route.get(*args))
    r.foo('/bar')
    is_deeply_ok(match(r, '/bar'), [{}], 'shortcut')

with subtest('add_type'):
    r = Pyjoyment.Routes.new()
    is_ok(r.add_type('foo', re.compile(r'\w+')), r, 'returns the routes')
    r = r.add_type('foo', ['bar', 'baz'])

    r.add_type('lower', re.compile(r'[a-z]+'))
    r.get('/<a:foo>/<b:lower>')
    is_deeply_ok(match(r, '/baz/yada'), [{'a': 'baz', 'b': 'yada'}], 'types')

with subtest('lookup'):
    r = Pyjoyment.Routes.new()
    foo = r.get('/foo').set(name='foo')
    route = r.lookup('foo')
    is_ok(route, foo, 'found')
    r.get('/bar').set(name='foo')
    is_ok(r.lookup('foo'), foo, 'cached')

done_testing()
