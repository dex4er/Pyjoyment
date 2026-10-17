import Pyjo.File
import Pyjo.Test.Pyjo
import Pyjoyment.Routes
import Pyjoyment.Routes.Route

from Pyjo.File import curfile
from Pyjo.Test import *

import os
import sys


# BEGIN { $ENV{MOJO_MODE} = 'production' }, before the mode of the application is read
os.environ['PYJO_MODE'] = 'production'

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

# Unlike Mojolicious: the "Server" header is "Pyjoyment (Python)", the names of the applications and the classes are
# the ones of Pyjoyment, as PyjoymentTest for MojoliciousTest, and Pyjoyment, the directory of this test, where Mojo
# has mojolicious

t = Pyjo.Test.Pyjo.new('PyjoymentTest')

# Application is already available
is_ok(t.app.routes.find('something').to_str(), '/test4/:something', 'right pattern')
is_ok(t.app.routes.find('test3').pattern.defaults['namespace'], 'PyjoymentTest2.Foo', 'right namespace')
is_ok(t.app.routes.find('withblock').pattern.defaults['controller'], 'foo', 'right controller')
is_ok(type(t.app.routes.find('something')), Pyjoyment.Routes.Route.object, 'right class')
is_ok(type(t.app.routes.find('something').root), Pyjoyment.Routes.object, 'right class')
is_ok(t.app.sessions.cookie_domain, '.example.com', 'right domain')
is_ok(t.app.sessions.cookie_path, '/bar', 'right path')
is_deeply_ok(
    t.app.commands.namespaces,
    ['Pyjoyment.Command.Author', 'Pyjoyment.Command', 'PyjoymentTest.Command'],
    'right namespaces',
)
is_ok(t.app, t.app.commands.app, 'applications are equal')
is_ok(t.app.static.file('hello.txt').slurp(), b'Hello Mojo from a static file!\n', 'right content')
is_ok(t.app.static.file('does_not_exist.html'), None, 'no file')
is_ok(t.app.moniker, 'pyjoyment_test', 'right moniker')

# Remove extra files
# Renamed from Mojolicious: pyjo, the directory of the bundled files of Pyjoyment, where Mojo has mojo
is_ok(t.app.static.file('pyjo/jquery/jquery.js'), None, 'no jQuery')

# Default namespaces
is_deeply_ok(t.app.routes.namespaces, ['PyjoymentTest.Controller', 'PyjoymentTest'], 'right namespaces')

# Plugin.Test.SomePlugin2.register (security violation)
(
    t.get_ok('/plugin-test-some_plugin2/register')
    .status_isnt(404)
    .status_is(500)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Not development mode error!')
)

# Plugin.Test.SomePlugin2.register (security violation again)
(
    t.get_ok('/plugin-test-some_plugin2/register')
    .status_isnt(404)
    .status_is(500)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Not development mode error!')
)

# SyntaxError.foo in production mode (syntax error in controller)
(
    t.get_ok('/syntax_error/foo')
    .status_is(500)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Not development mode error!')
)

# Foo.syntaxerror in production mode (syntax error in template)
(
    t.get_ok('/foo/syntaxerror')
    .status_is(500)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Not development mode error!')
)

# Exceptional.this_one_dies (action dies)
(
    t.get_ok('/exceptional/this_one_dies')
    .status_is(500)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Not development mode error!')
)

# Exceptional.this_one_might_die (bridge dies)
(
    t.get_ok('/exceptional_too/this_one_dies')
    .status_is(500)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Not development mode error!')
)

# Exceptional.this_one_might_die (action dies)
(
    t.get_ok('/exceptional_too/this_one_dies', {'X-DoNotDie': 1})
    .status_is(500)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Not development mode error!')
)

# Exceptional.this_one_does_not_exist (action does not exist)
(
    t.get_ok('/exceptional/this_one_does_not_exist')
    .status_is(404)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Page Not Found')
)

# Exceptional.this_one_does_not_exist (action behind bridge does not exist)
(
    t.get_ok('/exceptional_too/this_one_does_not_exist', {'X-DoNotDie': 1})
    .status_is(404)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Page Not Found')
)

# Static file /hello.txt in production mode
(
    t.get_ok('/hello.txt')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Hello Mojo from a static file!')
)

# Foo.bar in production mode (missing action)
(
    t.get_ok('/foo/baz')
    .status_is(500)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Not development mode error!')
)

# Try to access a file which is not under the web root via path traversal in
# production mode
(
    t.get_ok('/../../Pyjoyment/secret.txt')
    .status_is(404)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Page Not Found')
)

# Try to access a file which is not under the web root via path traversal in
# production mode (triple dot)
(
    t.get_ok('/.../Pyjoyment/secret.txt')
    .status_is(404)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Page Not Found')
)

# Try to access a file which is not under the web root via path traversal in
# production mode (backslashes)
(
    t.get_ok('/..\\..\\Pyjoyment\\secret.txt')
    .status_is(404)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Page Not Found')
)

# Try to access a file which is not under the web root via path traversal in
# production mode (escaped backslashes)
(
    t.get_ok('/..%5C..%5CPyjoyment%5Csecret.txt')
    .status_is(404)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Page Not Found')
)

# Check that backslashes in query or fragment parts don't block access in
# production mode
t.get_ok('/hello.txt?one=\\1#two=\\2').status_is(200).content_like(r'Hello Mojo from a static file!')

# Embedded production static file
(
    t.get_ok('/some/static/file.txt')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('Production static file with low precedence.\n\n')
)

# Embedded production template
(
    t.get_ok('/just/some/template')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('Production template with low precedence.\n')
)

# PyjoymentTest3.Bar.index (controller class in development namespace)
(
    t.get_ok('/test9', {'X-Test': 'Hi there!'})
    .status_is(500)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_like(r'Not development mode error!')
)

# PyjoymentTest.Baz.index (controller class precedence)
(
    t.get_ok('/test10')
    .status_is(200)
    .header_is('Server', 'Pyjoyment (Python)')
    .content_is('Production namespace has low precedence!')
)

done_testing()
