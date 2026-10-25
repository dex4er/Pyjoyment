Testing
=======

Web Application Testing Made Easy.

This document is an introduction to testing web applications with
:mod:`Pyjo.Test.Pyjo`. :mod:`Pyjo.Test.Pyjo` can be thought of as a module
that provides all of the tools and testing assertions needed to test web
applications in a Python-ish way.

While :mod:`Pyjo.Test.Pyjo` can be used to test any web application, it has
shortcuts designed to make testing :mod:`Pyjoyment` web applications easy
and pain-free.

Please refer to the :mod:`Pyjo.Test.Pyjo` documentation for a complete
reference to many of the ideas and syntax introduced in this document.

A test file for a simple web application might look like:

.. literalinclude:: testing/celestial.py
    :language: python
    :caption: t/celestial.py

In the rest of this document we'll explore these concepts and others related
to :mod:`Pyjo.Test.Pyjo`.

Concepts
--------

Essentials every :mod:`Pyjoyment` developer should know.

Test scripts
~~~~~~~~~~~~

A test of Pyjoyment is a Python script of its own, usually in the ``t``
directory of the application, which runs from its start to its end, as any
script does, and prints the results of its tests to the standard output in
the `Test Anything Protocol <https://testanything.org/>`_ (TAP). The
functions of :mod:`Pyjo.Test` print them:

.. code-block:: python
    :caption: t/equal.py

    from Pyjo.Test import *

    is_ok(1 + 1, 3, 'addition')

    with subtest('Strings'):
        ok('Pyjo'.startswith('P'), 'starts with P')
        is_ok('Pyjo'.lower(), 'pyjo', 'lower case')

    done_testing()

Each assertion is a test, which prints a line ``ok`` or ``not ok`` with its
number and its description. A failed test does not stop the script, as an
``assert`` would: its diagnostic message, with the got and the expected
values, goes to the standard error, and the script goes on with the next
test. A subtest groups tests, which it numbers on its own and indents, and
counts as one test, which passes when all of its tests pass.
:func:`~Pyjo.Test.done_testing` ends the output with the plan, ``1..2``, the
number of the tests that ran, so that a script that dies in the middle is not
taken for one that passed:

.. code-block:: console

    $ python t/equal.py
    not ok 1 - addition
    #   Failed test 'addition'
    #   at /home/user/my_app/t/equal.py line 3.
    #          got: 2
    #     expected: 3
    # Subtest: Strings
        ok 1 - starts with P
        ok 2 - lower case
        1..2
    ok 2 - Strings
    1..2
    # Looks like you failed 1 test of 2.

The exit status of the script is the number of its failed tests, here ``1``,
and ``0`` when all of them passed. Each script runs in a process of its own,
with an interpreter, an event loop and an environment of its own, so that
what one script does to them does not break another one.

The harness
~~~~~~~~~~~

A test harness runs many test scripts, reads their TAP output and their exit
status, and reports which of them failed and why. It is the harness that
checks that a script declared its plan and ran as many tests as it planned.
:mod:`Pyjo.Prove`, the command ``pyjo-prove``, is the harness of Pyjoyment,
inspired by Perl's ``prove``, which runs the same scripts too, as their
output is standard TAP. pytest is one as well, through the plugin
:mod:`Pyjo.Test.pytest_plugin`, which runs each script as a test of its own.
`Running`_ shows how to use them.

A harness tells its scripts that they run under it with
``PYJO_HARNESS_ACTIVE``, and with ``PYJO_HARNESS_IS_VERBOSE`` that its output
is verbose, which makes :mod:`Pyjo.Test.Pyjo` log everything that the
application does.

Pyjo.Test.Pyjo at a glance
~~~~~~~~~~~~~~~~~~~~~~~~~~

The :mod:`Pyjo.Test` module of Pyjoyment includes several primitive test
assertions, such as ``ok``, ``is_ok``, ``isnt_ok``, ``like_ok``,
``unlike_ok``, ``cmp_ok``, etc., named after those of Perl's ``Test::More``.
An assertion "passes" if its expression returns a true value. The assertion
function prints "ok" or "not ok" if an assertion passes or fails
(respectively).

:mod:`Pyjo.Test.Pyjo` supplies additional test assertions organized around
the web application request/response transaction (transport, response
headers, response bodies, etc.), and WebSocket communications.

