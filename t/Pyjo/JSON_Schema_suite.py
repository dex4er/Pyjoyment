import Pyjo.Exception
import Pyjo.JSON

from Pyjo.File import curfile
from Pyjo.JSON.Schema import Schema
from Pyjo.Test import *

from typing import Any


# Not in Mojolicious: the official test suite of JSON Schema, JSON-Schema-Test-Suite, for draft 2020-12, in
# tt/JSON-Schema-Test-Suite, with the files of the keywords that the validation supports

SUITE = curfile().dirname().dirname().sibling('tt', 'JSON-Schema-Test-Suite')
TESTS = SUITE.child('tests', 'draft2020-12')

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

# The schemas that a $ref refers to, on the host of the test suite
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
