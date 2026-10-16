import Pyjo.Exception

from Pyjo.File import tempdir
from Pyjo.Loader import data_section, file_is_binary, find_modules, find_packages, load_class, load_classes
from Pyjo.Test import *

import sys
import types


# Unlike Mojolicious: Prove runs every .py file under t, so the modules of the test are written into a temporary
# directory, and they are top-level, as Python does not merge a regular package like Mojo:: from every directory
# of sys.path
lib = tempdir()
for name, content in {
    'B.py': 'def svref_2object(): ...\n',
    'LoaderException.py': '# Mojo::LoaderException\n\nimport Pyjo.Base\n\ndef new(): ...\n\nfoo {\n\nTrue\n',
    'LoaderException2.py': '# Mojo::LoaderException2\nimport LoaderException2_2\n\nLoaderException2_2.throw_error()\n\nTrue\n',
    'LoaderException2_2.py': (
        'import LoaderException2_3\n\n\ndef throw_error():\n'
        '    try:\n        LoaderException2_3.throw_error()\n    except Exception:\n        raise\n'
    ),
    'LoaderException2_3.py': 'def throw_error():\n    raise Exception("Exception")\n',
    'LoaderTest/A.py': 'import Pyjo.Base\n\nnew = Pyjo.Base.new\n',
    'LoaderTest/B.py': 'import Pyjo.Base\n\nnew = Pyjo.Base.new\n',
    'LoaderTest/C.py': 'import Pyjo.Base\n\nnew = Pyjo.Base.new\n',
    'LoaderTest/D.txt': 'D\n',
    'LoaderTest/E/F.py': 'import Pyjo.Base\n\nnew = Pyjo.Base.new\n',
    'LoaderTest/E/G.txt': 'G\n',
    'LoaderTestException/A.py': '# Mojo::LoaderException::A\n\nimport Pyjo.Base\n\ndef new(): ...\n\nfoo {\n\nTrue\n',
}.items():
    lib.child(*name.split('/')).dirname().make_path()
    lib.child(*name.split('/')).spew(content)
sys.path.insert(0, lib.to_str())

# package MyLoaderTest::Foo::Bar; package MyLoaderTest::Foo::Baz;
for name in ('MyLoaderTest.Foo.Bar', 'MyLoaderTest.Foo.Baz'):
    sys.modules[name] = types.ModuleType(name)


# Perl's open of a filehandle to a string, as the DATA handle of a package
def package(name, data):
    sys.modules[name] = types.ModuleType(name)
    sys.modules[name].__DATA__ = data


with subtest('Single character core module'):
    # Unlike Mojolicious: Python has no module with a name of a single character, the test has one
    ok(not load_class('B'), 'loaded')
    ok(hasattr(sys.modules['B'], 'svref_2object'), 'method found')

with subtest('Exception'):
    e = load_class('LoaderException')
    isa_ok(e, Pyjo.Exception.object, 'right exception')
    # Unlike Mojolicious: Python reports the bracket that is never closed, Perl the end of the file
    like_ok(e.message, r'was never closed', 'right message')
    is_ok(e.lines_before[0][0], 2, 'right number')
    is_ok(e.lines_before[0][1], '', 'right line')
    is_ok(e.lines_before[1][0], 3, 'right number')
    is_ok(e.lines_before[1][1], 'import Pyjo.Base', 'right line')
    is_ok(e.lines_before[2][0], 4, 'right number')
    is_ok(e.lines_before[2][1], '', 'right line')
    is_ok(e.lines_before[3][0], 5, 'right number')
    is_ok(e.lines_before[3][1], 'def new(): ...', 'right line')
    is_ok(e.lines_before[4][0], 6, 'right number')
    is_ok(e.lines_before[4][1], '', 'right line')
    is_ok(e.line[0], 7, 'right number')
    is_ok(e.line[1], 'foo {', 'right line')
    like_ok(str(e), r'was never closed', 'right message')

with subtest('Complicated exception'):
    e = load_class('LoaderException2')
    isa_ok(e, Pyjo.Exception.object, 'right exception')
    like_ok(e.message, r'Exception', 'right message')
    is_ok(e.lines_before[0][0], 1, 'right number')
    is_ok(e.lines_before[0][1], '# Mojo::LoaderException2', 'right line')
    is_ok(e.lines_before[1][0], 2, 'right number')
    is_ok(e.lines_before[1][1], 'import LoaderException2_2', 'right line')
    is_ok(e.lines_before[2][0], 3, 'right number')
    is_ok(e.lines_before[2][1], '', 'right line')
    is_ok(e.line[0], 4, 'right number')
    is_ok(e.line[1], 'LoaderException2_2.throw_error()', 'right line')
    is_ok(e.lines_after[0][0], 5, 'right number')
    is_ok(e.lines_after[0][1], '', 'right line')
    is_ok(e.lines_after[1][0], 6, 'right number')
    is_ok(e.lines_after[1][1], 'True', 'right line')
    like_ok(str(e), r'Exception', 'right message')