One interesting thing of note: the return value of :mod:`Pyjo.Test.Pyjo`
object assertions is always the test object itself, allowing us to "chain"
test assertion methods. So rather than grouping related test statements like
this:

.. code-block:: python

    t.get_ok('/frogs')
    t.status_is(200)
    t.content_like(re.compile(r'bullfrog'))
    t.content_like(re.compile(r'hypnotoad'))

Method chaining allows us to connect test assertions that belong together:

.. code-block:: python

    (
        t.get_ok('/frogs')
        .status_is(200)
        .content_like(re.compile(r'bullfrog'))
        .content_like(re.compile(r'hypnotoad'))
    )

This makes for a much more *concise* and *coherent* testing experience:
concise because we are not repeating the invocant for each test, and coherent
because assertions that belong to the same request are syntactically bound in
the same method chain.

Occasionally it makes sense to break up a test to perform more complex
assertions on a response. :mod:`Pyjo.Test.Pyjo` exposes the entire
transaction object so you can get all the data you need from a response:

.. code-block:: python

    t.put_ok('/bees', json={'type': 'worker', 'name': 'Karl'}).status_is(202).json_has('/id')

    # Pull out the id from the response
    newbee = t.tx.res.json('/id')

    # Make a new request with data from the previous response
    t.get_ok(f'/bees/{newbee}').status_is(200).json_is('/name', 'Karl')

The :mod:`Pyjo.Test.Pyjo` object is *stateful*. As long as we haven't
started a new transaction by invoking one of the ``*_ok`` methods, the
request and response objects from the previous transaction are available in
the :mod:`Pyjo.Test.Pyjo` object:

.. code-block:: python

    # First transaction
    (
        t.get_ok('/frogs?q=bullfrog', {'Content-Type': 'application/json'})
        .status_is(200)
        .json_like('/0/species', re.compile(r'(?i)catesbeianus'))
    )

    # Still first transaction
    t.content_type_is('application/json;charset=UTF-8')

    # Second transaction
    (
        t.get_ok('/frogs?q=banjo', {'Content-Type': 'text/html'})
        .status_is(200)
        .content_like(re.compile(r'(?i)interioris'))
    )

    # Still second transaction
    t.content_type_is('text/html;charset=UTF-8')

This statefulness also enables :mod:`Pyjo.Test.Pyjo` to handle sessions,
follow redirects, and inspect past responses during a redirect.

The Pyjo.Test.Pyjo object
~~~~~~~~~~~~~~~~~~~~~~~~~

The :mod:`Pyjo.Test.Pyjo` object manages the Pyjoyment application
lifecycle (if a Pyjoyment application class is supplied) as well as exposes
the built-in :mod:`Pyjo.UserAgent` object. To create a bare
:mod:`Pyjo.Test.Pyjo` object:

.. code-block:: python

    t = Pyjo.Test.Pyjo.new()

This object initializes a :mod:`Pyjo.UserAgent` object and provides a
variety of test assertion methods for accessing a web application. For
example, with this object, we could test any running web application:

.. code-block:: python

    t.get_ok('https://www.google.com/').status_is(200).content_like(re.compile(r'(?i)search'))

You can access the user agent directly if you want to make web requests
without triggering test assertions:

.. code-block:: python

    tx = t.ua.post('https://duckduckgo.com/html', form={'q': 'pyjoyment'})
    tx.result.dom().find('a.result__a').each(lambda e, num: print(e.text))

See :mod:`Pyjo.UserAgent` for the complete API and return values.

Testing Pyjoyment applications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you pass the name of a :mod:`Pyjoyment` application class (e.g.,
``'MyApp'``) to the :mod:`Pyjo.Test.Pyjo` constructor,
:mod:`Pyjo.Test.Pyjo` will instantiate the class and start it, and cause it
to listen on a random (unused) port number. Testing a Pyjoyment application
using :mod:`Pyjo.Test.Pyjo` will never conflict with running applications,
including the application you're testing.

The :mod:`Pyjo.UserAgent` object in :mod:`Pyjo.Test.Pyjo` will know where
the application is running and make requests to it. Once the tests have
completed, the :mod:`Pyjoyment` application will be torn down.

.. code-block:: python

    # Listens on localhost:32114 (some unused TCP port)
    t = Pyjo.Test.Pyjo.new('Frogs')

