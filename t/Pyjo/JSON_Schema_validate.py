import Pyjo.Collection
import Pyjo.Exception
import Pyjo.JSON
import Pyjo.JSON.Schema

from Pyjo.JSON.Schema import Error, Result, Schema, z
from Pyjo.Test import *

import dataclasses
import datetime
import enum
import re
import uuid

from typing import Annotated, Literal, NotRequired, TypedDict


# Not in Mojolicious: the validation of Pyjo.JSON.Schema, with the cases of the keywords


def errors(schema, value, formats=False):
    return [str(error) for error in Schema.new(schema).validate(value, formats).errors]


class Unit(enum.Enum):
    CELSIUS = 'celsius'
    FAHRENHEIT = 'fahrenheit'


class Point(TypedDict):
    x: int
    y: int


class Tagged(TypedDict):
    name: str
    tag: NotRequired[Annotated[str, {'minLength': 1}]]


class Node(TypedDict):
    name: str
    children: list['Node']


@dataclasses.dataclass
class Location:
    city: str
    days: int = 3


with subtest('Result'):
    result = Schema.new({'type': 'integer'}).validate(1)
    isa_ok(result, Result, 'result')
    ok(result, 'valid')
    ok(result.is_valid, 'is valid')
    isa_ok(result.errors, Pyjo.Collection.object, 'collection')
    is_ok(len(result.errors), 0, 'no errors')
    is_ok(str(result), '', 'no lines')
    is_deeply_ok(result.__json__(), {'valid': True, 'errors': []}, 'JSON')
    result = Schema.new({'type': 'integer'}).validate('1')
    ok(not result, 'invalid')
    ok(not result.is_valid, 'is not valid')
    is_ok(str(result), '/: Expected integer - got string.', 'line')
    like_ok(repr(result), r'^<Pyjo\.JSON\.Schema\.Result is_valid=False>$', 'repr')
    error = result.errors[0]
    isa_ok(error, Error, 'error')
    is_ok(error.path, '', 'path')
    is_ok(error.keyword_path, '/type', 'keyword path')
    is_ok(error.message, 'Expected integer - got string.', 'message')
    is_deeply_ok(
        error.__json__(), {'path': '', 'keyword_path': '/type', 'message': 'Expected integer - got string.'}, 'JSON'
    )
    is_ok(Pyjo.JSON.to_json(result), Pyjo.JSON.to_json({'valid': False, 'errors': [error.__json__()]}), 'encoded')
    is_ok(str(Error('/a/0', '/items/type', 'Not allowed.')), '/a/0: Not allowed.', 'string of an error')
    is_ok(str(Result([Error('/a', '', 'A.'), Error('/b', '', 'B.')])), '/a: A.\n/b: B.', 'lines of a result')

with subtest('Boolean schemas'):
    is_deeply_ok(errors(True, {'a': [1]}), [], 'true')
    is_deeply_ok(errors(False, None), ['/: Not allowed.'], 'false')
    is_deeply_ok(errors({}, 'anything'), [], 'empty')
    is_deeply_ok(errors({'properties': {'a': False}}, {'a': 1}), ['/a: Not allowed.'], 'false property')

with subtest('Types'):
    is_deeply_ok(errors({'type': 'integer'}, 1), [], 'integer')
    is_deeply_ok(errors({'type': 'integer'}, 1.0), [], 'integral float is an integer')
    is_deeply_ok(errors({'type': 'integer'}, 1.5), ['/: Expected integer - got number.'], 'float')
    is_deeply_ok(errors({'type': 'integer'}, True), ['/: Expected integer - got boolean.'], 'bool is not an integer')
    is_deeply_ok(errors({'type': 'number'}, 1), [], 'integer is a number')
    is_deeply_ok(errors({'type': 'number'}, False), ['/: Expected number - got boolean.'], 'bool is not a number')
    is_deeply_ok(errors({'type': 'boolean'}, 0), ['/: Expected boolean - got integer.'], 'integer is not a bool')
    is_deeply_ok(errors({'type': 'null'}, None), [], 'null')
    is_deeply_ok(errors({'type': 'string'}, None), ['/: Expected string - got null.'], 'null is not a string')
    is_deeply_ok(errors({'type': 'array'}, (1, 2)), [], 'tuple is an array')
    is_deeply_ok(errors({'type': 'object'}, [1]), ['/: Expected object - got array.'], 'array is not an object')
    is_deeply_ok(errors({'type': ['string', 'null']}, None), [], 'list of types')
    is_deeply_ok(errors({'type': ['string', 'null']}, 1), ['/: Expected string or null - got integer.'], 'neither')

