from Pyjo.Test import *


with subtest('Synopsis'):
    from Pyjo.Asset import Asset

    class MyAsset(Asset):
        def add_chunk(self, chunk): ...
        def contains(self, string): ...
        def get_chunk(self, offset, max=None): ...
        def move_to(self, to): ...
        @property
        def mtime(self): ...
        @property
        def size(self): ...
        def slurp(self): ...
        def to_file(self): ...

    isa_ok(MyAsset(), Asset, 'subclass')

    import Pyjo.Asset

    class MyAsset(Pyjo.Asset.object):
        def add_chunk(self, chunk): ...
        def contains(self, string): ...
        def get_chunk(self, offset, max=None): ...
        def move_to(self, to): ...
        @property
        def mtime(self): ...
        @property
        def size(self): ...
        def slurp(self): ...
        def to_file(self): ...

    isa_ok(MyAsset.new(), Pyjo.Asset.object, 'subclass')

with subtest('new'):
    asset = Pyjo.Asset.new()
    is_ok(asset.start_range, 0, 'start_range')
    asset = Pyjo.Asset.new(start_range=3, end_range=8)
    is_ok((asset.start_range, asset.end_range), (3, 8), 'ranges')

with subtest('end_range'):
    asset = Pyjo.Asset.new()
    end = asset.end_range
    is_ok(end, None, 'default')
    asset.end_range = 8
    is_ok(asset.end_range, 8, 'set')

with subtest('start_range'):
    asset = Pyjo.Asset.new()
    start = asset.start_range
    is_ok(start, 0, 'default')
    asset.start_range = 3
    is_ok(asset.start_range, 3, 'set')

# The methods that a subclass overloads
asset = Pyjo.Asset.new()

with subtest('add_chunk'):
    throws_ok(lambda: asset.add_chunk(b'foo bar baz'), NotImplementedError, 'abstract')

with subtest('contains'):
    throws_ok(lambda: asset.contains(b'bar'), NotImplementedError, 'abstract')

with subtest('get_chunk'):
    throws_ok(lambda: asset.get_chunk(0), NotImplementedError, 'abstract')
    throws_ok(lambda: asset.get_chunk(0, 10), NotImplementedError, 'abstract with max')

with subtest('is_file'):
    boolean = asset.is_file
    is_ok(boolean, False, 'not a file')

with subtest('is_range'):
    boolean = asset.is_range
    is_ok(boolean, False, 'no range')
    is_ok(Pyjo.Asset.new(start_range=3).is_range, True, 'start_range')

with subtest('move_to'):
    throws_ok(lambda: asset.move_to('/home/sri/foo.txt'), NotImplementedError, 'abstract')

with subtest('mtime'):
    throws_ok(lambda: asset.mtime, NotImplementedError, 'abstract')

with subtest('size'):
    throws_ok(lambda: asset.size, NotImplementedError, 'abstract')

with subtest('slurp'):
    throws_ok(lambda: asset.slurp(), NotImplementedError, 'abstract')

with subtest('to_file'):
    throws_ok(lambda: asset.to_file(), NotImplementedError, 'abstract')

done_testing()
