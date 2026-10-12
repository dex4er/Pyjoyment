# Agent Guide: Pyjoyment

## Overview

Pyjoyment is a port of [Mojolicious](https://mojolicious.org) to Python. The
`Pyjo` package mirrors the `Mojo::*` toolkit (URL, DOM, HTTP messages, user
agent, servers, event loop), and the `Pyjoyment` package is reserved for the
`Mojolicious::*` framework layer (routes, controllers, renderer, `Lite`).

The code was written against Mojo 6.x and for Python 2 and 3 at once. The
project is being revived: the target is the latest Mojolicious on Python 3.14+,
with asyncio as the only I/O core. The plan, its order and its progress live in
GitHub Issues, starting from the open umbrella issue about the revival; this
file describes how the project works and why, not what is left to do.

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
  returns `Pyjo.String.Unicode`, DOM queries return `Pyjo.Collection`.
- **Builtin types are never patched.** New types that subclass or mirror a
  standard one and add framework behaviour are welcome, even when they look
  redundant: `Pyjo.Collection(list)`, `Pyjo.String.Unicode(str)`,
  `Pyjo.String.Bytes(bytes)`, and `Pyjo.String.Mixin`, which lets URL, Path,
  Headers and others behave like strings. Monkey-patching `str`, `list` or any
  other builtin is not.
- **Asyncio is the event loop.** Mojo's reactor exists because Perl has no
  standard event loop; Python has one. Mojo 9 moved from callbacks and
  `Mojo::IOLoop::Delay` to promises and async/await, and the Python
  counterpart of that is `asyncio`. A promise is an `asyncio.Future` subclass
  with Mojo's `then`/`catch`/`wait` API, so the same object works with
  `await`, with `asyncio.gather`, and in a callback chain.
- **Python 3.14 is the minimum**, for template strings (PEP 750): t-strings
  keep interpolations separate from the literal text, which gives templates
  auto-escaping without a template language.
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

`mise install` re-locks only the platform it runs on. After changing a tool
version, run `mise lock` so every platform in `mise.lock` is refreshed; CI
installs with `--locked` and fails on a tool that is not in the lock.

## Tests

The tests are scripts that print [TAP](https://testanything.org/), written
with `Pyjo.Test`, a port of Perl's `Test::More`. They run with `prove`:

```sh
PYTHONPATH=. mise exec -- prove t/Pyjo t/docs t/examples
```

`.proverc` supplies `--ext=py --exec=python`. A single file runs on its own as
well: `PYTHONPATH=. mise exec -- python t/Pyjo/URL.py`.

- `t/Pyjo/` holds the module tests, ported from Mojo's `t/mojo/*.t`.
- `t/docs/` checks the examples from the module documentation.
- `t/examples/` runs the scripts from `examples/`.

CI sets `PYTHONWARNINGS=error::SyntaxWarning`, so an invalid escape sequence
fails the build. Python keeps an unknown escape such as `"\:"` as a backslash
followed by the character, which is often exactly what a CSS selector or a
regular expression ported from Perl needs; write it as `"\\:"` or as a raw
string so it survives the Python release that turns the warning into an error.

## Syncing with Mojolicious

Mojo's tests are the specification. To sync a module, take the difference
between the Mojo version it was synced with and the target version, port the
changed tests first, then change the code until they pass:

```sh
git clone https://github.com/mojolicious/mojo.git
git -C mojo diff v6.39 v9.49 -- lib/Mojo/URL.pm t/mojo/url.t
```

Keep Mojo's test names and order, so the next sync is again a diff.

Perl and Python differ in a few places that a port must translate rather than
copy:

- A global inline regex flag such as `(?i)` is only valid at the start of a
  Python pattern; in the middle of one, use the scoped form `(?i:...)`.
- Perl's `weaken` is ported as `weakref.proxy`. Check whether the object
  behind a proxy still exists with `Pyjo.Util.isalive`; `dir(proxy)` and
  `bool(proxy)` raise `ReferenceError` for a dead proxy.
- `"\$"` in a double-quoted Perl string is a plain `$`; in Python it keeps the
  backslash.

## Python 2 Leftovers

The code still carries Python 2 compatibility: `sys.version_info` branches,
`u''` prefixes, `super(Class, self)`, `from __future__` imports, and the
nose and unittest adapters in `Pyjo.Test` and every test file. New code does
not add more of them. Removing them is a separate, mechanical step; mixing it
into a functional change makes both hard to review.

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

`README.rst` is for a user: what Pyjoyment is, how to install it, short
examples. This file is for whoever changes the code: how it works and why.
Module documentation lives in the module docstrings, in the layout of Mojo's
POD (synopsis, events, attributes, methods), and Sphinx builds the API
reference in `docs/` from them.

Documentation describes how things are and has to stay true without anyone
maintaining it. Keep out of it whatever goes stale on its own: issue and pull
request numbers, dates, counts that change without the document changing, and
the record of how it got there (decisions taken, alternatives rejected, status
lines). State the rule or the fact instead. The history belongs in the issue
and the pull request.

## Commits and Pull Requests

- Commit subjects are short and in the imperative or descriptive style of the
  history, optionally prefixed with the module: `Pyjo.IOLoop.Client: port is
  converted to int`.
- Keep mechanical changes (formatting, Python 2 cleanup) and functional
  changes in separate commits.
- A pull request description lists the changes and a validation checklist;
  check an item only once it has been verified.
