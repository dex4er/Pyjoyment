from Pyjo.File import tempdir
from Pyjo.Test import *

import contextlib
import io
import sys
import types


lib = tempdir()
lib.child('Some', 'Namespace').make_path()
lib.child('Some', 'Namespace', 'Good.py').spew("DATA = '''\n@@ some_file.txt\nSome file.\n'''\n")
lib.child('Some', 'Namespace', 'Bad.py').spew('raise Exception("Bad module")\n')
sys.path.insert(0, lib.to_str())

with subtest('Synopsis'):
    output, errors = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
        from Pyjo.Loader import data_section, find_modules, load_class
        from Pyjo.Util import warn

        # Find modules in a namespace
        for module in find_modules('Some.Namespace'):
            # Load them safely
            e = load_class(module)
            if isinstance(e, Exception):
                warn(f'Loading "{module}" failed: {e}')
                continue

            # And extract files from the DATA section
            print(data_section(module, 'some_file.txt'))
    is_ok(output.getvalue(), 'Some file.\n\n', 'file of the good module')
    like_ok(errors.getvalue(), r'^Loading "Some\.Namespace\.Bad" failed: Bad module', 'bad module')

with subtest('Description'):
    foo = types.ModuleType('Foo')
    sys.modules['Foo'] = foo
    foo.DATA = r"""
@@ test.txt
This is the first file.

@@ test2.html (base64)
VGhpcyBpcyB0aGUgc2Vjb25kIGZpbGUu

@@ test
This is the
third file.
"""
    is_ok(data_section('Foo', 'test.txt'), 'This is the first file.\n\n', 'first file')
    is_ok(data_section('Foo', 'test2.html'), b'This is the second file.', 'second file')
    is_ok(data_section('Foo', 'test'), 'This is the\nthird file.\n', 'third file')

with subtest('data_section'):
    bar = types.ModuleType('Foo.Bar')
    sys.modules['Foo.Bar'] = bar
    bar.__doc__ = 'Foo.Bar - the docstring\n\n__DATA__\n@@ index.html\n<p>Index</p>\n'
    all = data_section('Foo.Bar')
    index = data_section('Foo.Bar', 'index.html')
    is_ok(all, {'index.html': '<p>Index</p>\n'}, 'all files')
    is_ok(index, '<p>Index</p>\n', 'one file')

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        # List embedded files
        for name in data_section('Foo.Bar'):
            print(name)
    is_ok(output.getvalue(), 'index.html\n', 'listed')

with subtest('file_is_binary'):
    from Pyjo.Loader import file_is_binary

    sys.modules['Foo.Bar'].DATA = '@@ test.png (base64)\niVBORw0KGgo=\n'
    del sys.modules['Foo.Bar'].__doc__
    boolean = file_is_binary('Foo', 'test2.html')
    ok(boolean, 'Base64 encoded')
    ok(not file_is_binary('Foo', 'test.txt'), 'not encoded')

with subtest('find_packages'):
    from Pyjo.Loader import find_packages

    sys.modules['MyApp.Namespace.Foo'] = types.ModuleType('MyApp.Namespace.Foo')
    pkgs = find_packages('MyApp.Namespace')
    is_ok(pkgs, ['MyApp.Namespace.Foo'], 'packages')

with subtest('find_modules'):
    lib.child('MyApp', 'Namespace', 'Sub').make_path()
    lib.child('MyApp', 'Namespace', 'One.py').spew('')
    lib.child('MyApp', 'Namespace', 'Sub', 'Two.py').spew('')
    modules = find_modules('MyApp.Namespace')
    is_ok(modules, ['MyApp.Namespace.One'], 'modules')
    modules = find_modules('MyApp.Namespace', recursive=True)
    is_ok(modules, ['MyApp.Namespace.One', 'MyApp.Namespace.Sub.Two'], 'recursive')

with subtest('load_class'):
    e = load_class('Foo.Bar')
    is_ok(e, None, 'already loaded')

    # Handle exceptions
    try:
        if e := load_class('Foo.Quux'):
            raise Exception(f'Exception: {e}' if isinstance(e, Exception) else 'Not found!')
    except Exception as err:
        is_ok(str(err), 'Not found!', 'not found')

with subtest('load_classes'):
    from Pyjo.Loader import load_classes

    classes = load_classes('MyApp.Namespace')
    is_ok(classes, ['MyApp.Namespace.One', 'MyApp.Namespace.Sub.Two'], 'classes')

done_testing()
