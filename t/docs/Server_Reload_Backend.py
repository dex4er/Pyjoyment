from Pyjo.Test import *

import os

from unittest.mock import patch


with subtest('Synopsis'):
    from Pyjo.Server.Reload.Backend import Backend

    class Pyjo_Server_Reload_Backend_Inotify(Backend):
        def modified_files(self):
            return ['changed.py']

    new = Pyjo_Server_Reload_Backend_Inotify.new
    object = Pyjo_Server_Reload_Backend_Inotify

    is_deeply_ok(new().modified_files(), ['changed.py'], 'backend of its own')

    # Or import the module, as in Google Python Style Guide
    import Pyjo.Server.Reload.Backend

    class Pyjo_Server_Reload_Backend_Inotify(Pyjo.Server.Reload.Backend.object):
        def modified_files(self):
            return ['changed.py']

    new = Pyjo_Server_Reload_Backend_Inotify.new
    object = Pyjo_Server_Reload_Backend_Inotify

    is_deeply_ok(new().modified_files(), ['changed.py'], 'backend of its own')

with subtest('new'):
    backend = Pyjo.Server.Reload.Backend.new()
    isa_ok(backend, Pyjo.Server.Reload.Backend.object, 'backend')
    backend = Pyjo.Server.Reload.Backend.new(watch=['lib'], watch_timeout=2)
    is_deeply_ok(backend.watch, ['lib'], 'watch')
    is_ok(backend.watch_timeout, 2, 'watch_timeout')

with subtest('watch'):
    watch = Pyjo.Server.Reload.Backend.new().watch
    is_deeply_ok(watch, ['lib', 'templates'], 'default')
    backend.watch = ['/home/sri/my_app']
    is_deeply_ok(backend.watch, ['/home/sri/my_app'], 'set')

with subtest('watch_timeout'):
    timeout = Pyjo.Server.Reload.Backend.new().watch_timeout
    is_ok(timeout, 1, 'default')
    with patch.dict(os.environ, {'PYJO_RELOAD_TIMEOUT': '3'}):
        is_ok(Pyjo.Server.Reload.Backend.new().watch_timeout, 3, 'environment variable')
    backend.watch_timeout = 10
    is_ok(backend.watch_timeout, 10, 'set')

with subtest('modified_files'):
    throws_ok(
        lambda: Pyjo.Server.Reload.Backend.new().modified_files(),
        'Method "modified_files" not implemented by subclass',
        'abstract',
    )

done_testing()
