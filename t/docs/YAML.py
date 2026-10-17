from Pyjo.Test import *

import re


with subtest('Synopsis'):
    from Pyjo.YAML import load, load_all

    config = load("""\
foo: bar
list:
  - one
  - two
""")
    is_deeply_ok(config, {'foo': 'bar', 'list': ['one', 'two']}, 'mapping')

    documents = load_all('--- first\n--- second\n')
    is_deeply_ok(documents, ['first', 'second'], 'documents')

with subtest('Description'):
    # {'foo': ['1', 'true']}
    throws_ok(lambda: load('foo: [1, true]'), re.compile(r'^YAML'), 'raises an exception')
    is_deeply_ok(load('foo:\n  - 1\n  - true\n'), {'foo': ['1', 'true']}, 'strings')

with subtest('load'):
    value = load('foo: bar')

    # {'foo': 'bar'}
    is_deeply_ok(value, {'foo': 'bar'}, 'value')

with subtest('load_all'):
    values = load_all('--- first\n--- second\n')

    # ['first', 'second']
    is_deeply_ok(values, ['first', 'second'], 'values')

done_testing()
