# Agent Guide: Pyjoyment

## Overview

Pyjoyment is a port of [Mojolicious](https://mojolicious.org) to Python. The
`Pyjo` package mirrors the `Mojo::*` toolkit (URL, DOM, HTTP messages, user
agent, servers, event loop), and the `Pyjoyment` package is reserved for the
`Mojolicious::*` framework layer (routes, controllers, renderer, `Lite`).

The code was written against Mojo 6.x. The project is being revived: the
target is Mojolicious 9.49 on Python 3.12+, with asyncio as the only I/O
core. The plan, its order and its progress live in GitHub Issues, starting from
the open umbrella issue about the revival; this file describes how the project
works and why, not what is left to do.

## Design Principles

These are deliberate. A change that looks like a cleanup but goes against one
of them is a regression.

- **The spirit of Mojo over strict PEP 8.** Pyjoyment uses Python creatively,
  the way Mojo bends Perl. Module and class names follow Mojo
  (`Pyjo.URL`, `Pyjo.IOLoop.Client`), objects are created with `Class.new()`,
  and setters return `self` so calls chain.
- **Every statement has an expression form.** Helpers in `Pyjo.Util` such as
  `die`, `setenv`, `slurp` and `spurt` look redundant next to `raise`,
  `os.environ[...] = ...` and `pathlib`, but statements cannot appear in a
  lambda, a callback or a chain, and these can. Do not replace them with the
  standard library equivalent.
- **Every return value chains.** Functions return the framework's own types so
  the next method is available: `slurp` returns a string, `Collection.join`
  returns `Pyjo.String.Unicode`, DOM queries return `Pyjo.Collection`. A
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
- **Asyncio is the event loop.** Mojo's reactor exists because Perl has no
  standard event loop; Python has one. Mojo 9 moved from callbacks and
  `Mojo::IOLoop::Delay` to promises and async/await, and the Python
  counterpart of that is `asyncio`. A promise is an `asyncio.Future` subclass
  with Mojo's `then`/`catch`/`wait` API, so the same object works with
  `await`, with `asyncio.gather`, and in a callback chain.
- **Python 3.12 is the minimum, template strings come with 3.14.** t-strings
  (PEP 750) keep interpolations separate from the literal text, which gives
  templates auto-escaping without a template language. The `t"..."` syntax is
  written by the user, not by the library: the library only accepts
  `string.templatelib.Template` objects, so it supports them where the module
  exists and stays importable on Python 3.12 and 3.13, where PyPy is.
- **PyPy is supported on a best-effort basis.** Helper code for PyPy is fine,
  and a test may be skipped on PyPy where PyPy clearly differs from CPython,
  with the reason in the skip message.
- **No runtime dependencies.** Development tools are fine; `dependencies` in
  `pyproject.toml` stays empty.

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

`uv.lock` locks the Python dependencies; there are none at run time yet. After
a change to `pyproject.toml`, run `mise exec -- uv lock`; CI checks that the
lock matches with `uv lock --check`.

`mise install` re-locks only the platform it runs on. After changing a tool
version, run `mise lock` so every platform in `mise.lock` is refreshed; CI
installs with `--locked` and fails on a tool that is not in the lock.

## Tests

The tests are scripts that print [TAP](https://testanything.org/), written
with `Pyjo.Test`, which is inspired by Perl's `Test::More`. They run with
`Pyjo.Prove`, a TAP harness inspired by Perl's `prove`:

```sh
PYTHONPATH=. mise exec -- python -m Pyjo.Prove -j 4 -r t
```

A single file runs on its own as well:
`PYTHONPATH=. mise exec -- python t/Pyjo/URL.py`. Perl's `prove` still works,
because the output is standard TAP; `.proverc` supplies its
`--ext=py --exec=python`.

- `t/Pyjo/` holds the module tests, ported from Mojo's `t/mojo/*.t`.
- `t/docs/` checks that the code in the module documentation is correct: it
  is the same code as in the docstrings, in the same order, with `print` and
  the comments that show a result turned into assertions. Documented code
  that prints TAP itself or ends the script, as in `Pyjo.Test`, runs as a
  script of its own, and the test checks its output and exit status.
- `t/stdlib/` checks the interaction with the Python standard library,
  written for Pyjoyment, as Mojolicious has no counterpart.
- `t/examples/` runs the scripts from `examples/`.
- `t/lib/` holds helpers shared by the tests. Run on their own, they skip with
  `plan(skip_all=...)`, so `-r t` reports them as skipped instead of failing.

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

The exit status comes from an `atexit` handler that `Pyjo.Test` registers,
and only once a test function has been called, so importing the module (as
Sphinx does) has no effect. Older test files still wrap their body in
`if __name__ == '__main__':`, which is no longer needed.

CI sets `PYTHONWARNINGS=error::SyntaxWarning,error::DeprecationWarning`, so an
invalid escape sequence or a deprecated API fails the build, before a new
Python removes it; the weekly run catches the deprecations of a new Python
release. Python keeps an unknown escape such as `"\:"` as a backslash
followed by the character, which is often exactly what a CSS selector or a
regular expression ported from Perl needs; write it as `"\\:"` or as a raw
string so it survives the Python release that turns the warning into an error.

CI runs the tests on every supported CPython version and on PyPy. PyPy frees
objects only when its garbage collector runs, not when the last reference
goes, so code must not rely on that: resizing a `bytearray` that a regex
iterator still scans raises `BufferError`, and `__del__` may not run at all
before the interpreter exits.

## Porting from Mojolicious

The target is **Mojolicious 9.49**: every module is ported from the `v9.49`
tag, so the ported modules match each other. Moving to a newer Mojolicious is a
step of its own, which changes this version and updates every ported module.

Some modules have no counterpart in Mojolicious: `Pyjo.Test` (inspired by
Perl's `Test::More`), `Pyjo.String.*`, `Pyjo.Regexp` and the helpers in
`Pyjo.Util` that turn statements into expressions. These extras follow their
Perl inspiration where it helps, without porting it, and their tests are
written for them rather than ported.

`Pyjo.Util` is not ported anew as a whole: next to the functions of
`Mojo::Util` it has helpers of its own, for Python. A function of it is
brought to the target when a ported module needs it, without changing what
the modules that are not ported yet get from it: typed signatures, and a
variant for `str` next to the one for `bytes` where Mojo works on
characters, like `url_unescape`.
Its subtests from `t/mojo/util.t` come to `t/Pyjo/Util.py` with it.

A module is ported anew from the target Mojolicious, not migrated from the
existing Python code. The existing Python module is a reference for how
Perl idioms were translated before, not a base to patch: it follows an older
Mojo and carries compromises that a fresh port does not need.

```sh
git clone https://github.com/mojolicious/mojo.git
git -C mojo checkout v9.49
```

For each module:

1. Port its tests from `t/mojo/*.t` first, keeping Mojo's test names and
   order, one assertion for one, without folding repeated ones into a loop,
   so that the diff of a newer Mojolicious applies to them. Mojo's tests are
   the specification.
2. Port the module from `lib/Mojo/*.pm` until the tests pass.
3. Port its POD into the docstrings: the same sections in the same order
   (synopsis, description, events, attributes, methods, operators, see also)
   and Mojo's wording, with Python names and examples. The POD is the source of
   the Python documentation. Sphinx lists the classes after the module
   docstring, so "See also" ends the module docstring, before them. A test in
   `t/docs/` runs the examples.
4. Name the source at the end of "See also", as a link to the file at the
   tag (`https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Date.pm`),
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

Mojo's tests and the behaviour of its code at the tag are the reference, not
its POD: the examples in the POD are not tested and can be wrong. Where they
disagree, run the Perl code from the clone (`perl -Imojo/lib -MMojo::URL -e ...`)
and port what it does.

A bug or a quirk of Mojolicious itself, found while porting, goes to the issue
that collects them, with a Perl command that reproduces it at the tag and what
the port does about it. Reporting it upstream is a decision of its own.

Moving a ported module to a newer target is the difference between the two
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
- A Perl string of characters is a `str`, and bytes in Python are `bytes`,
  encoded with the charset of the module. Perl keeps bytes that do not decode
  as a byte string, which is a `str` of the characters 0-255 in Python:
  `.decode('latin-1')`.
  HTTP headers are such characters too, as `http.client` has them: bytes
  from the wire are decoded as ISO-8859-1.
- An environment variable `MOJO_*` is `PYJO_*`.
- Where Mojo uses an optional XS module for speed, as `Mojo::JSON` uses
  `Cpanel::JSON::XS`, the port uses the module of the standard library in its
  place and keeps the port of the pure-Perl code behind a `PYJO_NO_*`
  variable. Mojo's tests of the pure-Perl code set the variable, and those of
  the XS module run against the standard library.
- `TO_JSON` is `__json__`.
- `Mojo::ByteStream` is `Pyjo.String.Unicode` for characters and
  `Pyjo.String.Bytes` for bytes. A Mojo test's `b(...)` is `u(...)` or
  `b(...)`, by what the string holds.
- A callback that Mojo calls with `$_` gets the element as its first
  argument. A method name in a string, as in `$collection->map('text')`, can
  name a property, which is how a Mojo attribute is ported.
- A method of `Mojo::Collection` that has the name of a `list` method, like
  `sort` and `reverse`, returns a new collection, as in Mojo, and
  `list.sort(collection)` sorts in place.
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
- A function named after a keyword of Python has a trailing underscore, as
  `raise` of `Mojo::Exception` is `raise_`. The functions of `Pyjo.Test` are
  the exception: they have an `_ok` suffix, as `is_ok`.
- A name of a Perl package, as `Mojo::Exception` takes them, is a dotted name
  of a class in Python (`'MyApp.X.Foo'`), resolved by importing the longest
  prefix that is a module.
- A stack trace, Perl's `caller` frames, is a list of
  `traceback.FrameSummary`, the most recent first, as Mojo keeps it.
- `like` of `Test::More` stringifies what it checks, `like_ok` does not:
  a test of an object is `like_ok(str(obj), ...)`.
- A test that depends on the layout of its own source lines, as the context
  of `Mojo::Exception` does, is kept from the formatter with `# fmt: off`.
- Perl frees a temporary object at the end of the statement, Python as soon
  as nothing refers to it. Where an object holds a resource, like the
  temporary directory of `Pyjo.File.tempdir()`, an object made from it, like
  its `child()`, keeps it, so that `tempdir().child('x').spew(...)` works as in
  Perl.
- A method that Mojo calls on the class or on an object, like
  `Mojo::DOM->new_tag` and `$dom->new_tag`, is a descriptor that passes either
  of them.
- A module that is not ported yet but uses a ported one follows its API: the
  lines that use it are taken from the target Mojolicious, and so is the
  expectation of a test of them that the target changed.

## Linting and Formatting

[Trunk](https://docs.trunk.io) runs the linters and formatters configured in
`.trunk/trunk.yaml`: ruff for Python (lint, import order and formatting),
prettier for Markdown, YAML and JSON, taplo for TOML, yamllint, markdownlint
and actionlint. The `trunk` launcher is not pinned in `mise.toml` (mise only
has it as an npm package); install it with `mise use -g trunk` or the
installer from the Trunk documentation. The launcher downloads the CLI version
named in `trunk.yaml`.

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
Python 3.14), which also looks like Python 2's `except A, e:`.

## Type Hints

Modules are annotated as they are ported, and pyright checks them in strict
mode; the code that has not been ported yet is not type-checked. The
configuration in `pyproject.toml` turns type checking off for everything and
lists the annotated modules under `strict`. A ported module goes on that list
in the same change. Trunk passes the changed files to pyright explicitly,
which makes pyright ignore `include` and `exclude`, so the per-file mode is
what limits the checks. Examples that need libraries the project does not
install are excluded from pyright in `.trunk/trunk.yaml`.

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
signatures it uses (`Pyjo.Base.new`, `Pyjo.Util.split_header`), while the
module itself stays off the strict list. Where Mojo-style magic cannot be
typed, `Any` is fine, with a comment that says why. `Pyjo/py.typed` (PEP 561)
tells type checkers that the package is typed.

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
together. The one exception is `Pyjo/IOLoop/certs/server.key`, the default
self-signed certificate for TLS servers (as in Mojo): it is tracked, and
`.gitignore` whitelists it, because hatchling builds packages from the
`.gitignore` patterns and would otherwise leave it out of the wheel.

## Documentation

`README.rst` is for a user: what Pyjoyment is, its status, how to install
it, examples, and where the documentation is. This file is for whoever
changes the code: how it works and why. Module documentation lives in the
module docstrings, ported from Mojo's POD in the same layout (synopsis,
events, attributes, methods), and Sphinx builds the API reference in `docs/`
from them.

The intro, status, installation and license pages in `docs/` include their
text from `README.rst`, between `.. begin-<name>` and `.. end-<name>`
comments, so the text is edited in `README.rst` only. The examples are
included from `examples/` the same way, never copied: a copy is not tested
and goes stale. `README.rst` is the exception, as it has to render on GitHub,
which does not support `include`: its examples are copies of `examples/`.
`docs/conf.py` takes the name, the authors and the version from
`pyproject.toml`.

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