To test a :mod:`Pyjoyment.Lite` application, pass the file path to the
application script to the constructor.

.. code-block:: python

    # Load application script relative to the "t" directory
    from Pyjo.File import curfile

    t = Pyjo.Test.Pyjo.new(curfile().dirname().sibling('myapp.py'))

The object initializes a :mod:`Pyjo.UserAgent` object, loads the Pyjoyment
application, binds and listens on a free TCP port (e.g., 32114), and starts
the application event loop. When the :mod:`Pyjo.Test.Pyjo` object (``t``)
goes out of scope, the application is stopped, or at the end of a ``with``
block, which closes its connections and servers right away.

Relative URLs in the test object method assertions (``get_ok``,
``post_ok``, etc.) will be sent to the Pyjoyment application started by
:mod:`Pyjo.Test.Pyjo`:

.. code-block:: python

    # Rewritten to "http://localhost:32114/frogs"
    t.get_ok('/frogs')

:mod:`Pyjo.Test.Pyjo` has a lot of handy shortcuts built into it to make
testing :mod:`Pyjoyment` or :mod:`Pyjoyment.Lite` applications enjoyable.

An example
^^^^^^^^^^

Let's spin up a Pyjoyment application using ``pyjo generate app MyApp``. The
``pyjo`` utility will create a working application and a ``t`` directory
with a working test file:

.. code-block:: console

    $ pyjo generate app MyApp
      [mkdir] /my_app/MyApp
      [write] /my_app/MyApp/__main__.py
      ...
      [mkdir] /my_app/t
      [write] /my_app/t/basic.py
      ...

Let's run the tests (with ``-v`` the log of the application is shown too,
which ``PYJO_LOG_LEVEL=fatal`` quiets):

.. code-block:: console

    $ cd my_app
    $ PYJO_LOG_LEVEL=fatal pyjo-prove -lv t
    t/basic.py ..
    ok 1 - GET /
    ok 2 - 200 OK
    ok 3 - content is similar
    1..3
    t/basic.py ... ok
    All tests successful.
    Files=1, Tests=3, 0 wallclock secs
    Result: PASS

The boilerplate test file looks like this:

.. code-block:: python

    from Pyjo.Test import *

    import Pyjo.Test.Pyjo


    t = Pyjo.Test.Pyjo.new('MyApp')
    t.get_ok('/').status_is(200).content_like(r'(?i)Pyjoyment')

    done_testing()

Here we can see our application class name ``MyApp`` is passed to the
:mod:`Pyjo.Test.Pyjo` constructor. Under the hood, :mod:`Pyjo.Test.Pyjo`
creates a new :mod:`Pyjo.Server` instance, loads ``MyApp`` (which we just
created), and runs the application. We write our tests with relative URLs
because :mod:`Pyjo.Test.Pyjo` takes care of getting the request to the
running test application (since its port may change between runs).

Testing with configuration data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We can alter the behavior of our application using environment variables
(such as ``PYJO_MODE``) and through configuration values. One nice feature of
:mod:`Pyjo.Test.Pyjo` is its ability to pass configuration values directly
from its constructor.

Let's modify our application and add a "feature flag" to enable a new
feature when the ``enable_weather`` configuration value is set:

.. literalinclude:: testing/weather/MyApp/__init__.py
    :language: python
    :caption: MyApp/__init__.py
    :emphasize-lines: 19-24

To test this new feature, we don't even need to create a configuration
file—we can simply pass the configuration data to the application directly
via the constructor of :mod:`Pyjo.Test.Pyjo`:

.. code-block:: python

    t = Pyjo.Test.Pyjo.new('MyApp', {'enable_weather': 1})
    t.get_ok('/').status_is(200).content_like(re.compile(r'(?i)Pyjoyment'))
    t.get_ok('/weather').status_is(200).content_like(re.compile(r'🔥'))

When we run these tests, :mod:`Pyjo.Test.Pyjo` will pass this configuration
data to the application, which will cause it to create a special
``/weather`` route that we can access in our tests. Unless
``enable_weather`` is set in a configuration file, this route will not exist
when the application runs. Feature flags like this allow us to do soft
rollouts of features, targeting a small audience for a period of time. Once
the feature has been proven, we can refactor the conditional and make it a
full release.