with subtest('Values of Python'):
    is_deeply_ok(errors({}, b'bytes'), ['/: Not a JSON value: bytes.'], 'bytes')
    is_deeply_ok(errors({}, {'a': {1, 2}}), ['/a: Not a JSON value: set.'], 'set')
    is_deeply_ok(errors({}, [float('nan')]), ['/0: Not a JSON value: nan.'], 'NaN')
    is_deeply_ok(errors({}, float('inf')), ['/: Not a JSON value: inf.'], 'infinity')
    is_deeply_ok(errors({}, {1: 'one'}), ['/: Not a JSON value: the name 1.'], 'name of a property')
    is_deeply_ok(errors(True, datetime.date(2026, 10, 23)), ['/: Not a JSON value: date.'], 'any schema')
    is_deeply_ok(errors({}, {'a/b': {'c~d': uuid.UUID(int=0)}}), ['/a~1b/c~0d: Not a JSON value: UUID.'], 'pointer')

with subtest('enum and const'):
    is_deeply_ok(errors({'enum': ['a', 1]}, 'a'), [], 'enum')
    is_deeply_ok(errors({'enum': ['a', 1]}, 1.0), [], 'number of enum')
    is_deeply_ok(errors({'enum': ['a', 1]}, True), ['/: Not in enum: "a", 1.'], 'bool is not 1')
    is_deeply_ok(errors({'enum': [False]}, 0), ['/: Not in enum: false.'], '0 is not false')
    is_deeply_ok(errors({'const': {'a': [1, 2], 'b': None}}, {'b': None, 'a': [1.0, 2]}), [], 'const of an object')
    is_deeply_ok(errors({'const': [1, 2]}, [2, 1]), ['/: Not the const: [1,2].'], 'order of an array')
    is_deeply_ok(errors({'const': None}, False), ['/: Not the const: null.'], 'false is not null')

with subtest('Numbers'):
    is_deeply_ok(errors({'minimum': 1}, 0), ['/: Less than the minimum 1.'], 'minimum')
    is_deeply_ok(errors({'minimum': 1}, 1), [], 'minimum itself')
    is_deeply_ok(errors({'maximum': 1.5}, 2), ['/: Greater than the maximum 1.5.'], 'maximum')
    is_deeply_ok(errors({'exclusiveMinimum': 1}, 1), ['/: Not greater than the exclusive minimum 1.'], 'exclusive')
    is_deeply_ok(errors({'exclusiveMaximum': 1}, 1.0), ['/: Not less than the exclusive maximum 1.'], 'exclusive')
    is_deeply_ok(errors({'multipleOf': 0.0001}, 0.0075), [], 'multiple of a decimal')
    is_deeply_ok(errors({'multipleOf': 2}, 7), ['/: Not a multiple of 2.'], 'not a multiple')
    is_deeply_ok(errors({'multipleOf': 0.5}, 1e308), [], 'multiple of a large number')
    is_deeply_ok(errors({'minimum': 1}, 'a'), [], 'string is not a number')