with subtest('Search modules'):
    is_deeply_ok(
        find_modules('LoaderTest'), ['LoaderTest.A', 'LoaderTest.B', 'LoaderTest.C'], 'found the right modules'
    )

    is_deeply_ok(
        find_modules('LoaderTest', recursive=True),
        ['LoaderTest.A', 'LoaderTest.B', 'LoaderTest.C', 'LoaderTest.E.F'],
        'found the right modules',
    )

    is_deeply_ok(find_modules('MyLoaderTest.DoesNotExist'), [], 'no modules found')
    is_deeply_ok(find_modules('MyLoaderTest.DoesNotExist', recursive=True), [], 'no modules found')

with subtest('Search packages'):
    pkgs = find_packages('MyLoaderTest.Foo')
    is_deeply_ok(pkgs, ['MyLoaderTest.Foo.Bar', 'MyLoaderTest.Foo.Baz'], 'found the right packages')
    is_deeply_ok(find_packages('MyLoaderTest.DoesNotExist'), [], 'no packages found')

with subtest('Load'):
    ok(not load_class('LoaderTest.A'), 'loaded successfully')
    ok(hasattr(sys.modules['LoaderTest.A'], 'new'), 'loaded successfully')
    for module in find_modules('LoaderTest'):
        load_class(module)
    ok(hasattr(sys.modules['LoaderTest.B'], 'new'), 'loaded successfully')
    ok(hasattr(sys.modules['LoaderTest.C'], 'new'), 'loaded successfully')

with subtest('Class does not exist'):
    is_ok(load_class('LoaderTest'), True, 'nothing to load')
    is_ok(load_class('LoaderTest'), True, 'nothing to load')

with subtest('Invalid class'):
    is_ok(load_class('Pyjoyment/Lite'), True, 'nothing to load')
    is_ok(load_class('Pyjoyment/Lite.py'), True, 'nothing to load')
    is_ok(load_class('Pyjoyment\\Lite'), True, 'nothing to load')
    is_ok(load_class('Pyjoyment\\Lite.py'), True, 'nothing to load')
    is_ok(load_class('.Pyjoyment.Lite'), True, 'nothing to load')
    is_ok(load_class('Pyjoyment.Lite.'), True, 'nothing to load')
    is_ok(load_class('.Pyjoyment.Lite.'), True, 'nothing to load')
    is_ok(load_class('Pyjoyment.Lite'), None, 'loaded successfully')

with subtest('Load classes recursively'):
    is_deeply_ok(
        load_classes('LoaderTest'),
        ['LoaderTest.A', 'LoaderTest.B', 'LoaderTest.C', 'LoaderTest.E.F'],
        'classes loaded',
    )
    ok(hasattr(sys.modules['LoaderTest.E.F'], 'new'), 'loaded successfully')

with subtest('Exception in namespace'):
    try:
        load_classes('LoaderTestException')
    except Exception as e:
        err = e
    like_ok(str(err), r'was never closed.*A\.py', 'right error')

with subtest('UNIX DATA templates'):
    unix = '@@ template1\nFirst Template\n@@ template2\r\nSecond Template\n'
    package('Example.Package.UNIX', unix)
    ok(not file_is_binary('Example.Package.UNIX', 'template1'), 'file is not binary')
    is_ok(data_section('Example.Package.UNIX', 'template1'), 'First Template\n', 'right template')
    is_ok(data_section('Example.Package.UNIX', 'template2'), 'Second Template\n', 'right template')
    is_deeply_ok(sorted(data_section('Example.Package.UNIX')), ['template1', 'template2'], 'right DATA files')

with subtest('Windows DATA templates'):
    windows = '@@ template3\r\nThird Template\r\n@@ template4\r\nFourth Template\r\n'
    package('Example.Package.Windows', windows)
    is_ok(data_section('Example.Package.Windows', 'template3'), 'Third Template\r\n', 'right template')
    is_ok(data_section('Example.Package.Windows', 'template4'), 'Fourth Template\r\n', 'right template')
    is_deeply_ok(sorted(data_section('Example.Package.Windows')), ['template3', 'template4'], 'right DATA files')

with subtest('Mixed whitespace'):
    mixed = '@@template5\n5\n\n@@  template6\n6\n@@     template7\n7'
    package('Example.Package.Mixed', mixed)
    is_ok(data_section('Example.Package.Mixed', 'template5'), '5\n\n', 'right template')
    is_ok(data_section('Example.Package.Mixed', 'template6'), '6\n', 'right template')
    is_ok(data_section('Example.Package.Mixed', 'template7'), '7', 'right template')
    is_deeply_ok(
        sorted(data_section('Example.Package.Mixed')), ['template5', 'template6', 'template7'], 'right DATA files'
    )

with subtest('Base64'):
    b64 = '@@test.bin (base64)\n4pml'
    package('Example.Package.Base64', b64)
    ok(not file_is_binary('Example.Package.DoesNotExist', 'test.bin'), 'file is not binary')
    ok(file_is_binary('Example.Package.Base64', 'test.bin'), 'file is binary')
    is_ok(data_section('Example.Package.Base64', 'test.bin'), b'\xe2\x99\xa5', 'right template')
    is_deeply_ok(sorted(data_section('Example.Package.Base64')), ['test.bin'], 'right DATA files')

# Left out from Mojolicious: "Hide DATA usage from error messages", Perl adds the line of the last handle it read to
# a message of die, Python has no such thing

done_testing()
