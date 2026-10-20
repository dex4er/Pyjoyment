import Pyjo.HelloWorld
import Pyjo.Server

from Pyjo.File import tempdir
from Pyjo.Test import *

import os
import re
import sys

from unittest.mock import patch


tmp = tempdir()

with subtest('A script of load_app runs with runpy in a namespace of its own'):
    script = tmp.child('myapp.py').spew(
        'import os, sys\n'
        'import Pyjo.HelloWorld\n'
        'app = Pyjo.HelloWorld.new(moniker=f"{__name__} {sys.argv[0]} {os.environ.get(\'PYJO_APP_LOADER\')}")\n'
        'if __name__ == "__main__":\n'
        '    raise SystemExit("not as a program")\n'
        'app.start()\n'
    )
    argv = sys.argv[0]
    app = Pyjo.Server.new().load_app(script)
    like_ok(app.moniker, r'^Pyjo\.Server\.Sandbox\.[0-9a-f]{32} ', 'sandbox')
    like_ok(app.moniker, rf' {re.escape(script.to_str())} 1$', 'sys.argv[0] is the script, PYJO_APP_LOADER is set')
    is_ok(sys.argv[0], argv, 'sys.argv[0] restored')
    is_ok(os.environ.get('PYJO_APP_LOADER'), None, 'PYJO_APP_LOADER restored')
    is_ok(Pyjo.Server.loaded_app, None, 'loaded_app restored')

with subtest('The arguments of load_app reach the constructor of the application'):
    script = tmp.child('moniker.py').spew('import Pyjo.HelloWorld\n\nPyjo.HelloWorld.new().start()\n')
    is_ok(Pyjo.Server.new().load_app(script, moniker='test').moniker, 'test', 'right moniker')
    is_deeply_ok(Pyjo.Server.args_override, {}, 'args_override restored')

with subtest('Errors of the script'):
    script = tmp.child('broken.py').spew('def broken(:\n')
    throws_ok(
        lambda: Pyjo.Server.new().load_app(script),
        re.compile(re.escape(f'Can\'t load application from file "{script}": invalid syntax')),
        'syntax',
    )
    script = tmp.child('nothing.py').spew('import Pyjo.HelloWorld\n\nPyjo.HelloWorld.new()\n')
    throws_ok(
        lambda: Pyjo.Server.new().load_app(script), re.compile(r'did not return an application object'), 'not started'
    )

with subtest('A class of build_app by name or as a class'):
    server = Pyjo.Server.new()
    ok(isinstance(server.build_app('Pyjo.HelloWorld'), Pyjo.HelloWorld.object), 'module with new')
    ok(isinstance(server.build_app('Pyjo.HelloWorld.Pyjo_HelloWorld'), Pyjo.HelloWorld.object), 'class in a module')
    ok(isinstance(server.build_app(Pyjo.HelloWorld.object), Pyjo.HelloWorld.object), 'class')
    throws_ok(
        lambda: server.build_app('Pyjo.DoesNotExist'),
        re.compile(r'^Can\'t find application class "Pyjo\.DoesNotExist" in sys\.path'),
        'missing',
    )

with subtest('The trusted proxies of the environment'):
    with patch.dict(os.environ, {'PYJO_TRUSTED_PROXIES': ' 10.0.0.0/8 , 127.0.0.1,fc00::/7'}):
        server = Pyjo.Server.new()
        is_deeply_ok(server.trusted_proxies, [' 10.0.0.0/8', '127.0.0.1', 'fc00::/7'], 'split on commas')
        ok(server.reverse_proxy, 'behind a reverse proxy')

done_testing()
