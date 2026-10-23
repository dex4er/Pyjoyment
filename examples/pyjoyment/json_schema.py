"""
__DATA__

@@ index.html.ep
<!DOCTYPE html>
<html>
  <head>
    <title>JSON Schema</title>
    %= stylesheet('/pyjo/bootstrap/bootstrap.css')
  </head>
  <body>
    <div class="container py-4">
      <h1>JSON Schema</h1>
      <nav class="nav nav-pills small mb-3">
        % for name, title in examples.items():
          <a class="nav-link px-2<%= ' active' if name == example else '' %>" href="?example=<%= name %>"><%= title %></a>
        % end
      </nav>
      <form method="POST" action="<%= url_for('/') %>">
        <input type="hidden" name="example" value="<%= example %>">
        <div class="row">
          <div class="col-md-6 mb-3">
            <label class="form-label" for="document">Document</label>
            <textarea class="form-control font-monospace" id="document" name="document" rows="12"><%= document %></textarea>
          </div>
          <div class="col-md-6 mb-3">
            <label class="form-label" for="schema">Schema</label>
            <textarea class="form-control font-monospace" id="schema" name="schema" rows="12"><%= schema %></textarea>
          </div>
        </div>
        <div class="d-flex align-items-center gap-3 mb-3">
          <div class="form-check">
            <input class="form-check-input" type="checkbox" id="formats" name="formats" value="1"<%= ' checked' if formats else '' %>>
            <label class="form-check-label" for="formats">Check formats (date, email, URI…)</label>
          </div>
          <button class="btn btn-primary">Validate</button>
        </div>
      </form>
      % if not errors:
        <div class="alert alert-success" id="result">Valid.</div>
      % else:
        <div class="alert alert-danger" id="result">
          <ul class="mb-0">
            % for error in errors:
              <li><%= error %></li>
            % end
          </ul>
        </div>
      % end
    </div>
  </body>
</html>
"""

import Pyjo.Exception
import Pyjo.JSON

from Pyjo.File import curfile
from Pyjo.JSON.Schema import Schema
from Pyjoyment.Lite import *

import re


# The examples of https://json-schema.org/learn/json-schema-examples, a document and its schema in the files of
# json_schema_examples, and the schemas that they refer to by their $id, after a template of its own
EXAMPLES = curfile().sibling('json_schema_examples')
TITLES = {
    'custom': 'Custom',
    'address': 'Address',
    'blog-post': 'Blog post',
    'calendar': 'Calendar',
    'device': 'Device type',
    'ecommerce': 'Ecommerce system',
    'geographical-location': 'Geographical location',
    'health-record': 'Health record',
    'job-posting': 'Job posting',
    'movie': 'Movie',
    'user-profile': 'User profile',
}
SCHEMAS = [Pyjo.JSON.decode_json(file.slurp()) for file in EXAMPLES.list().grep(re.compile(r'\.schema\.json$'))]

CUSTOM_DOCUMENT = """{}
"""
CUSTOM_SCHEMA = """{
  "$id": "https://example.com/custom.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": [],
  "properties": {}
}
"""


def example(name):
    if name == 'custom':
        return CUSTOM_DOCUMENT, CUSTOM_SCHEMA
    return EXAMPLES.child(f'{name}.json').slurp().decode(), EXAMPLES.child(f'{name}.schema.json').slurp().decode()


def same(text, original):
    # A text area of a form sends its lines with CRLF
    return text.replace('\r\n', '\n').strip() == original.strip()


def validate(document, schema, formats):
    try:
        value = Pyjo.JSON.from_json(document)
    except ValueError as e:
        return [f'The document is not JSON: {e}']
    try:
        validator = Schema.new(Pyjo.JSON.from_json(schema))
        for other in SCHEMAS:
            validator.add_schema(other)
        return [str(error) for error in validator.validate(value, formats).errors]
    except ValueError as e:
        return [f'The schema is not JSON: {e}']
    except Pyjo.Exception.object as e:
        return [e.message]


# An example, Address by default, validated with the formats checked
@get('/')
def index(c):
    name = c.param('example') if c.param('example') in TITLES else 'address'
    document, schema = example(name)
    errors = validate(document, schema, True)
    c.render('index', examples=TITLES, example=name, document=document, schema=schema, formats=True, errors=errors)


# The document and the schema of the form, of the example that they come from, or of Custom once they are changed
@post('/')
def check(c):
    name = c.param('example') if c.param('example') in TITLES else 'custom'
    document, schema, formats = c.param('document') or '', c.param('schema') or '', bool(c.param('formats'))
    original_document, original_schema = example(name)
    if not (same(document, original_document) and same(schema, original_schema)):
        name = 'custom'
    errors = validate(document, schema, formats)
    c.render('index', examples=TITLES, example=name, document=document, schema=schema, formats=formats, errors=errors)


app.start()
