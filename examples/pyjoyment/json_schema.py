"""
__DATA__

@@ index.html.ep
<!DOCTYPE html>
<html>
  <head>
    <title>JSON Schema</title>
    <style>
      textarea { box-sizing: border-box; width: 100%; height: 20em; font-family: monospace; }
    </style>
  </head>
  <body>
    <h1>JSON Schema</h1>
    <p>
      % for name, title in examples.items():
        <a href="?example=<%= name %>"><%= title %></a>
      % end
    </p>
    <form method="POST" action="<%= url_for('index') %>">
      <h2>Document</h2>
      <textarea name="document"><%= document %></textarea>
      <h2>Schema</h2>
      <textarea name="schema"><%= schema %></textarea>
      <p>
        <label>
          <input type="checkbox" name="formats" value="1"<%= ' checked' if formats else '' %>>
          Formats as assertions
        </label>
        <button>Validate</button>
      </p>
    </form>
    <h2>Result</h2>
    % if not errors:
      <p id="result">Valid.</p>
    % else:
      <ul id="result">
        % for error in errors:
          <li><%= error %></li>
        % end
      </ul>
    % end
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
# json_schema_examples, and the schemas that they refer to by their $id
EXAMPLES = curfile().sibling('json_schema_examples')
TITLES = {
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


# An example, the first one by default, validated with the formats as assertions
@get('/')
def index(c):
    name = c.param('example') if c.param('example') in TITLES else 'address'
    document = EXAMPLES.child(f'{name}.json').slurp().decode()
    schema = EXAMPLES.child(f'{name}.schema.json').slurp().decode()
    errors = validate(document, schema, True)
    c.render('index', examples=TITLES, document=document, schema=schema, formats=True, errors=errors)


# The document and the schema of the form
@post('/')
def check(c):
    document, schema, formats = c.param('document') or '', c.param('schema') or '', bool(c.param('formats'))
    errors = validate(document, schema, formats)
    c.render('index', examples=TITLES, document=document, schema=schema, formats=formats, errors=errors)


app.start()
