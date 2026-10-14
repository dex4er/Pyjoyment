from Pyjo.Test import *

import contextlib
import io
import os


with subtest('Synopsis'):
    from Pyjo.File import tempdir

    dir = tempdir()
    os.chdir(dir)
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        import Pyjo.Server.Reload.Backend.Poll

        backend = Pyjo.Server.Reload.Backend.Poll.new()
        backend.watch_timeout = 0
        backend.modified_files()
        dir.child('lib').make_path().child('MyApp.py').spew(b'pass\n')
        if files := backend.modified_files():
            print('Files have been changed')
    is_ok(output.getvalue(), 'Files have been changed\n', 'changed')
    os.chdir('/')

with subtest('new'):
    backend = Pyjo.Server.Reload.Backend.Poll.new()
    isa_ok(backend, Pyjo.Server.Reload.Backend.Poll.object, 'backend')

with subtest('modified_files'):
    backend = Pyjo.Server.Reload.Backend.Poll.new(watch=[dir.child('lib')], watch_timeout=0)
    files = backend.modified_files()
    is_deeply_ok(files, [dir.child('lib', 'MyApp.py').to_str()], 'changed since the start')
    is_deeply_ok(backend.modified_files(), [], 'not changed again')

done_testing()
