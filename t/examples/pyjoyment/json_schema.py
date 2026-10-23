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
    t.element_count_is('nav a[href^="?example="]', len(NAMES) + 1)
    t.text_is('nav a:first-child', 'Custom')
    t.text_is('nav a.active', 'Address')
    t.element_exists('link[href="/pyjo/bootstrap/bootstrap.css"]')
    t.get_ok('/pyjo/bootstrap/bootstrap.css').status_is(200).content_type_is('text/css')
    t.get_ok('/')
    t.text_is('textarea[name=document]', EXAMPLES.child('address.json').slurp().decode())
    t.text_is('textarea[name=schema]', EXAMPLES.child('address.schema.json').slurp().decode())
    t.element_exists('input[name=formats][checked]')
    t.attr_is('form', 'method', 'POST').attr_is('form', 'action', '/')
    t.text_is('label[for=formats]', 'Check formats (date, email, URI…)')
    for name in NAMES:
        t.get_ok(f'/?example={name}').status_is(200).element_count_is('nav a.active', 1)
        t.attr_is('nav a.active', 'href', f'?example={name}')
        t.attr_is('input[type=hidden][name=example]', 'value', name)
        t.text_is('textarea[name=document]', EXAMPLES.child(f'{name}.json').slurp().decode())
        t.text_is('textarea[name=schema]', EXAMPLES.child(f'{name}.schema.json').slurp().decode())
        t.text_is('#result.alert-success', 'Valid.')

with subtest('Broken documents'):
    for name in NAMES:
        document = Pyjo.JSON.decode_json(EXAMPLES.child(f'{name}.json').slurp())
        schema = EXAMPLES.child(f'{name}.schema.json').slurp().decode()
        # A property of the document, whose value is replaced by one that no schema of the examples has
        broken = Pyjo.JSON.to_json({**document, next(iter(document)): [[None]]})
        t.post_ok('/', form={'document': broken, 'schema': schema, 'formats': '1'}).status_is(200)
        if name == 'ecommerce':
            # The schema of json-schema.org has only $defs, which validates any document
            t.text_is('#result.alert-success', 'Valid.')
        else:
            t.element_exists('#result li', f'{name} is not valid')

with subtest('Formats'):
    document = Pyjo.JSON.decode_json(EXAMPLES.child('movie.json').slurp())
    broken = Pyjo.JSON.to_json({**document, 'releaseDate': 'yesterday'})
    schema = EXAMPLES.child('movie.schema.json').slurp().decode()
    t.post_ok('/', form={'document': broken, 'schema': schema, 'formats': '1'}).status_is(200)
    t.text_is('#result li', '/releaseDate: Does not match the format date.')
    t.element_exists('input[name=formats][checked]')
    t.post_ok('/', form={'document': broken, 'schema': schema}).status_is(200)
    t.text_is('#result.alert-success', 'Valid.')
    t.element_exists_not('input[name=formats][checked]')

with subtest('Custom'):
    t.get_ok('/?example=custom').status_is(200).text_is('nav a.active', 'Custom')
    t.attr_is('input[name=example]', 'value', 'custom')
    document = Pyjo.JSON.from_json(t.tx.res.dom().at('textarea[name=document]').text)
    schema = Pyjo.JSON.from_json(t.tx.res.dom().at('textarea[name=schema]').text)
    is_deeply_ok(document, {}, 'template of a document')
    is_deeply_ok(
        schema,
        {
            '$id': 'https://example.com/custom.schema.json',
            '$schema': 'https://json-schema.org/draft/2020-12/schema',
            'type': 'object',
            'required': [],
            'properties': {},
        },
        'template of a schema',
    )
    t.text_is('#result.alert-success', 'Valid.')
    schema = {**schema, 'required': ['name'], 'properties': {'email': {'type': 'string', 'format': 'email'}}}
    form = {'example': 'custom', 'schema': Pyjo.JSON.to_json(schema), 'formats': '1'}
    t.post_ok('/', form={**form, 'document': '{"email": "joe"}'}).status_is(200)
    t.text_is('#result li:nth-child(1)', '/email: Does not match the format email.')
    t.text_is('#result li:nth-child(2)', '/name: Missing property.')
    t.post_ok('/', form={'example': 'custom', 'document': '1', 'schema': '{"type": "string"}'}).status_is(200)
    t.text_is('nav a.active', 'Custom').text_is('#result li', '/: Expected string - got integer.')

