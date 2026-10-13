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

exclude_patterns = ['_build']

html_theme = 'alabaster'
html_theme_options = {
    'github_user': 'dex4er',
    'github_repo': 'Pyjoyment',
    'show_powered_by': False,
}
