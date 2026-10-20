from Pyjo.File import curfile
from Pyjo.Test import *

import importlib
import re


# The class hierarchy of the section API of docs/guides/index.rst, a nested list with the modules of docs/api, each
# under the module of the base class of its class, which the test finds as the documentation does
DOCS = curfile().dirname().dirname().sibling('docs')


def listed():
    # The modules of the list, with the module of the item that the list is nested in
    section = re.search(r'\nAPI\n---\n(.*?)\nMore\n', DOCS.child('guides', 'index.rst').slurp('UTF-8'), re.S).group(1)
    parents, stack = {}, []
    for indent, name in re.findall(r'^( *)- :mod:`([^`]+)`$', section, re.M):
        depth = len(indent) // 2
        del stack[depth:]
        parents[name] = stack[-1] if stack else None
        stack.append(name)
    return parents


def documented():
    # The modules of the API reference, with the module of the base class of the class that a module names object
    names = [
        re.search(r'automodule:: (\S+)', path.slurp('UTF-8')).group(1)
        for path in DOCS.child('api').list()
        if path.basename() != 'index.rst'
    ]
    classes = {}
    for name in names:
        try:
            module = importlib.import_module(name)
        except ModuleNotFoundError as e:
            # A module of a library that is not installed, as Pyjo.Test.pytest_plugin of pytest, names no class
            if e.name is not None and e.name.split('.')[0] in ('Pyjo', 'Pyjoyment'):
                raise
            continue
        cls = getattr(module, 'object', None)
        if isinstance(cls, type) and cls.__module__ == name:
            classes[cls] = name
    parents = dict.fromkeys(names)
    for cls, name in classes.items():
        parents[name] = next((classes[base] for base in cls.__bases__ if base in classes), None)
    return parents


with subtest('API'):
    parents, modules = listed(), documented()
    is_deeply_ok(sorted(parents), sorted(modules), 'all the modules of the API reference')
    for name, parent in sorted(modules.items()):
        is_ok(parents.get(name), parent, f'{name} under {parent}')

done_testing()