with subtest('Strings'):
    is_deeply_ok(errors({'minLength': 2}, 'a'), ['/: Shorter than 2 characters.'], 'minLength')
    is_deeply_ok(errors({'minLength': 2}, '💩💩'), [], 'code points')
    is_deeply_ok(errors({'maxLength': 1}, '💩💩'), ['/: Longer than 1 characters.'], 'maxLength')
    is_deeply_ok(errors({'pattern': '^a+$'}, 'aa'), [], 'pattern')
    is_deeply_ok(errors({'pattern': 'b'}, 'abc'), [], 'pattern anywhere')
    is_deeply_ok(errors({'pattern': '^a+$'}, 'ab'), ['/: Does not match the pattern ^a+$.'], 'no match')
    is_deeply_ok(errors({'pattern': '^a'}, 1), [], 'number is not a string')

with subtest('Patterns of ECMAScript'):
    is_deeply_ok(errors({'pattern': r'^\d+$'}, '123'), [], 'digits')
    ok(errors({'pattern': r'^\d+$'}, '١٢٣'), 'digits are ASCII')
    ok(errors({'pattern': r'^\w+$'}, 'zażółć'), 'word characters are ASCII')
    ok(errors({'pattern': r'^\W$'}, 'a'), 'not a word character')
    is_deeply_ok(errors({'pattern': r'^[\W]$'}, 'ż'), [], 'not a word character in a class')
    is_deeply_ok(errors({'pattern': r'^\s$'}, ' '), [], 'white space of Unicode')
    ok(errors({'pattern': r'^\s$'}, '\x1c'), 'not the white space of Python')
    is_deeply_ok(errors({'pattern': r'^a\b'}, 'a ż'), [], 'boundary of a word')
    ok(errors({'pattern': '^abc$'}, 'abc\n'), 'end of the string, not of the line')
    ok(errors({'pattern': '^.$'}, '\r'), 'dot matches no line terminator')
    is_deeply_ok(errors({'pattern': r'^\p{L}+$'}, 'Zażółć'), [], 'property of Unicode')
    ok(errors({'pattern': r'^\p{Letter}+$'}, 'a1'), 'property of Unicode by its name')
    is_deeply_ok(errors({'pattern': r'^\P{Nd}+$'}, 'abc'), [], 'not a property of Unicode')
    is_deeply_ok(errors({'pattern': r'^[\p{Lu}\d]+$'}, 'A1'), [], 'property in a class')
    is_deeply_ok(errors({'pattern': r'^(?<a>x)\k<a>$'}, 'xx'), [], 'named group')
    is_deeply_ok(errors({'pattern': r'^\cA$'}, '\x01'), [], 'control')
    is_deeply_ok(errors({'pattern': r'^\u{1F4A9}$'}, '💩'), [], 'code point')
    is_deeply_ok(errors({'pattern': '^a[]$'}, 'a'), ['/: Does not match the pattern ^a[]$.'], 'empty class')
    is_deeply_ok(errors({'pattern': '^[^]$'}, '\n'), [], 'any character')
    is_deeply_ok(errors({'pattern': '^[a[&]+$'}, 'a[&'), [], 'characters of the sets of Python')
    is_deeply_ok(errors({'pattern': '^(?i:a)$'}, 'A'), [], 'modifier')
    for pattern, what in (
        ('(?P<a>x)', 'a group of Python'),
        ('(?i)a', 'a group of Python'),
        ('(?#a)', 'a group of Python'),
        (r'\Aa', r'\\A of Python'),
        (r'\p{Script=Greek}', 'the property Script=Greek'),
        ('(?<=a+)b', 'look-behind requires fixed-width pattern'),
    ):
        throws_ok(
            lambda pattern=pattern: Schema.new({'pattern': pattern}).validate('a'),
            re.compile(rf'^JSON Schema does not support the pattern .+: {what}'),
            pattern,
        )