This example shows how easy it is to start testing a Pyjoyment application
and how to set specific application configuration directives from a test
file.

Testing application helpers
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Let's say we register a helper in our application to generate an HTTP Basic
Authorization header:

.. code-block:: python

    from Pyjo.Util import b64_encode


    @app.helper('basic_auth')
    def basic_auth(c, *values):
        return {'Authorization': 'Basic ' + b64_encode(':'.join(values).encode(), '')}

How do we test application helpers like this? :mod:`Pyjo.Test.Pyjo` has
access to the application object, which allows us to invoke helpers from our
test file:

.. code-block:: python

    t = Pyjo.Test.Pyjo.new('MyApp')

    is_deeply_ok(
        t.app.basic_auth('bif', "Bif's Passwerdd"),
        {'Authorization': 'Basic YmlmOkJpZidzIFBhc3N3ZXJkZA=='},
        'correct header value',
    )

Any aspect of the application (helpers, plugins, routes, etc.) can be
introspected from :mod:`Pyjo.Test.Pyjo` through the application object. This
enables us to get deep test coverage of :mod:`Pyjoyment`-based applications.

Running
-------

The ways to run the test scripts of an application.

A single test script
~~~~~~~~~~~~~~~~~~~~

A test script runs on its own, as any Python script, with the directory of
the application in ``PYTHONPATH``, so that it finds the modules of the
application:

.. code-block:: console

    $ PYTHONPATH=. python t/basic.py
    ok 1 - GET /
    ok 2 - 200 OK
    ok 3 - content is similar
    1..3

pyjo-prove
~~~~~~~~~~

``pyjo-prove``, or ``python -m Pyjo.Prove``, runs the test scripts of a
directory, ``t`` by default, and prints a line for each of them and a
summary:

.. code-block:: console

    $ pyjo-prove -l t
    t/basic.py ... ok
    All tests successful.
    Files=1, Tests=3, 0 wallclock secs
    Result: PASS

``-l`` adds the current directory to ``PYTHONPATH``, ``-r`` runs the scripts
of the subdirectories too, ``-v`` prints the TAP output of each script,
``-j 4`` runs four scripts at the same time and ``-j 0`` as many as the
processors, and ``--timeout 60`` kills a script that runs longer than a
minute:

.. code-block:: console

    $ pyjo-prove -l -r -j 0 --timeout 60 t

In CI, the formatter ``junit`` writes the JUnit XML of the results, which the
reporters of CI systems read, and ``markdown`` a summary, as the one of a job
of GitHub Actions, to the file after ``=``, next to the usual output. The
diagnostics of the failures in them come from the standard error of the
scripts, which ``--capture-stderr`` captures:

.. code-block:: console

    $ pyjo-prove -l -r --capture-stderr --formatter junit=report.xml --formatter "markdown=$GITHUB_STEP_SUMMARY" t

Perl's ``prove`` runs them as well:

.. code-block:: console

    $ PYTHONPATH=. prove --ext=py --exec=python -r t

:mod:`Pyjo.Prove` describes all of its options.

pytest
~~~~~~

pytest runs the test scripts too, where it is installed, through the plugin
:mod:`Pyjo.Test.pytest_plugin`, as a test explorer of an IDE or a coding
agent runs them. Each script is a test of pytest, whose failure shows the
failed tests of the script with their diagnostic messages. The
``pyproject.toml`` of ``pyjo generate app`` has pytest and pytest-xdist in the
dependency group ``dev``, which ``uv`` installs, and names ``t`` in
``testpaths``, so ``uv run pytest`` runs it:

.. code-block:: console

    $ uv run pytest
    ...
    t/basic.py .                                                       [100%]

pytest runs its tests one after another, and pytest-xdist several at the same
time, as ``-j`` of ``pyjo-prove`` does:

.. code-block:: console

    $ uv run pytest -n auto

A test of pytest uses :mod:`Pyjo.Test.Pyjo` through the fixture ``t``, made
of the application of the fixture ``app``, and its first failed test raises
:exc:`AssertionError` with the description, the got and the expected values:

.. code-block:: python

    # tests/conftest.py
    import pytest


    @pytest.fixture
    def app():
        return 'MyApp'


    # tests/test_basic.py
    def test_index(t):
        t.get_ok('/').status_is(200).content_like(r'(?i)Pyjoyment')

