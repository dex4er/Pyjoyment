from Pyjo.Test import *


with subtest('Synopsis'):
    from Pyjo.Cache import Cache

    cache = Cache(max_keys=50)
    cache.set('foo', 'bar')
    foo = cache.get('foo')
    is_ok(foo, 'bar', 'cached value')

    import Pyjo.Cache

    cache = Pyjo.Cache.new(max_keys=50)
    cache.set('foo', 'bar')
    foo = cache.get('foo')
    is_ok(foo, 'bar', 'cached value')

with subtest('max_keys'):
    cache = Pyjo.Cache.new()
    max = cache.max_keys
    is_ok(max, 100, 'default')
    cache.max_keys = 50
    is_ok(cache.max_keys, 50, 'set')

with subtest('new'):
    cache = Pyjo.Cache.new()
    is_ok(cache.max_keys, 100, 'default')
    cache = Pyjo.Cache.new(max_keys=50)
    is_ok(cache.max_keys, 50, 'max_keys')

with subtest('__contains__'):
    cache = Pyjo.Cache.new().set('foo', 'bar')
    boolean = 'foo' in cache
    is_ok(boolean, True, 'cached')
    is_ok('bar' in cache, False, 'not cached')

with subtest('__len__'):
    cache = Pyjo.Cache.new().set('foo', 'bar')
    count = len(cache)
    is_ok(count, 1, 'one value')

with subtest('get'):
    cache = Pyjo.Cache.new().set('foo', 'bar')
    value = cache.get('foo')
    is_ok(value, 'bar', 'cached value')

with subtest('set'):
    cache = Pyjo.Cache.new()
    is_ok(cache.set('foo', 'bar'), cache, 'returns the cache')
    is_ok(cache.get('foo'), 'bar', 'cached value')

done_testing()