with subtest('Formats'):
    is_deeply_ok(errors({'format': 'date'}, 'today'), [], 'annotation')
    is_deeply_ok(errors({'format': 'date'}, 'today', True), ['/: Does not match the format date.'], 'assertion')
    is_deeply_ok(errors({'format': 'date'}, 1, True), [], 'number is not a string')
    is_deeply_ok(errors({'format': 'unknown'}, 'a', True), [], 'unknown format')
    for name, good, bad in (
        ('date', '2026-02-28', '2026-02-29'),
        ('date-time', '2026-10-23T12:00:00.5+02:00', '2026-10-23 12:00:00'),
        ('date-time', '1998-12-31T23:59:60Z', '1998-12-31T23:58:60Z'),
        ('time', '23:59:60Z', '12:00:00'),
        ('duration', 'P1Y2M3DT4H5M6S', 'P1Y2D'),
        ('email', 'joe.bloggs@example.com', 'joe..bloggs@example.com'),
        ('email', '"joe bloggs"@[IPv6:::1]', 'joe@example.com.'),
        ('hostname', 'www.example.com', '-example.com'),
        ('hostname', 'xn--9n2bp8q.xn--9t4b11yi5a', 'xn--X'),
        ('ipv4', '192.168.0.1', '192.168.0.01'),
        ('ipv6', '::ffff:192.168.0.1', '::1%eth0'),
        ('json-pointer', '/a~1b/0', 'a'),
        ('regex', '^[a-z]+$', '(?P<a>x)'),
        ('relative-json-pointer', '1/a', '-1/a'),
        ('uri', 'https://user@[::1]:443/a?b#c', '/a'),
        ('uri-reference', '../a?b#c', 'a b'),
        ('uri', 'http://[V1.a]/', 'http://[v1]/'),
        ('uuid', '2eb8aa08-aa98-11ea-b4aa-73b441d16380', '2eb8aa08aa9811eab4aa73b441d16380'),
    ):
        is_deeply_ok(errors({'format': name}, good, True), [], f'{name} {good}')
        ok(errors({'format': name}, bad, True), f'not {name} {bad}')

with subtest('Arrays'):
    schema = {'items': {'type': 'integer'}}
    is_deeply_ok(errors(schema, [1, 2]), [], 'items')
    is_deeply_ok(
        errors(schema, [1, 'a', None]),
        ['/1: Expected integer - got string.', '/2: Expected integer - got null.'],
        'items',
    )
    schema = {'prefixItems': [{'type': 'string'}, {'type': 'integer'}], 'items': False}
    is_deeply_ok(errors(schema, ['a']), [], 'prefixItems')
    is_deeply_ok(
        errors(schema, ['a', 'b', 'c']), ['/1: Expected integer - got string.', '/2: Not allowed.'], 'prefixItems'
    )
    is_deeply_ok(errors({'minItems': 2}, [1]), ['/: Fewer than 2 items.'], 'minItems')
    is_deeply_ok(errors({'maxItems': 1}, [1, 2]), ['/: More than 1 items.'], 'maxItems')
    is_deeply_ok(
        errors({'uniqueItems': True}, [1, True, {'a': 1}, {'a': 1.0}]), ['/: Items 2 and 3 are equal.'], 'unique'
    )
    is_deeply_ok(errors({'uniqueItems': False}, [1, 1]), [], 'not unique')
    schema = {'contains': {'type': 'integer'}}
    is_deeply_ok(errors(schema, ['a', 1]), [], 'contains')
    is_deeply_ok(errors(schema, ['a']), ['/: No item matches the schema of contains.'], 'contains')
    is_deeply_ok(errors(schema, []), ['/: No item matches the schema of contains.'], 'empty')
    schema = {'contains': {'type': 'integer'}, 'minContains': 2, 'maxContains': 3}
    is_deeply_ok(errors(schema, [1, 2]), [], 'minContains')
    is_deeply_ok(errors(schema, [1, 'a']), ['/: Fewer than 2 items match the schema of contains.'], 'minContains')
    is_deeply_ok(errors(schema, [1, 2, 3, 4]), ['/: More than 3 items match the schema of contains.'], 'maxContains')
    is_ok(Schema.new(schema).validate([1]).errors[0].keyword_path, '/minContains', 'keyword of minContains')
    is_deeply_ok(errors({'contains': False, 'minContains': 0}, [1]), [], 'minContains 0')
    is_deeply_ok(errors({'items': {'type': 'string'}}, 'a'), [], 'string is not an array')

