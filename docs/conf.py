# Sphinx configuration: https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
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

extensions = ['sphinx.ext.autodoc']

# Each module ends with `object = Pyjo_X`, an alias that only repeats the class;
# as targets named `object`, the aliases make the `object` type in annotations
# ambiguous.
autodoc_default_options = {'exclude-members': 'object'}


# A function or a method under a second name, as `raise_` of `throw`, is an alias
# that the documentation of the first one names, so it is not documented twice:
# its own name is public and finds the same object.
def skip_alias(app, what, name, obj, skip, options):
    canonical = getattr(obj, '__name__', name)
    if canonical == name or canonical.startswith('_') or isinstance(obj, type):
        return None
    found = sys.modules.get(getattr(obj, '__module__', None) or '')
    for part in getattr(obj, '__qualname__', '').split('.'):
        found = getattr(found, part, None)
    return True if found is obj else None


def setup(app):
    app.connect('autodoc-skip-member', skip_alias)


# The table of contents lists the pages, not the classes and functions that
# autodoc documents on them.
toc_object_entries = False

exclude_patterns = ['_build']

html_theme = 'alabaster'
html_theme_options = {
    'github_user': 'dex4er',
    'github_repo': 'Pyjoyment',
    'show_powered_by': False,
}
