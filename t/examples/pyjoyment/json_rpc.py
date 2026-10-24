import Pyjo.Test.Pyjo

from Pyjo.File import curfile
from Pyjo.Test import *


# The application of examples/pyjoyment/json_rpc.py, which the test loads without starting a server, and which requests
# its own server of JSON-RPC with the user agent of the application
examples = curfile().dirname().dirname().dirname().sibling('examples', 'pyjoyment')
t = Pyjo.Test.Pyjo.new(examples.child('json_rpc.py'))

with subtest('Calculator'):
    t.get_ok('/').status_is(200).text_is('title', 'JSON-RPC Calculator')
    t.element_exists('link[href="/pyjo/bootstrap/bootstrap.css"]')
    t.attr_is('form', 'method', 'POST').attr_is('form', 'action', '/')
    t.element_count_is('input[type=radio][name=method]', 4).element_exists('input[value=add][checked]')
    t.text_is('label[for=add]', '+').text_is('label[for=subtract]', '−')
    t.text_is('label[for=multiply]', '×').text_is('label[for=divide]', '÷')
    t.text_is('form button', '=')
    t.element_exists_not('#result').element_exists_not('#request').element_exists_not('#response')

with subtest('Operations'):
    t.post_ok('/', form={'a': '7', 'b': '2', 'method': 'add'}).status_is(200)
    t.text_is('#result.alert-success', '7 + 2 = 9').element_exists('input[value=add][checked]')
    t.attr_is('input[name=a]', 'value', '7').attr_is('input[name=b]', 'value', '2')
    t.text_is('#request', '{"id":1,"jsonrpc":"2.0","method":"add","params":[7,2]}')
    t.text_is('#response', '{"id":1,"jsonrpc":"2.0","result":9}')
    t.post_ok('/', form={'a': '7', 'b': '2', 'method': 'subtract'}).status_is(200)
    t.text_is('#result.alert-success', '7 − 2 = 5').element_exists('input[value=subtract][checked]')
    t.element_count_is('input[checked]', 1)
    t.post_ok('/', form={'a': '1.5', 'b': '2', 'method': 'multiply'}).status_is(200)
    t.text_is('#result.alert-success', '1.5 × 2 = 3')
    t.text_is('#response', '{"id":1,"jsonrpc":"2.0","result":3.0}')
    t.post_ok('/', form={'a': '7', 'b': '2', 'method': 'divide'}).status_is(200)
    t.text_is('#result.alert-success', '7 ÷ 2 = 3.5')
    t.post_ok('/', form={'a': '-6', 'b': '3', 'method': 'divide'}).status_is(200)
    t.text_is('#result.alert-success', '-6 ÷ 3 = -2')

with subtest('Errors'):
    t.post_ok('/', form={'a': '1', 'b': '0', 'method': 'divide'}).status_is(200)
    t.text_is('#result.alert-danger', 'Division by zero (1)')
    t.text_is('#response', '{"error":{"code":1,"message":"Division by zero"},"id":1,"jsonrpc":"2.0"}')
    t.post_ok('/', form={'a': 'x', 'b': '2', 'method': 'add'}).status_is(200)
    t.text_is('#result.alert-danger', 'Invalid params (-32602): /a: Expected number - got string.')
    t.text_is('#request', '{"id":1,"jsonrpc":"2.0","method":"add","params":["x",2]}')
    t.post_ok('/', form={'a': '1', 'b': '2', 'method': 'power'}).status_is(200)
    t.text_is('#result.alert-danger', 'Method not found (-32601)').element_exists('input[value=add][checked]')

with subtest('Server'):
    t.post_ok('/rpc', json={'jsonrpc': '2.0', 'method': 'multiply', 'params': {'a': 6, 'b': 7}, 'id': 'x'})
    t.status_is(200).json_is({'jsonrpc': '2.0', 'result': 42, 'id': 'x'})
    t.post_ok('/rpc', json={'jsonrpc': '2.0', 'method': 'add', 'params': [1, 2]}).status_is(202)

done_testing()
