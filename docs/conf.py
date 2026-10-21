# Sphinx configuration: https://www.sphinx-doc.org/en/master/usage/configuration.html

import functools
import inspect
import os
import subprocess
import sys
import tomllib


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# The modules are documented from the source tree, not from an installed package
sys.path.insert(0, ROOT)

with open(os.path.join(ROOT, 'pyproject.toml'), 'rb') as f:
    PROJECT = tomllib.load(f)['project']

project = PROJECT['name']
author = ', '.join(a['name'] for a in PROJECT['authors'])
copyright = f'2014-2026, {author}'
version = release = PROJECT['version']

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.linkcode']

# The commit that the links to the source point to: the one that Read the Docs builds, or the one of the checkout
COMMIT = (
    os.environ.get('READTHEDOCS_GIT_COMMIT_HASH')
    or subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    or 'main'
)


# The link [source] of a class, a function or a method goes to the lines of its source on GitHub; an object without
# source of its own, as a constant or a descriptor that a loop makes, has none
def linkcode_resolve(domain, info):
    if domain != 'py' or not info['module']:
        return None
    obj = sys.modules.get(info['module'])
    for part in info['fullname'].split('.'):
        obj = getattr(obj, part, None)
    if isinstance(obj, property):
        obj = obj.fget
    elif isinstance(obj, functools.cached_property):
        obj = obj.func
    try:
        obj = inspect.unwrap(obj)
        path = inspect.getsourcefile(obj)
        lines, start = inspect.getsourcelines(obj)
    except (TypeError, OSError, ValueError):
        return None
    if not path or not os.path.abspath(path).startswith(ROOT + os.sep):
        return None
    file = os.path.relpath(path, ROOT).replace(os.sep, '/')
    return f'https://github.com/dex4er/Pyjoyment/blob/{COMMIT}/{file}#L{start}-L{start + len(lines) - 1}'


# A function or a method under a second name, as `raise_` of `throw`, is an alias
# that the documentation of the first one names, so it is not documented twice:
# its own name is public and finds the same object. So is a class under a second
# name, as `object` and `Path` of `Pyjo_Path`, which each module has; as targets
# named `object`, those aliases would also make the `object` type in annotations
# ambiguous.
def skip_alias(app, what, name, obj, skip, options):
    canonical = getattr(obj, '__name__', name)
    if isinstance(obj, type):
        return True if canonical != name else None
    if canonical == name or canonical.startswith('_'):
        return None
    found = sys.modules.get(getattr(obj, '__module__', None) or '')
    for part in getattr(obj, '__qualname__', '').split('.'):
        found = getattr(found, part, None)
    return True if found is obj else None


# The attribute `__weakref__` that Python makes for a class without `__slots__`
# is not an API of the class, but `:special-members:` without a list documents it
def skip_weakref(app, what, name, obj, skip, options):
    return True if name == '__weakref__' else None


def setup(app):
    app.connect('autodoc-skip-member', skip_alias)
    app.connect('autodoc-skip-member', skip_weakref)


# The table of contents lists the pages, not the classes and functions that
# autodoc documents on them.
toc_object_entries = False

exclude_patterns = ['_build']

html_theme = 'alabaster'
html_theme_options = {
    'github_user': 'dex4er',
    'github_repo': 'Pyjoyment',
    'show_powered_by': False,
    # The sans-serif font of the system, where Alabaster has Georgia
    'font_family': "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
    'head_font_family': "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
}