with subtest('Objects'):
    schema = {'properties': {'a': {'type': 'integer'}, 'b/c': {'type': 'string'}}, 'required': ['a', 'd']}
    is_deeply_ok(errors(schema, {'a': 1, 'd': 0}), [], 'properties')
    result = Schema.new(schema).validate({'a': 'x', 'b/c': 1})
    is_deeply_ok(
        [error.__json__() for error in result.errors],
        [
            {'path': '/a', 'keyword_path': '/properties/a/type', 'message': 'Expected integer - got string.'},
            {'path': '/b~1c', 'keyword_path': '/properties/b~1c/type', 'message': 'Expected string - got integer.'},
            {'path': '/d', 'keyword_path': '/required', 'message': 'Missing property.'},
        ],
        'errors of the properties',
    )
    schema = {'properties': {'a': {}}, 'patternProperties': {'^x-': {'type': 'string'}}, 'additionalProperties': False}
    is_deeply_ok(errors(schema, {'a': 1, 'x-b': 'c'}), [], 'additionalProperties')
    is_deeply_ok(
        errors(schema, {'x-b': 1, 'c': 1}),
        ['/x-b: Expected string - got integer.', '/c: Property not allowed.'],
        'not allowed',
    )
    is_deeply_ok(
        errors({'additionalProperties': {'type': 'integer'}}, {'a': 'b'}),
        ['/a: Expected integer - got string.'],
        'schema',
    )
    is_deeply_ok(
        errors({'propertyNames': {'maxLength': 1}}, {'a': 1, 'bc': 2}),
        ['/bc: Longer than 1 characters.'],
        'propertyNames',
    )
    is_deeply_ok(errors({'minProperties': 1}, {}), ['/: Fewer than 1 properties.'], 'minProperties')
    is_deeply_ok(errors({'maxProperties': 1}, {'a': 1, 'b': 2}), ['/: More than 1 properties.'], 'maxProperties')
    schema = {'dependentRequired': {'card': ['address']}}
    is_deeply_ok(errors(schema, {'address': 'x'}), [], 'dependentRequired')
    is_deeply_ok(
        errors(schema, {'card': 1}), ['/address: Missing property, which "card" requires.'], 'dependentRequired'
    )
    schema = {'dependentSchemas': {'card': {'required': ['address']}}}
    is_deeply_ok(errors(schema, {'card': 1}), ['/address: Missing property.'], 'dependentSchemas')
    is_deeply_ok(errors({'required': ['a']}, [1]), [], 'array is not an object')

