# Files of the tests

Python files that the tests in [`t/`](../t/README.md) use as data. They are
not tests: the harness runs every `.py` file under `t/`, so these are kept
outside of it.

| Directory           | What it holds                                                                                        |
| ------------------- | ---------------------------------------------------------------------------------------------------- |
| `templates/`        | templates of files of `Pyjoyment.Plugin.PyRenderer`, as `files/hello.html.py`                        |
| `templates_native/` | the same with the t-strings of Python 3.14, checked by ruff and pyright as Python 3.14               |
| `lib/`              | modules of the tests, as `PyjoymentTest.Plugin.DeploymentPlugin`, where Mojo has `t/mojolicious/lib` |
| `external/`         | applications that `Pyjoyment.Plugin.Mount` mounts, where Mojo has `t/mojolicious/external`           |

A test adds a directory to the paths of the renderer of its application, and
renders a template by its name:

```python
app.renderer.paths.append(app.home.dirname().dirname().child('tt', 'templates').to_str())

get('/hello', lambda c: c.render('files/hello', name='Joe'))
```

The templates are rendered by the tests that use them, as
`t/Pyjoyment/py_lite_app.py`, or for `templates_native/` by
`t/Pyjoyment/py_native_lite_app.py`, which runs on Python 3.14:

```sh
mise exec -- python -m Pyjo.Prove -l t/Pyjoyment/py_lite_app.py t/Pyjoyment/py_native_lite_app.py
```

A test of the modules of `lib/` puts the directory in front of `sys.path`:

```python
sys.path.insert(0, Pyjo.File.path(__file__).to_abs().dirname().dirname().dirname().child('tt', 'lib').to_str())

plugin('JSONConfig')  # with {"plugins": [{"PyjoymentTest.Plugin.DeploymentPlugin": {}}]}
```

The applications of `lib/`, as `PyjoymentTest`, would detect `tt` as their
home, as `Pyjo.Home` takes the directory above `lib`. Mojo detects
`t/mojolicious` from `t/mojolicious/lib`, the home of the tests of
`Mojolicious::Lite` too, so a test of them sets `PYJO_HOME` to `t/Pyjoyment`,
where their templates, static files and configuration files are:

```python
os.environ['PYJO_HOME'] = Pyjo.File.path(__file__).to_abs().dirname().to_str()

t = Pyjo.Test.Pyjo.new('PyjoymentTest')
```

The applications of `external/` are scripts with their configuration files,
templates and static files next to them, as their home is the directory of
the script; a test mounts one by its path:

```python
external = Pyjo.File.path(__file__).to_abs().dirname().dirname().dirname().child('tt', 'external', 'myapp.py')
plugin('Mount', {'/x/1': external})
```

The files are read, never written: a test that needs a file of its own, as a
template with a syntax error, makes it in a temporary directory, not in `t/`
or `tt/`. The renderer compiles a template without importing it, so no
`__pycache__` appears in `templates/`; the modules of `lib/` are imported, and
their `__pycache__`, which git ignores, is not run by the harness.
