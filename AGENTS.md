# Agent Guide: Pyjoyment

## Overview

Pyjoyment is a port of [Mojolicious](https://mojolicious.org) to Python. The
`Pyjo` package mirrors the `Mojo::*` toolkit (URL, DOM, HTTP messages, user
agent, servers, event loop), and the `Pyjoyment` package is reserved for the
`Mojolicious::*` framework layer (routes, controllers, renderer, `Lite`).

`Pyjo` does not import `Pyjoyment`. Where a module of `Pyjo`, as an adapter
of another framework, needs what only the framework has, as the static files
of `reply.file` or its exception page, it takes it from the controller that a
route gives it, as `c.helpers.reply.file`, and goes without it when it runs
on its own.

The code was written against Mojo 6.x. The project is being revived: the
target is Mojolicious 9 on Python 3.12+, with asyncio as the only I/O core.
The plan, its order and its progress live in GitHub Issues, starting from the
open umbrella issue about the revival; this file describes how the project
works and why, not what is left to do.

## Design Principles

These are deliberate. A change that looks like a cleanup but goes against one
of them is a regression.

- **The spirit of Mojo over strict PEP 8.** Pyjoyment uses Python creatively,
  the way Mojo bends Perl. Module and class names follow Mojo
  (`Pyjo.URL`, `Pyjo.IOLoop.Client`), objects are created with `Class.new()`,
  and setters return `self` so calls chain. The constructor of Python is
  correct too: a module ends with `new = Pyjo_URL.new`, `object = Pyjo_URL`
  and the class under the name of the module, `URL = Pyjo_URL`, so that
  `from Pyjo.URL import URL` and `URL(...)` work. The documentation keeps
  `import Pyjo.URL` and `Pyjo.URL.new(...)`, as the Google Python Style Guide
  imports modules, not classes. A module has no such name where it would
  hide a builtin (`Pyjo.Exception`), the package (`Pyjo.Test.Pyjo`,
  `Pyjoyment`) or a name that the module has (`TLS` of `Pyjo.IOLoop.TLS`,
  `Template` of `Pyjo.String.Template`), and a module of a command is named
  after the command, not after a class.
- **Every statement has an expression form.** Helpers in `Pyjo.Util` such as
  `die`, `setenv`, `slurp` and `spurt` look redundant next to `raise`,
  `os.environ[...] = ...` and `pathlib`, but statements cannot appear in a
  lambda, a callback or a chain, and these can. Do not replace them with the
  standard library equivalent.
- **Every return value chains.** Functions return the framework's own types so
  the next method is available: `slurp` returns a string, `Collection.join`
  returns `Pyjo.String.Unicode`, DOM queries return `Pyjo.Collection`, and the
  assertions of `Pyjo.Test` return a `Pyjo.Test.Result`, which is true or
  false, as the `bool` of `Test::More`, and tests the value again, as the one
  that `that` makes of a value does. A
  function of the standard library that would wrap the chain from the front
  has a method form that continues it, such as `Collection.zip`, the
  conversions like `to_set()` and `Collection.get`, the expression form of an
  index with a default. A method that only repeats what a postfix operator
  does, like `item(0)` for `[0]`, is not needed.
- **Builtin types are never patched.** New types that subclass or mirror a
  standard one and add framework behaviour are welcome, even when they look
  redundant: `Pyjo.Collection(list)`, `Pyjo.String.Unicode(str)`,
  `Pyjo.String.Bytes(bytes)`, and `Pyjo.String.Mixin`, which lets URL, Path,
  Headers and others behave like strings. Monkey-patching `str`, `list` or any
  other builtin is not.
- **The standard library comes first at the boundary.** Inside, a module keeps
  Mojolicious' semantics; at its boundary, it works with the Python standard
  library. Constructors take the standard types
  (`Pyjo.URL.new(urlsplit(...))`, `Pyjo.Date.new(datetime(...))`), objects
  implement the protocols that the standard library's constructors use, with
  the meaning it expects (`float(date)` is the epoch), and explicit
  conversions are methods named after the library or the type
  (`url.to_urllib()`, `date.to_datetime()`). Where a Mojo method has the name
  of such a conversion, the conversion keeps it, and the Mojo method gets a
  name that says what it renders: Mojo's `to_datetime` is `to_rfc3339`.
- **Asyncio is the event loop, the reactor is where it is replaced.** Mojo's
  reactor exists because Perl has no standard event loop; Python has one.
  `Pyjo.Reactor.Asyncio` is the API of `Mojo::Reactor` on the asyncio event
  loop, so the I/O of Pyjoyment and the coroutines and tasks of asyncio run in
  the same loop. Only a reactor uses the event loop: everything else goes
  through the methods of `Pyjo.Reactor`, and ruff's TID251 rejects
  `import asyncio` outside `Pyjo/Reactor/`, the test harness, the tests and
  the examples. Another reactor, on uvloop, Trio, gevent or anything else,
  comes from another distribution, in the namespace `Pyjo.Reactor` that
  `extend_path` keeps open, and `PYJO_REACTOR` selects it, as
  `Mojo::Reactor::EV` replaces `Mojo::Reactor::Poll`. `Pyjo.Reactor.Poll`, the port of
  `Mojo::Reactor::Poll` on `select.poll`, or `select.select` on Windows, is a reactor without asyncio that
  runs the same tests, the example of such a reactor. Mojo 9 moved from
  callbacks and `Mojo::IOLoop::Delay` to promises and async/await; a promise
  is a port of `Mojo::Promise`, which follows the Promise of ECMAScript, and
  awaiting it, the counterpart of Mojo's `AWAIT_*` methods, is `__await__`,
  which asks the reactor for what to wait on, so that it works with the event
  loop of any reactor.
- **Concurrency lives in the reactor and the servers.** The reactor runs the
  I/O, the timers and the coroutines, and the workers of
  `Pyjo.Server.Prefork` and `Pyjo.Server.Prethread` run what blocks, with
  `max_clients` as low as 1. Nothing else brings a concurrency of its own: an
  adapter of another framework, as `Pyjo.App.WSGI`, has no pool of threads
  and forks nothing, so a blocking WSGI application blocks the event loop, as
  any blocking operation does, `Pyjo.App.ASGI` runs its application with
  `run_coroutine` of the reactor, and `Pyjo.App.CGI` runs the program of
  each request, which a CGI program is, with `Pyjo.IOLoop.ChildProcess`,
  whose pipes the reactor reads and writes, and which it reaps with a timer,
  without waiting for it. `Pyjo.App.Lambda` runs an event function of
  AWS Lambda in a process of its own too, which gets its invocations one
  after another from a Runtime API that a server on the event loop serves,
  as an execution environment of Lambda does, as a handler called in the
  event loop could not run an event loop of its own, as Mangum does. A package that needs the next cycle of the
  event loop asks the reactor for it, and guards itself against being called
  again from inside the event loop. What only a server knows, as how it runs
  an application, which the flags `wsgi.multithread`, `wsgi.multiprocess`
  and `wsgi.run_once` say, comes from the server, through `server` of the
  application and the hook `before_server_start`, or from the environment of
  an outer WSGI server, best-effort, not from an environment variable, which
  every server of the process and its children would share. The end of a
  server is the counterpart of its start: `server_stopped` of the application
  and the hook `after_server_stop`, once the server has stopped gracefully,
  in each process and thread that has run the application, with the event
  loop no longer running, which the server runs until the promise that they
  return is settled. What an application starts for a server, as the
  lifespan of an ASGI application, ends there, not at the beginning of a
  graceful stop, while requests are still served, nor in `atexit`, which a
  worker of `Pyjo.Server.Prefork` leaves with `os._exit`, as the child of a
  fork has the handlers of the manager, and which comes after the loop of an
  ASGI server is closed.
- **Python 3.12 is the minimum, template strings come with 3.14.** t-strings
  (PEP 750) keep interpolations separate from the literal text, which gives
  templates auto-escaping without a template language. The `t"..."` syntax is
  written by the user, not by the library: the library only accepts
  `string.templatelib.Template` objects, so it supports them where the module
  exists and stays importable on Python 3.12 and 3.13, where PyPy is. On
  every Python, `t()` of `Pyjo.String.Template` takes a string with the
  fields of `str.format` in their place, without `eval`: a t-string is safe
  because it is code, not data, and a string that `eval` reads would run the
  code of whoever wrote it.
- **PyPy is supported on a best-effort basis.** Helper code for PyPy is fine,
  and a test may be skipped on PyPy where PyPy clearly differs from CPython,
  with the reason in the skip message.
- **No runtime dependencies.** Development tools are fine; `dependencies` in
  `pyproject.toml` stays empty.
- **What an area needs, in patterns that port.** The core is a complete set of
  components of its own, and each gives what its area needs, not the whole of
  a standard or of a library that it follows: `Pyjo.YAML` is the YAML of
  configuration files, the builder of `Pyjo.JSON.Schema` the part of zod
  that JSON Schema has, and its validation the keywords of JSON Schema 2020-12
  that the schemas of tools and of APIs have, which reports the others instead
  of ignoring them. Its API takes the patterns of the languages that code
  comes from, Perl and JavaScript, whose idioms Mojolicious shares, and Python,
  where they make the work easier, so that code of Mojolicious, of Node.js or
  of a library of Python ports with few changes: `Pyjo.JSON.Schema` takes the
  type hints of Python and the chains of zod. A feature that Mojolicious does
  not have is welcome by this measure.

## Development Environment

Tools are declared in `mise.toml` and pinned with checksums in `mise.lock`
(lockfile format 3, which needs mise 2026.9.16 or newer).

```sh
mise install
```

An agent shell does not inherit mise activation, so the `python` on its `PATH`
may not be the pinned one, and nothing warns about it: tests can pass on a
Python the project does not use. Run tools through mise:

```sh
mise exec -- python --version
```

`mise -C <dir>` (`--cd`) does not only take the tools of the `mise.toml` of
`<dir>`: it changes the working directory to `<dir>` before it runs the
command, so that the relative paths of the command, as of a test script, of
`PYTHONPATH=.` or of a file that the command writes, are taken from there,
not from the directory it is called in. Run the command from the checkout
without it, or give it absolute paths:

```sh
mise -C ../Pyjoyment exec -- python -m Pyjo.Prove -l t/Pyjo/URL.py  # t/ of ../Pyjoyment
```

`uv.lock` locks the Python dependencies; there are none at run time yet. After
a change to `pyproject.toml`, run `mise exec -- uv lock`; CI checks that the
lock matches with `uv lock --check`.

`mise install` re-locks only the platform it runs on. After changing a tool
version, run `mise lock` so every platform in `mise.lock` is refreshed; CI
installs with `--locked` and fails on a tool that is not in the lock.

`pyjo-reload` (`Pyjo.Server.Reload`) runs the application in a worker that is
an `os.fork` of its manager, and forks a new one when a file that it watches
changes: the script of the application, and `lib` and `templates` by default,
or the paths of `-w` in their place. Before the first fork, the manager imports
`Pyjo.Server.Reload` and starts the daemon whose listen sockets it keeps, which
loads most of the toolkit, as `Pyjo.JSON`, `Pyjo.IOLoop`, `Pyjo.UserAgent` and
`Pyjo.Server.Daemon`, and a worker inherits these modules as they were then.
Only the script of the application, and what it imports that the manager has
not loaded, as `Pyjoyment` and the package of a distribution, as `Pyjo.MCP`,
is loaded anew in each worker. So a change of a module of the toolkit, by an
edit of the checkout or by `uv sync` of a newer Pyjoyment, needs a restart of
`pyjo-reload` itself, not a change of a file that it watches, and so does a
change of an installed package, which it does not watch. The modules that the
manager loads are listed with:

```sh
PYTHONPATH=. mise exec -- python -c "import sys, Pyjo.Server.Reload as R; r = R.new(); r.daemon.listen = ['http://127.0.0.1:0']; r.daemon.start().stop(); print(sorted(m for m in sys.modules if m.startswith('Pyjo')))"
```

## Tests

The tests are scripts that print [TAP](https://testanything.org/), written
with `Pyjo.Test`, which is inspired by Perl's `Test::More`. They run with
`Pyjo.Prove`, a TAP harness inspired by Perl's `prove`:

```sh
mise exec -- python -m Pyjo.Prove -l -j 4 -r t
```

A single file runs on its own as well:
`PYTHONPATH=. mise exec -- python t/Pyjo/URL.py`. Perl's `prove` still works,
because the output is standard TAP: `.proverc` supplies its
`--ext=py --exec=python`, and `PYTHONPATH` the directory of the modules, as
the `-l` of `prove` adds `lib` to the path of Perl, not of Python:

```sh
PYTHONPATH=. mise exec -- prove -r -j 4 t
```

`.proverc` cannot set the variable itself: `prove` keeps the quotes of an
option of the file, so a command with arguments, as `env PYTHONPATH=. python`,
does not fit in its `--exec`.

A test that requests remote hosts, as `t/Pyjo/UserAgent_online.py`, is
skipped unless `TEST_ONLINE` is set, as in Mojolicious. Its hosts are those of
GitHub, which the runners of GitHub Actions reach the most reliably, as are
the pages that the examples of the guides request, where Mojolicious requests
its own site, which Pyjoyment does not have yet, so CI sets `TEST_ONLINE` in
every job of its matrix.

CI runs the tests with `--timeout 60`: a test script that hangs, such as a
reactor that never stops, is killed with the processes it started and fails
with its name, instead of the job running out of time. The slowest script
takes a few seconds.

A server that a test starts in a process of its own, as those of
`Pyjo.Server.Hot`, `Pyjo.Server.Reload` and `Pyjo.Server.Prefork`, listens on
a port of `port` of `t/lib/ServerStart.py`, not of `generate_port`, which is
free when it is found, but not necessarily when the process binds it a second
later: a server of a test that runs at the same time, which listens on a port
that the system picks, or an outgoing connection, whose local port the system
picks, can get it, and the test then takes that server for its own. The system
picks them from its ephemeral ports, from 32768 on Linux and 49152 on macOS
and Windows, so `port` finds one below them, and a lock of its byte in a file
of the temporary directory, with `fcntl` or the `msvcrt` of Windows, which the
system releases when the test ends, keeps it from the other tests. Such a test starts its server with `retry`, which tries
again on new ports when a port is taken anyway, and waits for it with a limit
of time, so that a server that does not start fails the test instead of
hanging it. A server that runs in the process of the test can listen on the
port 0 instead, which `ports()` gives.

- `t/Pyjo/` holds the module tests, ported from Mojo's `t/mojo/*.t`. A
  file has the name of Mojo's test with the part of the module as Pyjoyment
  names it: `reactor_detect.t` is `Reactor_detect.py`, `ioloop_tls.t` is
  `IOLoop_TLS.py`, and `tls.t` is `TLS.py`.
- `t/Pyjoyment/` holds the tests of the framework, ported from Mojo's
  `t/mojolicious/*.t` and named the same way: `types.t` is `Types.py`. A test
  of an application, as the `*_lite_app.t` ones, is not one of a module, so it
  keeps the name of Mojo, as a capital letter tells a module:
  `log_lite_app.t` is `log_lite_app.py`. `ojo.t` is in `t/Pyjo/`, as the
  functions of `ojo` are those of `Pyjo`, and so is `t/test/mojo.t`, the test
  of `Test::Mojo`, as `Test_Pyjo.py`.
- `t/certs/` holds the certificates of the tests, as `t/mojo/certs` in Mojo.
- `t/cookies/` holds the cookie files of the tests, as `t/mojo/cookies` in
  Mojo.
- `t/docs/` checks that the code in the module documentation is correct: it
  is the same code as in the docstrings, in the same order, with `print` and
  the comments that show a result turned into assertions. Documented code
  that prints TAP itself or ends the script, as in `Pyjo.Test`, runs as a
  script of its own, and the test checks its output and exit status.
  A test of a guide, as `guides_tutorial.py`, loads the applications of
  its examples from their files and checks what the guide says of them.
  `usages.py` checks the usages of the commands and of the scripts of the
  servers: their options are the ones that they pass to `getopt`, which it
  captures by running them with an unknown option in a temporary directory,
  and their blocks of options are laid out as `format_usage` of
  `Pyjo.GetOpt` lays them out, which a failure shows to paste.
- `t/stdlib/` checks the interaction with the Python standard library,
  written for Pyjoyment, as Mojolicious has no counterpart.
- `t/examples/` checks the code of some scripts of `examples/` with assertions,
  in versions of its own, in the directories of the groups of `examples/`,
  which `examples/README.md` lists. The scripts themselves are not run by the tests, as
  some need the network or libraries the project does not install; they are
  reviewed by hand, the Perl ones, the Mojolicious counterparts of the Python
  ones, against the target Mojolicious.
- `t/servers/` runs `Pyjo.Server.ASGI`, `Pyjo.Server.WSGI` and
  `Pyjo.Server.CGI` on real ASGI, WSGI and CGI servers, and the examples of
  the quick start in `README.md`, each in a process of its own, as the ASGI server of the tests in `t/lib` and the validator of
  `wsgiref` cannot show how a server differs, and mounts the applications of
  other frameworks, as Flask and Starlette, with `Pyjoyment.Plugin.Mount`, and
  an application of Pyjoyment on WSGI or on ASGI in one of `Pyjoyment.Lite`,
  as the examples `mount_wsgi_inception.py` and `mount_asgi_inception.py` do,
  on the WSGI and the ASGI servers, and PHP on php-fpm with
  `Pyjo.App.FastCGI` and on php-cgi with `Pyjo.App.CGI`, which `setup-php`
  installs in CI, and without which the tests are skipped, and Starlette on
  Mangum as an event function of AWS Lambda with `Pyjo.App.Lambda`, and the
  server of the MCP SDK of the example `mount_mcp.py`, which the client of the
  SDK calls, on the daemon and without sessions on the workers of prefork, and
  compares the schemas of the type hints of `Pyjo.JSON.Schema` with the ones
  of pydantic, which the MCP SDK gives its tools. The servers, the frameworks
  and pydantic are in the dependency group `servers`, not in
  `dependencies`; without it, the tests are skipped.
- `t/lib/` holds helpers shared by the tests. Run on their own, they skip with
  `plan(skip_all=...)`, so `-r t` reports them as skipped instead of failing.
- `tt/` holds the Python files that the tests use as data, as the templates
  of files of `Pyjoyment.Plugin.PyRenderer`, the modules of `tt/lib` and the
  applications of `tt/external`, which `Pyjoyment.Plugin.Mount` mounts,
  outside `t/`, as `-r t` runs every Python file there. `tt/templates_native` holds the ones with the
  t-strings of Python 3.14, which only the tests of 3.14 render, and which
  ruff and pyright check as Python 3.14. `tt/pytest` is a project of test
  scripts and tests of pytest, which the tests of
  `Pyjo.Test.pytest_plugin` copy to a temporary directory and run pytest
  on. A test does not write files into `t/` or `tt/`: what it makes goes to
  a temporary directory.

A test script imports the test functions and groups its tests in subtests,
like Mojo's tests do; Python keywords give some functions an `_ok` suffix
(`is_ok`, `isnt_ok`, `like_ok`, `is_deeply_ok`):

```python
from Pyjo.Test import *

import Pyjo.URL

with subtest('Simple'):
    url = Pyjo.URL.new('HtTp://Example.Com')
    is_ok(url.host, 'Example.Com', 'right host')

done_testing()
```

A test of the project ends with `done_testing()`, as Mojo's tests do, so that
the diff of a newer Mojolicious applies to it; `with plan():`, which issues the
plan at the end of its block, is for the tests of the code that uses
Pyjoyment, and for the tests of `Pyjo.Test` itself.

The exit status comes from an `atexit` handler that `Pyjo.Test` registers,
and only once a test function has been called, so importing the module (as
Sphinx does) has no effect. Older test files still wrap their body in
`if __name__ == '__main__':`, which is no longer needed.

The tests run on the reactor that `Pyjo.Reactor.detect()` gives, the asyncio
one, where Mojo's tests set `MOJO_REACTOR` to `Mojo::Reactor::Poll`. The
matrix of CI runs all of them on each Python a second time, in a job of its
own, on `Pyjo.Reactor.Poll`, as a reactor without asyncio has to pass them
too. A test of what needs the loop of asyncio, as `Pyjo.Server.ASGI`, whose
reactor runs in the loop of the ASGI server, or a coroutine that awaits
`asyncio.sleep`, is skipped on another reactor:

```sh
PYJO_REACTOR=Pyjo.Reactor.Poll mise exec -- python -m Pyjo.Prove -l -j 4 --capture-stderr --stderr-lines 1000 -r t
```

CI runs them on Windows too, on the Python of `mise.toml` and on both
reactors. A test of what Windows does not have, as `os.fork`, UNIX domain
sockets, the signals of POSIX, a command of a shell of POSIX or the mode of a
file, skips there with the reason. A test of paths compares them as Windows
makes them, with the drive, both separators and the short names of 8.3 that
`os.path.realpath` resolves, as `C:\Users\RUNNER~1` of the runner, and a test
that captures output reads it with LF, as Windows writes CRLF in text mode. A
test signals its own process with `signal.raise_signal`, as `os.kill` of
Windows terminates the process, and stops a server of a process of its own
with `CTRL_BREAK_EVENT` in a process group of its own, as Windows sends no INT
or TERM to one process, and the `python.exe` of a virtual environment is a
launcher that starts the interpreter as a process of its own, which outlives
for a moment a launcher that is terminated, with its files still open. It closes a file before it removes its directory, as
Windows removes no file that is open.

CI runs the tests in `t/servers` on Python 3.12 and 3.15, the oldest and the
newest supported, of setup-python, with the dependency group `servers`
installed by uv in `.venv`, so that the servers and their libraries are tested
on both ends; locally, `.venv-3.12` keeps the other version apart:

```sh
mise exec -- uv run --python 3.15 \
  --only-group servers python -m Pyjo.Prove -l --timeout 120 -r t/servers
UV_PROJECT_ENVIRONMENT=.venv-3.12 mise exec -- uv run --python 3.12 \
  --only-group servers python -m Pyjo.Prove -l --timeout 120 -r t/servers
```

A server is a library of its own, so the known differences of a server are
expected results with a comment: a fix of the server fails the test, which
tells that the documentation of `Pyjo.Server.ASGI`, `Pyjo.Server.WSGI` or
`Pyjo.Server.CGI` can change. The server processes do not get
`PYTHONWARNINGS` or `PYTHONDEVMODE`, as the warnings of the servers and their
libraries are not ours. Renovate bumps the dependency groups in one pull
request.

The schemas of `Pyjo.JSON.Schema` are compared with the ones of the libraries
that its two forms follow: `t/servers/JSON_Schema_pydantic.py` with pydantic,
for the type hints, and `t/Pyjo/JSON_Schema_zod.py` with `z.toJSONSchema()`
of zod, for the builder, whose code in JavaScript runs on the Node.js of
`mise.toml`, with zod of the `devDependencies` of `package.json`, which
`npm ci --ignore-scripts` installs, as the job of CI on the Python of
`mise.toml` does; without it, the test is skipped. A difference of a library,
as the bounds of the safe integers of JavaScript that zod gives an integer, is
left out by a normalization with a comment of its own, so that a new one fails
the test. A major release of zod needs no approval in the Dependency
Dashboard, as the test checks it.

The validation of `Pyjo.JSON.Schema` runs the official test suite of JSON
Schema, JSON-Schema-Test-Suite, for draft 2020-12, in
`t/Pyjo/JSON_Schema_suite.py`, from the files of the suite in `node_modules`,
which the same `npm ci` installs, so that the repository does not keep a copy
of them; without it, the test is skipped. The suite is not on npm, so the
`devDependencies` take it from its repository of GitHub, at a commit, not at
a tag: the tags of the suite, as `Test-JSON-Schema-Acceptance-1.039`, are not
versions that the manager of npm of Renovate updates, which skips them as an
unversioned reference, and a commit is a digest that it updates to the last
commit of the suite, with `package-lock.json`. The test lists the files and
the cases that it leaves out with the reason, as the keywords that the
validation does not support, and fails when a case that it leaves out passes,
so that a newer suite tells what the list can lose.

uWSGI is the package `uwsgi`, built from its source with a C compiler, as the
wheels of `pyuwsgi` have no plugin `cgi`. `extra-build-variables` in
`pyproject.toml` builds the plugin into it with `UWSGI_EMBED_PLUGINS=cgi`, and
uv keeps such a build apart from one without the variable in its cache.
`http.server --cgi` runs the CGI tests too, on a Python that still has
`CGIHTTPRequestHandler`, which Python 3.15 removed, as the run of CI on
Python 3.12.

The workflow Docker Smoke Test builds and runs the images of
`generate dockerfile`, for an application, a Lite script with
`pyproject.toml` and one with the inline metadata of PEP 723, and checks that
they serve their pages and stop gracefully on the TERM of `docker stop`: the
Lite script with `pyproject.toml` in an image of `generate dockerfile --port`,
which exposes its port, and the one with the inline metadata on the port of
`PORT` of the container, as Knative sets it, and the application in an image
of `generate dockerfile --graceful-timeout`, whose workers stop with it. Its
variant `lambda` runs a Lite script that ends with `handler = app.start()` as
an event function in the image of AWS Lambda for Python, whose emulator of the
Runtime API it invokes with the events of the payload formats 2.0 and 1.0,
and its variant `fastcgi` runs a Lite script that listens for FastCGI, with
`PYJO_LISTEN`, behind Caddy in a container of its own on the same network,
whose image `Dockerfile.caddy` pins, so that Renovate bumps it, and checks the
pages through Caddy.
The image gets the wheel of the checkout, as the version that is tested is not
on PyPI, which is the only change of the generated `Dockerfile`. The workflow
runs only `tt/docker-smoke/smoke.sh`, which runs the script of a variant, as
`app.sh`, with the steps they share in `lib.sh`, so that the logic of the test
is in files of its own, which run locally as well, with Docker:

```sh
mise exec -- tt/docker-smoke/smoke.sh app
```

CI sets `PYTHONWARNINGS=error::SyntaxWarning,error::DeprecationWarning`, so an
invalid escape sequence or a deprecated API fails the build, before a new
Python removes it; the weekly run catches the deprecations of a new Python
release. Python keeps an unknown escape such as `"\:"` as a backslash
followed by the character, which is often exactly what a CSS selector or a
regular expression ported from Perl needs; write it as `"\\:"` or as a raw
string so it survives the Python release that turns the warning into an error.

CI runs the tests in the development mode of Python, `PYTHONDEVMODE=1` (or
`python -X dev`), which shows the `ResourceWarning` of a socket, a file or a
temporary directory that nothing closed. Python writes it to the standard
error, often from the garbage collector, where it cannot fail a test, so CI
fails when `ResourceWarning:` appears in the output. CI runs the scripts at
the same time, whose standard error would mix, so it passes
`--capture-stderr`: the standard error of a script follows the line of its
result, each line after the name of the script, which tells the script that
leaked. It passes `--color` too, as the log of GitHub Actions shows colors
while the output goes to a pipe, not to a terminal; the color of a line of
the standard error is around the whole line, so `ResourceWarning:` is still
in it. It writes the JUnit XML of the results with `--formatter junit=FILE`,
which the action `mikepenz/action-junit-report` turns into the annotations of
the failed tests, and the summary of the job with `--formatter markdown=FILE`,
whose diagnostics of the failures come from the standard error that
`--capture-stderr` captures, as `Pyjo.Test` writes them there and not into the
TAP output, as `Test::More` does.
Each job of the tests uploads its JUnit XML, also the one of pytest, as an
artifact named `junit-` and the name of the job, from which the job `report`
makes the summary of the summaries of all the jobs, with
`.github/scripts/test-report.py`, as its summary and as a comment of the pull
request, which each run edits, found by the marker it starts with.
`--stderr-lines 1000` keeps the first and the last lines of the
standard error of a script, as a script that fails in a loop, like an I/O
watcher of `Pyjo.Reactor.Poll` that raises each time the reactor calls it, can
write hundreds of megabytes of it, which the log of GitHub Actions takes
minutes to take in; a `ResourceWarning` among the lines left out does not
fail CI, but such a script fails anyway. The development mode is the debug
mode of asyncio too, whose loop logs a callback that takes longer than 0.1
seconds, which TLS and the applications of the tests do on a busy runner, so
CI sets `PYJO_ASYNCIO_SLOW_CALLBACK=5`, which `Pyjo.Reactor.Asyncio` gives the
loops that it makes, as asyncio has no variable of its own for it; a line of
`Executing <Handle ...> took` is a callback that blocked the loop that long.
A test closes what it
gets, as the handle of an `accept` or `connect` event or a connection of
`http.client`, where Perl closes it with the last reference. To find where a
leaked object was made:

```sh
PYTHONPATH=. mise exec -- python -W default::ResourceWarning -X tracemalloc=50 t/Pyjo/IOLoop.py
```

PyPy has no `_tracemalloc`: it ignores `-X tracemalloc` without a word, and its
`ResourceWarning` names no place. A leak of PyPy alone, as of an object that
CPython closes with its last reference, is found with `gc.collect()` and a
line to the standard error after each subtest, which puts the warning next to
the subtest that leaked it. PyPy skips some tests on macOS, as the one of
`Pyjo.Server.Prefork`, so such a leak may show on Linux only, as in a
container of the image `pypy:3.12-slim`. An object that a forked process
inherits is freed by the garbage collector of the child too, so a leak of one
test can show in the workers of the next one.

CI runs the tests on every supported CPython version and on PyPy. PyPy frees
objects only when its garbage collector runs, not when the last reference
goes, so code must not rely on that: resizing a `bytearray` that a regex
iterator still scans raises `BufferError`, and `__del__` may not run at all
before the interpreter exits.

CI runs them on the free-threaded build of the newest CPython too, without
the global interpreter lock, on which the threads of `Pyjo.Server.Prethread`
run at the same time. It counts the references of a function made at the top
level of a module in a deferred way, so it frees such a function, and what
only the function refers to, only when its garbage collector runs, and a
test that checks that an object is freed without the garbage collector makes
its callback in a function. The garbage collector then frees all of them
together and calls their `__del__` in any order, so a resource that an object
opens for itself, as the loop of its own of `Pyjo.Reactor.Asyncio`, is closed
by `weakref.finalize`, whose callback the garbage collector calls before
them. Locally, uv installs the free-threaded build next to the one of
`mise.toml`, as mise has it only as a flavor of all its versions of Python:

```sh
PYTHONDEVMODE=1 mise exec -- uv run --no-project --python 3.15t python -m Pyjo.Prove -l -j 4 -r t
```

A test script with the syntax of a newer Python, as the t-strings of Python
3.14, cannot skip itself on an older one with `plan(skip_all=...)`, as that
Python does not compile it. It names the version in the inline metadata of
PEP 723, and `Pyjo.Prove` skips it without running it; Perl's `prove` does
not read it.

```python
# /// script
# requires-python = ">=3.14"
# ///
```

pytest runs the test scripts too, through `Pyjo.Test.pytest_plugin`, which
`[project.entry-points.pytest11]` registers, so that pytest loads it wherever
Pyjoyment is installed, with nothing of Pyjoyment importing pytest. It is
for whoever runs `pytest` by habit, as a coding agent or the test explorer of
an IDE, not a second runner of the project: each script is one test of
pytest, which `Pyjo.Prove.run_script` runs in a process of its own, as
`Pyjo.Prove` does, not a fork of the process of pytest, whose modules,
threads and environment the script would inherit, and which Windows does not
have. pytest collects its items before it runs them, and the subtests of a
script are known only from its TAP output, so a script is not split into
tests. The wrapper of `pytest_collect_file` replaces what other plugins make
of a file of the directories of `pyjo_prove_paths`, as the module of pytest
for a `t/test_*.py`. `testpaths = ["t"]` of `pyproject.toml` makes `pytest`
without arguments run the whole suite, and pytest-xdist of the group
`pytest` runs the scripts at the same time, as `-j` of `Pyjo.Prove`, where
pytest alone runs them one after another, four times slower:

```sh
mise exec -- uv run --group pytest pytest -n 4
```

The plugin also calls `Pyjo.Test.raise_failures`, so that the functions of
`Pyjo.Test`, and with them the chains of `Pyjo.Test.Pyjo`, raise
`AssertionError` in a test of pytest: printing TAP there, the `atexit`
handler of `Pyjo.Test` would see tests without a plan and replace the exit
status of pytest with 254. A skip is `unittest.SkipTest`, which pytest and
unittest both know, so `Pyjo.Test` imports nothing of pytest. The module
variable `__tracebackhide__` of `Pyjo.Test` and `Pyjo.Test.Pyjo`, which pytest
reads from the globals of a frame too, leaves their frames out of the
traceback of a failed test. The plugin takes the environment of the scripts
when pytest starts, as the import of `Pyjo.Test.Pyjo` sets `PYJO_LOG_LEVEL`,
and imports `Pyjo.Test.Pyjo` only in the fixture `t`.

The tests of the plugin, `t/Pyjo/Test_pytest_plugin.py`,
`t/docs/Test_pytest_plugin.py` and the section of pytest of
`t/docs/guides_testing.py`, run pytest in a process of their own, and skip
without pytest, which is in the dependency group `pytest`, not in
`dependencies`. CI runs them in the job `pytest`, with the group installed by
uv, which installs the project too, so that pytest loads the plugin of its
entry point, where the tests pass `-p Pyjo.Test.pytest_plugin` without it,
and runs all the test scripts with pytest and pytest-xdist there:

```sh
mise exec -- uv run --group pytest python -m Pyjo.Prove -l t/Pyjo/Test_pytest_plugin.py t/docs/Test_pytest_plugin.py
```

## Benchmarks

`benchmarks/` measures hello world servers with one connection and one
request at a time: Pyjoyment on its own servers, through ASGI and WSGI, and
other Python servers next to it. `benchmarks/README.md` says how to run them
and how to measure well; it is also the recipe for a measurement of another
kind. A change made for speed is measured with `benchmarks/ab.sh`, the
version before and after interleaved on a machine that is otherwise quiet,
and a gain below the noise with the function calls per request of
`benchmarks/profile.sh`. The results, with the machine, the versions and the
load average, go to the issue or the pull request, not to the repository.

## Porting from Mojolicious

The target is **Mojolicious 9**. A module is ported from a release of it, the
newest one when the port starts, and its documentation names that release
("Ported from ... of Mojolicious 9.49"); the first ports are from 9.49. The
changes of newer releases are followed in the issue that tracks upstream, and a
change is ported to the modules it touches, whose documentation then names the
newer release. A fix that cannot wait for a release, as a security one, is
ported before it, and the module names the release that will have it. An edit
of a module that ports nothing from upstream leaves its release as it is.

Some modules have no counterpart in Mojolicious: `Pyjo.Test` (inspired by
Perl's `Test::More`), `Pyjo.Prove` (inspired by Perl's `prove`),
`Pyjo.String.*`, `Pyjo.GetOpt` (inspired by `Getopt::Long::Parser`, the engine
of `getopt` of `Pyjo.Util`, where Perl has references to variables as the
targets of the options), `Pyjo.IOLoop.Datagram` (inspired by `dgram` of Node.js),
`Pyjo.App` (inspired by `Mojo` of Mojolicious 6, the base class of
`Mojolicious` until Mojolicious 7, as `Pyjo_App` is of `Pyjoyment_App`),
`Pyjo.HelloWorld` (an application of pure Pyjo, where `Mojo::HelloWorld` is
one of Mojolicious, which `Pyjoyment.HelloWorld` ports), `Pyjo.App.WSGI` (the
application of Pyjo that runs a WSGI application, inspired by
`Mojolicious::Plugin::MountPSGI` of CPAN, the reverse of `Pyjo.Server.WSGI`),
`Pyjo.App.ASGI` (the application of Pyjo that runs an ASGI application, the
reverse of `Pyjo.Server.ASGI`), `Pyjo.App.FastCGI` (the application of Pyjo
that runs a FastCGI application, as PHP on php-fpm, through a connection to
it, the reverse of `Pyjo.Server.FastCGI`), `Pyjo.App.CGI` (the application of
Pyjo that runs a CGI program in a process of its own for each request, the
reverse of `Pyjo.Server.CGI`, inspired by `Mojolicious::Plugin::CGI` of CPAN,
whose base class has the response of CGI that `Pyjo.App.FastCGI` shares),
`Pyjo.App.Lambda` (the application of Pyjo that runs an event function of AWS
Lambda in a process of its own, through the Runtime API of Lambda, which it
serves, the reverse of `Pyjo.Server.Lambda`, whose runtime client runs a
handler of Python there),
`Pyjo.IOLoop.ChildProcess` (a program in a process of its own, with its
standard input, output and error as `Pyjo.IOLoop.Stream` objects, inspired by
`child_process` of Node.js, whose standard input is a stream that closes when
a write fails, as a stream handles an error of a write only when it reads, as
Mojo does, so that a pipe that is only written would be watched for ever after
the program closes it, and a reactor of poll reports its hang-up when it
watches for nothing),
`Pyjo.IOLoop.Stdio` (the standard input and output of the process as one
stream, inspired by `process.stdin` and `process.stdout` of Node.js),
`Pyjo.IOLoop.Messages` (a stream of messages on a stream of bytes, with the
framings of the transport stdio of MCP, of LSP and of Native Messaging),
`Pyjo.Server.Lambda`
and `Pyjoyment.Command.lambda` (the server and the command of the event
functions of AWS Lambda, inspired by `Pyjo.Server.WSGI` and its command, and
the client of the Runtime API of Lambda, `python -m Pyjo.Server.Lambda`,
which runs any handler, with `http.client` outside of the event loop, as a
handler that runs an event loop of its own, as Mangum, cannot run in one),
`Pyjo.Server.FastCGI` and `Pyjoyment.Command.fastcgi` (FastCGI on the
connections of the listen locations `fcgi://` and `fcgi+unix://` of
`Pyjo.Server.Daemon`, written from the specification of FastCGI 1.0, and the
command of a web server that starts the application with its listen socket
as the file descriptor 0, inspired by `Pyjo.Server.CGI` and its command),
`Pyjo.Server.Prethread` and `Pyjoyment.Command.prethread` (the server of
`Pyjo.Server.Prefork` with threads for the worker processes, each a copy of
the server with the event loop of its thread and the duplicates of the listen
sockets of the manager, or the sockets themselves on Windows, where `accept` of
a duplicate can block when another one accepts the connection, as Thrall is Starlight with threads, and its command,
a subclass of the one of `prefork`),
`Pyjoyment.Plugin.AllowedHosts` (the validation of `Host` and `Origin`
against DNS rebinding, which the transport of MCP over HTTP requires of a
server on localhost, as the middleware of the MCP SDK and the hosts of
Django have it, in a hook of `before_dispatch` or the helper `allowed_hosts`
of `under`, as a condition of a route that fails lets the next route match),
`Pyjoyment.Plugin.PyRenderer` (the renderer of template strings, inspired by
`Mojolicious::Plugin::EPLRenderer`), `Pyjoyment.Plugin.TOMLConfig` (inspired
by `Mojolicious::Plugin::NotYAMLConfig`, for the format of configuration of
the standard library), `Pyjo.TOML` (the dumper of TOML, which the standard library only reads),
`Pyjo.JSON.Schema` (JSON Schema 2020-12 from the type hints of Python and
from a builder inspired by zod, and its validation, written from the
specification, whose tests compare the schemas with the ones of pydantic and
of zod, and run the official test suite of JSON Schema on the validation),
`Pyjo.JSON.RPC` (JSON-RPC 2.0, its server and its client, without a
transport, written from the specification, whose first consumer is the
distribution of MCP, and whose `to_action` makes an action of a route of
Pyjoyment, which takes the controller from the route, as `Pyjo` does not import
`Pyjoyment`, and whose `serve` serves a stream of messages in both directions),
`Pyjo.Test.pytest_plugin` (the plugin of pytest, which runs the test scripts
as `Pyjo.Prove` does and the functions of `Pyjo.Test` in the tests of pytest),
`Pyjo.YAML` (the subset of YAML of `CPAN::Meta::YAML`,
which `Mojolicious::Plugin::NotYAMLConfig` reads, written anew, as the license
of the Perl module is that of Perl 5, with its regular expressions) and the
helpers in `Pyjo.Util` that turn statements into expressions. These extras follow their inspiration where it
helps, without porting it, and their tests are written for them rather than
ported.

`Pyjo.Util` is the port of `Mojo::Util` and of `Mojo::BaseUtil`, which
`Mojo::Util` exports again; the subtests of `t/mojo/base_util.t` are those
of `t/mojo/util.t`, so it has no test file of its own. Next to them,
`Pyjo.Util` has helpers of its own, for Python. A function of Mojo that waits
for a module that is not ported yet has a `# TODO:` comment in its place. A
function that works on characters in Mojo takes a `str`, and also `bytes`
where a ported module needs them, like `url_unescape`.

A module is ported anew from Mojolicious, not migrated from the existing
Python code. The existing Python module is a reference for how Perl idioms
were translated before, not a base to patch: it follows an older Mojo and
carries compromises that a fresh port does not need.

```sh
git clone https://github.com/mojolicious/mojo.git
git -C mojo checkout v9.49
```

For each module:

1. Port its tests from `t/mojo/*.t` first, keeping Mojo's test names and
   order, one assertion for one, without folding repeated ones into a loop
   or chaining the assertions of `Pyjo.Test`, so that the diff of a newer
   Mojolicious applies to them. Mojo's tests are the specification.
2. Port the module from `lib/Mojo/*.pm` until the tests pass.
3. Port its POD into the docstrings: the same sections in the same order
   (synopsis, description, events, attributes, methods, operators, see also)
   and Mojo's wording, with Python names and examples. The POD is the source of
   the Python documentation. Sphinx lists the classes after the module
   docstring, so "See also" ends the module docstring, before them. The
   synopsis of a module whose class it makes or subclasses starts with its
   first example in the form of Python, `from Pyjo.URL import URL` and
   `URL(...)`, which shows that both forms are correct. A test in `t/docs/`
   runs the examples.
4. Name the source at the end of "See also", as a link to the file at the tag
   of the release (`https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Date.pm`),
   annotate the module and put it on pyright's strict list.
5. Check the module off in the porting inventory issue, which lists every
   module of the target Mojolicious with its Pyjoyment counterpart.

Code that has no counterpart in the Mojolicious module or in its test, such
as a method, a branch, an assertion or a form of an argument for Python
only, has a comment that starts with `# Not in Mojolicious:` and says what it
is for, so that the diff of a newer Mojolicious can be applied around it.
This lists them:

```sh
grep -rn "Not in Mojolicious" Pyjo t/Pyjo
```

It is a comment, not a part of the docstring: the documentation describes
the API as it is. Translations of Perl idioms, as listed below, are Mojo's
code and are not marked.

A method of Mojolicious that has another name in Pyjoyment than the
translations below give it, as `to_rfc3339` for Mojo's `to_datetime`, has a
comment that starts with `# Renamed from Mojolicious:` and names the Mojo
method, in the module and in its ported tests, where the diff of a newer
Mojolicious uses the old name.

A method or an assertion of Mojolicious that is left out on purpose has a
comment where it would be, in the order of the Mojo module or test, that
starts with `# Left out from Mojolicious:`, names what is left out and says
why, so that its absence is not taken for an omission.

Behaviour that differs from Mojolicious on purpose has a comment that starts
with `# Unlike Mojolicious:`, says what Mojo does, and why the port does
otherwise, so that a newer Mojolicious does not bring the old behaviour back.
Where the difference comes from a bug of Mojolicious, the bug also goes to
the issue that collects them.

These markers are for what stays. What waits for a module that is not ported
yet, as a method left out, a stand-in for a class of Mojolicious or a test
that runs without a command, has a comment that starts with `# TODO:` and
says what to do and when, so that the port of that module finds it:

```sh
grep -rn "TODO:" Pyjo Pyjoyment t
```

Mojo's tests and the behaviour of its code at the tag are the reference, not
its POD: the examples in the POD are not tested and can be wrong. Where they
disagree, run the Perl code from the clone (`perl -Imojo/lib -MMojo::URL -e ...`)
and port what it does.

A bug or a quirk of Mojolicious itself, found while porting, goes to the issue
that collects them, with a Perl command that reproduces it at the tag and what
the port does about it. Reporting it upstream is a decision of its own.

Moving a ported module to a newer release is the difference between the two
versions, applied to code, tests and docstrings alike:

```sh
git -C mojo diff v9.49 v9.50 -- lib/Mojo/URL.pm t/mojo/url.t
```

Perl and Python differ in a few places that a port must translate rather than
copy:

- A global inline regex flag such as `(?i)` is only valid at the start of a
  Python pattern; in the middle of one, use the scoped form `(?i:...)`.
- Perl's `weaken` is ported as `weakref.proxy`. Check whether the object
  behind a proxy still exists with `Pyjo.Util.isalive`; `dir(proxy)` and
  `bool(proxy)` raise `ReferenceError` for a dead proxy. A `list` cannot be
  weakly referenced, so the parent of a node in the tree of `Pyjo.DOM` is a
  plain reference, and the garbage collector frees the cycles.
- `"\$"` in a double-quoted Perl string is a plain `$`; in Python it keeps the
  backslash.
- Overloaded operators become special methods: `""` is `__str__`, `bool` is
  `__bool__`, and `@{}` is `__getitem__`, `__iter__` and `__len__`.
  `to_string` is `to_str`, the counterpart of `to_bytes` in
  `Pyjo.String.Mixin`, and `to_unsafe_string` is `to_unsafe_str`.
  `to_hash` is `to_dict`, `to_array` is `to_list`, and a flat list of names
  and values, like the pairs of `Mojo::Parameters`, is a list of
  `(name, value)` tuples.
- Mojo's attributes and getter/setter methods are attributes and properties
  (`url.host`, `url.path`). A method without arguments that describes the
  object, like `is_abs` or `protocol`, is a property too: as a method,
  `if url.is_abs:` would always be true. A method that builds something,
  like `to_str`, `clone` or `names`, stays a method.
- Mojo's forms of an accessor with a list of arguments, an array reference
  and a hash reference are a `tuple`, a `list` and a `dict`:
  `url.query = ('a', 1)` replaces the parameters, `['a', 1]` appends
  them, and `{'a': 1}` merges them, as `query(a => 1)`, `query([a => 1])`
  and `query({a => 1})` do.
- A name followed by its data in Mojo's list of arguments, as a generator of
  `tx` in `Mojo::UserAgent::Transactor` with its options
  (`form => {a => 'b'}, charset => 'UTF-8'`), is a keyword argument
  (`form={'a': 'b'}, charset='UTF-8'`), and a hash reference of headers or
  the content before it are positional arguments. A callback that Mojo takes
  after them, as the request methods of `Mojo::UserAgent` do, is the keyword
  argument `cb` (`ua.get(url, {'DNT': 1}, form={'a': 'b'}, cb=cb)`), or the last
  positional argument, as the ported tests pass it.
- A Perl string of characters is a `str`, and bytes in Python are `bytes`,
  encoded with the charset of the module. Perl keeps bytes that do not decode
  as a byte string, which is a `str` of the characters 0-255 in Python:
  `.decode('latin-1')`.
  HTTP headers are such characters too, as `http.client` has them: bytes
  from the wire are decoded as ISO-8859-1.
- An environment variable `MOJO_*` is `PYJO_*`, and so are the ones that
  `prove` sets for the tests, as `HARNESS_ACTIVE`, which `Pyjo.Prove` sets as
  `PYJO_HARNESS_ACTIVE`.
- A name that Mojolicious takes from somewhere else, as `Mojo::Server::Hypnotoad`
  and `Mojo::Server::Morbo` are named after characters of Futurama, is a name
  that says what the module does, `Pyjo.Server.Hot` and `Pyjo.Server.Reload`,
  with a `# Renamed from Mojolicious:` comment; so are its environment
  variables (`PYJO_RELOAD_BACKEND`) and the jokes of its documentation. A
  script of Mojolicious, as `script/morbo`, is a `main` function of the module,
  a `pyjo-` command in `[project.scripts]` of `pyproject.toml` (`pyjo-reload`)
  and `python -m` of the module. It parses its options with `getopt` of
  `Pyjo.Util`, as the script does with the one of `Mojo::Util`, with the
  target `Pyjo.GetOpt.env` for an option that the script binds to `$ENV{...}`,
  as `PYJO_HOT_FOREGROUND` for `--foreground`, and its usage,
  which the script has in its SYNOPSIS, is the section of the docstring of the
  module with the name of the command, which `extract_usage(section=...)`
  reads, so that the help of the command and its documentation are one text.
  `script/mojo`, the command line interface of `Mojo::HelloWorld`, is `pyjo`,
  the `main` of `Pyjoyment.Commands`, and `python -m Pyjoyment`.
- A command of Mojolicious, as `Mojolicious::Command::daemon`, is a module of
  the package `Pyjoyment.Command` with the name of the command, as
  `Pyjoyment.Command.daemon`, and its usage, which Mojo extracts from the
  section SYNOPSIS of its POD, is the first literal block of the docstring of
  the module, which the class reads with `usage = extract_usage()`, with its
  options in a block that `format_usage` of `Pyjo.GetOpt` lays out, so that
  a new option needs no alignment by hand. Its
  options are parsed with `getopt` of `Pyjo.Util`, whose targets are a dict,
  as Python has no references to variables. The commands of the servers,
  `daemon` and `prefork`, parse them with `env_prefix='PYJO_'`, so that an
  option that is not given has the value of `PYJO_` and its name, as
  `PYJO_WORKERS`, the way Cobra and Viper of Go have it, which continues the
  variables that Mojo already has for some of them, as `MOJO_LISTEN` and
  `MOJO_INACTIVITY_TIMEOUT`; the environment of a container tunes the server
  without its command line. Other commands, as `get`, have no such
  variables, as `PYJO_METHOD` or `PYJO_VERBOSE` would surprise.
- PSGI is WSGI and ASGI: the command `psgi` is `wsgi`, and `asgi` is its
  counterpart, which return the application of `Pyjo.Server.WSGI` and
  `Pyjo.Server.ASGI`. `PYJO_WSGI` and `PYJO_ASGI` take the place of
  `PLACK_ENV`, as WSGI and ASGI have no environment variable of their own: a
  server imports the script of an application, which ends with
  `application = app.start()`, with its own arguments in `sys.argv`, so that
  the command has to be detected. The runtime of AWS Lambda imports the script
  the same way, and `AWS_LAMBDA_RUNTIME_API`, which it sets, detects the
  command `lambda`, whose module has the name of a keyword of Python, which
  only `importlib` imports.
- The generators of the command `generate` write projects for uv, where Mojo
  writes ones for ExtUtils::MakeMaker: `generate makefile` is
  `generate pyproject`, and `cpanify` is left out, as `uv publish` uploads to
  PyPI. An application is a package in the directory of its project, without
  `lib`, as `Pyjo.Prove -l` adds the current directory, and its
  `pyproject.toml` has no build system, as `uv init --app` makes it, since
  `Pyjo.Home` finds `templates` and `public` next to the package, which a
  wheel would leave behind; `MyApp/__main__.py` takes the place of
  `script/my_app`. A script of `Pyjoyment.Lite` has its dependencies in the
  `pyproject.toml` of `generate pyproject` next to it, as in Mojo, or in the
  inline metadata of PEP 723, which `generate dockerfile` installs where
  there is no `pyproject.toml`. A plugin is a distribution, built with
  hatchling, whose wheel has only its module, without the `__init__.py` of
  the namespace `Pyjoyment.Plugin`, which `extend_path` keeps open. A
  namespace finds its parts through the `__path__` of its parent package, so
  `Pyjoyment/__init__.py` extends its own before it imports its subpackages.
- `ojo` is the functions of the package `Pyjo`, which `from Pyjo import *`
  imports, and `perl -Mojo -E` is `python -m Pyjo`. A function imports the
  modules it uses when it is called, as every `import Pyjo.X` runs
  `Pyjo/__init__.py`. Its `u`, PUT, is `w`, as `u` is for characters, as in
  `Pyjo.String.Unicode`. `z`, which ojo does not have, is the builder of
  `Pyjo.JSON.Schema`, as `z` of zod: an object that imports the module when a
  method of the builder is read, as the class itself would need the import
  when `from Pyjo import *` runs, and that type checkers take for the class.
- Where Mojo uses an optional XS module for speed, as `Mojo::JSON` uses
  `Cpanel::JSON::XS`, the port uses the module of the standard library in its
  place and keeps the port of the pure-Perl code behind a `PYJO_NO_*`
  variable. Mojo's tests of the pure-Perl code set the variable, and those of
  the XS module run against the standard library.
- `TO_JSON` is `__json__`.
- A hash of Perl has no order, which `Mojo::JSON` makes up for by sorting the keys
  of an object, so that its output is the same each time. A `dict` keeps the order
  of its keys, which tells something, as the order of the parameters of a
  function in its JSON Schema, so `Pyjo.JSON`, `Pyjo.YAML` and `Pyjo.TOML` write
  the keys in that order, and sort them only with `sort_keys`.
- `Mojo::ByteStream` is `Pyjo.String.Unicode` for characters and
  `Pyjo.String.Bytes` for bytes. A Mojo test's `b(...)` is `u(...)` or
  `b(...)`, by what the string holds.
  Markup, which Mojo keeps from escaping as a `Mojo::ByteStream`, as a tag
  helper returns it, is `Pyjo.String.HTML`, `html(...)`: escaping leaves only
  what has the method `__html__`, so a string that `u()` or
  `Pyjo.Collection.join` makes is escaped.
- Perl code in a template of `Mojo::Template` is Python code in
  `Pyjo.Template`, and the templates of a Mojo test are translated with it:
  `@_` is `args`, a block of Perl in braces is a block of Python, with braces
  or with `:` and `end`, a statement modifier is a block of its own, and
  `begin` and `end` compile to a nested `def` that is defined before the
  statement that uses it, as a lambda cannot hold statements. The compiled
  code is not line for line the template, as the one of Mojo is, so a map
  gives the template lines of a traceback.
- An `ep` template is translated the same way: `$c` and `$self` are `c` and
  `self`, a value of the stash `$foo` is the variable `foo`, and a helper is
  a function, as `%= include('menubar')`. A helper that takes a block as its
  last argument, `content foo => begin`, closes its parenthesis after `end`:
  `%= content('foo', begin` and `% end)`. Python has one namespace where Perl
  has sigils, so a value of the stash hides the helper of its name, and the
  variable `c` hides the helper `c`; the template calls such a helper as a
  method of `c`, as `c.title('Welcome!')`.
- A tag helper takes the attributes of its tag as keyword arguments, after
  its positional ones, and a block of a template as the last positional
  argument, before them: `form_for login => (method => 'POST') => begin` is
  `%= form_for('login', begin` and `%= end, method='POST')`. An attribute that
  is a keyword of Python or has a dash goes with `**`, as
  `**{'class': 'menu'}`, and an attribute without a value is `None`. The
  attributes of an option or a group of `select_field` are a dict after its
  value, where Mojo takes a flat list of names and values.
- `use Mojolicious::Lite` is `from Pyjoyment.Lite import *`, which gives the
  module that imports it an application of its own, as Mojo makes one for the
  package that uses it: the functions are made for the module of the caller
  by `__getattr__` of `Pyjoyment.Lite` and kept in the module, so that a
  script that `load_app` runs again gets a new application. `get '/foo' =>
sub {...}` is `get('/foo', cb)` or the decorator `@get('/foo')`, as a route
  is a decorator of its callback, `group {...}` is `with group():`, and
  `app->start` is `app.start()`. The templates of the `__DATA__` section of
  a Lite script are in its docstring after a line `__DATA__`, as a variable
  at the end of the script comes after the code that serves them. Mojo makes
  the package a subclass of `Mojolicious` whose `new` returns its application,
  so that a route embeds it by its name, as `to('EmbeddedTestApp')`; Lite
  keeps such a class with the functions of the module, where the routes find
  it by the name of the module.
- `Test::Mojo` is `Pyjo.Test.Pyjo`, with the chains of methods of Mojo:
  `$t->get_ok('/')->status_is(200)` is `t.get_ok('/').status_is(200)`. Its
  attributes are attributes, so `$t->success(0)->or(...)` is an assignment
  followed by the call, and its handler gets the names of the functions of
  `Test::More`, as `is` and `is_deeply`, which the tests of Mojo check.
- A callback that Mojo calls with `$_` gets the element as its first
  argument. A method name in a string, as in `$collection->map('text')`, can
  name a property, which is how a Mojo attribute is ported.
- A method of `Mojo::Collection` that has the name of a `list` method, like
  `sort` and `reverse`, returns a new collection, as in Mojo, and
  `list.sort(collection)` sorts in place.
- `shift` and `unshift` of an array of Perl that is a queue, as the callbacks of
  `next_tick` of a reactor or the parts of a multipart form, are `popleft` and
  `extendleft` of a `collections.deque`, not `pop(0)` and an assignment to
  `[:0]` of a `list`, which move all the other items, so that a queue that the
  input makes long does not make the loop that empties it grow with its
  square. A queue that a limit keeps short, as the connections that
  `max_connections` keeps, stays a `list`.
- Perl's `split` is `Pyjo.String.Unicode.split`, not `str.split` or
  `re.split`: its pattern is a regular expression, a match of no length at
  the beginning makes no field, and the empty fields at the end are left out.
- `redo` in an `until` loop starts the body again without checking the
  condition. A `while` with `continue` checks it, so the port is a
  `while True:` inside an `if not ...:`.
- After a match of no length, Perl does not let the next `/gc` match be of no
  length at the same position, so `/\G\z/gc` fails right after
  `/\G\s*/gc` skipped nothing. A parser ported from Mojo that reports
  "before end of data" this way, as `Mojo::JSON` does, has to keep it where
  Mojo's tests expect it. A tokenizer that matches the text and then the tag
  of the same position in two matches, with a lazy `??` and this rule, as
  `Mojo::DOM::HTML` does, has them as alternatives in Python.
- Python has no relative backreference like `\g{-2}`; a named group takes
  its place, and works also where the pattern is embedded in another one.
- Python's recursion limit is 1000 calls. A recursive parser that must reach
  a nesting depth like `Mojo::JSON`'s 512 makes one call for each level,
  not two.
- A function that works on bytes in Mojo, such as a checksum, Base64
  encoding, compression or `xor_encode`, takes `bytes`, and a Mojo test that
  passes it a literal like `'foo bar baz'` passes `b'foo bar baz'`.
- Perl's `\w` matches the combining marks of scripts such as Devanagari,
  Python's does not, so a regular expression that keeps word characters of
  any script tests the Unicode category of the character as well.
- Methods that Mojo makes in a loop with `monkey_patch`, such as the
  shortcuts of `Mojo::Headers`, are class attributes, one for each, made
  with a descriptor class.
- `None` is not `undef` everywhere: `time.gmtime(None)` is the current time,
  `gmtime(undef)` is the epoch. Python's `tm_wday` counts from Monday, Perl's
  from Sunday.
- A Perl scalar keeps the form it was given (`'1.0'` stays `'1.0'`), and a
  number stringifies without a trailing `.0`. A port converts input to `int`
  or `float`, and formats it the Perl way where the output depends on it.
  Where Mojo only stores and prints a value, like a parameter, the port stores
  it as a `str`.
- A Perl quirk that only a warning reveals is not ported. `undef` counts as `0`
  with a warning, so `Mojo::Date` reads an unknown month name as January;
  `Pyjo.Date` rejects the date.
- A flag that Mojo sets to `1` and leaves `undef` otherwise is `True` or
  `None`. A test of the end of a list, `is $cookies->[1], undef`, becomes
  `is_ok(len(cookies), 1)`, or `is_ok(collection.get(1), None)` for a
  `Pyjo.Collection`.
- A function or a method named after a keyword of Python gets a name that is
  not one, which the documentation uses, and the name with a trailing
  underscore is its alias, which the ported tests use, so that the diff of a
  newer Mojolicious applies to them: `raise` of `Mojo::Exception` is `throw`
  and `raise_`, and `finally` of `Mojo::Promise` is `lastly`, as Bluebird
  names it, and `finally_`; `continue` of `Mojolicious::Routes` and
  `Mojolicious::Controller` is `proceed` and `continue_`, and `or` of
  `Test::Mojo` is `otherwise` and `or_`. An attribute only
  gets the other name, as `not`
  of `Mojo::UserAgent::Proxy` is `no`, after `NO_PROXY`. The functions of
  `Pyjo.Test` are the exception: they have an `_ok` suffix, as `is_ok`.
- A name of a Perl package, as `Mojo::Exception` takes them, is a dotted name
  of a class in Python (`'MyApp.X.Foo'`), resolved by importing the longest
  prefix that is a module.
  A plugin or a controller that Mojolicious loads by its package name is the
  class that a module names `object`, as `Pyjoyment.Plugin.HeaderCondition`,
  or a class in a module, as `MyApp.Controller.Foo`.
- A helper of Mojolicious, which `Mojo::DynamicMethods` makes a method of the
  controller and the application, is a callable that `__getattr__` finds in
  the renderer, and a prefix of nested helpers is an attribute: `c.title('x')`,
  `c.log().debug(...)` and `c.reply.not_found()`.
- Perl's `@INC` is `sys.path`, and `%INC`, the files of the modules that
  are loaded, and the symbol table of packages are `sys.modules` and the
  `__file__` of a module, as `Pyjo.Home` and `Pyjo.Loader` use them; a module
  that is not loaded is not imported to find it.
- The `__DATA__` section of a Perl module is the `__DATA__` variable of a
  Python module, or its docstring after a line `__DATA__`, which a script of
  `Pyjoyment.Lite` uses, as its docstring is there before `app.start()`.
- `croak` of Carp reports the line of the caller, Python the line of the
  `raise`. Where Mojo's tests check the line that `croak` gives, as
  `load_class` of `Mojo::Loader` does, the port takes the frame of the caller
  from the traceback.
- Modules that a Mojo test loads from `t/mojo/lib` are written into a
  temporary directory by the test, as `Pyjo.Prove` runs every `.py` file
  under `t`, and are top-level there, as Python does not merge a regular
  package like `Mojo::` from every directory of `sys.path`. The modules of
  `t/mojolicious/lib`, the test applications and plugins of the framework,
  are in `tt/lib`, with `PyjoymentTest` for `MojoliciousTest`, and a test
  puts `tt/lib` in front of `sys.path`. The packages of a Mojo test that use
  `Mojolicious::Lite`, as `TestApp` of `embedded_lite_app.t`, are modules of
  `tt/lib` too, as an application of `Pyjoyment.Lite` is one of a module. The
  applications of `t/mojolicious/external` are in `tt/external`.
- A stack trace, Perl's `caller` frames, is a list of
  `traceback.FrameSummary`, the most recent first, as Mojo keeps it.
- `like` of `Test::More` stringifies what it checks, `like_ok` does not:
  a test of an object is `like_ok(str(obj), ...)`.
- `Test::More` writes to a copy of STDOUT that it makes when it starts,
  `Pyjo.Test` to `sys.stdout` at the time of the call. A test that replaces
  `sys.stdout` to capture the output of the code, as `local *STDOUT` does,
  checks the results after it gives `sys.stdout` back.
- A script that Mojo loads with `do`, taking the application from its value,
  as `load_app` of `Mojo::Server` does, starts its application, and `start`
  keeps it in `Pyjo.Server.loaded_app` when `PYJO_APP_LOADER` is set, where
  Mojo's `start` returns it; `MyApp.new().start()` chains as in Perl.
- A test that depends on the layout of its own source lines, as the context
  of `Mojo::Exception` does, is kept from the formatter with `# fmt: off`.
- Perl frees a temporary object at the end of the statement, Python as soon
  as nothing refers to it. Where an object holds a resource, like the
  temporary directory of `Pyjo.File.tempdir()`, an object made from it, like
  its `child()`, keeps it, so that `tempdir().child('x').spew(...)` works as in
  Perl.
- What Mojo calls on the class as a shortcut to its singleton, like
  `Mojo::IOLoop->timer`, is a function of the module bound to the singleton,
  `Pyjo.IOLoop.timer`.
- An object that holds a resource, like a socket or an I/O watcher, and that
  Perl closes in `DESTROY` when the port drops the last reference to it, as
  `Mojo::IOLoop` does with the acceptors and connections it deletes, is closed
  by the port where it drops it, as PyPy frees it only when its garbage
  collector runs. A resource that an object opens for itself, as the file of
  `path` in `Pyjo.Log`, is closed with the object by `weakref.finalize`.
- Perl closes the handles that are left at the end of the interpreter, in its
  global destruction; Python warns that they were not closed, as `__del__`
  does nothing while it finalizes. A class whose objects hold a resource until
  then, as `Pyjo.IOLoop`, `Pyjo.Server.Daemon` and `Pyjo.Asset.File`, keeps
  them in a `weakref.WeakSet` and closes them in an `atexit` handler of its
  module, which `Pyjo.IOLoop` follows with `gc.collect()`, so that the
  objects in cycles are freed while `__del__` still works. `weakref.finalize`
  calls the finalizers of the objects that are left in an exit function of
  its own, after which it calls none, also for the objects that the garbage
  collector frees then, so a handler that has to come before it, as the one
  of `Pyjo.Reactor.Asyncio`, which cancels the tasks that are left in a loop
  of its own and runs them to their end, as `asyncio.run` does, before it
  closes the loop, is registered after the first finalizer, as `atexit` runs
  the handlers in the reverse order.
- A method that Mojo calls on the class or on an object, like
  `Mojo::DOM->new_tag` and `$dom->new_tag`, is a descriptor that passes either
  of them.
- A method of Mojolicious with the name of a method of `Pyjo.Base`, like `set`
  of `Mojo::Cache`, replaces it in the class. Mojo's chain of an attribute and
  the method, `$cache->max_keys(1)->set(one => 1)`, is then an assignment
  followed by the call.
- Perl passes arguments by reference, so a callback can change a string of
  its caller through `$_[1]`; in Python, the caller passes a mutable object,
  like `io.StringIO`, and the callback changes it.
  A method that changes a string of its caller through a reference, as
  `match_partial(\$path)` of `Mojolicious::Routes::Pattern` removes what
  matched, returns the new string with its result: `captures, path =
pattern.match_partial(path)`.
- The name of the class of an object in a message, `blessed $self` or
  `ref $self`, is `module.qualname` of its class, as
  `Pyjo.EventEmitter.Pyjo_EventEmitter`.
- A callback is an argument in the order that suits Python, not necessarily
  the one of Mojo, and a call can also pass it as `cb`, where it is the only
  callback. A method that takes a callback, and means nothing else without
  it, is a decorator without it, and the decorated name is what the method
  returns with it: the id of a timer, a server or a connection of
  `Pyjo.IOLoop` or `Pyjo.UserAgent`, which `remove` takes, and the callback
  that `on` of `Pyjo.EventEmitter` subscribes. Where a call without the
  callback means something else, as a blocking request of
  `Pyjo.UserAgent`, there is no decorator. The callback is positional-only
  only where the keyword arguments of the method go on, to the callback, as
  in `map` of `Pyjo.Collection`, or somewhere else, as the attributes of
  `tag` of `Pyjo.DOM.HTML`. Where the order or the keyword differs from Mojo,
  a comment at the declaration says so.
- An object that undoes something when it goes away, like the one that
  `capture` of `Mojo::Log` returns, is a context manager: PyPy does not free
  it when the last reference goes, and `with` says where it ends. So is an
  object that holds a resource, as a socket, a file, a server or an event
  loop, whose `__exit__` does what its finalizer does, and the module
  documentation says what the end of the block releases. Such an object has a
  method `close` too, which `__exit__` calls, with `# Not in Mojolicious:`
  where Perl releases it in `DESTROY`: the context manager is an option, not a
  requirement, as for an object that lives longer than a block, as the user
  agent of an application, which closes it when it stops. It is an interface
  for the code that uses Pyjoyment, its tests and examples: the modules call
  `close` and the like themselves, as `with` costs more than a call. An
  object in a cycle, as a user agent with its server, is freed by the
  garbage collector at any point, even in the middle of what the event loop
  does, so a test that makes many of them releases them with `with`.
- An attribute with a default that Mojo builds on first use, like `format`
  and `handle` of `Mojo::Log`, or that comes from a call, like the limits
  that `Pyjo.Headers` and `Pyjo.Message` read from `PYJO_MAX_*`, is a
  property that builds and keeps it the first time it is read, as Mojo
  does: an object that never reads it, like most of those of a request,
  does not pay for the call. A default that is a constant is set by the
  constructor.
- `die` or `croak` with a message raises a `Pyjo.Exception`. An error of the
  system, `$!`, is the `OSError` itself, with the message of Mojo in front of
  its `strerror`.
- A callback returns a list in Perl and one value in Python. Where Mojo
  makes values of what a callback returns, as `then` of `Mojo::Promise` does,
  the return value is one value, `None` is none, as Perl's `return;`, and a
  promise of several values passes them on. Where the values are passed on as
  they are, as the first callback of `run` of `Pyjo.IOLoop.Subprocess` gives
  them to the second one, a tuple is several values.
- Perl's `fork` is `os.fork`, where it exists, and `POSIX::_exit` is
  `os._exit`, which leaves the buffers of `sys.stdout` and `sys.stderr`, so
  they are written before both. A process with threads may deadlock in the
  child of a fork, which Python warns about, so a pool of threads of the port,
  as the one of name resolution in `Pyjo.IOLoop.Client`, is stopped before a
  fork with `os.register_at_fork` and started again when it is needed.
- `async sub` of Mojo is an `async def` that the reactor runs as a promise,
  `Pyjo.Promise.coroutine`, and Mojo's `AWAIT_*` methods are `__await__`. A
  reactor without asyncio drives a coroutine that awaits promises of
  Pyjoyment; the asyncio reactor runs it as a task.
- A method that the base class of Mojo leaves to a subclass raises
  `NotImplementedError` with the message of Mojo's croak,
  `Method "x" not implemented by subclass`.
- Perl defers the handler of a signal to a safe point and returns from a
  system call that the signal interrupts. Python runs the handler in the
  middle of what the main thread does, where writing to a stream that is
  being written raises `RuntimeError`, and repeats the interrupted call until
  its timeout. So the handler of a server, as the ones of
  `Pyjo.Server.Prefork`, only notes the signal, which the main loop handles,
  and `signal.set_wakeup_fd` with a socket pair that the loop watches wakes it
  up. In the child of a fork, a reactor of asyncio that is not given a loop
  moves to a new one, as the selector of the loop of the parent, epoll or
  kqueue, is not the child's. Python clears in the child a signal that comes
  during the fork, and the child has the handlers of the parent until it sets
  its own, so a signal that the child must not miss, as QUIT of a worker of
  `Pyjo.Server.Prefork`, is blocked with `signal.pthread_sigmask` across the
  fork and unblocked once the child has its handler.
- The signals of the servers follow the conventions of containers, where
  Mojo follows the ones of nginx and unicorn: Docker and Kubernetes stop a
  server with TERM, so INT and TERM shut `Pyjo.Server.Daemon`,
  `Pyjo.Server.Prefork` and `Pyjo.Server.Hot` down gracefully, a second INT,
  as of Ctrl-C pressed twice, immediately, and QUIT immediately; HUP reloads,
  as in gunicorn and in `ExecReload` of systemd: a hot deployment in
  `Pyjo.Server.Hot`, where Mojo has USR2, which is left out, so that no
  signal keeps the meaning that Mojo gives it, a graceful restart of the
  workers in `Pyjo.Server.Prefork`, and nothing in `Pyjo.Server.Daemon`. A
  worker stops gracefully on TERM and ignores INT, which Ctrl-C sends to all
  the processes of the server. `graceful_timeout` of `Pyjo.Server.Prefork`
  is 25 seconds, where Mojo has 120, below the 30 seconds that Kubernetes
  gives a container to stop, so that the server forces its workers and stops
  by itself before the orchestrator kills it. The tests of Mojo that send
  these signals have `# Unlike Mojolicious:` comments. Windows has INT, TERM
  and BREAK only, and a TERM of another process terminates the process there
  without its handler, so BREAK, of Ctrl-Break, takes the place of QUIT, and
  a server stops from its console.
- `File::Spec` and `File::Basename` follow the system, so `Pyjo.File` has
  their rules of Unix and, on Windows, of `File::Spec::Win32` and of
  `MSWin32`, with the volume of a path and both separators. A file is read
  and written with `os.O_BINARY` there, as `sysread` and `syswrite` pass the
  bytes as they are, where the text mode of Windows writes `\n` as CRLF.
- `local` on an attribute, as `local $self->{running}`, is the value saved
  before and set back in a `finally`.
- `__del__`, the counterpart of `DESTROY`, does nothing when
  `sys.is_finalizing()`, as Mojo checks `${^GLOBAL_PHASE}`, and keeps its
  whole body in a `try`: at the end of the interpreter the globals of the
  module may already be `None`, even `sys`.
- Perl runs `DESTROY` when the last reference goes, at the end of a
  statement; the garbage collector of Python frees the objects in cycles at
  any allocation, even in the middle of what an event loop does, as inside
  `selector.register` of asyncio. A finalizer that changes an event loop, as
  one that closes a socket or removes an acceptor, cleans up through
  `Pyjo.Reactor._finalize`: at once, as `DESTROY`, unless it interrupted a
  frame of `Pyjo.IOLoop`, of a reactor, of asyncio or of `selectors`, where
  the cleanup waits for the next tick of the event loop, which every reactor
  runs at a point that is safe, and for the end of the interpreter. The
  garbage collector runs in any thread that allocates, as a thread of name
  resolution, whose frames do not show what the thread of the event loop
  does, so a finalizer outside of the thread of the reactor of its object,
  the main one for an object without a reactor, always waits for the next
  tick of that thread, which any of its reactors runs, as an object may
  belong to several event loops, and the asyncio reactor is woken up with
  `call_soon_threadsafe`; on Linux, epoll reports a socket closed in the
  middle of `add_reader` as `FileNotFoundError`. `t/stdlib/IOLoop_gc.py`
  makes the garbage collector run all the time.
- Each thread of Perl has a copy of the interpreter, with a `Mojo::IOLoop`
  singleton of its own; Python shares the module, so `Pyjo.IOLoop.singleton`
  is found with `__getattr__` of the module in a `threading.local`, the
  functions of the module, as `Pyjo.IOLoop.timer`, call their methods on it,
  and a reactor runs in the thread that made it. Threads run event loops of
  their own at the same time, as `t/stdlib/IOLoop_threading.py` checks.
- An optional module of Perl that Mojo uses when it is installed has a
  counterpart in the standard library, one of the port's own where the
  standard library has none, or is left out until something needs it:
  Net::DNS::Native is `getaddrinfo` in a thread that tells the reactor through
  a socket pair, IO::Socket::Socks is a SOCKS5 client in `Pyjo.IOLoop.Client`,
  which `PYJO_NO_SOCKS` turns off as `PYJO_NO_TLS` does TLS, and
  `socket_options` of IO::Socket::IP is `source_address`, as
  `socket.create_connection` has it. `SSL_hostname` and `SSL_verifycn_name`
  of IO::Socket::SSL are one `tls_hostname`, as Python has one
  `server_hostname` for SNI and for the verification.
- `tls_options` of IO::Socket::SSL is an `ssl.SSLContext`, `tls_context`, as
  asyncio takes `ssl=context`. OpenSSL chooses an ALPN protocol by the order
  of the server, IO::Socket::SSL by the order of the client.
- A timer of no time, as `next_tick` makes, runs in Mojo's reactor in the
  same tick as the I/O before it, so before the next I/O; asyncio runs a
  `call_later(0)` after the I/O of its next iteration, and a `call_soon`
  before it, so the asyncio reactor schedules such a timer with `call_soon`.
  The callbacks of `next_tick` run until none is left, as in Mojo, also the
  ones that they add, so code that tries again until something is there, as
  a body without a chunk yet, tries with a timer of no time, which lets the
  I/O and the timers of the next cycle run first.
- A callback that an asyncio loop keeps, as a timer or an I/O watcher,
  refers to the reactor weakly, so that the reactor and the loop it owns do
  not make a cycle: in a cycle the garbage collector may close the sockets of
  the loop before the loop itself, and closing the loop then fails.
- asyncio does not nest event loops, and it logs an exception that a
  callback raises instead of passing it on. Where Mojo runs the reactor from
  a callback, the port returns at once, and an exception that Mojo lets die
  out of `start` is kept by the reactor and raised after the loop stops.
  So code that the event loop calls never runs the event loop to wait: the
  `one_tick` of the asyncio reactor returns at once in a loop that runs, so a
  wait on it spins for ever, and `Pyjo.Reactor.Poll` would run the callbacks
  of other connections in the middle of the code that waits. A server that
  waits for a response, as `Pyjo.Server.WSGI`, waits only where the event
  loop does not run, and gives empty chunks of the body until it is there in
  the one that runs, and `Pyjo.App.WSGI` takes each chunk of the body of its
  application in a tick of its own, once the one before has been written,
  not in the middle of what the server writes. An application mounted in
  another one in the same process, as in the examples
  `mount_wsgi_inception.py` and `mount_asgi_inception.py`, is what catches
  such reentry in the tests, which a test in two processes would hide.
- A module that is not ported yet but uses a ported one follows its API: the
  lines that use it are taken from the target Mojolicious, and so is the
  expectation of a test of them that the target changed.
- The files that Mojolicious bundles in `lib/Mojolicious/resources` are in
  `Pyjoyment/resources`, with `pyjo` in the place of `mojo` in their paths, as
  `pyjo/logo-white.png` for `mojo/logo-white.png`. The artwork of Mojolicious,
  as its logo, the raptors, the favicon and the pinstripes, is not copied: it
  is under CC-BY-SA, and the license of Mojolicious does not grant its logo.
  Its place is taken by the artwork of Pyjoyment, in the same formats and
  sizes: a joystick for the logo, and a unicat, a cat with the horn of a
  unicorn and a rainbow, for the raptor, whose images are named after it,
  `failunicat.png` and `nounicat.png` for `failraptor.png` and `noraptor.png`.
  The code, templates and tests that use these paths have a
  `# Renamed from Mojolicious:` comment. Each image has its source next to it,
  an SVG of the same name, which is edited and rendered again with
  `rsvg-convert logo.svg -o logo.png`; `favicon.ico` holds the renders of
  `favicon.svg` at 48, 32 and 16 pixels. The text in them is set in Fredoka,
  under the SIL Open Font License, and converted to paths, so that the SVG
  needs no font.
- The JavaScript libraries that the bundled templates use, Bootstrap and
  highlight.js, are kept up to date on their own, not in the versions that
  Mojolicious bundles. `package.json` names their packages of npm, with exact
  versions that Renovate bumps, and maps the files of the packages to the files
  in `Pyjoyment/resources/public/pyjo`, under the names that Mojolicious gives
  them; `npm run bundle` copies them, after `npm ci --ignore-scripts`, which
  checks the packages against `package-lock.json` and runs none of their
  scripts:

  ```sh
  mise exec -- npm ci --ignore-scripts
  mise exec -- npm run bundle
  ```

  The workflow Bundle Check fails a pull request whose files do not match the
  lock, and commits them to a branch of Renovate, which cannot run the copy,
  with the token of the workflow; a push with that token starts no workflow, so
  the job starts Bundle Check, Build, Tests and Trunk Check on the commit with
  `workflow_dispatch`. Renovate keeps a major release for an approval in its
  Dependency Dashboard, as the tests do not run JavaScript: such a release is
  checked in a browser, and the templates follow its API. `bootstrap.js` is the
  bundle of Bootstrap, which has Popper, so Pyjoyment has no `popper.js`, and
  the build of highlight.js has Python among its languages. Each library has
  the text of its license in a `LICENSE` next to it. The stylesheet
  `mojo/mojo.css` is `pyjo/pyjo.css`, the theme of highlight.js
  `highlight-mojo-dark.css` is the one of Mojolicious, and `pyjoyment.min.js`,
  the language of highlight.js for the templates, is `mojolicious.min.js` with
  Python in the place of Perl; the copy leaves them as they are. Trunk does not
  lint or format any of them, so that a newer version replaces them as they
  are. The links of the pages are those of Pyjoyment. A bundled template has
  its markers as comments of the template, as `%# Renamed from Mojolicious:`.

## Standard Input and Output

`Pyjo.IOLoop.Stdio` serves a protocol on the standard input and output, as the
transport stdio of MCP or LSP, where a single stray byte on the standard
output breaks the protocol, so it takes them for itself: it reads and writes
duplicates of the file descriptors `0` and `1`, the descriptor `0` reads
`/dev/null`, and the descriptor `1` and `sys.stdout` write to the standard
error, so that a `print`, a library or a process that inherits them writes
there; `close` gives them back. A test runs it in a process of its own, as
`t/Pyjo/IOLoop_Stdio.py` does, as it changes the descriptors of its process.

- `O_NONBLOCK` belongs to the open file description, which the process shares
  with its parent and the other processes of a pipeline, so the stream sets
  it only on pipes and sockets and gives back the mode that it had, and a
  terminal, whose description the shell shares, stays blocking.
- A reactor watches pipes, sockets and terminals, but epoll watches no file
  and no `/dev/null` (`EPERM`) and kqueue no `/dev/null` (`EINVAL`), so a file
  is read with a timer of no time and written at once, as its reads and writes
  do not block.
- A peer that writes requests without reading the responses fills the pipe of
  the output, and then the buffer of the stream grows without a limit; a
  server that has much to write waits for `drain`, with the callback of
  `write` or `send`, or stops reading while `can_write` is false. A blocking
  write in its place would deadlock both sides once both pipes are full.
- The end of the input is the event `end`, not `close`, as the responses of
  the requests in progress are still to be written: without a subscriber, the
  stream closes gracefully, as a connection of TCP that the peer closes.
- Windows has no pipes that the event loop watches, so the constructor
  raises there, as `Pyjo.IOLoop.ChildProcess` emits `error`.

A framing of `Pyjo.IOLoop.Messages` decodes one message at a time, so that a
message over the maximum size, which closes the stream, does not lose the
messages before it in the same read, and `Lines` remembers how far it has
searched, so that a long line that comes in many reads is not searched from
its beginning each time. With the input and the output of a child process,
`close_gracefully` closes the output only, the standard input of the child,
which is how a server of the standard input and output learns that no request
comes anymore, and the input is read until the child ends it, so that the
responses of the requests in progress still come in.

The promises of a stream and of its messages, `read_p` and `message_p`, and
their iterators, pull them as the streams of Node.js in their paused mode: the
stream reads only while a promise waits, so that a peer that sends more than
is asked for waits in the pipe, and what came before the first promise went to
the subscribers of the event `read` alone, as a stream of Mojo emits what it
reads at once. The reactor of asyncio runs a coroutine as a task, in the next
cycle of its loop, where the base reactor runs it at once until it waits, so
a promise or an iterator is made before the coroutine that awaits it, as
`read_all_p` asks for its first chunk at once, and `once_p` before the event
that it waits for. The methods of `Pyjo.EventEmitter` are `once_p` and
`events`, as `iterate` of a stream takes a size.

`serve` of `Pyjo.JSON.RPC` makes both peers of a stream servers and clients,
so it drops a response to no call of its client, as answering it with an
error, as a server answers what is not a request, would send the error back
and forth between two peers that serve each other.

## Distributions of Their Own

What needs a dependency is a distribution of its own, never a part of
Pyjoyment: a reactor on another event loop, as Pyjo-Reactor-Twisted, or a
plugin that needs a library. Each lives in a repository of its own, next to
the checkout of Pyjoyment, so that one does not pull the dependencies of
another, and follows the conventions of this file, which its own `AGENTS.md`
points to; its documentation leaves out the paragraph "It has no counterpart
in Mojolicious", which is obvious there. What it teaches about Pyjoyment comes
back here.

- **The package.** A distribution adds a module to a namespace of Pyjoyment,
  `Pyjo.Reactor` or `Pyjoyment.Plugin`, which `extend_path` keeps open: its
  wheel has only the module (`only-include` of hatchling), without the
  `__init__.py` of the packages, which are those of Pyjoyment. Until the
  revival of Pyjoyment is on PyPI, `tool.uv.sources` takes Pyjoyment from its
  Git repository, never from a path to the checkout next to it: uv applies the
  sources of a dependency of Git, so whoever installs the distribution from Git
  would get a subdirectory of its repository that does not exist. Its tests
  lay the checkout next to it over the one of Git with `uv run --with-editable
../Pyjoyment`, so that they test what is there.
- **The tests.** Its CI checks out Pyjoyment next to it and runs the whole
  suite of Pyjoyment with the distribution, as `PYJO_REACTOR` set to the
  reactor, on the Pythons of the matrix of Pyjoyment, daily too, as Pyjoyment
  changes more often. A test of its own covers only what the suite does not,
  as the port of the test of a reactor of Mojolicious (`reactor_ev.t`).
- **A reactor on an event loop that is unique in a process**, as the reactor
  of Twisted, is a subclass of `Pyjo.Reactor.Poll`, as `Mojo::Reactor::EV` is,
  and `new` returns a `Pyjo.Reactor.Poll` object while another object uses the
  loop. A loop that cannot run a second time, as `reactor.run()` of Twisted, is
  driven one iteration at a time by `one_tick`, with the I/O before the timers,
  as the reactor of poll has them: with the timers first, a recurring timer of
  no time starves the I/O. While the loop runs, started by something else,
  `start` and `one_tick` return right away, as `Pyjo.Reactor.Asyncio` does.
- **State in the kernel.** Pyjoyment closes some sockets before it removes
  them from the reactor, and forks the workers of `Pyjo.Server.Prefork`, the
  servers of `Pyjo.Server.Hot` and `Pyjo.Server.Reload`, and the subprocesses.
  A loop that keeps its state in the kernel, as epoll or kqueue, loses a
  socket that is closed before it is removed, and shares the state with the
  child of a fork, so a reactor prefers a loop with its state in the process,
  as poll or select, gives the child of a fork what is its own, as the waker
  of the loop, and is tested on Linux, as macOS has no epoll to show it.
- **Hang-ups.** A loop that drops a handle at a hang-up or an error without
  data, as a refused connection, still calls the watcher, as
  `Pyjo.Reactor.Poll` does: the watcher finds the error of the socket, as
  `Pyjo.IOLoop.Client` does to try the next address.
- **References.** The callbacks that a loop of the whole process keeps refer
  to the reactor weakly, and a callback does not refer to itself, as a
  recurring timer that schedules itself from its closure would: the cycle
  keeps the callback, and what it refers to, as a controller, until the
  garbage collector runs, which `t/Pyjoyment/longpolling_lite_app.py` catches.
  A finalizer removes what an object leaves in the loop.
- **The direction of the dependencies.** A distribution depends on
  Pyjoyment, never the other way: its code imports Pyjoyment, its CI checks
  Pyjoyment out, and its documentation may link to the one of Pyjoyment, with
  intersphinx too. Pyjoyment knows a distribution only by a plain link on the
  page of the documentation that lists them, which the distribution adds with
  a pull request: no import, no autodoc, no intersphinx and no CI of a
  distribution, which would make Pyjoyment depend on its dependencies, and
  fail its build with -W where the site of the distribution does not answer.
- **The formats.** The docstrings are reStructuredText, as those of
  Pyjoyment, so that they read the same; the README and `AGENTS.md` are
  Markdown, which GitHub and PyPI render, as those of Pyjoyment.

## Linting and Formatting

[Trunk](https://docs.trunk.io) runs the linters and formatters configured in
`.trunk/trunk.yaml`: ruff for Python (lint, import order and formatting),
prettier for Markdown, YAML and JSON, taplo for TOML, yamllint, markdownlint,
actionlint, and shellcheck and shfmt for the shell scripts. shellcheck runs
with all its checks but the ones that `.shellcheckrc` disables, and shfmt
formats as `.editorconfig` says, with the branches of `case` indented: the
definition of shfmt in `.trunk/trunk.yaml` runs it without the flags that
would make it ignore `.editorconfig`. actionlint is the one of the
maintained fork kjanat/actionlint, whose releases continue those of
rhysd/actionlint after 1.7.12: `downloads` in `.trunk/trunk.yaml` replaces the
URLs of the plugin with those of the fork, whose files have the same names.
The `trunk` launcher is not pinned in
`mise.toml` (mise only has it as an npm package); install it with
`mise use -g trunk` or the installer from the Trunk documentation. The
launcher downloads the CLI version named in `trunk.yaml`.

```sh
trunk fmt          # format changed files
trunk check        # lint changed files
trunk check --all  # lint everything, as CI does
```

Without `--fix` or `--no-fix`, `trunk check` asks whether to apply each
autofix and waits for an answer, which hangs a non-interactive shell such as
an agent's. Pass one of them there.

`trunk-fmt-pre-commit` formats staged files on commit and
`trunk-check-pre-push` checks before a push, once Trunk has installed its git
hooks (any `trunk` command does). The hook formats with the configuration that
is staged, so a change to the formatter configuration goes in its own commit,
before the code that depends on it.

A commit that only reformats code goes into `.git-blame-ignore-revs`, so that
`git blame` and GitHub's blame view skip it. The trunk action
`git-blame-ignore-revs` points `blame.ignoreRevsFile` at the file locally.

The workflow Automated trunk upgrade runs `trunk upgrade` every day and keeps
its changes in the pull request of the branch `automated/trunk-upgrade`, which
a comment `/rerun` runs again; it works with the token of the workflow, and
starts Tests and Trunk Check on the branch with `workflow_dispatch`, as Bundle
Check does. A linter that the upgrade enables is kept or disabled there, with
its configuration in the root of the repository, where the extensions of the
editors find it, not in `.trunk/configs`.

The linters are there to keep plain mistakes out, not to enforce PEP 8: the
project bends Python's conventions on purpose, and a rule that fights its
style is turned off. Every disabled rule or linter carries a comment with the
linter's own message for it, not just the code (`B018 "Found useless
expression..."`, not `B018`), and why it does not fit. A single false
positive is silenced where it happens (`# noqa: B023`), with a comment on the
line above.

The ruff configuration lives in `pyproject.toml`. Its rule list is explicit:
newer ruff versions enable many more rules by default, including one that
rejects the Mojo-style module names. Formatting uses single quotes and a line
length of 120. Imports list `Pyjo` modules before the standard library, like
Mojo modules list `Mojo::*` before core modules.

New code targets Python 3.12 and newer: no compatibility shims for older
versions. The ruff `UP` rules and `target-version` keep it that way; with a
newer target, the formatter would use syntax such as `except A, B:` (PEP 758,
Python 3.14), which also looks like Python 2's `except A, e:`. A test of
t-strings, which only Python 3.14 compiles, is listed under
`per-file-target-version` of ruff and `executionEnvironments` of pyright in
`pyproject.toml`, with `pythonVersion = "3.14"`.

## Type Hints

Modules are annotated as they are ported, and pyright checks them in strict
mode; the code that has not been ported yet is not type-checked. The
configuration in `pyproject.toml` turns type checking off for everything and
lists the annotated modules under `strict`. A ported module goes on that list
in the same change. Trunk passes the changed files to pyright explicitly,
which makes pyright ignore `include` and `exclude`, so the per-file mode is
what limits the checks. Examples that need libraries the project does not
install are excluded from pyright in `.trunk/trunk.yaml`, and so is
`Pyjo.Test.pytest_plugin`, which imports pytest, so it is not on the strict
list: check it in strict mode with pytest installed, from a configuration
outside the repository that names it in `include` and the virtual
environment with pytest in `venvPath` and `venv`. pyright, as Python with a
script, resolves an import against the directory of the file first, so a
module named `pytest.py` would import itself.

Trunk reports only the issues that a change introduces, and counts an issue
in a file that already exists upstream as existing, even when the file has
just been put on the strict list. Check a newly strict module with
`trunk check --show-existing` or with `.trunk/tools/pyright` directly.

Python 3.12 evaluates the annotations of a function when it defines it, so
a module in an import cycle, like `Pyjo.String.Unicode` and
`Pyjo.String.Bytes`, quotes the annotations that name the other module. So
does a package that names its own submodules, as `Pyjo.DOM.CSS` in
`Pyjo/DOM/__init__.py`: `Pyjo.DOM` is not an attribute of `Pyjo` until the
package is loaded.

A module that ends with `object = Pyjo_X` cannot use `object` in its
annotations: they are evaluated lazily (PEP 649, Python 3.14), when `object`
is the class. Such a module declares `type Anything = builtins.object` and
uses that.

Annotations use the Python 3.12 syntax: generics with type parameters
(`class Collection[T](list[T])`, `def f[T](x: T) -> T`), `type` aliases,
`Self` for methods that return `self` so that chains keep their type, and
`@overload` for functions with several call forms, like `Pyjo.Test.subtest`.
A descriptor class with an overloaded `__get__` types what Mojo makes with
`monkey_patch`: a `property` made by a call is `Any` to pyright.
A class method that returns instances of the class, like `parse`, is generic
(`def parse[C: Pyjo_Cookie](cls: type[C], ...) -> list[C]`): with `list[Self]`,
pyright rejects the method of a subclass as an incompatible override. A
ported module that uses one that is not ported yet gets annotations on the
signatures it uses, while the module itself stays off the strict list. Where
Mojo-style magic cannot be typed, `Any` is fine, with a comment that says why.
`Pyjo/py.typed` and `Pyjoyment/py.typed` (PEP 561) tell type checkers that the
packages are typed, so that pyright in strict mode takes the annotations of a
module of Pyjoyment that a distribution of its own uses, as a controller,
instead of failing on a library without stubs.

## Session and Temporary Files

Files created while working on a task, such as scratch scripts, command
output, a clone of the Mojo repository, or build artifacts, must never be
written into the tracked working tree, or they leak into git history. Write
them to a temporary directory outside the repository.

Never `git add -A` or `git add .` blindly: review `git status` first and stage
only the files the change actually touches.

## Security

Never read, display, reference, or include the contents of the following files:

- `.env`, `.env.*`, `.envrc`
- `.pypirc`
- `*.jks`, `*.keystore`, `*.p12`, `*.pfx`, `*.pem`, `*.key`

The same list is git-ignored in `.gitignore` and enforced for Claude Code by
the `permissions.deny` rules in `.claude/settings.json`. Change all three
together. The one exception is `Pyjo/IOLoop/certs/server.key`, the key of
the default certificate for TLS servers (as in Mojo): it is tracked, and
`.gitignore` whitelists it, because hatchling builds packages from the
`.gitignore` patterns and would otherwise leave it out of the wheel.

The certificate `server.crt` is for `localhost` and `127.0.0.1`, and a CA of
its own, `ca.crt`, signs it, so that the tests can verify it. The key of the
CA is not kept: new certificates come with a new CA, made with OpenSSL 3
(RSA 2048, a hundred years, `basicConstraints`, `keyUsage`,
`extendedKeyUsage=serverAuth` and `subjectAltName=DNS:localhost,IP:127.0.0.1`
for the server), and the key of the CA is deleted afterwards.

The certificates of the tests in `t/certs` are the other exception: their
keys are tracked, and `.gitignore` lets `t/certs/*.key` in, as the tests of
TLS need them. Another CA of its own, `t/certs/ca.crt`, whose key is not kept
either, signs `server` (`localhost`, `127.0.0.1`, `::1`, `serverAuth`),
`mojo_server` (`mojolicious.org`) and `client` (`clientAuth`), and `bad` is
self-signed. They are made all of them together with a new CA, with the
commands in `t/certs/README.md`. Claude Code does not read these keys either: the
rules of `.claude/settings.json` stay as they are, and the tests read the
keys.

## Documentation

`README.md` is for a user, the front page of the repository on GitHub and of
the project on PyPI: what Pyjoyment is, its status, how to install it,
examples, and where the documentation is. This file is for whoever
changes the code: how it works and why. Module documentation lives in the
module docstrings, ported from Mojo's POD in the same layout (synopsis,
events, attributes, methods), and Sphinx builds the API reference in `docs/`
from them. Read the Docs builds the documentation with the Sphinx of
`docs/requirements.txt`, which has pytest too, as autodoc imports
`Pyjo.Test.pytest_plugin`, and so does the workflow Docs, with `-W`, so that
a warning, as a reference that is not found or a docstring that is not valid
reStructuredText, fails the pull request that makes it:

```sh
mise exec -- uv run --with-requirements docs/requirements.txt sphinx-build -W --keep-going -b html docs docs/_build/html
```

The documentation on Read the Docs and the front page on GitHub are two
things with two readers, so the intro, status, installation and license
pages in `docs/` have the same text as the sections of `README.md`, in
reStructuredText and in Markdown, and a change of one goes to the other.
`README.md` has examples of its own besides, a choice of the short ones. The
pages of `docs/` include the examples from `examples/`, never copied: a copy
is not tested and goes stale. `README.md` is the exception, as GitHub does
not include files: its examples are copies of `examples/`.
`docs/conf.py` takes the name, the authors and the version from
`pyproject.toml`.

The guides of Mojolicious, `Mojolicious::Guides::*`, are pages of
`docs/guides`, as `tutorial.rst` for `Mojolicious::Guides::Tutorial`, which
start as ports, with the sections and the wording of Mojo and the forms of
Pyjoyment, and end with the name of their source, as the modules do. The
docstrings are the living documentation of the API and the modules, so they
stay ports of the POD, while the guides are loose, additional documentation,
whose divergence from Mojo nobody watches. So, unlike a docstring, a guide is
not kept 1:1 with Mojo: it adds, moves and rewrites sections for what a Python
developer needs, as the test scripts, the harness and the assertions of
`Pyjo.Test` in `testing.rst`, which a Perl developer knows from `Test::More`
and `prove`, and it has no `Not in Mojolicious:` comments; the ones that are
left go when the guide is edited. A subject that outgrows the guide of
Mojolicious it was added to becomes a guide of its own, without a source to
name, as `mounting.rst` for the applications of other frameworks that
`Pyjoyment.Plugin.Mount` mounts, which `routing.rst` links to from the
section of Mojolicious about mounting. `Mojolicious::Guides` is
`docs/guides/index.rst`, whose section API is the class hierarchy of the
modules of `docs/api`, each under the module of the base class of its
class, which `t/docs/guides_index.py` checks, so that a new module goes into
it. A part of a guide that is about the Mojolicious project rather than the
code, as its voting rules, is left out with a comment of reStructuredText
that starts with `Left out from Mojolicious:`. An example that is a whole
application is a file of its own, in a directory with the name of the page,
as `docs/guides/tutorial/`, which the page includes with `literalinclude`
and the test of the guide in `t/docs` loads, so that what the reader sees is
what is tested; a short snippet stays in the page, and the test has a copy of
it. A guide that grows an application of several files, as `growing.rst`,
has a directory for each stage, with only the files that the stage adds or
changes, and the final application whole, in `docs/guides/growing/login`:
its test copies the stages over each other into a temporary directory and
runs the commands of the guide there, as `inflate` and the moves of the
templates, so that each stage is tested as the reader has it, and pyright
finds the modules of the final application from the other stages with
`extraPaths` in `pyproject.toml`. A guide whose examples are several
applications, as `routing.rst`, has a directory for each, which its test
puts on `sys.path` while it loads that application, after it removes the
modules of the one before, as they all have the package `MyApp`. A plugin of
an example is a file of `Pyjoyment/Plugin` in its directory, which
`extend_path` adds to the namespace only when the directory is on
`sys.path` before `Pyjoyment.Plugin` is imported; the test removes it from
`sys.path` afterwards, as a `MyApp` with `__init__.py` there would hide a
`MyApp` without it, which Python makes a namespace package only when no
regular package of the name is found. Two plugins of the same name, as the
two forms of one in `rendering.rst`, are run with the script that loads
them in a process of their own, with their directory in `PYTHONPATH`. The
remote services that the examples request, as in `cookbook.rst`, are
answered by a mock, as the tests do not use the network: the event `start`
of the user agent sends a request to it, with the host of the service as
the `Host` header, and the mock runs in a process of its own, as a blocking
request runs an event loop of its own, which a server on the event loop of
the test would not answer. The
names of the files are not those of modules of the standard library,
as the directory of a script is the first one of `sys.path`. A link to a
guide that is not ported yet goes to the one of Mojolicious. An example of
Mojolicious that does not do what its guide says at the tag of the release,
as a template that does not exist, which gives 500 and not 404, is
corrected in the port, and goes to the issue that collects the quirks of
Mojolicious.

Documentation describes how things are and has to stay true without anyone
maintaining it. Keep out of it whatever goes stale on its own: issue and pull
request numbers, dates, counts that change without the document changing, and
the record of how it got there (decisions taken, alternatives rejected, status
lines). State the rule or the fact instead. The history belongs in the issue
and the pull request.

## Commits and Pull Requests

- Commit subjects are short and in the imperative or descriptive style of the
  history, optionally prefixed with the module:
  `Pyjo.IOLoop.Client: port is converted to int`.
- Keep mechanical changes (formatting, import order, renames) and functional
  changes in separate commits.
- A pull request description lists the changes and a validation checklist;
  check an item only once it has been verified.
- A pull request fixes what it finds at the cause, also in another module than
  the one it is about, as the reactor of a change of an adapter, in a commit
  of its own, rather than working around it in a test: Pyjoyment is a
  framework, and a defect that one module shows is often in the one below it.
- A change of `AGENTS.md` alone, as what a distribution of its own teaches, is
  committed on `main` directly, without a pull request.
