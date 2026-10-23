from Pyjo.File import curfile
from Pyjo.JSON.Schema import z
from Pyjo.Test import *

import json
import os
import shutil
import subprocess

from typing import Any


# Not in Mojolicious: the schemas of the builder of Pyjo.JSON.Schema next to the ones that z.toJSONSchema() of zod
# makes for the input, with the same code in JavaScript, where Node.js and zod of package.json are installed

ROOT = curfile().dirname().dirname().dirname()
NODE = shutil.which('node')

if NODE is None:
    plan(skip_all='Node.js is not installed')
if not os.path.exists(ROOT.child('node_modules', 'zod', 'package.json')):
    plan(skip_all='zod is not installed, npm ci installs it')

# zod for the integers of JavaScript, and its regular expressions of formats
SAFE_INTEGER = 9007199254740991
PATTERN_FORMATS = ('email', 'uuid', 'date-time', 'date')
TIME_PATTERN = r'^(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d(?:\.\d+)?)?$'

CASES: list[tuple[str, Any, str]] = [
    ('string', z.string(), 'z.string()'),
    ('string min max regex', z.string().min(1).max(5).regex('^a+$'), 'z.string().min(1).max(5).regex(/^a+$/)'),
    ('string length', z.string().length(3), 'z.string().length(3)'),
    ('string nonempty', z.string().nonempty(), 'z.string().nonempty()'),
    ('email', z.email(), 'z.email()'),
    ('string email', z.string().email(), 'z.string().email()'),
    ('url', z.url(), 'z.url()'),
    ('uuid', z.uuid(), 'z.uuid()'),
    ('iso datetime', z.iso.datetime(), 'z.iso.datetime()'),
    ('iso date', z.iso.date(), 'z.iso.date()'),
    ('iso time', z.iso.time(), 'z.iso.time()'),
    ('number', z.number().min(0).max(10), 'z.number().min(0).max(10)'),
    ('number gt lt multiple_of', z.number().gt(0).lt(10).multiple_of(2), 'z.number().gt(0).lt(10).multipleOf(2)'),
    ('int', z.int(), 'z.int()'),
    ('int min', z.int().min(1), 'z.int().min(1)'),
    ('int gte lte', z.int().gte(1).lte(7), 'z.int().gte(1).lte(7)'),
    ('boolean', z.boolean(), 'z.boolean()'),
    ('null', z.null(), 'z.null()'),
    ('any', z.any(), 'z.any()'),
    ('literal', z.literal('a'), "z.literal('a')"),
    ('literals', z.literal(['a', 'b']), "z.literal(['a', 'b'])"),
    ('enum', z.enum(['a', 'b']), "z.enum(['a', 'b'])"),
    ('union', z.union([z.string(), z.int()]), 'z.union([z.string(), z.int()])'),
    ('array', z.array(z.string()).min(1).max(3), 'z.array(z.string()).min(1).max(3)'),
    ('array nonempty', z.array(z.string()).nonempty(), 'z.array(z.string()).nonempty()'),
    ('array length', z.array(z.string()).length(2), 'z.array(z.string()).length(2)'),
    ('tuple', z.tuple([z.string(), z.int()]), 'z.tuple([z.string(), z.int()])'),
    ('tuple rest', z.tuple([z.string()], z.int()), 'z.tuple([z.string()], z.int())'),
    ('record', z.record(z.string(), z.int()), 'z.record(z.string(), z.int())'),
    (
        'object',
        z.object({'a': z.string(), 'b': z.int().optional(), 'c': z.int().default(1), 'd': z.string().nullable()}),
        'z.object({a: z.string(), b: z.int().optional(), c: z.int().default(1), d: z.string().nullable()})',
    ),
    ('object nested', z.object(p=z.object(x=z.int())), 'z.object({p: z.object({x: z.int()})})'),
    ('strict', z.object(a=z.string()).strict(), 'z.object({a: z.string()}).strict()'),
    ('strict_object', z.strict_object({'a': z.string()}), 'z.strictObject({a: z.string()})'),
    ('loose', z.object(a=z.string()).loose(), 'z.object({a: z.string()}).loose()'),
    ('passthrough', z.object(a=z.string()).passthrough(), 'z.object({a: z.string()}).passthrough()'),
    ('loose_object', z.loose_object({'a': z.string()}), 'z.looseObject({a: z.string()})'),
    ('describe', z.string().describe('City'), "z.string().describe('City')"),
    ('meta', z.string().meta(title='City'), "z.string().meta({title: 'City'})"),
    ('nullable', z.string().nullable(), 'z.string().nullable()'),
    ('nullable int', z.int().nullable(), 'z.int().nullable()'),
    ('nullable object', z.object(a=z.int()).nullable(), 'z.object({a: z.int()}).nullable()'),
    ('nullish', z.string().nullish(), 'z.string().nullish()'),
    ('optional', z.string().optional(), 'z.string().optional()'),
    ('default', z.int().default(3), 'z.int().default(3)'),
    (
        'lazy',
        z.lazy(lambda: category),
        '(() => { const c = z.object({name: z.string(), get subcategories() { return z.array(c) }}); return c })()',
    ),
]