with subtest('Switch to Custom'):
    document = EXAMPLES.child('movie.json').slurp().decode()
    schema = EXAMPLES.child('movie.schema.json').slurp().decode()
    # A text area of a form sends its lines with CRLF
    form = {'example': 'movie', 'document': document.replace('\n', '\r\n'), 'schema': schema, 'formats': '1'}
    t.post_ok('/', form=form).status_is(200)
    t.text_is('nav a.active', 'Movie').attr_is('input[name=example]', 'value', 'movie')
    t.post_ok('/', form={**form, 'document': document.replace('Sample Movie', 'Other Movie')}).status_is(200)
    t.text_is('nav a.active', 'Custom').attr_is('input[name=example]', 'value', 'custom')
    t.text_is('#result.alert-success', 'Valid.')
    t.post_ok('/', form={**form, 'schema': schema.replace('"date"', '"time"')}).status_is(200)
    t.text_is('nav a.active', 'Custom').text_is('#result li', '/releaseDate: Does not match the format time.')
    t.post_ok('/', form={**form, 'example': 'address'}).status_is(200)
    t.text_is('nav a.active', 'Custom')
    t.post_ok('/', form={'document': document, 'schema': schema}).status_is(200)
    t.text_is('nav a.active', 'Custom')
    t.post_ok('/', form={**form, 'example': 'missing'}).status_is(200)
    t.text_is('nav a.active', 'Custom')

with subtest('References'):
    document = Pyjo.JSON.to_json({'deviceType': 'laptop', 'brand': 'Lenovo', 'model': 'X1'})
    schema = EXAMPLES.child('device.schema.json').slurp().decode()
    t.post_ok('/', form={'document': document, 'schema': schema}).status_is(200)
    # The errors of both schemas of oneOf, as none of them validates the document
    t.text_is('#result li:nth-child(1)', '/deviceType: Not the const: "smartphone".')
    t.text_is('#result li:nth-child(2)', '/screenSize: Missing property.')
    t.text_is('#result li:nth-child(3)', '/processor: Missing property.')
    t.text_is('#result li:nth-child(4)', '/ramSize: Missing property.')
    t.element_count_is('#result li', 4)
    document = Pyjo.JSON.to_json(
        {'deviceType': 'laptop', 'brand': 'Lenovo', 'model': 'X1', 'processor': 'i7', 'ramSize': 16}
    )
    t.post_ok('/', form={'document': document, 'schema': schema}).status_is(200)
    t.text_is('#result.alert-success', 'Valid.')

with subtest('Errors'):
    t.post_ok('/', form={'document': '{', 'schema': '{}'}).status_is(200)
    t.text_like('#result li', r'^The document is not JSON: Malformed JSON')
    t.post_ok('/', form={'document': '1', 'schema': '{'}).status_is(200)
    t.text_like('#result li', r'^The schema is not JSON: Malformed JSON')
    t.post_ok('/', form={'document': '1', 'schema': '{"$dynamicRef": "#a"}'}).status_is(200)
    t.text_is('#result li', 'JSON Schema does not support $dynamicRef in /')
    t.post_ok('/', form={'document': '1', 'schema': '{"$ref": "https://example.com/missing.json"}'}).status_is(200)
    t.text_is('#result li', 'JSON Schema has no schema of the $ref https://example.com/missing.json in /$ref')

done_testing()
