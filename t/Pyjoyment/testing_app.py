import Pyjo.File
import Pyjo.Test.Pyjo

from Pyjo.File import curfile
from Pyjo.Test import *

import os
import sys


# BEGIN { $ENV{MOJO_MODE} = 'testing' }, before the mode of the application is read
os.environ['PYJO_MODE'] = 'testing'

# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# Renamed from Mojolicious: the modules of the tests are in tt/lib, where Mojo has them in t/mojolicious/lib
sys.path.insert(0, curfile().dirname().dirname().dirname().child('tt', 'lib').to_str())

import PyjoymentTest  # noqa: E402  # pyright: ignore[reportMissingImports]


# Not in Mojolicious: the home of the applications of tt/lib is the directory of this test, with the templates, the
# static files and the configuration files of the tests, as Mojo detects t/mojolicious from t/mojolicious/lib
os.environ['PYJO_HOME'] = curfile().dirname().to_str()

# Not in Mojolicious: the module with a syntax error in a temporary directory, as the linters check the files of tt/lib,
# which is a part of the package PyjoymentTest
syntax_error = Pyjo.File.tempdir()
syntax_error.child('SyntaxError.py').spew(
    b'import Pyjoyment.Controller\n\n\nclass SyntaxError(Pyjoyment.Controller.object):\n    def foo(self):\n        (\n'
)
PyjoymentTest.__path__.append(syntax_error.to_str())

# Unlike Mojolicious: the "Server" header is "Pyjoyment (Python)", the message of Python for a syntax error, where Perl
# has "Missing right curly", and Pyjoyment, the directory of this test, where Mojo has mojolicious

t = Pyjo.Test.Pyjo.new('PyjoymentTest')
success = []
t.or_(lambda t: success.append('one'))
t.success = True
t.or_(lambda t: success.append('two'))
t.success = False
t.or_(lambda t: success.append(t.app.mode))
is_ok(''.join(success), 'onetesting', 'two callbacks have been executed')
ok(t.get_ok('/').success, 'test was successful')

# SyntaxError.foo in testing mode (syntax error in controller)
(
    t.get_ok('/syntax_error/foo')
    .status_is(500)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Testing &#39;\(&#39; was never closed')
)

# Foo.syntaxerror in testing mode (syntax error in template)
(
    t.get_ok('/foo/syntaxerror')
    .status_is(500)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Testing &#39;\(&#39; was never closed')
)

# Static file /hello.txt in testing mode
(
    t.get_ok('/hello.txt')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Hello Mojo from a static file!')
)

# Foo.bar in testing mode (missing action)
t.get_ok('/foo/baz').status_is(500).header_is('Server', 'Pyjoyment (Python)').content_like(r'Testing')

# Try to access a file which is not under the web root via path traversal in
# testing mode
(
    t.get_ok('/../../Pyjoyment/secret.txt')
    .status_is(404)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Testing not found')
)

# Try to access a file which is not under the web root via path traversal in
# testing mode (goes back and forth one directory)
(
    t.get_ok('/another/../../../Pyjoyment/secret.txt')
    .status_is(404)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Testing not found')
)

# Try to access a file which is not under the web root via path traversal in
# testing mode (triple dot)
(
    t.get_ok('/.../Pyjoyment/secret.txt')
    .status_is(404)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Testing not found')
)

# Try to access a file which is not under the web root via path traversal in
# testing mode (backslashes)
(
    t.get_ok('/..\\..\\Pyjoyment\\secret.txt')
    .status_is(404)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Testing not found')
)

# Try to access a file which is not under the web root via path traversal in
# testing mode (escaped backslashes)
(
    t.get_ok('/..%5C..%5CPyjoyment%5Csecret.txt')
    .status_is(404)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Testing not found')
)

# Check that backslashes in query or fragment parts don't block access in
# testing mode
t.get_ok('/hello.txt?one=\\1#two=\\2').status_is(200).content_like(r'Hello Mojo from a static file!')

done_testing()