with subtest('Combinations'):
    schema = {'allOf': [{'type': 'integer'}, {'minimum': 2}]}
    is_deeply_ok(errors(schema, 2), [], 'allOf')
    is_deeply_ok(errors(schema, 1), ['/: Less than the minimum 2.'], 'allOf')
    schema = {'anyOf': [{'type': 'string', 'minLength': 2}, {'type': 'integer'}, {'type': 'null'}]}
    is_deeply_ok(errors(schema, None), [], 'anyOf')
    is_deeply_ok(errors(schema, 1.5), ['/: Expected string or integer or null - got number.'], 'types of anyOf')
    is_deeply_ok(errors(schema, 'a'), ['/: Shorter than 2 characters.'], 'schema of the type of the value')
    schema = {'anyOf': [{'const': 1}, {'const': 2}]}
    is_deeply_ok(errors(schema, 3), ['/: Not the const: 1.', '/: Not the const: 2.'], 'errors of all the schemas')
    schema = {'oneOf': [{'type': 'integer'}, {'minimum': 2}]}
    is_deeply_ok(errors(schema, 1), [], 'oneOf')
    is_deeply_ok(errors(schema, 3), ['/: Matches more than one schema of oneOf: 0, 1.'], 'more than one')
    is_deeply_ok(errors(schema, 1.5), ['/: Less than the minimum 2.'], 'none')
    is_deeply_ok(errors({'not': {'type': 'string'}}, 'a'), ['/: Matches the schema of not.'], 'not')
    is_deeply_ok(errors({'not': {'type': 'string'}}, 1), [], 'not')
    schema = {'if': {'type': 'integer'}, 'then': {'minimum': 1}, 'else': {'type': 'string'}}
    is_deeply_ok(errors(schema, 1), [], 'then')
    is_deeply_ok(errors(schema, 0), ['/: Less than the minimum 1.'], 'then')
    is_deeply_ok(errors(schema, None), ['/: Expected string - got null.'], 'else')
    is_ok(Schema.new(schema).validate(None).errors[0].keyword_path, '/else/type', 'keyword of else')
    is_deeply_ok(errors({'then': False, 'else': False}, 1), [], 'then and else without if')
    schema = {'type': 'object', 'properties': {'a': {'anyOf': [{'$ref': '#/$defs/b'}, {'type': 'null'}]}}}
    schema['$defs'] = {'b': {'type': 'object', 'required': ['c']}}
    is_deeply_ok(errors(schema, {'a': {}}), ['/a/c: Missing property.'], 'nullable reference')

with subtest('References'):
    schema = {'$defs': {'positive': {'type': 'integer', 'minimum': 1}}, 'items': {'$ref': '#/$defs/positive'}}
    is_deeply_ok(errors(schema, [1, 2]), [], '$defs')
    result = Schema.new(schema).validate([1, 0])
    is_deeply_ok(
        [error.__json__() for error in result.errors],
        [{'path': '/1', 'keyword_path': '/items/$ref/minimum', 'message': 'Less than the minimum 1.'}],
        'keyword path through $ref',
    )
    schema = {'$defs': {'a': {'$anchor': 'name', 'type': 'string'}}, '$ref': '#name'}
    is_deeply_ok(errors(schema, 1), ['/: Expected string - got integer.'], '$anchor')
    schema = {
        'type': 'object',
        'properties': {'name': {'type': 'string'}, 'children': {'type': 'array', 'items': {'$ref': '#'}}},
        'required': ['name'],
    }
    is_deeply_ok(errors(schema, {'name': 'a', 'children': [{'name': 'b', 'children': []}]}), [], 'recursion')
    is_deeply_ok(
        errors(schema, {'name': 'a', 'children': [{'children': [{}]}]}),
        ['/children/0/children/0/name: Missing property.', '/children/0/name: Missing property.'],
        'recursion',
    )
    schema = {
        '$id': 'https://example.com/root.json',
        '$defs': {'a': {'$id': 'a.json', '$defs': {'b': {'$anchor': 'b', 'type': 'integer'}}}},
        '$ref': 'a.json#b',
    }
    is_deeply_ok(errors(schema, 'x'), ['/: Expected integer - got string.'], 'embedded $id')
    is_deeply_ok(
        errors({'$defs': {'a%b': {'type': 'null'}}, '$ref': '#/$defs/a%25b'}, 1),
        ['/: Expected null - got integer.'],
        'percent-encoded',
    )
    throws_ok(
        lambda: Schema.new({'$ref': '#/$defs/missing'}).validate(1),
        re.compile(r'^JSON Schema has no schema of the \$ref #/\$defs/missing in /\$ref'),
        'missing',
    )
    throws_ok(
        lambda: Schema.new(
            {'$defs': {'a': {'$ref': '#/$defs/b'}, 'b': {'$ref': '#/$defs/a'}}, '$ref': '#/$defs/a'}
        ).validate(1),
        re.compile(r'^JSON Schema refers to itself in /\$ref/\$ref/\$ref without a value of its own'),
        'loop',
    )

