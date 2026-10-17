# Tests

The tests of Pyjoyment. Each `.py` file under this directory is a test script
that prints [TAP](https://testanything.org/), written with `Pyjo.Test` and run
by `Pyjo.Prove`, the harness of the project. `AGENTS.md` says how the tests
are ported from Mojolicious and the rules they follow.

## Layout

| Directory    | What it holds                                                                     |
| ------------ | --------------------------------------------------------------------------------- |
| `Pyjo/`      | tests of the `Pyjo` modules, ported from `t/mojo/*.t` of Mojolicious              |
| `Pyjoyment/` | tests of the framework, ported from `t/mojolicious/*.t`, as `*_lite_app.py`       |
| `docs/`      | the examples of the module documentation, with assertions                         |
| `stdlib/`    | the interaction with the Python standard library                                  |
| `examples/`  | the code of the scripts in `examples/`                                            |
| `servers/`   | Pyjoyment on real ASGI, WSGI and CGI servers, with the dependency group `servers` |
| `lib/`       | helpers shared by the tests, skipped when run on their own                        |
| `certs/`     | the certificates and keys of the TLS tests                                        |
| `cookies/`   | the cookie files of the tests                                                     |
| `templates/` | the templates of the tests of `Pyjo.Template`                                     |

The harness runs every `.py` file here, so Python files that a test only
reads, as the templates `index.html.py`, are in [`tt/`](../tt/README.md).

## Running

Run the commands from the root of the repository, with the tools of
`mise.toml`:

```sh
mise install
```

All the tests, four scripts at a time:

```sh
mise exec -- python -m Pyjo.Prove -l -j 4 -r t
```

One directory, or some files, with the output of each test:

```sh
mise exec -- python -m Pyjo.Prove -l -r t/Pyjoyment
mise exec -- python -m Pyjo.Prove -l -v t/Pyjo/URL.py t/Pyjo/Date.py
```

One file on its own:

```sh
PYTHONPATH=. mise exec -- python t/Pyjo/URL.py
```

As CI runs them, with the warnings of the development mode of Python, a
limit of time for each script, and its standard error after its result:

```sh
PYTHONDEVMODE=1 PYTHONWARNINGS=error::SyntaxWarning,error::DeprecationWarning \
  mise exec -- python -m Pyjo.Prove -l -j 4 --timeout 60 --capture-stderr -r t
```

On the reactor without asyncio:

```sh
PYJO_REACTOR=Pyjo.Reactor.Poll mise exec -- python -m Pyjo.Prove -l -j 4 t/Pyjo/IOLoop*.py
```

The tests of the servers, which install their dependency group:

```sh
mise exec -- uv run --python "$(mise exec -- which python)" \
  --only-group servers python -m Pyjo.Prove -l --timeout 120 -r t/servers
```

On Python 3.14 too, which still has the CGI server of `http.server`, in an
environment of its own:

```sh
UV_PROJECT_ENVIRONMENT=.venv-3.14 mise exec -- uv run --python 3.14 \
  --only-group servers python -m Pyjo.Prove -l --timeout 120 -r t/servers
```

The output is standard TAP, so Perl's `prove -lr t` works too; `.proverc`
gives it the extension and the interpreter.

A test with the syntax of a newer Python, as the t-strings of Python 3.14,
names the version in its inline metadata (PEP 723), and the harness skips it
on an older Python.
