import Pyjo.Exception

from Pyjo.File import tempdir
from Pyjo.Loader import data_section, file_is_binary, find_modules, load_class, load_classes
from Pyjo.Test import *

import sys


lib = tempdir()
files = {
    'stdlib_data/__init__.py': '',
    'stdlib_data/variable.py': "'''Docstring.\n\n__DATA__\n@@ doc.txt\nDoc\n'''\n\nDATA = '@@ var.txt\\nVar\\n'\n",
    'stdlib_data/docstring.py': "'''Docstring.\n\n__DATA__\n@@ doc.txt\nDoc\n__END__\nNot a file\n'''\n\n\nclass App:\n    pass\n",
    'stdlib_data/plain.py': "'''Docstring without data.'''\n",
    'stdlib_pkg/__init__.py': '',
    'stdlib_pkg/sub/__init__.py': 'import Pyjo.Base\n\nnew = Pyjo.Base.new\n',
    'stdlib_pkg/sub/leaf.py': '',
    'stdlib_pkg/mod.py': '',
    'stdlib_pkg/missing_dependency.py': 'import stdlib_does_not_exist\n',
    'stdlib_pkg/syntax.py': 'x = (\n',
    'stdlib_ns/inner.py': '',
}
for name, content in files.items():
    lib.child(*name.split('/')).dirname().make_path()
    lib.child(*name.split('/')).spew(content)
sys.path.insert(0, lib.to_str())

with subtest('DATA variable and docstring'):
    is_ok(load_class('stdlib_data.variable'), None, 'loaded')
    is_deeply_ok(data_section('stdlib_data.variable'), {'var.txt': 'Var\n'}, 'variable comes first')
    load_class('stdlib_data.docstring')
    is_deeply_ok(data_section('stdlib_data.docstring'), {'doc.txt': 'Doc\n'}, 'docstring after __DATA__ until __END__')
    load_class('stdlib_data.plain')
    is_deeply_ok(data_section('stdlib_data.plain'), {}, 'no __DATA__ in the docstring')
    is_ok(file_is_binary('stdlib_data.plain', 'doc.txt'), None, 'no files')

with subtest('Modules and classes'):
    module = sys.modules['stdlib_data.docstring']
    is_ok(data_section(module, 'doc.txt'), 'Doc\n', 'module')
    is_ok(data_section(module.App, 'doc.txt'), 'Doc\n', 'class')
    is_ok(data_section('stdlib_data.docstring.App', 'doc.txt'), 'Doc\n', 'name of the class')
    is_ok(data_section('stdlib_data.not_loaded', 'doc.txt'), None, 'not loaded')
    is_ok(data_section(None), None, 'no class')

with subtest('Packages'):
    is_deeply_ok(
        find_modules('stdlib_pkg'),
        [
            'stdlib_pkg.missing_dependency',
            'stdlib_pkg.mod',
            'stdlib_pkg.sub',
            'stdlib_pkg.syntax',
        ],
        'a package is a module',
    )
    is_deeply_ok(
        find_modules('stdlib_pkg.sub', recursive=True), ['stdlib_pkg.sub.leaf'], 'the namespace itself is left out'
    )
    is_ok(load_class('stdlib_pkg.sub'), None, 'package loaded')
    ok(hasattr(sys.modules['stdlib_pkg.sub'], 'new'), 'with new')

with subtest('Not found'):
    is_ok(load_class('stdlib_ns'), True, 'namespace package')
    is_ok(load_class('stdlib_ns.inner'), None, 'module in a namespace package')
    is_ok(load_class('stdlib_does_not_exist.child'), True, 'parent missing')
    is_ok(load_class('stdlib_pkg.does_not_exist'), True, 'module missing')
    is_ok(load_class(''), True, 'empty name')

with subtest('Already loaded'):
    is_ok(load_class('sys'), None, 'built-in module')
    is_ok(load_class('os.path'), None, 'standard library')

with subtest('Real errors'):
    e = load_class('stdlib_pkg.missing_dependency')
    isa_ok(e, Pyjo.Exception.object, 'missing dependency is an error')
    isa_ok(e.__cause__, ModuleNotFoundError, 'cause')
    is_ok(e.line[1], 'import stdlib_does_not_exist', 'line of the module')
    ok('stdlib_pkg.missing_dependency' not in sys.modules, 'not loaded')

    e = load_class('stdlib_pkg.syntax')
    isa_ok(e.__cause__, SyntaxError, 'syntax error')
    is_ok(e.frames[0].filename, lib.child('stdlib_pkg', 'syntax.py').to_str(), 'file of the syntax error')
    is_ok(e.line, [1, 'x = ('], 'line of the syntax error')

    throws_ok(lambda: load_classes('stdlib_pkg'), Pyjo.Exception.object, 'load_classes raises')

done_testing()