with subtest('Registry'):
    address = {
        '$id': 'https://example.com/address',
        'type': 'object',
        'required': ['city'],
        '$defs': {'zip': {'$anchor': 'zip', 'pattern': '^[0-9]{2}-[0-9]{3}$'}},
    }
    schema = Schema.new(
        {
            'properties': {
                'address': {'$ref': 'https://example.com/address'},
                'zip': {'$ref': 'https://example.com/address#zip'},
            }
        }
    )
    is_ok(schema.add_schema(address), schema, 'chain')
    is_deeply_ok(
        [str(e) for e in schema.validate({'address': {}, 'zip': '00950'}).errors],
        ['/address/city: Missing property.', '/zip: Does not match the pattern ^[0-9]{2}-[0-9]{3}$.'],
        'by $id',
    )
    schema = Schema.new({'$id': 'https://example.com/person', 'properties': {'name': {'$ref': 'name'}}})
    schema.add_schema(z.string().min(1), 'https://example.com/name')
    is_deeply_ok(
        [str(e) for e in schema.validate({'name': ''}).errors],
        ['/name: Shorter than 1 characters.'],
        'by URI, relative',
    )
    throws_ok(
        lambda: schema.add_schema({'type': 'string'}),
        re.compile(r'^JSON Schema has no \$id of the schema to add'),
        'no $id',
    )
    copy = schema.describe('A person')
    is_deeply_ok(
        [str(e) for e in copy.validate({'name': 1}).errors],
        ['/name: Expected string - got integer.'],
        'registry of a copy',
    )

with subtest('Keywords of 2020-12 that are not supported'):
    for keyword, schema in (
        ('$dynamicRef', {'$dynamicRef': '#meta'}),
        ('unevaluatedProperties', {'properties': {'a': {'unevaluatedProperties': False}}}),
        ('unevaluatedItems', {'$defs': {'a': {'unevaluatedItems': False}}}),
    ):
        throws_ok(
            lambda schema=schema: Schema.new(schema).validate(1),
            re.compile(rf'^JSON Schema does not support {keyword.replace("$", r"\$")} in /'),
            keyword,
        )
    throws_ok(
        lambda: Schema.new({'$schema': 'http://json-schema.org/draft-07/schema#'}).validate(1),
        re.compile(r'^JSON Schema does not support the dialect http://json-schema.org/draft-07/schema#'),
        'dialect',
    )
    is_deeply_ok(errors({'$schema': Pyjo.JSON.Schema.DIALECT, 'type': 'null'}, None), [], 'dialect of 2020-12')
    is_deeply_ok(errors({'$schema': Pyjo.JSON.Schema.DIALECT + '#'}, None), [], 'dialect with a fragment')
    is_deeply_ok(
        errors({'additionalItems': False, 'definitions': {'a': 1}, 'x-custom': [1]}, [1]),
        [],
        'keywords that 2020-12 does not have',
    )
    throws_ok(
        lambda: Schema.new({'items': [{'type': 'string'}]}).validate([1]),
        re.compile(r'^JSON Schema has no schema in /items'),
        'items of older drafts',
    )