category = z.object(name=z.string(), subcategories=z.array(z.lazy(lambda: category)))


def zod(cases: list[tuple[str, Any, str]]) -> dict[str, Any]:
    # One run of Node.js for all of them, whose ESM resolves zod from the current directory, as the code is on stdin
    entries = ',\n'.join(f'  [{json.dumps(name)}, () => {code}]' for name, _, code in cases)
    script = (
        "import { z } from 'zod';\n"
        f'const cases = [\n{entries}\n];\n'
        "const out = Object.fromEntries(cases.map(([name, f]) => [name, z.toJSONSchema(f(), {io: 'input'})]));\n"
        'process.stdout.write(JSON.stringify(out));\n'
    )
    result = subprocess.run(
        [str(NODE), '--input-type=module'],
        input=script,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        check=True,
        encoding='UTF-8',
    )
    return json.loads(result.stdout)


def normalize(schema: Any, root: bool = False) -> Any:
    # The differences of zod, each noted where it is left out
    if isinstance(schema, list):
        return [normalize(item) for item in schema]  # pyright: ignore[reportUnknownVariableType]
    if not isinstance(schema, dict):
        return schema
    schema = {name: normalize(value) for name, value in schema.items()}  # pyright: ignore[reportUnknownVariableType]

    # zod names its dialect, which Pyjo.JSON.Schema does on request
    if root:
        schema.pop('$schema', None)

    # zod bounds an integer by the safe integers of JavaScript, which an integer of Python does not have
    if schema.get('type') == 'integer':
        if schema.get('minimum') == -SAFE_INTEGER:
            del schema['minimum']
        if schema.get('maximum') == SAFE_INTEGER:
            del schema['maximum']

    # zod adds null to the type of a schema of only a type, which an integer is not with its bounds
    any_of = schema.get('anyOf')
    if (
        isinstance(any_of, list)
        and len(any_of) == 2  # pyright: ignore[reportUnknownArgumentType]
        and any_of[1] == {'type': 'null'}
        and isinstance(any_of[0], dict)
        and list(any_of[0]) == ['type']  # pyright: ignore[reportUnknownArgumentType]
        and len(schema) == 1
    ):
        schema = {'type': [any_of[0]['type'], 'null']}

    # zod adds the pattern of its own regular expression to a format, and has only the pattern of a time
    if schema.get('format') in PATTERN_FORMATS:
        schema.pop('pattern', None)
    if schema.get('type') == 'string' and schema.get('pattern') == TIME_PATTERN and 'format' not in schema:
        del schema['pattern']
        schema['format'] = 'time'

    # zod forbids the items after those of a tuple, which its maxItems already does
    if 'prefixItems' in schema and 'maxItems' in schema and schema.get('items') is False:
        del schema['items']

    # zod names the names of a record any string, which every name of JSON is
    if schema.get('propertyNames') == {'type': 'string'}:
        del schema['propertyNames']

    return schema


with subtest('Builder against zod'):
    schemas = zod(CASES)
    for name, ours, _ in CASES:
        is_deeply_ok(ours.data, normalize(schemas[name], True), name)

done_testing()
