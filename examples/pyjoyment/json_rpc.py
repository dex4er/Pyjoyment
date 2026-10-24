"""
__DATA__

@@ index.html.ep
<!DOCTYPE html>
<html>
  <head>
    <title>JSON-RPC Calculator</title>
    %= stylesheet('/pyjo/bootstrap/bootstrap.css')
  </head>
  <body>
    <div class="container py-4">
      <h1>JSON-RPC Calculator</h1>
      <form method="POST" action="<%= url_for('/') %>">
        <div class="input-group mb-3">
          <input class="form-control" type="number" step="any" name="a" value="<%= a %>" aria-label="First number" required>
          % for name, sign in operations.items():
            <input class="btn-check" type="radio" name="method" id="<%= name %>" value="<%= name %>" autocomplete="off"<%= ' checked' if name == (method or 'add') else '' %>>
            <label class="btn btn-outline-primary" for="<%= name %>"><%= sign %></label>
          % end
          <input class="form-control" type="number" step="any" name="b" value="<%= b %>" aria-label="Second number" required>
          <button class="btn btn-primary" aria-label="Calculate">=</button>
        </div>
      </form>
      % if error:
        <div class="alert alert-danger" id="result"><%= error %></div>
      % elif method:
        <div class="alert alert-success" id="result"><%= a %> <%= operations[method] %> <%= b %> = <%= result %></div>
      % end
      % if request:
        <div class="row">
          <div class="col-md-6 mb-3">
            <h2 class="h6">Request</h2>
            <pre class="bg-body-tertiary border rounded p-2 text-wrap text-break" id="request"><%= request %></pre>
          </div>
          <div class="col-md-6 mb-3">
            <h2 class="h6">Response</h2>
            <pre class="bg-body-tertiary border rounded p-2 text-wrap text-break" id="response"><%= response %></pre>
          </div>
        </div>
      % end
    </div>
  </body>
</html>
"""

import Pyjo.Exception
import Pyjo.JSON

from Pyjo.JSON.RPC import RPC, Client, Error
from Pyjoyment.Lite import *


# The server of JSON-RPC, whose methods validate their parameters with the schema of their type hints
rpc = RPC()

# An error of the application, outside of the codes that JSON-RPC keeps for itself
DIVISION_BY_ZERO = 1

OPERATIONS = {'add': '+', 'subtract': '−', 'multiply': '×', 'divide': '÷'}


@rpc.method(schema=True)
def add(a: float, b: float) -> float:
    return a + b


@rpc.method(schema=True)
def subtract(a: float, b: float) -> float:
    return a - b


@rpc.method(schema=True)
def multiply(a: float, b: float) -> float:
    return a * b


@rpc.method(schema=True)
def divide(a: float, b: float) -> float:
    if b == 0:
        raise Error.new(DIVISION_BY_ZERO, 'Division by zero')
    return a / b


post('/rpc', rpc.to_action())


def number(value):
    # A number of the form, or the text itself, which the schema of the method rejects
    for convert in (int, float):
        try:
            return convert(value)
        except ValueError:
            pass
    return value


def page(c, a='', b='', method=None, result=None, error=None, request=None, response=None):
    # The calculator, with the call and the exchange of JSON-RPC that gave its result
    method = method if method in OPERATIONS else None
    c.render(
        'index',
        operations=OPERATIONS,
        a=a,
        b=b,
        method=method,
        result=result,
        error=error,
        request=request,
        response=response,
    )


get('/', page)


# The calculator is a client of the server, through the user agent of the application, which requests the application
# itself, as a relative URL has no host
@post('/')
async def calculate(c):
    a, b, method = c.param('a') or '', c.param('b') or '', c.param('method')
    exchange = {}

    def send(request):
        exchange['request'] = Pyjo.JSON.to_json(request)

        def received(tx):
            exchange['response'] = tx.res.text
            return tx.res.json()

        return c.ua().post_p('/rpc', json=request).then(received)

    result = error = None
    try:
        result = await Client.new(send).call_p(method or '', number(a), number(b))
        # A number without a fraction, as 2.0 of a division, without it on the page, as in JavaScript
        if isinstance(result, float) and result.is_integer():
            result = int(result)
    except Error as e:
        error = f'{e.message} ({e.code})' + (f': {e.data}' if e.data is not None else '')
    except Pyjo.Exception.object as e:
        error = e.message
    page(c, a, b, method, result, error, exchange.get('request'), exchange.get('response'))


app.start()
