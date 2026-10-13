import Pyjo.Cache

from Pyjo.Test import *


with subtest('A container'):
    cache = Pyjo.Cache.new(max_keys=2)
    is_ok(len(cache), 0, 'empty')
    ok(not cache, 'false when empty, as a container')
    cache.set('foo', 'bar').set('bar', 'baz').set('baz', 'yada')
    is_ok(len(cache), 2, 'limited by max_keys')
    ok(cache, 'true with values')
    ok('foo' not in cache, 'oldest key evicted')
    ok('bar' in cache, 'key kept')
    ok('baz' in cache, 'newest key')
    throws_ok(lambda: [] in cache, TypeError, 'unhashable key raises TypeError, as in a dict')

with subtest('Cached None'):
    cache = Pyjo.Cache.new()
    cache.set('foo', None)
    is_ok(cache.get('foo'), None, 'value is None')
    ok('foo' in cache, 'but the key is cached')

with subtest('Keys of Python types'):
    cache = Pyjo.Cache.new()
    cache.set(('GET', '/'), 'index').set(23, 'number').set(frozenset({'a'}), 'set')
    is_ok(cache.get(('GET', '/')), 'index', 'tuple key')
    is_ok(cache.get(23), 'number', 'int key')
    is_ok(cache.get(frozenset({'a'})), 'set', 'frozenset key')
    is_ok(len(cache), 3, 'three values')

with subtest('Updated value keeps its place'):
    cache = Pyjo.Cache.new(max_keys=3)
    cache.set('a', 1).set('b', 2).set('c', 3).set('b', 4)
    is_ok(cache.get('b'), 4, 'updated value')
    cache.max_keys = 2
    cache.set('d', 5)
    ok('a' not in cache, 'first evicted')
    ok('b' not in cache, 'second evicted')
    is_ok(cache.get('c'), 3, 'third kept')
    is_ok(cache.get('d'), 5, 'new value')

done_testing()
