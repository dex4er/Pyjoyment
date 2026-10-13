import Pyjo.Path

from Pyjo.Test import *

import pathlib


with subtest('A URL path is not a file system path'):
    path = Pyjo.Path.new().set(parts=['foo/bar', '..', 'baz'])
    throws_ok(lambda: pathlib.Path(path), TypeError, 'no __fspath__')
    is_ok(str(path), 'foo%2Fbar/../baz', 'a part can hold "/", and a path can hold ".."')

with subtest('Strings'):
    is_ok(str(Pyjo.Path.new(pathlib.PurePosixPath('/foo/bar'))), '/foo/bar', 'from the string form of a path')

done_testing()