Such tests go to a directory of their own, as ``tests``, since ``pyjo-prove``
runs every script of ``t``:

.. code-block:: console

    $ uv run pytest tests
    ...
    tests/test_basic.py .                                              [100%]

:mod:`Pyjo.Test.pytest_plugin` says what else differs from a test script.

Assertions
----------

This section describes the basic test assertions supplied by
:mod:`Pyjo.Test.Pyjo`. There are four broad categories of assertions for
HTTP requests:

* HTTP requests

* HTTP response status

* HTTP response headers

* HTTP response content/body

WebSocket test assertions are covered in `Testing WebSocket web services`_.

Basic assertions
~~~~~~~~~~~~~~~~

The assertions of :mod:`Pyjo.Test.Pyjo` are made of the functions of
:mod:`Pyjo.Test`, which a test script uses for whatever else it checks, as
the value of a helper or a part of a response. Each of them is a test, takes
its description as the last argument, and returns whether it passed:

.. code-block:: python

    from Pyjo.Test import *

    import re

    ok(1 + 1 == 2, 'a true value')
    is_ok(int('42'), 42, 'equal, with ==')
    isnt_ok('pyjo', 'mojo', 'not equal, with !=')
    like_ok('Hello Pyjo', r'Pyjo$', 'matches a regular expression')
    unlike_ok('Hello Pyjo', re.compile(r'(?i)mojo'), "doesn't match a regular expression")
    cmp_ok(3, '<', 4, 'compared with an operator')
    is_deeply_ok({'a': [1, 2]}, {'a': [1, 2]}, 'the same data structure')
    isa_ok([], list, 'an instance of a class')
    in_ok(['foo', 'bar'], 'foo', 'contains an element')
    not_in_ok({'a': 1}, 'b', "doesn't contain an element")
    none_ok({}.get('missing'), 'None')
    throws_ok(lambda: int('x'), ValueError, 'raises an exception')
    pass_ok('passes always')

    done_testing()

They have the names of the functions of Perl's ``Test::More``, with the
suffix ``_ok``, as ``is`` is a keyword of Python: ``is_ok`` for ``is`` and
``is_deeply_ok`` for ``is_deeply``. A failed one shows what differs: the got
and the expected values, or for :func:`~Pyjo.Test.is_deeply_ok` the place in
the structures where they begin to differ.

The ones that test a value return a :class:`~Pyjo.Test.Result`, which is
true when the test passed, and whose methods test the same value again, with
the names of ``Test::More``, so that the tests of one value chain, as the
assertions of :mod:`Pyjo.Test.Pyjo` do. :func:`~Pyjo.Test.that` starts a
chain with no test of its own:

.. code-block:: python

    isa_ok(int('42'), int, 'an integer').cmp('>', 0, 'positive').is_(42, 'the answer')
    that('Hello Pyjo').like(r'^Hello', 'a greeting').unlike(r'Mojo', 'not Mojo')

:func:`~Pyjo.Test.diag` prints a diagnostic message to the standard error,
which the harness shows, and :func:`~Pyjo.Test.note` a comment to the standard
output, which ``pyjo-prove`` shows with ``-v`` only:

.. code-block:: python

    if not is_ok(t.tx.res.code, 200, 'right status'):
        diag(t.tx.res.text)

:func:`~Pyjo.Test.plan` with ``skip_all`` skips the whole script, as one that
needs the network:

.. code-block:: python

    if not os.getenv('TEST_ONLINE'):
        plan(skip_all='set TEST_ONLINE to enable this test')

:mod:`Pyjo.Test` describes all of them.

HTTP request assertions
~~~~~~~~~~~~~~~~~~~~~~~

:mod:`Pyjo.Test.Pyjo` has a :mod:`Pyjo.UserAgent` object that allows it to
make HTTP requests and check for HTTP transport errors. HTTP request
assertions include ``get_ok``, ``post_ok``, etc. These assertions do not
test whether the request was handled *successfully*, only that the web
application handled the request in an HTTP compliant way.

You may also make HTTP requests using custom verbs (beyond ``GET``,
``POST``, ``PUT``, etc.) by building your own transaction object. See
`Custom transactions`_ below.

Using HTTP request assertions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To post a URL-encoded form to the ``/calls`` endpoint of an application, we
simply use the ``form`` content type shortcut:

