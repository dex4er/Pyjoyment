import Pyjo.JSON
import Pyjo.Test.Pyjo

from Pyjo.File import curfile
from Pyjo.Test import *


# The application of examples/pyjoyment/json_schema.py, which the test loads without starting a server
examples = curfile().dirname().dirname().dirname().sibling('examples', 'pyjoyment')
t = Pyjo.Test.Pyjo.new(examples.child('json_schema.py'))

EXAMPLES = examples.child('json_schema_examples')
NAMES = [
    'address',
    'blog-post',
    'calendar',
    'device',
    'ecommerce',
    'geographical-location',
    'health-record',
    'job-posting',
    'movie',
    'user-profile',
]

with subtest('Examples'):
    t.get_ok('/').status_is(200).text_is('title', 'JSON Schema')
    t.element_count_is('p a[href^="?example="]', len(NAMES))
    t.text_is('textarea[name=document]', EXAMPLES.child('address.json').slurp().decode())
    t.text_is('textarea[name=schema]', EXAMPLES.child('address.schema.json').slurp().decode())
    t.element_exists('input[name=formats][checked]')
    for name in NAMES:
        t.get_ok(f'/?example={name}').status_is(200)
        t.text_is('textarea[name=document]', EXAMPLES.child(f'{name}.json').slurp().decode())
        t.text_is('textarea[name=schema]', EXAMPLES.child(f'{name}.schema.json').slurp().decode())
        if name == 'calendar':
            # The document of json-schema.org has startDate, where its schema requires dtstart
            t.text_is('ul#result li', '/dtstart: Missing property.')
        else:
            t.text_is('p#result', 'Valid.')

with subtest('Broken documents'):
    for name in NAMES:
        document = Pyjo.JSON.decode_json(EXAMPLES.child(f'{name}.json').slurp())
        schema = EXAMPLES.child(f'{name}.schema.json').slurp().decode()
        # A property of the document, whose value is replaced by one that no schema of the examples has
        broken = Pyjo.JSON.to_json({**document, next(iter(document)): [[None]]})
        t.post_ok('/', form={'document': broken, 'schema': schema, 'formats': '1'}).status_is(200)
        if name == 'ecommerce':
            # The schema of json-schema.org has only $defs, which validates any document
            t.text_is('p#result', 'Valid.')
        else:
            t.element_exists('ul#result li', f'{name} is not valid')

with subtest('Formats'):
    document = Pyjo.JSON.decode_json(EXAMPLES.child('movie.json').slurp())
    broken = Pyjo.JSON.to_json({**document, 'releaseDate': 'yesterday'})
    schema = EXAMPLES.child('movie.schema.json').slurp().decode()
    t.post_ok('/', form={'document': broken, 'schema': schema, 'formats': '1'}).status_is(200)
    t.text_is('ul#result li', '/releaseDate: Does not match the format date.')
    t.element_exists('input[name=formats][checked]')
    t.post_ok('/', form={'document': broken, 'schema': schema}).status_is(200)
    t.text_is('p#result', 'Valid.')
    t.element_exists_not('input[name=formats][checked]')

with subtest('References'):
    document = Pyjo.JSON.to_json({'deviceType': 'laptop', 'brand': 'Lenovo', 'model': 'X1'})
    schema = EXAMPLES.child('device.schema.json').slurp().decode()
    t.post_ok('/', form={'document': document, 'schema': schema}).status_is(200)
    # The errors of both schemas of oneOf, as none of them validates the document
    t.text_is('ul#result li:nth-child(1)', '/deviceType: Not the const: "smartphone".')
    t.text_is('ul#result li:nth-child(2)', '/screenSize: Missing property.')
    t.text_is('ul#result li:nth-child(3)', '/processor: Missing property.')
    t.text_is('ul#result li:nth-child(4)', '/ramSize: Missing property.')
    t.element_count_is('ul#result li', 4)
    document = Pyjo.JSON.to_json(
        {'deviceType': 'laptop', 'brand': 'Lenovo', 'model': 'X1', 'processor': 'i7', 'ramSize': 16}
    )
    t.post_ok('/', form={'document': document, 'schema': schema}).status_is(200)
    t.text_is('p#result', 'Valid.')

with subtest('Errors'):
    t.post_ok('/', form={'document': '{', 'schema': '{}'}).status_is(200)
    t.text_like('ul#result li', r'^The document is not JSON: Malformed JSON')
    t.post_ok('/', form={'document': '1', 'schema': '{'}).status_is(200)
    t.text_like('ul#result li', r'^The schema is not JSON: Malformed JSON')
    t.post_ok('/', form={'document': '1', 'schema': '{"$dynamicRef": "#a"}'}).status_is(200)
    t.text_is('ul#result li', 'JSON Schema does not support $dynamicRef in /')
    t.post_ok('/', form={'document': '1', 'schema': '{"$ref": "https://example.com/missing.json"}'}).status_is(200)
    t.text_is('ul#result li', 'JSON Schema has no schema of the $ref https://example.com/missing.json in /$ref')

done_testing()
