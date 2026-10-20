import Pyjo.File
import Pyjoyment
import Pyjoyment.Command

from Pyjo.Test import *

import contextlib
import io
import os
import re
import sys


with subtest('Synopsis'):
    # The module of the example in the Python form, in a temporary directory of its own
    tmp = Pyjo.File.tempdir()
    tmp.child('mycommand.py').spew(b'''\
"""
Pyjoyment.Command.mycommand - My command
========================================
::

    Usage: APPLICATION mycommand [OPTIONS]

    Options:
      -s, --something   Does something
"""

from Pyjoyment.Command import Command

from Pyjo.Util import extract_usage


class Pyjoyment_Command_mycommand(Command):
    # Short description
    description = 'My first Pyjoyment command'

    # Usage message from the synopsis of the docstring of the module
    usage = extract_usage()

    def run(self, *args):
        # Magic here! :)
        return 'magic'


object = Pyjoyment_Command_mycommand
''')
    sys.path.insert(0, tmp.to_str())
    try:
        import mycommand  # pyright: ignore[reportMissingImports]
    finally:
        sys.path.remove(tmp.to_str())
    command = mycommand.object()
    isa_ok(command, Pyjoyment.Command.Command, 'command')
    is_ok(command.description, 'My first Pyjoyment command', 'description')
    like_ok(command.usage, r'^Usage: APPLICATION mycommand \[OPTIONS\]\n\nOptions:\n  -s, --something', 'usage')
    is_ok(command.run(), 'magic', 'run')
    # The example in the form of Mojolicious is imported again from its own directory
    del sys.modules['mycommand']

    # The module of the example, in a temporary directory, as a test writes nothing into t
    tmp = Pyjo.File.tempdir()
    tmp.child('mycommand.py').spew(b'''\
"""
Pyjoyment.Command.mycommand - My command
========================================
::

    Usage: APPLICATION mycommand [OPTIONS]

    Options:
      -s, --something   Does something
"""

import Pyjoyment.Command

from Pyjo.Util import extract_usage


class Pyjoyment_Command_mycommand(Pyjoyment.Command.object):
    # Short description
    description = 'My first Pyjoyment command'

    # Usage message from the synopsis of the docstring of the module
    usage = extract_usage()

    def run(self, *args):
        # Magic here! :)
        return 'magic'


object = Pyjoyment_Command_mycommand
''')
    sys.path.insert(0, tmp.to_str())
    try:
        import mycommand  # pyright: ignore[reportMissingImports]
    finally:
        sys.path.remove(tmp.to_str())
    command = mycommand.new() if hasattr(mycommand, 'new') else mycommand.object.new()
    is_ok(command.description, 'My first Pyjoyment command', 'description')
    like_ok(command.usage, r'^Usage: APPLICATION mycommand \[OPTIONS\]\n\nOptions:\n  -s, --something', 'usage')
    is_ok(command.run(), 'magic', 'run')

with subtest('app'):
    command = Pyjoyment.Command.new()
    isa_ok(command.app, Pyjoyment.object, 'default')
    app = Pyjoyment.new()
    command.app = app
    ok(command.app is app, 'application')

    # Introspect
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        for path in command.app.renderer.paths:
            print(f'Template path: {path}')
    like_ok(buffer.getvalue(), r'^Template path: ', 'introspect')

with subtest('Attributes'):
    command = Pyjoyment.Command.new()
    is_ok(command.description, 'No description', 'description')
    command.description = 'Foo'
    is_ok(command.description, 'Foo', 'description changed')
    is_ok(command.quiet, None, 'quiet')
    is_deeply_ok(command.template, {'vars': True}, 'template')
    is_ok(command.usage, 'Usage: APPLICATION\n', 'usage')

with subtest('Methods'):
    command = Pyjoyment.Command.new().set(quiet=True)
    cwd = Pyjo.File.path()
    tmp = Pyjo.File.tempdir()
    os.chdir(tmp)
    try:
        command.create_dir(tmp.child('foo', 'bar'))
        ok(os.path.isdir(tmp.child('foo', 'bar').to_str()), 'create_dir')
        command.create_rel_dir('foo/bar/baz')
        ok(os.path.isdir(tmp.child('foo', 'bar', 'baz').to_str()), 'create_rel_dir')
        command.write_file(tmp.child('foo.txt'), 'Hello World!')
        is_ok(tmp.child('foo.txt').slurp(), b'Hello World!', 'write_file')
        command.write_rel_file('foo/bar.txt', 'Hello World!')
        is_ok(tmp.child('foo', 'bar.txt').slurp(), b'Hello World!', 'write_rel_file')
        command.chmod_file(tmp.child('foo.txt'), 0o644)
        command.chmod_rel_file('foo/bar.txt', 0o644)
        # Windows keeps the bit of read-only of a mode only
        if sys.platform == 'win32':
            skip('no mode of files on Windows', 2)
        else:
            is_ok(os.stat(tmp.child('foo.txt').to_str()).st_mode & 0o777, 0o644, 'chmod_file')
            is_ok(os.stat(tmp.child('foo', 'bar.txt').to_str()).st_mode & 0o777, 0o644, 'chmod_rel_file')
        is_ok(
            os.path.realpath(command.rel_file('foo/bar.txt').to_str()),
            os.path.realpath(tmp.child('foo', 'bar.txt').to_str()),
            'rel_file',
        )
        is_ok(command.extract_usage(), '', 'extract_usage of this file, which has no docstring')
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            command.help()
        is_ok(buffer.getvalue(), 'Usage: APPLICATION\n', 'help')
        throws_ok(lambda: command.run(), re.compile(r'Method "run" not implemented by subclass'), 'run')

        Pyjoyment.Command.__DATA__ = '@@ foo_bar\n<%= args[0] if args else foo %>\n'
        is_ok(command.render_data('foo_bar', {'foo': 'bar'}), 'bar\n', 'render_data')
        command.template = {}
        is_ok(command.render_data('foo_bar', 'baz'), 'baz\n', 'render_data with arguments')
        command.render_to_file('foo_bar', tmp.child('two.txt'), 'two')
        is_ok(tmp.child('two.txt').slurp(), b'two\n', 'render_to_file')
        command.render_to_rel_file('foo_bar', 'foo/three.txt', 'three')
        is_ok(tmp.child('foo', 'three.txt').slurp(), b'three\n', 'render_to_rel_file')
    finally:
        os.chdir(cwd)

done_testing()
