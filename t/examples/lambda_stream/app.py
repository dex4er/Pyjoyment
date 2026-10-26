import Pyjo.App.Lambda
import Pyjo.Test.Pyjo

from Pyjo.File import curfile
from Pyjo.Test import *

import os
import time


# The function of examples/lambda_stream on AWS, behind the Function URL of TEST_LAMBDA_STREAM_URL, which
# "tofu output -raw url" gives, or with Pyjo.App.Lambda otherwise, which streams its responses as the Function URL does
ROOT = curfile().dirname().dirname().dirname()
URL = os.environ.get('TEST_LAMBDA_STREAM_URL')

if not URL and os.name == 'nt':
    plan(skip_all='Lambda functions need pipes that the event loop watches, which Windows does not have')


def check(t: Pyjo.Test.Pyjo.object, url: str) -> None:
    with subtest('Hello'):
        t.get_ok(f'{url}/').status_is(200).content_is('Hello Pyjoyment on AWS Lambda, streaming!')

    with subtest('Count'):
        # The times the lines come at, as a read can take several of them
        times = []

        @t.ua.once('start')
        def start(ua, tx):
            tx.res.content.on('read', lambda content, chunk: times.append((time.monotonic(), bytes(chunk))))

        t.get_ok(f'{url}/count').status_is(200).content_type_is('text/plain').content_is('1\n2\n3\n4\n5\n')
        at = {}
        received = b''
        for when, chunk in times:
            received += chunk
            for line in (b'1\n', b'5\n'):
                if line in received:
                    at.setdefault(line, when)
        ok(at[b'5\n'] - at[b'1\n'] >= 1.5, 'lines as they are written')

    with subtest('Not found'):
        t.get_ok(f'{url}/missing').status_is(404)


if URL:
    with subtest('Function URL on AWS'):
        check(Pyjo.Test.Pyjo.new(), URL.rstrip('/'))
else:
    with subtest('Function URL'):
        env = {'PYJO_MODE': 'production', 'PYJO_LAMBDA_INVOKE_MODE': 'RESPONSE_STREAM'}
        task_root = ROOT.sibling('examples', 'lambda_stream').to_str()
        with Pyjo.App.Lambda.new(function='app.handler', task_root=task_root, env=env) as function:
            check(Pyjo.Test.Pyjo.new(function), '')

done_testing()
