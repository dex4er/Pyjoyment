import Pyjoyment
import Pyjoyment.Command.Author.generate

from Pyjo.Test import *

import contextlib
import io
import os


with subtest('Synopsis'):
    generator = Pyjoyment.Command.Author.generate.new(app=Pyjoyment.new())
    like_ok(
        generator.message,
        r'^Usage: APPLICATION generate GENERATOR \[OPTIONS\]\n\n  pyjo generate app\n  pyjo generate lite-app\n',
        'usage',
    )

with subtest('Description'):
    app = Pyjoyment.new()
    generator = Pyjoyment.Command.Author.generate.new(app=app)
    buffer = io.StringIO()
    os.environ['PYJO_HARNESS_ACTIVE'] = '0'
    try:
        with contextlib.redirect_stdout(buffer):
            generator.run()
    finally:
        os.environ['PYJO_HARNESS_ACTIVE'] = '1'
    like_ok(buffer.getvalue(), r'(?s)Generators:\n app .* dockerfile .* lite-app .* plugin .* pyproject ', 'generators')

with subtest('Attributes'):
    generator = Pyjoyment.Command.Author.generate.new()
    is_ok(generator.description, 'Generate files and directories from templates', 'description')
    like_ok(generator.hint, r"See 'APPLICATION generate help GENERATOR'", 'hint')
    like_ok(generator.message, r'Generators:\n$', 'message')
    generator.message = 'Bar'
    is_ok(generator.message, 'Bar', 'message changed')
    is_deeply_ok(generator.namespaces, ['Pyjoyment.Command.Author.generate'], 'namespaces')
    generator = Pyjoyment.Command.Author.generate.new(namespaces=['MyApp.Command.generate'])
    is_deeply_ok(generator.namespaces, ['MyApp.Command.generate'], 'namespaces changed')

with subtest('Methods'):
    app = Pyjoyment.new()
    generator = Pyjoyment.Command.Author.generate.new(app=app)
    buffer = io.StringIO()
    os.environ['PYJO_HELP'] = '1'
    try:
        with contextlib.redirect_stdout(buffer):
            generator.help('app')
    finally:
        os.environ.pop('PYJO_HELP', None)
    like_ok(buffer.getvalue(), r'^Usage: APPLICATION generate app \[OPTIONS\] \[NAME\]', 'help')

done_testing()
