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
    # {'foo': [1, True, 'yes', '2']}
    is_deeply_ok(load("foo:\n  - 1\n  - true\n  - yes\n  - '2'\n"), {'foo': [1, True, 'yes', '2']}, 'types')
    throws_ok(lambda: load('foo: !tag bar'), re.compile(r'^YAML does not support a feature'), 'other tag')

with subtest('Tags'):
    import datetime

    # {'port': '8080', 'key': b'hello', 'day': datetime.date(2001, 12, 14)}
    is_deeply_ok(
        load('port: !!str 8080\nkey: !!binary aGVsbG8=\nday: !!timestamp 2001-12-14\n'),
        {'port': '8080', 'key': b'hello', 'day': datetime.date(2001, 12, 14)},
        'standard tags',
    )

with subtest('Anchors'):
    # {'base': {'a': 1, 'b': 1}, 'copy': {'a': 1, 'b': 2}}
    is_deeply_ok(
        load('base: &base\n  a: 1\n  b: 1\ncopy:\n  <<: *base\n  b: 2\n'),
        {'base': {'a': 1, 'b': 1}, 'copy': {'a': 1, 'b': 2}},
        'anchor, alias and merge key',
    )

with subtest('load'):
    value = load('foo: bar')

    # {'foo': 'bar'}
    is_deeply_ok(value, {'foo': 'bar'}, 'value')

with subtest('load_all'):
    values = load_all('--- first\n--- second\n')

    # ['first', 'second']
    is_deeply_ok(values, ['first', 'second'], 'values')

done_testing()
