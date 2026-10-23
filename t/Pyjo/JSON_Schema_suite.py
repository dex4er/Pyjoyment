import Pyjo.Exception
import Pyjo.JSON

from Pyjo.File import curfile
from Pyjo.JSON.Schema import Schema
from Pyjo.Test import *

import os

from typing import Any


# Not in Mojolicious: the official test suite of JSON Schema, JSON-Schema-Test-Suite, for draft 2020-12, of the
# devDependencies of package.json, which npm ci installs

ROOT = curfile().dirname().dirname().dirname()
SUITE = ROOT.child('node_modules', 'json-schema-test-suite')
TESTS = SUITE.child('tests', 'draft2020-12')

if not os.path.exists(TESTS.to_str()):
    plan(skip_all='JSON-Schema-Test-Suite is not installed, npm ci installs it')

# The files that are left out, with the reason
LEFT_OUT_FILES = {
    'dynamicRef.json': '$dynamicRef',
    'unevaluatedItems.json': 'unevaluatedItems',
    'unevaluatedProperties.json': 'unevaluatedProperties',
    'vocabulary.json': 'the vocabularies of a metaschema of its own',
    'optional/cross-draft.json': 'the dialects of the older drafts',
    'optional/dependencies-compatibility.json': 'dependencies of the older drafts, which 2020-12 does not have',
    'optional/dynamicRef.json': '$dynamicRef',
    'optional/format-assertion.json': 'the vocabularies of a metaschema of its own',
    'optional/format/idn-email.json': 'a format that stays an annotation',
    'optional/format/idn-hostname.json': 'a format that stays an annotation',
    'optional/format/iri.json': 'a format that stays an annotation',
    'optional/format/iri-reference.json': 'a format that stays an annotation',
    'optional/format/uri-template.json': 'a format that stays an annotation',
}

# The cases that are left out, by their file and the description of their group, with the reason
LEFT_OUT = {
    ('defs.json', 'validate definition against metaschema'): 'the metaschema of 2020-12 has $dynamicRef',
    ('not.json', "collect annotations inside a 'not', even if collection is disabled"): 'unevaluatedProperties',
    ('ref.json', 'remote ref, containing refs itself'): 'the metaschema of 2020-12 has $dynamicRef',
    ('ref.json', 'ref creates new scope when adjacent to keywords'): 'unevaluatedProperties',
    ('optional/format/ecmascript-regex.json', 'ECMA 262 lookbehind is valid, including variable width'): (
        're of Python has no lookbehind of a variable width'
    ),
    ('optional/format/hostname.json', 'validation of A-label (punycode) host names'): (
        'the rules of IDNA 2008 for the A-labels, but Punycode'
    ),
}

# The schemas that a $ref refers to, on the host of the test suite, which the registry indexes when a $ref looks for
# them, so that the ones of the older drafts and of $dynamicRef are left alone
remotes: dict[str, Any] = {}
for file in SUITE.child('remotes').list_tree().sort():
    remotes[f'http://localhost:1234/{file.to_rel(SUITE.child("remotes")).to_str().replace("\\", "/")}'] = (
        Pyjo.JSON.decode_json(file.slurp())
    )


def valid(schema: Schema, data: Any, formats: bool) -> bool | str:
    try:
        return bool(schema.validate(data, formats))
    except Pyjo.Exception.object as e:
        return str(e)


for file in TESTS.list_tree().sort():
    name = file.to_rel(TESTS).to_str().replace('\\', '/')
    if not name.endswith('.json'):
        continue
    if name in LEFT_OUT_FILES:
        skip(f'{name}: {LEFT_OUT_FILES[name]}')
        continue
    # The formats are assertions in the tests of formats, as the test suite says
    formats = name.startswith('optional/format/')
    with subtest(name):
        for group in Pyjo.JSON.decode_json(file.slurp()):
            with subtest(group['description']):
                schema = Schema.new(group['schema'])
                for uri, remote in remotes.items():
                    schema.add_schema(remote, uri)
                reason = LEFT_OUT.get((name, group['description']))
                if reason is not None:
                    results = [valid(schema, test['data'], formats) is test['valid'] for test in group['tests']]
                    ok(not all(results), f'still left out: {reason}')
                    skip(reason, len(group['tests']))
                    continue
                for test in group['tests']:
                    is_ok(valid(schema, test['data'], formats), test['valid'], test['description'])

done_testing()