with subtest('Schemas of type hints'):
    for tp, good, bad in (
        (bool, [True], [1, None]),
        (int, [1, 1.0], [True, 1.5, '1']),
        (float, [1, 1.5], [True, '1.5']),
        (str, [''], [None, 1]),
        (None, [None], [False, 0]),
        (list[int], [[], [1, 2]], [[1, 'a'], {}]),
        (set[str], [['a', 'b']], [['a', 'a']]),
        (tuple[int, str], [[1, 'a'], (1, 'a')], [[1], [1, 'a', 2], ['a', 1]]),
        (tuple[int, ...], [[1, 2, 3]], [[1, 'a']]),
        (dict[str, int], [{'a': 1}], [{'a': 'b'}, [1]]),
        (int | None, [1, None], ['a']),
        (int | str, [1, 'a'], [None]),
        (Literal['a', 'b'], ['a'], ['c']),
        (Literal[1], [1], [True]),
        (Unit, ['celsius'], ['kelvin']),
        (Point, [{'x': 1, 'y': 2}, {'x': 1, 'y': 2, 'z': 3}], [{'x': 1}, {'x': 'a', 'y': 2}]),
        (Tagged, [{'name': 'a'}, {'name': 'a', 'tag': 'b'}], [{'name': 'a', 'tag': ''}]),
        (
            Node,
            [{'name': 'a', 'children': [{'name': 'b', 'children': []}]}],
            [{'name': 'a', 'children': [{'name': 'b'}]}],
        ),
        (Location, [{'city': 'Warsaw'}, {'city': 'Warsaw', 'days': 1}], [{'days': 1}, {'city': 'Warsaw', 'days': '1'}]),
        (Annotated[int, {'minimum': 1}], [1], [0]),
        (datetime.date, ['2026-10-23'], ['23.10.2026']),
        (uuid.UUID, [str(uuid.UUID(int=1))], ['1']),
    ):
        schema = Schema.of(tp)
        for value in good:
            ok(schema.validate(value, True), f'{tp} validates {value!r}')
        for value in bad:
            ok(not schema.validate(value, True), f'{tp} rejects {value!r}')

    def weather(city: str, days: int = 3, unit: Unit = Unit.CELSIUS) -> dict[str, float]:
        """Forecast of the weather."""
        return {}

    schema = Schema.parameters(weather)
    ok(schema.validate({'city': 'Warsaw'}), 'parameters')
    is_deeply_ok(
        [str(e) for e in schema.validate({'days': 'three', 'unit': 'kelvin'}).errors],
        [
            '/days: Expected integer - got string.',
            '/unit: Not in enum: "celsius", "fahrenheit".',
            '/city: Missing property.',
        ],
        'parameters',
    )
    ok(Schema.returns(weather).validate({'a': 1.5}), 'return value')
    ok(not Schema.returns(weather).validate({'a': None}), 'return value')

with subtest('Schemas of the builder'):
    schema = z.object(name=z.string().min(1), email=z.email().optional(), age=z.int().gte(0).nullable())
    ok(schema.validate({'name': 'Joe', 'age': None}), 'object')
    ok(schema.validate({'name': 'Joe', 'age': 1, 'other': True}), 'loose')
    is_deeply_ok(
        [str(e) for e in schema.strict().validate({'name': '', 'email': 'joe', 'other': 1}, True).errors],
        [
            '/name: Shorter than 1 characters.',
            '/email: Does not match the format email.',
            '/age: Missing property.',
            '/other: Property not allowed.',
        ],
        'strict',
    )
    schema = z.union([z.literal('a'), z.array(z.int()).nonempty()])
    ok(schema.validate('a'), 'union')
    ok(schema.validate([1]), 'union')
    ok(not schema.validate([]), 'union')
    schema = z.lazy(lambda: z.object(children=z.array(schema).optional()))
    ok(schema.validate({'children': [{'children': [{}]}]}), 'lazy')
    ok(not schema.validate({'children': [{'children': [1]}]}), 'lazy')
    schema = z.record(z.string().regex('^[a-z]+$'), z.number())
    ok(schema.validate({'a': 1.5}), 'record')
    is_deeply_ok(
        [str(e) for e in schema.validate({'A': 1}).errors], ['/A: Does not match the pattern ^[a-z]+$.'], 'record'
    )
    ok(z.iso.datetime().validate('2026-10-23T12:00:00Z', True), 'format')
    ok(not z.iso.datetime().validate('2026-10-23', True), 'format')

with subtest('parse'):
    schema = z.object(days=z.int())
    value = {'days': 3}
    is_ok(schema.parse(value), value, 'value')
    throws_ok(
        lambda: schema.parse({'days': 'three'}), re.compile(r'^/days: Expected integer - got string\.$'), 'errors'
    )
    throws_ok(
        lambda: z.object(a=z.iso.date()).parse({'a': 'b'}, True),
        re.compile(r'^/a: Does not match the format date\.$'),
        'formats',
    )

done_testing()
