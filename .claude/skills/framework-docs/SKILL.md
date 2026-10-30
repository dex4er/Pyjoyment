---
name: framework-docs
description: Write the documentation of Pyjoyment itself, with README.md and the pages of docs that repeat it, the docstrings ported from the POD, the guides of docs/guides ported from Mojolicious::Guides with their tested examples, and Sphinx. Use when changing the documentation of the framework.
---

# Documentation of Pyjoyment

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
