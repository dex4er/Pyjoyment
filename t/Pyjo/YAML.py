from Pyjo.Test import *
from Pyjo.YAML import load, load_all

import re


# Not in Mojolicious: Pyjo.YAML, the YAML that Mojolicious::Plugin::NotYAMLConfig reads with CPAN::Meta::YAML; the
# results are those of CPAN::Meta::YAML, except for the aliases and the flow collections, which it reads as strings

with subtest('Mappings'):
    is_deeply_ok(load('foo: bar\n'), {'foo': 'bar'}, 'one key')
    is_deeply_ok(load('foo: bar\nbaz: yada\n'), {'foo': 'bar', 'baz': 'yada'}, 'two keys')
    is_deeply_ok(load('a:\n  b:\n    c: d\n  e: f\ng: h\n'), {'a': {'b': {'c': 'd'}, 'e': 'f'}, 'g': 'h'}, 'nested')
    is_deeply_ok(load('\'quoted key\': v\n"dq key": w\n'), {'quoted key': 'v', 'dq key': 'w'}, 'quoted keys')
    is_deeply_ok(load('key with spaces: value\n'), {'key with spaces': 'value'}, 'key with spaces')
    is_deeply_ok(load('url: http://example.com:80/path\n'), {'url': 'http://example.com:80/path'}, 'colon in value')
    is_deeply_ok(load('time: 12:30\n'), {'time': '12:30'}, 'colon without space')
    is_deeply_ok(load('foo:\n  bar:\n  baz: x\n'), {'foo': {'bar': None, 'baz': 'x'}}, 'null in nested')

with subtest('Sequences'):
    is_deeply_ok(load('- one\n- two\n'), ['one', 'two'], 'root sequence')
    is_deeply_ok(load('foo:\n  - one\n  - two\nbar: x\n'), {'foo': ['one', 'two'], 'bar': 'x'}, 'indented')
    is_deeply_ok(load('foo:\n- one\n- two\nbar: x\n'), {'foo': ['one', 'two'], 'bar': 'x'}, 'not indented')
    is_deeply_ok(load('- a: 1\n  b: 2\n- c: 3\n'), [{'a': '1', 'b': '2'}, {'c': '3'}], 'mappings in items')
    is_deeply_ok(load('-\n  - x\n  - y\n- z\n'), [['x', 'y'], 'z'], 'nested sequence')
    is_deeply_ok(load('list:\n  -\n    a: 1\n  -\n    b: 2\n'), {'list': [{'a': '1'}, {'b': '2'}]}, 'items below')
    is_deeply_ok(load('- \n'), [None], 'null item')

with subtest('Scalars'):
    is_deeply_ok(load('foo: ~\nbar:\n'), {'foo': None, 'bar': None}, 'null')
    is_deeply_ok(load("foo: 'it''s'\n"), {'foo': "it's"}, 'single quoted')
    is_deeply_ok(load('foo: "a\\nb\\tc\\x41\\\\d\\"e"\n'), {'foo': 'a\nb\tcA\\d"e'}, 'double quoted')
    is_deeply_ok(load('foo: "\\N\\e\\0"\n'), {'foo': '\x85\x1b\x00'}, 'escapes')
    is_deeply_ok(load("foo: '\\n'\n"), {'foo': '\\n'}, 'no escapes in single quotes')
    is_deeply_ok(load('foo: {}\nbar: []\n'), {'foo': {}, 'bar': []}, 'empty collections')
    is_deeply_ok(load("empty: ''\n"), {'empty': ''}, 'empty string')
    is_deeply_ok(load('foo: 1\nbar: true\nbaz: 1.5\n'), {'foo': '1', 'bar': 'true', 'baz': '1.5'}, 'strings')
    is_deeply_ok(load('foo:   spaced   \n'), {'foo': 'spaced'}, 'trimmed')
    is_deeply_ok(load('utf: утф\n'), {'utf': 'утф'}, 'Unicode')