.. code-block:: python

    t.post_ok('/calls', form={'to': '+43.55.555.5555'})

Which will create the following HTTP request:

.. code-block:: text

    POST /calls HTTP/1.1
    Content-Length: 20
    Content-Type: application/x-www-form-urlencoded

    to=%2B43.55.555.5555

The ``*_ok`` HTTP request assertion methods accept the same arguments as
their corresponding :mod:`Pyjo.UserAgent` methods (except for the callback
argument). This allows us to set headers and build query strings for
authentic test situations:

.. code-block:: python

    t.get_ok('/internal/personnel', {'Authorization': 'Token secret-password'}, form={'q': 'Professor Plum'})

which generates the following request:

.. code-block:: text

    GET /internal/personnel?q=Professor+Plum HTTP/1.1
    Authorization: Token secret-password

The ``form`` content generator (see :mod:`Pyjo.UserAgent.Transactor`) will
generate a query string for ``GET`` requests and
``application/x-www-form-urlencoded`` or ``multipart/form-data`` for POST
requests.

While these ``*_ok`` assertions make the HTTP *requests* we expect, they
tell us little about *how well* the application handled the request. The
application we're testing might have returned any content-type, body, or
HTTP status code (200, 302, 400, 404, 500, etc.) and we wouldn't know it.

:mod:`Pyjo.Test.Pyjo` provides assertions to test almost every aspect of the
HTTP response, including the HTTP response status code, the value of the
``Content-Type`` header, and other arbitrary HTTP header information.

HTTP response status code
~~~~~~~~~~~~~~~~~~~~~~~~~

While not technically an HTTP header, the status line is the first line in an
HTTP response and is followed by the response headers. Testing the response
status code is common in REST-based and other web applications that use the
HTTP status codes to broadly indicate the type of response the server is
returning.

Testing the status code is as simple as adding the ``status_is`` assertion:

.. code-block:: python

    t.post_ok('/doorbell', form={'action': 'ring once'}).status_is(200)

Along with ``status_isnt``, this will cover most needs. For more elaborate
status code testing, you can access the response internals directly:

.. code-block:: python

    t.post_ok('/doorbell', form={'action': 'ring once'})
    is_ok(t.tx.res.message, 'Moved Permanently', 'try next door')

HTTP response headers
~~~~~~~~~~~~~~~~~~~~~

:mod:`Pyjo.Test.Pyjo` allows us to inspect and make assertions about HTTP
response headers. The ``Content-Type`` header is commonly tested and has its
own assertion:

.. code-block:: python

    t.get_ok('/map-of-the-world.pdf').content_type_is('application/pdf')

This is equivalent to the more verbose:

.. code-block:: python

    t.get_ok('/map-of-the-world.pdf').header_is('Content-Type', 'application/pdf')

We can test for multiple headers in a single response using method chains:

.. code-block:: python

    (
        t.get_ok('/map-of-the-world.pdf')
        .content_type_is('application/pdf')
        .header_isnt('Compression', 'gzip')
        .header_unlike('Server', re.compile(r'(?i)IIS'))
    )

