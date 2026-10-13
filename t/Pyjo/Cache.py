import Pyjo.Cache

from Pyjo.Test import *


with subtest('Basics'):
    cache = Pyjo.Cache.new(max_keys=2)
    is_ok(cache.get('foo'), None, 'no result')
    cache.set('foo', 'bar')
    is_ok(cache.get('foo'), 'bar', 'right result')
    cache.set('bar', 'baz')
    is_ok(cache.get('foo'), 'bar', 'right result')
    is_ok(cache.get('bar'), 'baz', 'right result')
    cache.set('baz', 'yada')
    is_ok(cache.get('foo'), None, 'no result')
    is_ok(cache.get('bar'), 'baz', 'right result')
    is_ok(cache.get('baz'), 'yada', 'right result')
    cache.set('yada', 23)
    is_ok(cache.get('foo'), None, 'no result')
    is_ok(cache.get('bar'), None, 'no result')
    is_ok(cache.get('baz'), 'yada', 'right result')
    is_ok(cache.get('yada'), 23, 'right result')
    cache.max_keys = 1
    cache.set('one', 1).set('two', 2)
    is_ok(cache.get('one'), None, 'no result')
    is_ok(cache.get('two'), 2, 'right result')

with subtest('Bigger cache'):
    cache = Pyjo.Cache.new(max_keys=3)
    is_ok(cache.get('foo'), None, 'no result')
    is_ok(cache.set('foo', 'bar').get('foo'), 'bar', 'right result')
    cache.set('bar', 'baz')
    is_ok(cache.get('foo'), 'bar', 'right result')
    is_ok(cache.get('bar'), 'baz', 'right result')
    cache.set('baz', 'yada')
    is_ok(cache.get('foo'), 'bar', 'right result')
    is_ok(cache.get('bar'), 'baz', 'right result')
    is_ok(cache.get('baz'), 'yada', 'right result')
    cache.set('yada', 23)
    is_ok(cache.get('foo'), None, 'no result')
    is_ok(cache.get('bar'), 'baz', 'right result')
    is_ok(cache.get('baz'), 'yada', 'right result')
    is_ok(cache.get('yada'), 23, 'right result')

with subtest('Cache disabled'):
    cache = Pyjo.Cache.new(max_keys=0)
    is_ok(cache.get('foo'), None, 'no result')
    is_ok(cache.set('foo', 'bar').get('foo'), None, 'no result')

    cache = Pyjo.Cache.new(max_keys=-1)
    is_ok(cache.get('foo'), None, 'no result')
    cache.set('foo', 'bar')
    is_ok(cache.get('foo'), None, 'no result')

done_testing()