with subtest('Block scalars'):
    is_deeply_ok(
        load('foo: |\n  line one\n  line two\nbar: x\n'), {'foo': 'line one\nline two\n', 'bar': 'x'}, 'literal'
    )
    is_deeply_ok(load('foo: |-\n  line one\n  line two\n'), {'foo': 'line one\nline two'}, 'literal chomped')
    is_deeply_ok(load('foo: >\n  folded\n  text\n'), {'foo': 'folded text\n'}, 'folded')
    is_deeply_ok(load('foo: >-\n  folded\n  text\n'), {'foo': 'folded text'}, 'folded chomped')

with subtest('Comments and lines'):
    is_deeply_ok(load('foo: bar # comment\n'), {'foo': 'bar'}, 'trailing comment')
    is_deeply_ok(load('# comment\nfoo: bar\n\n# another\n'), {'foo': 'bar'}, 'comment lines')
    is_deeply_ok(load('\ufefffoo: bar\n'), {'foo': 'bar'}, 'byte order mark')
    is_deeply_ok(load('foo: bar\r\nbaz: yada\r\n'), {'foo': 'bar', 'baz': 'yada'}, 'CRLF')

with subtest('Documents'):
    is_deeply_ok(load('---\nfoo: bar\n'), {'foo': 'bar'}, 'start')
    is_deeply_ok(load('---\nfoo: bar\n...\n'), {'foo': 'bar'}, 'end')
    is_deeply_ok(load('%YAML 1.1\n---\nfoo: bar\n'), {'foo': 'bar'}, 'directive')
    is_ok(load('--- scalar\n'), 'scalar', 'scalar document')
    is_deeply_ok(load_all('--- one\n--- two\n'), ['one', 'two'], 'all documents')
    is_ok(load('--- one\n--- two\n'), 'two', 'last document')
    is_deeply_ok(load_all('---\n- a\n---\n- b\n'), [['a'], ['b']], 'sequences')
    is_deeply_ok(load_all(''), [], 'no document')
    is_ok(load(''), None, 'empty')
    is_ok(load('   \n'), None, 'blank')

with subtest('Errors'):
    throws_ok(lambda: load('a: b\n  c: d\n'), re.compile(r"^YAML found bad indenting in line '  c: d'"), 'indent')
    throws_ok(lambda: load('? complex\n'), re.compile(r'^YAML does not support a feature'), 'complex key')
    throws_ok(lambda: load('foo: &anchor bar\n'), re.compile(r'^YAML does not support a feature'), 'anchor')
    throws_ok(lambda: load('foo: !tag bar\n'), re.compile(r'^YAML does not support a feature'), 'tag')
    throws_ok(lambda: load('foo: - bar\n'), re.compile(r'^YAML found illegal characters'), 'dash')
    throws_ok(lambda: load('foo: @bar\n'), re.compile(r'^YAML found illegal characters'), 'reserved')
    throws_ok(lambda: load('foo: a: b\n'), re.compile(r'^YAML found illegal characters'), 'colon')
    throws_ok(lambda: load('foo: |\nbar: x\n'), re.compile(r'^YAML found bad indenting'), 'block scalar')
    throws_ok(lambda: load('--- foo\nbar: baz\n'), re.compile(r'^YAML failed to classify the line'), 'second document')
    throws_ok(lambda: load('- a\n  - b\n'), re.compile(r'^YAML found bad indenting'), 'nested without item')
    throws_ok(lambda: load('foo: {a: 1}\n'), re.compile(r'^YAML found illegal characters'), 'flow mapping')

    # Not in CPAN::Meta::YAML: an alias and a flow sequence are errors, not strings
    throws_ok(lambda: load('foo: *alias\n'), re.compile(r'^YAML does not support a feature'), 'alias')
    throws_ok(lambda: load('foo: [1, 2]\n'), re.compile(r'^YAML found illegal characters'), 'flow sequence')

done_testing()