HTTP response content assertions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:mod:`Pyjo.Test.Pyjo` also exposes a rich set of assertions for testing the
body of a response, whether that body be HTML, plain-text, or JSON. The
``content_*`` methods look at the body of the response as plain text (as
defined by the response's character set):

.. code-block:: python

    t.get_ok('/scary-things/spiders.json').content_is('{"arachnid":"brown recluse"}')

Although this is a JSON document, ``content_is`` treats it as if it were a
text document. This may be useful for situations where we're looking for a
particular string and not concerned with the structure of the document. For
example, we can do the same thing with an HTML document:

.. code-block:: python

    t.get_ok('/scary-things/spiders.html').content_like(re.compile(r'<title>All The Spiders</title>'))

But because :mod:`Pyjo.Test.Pyjo` has access to everything that
:mod:`Pyjo.UserAgent` does, we can introspect JSON documents as well as
DOM-based documents (HTML, XML) with assertions that allow us to check for
the existence of elements as well as inspect the content of text nodes.

JSON response assertions
^^^^^^^^^^^^^^^^^^^^^^^^

The :mod:`Pyjo.UserAgent` of :mod:`Pyjo.Test.Pyjo` has access to a JSON
parser, which allows us to test to see if a JSON response contains a value at
a location in the document using JSON pointer syntax:

.. code-block:: python

    t.get_ok('/animals/friendly.json').json_has('/beings/jeremiah/age')

This assertion tells us that the ``friendly.json`` document contains a value
at the ``/beings/jeremiah/age`` JSON pointer location. We can also inspect
the value at JSON pointer locations:

.. code-block:: python

    (
        t.get_ok('/animals/friendly.json')
        .json_has('/beings/jeremiah/age')
        .json_is('/beings/jeremiah/age', 42)
        .json_like('/beings/jeremiah/species', re.compile(r'(?i)bullfrog'))
    )

JSON pointer syntax makes testing JSON responses simple and readable.

DOM response assertions
^^^^^^^^^^^^^^^^^^^^^^^

We can also inspect HTML and XML responses using the :mod:`Pyjo.DOM` parser
in the user agent. Here are a few examples from the :mod:`Pyjo.Test.Pyjo`
documentation:

.. code-block:: python

    t.text_is('div.foo[x=y]', 'Hello!')
    t.text_is('html head title', 'Hello!', 'right title')

The :mod:`Pyjo.DOM` parser uses the CSS selector syntax described in
:mod:`Pyjo.DOM.CSS`, allowing us to test for values in HTML and XML documents
without resorting to typically verbose and inflexible DOM traversal methods.

Advanced topics
---------------

This section describes some complex (but common) testing situations that
:mod:`Pyjo.Test.Pyjo` excels in making simple.

Redirects
~~~~~~~~~

The :mod:`Pyjo.UserAgent` object in :mod:`Pyjo.Test.Pyjo` can handle HTTP
redirections internally to whatever level you need. Let's say we have a web
service that redirects ``/1`` to ``/2``, ``/2`` redirects to ``/3``, ``/3``
redirects to ``/4``, and ``/4`` redirects to ``/5``:

.. code-block:: text

    GET /1

returns:

.. code-block:: text

    302 Found
    Location: /2

and:

.. code-block:: text

    GET /2

returns:

.. code-block:: text

    302 Found
    Location: /3

and so forth, up to ``/5``:

.. code-block:: text

    GET /5

which returns the data we wanted:

.. code-block:: text

    200 OK

    {"message":"this is five"}

We can tell the user agent in :mod:`Pyjo.Test.Pyjo` how to deal with
redirects. Each test is making a request to ``GET /1``, but we vary the
number of redirects the user agent should follow with each test:

.. code-block:: python

    t = Pyjo.Test.Pyjo.new()

    t.get_ok('/1').header_is('location', '/2')

    t.ua.max_redirects = 1
    t.get_ok('/1').header_is('location', '/3')

    t.ua.max_redirects = 2
    t.get_ok('/1').header_is('location', '/4')

    # Look at the previous hop
    is_ok(t.tx.previous.res.headers.location, '/3', 'previous redirect')

    t.ua.max_redirects = 3
    t.get_ok('/1').header_is('location', '/5')

    t.ua.max_redirects = 4
    t.get_ok('/1').json_is('/message', 'this is five')

When we set ``max_redirects``, it stays set for the life of the test object
until we change it.

The handling of HTTP redirects of :mod:`Pyjo.Test.Pyjo` eliminates the need
for making many, sometimes an unknown number, of redirections to keep testing
precise and easy to follow (ahem).

Cookies and session management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We can use :mod:`Pyjo.Test.Pyjo` to test applications that keep session
state in cookies. By default, the :mod:`Pyjo.UserAgent` object in
:mod:`Pyjo.Test.Pyjo` will manage session for us by saving and sending
cookies automatically, just like common web browsers:

.. literalinclude:: testing/login.py
    :language: python
    :caption: t/login.py

We can also inspect cookies in responses for special values through the
transaction's response (:mod:`Pyjo.Message.Response`) object:

.. code-block:: python

    t.get_ok('/')
    like_ok(str(t.tx.res.cookie('smarty')), re.compile(r'smarty=pants'), 'cookie found')

Custom transactions
~~~~~~~~~~~~~~~~~~~

Let's say we have an application that responds to a new HTTP verb ``RING``
and to use it we must also pass in a secret cookie value. This is not a
problem. We can test the application by creating a
:mod:`Pyjo.Transaction` object, setting the cookie (see
:mod:`Pyjo.Message.Request`), then passing the transaction object to
``request_ok``:

.. code-block:: python

    # Use custom "RING" verb
    tx = t.ua.build_tx('RING', '/doorbell')

    # Set a special cookie
    tx.req.cookies({'name': 'Secret', 'value': "don't tell anybody"})

    # Make the request
    t.request_ok(tx).status_is(200).json_is('/status', 'ding dong')

Testing WebSocket web services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While the message flow on WebSocket connections can be rather dynamic, it
more often than not is quite predictable, which allows this rather pleasant
WebSocket API of :mod:`Pyjo.Test.Pyjo` to be used:

.. literalinclude:: testing/echo.py
    :language: python
    :caption: t/echo.py

Because of their inherent asynchronous nature, testing WebSocket
communications can be tricky. The WebSocket assertions of
:mod:`Pyjo.Test.Pyjo` serialize messages via event loop primitives. This
enables us to treat WebSocket messages as if they were using the same
request-response communication pattern we're accustomed to with HTTP.

To illustrate, let's walk through these tests. In the first test, we use the
``websocket_ok`` assertion to ensure that we can connect to our
application's WebSocket route at ``/echo`` and that it's "speaking"
WebSocket protocol to us. The next ``send_ok`` assertion tests the
connection again (in case it closed, for example) and attempts to send the
message ``Hello Pyjo!``. The next assertion, ``message_ok``, blocks (using
the :mod:`Pyjo.IOLoop` singleton in the application) and waits for a
response from the server. The response is then compared with
``'echo: Hello Pyjo!'`` in the ``message_is`` assertion, and finally we close
and test our connection status again with ``finish_ok``.

The second test is like the first, but now we're sending and expecting JSON
documents at ``/echo.json``. In the ``send_ok`` assertion we take advantage
of the JSON content generator of :mod:`Pyjo.UserAgent` (see
:mod:`Pyjo.UserAgent.Transactor`) to marshal dicts and lists into JSON
documents, and then send them as a WebSocket message. We wait (block) for a
response from the server with ``message_ok``. Then because we're expecting a
JSON document back, we can leverage ``json_message_is`` which parses the
WebSocket response body and returns an object we can access through
:mod:`Pyjo.JSON.Pointer` syntax. Then we close (and test) our WebSocket
connection.

Testing WebSocket servers does not get any simpler than with
:mod:`Pyjo.Test.Pyjo`.

Extending Pyjo.Test.Pyjo
~~~~~~~~~~~~~~~~~~~~~~~~

If you see that you're writing a lot of test assertions that aren't
chainable, you may benefit from writing your own test assertions. Let's say
we want to test the ``Location`` header after a redirect. We'll create a
subclass of :mod:`Pyjo.Test.Pyjo` that implements a test assertion named
``location_is``, as Python does with classes what Perl does with roles:

.. literalinclude:: testing/TestLocation.py
    :language: python
    :caption: TestLocation.py

When we make new test assertions, we want to use method signatures that
match other ``*_is`` methods in :mod:`Pyjo.Test.Pyjo`, so here we accept the
test object, the value to compare, and an optional description.

We assign a default description value (``desc``), then we use
:meth:`~Pyjo.Test.Pyjo.Pyjo_Test_Pyjo.test` to compare the location header
with the expected header value, and finally propagates the
:mod:`Pyjo.Test.Pyjo` object for method chaining.

With this new class, we're ready to create a new test object that has the
assertion:

.. code-block:: python

    import TestLocation

    t = TestLocation.new('MyApp')

    (
        t.post_ok('/redirect/pyjo', json={'message': 'Pyjo, here I come!'})
        .status_is(302)
        .location_is('https://pyjoyment.readthedocs.io')
        .otherwise(lambda t: diag('I miss tempire.'))
    )

In this section we've covered how to add custom test assertions to
:mod:`Pyjo.Test.Pyjo` with a subclass and how to use it to simplify testing.

More
----

You can continue with :doc:`index` now or take a look at the `Mojolicious
wiki <https://github.com/mojolicious/mojo/wiki>`_, which contains a lot more
documentation and examples by many different authors.

Ported from `Mojolicious::Guides::Testing
<https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Guides/Testing.pod>`_
of Mojolicious 9.49.
