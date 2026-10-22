import Pyjo.App.Lambda
import Pyjo.Test.Pyjo

from Pyjo.File import curfile
from Pyjo.Test import *

import os


# The function of examples/lambda behind the load balancer of AWS of TEST_LAMBDA_URL, which "tofu output -raw url"
# gives, or in the events of a load balancer of Pyjo.App.Lambda otherwise
url = os.environ.get('TEST_LAMBDA_URL', '').rstrip('/')
if url:
    function = None
    t = Pyjo.Test.Pyjo.new()
else:
    if os.name == 'nt':
        plan(skip_all='Lambda functions need pipes that the event loop watches, which Windows does not have')
    root = curfile().dirname().dirname().dirname().sibling('examples', 'lambda')
    function = Pyjo.App.Lambda.new(
        function='app.handler', task_root=root.to_str(), payload='alb', env={'PYJO_MODE': 'production'}
    )
    t = Pyjo.Test.Pyjo.new(function)

with subtest('Hello'):
    t.get_ok(f'{url}/').status_is(200).content_is('Hello Pyjoyment on AWS Lambda!')

with subtest('Query'):
    # The load balancer sends the last value of a parameter, without the values of multiple values of the target group
    t.get_ok(f'{url}/echo?foo=bar&foo=baz&a+b=c%26d').status_is(200)
    t.json_is('/method', 'GET').json_is('/path', '/echo').json_is('/query', {'foo': 'baz', 'a b': 'c&d'})

with subtest('Body'):
    t.post_ok(f'{url}/echo', 'Hello ♥!').status_is(200).json_is('/method', 'POST').json_is('/body', 'Hello ♥!')

with subtest('Not found'):
    t.get_ok(f'{url}/missing').status_is(404)

with subtest('Static file'):
    # A file of the resources of Pyjoyment, of the layer on AWS, in Base64 in the response of the function
    png = curfile().dirname().dirname().dirname().sibling('Pyjoyment', 'resources', 'public', 'pyjo', 'nounicat.png')
    t.get_ok(f'{url}/pyjo/nounicat.png').status_is(200).content_type_is('image/png')
    is_ok(t.tx.res.body, png.slurp(), 'same bytes')

if function:
    function.close()

done_testing()
