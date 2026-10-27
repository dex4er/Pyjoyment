import Pyjo.App.Lambda
import Pyjo.Test.Pyjo

from Pyjo.File import curfile
from Pyjo.Test import *

import os


# The function of examples/lambda on AWS, behind the Function URL of TEST_LAMBDA_URL and the load balancer of
# TEST_LAMBDA_ALB_URL, which "tofu output -raw url" and "tofu output -raw alb_url" give, or with Pyjo.App.Lambda in the
# events of both otherwise
ROOT = curfile().dirname().dirname().dirname()
URLS = {'2.0': os.environ.get('TEST_LAMBDA_URL'), 'alb': os.environ.get('TEST_LAMBDA_ALB_URL')}
remote = any(URLS.values())

if not remote and os.name == 'nt':
    plan(skip_all='Lambda functions need pipes that the event loop watches, which Windows does not have')


def check(t: Pyjo.Test.Pyjo.object, url: str, payload: str) -> None:
    with subtest('Hello'):
        t.get_ok(f'{url}/').status_is(200).content_is('Hello Pyjoyment on AWS Lambda!')

    with subtest('Query'):
        # The load balancer sends the last value of a parameter, without the values of multiple values of the target
        # group, and a Function URL rejects a "+" in the name of a parameter with 400, before the function
        t.get_ok(f'{url}/echo?foo=bar&foo=baz&a%20b=c+%26+d').status_is(200)
        t.json_is('/method', 'GET').json_is('/path', '/echo')
        t.json_is('/query', {'foo': 'baz' if payload == 'alb' else ['bar', 'baz'], 'a b': 'c & d'})

    with subtest('Body'):
        t.post_ok(f'{url}/echo', 'Hello ♥!').status_is(200).json_is('/method', 'POST').json_is('/body', 'Hello ♥!')

    with subtest('Not found'):
        t.get_ok(f'{url}/missing').status_is(404)

    with subtest('Static file'):
        # A file of the resources of Pyjoyment, of the layer on AWS, in Base64 in the response of the function
        png = ROOT.sibling('Pyjoyment', 'resources', 'public', 'pyjo', 'nounicat.png')
        t.get_ok(f'{url}/pyjo/nounicat.png').status_is(200).content_type_is('image/png')
        is_ok(t.tx.res.body, png.slurp(), 'same bytes')


for payload, url in URLS.items():
    if url:
        with subtest(f'Payload {payload} on AWS'):
            check(Pyjo.Test.Pyjo.new(), url.rstrip('/'), payload)
    elif not remote:
        with subtest(f'Payload {payload}'):
            env = {'PYJO_MODE': 'production'}
            task_root = ROOT.sibling('examples', 'lambda', 'function').to_str()
            with Pyjo.App.Lambda.new(function='app.handler', task_root=task_root, payload=payload, env=env) as function:
                check(Pyjo.Test.Pyjo.new(function), '', payload)

done_testing()
