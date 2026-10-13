import Pyjo.Collection

from Pyjo.Collection import c
from Pyjo.Test import *

import copy
import json
import pickle


with subtest('A list'):
    collection = c(3, 1, 2)
    isa_ok(collection, list, 'collection')
    is_deeply_ok(list(collection), [3, 1, 2], 'list()')
    is_ok(collection, [3, 1, 2], 'equal to a list')
    is_deeply_ok(sorted(collection), [1, 2, 3], 'sorted()')
    is_deeply_ok(list(reversed(collection)), [2, 1, 3], 'reversed()')
    is_ok(len(collection), 3, 'len()')

with subtest('From an iterable'):
    is_deeply_ok(Pyjo.Collection.object(range(3)), [0, 1, 2], 'from range()')
    is_deeply_ok(Pyjo.Collection.object(x * 2 for x in [1, 2]), [2, 4], 'from a generator')
    is_deeply_ok(c(*'abc'), ['a', 'b', 'c'], 'c() of the elements of a string')

with subtest('Sort and reverse in place'):
    collection = c(3, 1, 2)
    list.sort(collection)
    is_deeply_ok(collection, [1, 2, 3], 'list.sort()')
    list.reverse(collection)
    is_deeply_ok(collection, [3, 2, 1], 'list.reverse()')

with subtest('Copy and pickle'):
    collection = c(1, [2, 3])
    clone = copy.copy(collection)
    isa_ok(clone, Pyjo.Collection.object, 'copy.copy()')
    is_ok(clone, collection, 'same elements')
    deep = copy.deepcopy(collection)
    isa_ok(deep, Pyjo.Collection.object, 'copy.deepcopy()')
    ok(deep[1] is not collection[1], 'elements copied')
    loaded = pickle.loads(pickle.dumps(collection))
    isa_ok(loaded, Pyjo.Collection.object, 'pickle')
    is_ok(loaded, collection, 'same elements')

with subtest('To the types of the standard library'):
    collection = c(('a', 1), ('b', 2), ('a', 3))
    is_ok(type(collection.to_list()), list, 'to_list() is a list')
    is_deeply_ok(collection.to_list(), [('a', 1), ('b', 2), ('a', 3)], 'same elements')
    is_ok(type(collection.to_tuple()), tuple, 'to_tuple() is a tuple')
    is_deeply_ok(collection.to_tuple(), (('a', 1), ('b', 2), ('a', 3)), 'same elements')
    is_deeply_ok(collection.to_set(), {('a', 1), ('b', 2), ('a', 3)}, 'to_set() is a set')
    is_deeply_ok(collection.to_dict(), {'a': 3, 'b': 2}, 'to_dict() is a dict, the last value wins')
    iterator = collection.to_iter()
    is_ok(next(iterator), ('a', 1), 'to_iter() is an iterator')
    is_deeply_ok(list(iterator), [('b', 2), ('a', 3)], 'the rest of the elements')

with subtest('Expression forms'):
    collection = c('a', 'b', 'c')
    is_ok(collection.get(1), collection[1], 'get() is an index')
    is_ok(collection.get(-1), collection[-1], 'also from the end')
    is_ok(collection.get(3), None, 'None instead of IndexError')
    is_ok(collection.get(-4, 'z'), 'z', 'or the default')
    is_deeply_ok(collection.zip(range(3)).to_list(), list(zip(collection, range(3), strict=False)), 'zip() as a method')
    is_deeply_ok(collection.zip([1], [2, 3]).to_list(), [('a', 1, 2)], 'of more iterables')
    throws_ok(lambda: collection.zip([1], strict=True), ValueError, 'strict, as zip() is')
    isa_ok(collection.zip([1]), Pyjo.Collection.object, 'zip()')

with subtest('JSON'):
    is_ok(json.dumps(c(1, 'a', None)), '[1, "a", null]', 'json.dumps()')

done_testing()
