import Pyjo.File
import Pyjoyment
import Pyjoyment.Command.Author.inflate

from Pyjo.Test import *

import contextlib
import io
import os
import sys
import types


cwd = Pyjo.File.path()

with subtest('Synopsis'):
    application = Pyjoyment.new()
    inflate = Pyjoyment.Command.Author.inflate.new(app=application)
    like_ok(inflate.usage, r'^Usage: APPLICATION inflate \[OPTIONS\]\n\n  \./myapp\.py inflate\n', 'usage')

with subtest('Description'):
    # A module with templates and static files in its DATA section
    module = types.ModuleType('InflateTest')
    module.__DATA__ = '@@ index.html.ep\n<p>Index</p>\n@@ foo.txt\nFoo\n@@ bar.bin (base64)\nAAEC\n@@ nothing\n'
    sys.modules['InflateTest'] = module
    application = Pyjoyment.new()
    application.renderer.classes = ['InflateTest']
    application.static.classes = ['InflateTest']
    inflate = Pyjoyment.Command.Author.inflate.new(app=application)
    tmp = Pyjo.File.tempdir()
    os.chdir(tmp)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            inflate.run()
    finally:
        os.chdir(cwd)
        del sys.modules['InflateTest']
    is_ok(tmp.child('templates', 'index.html.ep').slurp(), b'<p>Index</p>\n', 'template')
    is_ok(tmp.child('public', 'foo.txt').slurp(), b'Foo\n', 'static file')
    is_ok(tmp.child('public', 'bar.bin').slurp(), b'\x00\x01\x02', 'binary file')
    ok(not os.path.exists(tmp.child('public', 'nothing').to_str()), 'no extension')

with subtest('Attributes'):
    inflate = Pyjoyment.Command.Author.inflate.new()
    is_ok(inflate.description, 'Inflate embedded files to real files', 'description')
    like_ok(inflate.usage, r'inflate', 'usage')

done_testing()
